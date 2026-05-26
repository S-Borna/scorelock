"""ScoreLock intelligens-worker — host/box-entrypoint för generering.

Kör DÄR Max-auth (claude -p) finns: lokalt på Saids host, i drift på en
alltid-på-box. Bygger sin EGEN async-engine mot en host-nåbar DB-URL (default
localhost:5432, på boxen → prod-DB:n) eftersom app.core.database pekar på
Docker-internt `db:5432`. Prod (Railway) läser bara den lagrade texten.

Jobb-selektionen delas med Celery-tasken via orchestrator.select_pending_jobs
(idempotent: live regenereras bara när minuten gått framåt, pre/post bara om de saknas).

Användning (host, från backend/):
    python -m scripts.intelligence_worker --fixture 11 --kind pre_match --force
    python -m scripts.intelligence_worker --limit 20          # en batch
    python -m scripts.intelligence_worker --loop --interval 300   # daemon (boxen)

Boxen kör daemon-läget under launchd/systemd; INTELLIGENCE_DB_URL pekar på prod-DB:n.
"""
from __future__ import annotations

import argparse
import asyncio
import os

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.models import IntelligenceKind
from app.services.intelligence_orchestrator import (
    generate_intelligence,
    select_pending_jobs,
)

_DEFAULT_DB = "postgresql+asyncpg://scorelock:scorelock_dev@localhost:5432/scorelock"


def _db_url() -> str:
    return os.environ.get("INTELLIGENCE_DB_URL") or _DEFAULT_DB


async def _run_pass(Session, args) -> int:
    """En genererings-pass. Returnerar antal genererade analyser."""
    if args.fixture and args.kind:
        jobs = [(args.fixture, IntelligenceKind(args.kind), True)]
    else:
        async with Session() as s:
            jobs = await select_pending_jobs(s, args.limit)

    if not jobs:
        print("  inga matcher att generera")
        return 0

    done = 0
    for fid, kind, force in jobs:
        async with Session() as s:
            try:
                row = await generate_intelligence(
                    s, fid, kind, force=force or args.force
                )
                done += 1
                minute = f" @ {row.as_of_minute}'" if row.as_of_minute else ""
                print(
                    f"  ✓ fixture {fid} [{kind.value}] "
                    f"{row.provider}/{row.model_version}{minute}\n    {row.summary}"
                )
            except Exception as exc:  # noqa: BLE001 — logga + fortsätt nästa match
                print(f"  ✗ fixture {fid} [{kind.value}] FEL: {type(exc).__name__}: {exc}")
    return done


async def _run(args) -> None:
    engine = create_async_engine(_db_url(), pool_pre_ping=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    target = _db_url().split("@")[-1]
    try:
        if args.loop:
            print(f"Loop-läge: batch var {args.interval}s mot {target}. Ctrl-C avslutar.")
            n = 0
            while True:
                n += 1
                print(f"— pass {n} —")
                await _run_pass(Session, args)
                await asyncio.sleep(args.interval)
        else:
            print(f"Batch mot {target}")
            await _run_pass(Session, args)
    finally:
        await engine.dispose()


def main() -> None:
    p = argparse.ArgumentParser(description="ScoreLock intelligens-worker (host/box)")
    p.add_argument("--fixture", type=int, help="Rikta mot en fixture")
    p.add_argument("--kind", choices=[k.value for k in IntelligenceKind])
    p.add_argument("--limit", type=int, default=25, help="Max jobb per batch")
    p.add_argument("--force", action="store_true", help="Regenerera även om analys finns")
    p.add_argument("--loop", action="store_true", help="Daemon: kör batch på intervall")
    p.add_argument("--interval", type=int, default=300, help="Sekunder mellan loop-pass")
    try:
        asyncio.run(_run(p.parse_args()))
    except KeyboardInterrupt:
        print("\nAvslutar.")


if __name__ == "__main__":
    main()
