"""ScoreLock Football Analytics — FastAPI Application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import structlog

import sentry_sdk

from app.core.config import get_settings
from app.core.database import engine
from app.core.rate_limit import RateLimitMiddleware
from app.api.routes import router
from app.api.auth import router as auth_router
from app.api.stripe import router as stripe_router
from app.api.websocket import router as ws_router
from app.api.fantasy_routes import router as fantasy_router

settings = get_settings()
logger = structlog.get_logger()

# ── Sentry error monitoring ────────────────────────────────
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        environment=settings.environment,
        release="scorelock-api@0.1.0",
        send_default_pii=False,
    )
    logger.info("sentry_initialized", environment=settings.environment)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events. Schema is owned by Alembic."""
    logger.info("scorelock_starting", environment=settings.environment)
    logger.info("scorelock_ready")
    yield
    logger.info("scorelock_shutting_down")
    await engine.dispose()


# ── App Factory ────────────────────────────────────────────

app = FastAPI(
    title="ScoreLock Football Analytics",
    description="AI-driven football match predictions, sentiment analysis, and value bet identification.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
)

# ── Middleware ─────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Prometheus metrics ─────────────────────────────────────

Instrumentator().instrument(app).expose(app)

# ── Rate Limiting ──────────────────────────────────────────

app.add_middleware(RateLimitMiddleware)

# ── Routes ─────────────────────────────────────────────────

app.include_router(router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(stripe_router, prefix="/api/v1")
app.include_router(fantasy_router, prefix="/api/v1/fantasy")
app.include_router(ws_router)  # WebSocket on root path: /ws/live (not /api/v1/ws/live)
