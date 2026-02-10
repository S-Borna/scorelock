"""Celery application with scheduled data pipeline tasks."""

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
celery_app.conf.beat_schedule = {
    # Fetch today's fixtures every morning at 06:00 UTC
    "fetch-daily-fixtures": {
        "task": "app.services.tasks.fetch_daily_fixtures",
        "schedule": crontab(hour=6, minute=0),
    },
    # Update live scores every 60 seconds during match hours (12:00–23:00 UTC)
    "update-live-scores": {
        "task": "app.services.tasks.update_live_scores",
        "schedule": 60.0,  # Every 60 seconds
    },
    # Fetch and store odds updates every 30 minutes
    "fetch-odds": {
        "task": "app.services.tasks.fetch_odds_updates",
        "schedule": crontab(minute="*/30"),
    },
    # Run ML predictions for tomorrow's matches at 22:00 UTC
    "run-predictions": {
        "task": "app.services.tasks.run_daily_predictions",
        "schedule": crontab(hour=22, minute=0),
    },
    # Fetch news and run sentiment analysis every 2 hours
    "sentiment-analysis": {
        "task": "app.services.tasks.run_sentiment_analysis",
        "schedule": crontab(minute=0, hour="*/2"),
    },
    # Update standings weekly on Monday at 05:00 UTC
    "update-standings": {
        "task": "app.services.tasks.update_standings",
        "schedule": crontab(hour=5, minute=0, day_of_week=1),
    },
}

# Auto-discover tasks from services module
celery_app.autodiscover_tasks(["app.services"])
