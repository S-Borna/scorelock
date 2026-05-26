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
    # SHELVED 2026-05-04 — API-Football account suspended (HTTP 403 on /status + /leagues).
    # Re-enable when account is restored eller efter pivot till SportMonks livescores.
    # Task-koden i services/tasks.py + services/api_football.py är intakt och re-arms vid uncomment.
    # "update-live-scores": {
    #     "task": "app.services.tasks.update_live_scores",
    #     "schedule": crontab(minute="*/5", hour="12-23"),
    # },
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
    # ── Match-intelligens ───────────────────────────────────
    # SHELVED: Max-primär-genereringen kör på alltid-på-boxen (claude -p, platt
    # kostnad). Den HÄR beat-tasken kör i Docker/prod UTAN claude → faller på
    # Anthropic-API (metered). Aktivera FÖRST när boxen är i drift som primär,
    # som rent skyddsnät — annars genereras allt via betal-API:t. Task-koden i
    # services/tasks.py är intakt och re-arms vid uncomment.
    # "generate-intelligence-batch": {
    #     "task": "app.services.tasks.generate_match_intelligence_batch",
    #     "schedule": crontab(minute="*/30", hour="12-23"),
    # },
    # ── Social Distribution (M8) — GATED 2026-05-25 ──────────
    # Avstängda: alla tre refererar en borttagen ValueBet-modell + fältnamn
    # som inte längre finns (fixture.home_team som sträng, fixture.league_name,
    # Article.article_type/.created_at, Fixture.home_score). De kraschade tyst
    # vid varje körning. Task-funktionerna finns kvar i tasks.py oförändrade.
    # Strategiskt: detta är outbound auto-posting; vår riktning är in-app hangout.
    # Återaktivera först när tasks + ValueBet-källa är ombyggda mot rätt schema.
    # "distribute-previews": {
    #     "task": "app.services.tasks.distribute_match_previews",
    #     "schedule": crontab(hour=10, minute=30),
    # },
    # "distribute-value-bets": {
    #     "task": "app.services.tasks.distribute_value_bet_alerts",
    #     "schedule": crontab(hour=9, minute=30),
    # },
    # "distribute-match-results": {
    #     "task": "app.services.tasks.distribute_match_results",
    #     "schedule": crontab(minute=45, hour="14-23"),
    # },
}

# ── SportMonks sync (Phase 7.4) ────────────────────────────
# Aktiveras automatiskt när SPORTMONKS_USE_STATIC_FIXTURES=false (post-augusti
# tier-upgrade). Static-mode behöver ingen schedule eftersom payload-filer
# inte ändras — manuell trigger via /admin/trigger/sportmonks-sync/{id}-endpoint
# används istället.
#
# Live-schedule design:
#   - Pre-match (kickoff +/- 24h): var 6:e h
#   - In-play (status=IN_PLAY): var 15:e min
#   - Post-match (status=FINISHED): single sync inom 30 min av FT
#
# Dessa entries läggs in när live-mode aktiveras + sportmonks_sync_live_fixtures
# meta-task implementeras (Phase 7.5 / launch-prep).
if not settings.sportmonks_use_static_fixtures:
    celery_app.conf.beat_schedule.update(
        {
            # Realtids-spine: 1 API-anrop/cykel mot /livescores/inplay.
            # 30s = 120 anrop/h, väl under SportMonks-gränsen 2000/h/entity.
            # Tom respons när inget spelas → cheap no-op. Lager 2 (events) köas
            # av tasken själv vid mål, inte på schema.
            "sportmonks-sync-inplay": {
                "task": "app.services.tasks.sportmonks_sync_live_fixtures",
                "schedule": 30.0,
            },
        }
    )

# Auto-discover tasks from services module
celery_app.autodiscover_tasks(["app.services"])
