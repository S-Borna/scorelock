"""Shared fixtures for ScoreLock API tests.

Tables are created by 'alembic upgrade head' in CI (see ci.yml).
This conftest provides a fallback create_all and drops tables after
the session so the test database stays clean.
"""

import subprocess
import sys

import pytest

from app.core.database import Base
from app.models import models  # noqa: F401 — register all ORM models on Base


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    """Ensure tables exist (fallback if alembic hasn't run yet)."""
    from app.core.config import get_settings

    url = get_settings().database_url
    # Use a sync engine for DDL — avoids all event-loop issues.
    sync_url = url.replace("+asyncpg", "+psycopg2").replace(
        "postgresql+psycopg2", "postgresql"
    )
    try:
        from sqlalchemy import create_engine

        sync_engine = create_engine(sync_url)
        Base.metadata.create_all(sync_engine)
        sync_engine.dispose()
    except Exception:
        # psycopg2 may not be installed — try via alembic subprocess
        try:
            subprocess.run(
                [sys.executable, "-m", "alembic", "upgrade", "head"],
                check=True,
                timeout=30,
            )
        except Exception as exc:
            pytest.skip(f"Cannot create tables: {exc}")

    yield

    # Teardown: best-effort drop
    try:
        from sqlalchemy import create_engine

        sync_engine = create_engine(sync_url)
        Base.metadata.drop_all(sync_engine)
        sync_engine.dispose()
    except Exception:
        pass
