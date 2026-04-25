"""API routes for ScoreLock football analytics.

All routes query the database via the db_service layer.
"""

import asyncio
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, get_optional_user
from app.schemas.schemas import (
    FixtureResponse,
    FixtureDetail,
    PredictionResponse,
    ValueBetResponse,
    StandingResponse,
    LeagueResponse,
    SentimentResponse,
    TeamResponse,
    OddsResponse,
    ArticleResponse,
    ArticleListResponse,
    AffiliateLinkResponse,
    AffiliateClickCreate,
    AffiliateClickResponse,
    AffiliateStatsResponse,
    UserPredictionCreate,
    UserPredictionResponse,
    UserPredictionWithFixture,
    LeaderboardEntry,
    AIvsUserStats,
    WeeklyTopTipper,
    BroadcastResponse,
)
from app.services import db_service
from app.models.models import User, ArticleType, FixtureBroadcast

router = APIRouter()


# ── Health ─────────────────────────────────────────────────


@router.get("/health")
async def health_check():
    """Service health check — validates DB + Redis connectivity.

    Does NOT use the get_db dependency so the endpoint always
    returns 200 even when the database is completely unreachable.
    Railway / k8s healthchecks need a response; downstream checks
    are reported as "ok" or "error" in the JSON body.
    """
    import redis as redis_lib
    from app.core.config import get_settings
    from app.core.database import async_session

    checks: dict = {"status": "ok", "service": "scorelock-api", "version": "0.1.0"}

    # DB check — short timeout so healthcheck never hangs
    try:
        async with asyncio.timeout(3):
            async with async_session() as session:
                await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
        checks["status"] = "degraded"

    # Redis check
    try:
        settings = get_settings()
        r = redis_lib.from_url(settings.redis_url, socket_timeout=2)
        r.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"
        checks["status"] = "degraded"

    return checks


# ── Leagues ────────────────────────────────────────────────


@router.get("/leagues", response_model=list[LeagueResponse])
async def get_leagues(db: AsyncSession = Depends(get_db)):
    """Get all active leagues covered by ScoreLock."""
    leagues = await db_service.get_all_leagues(db)
    return leagues


# ── Fixtures ───────────────────────────────────────────────


@router.get("/fixtures", response_model=list[FixtureResponse])
async def get_fixtures(
    match_date: date | None = Query(
        None, alias="date", description="Filter by date (YYYY-MM-DD)"
    ),
    league_id: int | None = Query(None, description="Filter by league"),
    status: str | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
):
    """Get fixtures with optional filters."""
    fixtures = await db_service.get_fixtures(
        db, match_date=match_date, league_id=league_id, status=status
    )
    return fixtures


@router.get("/fixtures/live", response_model=list[FixtureResponse])
async def get_live_fixtures(db: AsyncSession = Depends(get_db)):
    """Get currently live fixtures."""
    fixtures = await db_service.get_live_fixtures(db)
    return fixtures


@router.get("/fixtures/{fixture_id}", response_model=FixtureDetail)
async def get_fixture_detail(fixture_id: int, db: AsyncSession = Depends(get_db)):
    """Get full fixture detail including prediction, odds, and stats."""
    fixture = await db_service.get_fixture_by_id(db, fixture_id)
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    # Build the detail response
    prediction = fixture.predictions[0] if fixture.predictions else None

    return FixtureDetail(
        id=fixture.id,
        league=LeagueResponse.model_validate(fixture.league),
        home_team=TeamResponse.model_validate(fixture.home_team),
        away_team=TeamResponse.model_validate(fixture.away_team),
        kickoff=fixture.kickoff,
        status=fixture.status.value,
        home_goals=fixture.home_goals,
        away_goals=fixture.away_goals,
        round=fixture.round,
        home_goals_ht=fixture.home_goals_ht,
        away_goals_ht=fixture.away_goals_ht,
        stats=fixture.stats,
        prediction=PredictionResponse.model_validate(prediction)
        if prediction
        else None,
        odds=[OddsResponse.model_validate(o) for o in fixture.odds],
    )


