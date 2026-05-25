"""ScoreLock intelligens-worker — host/box-entrypoint för generering.

Kör DÄR Max-auth (claude -p) finns: lokalt på Saids host, i drift på en
alltid-på-box. Bygger sin EGEN async-engine mot en host-nåbar DB-URL (default
localhost:5432, på boxen → prod-DB:n) eftersom app.core.database pekar på
Docker-internt `db:5432`. Prod (Railway) läser bara den lagrade texten.

Anropar orkestratorn `generate_intelligence` per (fixture, fas):
- batch (default): betar av live-matcher (in_match), nyss avslutade (post_match)
  och kommande inom 48h (pre_match) som saknar färsk analys.
- riktat: `--fixture <id> --kind <pre_match|in_match|post_match>`.

Användning (host, från backend/):
    python -m scripts.intelligence_worker --fixture 11 --kind pre_match --force
    python -m scripts.intelligence_worker --limit 20
"""
from __future__ import annotations

import argparse
import asyncio
import os
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.models import Fixture, IntelligenceKind, MatchIntelligence, MatchStatus
from app.services.intelligence_orchestrator import generate_intelligence

_DEFAULT_DB = "postgresql+asyncpg://scorelock:scorelock_dev@localhost:5432/scorelock"

_LIVE_STATUSES = (
    MatchStatus.LIVE,
    MatchStatus.HALFTIME,
    MatchStatus.IN_PLAY,
    MatchStatus.IN_PROGRESS_EXTRA_TIME,
    MatchStatus.IN_PROGRESS_PENALTIES,
)


def _db_url() -> str:
    return os.environ.get("INTELLIGENCE_DB_URL") or _DEFAULT_DB


async def _missing(session, fixture_id: int, kind: IntelligenceKind) -> bool:
    row = (
        await session.execute(
            select(MatchIntelligence.id).where(
                MatchIntelligence.fixture_id == fixture_id,
                MatchIntelligence.kind == kind,
                MatchIntelligence.language == "sv",
            )
        )
    ).scalar_one_or_none()
    return row is None


async def _select_jobs(session, limit: int) -> list[tuple[int, IntelligenceKind]]:
    """Plocka matcher som behöver analys, per fas."""
    jobs: list[tuple[int, IntelligenceKind]] = []
    now = datetime.utcnow()

    live = (
        (await session.execute(select(Fixture.id).where(Fixture.status.in_(_LIVE_STATUSES))))
        .scalars()
        .all()
    )
    for fid in live:
        jobs.append((fid, IntelligenceKind.IN_MATCH))  # live → regenerera alltid

    finished = (
        (
            await session.execute(
                select(Fixture.id).where(
                    Fixture.status == MatchStatus.FINISHED,
                    Fixture.kickoff >= now - timedelta(hours=24),
                )
            )
        )
        .scalars()
        .all()
    )
    for fid in finished:
        if await _missing(session, fid, IntelligenceKind.POST_MATCH):
            jobs.append((fid, IntelligenceKind.POST_MATCH))

    upcoming = (
        (
            await session.execute(
                select(Fixture.id).where(
                    Fixture.status == MatchStatus.SCHEDULED,
                    Fixture.kickoff >= now,
                    Fixture.kickoff <= now + timedelta(hours=48),
                )
            )
        )
        .scalars()
        .all()
    )
    for fid in upcoming:
        if await _missing(session, fid, IntelligenceKind.PRE_MATCH):
            jobs.append((fid, IntelligenceKind.PRE_MATCH))

    return jobs[:limit]


async def _run(args) -> None:
    engine = create_async_engine(_db_url(), pool_pre_ping=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    try:
        if args.fixture and args.kind:
            jobs = [(args.fixture, IntelligenceKind(args.kind))]
        else:
            async with Session() as s:
                jobs = await _select_jobs(s, args.limit)

        if not jobs:
            print("Inga matcher att generera.")
            return

        print(f"{len(jobs)} jobb. DB={_db_url().split('@')[-1]}")
        for fid, kind in jobs:
            async with Session() as s:
                try:
                    row = await generate_intelligence(
                        s, fid, kind, force=args.force or bool(args.fixture)
                    )
                    print(
                        f"  ✓ fixture {fid} [{kind.value}] {row.provider}/{row.model_version}"
                        f"{f' @ {row.as_of_minute}' if row.as_of_minute else ''}\n"
                        f"    {row.summary}"
                    )
                except Exception as exc:  # noqa: BLE001 — logga + fortsätt nästa match
                    print(f"  ✗ fixture {fid} [{kind.value}] FEL: {type(exc).__name__}: {exc}")
    finally:
        await engine.dispose()


def main() -> None:
    p = argparse.ArgumentParser(description="ScoreLock intelligens-worker (host/box)")
    p.add_argument("--fixture", type=int, help="Rikta mot en fixture")
    p.add_argument("--kind", choices=[k.value for k in IntelligenceKind])
    p.add_argument("--limit", type=int, default=25, help="Max jobb i batch-läge")
    p.add_argument("--force", action="store_true", help="Regenerera även om analys finns")
    asyncio.run(_run(p.parse_args()))


if __name__ == "__main__":
    main()
