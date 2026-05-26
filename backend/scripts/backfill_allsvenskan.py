"""Backfill Allsvenskan-djup: hela den spelade säsongen via SportMonks (events/stats/
lineups) + härled ligatabellen ur våra egna färdigspelade matcher.

Varför: intelligens-motorn (orkestratorn) läser form + tabell ur dossiern. Med bara
~25 synkade matcher blev analysen tunn ("form 1 match", "tabell saknas"). Detta
fördjupar formdatan och fyller tabellen → dossier-grundad analys lyfter.

Kör i containern (har provider + deps + db):
    docker compose exec backend python -m scripts.backfill_allsvenskan
    docker compose exec backend python -m scripts.backfill_allsvenskan --start 2026-03-15 --end 2026-05-27

Allsvenskan (573) ligger i nuvarande SportMonks-plan → kräver inte VM-paketet.
"""
from __future__ import annotations

import argparse
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta

from sqlalchemy import delete, select

from app.core.config import get_settings
from app.core.database import async_session
from app.models.models import Fixture, League, MatchStatus, Standing
from app.providers.base import DateRange
from app.providers.sportmonks import SportMonksProvider
from app.services.sportmonks_normalizer import sync_fixture_detail

_ALLSVENSKAN = "573"
_SEASON = 2026
_WINDOW_DAYS = 14  # ≤2 omgångar (~16 matcher) < SportMonks page-1-cap (25)


async def _backfill_fixtures(provider, start: datetime, end: datetime, window_days: int) -> int:
    """Fönstra över säsongen (SportMonks max 100 dgr/anrop, page-1 ⇒ små fönster)."""
    seen: set[str] = set()
    synced = 0
    cur = start
    while cur < end:
        w_end = min(cur + timedelta(days=window_days), end)
        fixtures = await provider.fetch_fixtures(
            _ALLSVENSKAN, _SEASON, DateRange(start=cur, end=w_end)
        )
        for nf in fixtures:
            if nf.external_id in seen:
                continue
            seen.add(nf.external_id)
            async with async_session() as session:
                try:
                    await sync_fixture_detail(session, provider, nf.external_id)
                    await session.commit()
                    synced += 1
                except Exception as exc:  # noqa: BLE001 — logga + fortsätt
                    print(f"  skip {nf.external_id}: {type(exc).__name__}: {str(exc)[:60]}")
        cur = w_end
    return synced


async def _derive_standings() -> int:
    """Härled tabellen ur färdigspelade Allsvenskan-matcher → upsert i standings."""
    async with async_session() as session:
        league = (
            await session.execute(select(League).where(League.name.ilike("%allsvensk%")))
        ).scalars().first()
        if league is None:
            print("  ingen Allsvenskan-liga i DB")
            return 0

        fixtures = (
            await session.execute(
                select(Fixture).where(
                    Fixture.league_id == league.id,
                    Fixture.status == MatchStatus.FINISHED,
                )
            )
        ).scalars().all()

        table: dict[int, dict] = defaultdict(
            lambda: {"p": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "pts": 0}
        )
        season = _SEASON
        for f in fixtures:
            if f.home_goals is None or f.away_goals is None:
                continue
            season = f.season or _SEASON
            hg, ag = f.home_goals, f.away_goals
            h, a = table[f.home_team_id], table[f.away_team_id]
            h["p"] += 1
            a["p"] += 1
            h["gf"] += hg
            h["ga"] += ag
            a["gf"] += ag
            a["ga"] += hg
            if hg > ag:
                h["w"] += 1
                a["l"] += 1
                h["pts"] += 3
            elif hg < ag:
                a["w"] += 1
                h["l"] += 1
                a["pts"] += 3
            else:
                h["d"] += 1
                a["d"] += 1
                h["pts"] += 1
                a["pts"] += 1

        ranked = sorted(
            table.items(),
            key=lambda kv: (-kv[1]["pts"], -(kv[1]["gf"] - kv[1]["ga"]), -kv[1]["gf"]),
        )
        # Recompute → ersätt den här ligans/säsongens rader (scopad DELETE + insert).
        await session.execute(
            delete(Standing).where(
                Standing.league_id == league.id, Standing.season == season
            )
        )
        for pos, (team_id, r) in enumerate(ranked, start=1):
            session.add(
                Standing(
                    league_id=league.id, season=season, team_id=team_id, position=pos,
                    points=r["pts"], played=r["p"], won=r["w"], drawn=r["d"], lost=r["l"],
                    goals_for=r["gf"], goals_against=r["ga"],
                    goal_diff=r["gf"] - r["ga"],
                )
            )
        await session.commit()
        return len(ranked)


async def _run(args) -> None:
    start = datetime.fromisoformat(args.start)
    end = datetime.fromisoformat(args.end)
    provider = SportMonksProvider(get_settings())
    try:
        print(f"Backfill Allsvenskan {start.date()} → {end.date()} (fönster {args.window}d)")
        synced = await _backfill_fixtures(provider, start, end, args.window)
        print(f"  fixtures synkade: {synced}")
        rows = await _derive_standings()
        print(f"  tabell härledd: {rows} lag")
    finally:
        await provider.aclose()


def main() -> None:
    p = argparse.ArgumentParser(description="Backfill Allsvenskan-djup (SportMonks)")
    p.add_argument("--start", default="2026-03-15")
    p.add_argument("--end", default=datetime.utcnow().date().isoformat())
    p.add_argument("--window", type=int, default=_WINDOW_DAYS)
    asyncio.run(_run(p.parse_args()))


if __name__ == "__main__":
    main()
