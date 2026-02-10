"""Celery tasks — the data pipeline that powers ScoreLock.

These tasks run on schedule (configured in celery_app.py) and keep
the database up to date with fixtures, scores, odds, and predictions.
"""

import asyncio
from datetime import date, timedelta

import structlog
from app.core.celery_app import celery_app

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
    """Fetch today's and tomorrow's fixtures from API-Football."""
    async def _fetch():
        from app.services.api_football import api_football, LEAGUE_IDS, PHASE_1_LEAGUES

        today = date.today()
        tomorrow = today + timedelta(days=1)

        for day in [today, tomorrow]:
            for league_name in PHASE_1_LEAGUES:
                league_id = LEAGUE_IDS[league_name]
                fixtures = await api_football.get_fixtures_by_date(day, league_id)
                logger.info(
                    "fetched_fixtures",
                    date=day.isoformat(),
                    league=league_name,
                    count=len(fixtures),
                )
                # TODO: Upsert fixtures into database
                # await upsert_fixtures(fixtures)

    run_async(_fetch())
    return {"status": "ok"}


@celery_app.task(name="app.services.tasks.update_live_scores")
def update_live_scores():
    """Update scores for currently live matches."""
    async def _update():
        from app.services.api_football import api_football

        live = await api_football.get_live_fixtures()
        logger.info("live_fixtures_update", count=len(live))
        # TODO: Update fixture scores in database
        # TODO: Push WebSocket updates to connected clients

    run_async(_update())
    return {"status": "ok"}


@celery_app.task(name="app.services.tasks.fetch_odds_updates")
def fetch_odds_updates():
    """Fetch latest odds for upcoming fixtures."""
    logger.info("fetch_odds_updates_started")
    # TODO: Get upcoming fixtures from DB, fetch odds for each
    # TODO: Store in odds table, calculate odds movement
    return {"status": "ok"}


@celery_app.task(name="app.services.tasks.run_daily_predictions")
def run_daily_predictions():
    """Run ML predictions for tomorrow's matches."""
    logger.info("running_daily_predictions")
    # TODO: Load tomorrow's fixtures from DB
    # TODO: Build feature vectors
    # TODO: Run XGBoost model
    # TODO: Compare against bookmaker odds for value detection
    # TODO: Store predictions in DB
    return {"status": "ok"}


@celery_app.task(name="app.services.tasks.run_sentiment_analysis")
def run_sentiment_analysis():
    """Run LLM sentiment analysis on recent football news."""
    logger.info("running_sentiment_analysis")
    # TODO: Fetch news from NewsAPI for each team
    # TODO: Run Claude/sentiment model on headlines + summaries
    # TODO: Calculate sentiment score and buzz score
    # TODO: Store in sentiment_scores table
    return {"status": "ok"}


@celery_app.task(name="app.services.tasks.update_standings")
def update_standings():
    """Update league standings (weekly)."""
    async def _update():
        from app.services.api_football import api_football, LEAGUE_IDS, PHASE_1_LEAGUES

        current_season = date.today().year
        for league_name in PHASE_1_LEAGUES:
            league_id = LEAGUE_IDS[league_name]
            standings = await api_football.get_standings(league_id, current_season)
            logger.info(
                "updated_standings",
                league=league_name,
                teams=len(standings),
            )
            # TODO: Upsert standings into database

    run_async(_update())
    return {"status": "ok"}