@router.get(
    "/fixtures/{fixture_id}/broadcasts",
    response_model=list[BroadcastResponse],
)
async def get_fixture_broadcasts(
    fixture_id: int,
    country: str = "SE",
    db: AsyncSession = Depends(get_db),
):
    """Return TV / streaming broadcasts for a fixture in the given country."""
    result = await db.execute(
        select(FixtureBroadcast)
        .where(FixtureBroadcast.fixture_id == fixture_id)
        .where(FixtureBroadcast.country_iso_2 == country.upper())
        .order_by(FixtureBroadcast.provider_type, FixtureBroadcast.channel_name)
    )
    return result.scalars().all()


# ── Predictions ────────────────────────────────────────────


@router.get("/predictions/today", response_model=list[PredictionResponse])
async def get_todays_predictions(db: AsyncSession = Depends(get_db)):
    """Get ML predictions for today's matches."""
    predictions = await db_service.get_predictions_for_date(db, date.today())
    return predictions


@router.get("/predictions/accuracy")
async def get_prediction_accuracy(
    league_id: int | None = None,
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive model accuracy stats over the last N days.

    Returns overall accuracy, per-league breakdown, calibration,
    value bet performance, and model version info.
    """
    from sqlalchemy import select, func, and_, case
    from app.models.models import Prediction, Fixture, League

    cutoff = datetime.utcnow() - __import__("datetime").timedelta(days=days)

    # ── Overall accuracy ──
    base_filter = and_(
        Prediction.created_at >= cutoff,
        Prediction.was_correct.is_not(None),
    )
    query = (
        select(
            func.count(Prediction.id).label("total"),
            func.sum(case((Prediction.was_correct.is_(True), 1), else_=0)).label(
                "correct"
            ),
            func.avg(Prediction.confidence).label("avg_confidence"),
        )
        .join(Fixture)
        .where(base_filter)
    )
    if league_id:
        query = query.where(Fixture.league_id == league_id)

    result = await db.execute(query)
    row = result.one()
    total = row.total or 0
    correct = row.correct or 0
    accuracy = (correct / total * 100) if total > 0 else 0.0

    # ── Per-league breakdown ──
    league_query = (
        select(
            Fixture.league_id,
            League.name.label("league_name"),
            func.count(Prediction.id).label("total"),
            func.sum(case((Prediction.was_correct.is_(True), 1), else_=0)).label(
                "correct"
            ),
        )
        .join(Fixture, Prediction.fixture_id == Fixture.id)
        .join(League, Fixture.league_id == League.id)
        .where(base_filter)
        .group_by(Fixture.league_id, League.name)
        .order_by(func.count(Prediction.id).desc())
    )
    league_result = await db.execute(league_query)
    per_league = [
        {
            "league_id": r.league_id,
            "league_name": r.league_name,
            "total": r.total,
            "correct": r.correct or 0,
            "accuracy": round((r.correct or 0) / r.total * 100, 2) if r.total else 0,
        }
        for r in league_result.all()
    ]

    # ── Value bet performance ──
    vb_query = (
        select(
            func.count(Prediction.id).label("total"),
            func.sum(case((Prediction.was_correct.is_(True), 1), else_=0)).label(
                "correct"
            ),
            func.avg(Prediction.value_edge).label("avg_edge"),
        )
        .join(Fixture)
        .where(
            base_filter,
            Prediction.value_edge.is_not(None),
            Prediction.value_edge > 0,
        )
    )
    vb_result = await db.execute(vb_query)
    vb_row = vb_result.one()
    vb_total = vb_row.total or 0
    vb_correct = vb_row.correct or 0

    # ── Model version info ──
    version_query = (
        select(
            Prediction.model_version,
            func.count(Prediction.id).label("count"),
            func.sum(case((Prediction.was_correct.is_(True), 1), else_=0)).label(
                "correct"
            ),
        )
        .where(base_filter)
        .group_by(Prediction.model_version)
        .order_by(func.count(Prediction.id).desc())
    )
    version_result = await db.execute(version_query)
    per_version = [
        {
            "version": r.model_version,
            "predictions": r.count,
            "correct": r.correct or 0,
            "accuracy": round((r.correct or 0) / r.count * 100, 2) if r.count else 0,
        }
        for r in version_result.all()
    ]

    return {
        "period_days": days,
        "overall": {
            "total_predictions": total,
            "correct": correct,
            "accuracy": round(accuracy, 2),
            "avg_confidence": round(float(row.avg_confidence or 0), 4),
        },
        "per_league": per_league,
        "value_bets": {
            "total": vb_total,
            "correct": vb_correct,
            "accuracy": round((vb_correct / vb_total * 100) if vb_total else 0, 2),
            "avg_edge": round(float(vb_row.avg_edge or 0), 2),
        },
        "per_model_version": per_version,
    }


@router.get("/predictions/{fixture_id}", response_model=PredictionResponse)
async def get_prediction(fixture_id: int, db: AsyncSession = Depends(get_db)):
    """Get prediction for a specific fixture."""
    prediction = await db_service.get_prediction_by_fixture(db, fixture_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction


# ── Value Bets ─────────────────────────────────────────────


@router.get("/value-bets", response_model=list[ValueBetResponse])
async def get_value_bets(
    min_edge: float = Query(5.0, description="Minimum edge % to show"),
    league_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get matches where our model identifies value vs bookmaker odds."""
    from sqlalchemy import select, or_
    from app.models.models import Prediction, Fixture

    query = (
        select(Prediction)
        .join(Fixture)
        .where(
            or_(
                Prediction.is_value_home.is_(True),
                Prediction.is_value_draw.is_(True),
                Prediction.is_value_away.is_(True),
            ),
            Prediction.value_edge >= min_edge,
            Fixture.status == "scheduled",
        )
    )
    if league_id:
        query = query.where(Fixture.league_id == league_id)

    result = await db.execute(query)
    predictions = list(result.scalars().all())

    # Build value bet responses (requires fixture + odds data loaded)
    value_bets = []
    for pred in predictions:
        fixture = await db_service.get_fixture_by_id(db, pred.fixture_id)
        if not fixture or not fixture.odds:
            continue

        best_odds = fixture.odds[0]  # Use first available bookmaker
        suggested = (
            "Home" if pred.is_value_home else ("Draw" if pred.is_value_draw else "Away")
        )

        from app.ml.predictor import MatchPrediction

        model_pred = MatchPrediction(
            home_win_prob=pred.home_win_prob,
            draw_prob=pred.draw_prob,
            away_win_prob=pred.away_win_prob,
            confidence=pred.confidence,
            over_25_prob=pred.over_25_prob or 0.5,
            expected_goals=pred.expected_goals or 2.5,
        )

        kelly = 0.0
        if best_odds.home_odds and best_odds.draw_odds and best_odds.away_odds:
            from app.ml.predictor import identify_value_bets

            vb = identify_value_bets(
                model_pred,
                {
                    "home": best_odds.home_odds,
                    "draw": best_odds.draw_odds,
                    "away": best_odds.away_odds,
                },
            )
            kelly = vb.get("kelly_fraction", 0.0)

        value_bets.append(
            ValueBetResponse(
                fixture=FixtureResponse.model_validate(fixture),
                prediction=PredictionResponse.model_validate(pred),
                best_odds=OddsResponse.model_validate(best_odds),
                edge_percent=pred.value_edge or 0.0,
                suggested_bet=suggested,
                kelly_fraction=kelly,
            )
        )

    return value_bets


# ── Head to Head ───────────────────────────────────────────


@router.get("/h2h/{team1_id}/{team2_id}")
async def get_head_to_head(
    team1_id: int, team2_id: int, last: int = 10, db: AsyncSession = Depends(get_db)
):
    """Get head-to-head history and analysis between two teams."""
    fixtures = await db_service.get_h2h_fixtures(db, team1_id, team2_id, last)

    team1_wins = sum(
        1
        for f in fixtures
        if (f.home_team_id == team1_id and (f.home_goals or 0) > (f.away_goals or 0))
        or (f.away_team_id == team1_id and (f.away_goals or 0) > (f.home_goals or 0))
    )
    team2_wins = sum(
        1
        for f in fixtures
        if (f.home_team_id == team2_id and (f.home_goals or 0) > (f.away_goals or 0))
        or (f.away_team_id == team2_id and (f.away_goals or 0) > (f.home_goals or 0))
    )
    draws = len(fixtures) - team1_wins - team2_wins
    total_goals = sum((f.home_goals or 0) + (f.away_goals or 0) for f in fixtures)
    avg_goals = total_goals / len(fixtures) if fixtures else 0.0

    return {
        "team1_id": team1_id,
        "team2_id": team2_id,
        "matches": [FixtureResponse.model_validate(f) for f in fixtures],
        "summary": {
            "total_matches": len(fixtures),
            "team1_wins": team1_wins,
            "draws": draws,
            "team2_wins": team2_wins,
            "avg_goals": round(avg_goals, 2),
        },
    }


# ── Standings ──────────────────────────────────────────────


@router.get("/standings/{league_id}", response_model=list[StandingResponse])
async def get_standings(
    league_id: int, season: int | None = None, db: AsyncSession = Depends(get_db)
):
    """Get league standings with xG data."""
    standings = await db_service.get_standings(db, league_id, season)
    if not standings:
        raise HTTPException(status_code=404, detail="Standings not found")

    # We need to load the team for each standing
    result = []
    for s in standings:
        from sqlalchemy import select
        from app.models.models import Team

        team_result = await db.execute(select(Team).where(Team.id == s.team_id))
        team = team_result.scalar_one_or_none()
        if not team:
            continue
        result.append(
            StandingResponse(
                position=s.position,
                team=TeamResponse.model_validate(team),
                points=s.points,
                played=s.played,
                won=s.won,
                drawn=s.drawn,
                lost=s.lost,
                goals_for=s.goals_for,
                goals_against=s.goals_against,
                goal_diff=s.goal_diff,
                form=s.form,
                xg_for=s.xg_for,
                xg_against=s.xg_against,
            )
        )

    return result


# ── Sentiment ──────────────────────────────────────────────


@router.get("/sentiment/{team_id}", response_model=list[SentimentResponse])
async def get_team_sentiment(
    team_id: int, days: int = Query(7, ge=1, le=30), db: AsyncSession = Depends(get_db)
):
    """Get sentiment analysis for a team over the last N days."""
    scores = await db_service.get_team_sentiment(db, team_id, days)
    return scores


@router.get("/sentiment/match/{fixture_id}")
async def get_match_sentiment(fixture_id: int, db: AsyncSession = Depends(get_db)):
    """Get sentiment comparison for both teams in a fixture."""
    fixture = await db_service.get_fixture_by_id(db, fixture_id)
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    home_sentiment = await db_service.get_team_sentiment(
        db, fixture.home_team_id, days=7
    )
    away_sentiment = await db_service.get_team_sentiment(
        db, fixture.away_team_id, days=7
    )

    def avg_score(scores: list) -> float | None:
        if not scores:
            return None
        return round(sum(s.score for s in scores) / len(scores), 3)

    return {
        "fixture_id": fixture_id,
        "home_sentiment": avg_score(home_sentiment),
        "away_sentiment": avg_score(away_sentiment),
        "home_detail": [SentimentResponse.model_validate(s) for s in home_sentiment],
        "away_detail": [SentimentResponse.model_validate(s) for s in away_sentiment],
    }


# ── Admin — manual task triggers ───────────────────────────

ADMIN_EMAILS: set[str] = {"REDACTED-EMAIL", "admin@scorelock.saidborna.com"}


@router.post("/admin/trigger/{task_name}")
async def trigger_task(
    task_name: str,
    user: User = Depends(get_current_user),
):
    """Manually trigger a Celery task (admin only).

    Available tasks: standings, fixtures, predictions, sentiment, odds, train
    """
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    from app.core.celery_app import celery_app

    task_map = {
        "standings": "app.services.tasks.update_standings",
        "fixtures": "app.services.tasks.fetch_daily_fixtures",
        "predictions": "app.services.tasks.run_daily_predictions",
        "sentiment": "app.services.tasks.run_sentiment_analysis",
        "odds": "app.services.tasks.fetch_odds_updates",
        "train": "app.services.tasks.train_model",
        "content-previews": "app.services.tasks.generate_content_previews",
        "content-reports": "app.services.tasks.generate_content_reports",
        "content-round-summaries": "app.services.tasks.generate_content_round_summaries",
        "content-value-bets": "app.services.tasks.generate_content_value_bets",
        "content-news-rewrites": "app.services.tasks.generate_content_news_rewrites",
    }

    if task_name not in task_map:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown task. Choose from: {', '.join(task_map.keys())}",
        )

    result = celery_app.send_task(task_map[task_name])
    return {"status": "queued", "task_id": result.id, "task_name": task_name}


