"""Shared fixtures for ScoreLock API tests.

Tests run against a DEDICATED `<db>_test` database — NEVER the dev/prod DB.

Why this matters: `app.core.database` builds its async engine at IMPORT time from
`settings.database_url`. So before any app module is imported, this module rewrites
`DATABASE_URL` to point at an isolated `<db>_test` database. The test DB is created
if missing, tables are built at session start, and dropped clean at teardown.

A hard guard refuses to create_all/drop_all unless the target DB name ends with
`_test`, so a misconfigured DATABASE_URL (e.g. pointing at dev or prod) can never
wipe real data. (2026-05-26: the previous conftest ran drop_all against the dev DB
directly and wiped it — this prevents a repeat, including against prod.)
"""

import os

from sqlalchemy.engine import make_url

# ── Redirect ALL DB access to an isolated test database BEFORE app imports ──
_raw = os.environ.get("DATABASE_URL") or (
    "postgresql+asyncpg://scorelock:scorelock_dev@db:5432/scorelock"
)
_url = make_url(_raw)
if not (_url.database or "").endswith("_test"):
    _url = _url.set(database=f"{_url.database}_test")
_TEST_URL = _url
os.environ["DATABASE_URL"] = _url.render_as_string(hide_password=False)

import pytest  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.database import Base  # noqa: E402
from app.models import models  # noqa: E402,F401 — register all ORM models on Base

# Settings may have been built during the imports above; rebuild from the test URL.
get_settings.cache_clear()


def _sync_url() -> str:
    """Same DB, sync psycopg2 driver — for DDL (avoids event-loop issues)."""
    return _TEST_URL.set(drivername="postgresql+psycopg2").render_as_string(
        hide_password=False
    )


def _ensure_test_db() -> None:
    """CREATE DATABASE <db>_test if missing — connect to maintenance db, autocommit."""
    from sqlalchemy import create_engine, text

    admin = _TEST_URL.set(drivername="postgresql+psycopg2", database="postgres")
    eng = create_engine(
        admin.render_as_string(hide_password=False), isolation_level="AUTOCOMMIT"
    )
    try:
        with eng.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :n"),
                {"n": _TEST_URL.database},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{_TEST_URL.database}"'))
    finally:
        eng.dispose()


@pytest.fixture(scope="session", autouse=True)
def _create_tables():
    """Build tables in the isolated test DB; drop them clean at teardown."""
    # Hard guard: refuse to touch any DB that isn't explicitly a *_test database.
    assert (_TEST_URL.database or "").endswith("_test"), (
        f"Refusing to run tests against non-test DB '{_TEST_URL.database}' "
        "— DATABASE_URL must resolve to a *_test database."
    )

    from sqlalchemy import create_engine

    try:
        _ensure_test_db()
        sync_engine = create_engine(_sync_url())
        Base.metadata.create_all(sync_engine)
        sync_engine.dispose()
    except Exception as exc:
        pytest.skip(f"Cannot prepare test DB: {exc}")

    yield

    # Teardown — the guard above guarantees this only ever hits a *_test DB.
    try:
        sync_engine = create_engine(_sync_url())
        Base.metadata.drop_all(sync_engine)
        sync_engine.dispose()
    except Exception:
        pass
