"""Shared fixtures for ScoreLock API tests.

Loop scope is set to "session" via pyproject.toml
(asyncio_default_test_loop_scope) so the module-level
SQLAlchemy engine keeps its asyncpg pool on one event loop.
"""
