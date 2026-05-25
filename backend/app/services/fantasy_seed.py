"""Koppla fantasy-modulen mot synkad Allsvenskan-data (Steg 5).

Idempotent: skapar en FantasySeason för Allsvenskan + gameweeks (grupperade per
kickoff-vecka eftersom fixtures saknar round-fält) + gameweek↔fixture-länkar +
pricing för alla spelare i ligans lag. Kör om = inga dubbletter.

Pris-units: 10 = €1.0M. Startpriser per position är schabloner tills riktig
marknadsmodell finns (uppskjutet).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    FantasyGameweek,
    FantasyGameweekFixture,
    FantasyPlayerPricing,
    FantasyScope,
    FantasySeason,
    Fixture,
    League,
    Player,
)

_PRICE_BY_POSITION = {
    "goalkeeper": 45,
    "defender": 50,
    "midfielder": 60,
    "attacker": 70,
}
_DEFAULT_PRICE = 50


async def seed_allsvenskan_fantasy(session: AsyncSession) -> dict:
    league = (
        await session.execute(select(League).where(League.name == "Allsvenskan"))
    ).scalar_one_or_none()
    if league is None:
        return {"status": "error", "reason": "Allsvenskan saknas i DB"}

    fixtures = (
        (
            await session.execute(
                select(Fixture)
                .where(Fixture.league_id == league.id)
                .order_by(Fixture.kickoff)
            )
        )
        .scalars()
        .all()
    )
    if not fixtures:
        return {"status": "error", "reason": "inga Allsvenskan-fixtures"}

    # 1. Säsong (idempotent på primary_league_id + scope)
    season = (
        await session.execute(
            select(FantasySeason).where(
                FantasySeason.primary_league_id == league.id,
                FantasySeason.scope == FantasyScope.SINGLE_LEAGUE,
            )
        )
    ).scalar_one_or_none()
    if season is None:
        season = FantasySeason(
            name="Allsvenskan 2026",
            scope=FantasyScope.SINGLE_LEAGUE,
            primary_league_id=league.id,
            start_date=fixtures[0].kickoff.date(),
            end_date=fixtures[-1].kickoff.date(),
            total_budget_units=1000,
            is_active=True,
        )
        session.add(season)
        await session.flush()

    # 2. Gameweeks per ISO-vecka + fixture-länkar
    by_week: dict[int, list[Fixture]] = {}
    for f in fixtures:
        by_week.setdefault(f.kickoff.isocalendar().week, []).append(f)

    gw_created = 0
    link_created = 0
    for number, week in enumerate(sorted(by_week), start=1):
        fl = by_week[week]
        gw = (
            await session.execute(
                select(FantasyGameweek).where(
                    FantasyGameweek.season_id == season.id,
                    FantasyGameweek.gameweek_number == number,
                )
            )
        ).scalar_one_or_none()
        if gw is None:
            gw = FantasyGameweek(
                season_id=season.id,
                gameweek_number=number,
                deadline_at=fl[0].kickoff,
                first_kickoff_at=fl[0].kickoff,
                last_kickoff_at=fl[-1].kickoff,
                is_finalized=True,
            )
            session.add(gw)
            await session.flush()
            gw_created += 1

        linked = {
            r
            for (r,) in (
                await session.execute(
                    select(FantasyGameweekFixture.fixture_id).where(
                        FantasyGameweekFixture.gameweek_id == gw.id
                    )
                )
            ).all()
        }
        for f in fl:
            if f.id not in linked:
                session.add(
                    FantasyGameweekFixture(gameweek_id=gw.id, fixture_id=f.id)
                )
                link_created += 1

    # 3. Pricing för spelare i ligans lag
    team_ids: set[int] = set()
    for f in fixtures:
        team_ids.add(f.home_team_id)
        team_ids.add(f.away_team_id)

    players = (
        (
            await session.execute(
                select(Player).where(Player.current_team_id.in_(team_ids))
            )
        )
        .scalars()
        .all()
    )
    priced = {
        r
        for (r,) in (
            await session.execute(
                select(FantasyPlayerPricing.player_id).where(
                    FantasyPlayerPricing.season_id == season.id
                )
            )
        ).all()
    }
    price_created = 0
    for p in players:
        if p.id in priced:
            continue
        price = _PRICE_BY_POSITION.get(p.position_code or "", _DEFAULT_PRICE)
        session.add(
            FantasyPlayerPricing(
                player_id=p.id,
                season_id=season.id,
                current_price=price,
                starting_price=price,
            )
        )
        price_created += 1

    await session.commit()
    return {
        "status": "ok",
        "season_id": season.id,
        "gameweeks_created": gw_created,
        "fixture_links_created": link_created,
        "players_priced": price_created,
        "players_in_league": len(players),
    }