@router.get("/admin/quota")
async def get_quota_status(user: User = Depends(get_current_user)):
    """Get API quota usage across all data sources (admin only)."""
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")

    from app.core.quota_manager import get_quota_manager

    quota = get_quota_manager()
    usage = await quota.get_all_usage()
    return {"quotas": usage}


@router.get("/admin/debug/api-test")
async def debug_api_test(
    league_id: int = Query(39, description="API-Football league ID"),
    season: int = Query(2025, description="Season year"),
    user: User = Depends(get_current_user),
):
    """Test API-Football endpoint directly — returns raw JSON (admin only, 1 API call)."""
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")

    from app.services.api_football import api_football
    from app.core.config import get_settings
    from app.services.tasks import _detect_season
    import httpx

    s = get_settings()
    key = s.api_football_key
    key_status = (
        f"{key[:4]}...{key[-4:]}" if len(key) > 8 else ("SET" if key else "EMPTY")
    )

    try:
        async with httpx.AsyncClient(
            base_url=api_football.base_url,
            headers=api_football.headers,
            timeout=30.0,
        ) as client:
            resp = await client.get(
                "/fixtures", params={"league": league_id, "season": season}
            )
            data = resp.json()
            return {
                "api_key_status": key_status,
                "base_url": api_football.base_url,
                "detected_season": _detect_season(date.today().year, "premier_league"),
                "requested": {"league_id": league_id, "season": season},
                "status_code": resp.status_code,
                "errors": data.get("errors"),
                "results_count": data.get("results", 0),
                "paging": data.get("paging"),
                "first_3": data.get("response", [])[:3],
                "headers": {
                    "x-ratelimit-requests-remaining": resp.headers.get(
                        "x-ratelimit-requests-remaining"
                    ),
                    "x-ratelimit-requests-limit": resp.headers.get(
                        "x-ratelimit-requests-limit"
                    ),
                },
            }
    except Exception as exc:
        return {"error": str(exc)}


