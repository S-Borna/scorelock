"""Shared fixtures for ScoreLock API tests.

Uses a **synchronous** session-scoped fixture that calls asyncio.run()
to create / drop tables.  This avoids every known pytest-asyncio
event-loop mismatch (the DDL engine is created, used, and disposed
inside its own temporary loop so the main test loop is never polluted).
"""

import asyncio

import pytest
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.core.database import Base
from app.models import models  # noqa: F401 — register all ORM models on Base


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    """Create all tables once before the test session, drop after."""
    url = get_settings().database_url

    async def _setup():
        ddl_engine = create_async_engine(url)
        async with ddl_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await ddl_engine.dispose()

    async def _teardown():
        ddl_engine = create_async_engine(url)
        async with ddl_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await ddl_engine.dispose()

    asyncio.run(_setup())
    yield
    asyncio.run(_teardown())
