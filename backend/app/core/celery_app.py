"""Celery application with scheduled data pipeline tasks.

Data source strategy:
  - football-data.org: Primary for fixtures + standings (10 req/min free)
  - API-Football: Live scores only + Allsvenskan/EL/ECL (100 req/day free)
  - The Odds API: All odds from 40+ bookmakers (500 req/month free)
"""

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "scorelock",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# ── Scheduled Tasks ────────────────────────────────────────
# Budget targets (monthly):
#   API-Football:    100/day  → ~20 used/day (live scores only)
#   football-data:   10/min   → unlimited daily (fixtures + standings)
#   The Odds API:    500/mo   → ~16/day (odds 2x/day × 8 leagues)
celery_app.conf.beat_schedule = {
    # Fetch upcoming fixtures (football-data.org primary) — 06:00 + 18:00 UTC
    "fetch-daily-fixtures": {
        "task": "app.services.tasks.fetch_daily_fixtures",
        "schedule": crontab(hour="6,18", minute=0),
    },
    # Update live scores (API-Football — only source with live data)
    # Every 5 minutes during match hours (12:00–23:00 UTC)
    "update-live-scores": {
        "task": "app.services.tasks.update_live_scores",
        "schedule": crontab(minute="*/5", hour="12-23"),
    },
    # Fetch odds from The Odds API (2x/day to conserve 500 req/month budget)
    "fetch-odds": {
        "task": "app.services.tasks.fetch_odds_updates",
        "schedule": crontab(hour="8,20", minute=0),
    },
    # Run ML predictions at 07:00 + 22:00 UTC (after fixture + odds sync)
    "run-predictions": {
        "task": "app.services.tasks.run_daily_predictions",
        "schedule": crontab(hour="7,22", minute=0),
    },
    # Fetch news and run sentiment analysis every 2 hours
    "sentiment-analysis": {
        "task": "app.services.tasks.run_sentiment_analysis",
        "schedule": crontab(minute=0, hour="*/2"),
    },
    # Update standings (football-data.org primary) — daily at 05:00 UTC
    "update-standings": {
        "task": "app.services.tasks.update_standings",
        "schedule": crontab(hour=5, minute=0),
    },
    # Retrain ML model weekly on Sunday at 03:00 UTC
    "retrain-model": {
        "task": "app.services.tasks.train_model",
        "schedule": crontab(hour=3, minute=0, day_of_week=0),
    },

    # ── AI Content Engine (M3) ──────────────────────────────
    # Match previews — daily at 10:00 UTC (for tomorrow's fixtures)
    "content-previews": {
        "task": "app.services.tasks.generate_content_previews",
        "schedule": crontab(hour=10, minute=0),
    },
    # Match reports — every hour 14:00–23:00 UTC (after matches finish)
    "content-reports": {
        "task": "app.services.tasks.generate_content_reports",
        "schedule": crontab(minute=30, hour="14-23"),
    },
    # Round summaries — daily at 04:00 UTC
    "content-round-summaries": {
        "task": "app.services.tasks.generate_content_round_summaries",
        "schedule": crontab(hour=4, minute=0),
    },
    # Value bet articles — daily at 09:00 UTC
    "content-value-bets": {
        "task": "app.services.tasks.generate_content_value_bets",
        "schedule": crontab(hour=9, minute=0),
    },
    # News rewrites — every 4 hours
    "content-news-rewrites": {
        "task": "app.services.tasks.generate_content_news_rewrites",
        "schedule": crontab(minute=15, hour="*/4"),
    },

    # ── Tipping League (M6) ─────────────────────────────────
    # Score user predictions every 15 min during match hours
    "score-user-predictions": {
        "task": "app.services.tasks.score_user_predictions",
        "schedule": crontab(minute="*/15", hour="14-23"),
    },
}

# Auto-discover tasks from services module
celery_app.autodiscover_tasks(["app.services"])
