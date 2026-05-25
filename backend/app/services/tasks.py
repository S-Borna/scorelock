"""Celery tasks — the data pipeline that powers ScoreLock.

These tasks run on schedule (configured in celery_app.py) and keep
the database up to date with fixtures, scores, odds, and predictions.

Data source strategy:
  - football-data.org: PRIMARY for fixtures + standings (14,400 req/day free!)
    Covers: PL, La Liga, Serie A, Bundesliga, Ligue 1, CL — CURRENT SEASON
  - API-Football: Live scores only (free plan blocks current season fixtures!)
    Free plan limited to seasons 2022-2024, NOT 2025-26
  - The Odds API: All odds (40+ bookmakers, 500 req/month)

Daily football-data.org budget (~12 of 14,400 calls):
  - Fixtures: 6 calls (1/league)
  - Standings: 5 calls (1/league, skip cups)
  - Remaining: ~14,380 calls buffer
"""

import asyncio
from datetime import date, datetime, timedelta, timezone

import structlog
from app.core.celery_app import celery_app
from app.core.database import async_session, engine

logger = structlog.get_logger()


def run_async(coro):
    """Helper to run async code inside sync Celery tasks.

    Disposes the SQLAlchemy engine pool after each run så att asyncpg-
    connections inte överlever event-loop-bytet mellan Celery-task-anrop
    (som annars ger "InterfaceError: another operation in progress" när
    pool-cachade connections är bundna till en stängd event loop).
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        # Dispose pool oavsett success/fail så nästa task får ny event-loop-bunden pool.
        try:
            loop.run_until_complete(engine.dispose())
        except Exception:
            pass
        loop.close()


def _detect_season(current_year: int, league_name: str) -> int:
    """Return the correct API-Football season parameter.

    API-Football uses the START year of each campaign:
      - European leagues (PL, La Liga, etc.): 2025-2026 season → param **2025**
      - European cups (CL, EL, ECL): 2025-2026 season → param **2025**
      - Allsvenskan: calendar-year league, 2026 season → param **2026**

    Logic:
      - European: season runs Aug → May. If month >= 8 → current_year, else year-1
      - Allsvenskan: season runs Apr → Nov. If month >= 4 → current_year, else year-1
    """
    month = date.today().month

    if league_name == "allsvenskan":
        # Calendar-year league: Apr–Nov
        # Jan-Mar = previous year's season is the latest completed
        return current_year if month >= 4 else current_year - 1

    # European leagues & cups: Aug–May cycle
    # Feb 2026 → month < 8 → season = 2026-1 = 2025 (correct: 2025-26 season)
    # Sep 2026 → month >= 8 → season = 2026 (correct: 2026-27 season)
    return current_year if month >= 8 else current_year - 1


@celery_app.task(name="app.services.tasks.fetch_daily_fixtures")
def fetch_daily_fixtures():
    """Fetch fixtures — football-data.org PRIMARY (current season), API-Football fallback.

    Strategy (after discovering API-Football free plan blocks current season):
      - football-data.org: PRIMARY for PL, La Liga, Serie A, Bundesliga, Ligue 1, CL
        → free tier, 14400 req/day, HAS current 2025-26 season
      - API-Football: FALLBACK only for leagues not in football-data.org
        → free plan limited to seasons 2022-2024, NO current season access
    Budget: ~6 football-data.org calls (1/league), 0 API-Football calls
    """

    async def _fetch():
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
        )

        total = 0
        current_year = date.today().year

        # Build reverse map: league_name → FD competition code
        fd_name_to_code = {v["name"]: code for code, v in FD_COMPETITIONS.items()}

        async with async_session() as session:
            # ── 1. football-data.org — PRIMARY source (current season!) ──
            for league_name in PHASE_1_LEAGUES:
                api_id = LEAGUE_IDS[league_name]
                league = await get_league_by_api_id(session, api_id)
                if not league:
                    league = await upsert_league(
                        session,
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
                if fd_code:
                    # football-data.org covers this league — use it!
                    try:
                        # Fetch ALL matches (not just upcoming) for full season data
                        matches = await football_data.get_matches(fd_code)
                        normalized = [
                            FootballDataClient.normalize_match_to_fixture(m, api_id)
                            for m in matches
                        ]
                        normalized = [n for n in normalized if n]
                        if normalized:
                            count = await upsert_fixtures_batch(
                                session, normalized, league
                            )
                            total += count
                            logger.info(
                                "fixtures_synced",
                                source="football_data",
                                league=league_name,
                                count=count,
                                total_returned=len(matches),
                            )
                        else:
                            logger.warning(
                                "fixtures_empty",
                                source="football_data",
                                league=league_name,
                            )
                    except Exception as exc:
                        logger.error(
                            "fixture_fetch_failed",
                            source="football_data",
                            league=league_name,
                            error=str(exc),
                        )
                else:
                    # League not in football-data.org (allsvenskan, europa_league, conference_league)
                    # API-Football free plan can't access current season either, so skip for now
                    logger.info(
                        "league_skipped_no_source",
                        league=league_name,
                        reason="Not in football-data.org free tier, API-Football free blocks current season",
                    )

            await session.commit()

        return total

    count = run_async(_fetch())
    return {"status": "ok", "fixtures_processed": count}


@celery_app.task(name="app.services.tasks.update_live_scores")
def update_live_scores():
    """Update scores for currently live matches (API-Football only — needs live data)."""

    async def _update():
        from app.services.api_football import api_football
        from app.services.db_service import upsert_fixture, get_league_by_api_id
        from app.core.quota_manager import get_quota_manager

        quota = get_quota_manager()
        if not await quota.can_call("api_football"):
            logger.warning("api_football_quota_exhausted", task="update_live_scores")
            return 0

        try:
            await quota.record_call("api_football")
            live = await api_football.get_live_fixtures()
        except Exception as exc:
            logger.error("live_fetch_failed", error=str(exc))
            return 0

        if not live:
            return 0

        updated = 0
        async with async_session() as session:
            for fixture_data in live:
                league_api_id = fixture_data.get("league", {}).get("id")
                if not league_api_id:
                    continue

                league = await get_league_by_api_id(session, league_api_id)
                if not league:
                    continue  # Not a league we track

                result = await upsert_fixture(session, fixture_data, league)
                if result:
                    updated += 1

                    # Publish live update via WebSocket
                    try:
                        from app.api.websocket import publish_score_update

                        goals = fixture_data.get("goals", {})
                        status_info = fixture_data.get("fixture", {}).get("status", {})
                        publish_score_update(
                            fixture_id=result.id,
                            home_goals=goals.get("home", 0) or 0,
                            away_goals=goals.get("away", 0) or 0,
                            status=result.status.value
                            if hasattr(result.status, "value")
                            else str(result.status),
                            minute=status_info.get("elapsed"),
                        )
                    except Exception as exc:
                        logger.warning("ws_publish_failed", error=str(exc))

            await session.commit()

        logger.info("live_scores_updated", count=updated)
        return updated

    count = run_async(_update())
    return {"status": "ok", "updated": count}


@celery_app.task(name="app.services.tasks.fetch_odds_updates")
def fetch_odds_updates():
    """Fetch odds from The Odds API (40+ bookmakers) — replaces API-Football odds.

    Strategy: One call per league fetches ALL upcoming match odds.
    500 req/month budget → ~2 calls/league × 8 leagues × 2/day = ~32 req/day = 960/month
    So we only run this 1-2x/day, controlled by Celery Beat.
    """

    async def _fetch():
        from app.services.odds_api import odds_api, ODDS_SPORT_KEYS, OddsAPIClient
        from app.services.db_service import upsert_odds, get_league_by_api_id
        from app.models.models import Fixture, MatchStatus
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.core.quota_manager import get_quota_manager

        quota = get_quota_manager()
        total_odds = 0

        async with async_session() as session:
            for sport_key, info in ODDS_SPORT_KEYS.items():
                if not await quota.can_call("the_odds_api"):
                    logger.warning("odds_api_quota_exhausted")
                    break

                api_football_id = info["api_football_id"]
                league = await get_league_by_api_id(session, api_football_id)
                if not league:
                    continue

                try:
                    # Single call gets h2h + totals for all upcoming matches
                    events = await odds_api.get_h2h_and_totals(sport_key)
                except Exception as exc:
                    logger.error(
                        "odds_fetch_failed", league=info["name"], error=str(exc)
                    )
                    continue

                if not events:
                    continue

                # Build fixture name map for matching
                from datetime import datetime

                result = await session.execute(
                    select(Fixture)
                    .where(
                        Fixture.league_id == league.id,
                        Fixture.status == MatchStatus.SCHEDULED,
                        Fixture.kickoff >= datetime.utcnow(),
                    )
                    .options(
                        selectinload(Fixture.home_team),
                        selectinload(Fixture.away_team),
                    )
                )
                fixtures = list(result.scalars().all())

                # Create name → fixture_id map
                name_map: dict[str, int] = {}
                for f in fixtures:
                    if f.home_team and f.away_team:
                        key = f"{f.home_team.name.lower().strip()} vs {f.away_team.name.lower().strip()}"
                        name_map[key] = f.id

                for event in events:
                    fixture_id = OddsAPIClient.match_event_to_fixture(event, name_map)
                    if not fixture_id:
                        continue

                    best = OddsAPIClient.extract_best_odds(event)

                    # Store 1X2 odds (best across all bookmakers)
                    if best["home_odds"] and best["draw_odds"] and best["away_odds"]:
                        await upsert_odds(
                            session,
                            fixture_id=fixture_id,
                            bookmaker=f"Best ({best['home_bookmaker']})",
                            market="1X2",
                            home_odds=best["home_odds"],
                            draw_odds=best["draw_odds"],
                            away_odds=best["away_odds"],
                        )
                        total_odds += 1

                    # Store individual bookmaker odds too
                    for bm in event.get("bookmakers", []):
                        bm_name = bm.get("title", "Unknown")
                        for market in bm.get("markets", []):
                            market_key = market.get("key", "")
                            outcomes = {
                                o["name"]: o.get("price", 0)
                                for o in market.get("outcomes", [])
                            }

                            if market_key == "h2h":
                                home_team = event.get("home_team", "")
                                away_team = event.get("away_team", "")
                                await upsert_odds(
                                    session,
                                    fixture_id=fixture_id,
                                    bookmaker=bm_name,
                                    market="1X2",
                                    home_odds=outcomes.get(home_team),
                                    draw_odds=outcomes.get("Draw"),
                                    away_odds=outcomes.get(away_team),
                                )
                                total_odds += 1

                            elif market_key == "totals":
                                for o in market.get("outcomes", []):
                                    point = o.get("point", 0)
                                    if point == 2.5:
                                        await upsert_odds(
                                            session,
                                            fixture_id=fixture_id,
                                            bookmaker=bm_name,
                                            market="Over/Under 2.5",
                                            over_odds=outcomes.get("Over"),
                                            under_odds=outcomes.get("Under"),
                                            line=2.5,
                                        )

                logger.info("odds_synced", league=info["name"], events=len(events))

            await session.commit()

        logger.info("odds_sync_complete", total_odds=total_odds)
        return total_odds

    count = run_async(_fetch())
    return {"status": "ok", "odds_updated": count}


@celery_app.task(name="app.services.tasks.run_daily_predictions")
def run_daily_predictions():
    """Run ML predictions for upcoming matches using trained model."""

    async def _predict():
        from app.ml.predictor import get_predictor, identify_value_bets
        from app.ml.features import FeatureComputer
        from app.services.db_service import (
            get_finished_fixtures_for_training,
            get_upcoming_fixtures_for_prediction,
            upsert_prediction,
            update_prediction_results,
        )

        predictor = get_predictor()
        if not predictor.is_loaded:
            logger.warning("model_not_loaded", reason="No trained model found")
            return {"status": "skipped", "reason": "model_not_loaded"}

        async with async_session() as session:
            # 1. Update results for past predictions
            updated = await update_prediction_results(session)
            if updated:
                logger.info("prediction_results_updated", count=updated)

            # 2. Load historical fixtures to populate feature computer
            finished = await get_finished_fixtures_for_training(session)
            computer = FeatureComputer()
            computer.populate_from_fixtures(finished)

            # 3. Get upcoming fixtures without predictions
            upcoming = await get_upcoming_fixtures_for_prediction(session)
            if not upcoming:
                logger.info("no_upcoming_fixtures")
                await session.commit()
                return {"status": "ok", "predictions": 0, "results_updated": updated}

            # 4. Generate predictions
            predicted = 0
            for fixture in upcoming:
                try:
                    prediction = predictor.predict_match(
                        computer,
                        fixture.home_team_id,
                        fixture.away_team_id,
                        fixture.kickoff,
                        fixture.season,
                    )

                    # Check for value bets using best available odds
                    is_value_home = False
                    is_value_draw = False
                    is_value_away = False
                    value_edge = None

                    odds_1x2 = [o for o in fixture.odds if o.market == "1X2"]
                    if odds_1x2:
                        # Find best odds across all bookmakers
                        best_home = max(
                            (o.home_odds for o in odds_1x2 if o.home_odds), default=0
                        )
                        best_draw = max(
                            (o.draw_odds for o in odds_1x2 if o.draw_odds), default=0
                        )
                        best_away = max(
                            (o.away_odds for o in odds_1x2 if o.away_odds), default=0
                        )

                        if best_home and best_draw and best_away:
                            vb = identify_value_bets(
                                prediction,
                                {
                                    "home": best_home,
                                    "draw": best_draw,
                                    "away": best_away,
                                },
                            )
                            is_value_home = vb.get("is_value_home", False)
                            is_value_draw = vb.get("is_value_draw", False)
                            is_value_away = vb.get("is_value_away", False)
                            value_edge = vb.get("value_edge")

                    await upsert_prediction(
                        session,
                        fixture_id=fixture.id,
                        home_win_prob=prediction.home_win_prob,
                        draw_prob=prediction.draw_prob,
                        away_win_prob=prediction.away_win_prob,
                        confidence=prediction.confidence,
                        over_25_prob=prediction.over_25_prob,
                        expected_goals=prediction.expected_goals,
                        model_version=prediction.model_version,
                        is_value_home=is_value_home,
                        is_value_draw=is_value_draw,
                        is_value_away=is_value_away,
                        value_edge=value_edge,
                    )
                    predicted += 1

                except Exception as exc:
                    logger.error(
                        "prediction_failed",
                        fixture_id=fixture.id,
                        error=str(exc),
                    )

            await session.commit()

        logger.info("daily_predictions_complete", predicted=predicted)
        return {"status": "ok", "predictions": predicted, "results_updated": updated}

    return run_async(_predict())


@celery_app.task(name="app.services.tasks.run_sentiment_analysis")
def run_sentiment_analysis():
    """Run LLM sentiment analysis on teams with upcoming fixtures."""

    async def _analyze():
        from app.services.sentiment import get_sentiment_analyzer
        from app.services.news_fetcher import (
            fetch_team_news,
            format_articles_for_analysis,
        )
        from app.services.db_service import get_upcoming_fixtures_for_prediction
        from app.models.models import SentimentScore

        analyzer = get_sentiment_analyzer()
        analyzed = 0

        async with async_session() as session:
            upcoming = await get_upcoming_fixtures_for_prediction(session, days_ahead=3)

            team_ids_done: set[int] = set()
            for fixture in upcoming:
                for team, team_id in [
                    (fixture.home_team, fixture.home_team_id),
                    (fixture.away_team, fixture.away_team_id),
                ]:
                    if team_id in team_ids_done:
                        continue
                    team_ids_done.add(team_id)

                    team_name = team.name if team else f"Team {team_id}"

                    # Fetch real news articles about this team
                    try:
                        articles = await fetch_team_news(team_name)
                    except Exception as exc:
                        logger.warning(
                            "news_fetch_failed", team=team_name, error=str(exc)
                        )
                        articles = []

                    if not articles:
                        logger.info("sentiment_no_news", team=team_name)
                        continue

                    news_text = format_articles_for_analysis(articles)

                    try:
                        result = await analyzer.analyze_text(team_name, news_text)
                    except RuntimeError:
                        logger.warning(
                            "sentiment_skipped", reason="anthropic_key_missing"
                        )
                        return {"status": "skipped", "reason": "anthropic_key_missing"}
                    except Exception as exc:
                        logger.error("sentiment_failed", team=team_name, error=str(exc))
                        continue

                    score = SentimentScore(
                        team_id=team_id,
                        fixture_id=fixture.id,
                        score=result["score"],
                        buzz_score=result["buzz_score"],
                        source="llm_analysis",
                        summary=result.get("summary"),
                        raw_data=result,
                    )
                    session.add(score)
                    analyzed += 1

            await session.commit()

        logger.info("sentiment_analysis_complete", teams_analyzed=analyzed)
        return {"status": "ok", "analyzed": analyzed}

    return run_async(_analyze())


@celery_app.task(name="app.services.tasks.update_standings")
def update_standings():
    """Update league standings — football-data.org PRIMARY (current season!).

    football-data.org: PRIMARY for PL, La Liga, Serie A, Bundesliga, Ligue 1
    API-Football free plan cannot access current season standings.
    """

    async def _update():
        from app.services.football_data import (
            football_data,
            FD_COMPETITIONS,
            FootballDataClient,
        )
        from app.services.api_football import LEAGUE_IDS, PHASE_1_LEAGUES
        from app.services.db_service import upsert_standing, get_league_by_api_id

        current_year = date.today().year
        total = 0

        # Build reverse map: league_name → FD competition code
        fd_name_to_code = {v["name"]: code for code, v in FD_COMPETITIONS.items()}

        async with async_session() as session:
            for league_name in PHASE_1_LEAGUES:
                api_id = LEAGUE_IDS[league_name]
                league = await get_league_by_api_id(session, api_id)
                if not league:
                    continue

                # Skip cups without traditional standings
                if league_name in (
                    "champions_league",
                    "europa_league",
                    "conference_league",
                ):
                    continue

                fd_code = fd_name_to_code.get(league_name)
                if not fd_code:
                    # League not in football-data.org (e.g. allsvenskan)
                    logger.info(
                        "standings_skipped",
                        league=league_name,
                        reason="Not in football-data.org free tier",
                    )
                    continue

                try:
                    standings = await football_data.get_standings(fd_code)
                except Exception as exc:
                    logger.error(
                        "standings_fetch_failed",
                        source="football_data",
                        league=league_name,
                        error=str(exc),
                    )
                    continue

                if standings:
                    season = _detect_season(current_year, league_name)
                    for entry in standings:
                        normalized = FootballDataClient.normalize_standing(
                            entry, fd_code
                        )
                        result = await upsert_standing(
                            session, normalized, league, season
                        )
                        if result:
                            total += 1
                    logger.info(
                        "standings_synced",
                        source="football_data",
                        league=league_name,
                        season=season,
                        teams=len(standings),
                    )
                else:
                    logger.warning(
                        "standings_empty", source="football_data", league=league_name
                    )

            await session.commit()

        return total

    count = run_async(_update())
    return {"status": "ok", "standings_updated": count}


@celery_app.task(name="app.services.tasks.seed_data")
def seed_data():
    """One-time seed task — fetch leagues and teams from API-Football."""

    async def _seed():
        from app.services.seed import seed_all

        await seed_all()

    run_async(_seed())
    return {"status": "ok"}


@celery_app.task(name="app.services.tasks.train_model")
def train_model():
    """Train/retrain the ML prediction model from historical data."""

    async def _train():
        from app.ml.trainer import run_training_pipeline

        return await run_training_pipeline()

    return run_async(_train())


@celery_app.task(name="app.services.tasks.fetch_historical_data")
def fetch_historical_data():
    """Fetch historical fixtures and standings from API-Football."""

    async def _fetch():
        from app.services.historical import (
            fetch_historical_fixtures,
            fetch_historical_standings,
        )

        fixtures = await fetch_historical_fixtures()
        standings = await fetch_historical_standings()
        return {
            "status": "ok",
            "fixtures": fixtures["total_fixtures"],
            "standings": standings["total_standings"],
            "api_requests": fixtures["total_requests"] + standings["total_requests"],
        }

    return run_async(_fetch())


# ══════════════════════════════════════════════════════════
# AI Content Engine Tasks  (M3)
# ══════════════════════════════════════════════════════════


@celery_app.task(name="app.services.tasks.generate_content_previews")
def generate_content_previews():
    """Generate match previews for tomorrow's fixtures.

    Runs daily at 10:00 UTC — generates Swedish AI-articles for
    every scheduled fixture in the next 24 hours.
    """

    async def _gen():
        from app.services.content_generator import generate_match_preview
        from app.services.db_service import get_fixtures

        created = 0
        async with async_session() as session:
            fixtures = await get_fixtures(
                session, days_ahead=1, league_id=None, status="scheduled"
            )
            for fixture in fixtures:
                article = await generate_match_preview(session, fixture)
                if article:
                    created += 1
        return {"status": "ok", "previews_created": created}

    return run_async(_gen())


@celery_app.task(name="app.services.tasks.generate_content_reports")
def generate_content_reports():
    """Generate match reports for recently finished fixtures.

    Runs every hour during match hours — picks up fixtures that
    finished within the last 3 hours and generates reports.
    """

    async def _gen():
        from app.services.content_generator import generate_match_report
        from app.models.models import MatchStatus, Fixture
        from sqlalchemy import select

        created = 0
        cutoff = datetime.now(timezone.utc) - timedelta(hours=3)
        async with async_session() as session:
            q = (
                select(Fixture)
                .where(
                    Fixture.status == MatchStatus.FINISHED,
                    Fixture.updated_at >= cutoff,
                )
                .order_by(Fixture.kickoff.desc())
            )
            result = await session.execute(q)
            fixtures = list(result.scalars().all())

            for fixture in fixtures:
                article = await generate_match_report(session, fixture)
                if article:
                    created += 1
        return {"status": "ok", "reports_created": created}

    return run_async(_gen())


@celery_app.task(name="app.services.tasks.generate_content_round_summaries")
def generate_content_round_summaries():
    """Generate round summaries for completed rounds.

    Runs daily at 04:00 UTC — checks each league for rounds
    where all fixtures are finished but no summary exists yet.
    """

    async def _gen():
        from app.services.content_generator import generate_round_summary
        from app.services.db_service import get_all_leagues
        from app.models.models import Fixture, MatchStatus
        from sqlalchemy import select, func

        created = 0
        async with async_session() as session:
            leagues = await get_all_leagues(session)
            for league in leagues:
                # Find rounds with all fixtures finished
                rounds_q = await session.execute(
                    select(Fixture.round)
                    .where(Fixture.league_id == league.id)
                    .group_by(Fixture.round)
                    .having(
                        func.count(Fixture.id)
                        == func.count(
                            func.nullif(Fixture.status != MatchStatus.FINISHED, True)
                        )
                    )
                )
                rounds_done = [r[0] for r in rounds_q.all() if r[0]]

                for round_str in rounds_done[-3:]:  # Last 3 completed rounds
                    article = await generate_round_summary(
                        session, league.id, round_str
                    )
                    if article:
                        created += 1

        return {"status": "ok", "summaries_created": created}

    return run_async(_gen())


@celery_app.task(name="app.services.tasks.generate_content_value_bets")
def generate_content_value_bets():
    """Generate daily value bet article.

    Runs daily at 09:00 UTC — analyses all upcoming fixtures (next 48h)
    and creates a value bet article if any value bets are found.
    """

    async def _gen():
        from app.services.content_generator import generate_value_bet_article

        async with async_session() as session:
            article = await generate_value_bet_article(session)
            return {
                "status": "ok",
                "created": article is not None,
                "slug": article.slug if article else None,
            }

    return run_async(_gen())


@celery_app.task(name="app.services.tasks.generate_content_news_rewrites")
def generate_content_news_rewrites():
    """Fetch RSS news and rewrite as original Swedish articles.

    Runs every 4 hours — fetches top stories from 10 RSS feeds,
    deduplicates, and rewrites as Swedish articles.
    """

    async def _gen():
        from app.services.content_generator import generate_news_rewrite
        from app.services.news_fetcher import fetch_team_news

        created = 0
        top_teams = [
            "Arsenal",
            "Manchester City",
            "Liverpool",
            "Barcelona",
            "Real Madrid",
            "Bayern Munich",
            "Inter",
            "PSG",
        ]

        async with async_session() as session:
            for team in top_teams:
                articles = await fetch_team_news(team)
                for art in articles[:2]:  # Max 2 per team per run
                    if len(art.get("content", "")) < 100:
                        continue
                    article = await generate_news_rewrite(
                        session,
                        source=art.get("source", "Unknown"),
                        original_title=art.get("title", ""),
                        original_content=art.get("content", ""),
                        context=f"Lag: {team}",
                    )
                    if article:
                        created += 1

        return {"status": "ok", "rewrites_created": created}

    return run_async(_gen())


@celery_app.task(name="app.services.tasks.score_user_predictions")
def score_user_predictions_task():
    """Score user predictions for all recently finished matches.

    Runs every 15 min. Finds fixtures that finished but have unscored
    user predictions and scores them (3p exact, 1p correct outcome, 0p wrong).
    """

    async def _score():
        from app.services.db_service import score_user_predictions
        from app.models.models import Fixture, MatchStatus, UserPrediction

        total_scored = 0

        async with async_session() as session:
            # Find finished fixtures with unscored user predictions
            from sqlalchemy import select

            result = await session.execute(
                select(Fixture.id)
                .join(UserPrediction, UserPrediction.fixture_id == Fixture.id)
                .where(
                    Fixture.status == MatchStatus.FINISHED,
                    UserPrediction.points_earned.is_(None),
                )
                .group_by(Fixture.id)
            )
            fixture_ids = [row[0] for row in result.all()]

            for fixture_id in fixture_ids:
                count = await score_user_predictions(session, fixture_id)
                total_scored += count

            await session.commit()

        logger.info(
            "user_predictions_scored", total=total_scored, fixtures=len(fixture_ids)
        )
        return {"status": "ok", "scored": total_scored}

    return run_async(_score())


# ── Social Media Distribution (M8) ─────────────────────────


@celery_app.task(name="app.services.tasks.distribute_match_previews")
def distribute_match_previews():
    """Distribute match previews to all social channels.

    Runs daily at 10:30 UTC (after content-previews generates articles).
    Posts the top 5 previews to Twitter, Discord, Telegram, and push.
    """

    async def _distribute():
        from app.models.models import Article, ArticleType
        from app.services.social.twitter import post_match_preview_tweet
        from app.services.social.discord import post_match_preview_discord
        from app.services.social.telegram import post_match_preview_telegram
        from app.services.social.push import push_match_preview
        from sqlalchemy import select

        posted = {"twitter": 0, "discord": 0, "telegram": 0, "push": 0}
        cutoff = datetime.now(timezone.utc) - timedelta(hours=4)

        async with async_session() as session:
            result = await session.execute(
                select(Article)
                .where(
                    Article.article_type == ArticleType.MATCH_PREVIEW,
                    Article.created_at >= cutoff,
                )
                .order_by(Article.created_at.desc())
                .limit(5)
            )
            articles = list(result.scalars().all())

            for article in articles:
                # Extract match info from article context
                home = article.home_team or "Home"
                away = article.away_team or "Away"
                league = article.league_name or "League"
                fixture_id = article.fixture_id or 0
                prediction = article.title or ""
                kickoff = article.match_date or ""

                try:
                    await post_match_preview_tweet(
                        home_team=home,
                        away_team=away,
                        league=league,
                        prediction=prediction,
                        fixture_id=fixture_id,
                    )
                    posted["twitter"] += 1
                except Exception as e:
                    logger.error("twitter_post_failed", error=str(e))

                try:
                    await post_match_preview_discord(
                        home_team=home,
                        away_team=away,
                        league=league,
                        kickoff=str(kickoff),
                        prediction=prediction,
                        fixture_id=fixture_id,
                    )
                    posted["discord"] += 1
                except Exception as e:
                    logger.error("discord_post_failed", error=str(e))

                try:
                    await post_match_preview_telegram(
                        home_team=home,
                        away_team=away,
                        league=league,
                        kickoff=str(kickoff),
                        prediction=prediction,
                        fixture_id=fixture_id,
                    )
                    posted["telegram"] += 1
                except Exception as e:
                    logger.error("telegram_post_failed", error=str(e))

                try:
                    await push_match_preview(
                        home_team=home,
                        away_team=away,
                        league=league,
                        prediction=prediction,
                        fixture_id=fixture_id,
                    )
                    posted["push"] += 1
                except Exception as e:
                    logger.error("push_preview_failed", error=str(e))

        logger.info("previews_distributed", counts=posted)
        return {"status": "ok", "posted": posted}

    return run_async(_distribute())


@celery_app.task(name="app.services.tasks.distribute_value_bet_alerts")
def distribute_value_bet_alerts():
    """Distribute value bet alerts to all social channels.

    Runs daily at 09:30 UTC (after content-value-bets).
    Posts high-edge value bets (edge > 5%) to all channels.
    """

    async def _distribute():
        from app.models.models import ValueBet, Fixture
        from app.services.social.twitter import post_value_bet_alert_tweet
        from app.services.social.discord import post_value_bet_alert_discord
        from app.services.social.telegram import post_value_bet_alert_telegram
        from app.services.social.push import push_value_bet_alert
        from sqlalchemy import select

        posted = {"twitter": 0, "discord": 0, "telegram": 0, "push": 0}

        async with async_session() as session:
            result = await session.execute(
                select(ValueBet, Fixture)
                .join(Fixture, ValueBet.fixture_id == Fixture.id)
                .where(ValueBet.edge > 5.0)
                .order_by(ValueBet.edge.desc())
                .limit(5)
            )
            rows = result.all()

            for vb, fixture in rows:
                home = fixture.home_team
                away = fixture.away_team
                league = fixture.league_name or "League"
                bet_desc = f"{vb.bet_type} @{vb.odds:.2f} (edge: +{vb.edge:.1f}%)"

                try:
                    await post_value_bet_alert_tweet(
                        home_team=home,
                        away_team=away,
                        league=league,
                        bet_type=vb.bet_type,
                        odds=vb.odds,
                        edge=vb.edge,
                        fixture_id=fixture.id,
                    )
                    posted["twitter"] += 1
                except Exception as e:
                    logger.error("twitter_vb_failed", error=str(e))

                try:
                    await post_value_bet_alert_discord(
                        home_team=home,
                        away_team=away,
                        league=league,
                        bet_type=vb.bet_type,
                        odds=vb.odds,
                        edge=vb.edge,
                        fixture_id=fixture.id,
                    )
                    posted["discord"] += 1
                except Exception as e:
                    logger.error("discord_vb_failed", error=str(e))

                try:
                    await post_value_bet_alert_telegram(
                        home_team=home,
                        away_team=away,
                        league=league,
                        bet_type=vb.bet_type,
                        odds=vb.odds,
                        edge=vb.edge,
                        fixture_id=fixture.id,
                    )
                    posted["telegram"] += 1
                except Exception as e:
                    logger.error("telegram_vb_failed", error=str(e))

                try:
                    await push_value_bet_alert(
                        home_team=home,
                        away_team=away,
                        bet_description=bet_desc,
                        fixture_id=fixture.id,
                    )
                    posted["push"] += 1
                except Exception as e:
                    logger.error("push_vb_failed", error=str(e))

        logger.info("value_bets_distributed", counts=posted)
        return {"status": "ok", "posted": posted}

    return run_async(_distribute())


@celery_app.task(name="app.services.tasks.distribute_match_results")
def distribute_match_results():
    """Push notifications for match results (checking prediction accuracy).

    Runs hourly during match hours. Sends push for recently finished matches.
    """

    async def _distribute():
        from app.models.models import Fixture, Prediction, MatchStatus
        from app.services.social.push import push_match_result
        from sqlalchemy import select

        sent = 0
        cutoff = datetime.now(timezone.utc) - timedelta(hours=2)

        async with async_session() as session:
            result = await session.execute(
                select(Fixture)
                .where(
                    Fixture.status == MatchStatus.FINISHED,
                    Fixture.updated_at >= cutoff,
                )
                .order_by(Fixture.kickoff.desc())
                .limit(10)
            )
            fixtures = list(result.scalars().all())

            for fixture in fixtures:
                # Check if AI predicted correctly
                pred_result = await session.execute(
                    select(Prediction).where(Prediction.fixture_id == fixture.id)
                )
                pred = pred_result.scalar_one_or_none()

                prediction_correct = False
                if (
                    pred
                    and fixture.home_score is not None
                    and fixture.away_score is not None
                ):
                    actual = (
                        "home"
                        if fixture.home_score > fixture.away_score
                        else "away"
                        if fixture.away_score > fixture.home_score
                        else "draw"
                    )
                    prediction_correct = pred.predicted_outcome == actual

                score = f"{fixture.home_score or 0}-{fixture.away_score or 0}"
                try:
                    await push_match_result(
                        home_team=fixture.home_team,
                        away_team=fixture.away_team,
                        score=score,
                        prediction_correct=prediction_correct,
                        fixture_id=fixture.id,
                    )
                    sent += 1
                except Exception as e:
                    logger.error("push_result_failed", error=str(e))

        logger.info("results_distributed", sent=sent)
        return {"status": "ok", "sent": sent}

    return run_async(_distribute())


# ── SportMonks provider sync (Phase 7.4) ───────────────────


@celery_app.task(
    name="app.services.tasks.sportmonks_sync_fixture",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=3,
)
def sportmonks_sync_fixture(self, fixture_external_id: str):
    """Sync en SportMonks-fixture end-to-end till DB.

    Static-mode (default pre-augusti): ignorerar fixture_external_id, läser
    från `/competitor-ref/sportmonks/payloads/Match Centre.json`.

    Live-mode: hämtar via SportMonks v3 API + persisterar via normalizer.

    Idempotent — re-sync av samma fixture uppdaterar mutable fält men
    skapar inga duplicat-rader (verifierat i test_sportmonks_normalizer).
    """

    async def _sync():
        from app.core.config import get_settings
        from app.providers.sportmonks import SportMonksProvider
        from app.services.sportmonks_normalizer import sync_fixture_detail

        provider = SportMonksProvider(get_settings())
        async with async_session() as session:
            try:
                fixture = await sync_fixture_detail(
                    session, provider, fixture_external_id
                )
                await session.commit()
                logger.info(
                    "sportmonks_sync_ok",
                    fixture_external_id=fixture_external_id,
                    fixture_id=fixture.id,
                    home_score=fixture.home_goals,
                    away_score=fixture.away_goals,
                    status=fixture.status.value,
                )
                return {
                    "status": "ok",
                    "fixture_id": fixture.id,
                    "external_id": fixture_external_id,
                    "score": f"{fixture.home_goals}-{fixture.away_goals}",
                    "match_status": fixture.status.value,
                }
            finally:
                await provider.aclose()

    return run_async(_sync())


@celery_app.task(
    name="app.services.tasks.sportmonks_sync_live_fixtures",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=120,
    max_retries=2,
)
def sportmonks_sync_live_fixtures(self):
    """Realtids-spine: pollar SportMonks /livescores/inplay → WS.

    Lager 1 (denna task): ETT API-anrop per cykel oavsett antal live-matcher.
    Uppdaterar score/minut/status på befintliga fixtures + publish_score_update.
    Lager 2: vid mål (score-ändring) eller okänd live-match köas
    sportmonks_sync_fixture för full event-/timeline-refresh — håller timeline
    färsk utan att bränna kvot (1 anrop/cykel istället för N×4).
    """

    async def _sync():
        from app.api.websocket import publish_score_update
        from app.core.config import get_settings
        from app.models.models import Fixture, MatchStatus
        from app.providers.sportmonks import SportMonksProvider
        from app.services.sportmonks_normalizer import get_canonical_id

        provider = SportMonksProvider(get_settings())
        try:
            live = await provider.fetch_live_fixtures()
        except Exception:
            await provider.aclose()
            raise

        if not live:
            await provider.aclose()
            return {"status": "ok", "live": 0, "published": 0}

        published = 0
        async with async_session() as session:
            try:
                for nf in live:
                    mapped_id = await get_canonical_id(
                        session, "fixture", nf.external_id
                    )
                    fixture = (
                        await session.get(Fixture, mapped_id)
                        if mapped_id is not None
                        else None
                    )

                    # Okänd live-match → köa full skapande-sync, hoppa denna cykel
                    if fixture is None:
                        sportmonks_sync_fixture.delay(nf.external_id)
                        continue

                    score_changed = (
                        fixture.home_goals != nf.home_score
                        or fixture.away_goals != nf.away_score
                    )

                    fixture.home_goals = nf.home_score
                    fixture.away_goals = nf.away_score
                    fixture.live_minute = nf.live_minute
                    fixture.live_stoppage = nf.live_stoppage
                    try:
                        fixture.status = MatchStatus[nf.status]
                    except KeyError:
                        logger.warning("sportmonks_live_unknown_status", status=nf.status)

                    publish_score_update(
                        fixture_id=fixture.id,
                        home_goals=nf.home_score or 0,
                        away_goals=nf.away_score or 0,
                        status=fixture.status.value,
                        minute=nf.live_minute,
                    )
                    published += 1

                    # Mål → refresha events/timeline (lager 2) + pusha explosion
                    # till matchrummet (Steg 4)
                    if score_changed:
                        sportmonks_sync_fixture.delay(nf.external_id)
                        try:
                            import json as _json
                            import redis as _redis
                            from app.core.config import get_settings as _gs
                            from app.core.room_realtime import room_channel

                            _rc = _redis.from_url(
                                _gs().redis_url, decode_responses=True
                            )
                            _rc.publish(
                                room_channel(fixture.id),
                                _json.dumps(
                                    {
                                        "type": "goal",
                                        "fixture_id": fixture.id,
                                        "home_goals": nf.home_score or 0,
                                        "away_goals": nf.away_score or 0,
                                        "minute": nf.live_minute,
                                    }
                                ),
                            )
                            _rc.close()
                        except Exception as exc:
                            logger.warning("room_goal_publish_failed", error=str(exc))

                await session.commit()
            finally:
                await provider.aclose()

        logger.info(
            "sportmonks_live_synced", live=len(live), published=published
        )
        return {"status": "ok", "live": len(live), "published": published}

    return run_async(_sync())
