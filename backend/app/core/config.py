"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """All app settings. Loaded from .env or environment variables."""

    # ── App ────────────────────────────────────────────────
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,https://scorelock.saidborna.com"
    base_url: str = "https://scorelock.saidborna.com"

    # ── Database ───────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://scorelock:scorelock_dev@db:5432/scorelock"

    # ── Redis ──────────────────────────────────────────────
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    # ── Auth ───────────────────────────────────────────────
    secret_key: str = "change-me"
    access_token_expire_minutes: int = 30

    # ── External APIs ──────────────────────────────────────
    api_football_key: str = ""
    api_football_base_url: str = "https://v3.football.api-sports.io"
    football_data_key: str = ""
    football_data_base_url: str = "https://api.football-data.org/v4"
    the_odds_api_key: str = ""
    the_odds_api_base_url: str = "https://api.the-odds-api.com/v4"

    # ── Stripe ─────────────────────────────────────────────
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_pro: str = ""
    stripe_price_elite: str = ""

    # ── LLM ────────────────────────────────────────────────
    anthropic_api_key: str = ""

    # ── Error Monitoring ───────────────────────────────────
    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = 0.2

    # ── Social Media Distribution ──────────────────────────
    twitter_bearer_token: str = ""
    twitter_api_key: str = ""
    twitter_api_secret: str = ""
    twitter_access_token: str = ""
    twitter_access_token_secret: str = ""
    discord_webhook_url: str = ""
    discord_webhook_valuebets: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # ── Push Notifications (OneSignal) ─────────────────────
    onesignal_app_id: str = ""
    onesignal_api_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
