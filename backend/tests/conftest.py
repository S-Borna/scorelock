"""Shared fixtures for ScoreLock API tests.

Loop scope is set to "session" via pyproject.toml
(asyncio_default_test_loop_scope) so the module-level
SQLAlchemy engine keeps its asyncpg pool on one event loop.

The auto-use ``_create_tables`` fixture runs once per session
to create all tables (via metadata.create_all) so the CI
PostgreSQL service has the schema before any endpoint tests run.
"""

import pytest_asyncio

from app.core.database import Base, engine
from app.models import models  # noqa: F401 — register all models


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_tables():
    """Create all tables once before the test session, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
