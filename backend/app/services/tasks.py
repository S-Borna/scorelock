"""Celery tasks — the data pipeline that powers ScoreLock.

These tasks run on schedule (configured in celery_app.py) and keep
the database up to date with fixtures, scores, odds, and predictions.
"""

import asyncio
from datetime import date, timedelta

import structlog
from app.core.celery_app import celery_app
from app.core.database import async_session

logger = structlog.get_logger()


def run_async(coro):
    """Helper to run async code inside sync Celery tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.services.tasks.fetch_daily_fixtures")
def fetch_daily_fixtures():
    """Fetch today's and tomorrow's fixtures from API-Football and store in DB."""
    async def _fetch():
        from app.services.api_football import api_football, LEAGUE_IDS, PHASE_1_LEAGUES
        from app.services.db_service import upsert_fixtures_batch, get_league_by_api_id

        today = date.today()
        tomorrow = today + timedelta(days=1)
        total = 0

        async with async_session() as session:
            for day in [today, tomorrow]:
                for league_name in PHASE_1_LEAGUES:
                    api_id = LEAGUE_IDS[league_name]

                    league = await get_league_by_api_id(session, api_id)
                    if not league:
                        logger.warning("league_not_in_db", league=league_name, api_id=api_id)
                        continue

                    try:
                        fixtures = await api_football.get_fixtures_by_date(day, api_id)
                    except Exception as exc:
                        logger.error("fixture_fetch_failed", league=league_name, error=str(exc))
                        continue

                    if fixtures:
                        count = await upsert_fixtures_batch(session, fixtures, league)
                        total += count
                        logger.info(
                            "fixtures_upserted",
                            date=day.isoformat(),
                            league=league_name,
                            count=count,
                        )

            await session.commit()

        return total

    count = run_async(_fetch())
    return {"status": "ok", "fixtures_processed": count}


@celery_app.task(name="app.services.tasks.update_live_scores")
def update_live_scores():
    """Update scores for currently live matches."""
    async def _update():
        from app.services.api_football import api_football
        from app.services.db_service import upsert_fixture, get_league_by_api_id

        try:
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
                            status=result.status.value if hasattr(result.status, "value") else str(result.status),
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
    """Fetch latest odds for upcoming fixtures."""
    async def _fetch():
        from app.services.api_football import api_football
        from app.services.db_service import upsert_odds
        from app.models.models import Fixture, MatchStatus
        from sqlalchemy import select
        from datetime import datetime

        async with async_session() as session:
            # Get upcoming scheduled fixtures
            result = await session.execute(
                select(Fixture)
                .where(
                    Fixture.status == MatchStatus.SCHEDULED,
                    Fixture.kickoff >= datetime.utcnow(),
                    Fixture.kickoff <= datetime.utcnow() + timedelta(days=2),
                )
                .limit(10)  # Stay within API limits
            )
            fixtures = list(result.scalars().all())

            updated = 0
            for fixture in fixtures:
                try:
                    odds_data = await api_football.get_odds(fixture.api_football_id)
                except Exception as exc:
                    logger.error("odds_fetch_failed", fixture_id=fixture.id, error=str(exc))
                    continue

                for bookmaker_entry in odds_data:
                    bookmaker_info = bookmaker_entry.get("bookmakers", [])
                    for bm in bookmaker_info:
                        bm_name = bm.get("name", "Unknown")
                        for bet in bm.get("bets", []):
                            market = bet.get("name", "")
                            values = {v.get("value"): float(v.get("odd", 0)) for v in bet.get("values", [])}

                            if market == "Match Winner":
                                await upsert_odds(
                                    session,
                                    fixture_id=fixture.id,
                                    bookmaker=bm_name,
                                    market="1X2",
                                    home_odds=values.get("Home"),
                                    draw_odds=values.get("Draw"),
                                    away_odds=values.get("Away"),
                                )
                                updated += 1

                            elif "Over/Under" in market:
                                await upsert_odds(
                                    session,
                                    fixture_id=fixture.id,
                                    bookmaker=bm_name,
                                    market=market,
                                    over_odds=values.get("Over"),
                                    under_odds=values.get("Under"),
                                    line=2.5,
                                )

            await session.commit()

        logger.info("odds_updated", fixtures=len(fixtures), odds_entries=updated)
        return updated

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

                    # Check for value bets if odds available
                    is_value_home = False
                    is_value_draw = False
                    is_value_away = False
                    value_edge = None

                    odds_1x2 = [o for o in fixture.odds if o.market == "1X2"]
                    if odds_1x2:
                        best = odds_1x2[0]
                        if best.home_odds and best.draw_odds and best.away_odds:
                            vb = identify_value_bets(
                                prediction,
                                {
                                    "home": best.home_odds,
                                    "draw": best.draw_odds,
                                    "away": best.away_odds,
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
        from app.services.news_fetcher import fetch_team_news, format_articles_for_analysis
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
                        logger.warning("news_fetch_failed", team=team_name, error=str(exc))
                        articles = []

                    if not articles:
                        logger.info("sentiment_no_news", team=team_name)
                        continue

                    news_text = format_articles_for_analysis(articles)

                    try:
                        result = await analyzer.analyze_text(team_name, news_text)
                    except RuntimeError:
                        logger.warning("sentiment_skipped", reason="anthropic_key_missing")
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
    """Update league standings from API-Football."""
    async def _update():
        from app.services.api_football import api_football, LEAGUE_IDS, PHASE_1_LEAGUES
        from app.services.db_service import upsert_standing, get_league_by_api_id

        current_year = date.today().year
        total = 0

        async with async_session() as session:
            for league_name in PHASE_1_LEAGUES:
                api_id = LEAGUE_IDS[league_name]
                league = await get_league_by_api_id(session, api_id)
                if not league:
                    continue

                # Allsvenskan follows calendar year
                season = current_year if league_name == "allsvenskan" else current_year - 1

                try:
                    standings = await api_football.get_standings(api_id, season)
                except Exception as exc:
                    logger.error("standings_fetch_failed", league=league_name, error=str(exc))
                    continue

                for entry in standings:
                    result = await upsert_standing(session, entry, league, season)
                    if result:
                        total += 1

                logger.info("standings_upserted", league=league_name, teams=len(standings))

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