@router.post("/admin/fix-league-metadata")
async def fix_league_metadata(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """One-shot: update league display names, logos, and countries."""
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")

    from app.models.models import League as LeagueModel

    LEAGUE_META = {
        # Match by slug OR display name (idempotent)
        "premier_league": {
            "display": "Premier League",
            "logo_url": "https://crests.football-data.org/PL.png",
            "country": "England",
            "league_type": "league",
        },
        "Premier League": {
            "display": "Premier League",
            "logo_url": "https://crests.football-data.org/PL.png",
            "country": "England",
            "league_type": "league",
        },
        "la_liga": {
            "display": "La Liga",
            "logo_url": "https://crests.football-data.org/laliga.png",
            "country": "Spain",
            "league_type": "league",
        },
        "La Liga": {
            "display": "La Liga",
            "logo_url": "https://crests.football-data.org/laliga.png",
            "country": "Spain",
            "league_type": "league",
        },
        "serie_a": {
            "display": "Serie A",
            "logo_url": "https://crests.football-data.org/c111.png",
            "country": "Italy",
            "league_type": "league",
        },
        "Serie A": {
            "display": "Serie A",
            "logo_url": "https://crests.football-data.org/c111.png",
            "country": "Italy",
            "league_type": "league",
        },
        "bundesliga": {
            "display": "Bundesliga",
            "logo_url": "https://crests.football-data.org/BL1.png",
            "country": "Germany",
            "league_type": "league",
        },
        "Bundesliga": {
            "display": "Bundesliga",
            "logo_url": "https://crests.football-data.org/BL1.png",
            "country": "Germany",
            "league_type": "league",
        },
        "ligue_1": {
            "display": "Ligue 1",
            "logo_url": "https://crests.football-data.org/FL1.png",
            "country": "France",
            "league_type": "league",
        },
        "Ligue 1": {
            "display": "Ligue 1",
            "logo_url": "https://crests.football-data.org/FL1.png",
            "country": "France",
            "league_type": "league",
        },
        "champions_league": {
            "display": "Champions League",
            "logo_url": "https://crests.football-data.org/CL.png",
            "country": "Europe",
            "league_type": "cup",
        },
        "Champions League": {
            "display": "Champions League",
            "logo_url": "https://crests.football-data.org/CL.png",
            "country": "Europe",
            "league_type": "cup",
        },
        "europa_league": {
            "display": "Europa League",
            "logo_url": "https://crests.football-data.org/CL.png",
            "country": "Europe",
            "league_type": "cup",
        },
        "Europa League": {
            "display": "Europa League",
            "logo_url": "https://crests.football-data.org/CL.png",
            "country": "Europe",
            "league_type": "cup",
        },
        "conference_league": {
            "display": "Conference League",
            "logo_url": "https://crests.football-data.org/CL.png",
            "country": "Europe",
            "league_type": "cup",
        },
        "Conference League": {
            "display": "Conference League",
            "logo_url": "https://crests.football-data.org/CL.png",
            "country": "Europe",
            "league_type": "cup",
        },
        "allsvenskan": {
            "display": "Allsvenskan",
            "logo_url": "https://crests.football-data.org/BL1.png",
            "country": "Sweden",
            "league_type": "league",
        },
        "Allsvenskan": {
            "display": "Allsvenskan",
            "logo_url": "https://crests.football-data.org/BL1.png",
            "country": "Sweden",
            "league_type": "league",
        },
    }

    updated = []
    from sqlalchemy import select

    result = await db.execute(select(LeagueModel))
    leagues = list(result.scalars().all())

    for league in leagues:
        meta = LEAGUE_META.get(league.name)
        if meta:
            league.logo_url = meta["logo_url"]
            league.country = meta["country"]
            league.type = meta["league_type"]
            league.name = meta["display"]
            updated.append(meta["display"])

    await db.commit()
    return {"updated": updated}


@router.get("/admin/debug/db-stats")
async def debug_db_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get database fixture/standings counts by season (admin only)."""
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")

    from sqlalchemy import func, select as sa_select
    from app.models.models import Fixture, Standing, League, Team

    # Count fixtures by season
    fixture_stats = await db.execute(
        sa_select(Fixture.season, func.count(Fixture.id))
        .group_by(Fixture.season)
        .order_by(Fixture.season.desc())
    )
    fixtures_by_season = [{"season": s, "count": c} for s, c in fixture_stats.all()]

    # Count standings by season
    standing_stats = await db.execute(
        sa_select(Standing.season, func.count(Standing.id))
        .group_by(Standing.season)
        .order_by(Standing.season.desc())
    )
    standings_by_season = [{"season": s, "count": c} for s, c in standing_stats.all()]

    # League count
    league_count = await db.execute(sa_select(func.count(League.id)))
    team_count = await db.execute(sa_select(func.count(Team.id)))

    # Date range of fixtures
    date_range = await db.execute(
        sa_select(func.min(Fixture.kickoff), func.max(Fixture.kickoff))
    )
    min_date, max_date = date_range.one()

    return {
        "fixtures_by_season": fixtures_by_season,
        "standings_by_season": standings_by_season,
        "total_leagues": league_count.scalar(),
        "total_teams": team_count.scalar(),
        "fixture_date_range": {
            "earliest": str(min_date) if min_date else None,
            "latest": str(max_date) if max_date else None,
        },
    }


@router.post("/admin/sync-now")
async def admin_sync_now(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch fixtures + standings synchronously via football-data.org (admin only).
    Uses ~11 football-data.org calls (6 fixtures + 5 standings). Current season!
    """
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")

    from app.services.football_data import (
        football_data,
        FD_COMPETITIONS,
        FootballDataClient,
    )
    from app.services.api_football import LEAGUE_IDS, PHASE_1_LEAGUES
    from app.services.db_service import (
        upsert_fixtures_batch,
        get_league_by_api_id,
        upsert_league,
        upsert_standing,
    )
    from app.services.tasks import _detect_season

    current_year = date.today().year
    results = {
        "fixtures": {},
        "standings": {},
        "errors": [],
        "source": "football-data.org",
    }

    # Build reverse map
    fd_name_to_code = {v["name"]: code for code, v in FD_COMPETITIONS.items()}

    # ── Fixtures ──
    for league_name in PHASE_1_LEAGUES:
        api_id = LEAGUE_IDS[league_name]
        league = await get_league_by_api_id(db, api_id)
        if not league:
            league = await upsert_league(
                db,
                api_id=api_id,
                name=league_name,
                country=league_name,
                logo_url=None,
                league_type="cup"
                if league_name
                in ("champions_league", "europa_league", "conference_league")
                else "league",
                current_season=current_year,
            )

        fd_code = fd_name_to_code.get(league_name)
        if not fd_code:
            results["fixtures"][league_name] = {
                "skipped": True,
                "reason": "Not in football-data.org",
            }
            continue

        try:
            matches = await football_data.get_matches(fd_code)
            normalized = [
                FootballDataClient.normalize_match_to_fixture(m, api_id)
                for m in matches
            ]
            normalized = [n for n in normalized if n]
            if normalized:
                count = await upsert_fixtures_batch(db, normalized, league)
                results["fixtures"][league_name] = {
                    "fetched": len(matches),
                    "upserted": count,
                }
            else:
                results["fixtures"][league_name] = {
                    "fetched": 0,
                    "error": "empty after normalization",
                }
        except Exception as exc:
            results["errors"].append(f"{league_name}: {str(exc)}")

    # ── Standings (domestic leagues only) ──
    STANDINGS_LEAGUES = ["premier_league", "la_liga", "serie_a", "bundesliga"]
    for league_name in STANDINGS_LEAGUES:
        api_id = LEAGUE_IDS[league_name]
        league = await get_league_by_api_id(db, api_id)
        if not league:
            continue

        fd_code = fd_name_to_code.get(league_name)
        if not fd_code:
            continue

        season = _detect_season(current_year, league_name)

        try:
            standings = await football_data.get_standings(fd_code)
            count = 0
            for entry in standings:
                normalized = FootballDataClient.normalize_standing(entry, fd_code)
                result = await upsert_standing(db, normalized, league, season)
                if result:
                    count += 1
            results["standings"][league_name] = {"season": season, "count": count}
        except Exception as exc:
            results["errors"].append(f"standings/{league_name}: {str(exc)}")

    await db.commit()
    return results


# ── Articles (AI Content Engine) ──────────────────────────


@router.get("/articles", response_model=ArticleListResponse)
async def list_articles(
    article_type: str | None = Query(
        None,
        description="Filter by type: MATCH_PREVIEW, MATCH_REPORT, ROUND_SUMMARY, VALUE_BET_ALERT, NEWS_REWRITE",
    ),
    league_id: int | None = Query(None, description="Filter by league ID"),
    language: str | None = Query(None, description="Filter by language (e.g. sv)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List published articles with optional filters."""
    a_type = None
    if article_type:
        try:
            a_type = ArticleType(article_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid type. Choose from: {[t.value for t in ArticleType]}",
            )

    articles = await db_service.get_articles(
        db, a_type, league_id, language, limit, offset
    )
    total = await db_service.count_articles(db, a_type, league_id)
    return ArticleListResponse(
        articles=[ArticleResponse.model_validate(a) for a in articles],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/articles/{slug}", response_model=ArticleResponse)
async def get_article(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single article by slug."""
    article = await db_service.get_article_by_slug(db, slug)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return ArticleResponse.model_validate(article)


# ── Affiliate System ──────────────────────────────────────


@router.get("/affiliate/links", response_model=list[AffiliateLinkResponse])
async def get_affiliate_links(
    country: str = Query("SE", description="Country code (e.g. SE, UK)"),
    bookmaker: str | None = Query(None, description="Filter by bookmaker slug"),
    db: AsyncSession = Depends(get_db),
):
    """Get active affiliate links for a given country."""
    links = await db_service.get_affiliate_links(db, country, bookmaker)
    return [AffiliateLinkResponse.model_validate(link) for link in links]


@router.post("/affiliate/click", response_model=AffiliateClickResponse)
async def record_click(
    click: AffiliateClickCreate,
    request: Request,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Record an affiliate link click (called by frontend before redirect)."""
    import hashlib

    ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
    ua = request.headers.get("user-agent", "")[:500]

    result = await db_service.record_affiliate_click(
        db,
        link_id=click.link_id,
        fixture_id=click.fixture_id,
        user_id=user.id if user else None,
        page_source=click.page_source,
        ip_hash=ip_hash,
        user_agent=ua,
    )
    await db.commit()
    return AffiliateClickResponse.model_validate(result)


@router.get("/admin/affiliate/stats", response_model=list[AffiliateStatsResponse])
async def get_affiliate_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get affiliate click statistics (admin only)."""
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    stats = await db_service.get_affiliate_stats(db)
    return stats


# ── Tipping League ────────────────────────────────────────


@router.post("/tips", response_model=UserPredictionResponse)
async def create_tip(
    tip: UserPredictionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a prediction (tip) for a match. Can update before kickoff."""
    if tip.predicted_outcome not in ("H", "D", "A"):
        raise HTTPException(status_code=400, detail="outcome must be H, D, or A")
    try:
        result = await db_service.create_user_prediction(
            db,
            user_id=user.id,
            fixture_id=tip.fixture_id,
            predicted_outcome=tip.predicted_outcome,
            predicted_home_goals=tip.predicted_home_goals,
            predicted_away_goals=tip.predicted_away_goals,
        )
        await db.commit()
        return UserPredictionResponse.model_validate(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tips/mine", response_model=list[UserPredictionWithFixture])
async def get_my_tips(
    scored_only: bool = Query(False, description="Only show scored tips"),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's tips."""
    preds = await db_service.get_user_predictions(
        db, user.id, scored_only=scored_only, limit=limit
    )
    return [UserPredictionWithFixture.model_validate(p) for p in preds]


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    days: int | None = Query(
        None, description="Filter by last N days (null = all time)"
    ),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get the tipping league leaderboard."""
    return await db_service.get_leaderboard(db, limit=limit, days=days)


@router.get("/tips/ai-vs-me", response_model=AIvsUserStats)
async def ai_vs_me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compare the user's tipping accuracy against the AI model."""
    stats = await db_service.get_ai_vs_user(db, user.id)
    return stats


@router.get("/tips/weekly-top", response_model=WeeklyTopTipper | None)
async def weekly_top_tipper(
    db: AsyncSession = Depends(get_db),
):
    """Get the top tipper for the current week."""
    return await db_service.get_weekly_top_tipper(db)


# ── Prediction Cards (M8) ─────────────────────────────────


@router.get("/prediction-card/{fixture_id}")
async def get_prediction_card(
    fixture_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Generate a shareable prediction card image for a fixture.

    Returns a PNG image (1200×630 OG-image format).
    """
    from fastapi.responses import Response
    from app.models.models import Fixture, Prediction, ValueBet
    from app.services.social.prediction_card import generate_prediction_card
    from sqlalchemy import select

    # Get fixture
    result = await db.execute(select(Fixture).where(Fixture.id == fixture_id))
    fixture = result.scalar_one_or_none()
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    # Get prediction
    pred_result = await db.execute(
        select(Prediction).where(Prediction.fixture_id == fixture_id)
    )
    pred = pred_result.scalar_one_or_none()

    # Get value bet
    vb_result = await db.execute(
        select(ValueBet)
        .where(ValueBet.fixture_id == fixture_id)
        .order_by(ValueBet.edge.desc())
        .limit(1)
    )
    vb = vb_result.scalar_one_or_none()

    prediction_text = "Ingen prognos tillgänglig"
    home_pct = draw_pct = away_pct = None
    if pred:
        prediction_text = pred.predicted_outcome or "—"
        home_pct = pred.home_win_probability
        draw_pct = pred.draw_probability
        away_pct = pred.away_win_probability

    value_bet_text = None
    if vb:
        value_bet_text = f"{vb.bet_type} @{vb.odds:.2f} (edge: +{vb.edge:.1f}%)"

    kickoff_str = (
        fixture.kickoff.strftime("%Y-%m-%d %H:%M UTC") if fixture.kickoff else "TBD"
    )

    image_bytes = generate_prediction_card(
        home_team=fixture.home_team,
        away_team=fixture.away_team,
        league_name=fixture.league_name or "League",
        kickoff=kickoff_str,
        prediction=prediction_text,
        home_win_pct=home_pct,
        draw_pct=draw_pct,
        away_win_pct=away_pct,
        value_bet=value_bet_text,
    )

    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Content-Disposition": f"inline; filename=scorelock-{fixture_id}.png",
        },
    )
