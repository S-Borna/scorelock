"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """All app settings. Loaded from .env or environment variables."""

    # ── App ────────────────────────────────────────────────
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

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

    # ── Stripe ─────────────────────────────────────────────
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_pro: str = ""
    stripe_price_elite: str = ""

    # ── LLM ────────────────────────────────────────────────
    anthropic_api_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
