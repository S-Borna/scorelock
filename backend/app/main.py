"""ScoreLock Football Analytics — FastAPI Application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import structlog

from app.core.config import get_settings
from app.core.database import engine, Base
from app.api.routes import router

settings = get_settings()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # ── Startup ────────────────────────────────────────
    logger.info("scorelock_starting", environment=settings.environment)

    # Create tables (use Alembic migrations in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("scorelock_ready")
    yield

    # ── Shutdown ───────────────────────────────────────
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

# ── Routes ─────────────────────────────────────────────────

app.include_router(router, prefix="/api/v1")
