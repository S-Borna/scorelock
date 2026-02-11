"""Shared fixtures for ScoreLock API tests.

Key fix: use a single event loop for all async tests so the
module-level SQLAlchemy engine (app.core.database.engine) keeps
its asyncpg connection pool on the same loop throughout the
test session.  Without this, each test function gets a new loop
and the pool's old connections raise
"cannot perform operation: another operation is in progress".
"""

import asyncio

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop shared by every async test."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
