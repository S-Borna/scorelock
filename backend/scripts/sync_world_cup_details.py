"""Sync detalj-data (lineups, events, statistics, venue, referee) för alla
VM-fixtures med riktiga lag. Hoppa över knockout-placeholders ('Winner of X').

Använder befintliga sportmonks_normalizer.sync_fixture_detail som gör full
audit + upsert. Pacar mellan anrop för att inte sprängra rate-limit
(2000/timme per entity).

Kör:
    docker compose exec backend python -m scripts.sync_world_cup_details
    docker compose exec backend python -m scripts.sync_world_cup_details --limit 10
"""
from __future__ import annotations

import argparse
import asyncio
import os
import time
from typing import Any

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import async_session
from app.models.models import Fixture, Team
from app.providers.sportmonks import SportMonksProvider
from app.services.sportmonks_normalizer import sync_fixture_detail


WC_LEAGUE_ID = 12


async def _real_wc_fixture_external_ids(session) -> list[str]:
    """Returnera SportMonks-external-ids för VM-fixtures med riktiga lag.

    Filtrera bort placeholder-lag ('Winner Semi-final 1', 'Winner Round of 16
    Match 1', etc.) — de har inga riktiga lineups/events ändå.
    """
    rows = await session.execute(
        select(Fixture, Team.name)
        .join(Team, Team.id == Fixture.home_team_id)
        .where(Fixture.league_id == WC_LEAGUE_ID)
        .order_by(Fixture.kickoff.asc())
    )
    out: list[str] = []
    for fix, home_name in rows.all():
        if home_name.lower().startswith(("winner", "loser")):
            continue
        # Hämta away-name också (separat query för enkelhet)
        away_row = await session.execute(
            select(Team.name).where(Team.id == fix.away_team_id)
        )
        away_name = away_row.scalar_one_or_none() or ""
        if away_name.lower().startswith(("winner", "loser")):
            continue
        ext = (fix.external_ids or {}).get("sportmonks")
        if ext:
            out.append(str(ext))
    return out


async def run(args) -> None:
    settings = get_settings()
    provider = SportMonksProvider(settings)

    async with async_session() as session:
        ext_ids = await _real_wc_fixture_external_ids(session)

    if args.limit:
        ext_ids = ext_ids[: args.limit]

    print(f"Synkar {len(ext_ids)} VM-fixtures (skipping placeholders)")
    print(f"Pacing: {args.pace_ms}ms mellan anrop")

    ok = fail = 0
    start = time.monotonic()
    try:
        for i, ext_id in enumerate(ext_ids, 1):
            async with async_session() as session:
                try:
                    fx = await sync_fixture_detail(session, provider, ext_id)
                    await session.commit()
                    print(f"  [{i:3}/{len(ext_ids)}] ✓ {ext_id} → fixture_id={fx.id}")
                    ok += 1
                except Exception as exc:  # noqa: BLE001 — logga + fortsätt
                    print(
                        f"  [{i:3}/{len(ext_ids)}] ✗ {ext_id} {type(exc).__name__}: {str(exc)[:80]}"
                    )
                    fail += 1
            if args.pace_ms > 0:
                await asyncio.sleep(args.pace_ms / 1000.0)
    finally:
        await provider.aclose()

    elapsed = time.monotonic() - start
    print(
        f"\nKLART: {ok}/{len(ext_ids)} synkade på {elapsed:.1f}s "
        f"({fail} fel, snitt {elapsed / max(1, len(ext_ids)):.1f}s/match)"
    )


def main() -> None:
    p = argparse.ArgumentParser(description="VM fixture-detail-sync")
    p.add_argument("--limit", type=int, help="Sync bara N matcher (debug)")
    p.add_argument(
        "--pace-ms",
        type=int,
        default=200,
        help="Vila mellan anrop (rate-limit-skydd)",
    )
    asyncio.run(run(p.parse_args()))


if __name__ == "__main__":
    main()
