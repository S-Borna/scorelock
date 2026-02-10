"""API routes for ScoreLock football analytics.

All routes query the database via the db_service layer.
"""

from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
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
)
from app.services import db_service

router = APIRouter()


# ── Health ─────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    """Service health check."""
    return {"status": "ok", "service": "scorelock-api", "version": "0.1.0"}


# ── Leagues ────────────────────────────────────────────────

@router.get("/leagues", response_model=list[LeagueResponse])
async def get_leagues(db: AsyncSession = Depends(get_db)):
    """Get all active leagues covered by ScoreLock."""
    leagues = await db_service.get_all_leagues(db)
    return leagues


# ── Fixtures ───────────────────────────────────────────────

@router.get("/fixtures", response_model=list[FixtureResponse])
async def get_fixtures(
    match_date: date | None = Query(None, alias="date", description="Filter by date (YYYY-MM-DD)"),
    league_id: int | None = Query(None, description="Filter by league"),
    status: str | None = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
):
    """Get fixtures with optional filters."""
    fixtures = await db_service.get_fixtures(db, match_date=match_date, league_id=league_id, status=status)
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
        prediction=PredictionResponse.model_validate(prediction) if prediction else None,
        odds=[OddsResponse.model_validate(o) for o in fixture.odds],
    )


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
    """Get model accuracy stats over the last N days."""
    from sqlalchemy import select, func, and_
    from app.models.models import Prediction, Fixture

    cutoff = datetime.utcnow() - __import__("datetime").timedelta(days=days)

    query = (
        select(
            func.count(Prediction.id).label("total"),
            func.sum(func.cast(Prediction.was_correct, __import__("sqlalchemy").Integer)).label("correct"),
        )
        .join(Fixture)
        .where(and_(Prediction.created_at >= cutoff, Prediction.was_correct.is_not(None)))
    )
    if league_id:
        query = query.where(Fixture.league_id == league_id)

    result = await db.execute(query)
    row = result.one()
    total = row.total or 0
    correct = row.correct or 0
    accuracy = (correct / total * 100) if total > 0 else 0.0

    return {
        "period_days": days,
        "total_predictions": total,
        "correct": correct,
        "accuracy": round(accuracy, 2),
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
        suggested = "Home" if pred.is_value_home else ("Draw" if pred.is_value_draw else "Away")

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
                {"home": best_odds.home_odds, "draw": best_odds.draw_odds, "away": best_odds.away_odds},
            )
            kelly = vb.get("kelly_fraction", 0.0)

        value_bets.append(ValueBetResponse(
            fixture=FixtureResponse.model_validate(fixture),
            prediction=PredictionResponse.model_validate(pred),
            best_odds=OddsResponse.model_validate(best_odds),
            edge_percent=pred.value_edge or 0.0,
            suggested_bet=suggested,
            kelly_fraction=kelly,
        ))

    return value_bets


# ── Head to Head ───────────────────────────────────────────

@router.get("/h2h/{team1_id}/{team2_id}")
async def get_head_to_head(team1_id: int, team2_id: int, last: int = 10, db: AsyncSession = Depends(get_db)):
    """Get head-to-head history and analysis between two teams."""
    fixtures = await db_service.get_h2h_fixtures(db, team1_id, team2_id, last)

    team1_wins = sum(
        1 for f in fixtures
        if (f.home_team_id == team1_id and (f.home_goals or 0) > (f.away_goals or 0))
        or (f.away_team_id == team1_id and (f.away_goals or 0) > (f.home_goals or 0))
    )
    team2_wins = sum(
        1 for f in fixtures
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
async def get_standings(league_id: int, season: int | None = None, db: AsyncSession = Depends(get_db)):
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
        result.append(StandingResponse(
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
        ))

    return result


# ── Sentiment ──────────────────────────────────────────────

@router.get("/sentiment/{team_id}", response_model=list[SentimentResponse])
async def get_team_sentiment(team_id: int, days: int = Query(7, ge=1, le=30), db: AsyncSession = Depends(get_db)):
    """Get sentiment analysis for a team over the last N days."""
    scores = await db_service.get_team_sentiment(db, team_id, days)
    return scores


@router.get("/sentiment/match/{fixture_id}")
async def get_match_sentiment(fixture_id: int, db: AsyncSession = Depends(get_db)):
    """Get sentiment comparison for both teams in a fixture."""
    fixture = await db_service.get_fixture_by_id(db, fixture_id)
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    home_sentiment = await db_service.get_team_sentiment(db, fixture.home_team_id, days=7)
    away_sentiment = await db_service.get_team_sentiment(db, fixture.away_team_id, days=7)

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
