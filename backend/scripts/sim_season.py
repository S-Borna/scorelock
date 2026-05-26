"""ScoreLock peak-säsong-simulering — fake live över alla ligor.

Off-season ger en tom sida; detta ger en LEVANDE peak-säsong-miljö att polera UI
mot, som om det vore högsäsong med många samtidiga live-matcher. Rör ALDRIG prod —
kör mot lokal docker-DB och publicerar via SAMMA Redis→WS-väg som riktiga live-
spinen (publish_score_update), så frontend inte ser någon skillnad.

  docker compose exec backend python -m scripts.sim_season setup   # seed peak-omgång
  docker compose exec backend python -m scripts.sim_season run --speed 30  # fake-live
  docker compose exec backend python -m scripts.sim_season reset   # rensa sim-matcher

--speed N: matchminuter per verklig sekund (30 ⇒ en 90-min-match på ~3 s).

Sim-matcher märks med external_ids={"sim":"1"} + api_football_id i 9·10^8-serien.
"""
from __future__ import annotations

import argparse
import asyncio
import random
from datetime import datetime, timedelta

from sqlalchemy import delete, select

from app.core.database import async_session
from app.models.models import (
    Fixture,
    FixtureEvent,
    FixtureStatistics,
    League,
    MatchStatus,
    Odds,
    Prediction,
    Team,
)

_SIM_LEAGUES = [
    "premier_league",
    "la_liga",
    "serie_a",
    "bundesliga",
    "champions_league",
    "allsvenskan",
]
_SIM_API_BASE = 900_000_000
_MATCHES_PER_LEAGUE = 5
_P_GOAL = 0.028  # per match-minut per fixture
_P_CARD = 0.020
_FULL_TIME = 90


def _is_sim(fixture: Fixture) -> bool:
    return bool((fixture.external_ids or {}).get("sim"))


async def _league_teams(session, league_id: int) -> list[int]:
    rows = (
        await session.execute(
            select(Fixture.home_team_id, Fixture.away_team_id).where(
                Fixture.league_id == league_id
            )
        )
    ).all()
    ids: set[int] = set()
    for h, a in rows:
        ids.add(h)
        ids.add(a)
    # Deduppa på lagnamn — cross-provider-dubbletter (samma klubb, två team_ids)
    # finns och skulle annars para ett lag mot sig självt.
    named = (
        await session.execute(select(Team.id, Team.name).where(Team.id.in_(ids)))
    ).all()
    by_name: dict[str, int] = {}
    for tid, name in named:
        key = (name or "").strip().lower()
        if key and key not in by_name:
            by_name[key] = tid
    return list(by_name.values())


async def setup() -> None:
    """Skapa en peak-omgång (matcher strax) över alla ligor + 1X2-odds."""
    now = datetime.utcnow()
    # Near-future kickoff: gör matcherna prediktions-berättigade (fönstret kräver
    # kickoff >= now). Live-motorn ignorerar kickoff och gör dem live ändå.
    kickoff = now + timedelta(minutes=15)
    counter = 0
    created = 0
    async with async_session() as session:
        for name in _SIM_LEAGUES:
            league = (
                await session.execute(select(League).where(League.name == name))
            ).scalar_one_or_none()
            if league is None:
                continue
            teams = await _league_teams(session, league.id)
            random.shuffle(teams)
            pairs = min(_MATCHES_PER_LEAGUE, len(teams) // 2)
            for i in range(pairs):
                home_id, away_id = teams[2 * i], teams[2 * i + 1]
                fixture = Fixture(
                    api_football_id=_SIM_API_BASE + counter,
                    league_id=league.id,
                    season=2026,
                    round="Sim-omgång",
                    home_team_id=home_id,
                    away_team_id=away_id,
                    kickoff=kickoff,
                    status=MatchStatus.SCHEDULED,
                    home_goals=None,
                    away_goals=None,
                    external_ids={"sim": "1"},
                )
                session.add(fixture)
                await session.flush()
                # Realistiska 1X2-odds (slumpad favorit).
                h = round(random.uniform(1.5, 3.6), 2)
                a = round(random.uniform(1.5, 3.6), 2)
                session.add(
                    Odds(
                        fixture_id=fixture.id,
                        bookmaker="SimBook",
                        market="1X2",
                        home_odds=h,
                        draw_odds=round(random.uniform(3.0, 4.2), 2),
                        away_odds=a,
                        fetched_at=now,
                    )
                )
                counter += 1
                created += 1
        await session.commit()
    print(f"Sim-setup klar: {created} matcher (avspark nu, SCHEDULED) över {len(_SIM_LEAGUES)} ligor.")
    print("Kör prediktioner: docker compose exec backend python -c "
          "\"from app.services.tasks import run_daily_predictions; print(run_daily_predictions())\"")
    print("Starta live: docker compose exec backend python -m scripts.sim_season run --speed 30")


async def _ensure_stats(session, fixture_id: int, team_id: int) -> FixtureStatistics:
    row = (
        await session.execute(
            select(FixtureStatistics).where(
                FixtureStatistics.fixture_id == fixture_id,
                FixtureStatistics.team_id == team_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        row = FixtureStatistics(
            fixture_id=fixture_id,
            team_id=team_id,
            possession_pct=50.0,
            shots_total=0,
            shots_on_target=0,
            corners=0,
            provider="sim",
        )
        session.add(row)
    return row


async def _tick_fixture(session, fixture: Fixture, publish) -> bool:
    """Avancera en match en minut. Returnerar True om matchen fortf. pågår."""
    minute = (fixture.live_minute or 0) + 1
    fixture.live_minute = minute
    if fixture.home_goals is None:
        fixture.home_goals = 0
        fixture.away_goals = 0
    fixture.status = MatchStatus.HALFTIME if minute in (45, 46) else MatchStatus.LIVE

    h_stats = await _ensure_stats(session, fixture.id, fixture.home_team_id)
    a_stats = await _ensure_stats(session, fixture.id, fixture.away_team_id)

    # Mål?
    if random.random() < _P_GOAL:
        home_scores = random.random() < 0.55  # hemmafördel
        scorer = fixture.home_team_id if home_scores else fixture.away_team_id
        if home_scores:
            fixture.home_goals += 1
            h_stats.shots_on_target = (h_stats.shots_on_target or 0) + 1
        else:
            fixture.away_goals += 1
            a_stats.shots_on_target = (a_stats.shots_on_target or 0) + 1
        session.add(
            FixtureEvent(
                fixture_id=fixture.id,
                minute=minute,
                event_type="GOAL",
                team_id=scorer,
                description="Mål (sim)",
                provider="sim",
            )
        )
    # Kort?
    if random.random() < _P_CARD:
        team = random.choice([fixture.home_team_id, fixture.away_team_id])
        session.add(
            FixtureEvent(
                fixture_id=fixture.id,
                minute=minute,
                event_type="YELLOW_CARD",
                team_id=team,
                description="Gult kort (sim)",
                provider="sim",
            )
        )
    # Statistik-drift
    h_stats.shots_total = (h_stats.shots_total or 0) + (1 if random.random() < 0.2 else 0)
    a_stats.shots_total = (a_stats.shots_total or 0) + (1 if random.random() < 0.2 else 0)
    h_stats.possession_pct = round(50 + random.uniform(-12, 12), 1)
    a_stats.possession_pct = round(100 - h_stats.possession_pct, 1)

    finished = minute >= _FULL_TIME
    if finished:
        fixture.status = MatchStatus.FINISHED

    await publish(
        fixture.id, fixture.home_goals, fixture.away_goals, fixture.status.value, minute
    )
    return not finished


async def run(speed: int) -> None:
    """Fake-live-motor: ticka matchminut, slumpa mål/kort, publicera WS."""
    from app.api.websocket import publish_score_update

    async def publish(fid, hg, ag, status, minute):
        await asyncio.to_thread(publish_score_update, fid, hg, ag, status, minute)

    interval = 1.0 / max(1, speed)
    print(f"Sim-live startar ({speed} matchminuter/sek). Ctrl-C för att avsluta.")
    while True:
        async with async_session() as session:
            sims = (
                (
                    await session.execute(
                        select(Fixture).where(
                            Fixture.api_football_id >= _SIM_API_BASE,
                            Fixture.status != MatchStatus.FINISHED,
                        )
                    )
                )
                .scalars()
                .all()
            )
            if not sims:
                print("Alla sim-matcher färdigspelade.")
                return
            live_count = 0
            for fixture in sims:
                if await _tick_fixture(session, fixture, publish):
                    live_count += 1
            await session.commit()
            any_minute = max((f.live_minute or 0) for f in sims)
            print(f"  minut ~{any_minute}' · {live_count} live · {len(sims) - live_count} slut denna tick")
        await asyncio.sleep(interval)


async def reset() -> None:
    """Ta bort alla sim-matcher + deras barn-rader."""
    async with async_session() as session:
        ids = (
            (
                await session.execute(
                    select(Fixture.id).where(Fixture.api_football_id >= _SIM_API_BASE)
                )
            )
            .scalars()
            .all()
        )
        if ids:
            for model in (FixtureEvent, FixtureStatistics, Odds, Prediction):
                await session.execute(delete(model).where(model.fixture_id.in_(ids)))
            await session.execute(delete(Fixture).where(Fixture.id.in_(ids)))
            await session.commit()
        print(f"Sim-reset klar: tog bort {len(ids)} sim-matcher.")


def main() -> None:
    p = argparse.ArgumentParser(description="ScoreLock peak-säsong-simulering")
    p.add_argument("command", choices=["setup", "run", "reset"])
    p.add_argument("--speed", type=int, default=30, help="Matchminuter per verklig sekund")
    args = p.parse_args()
    if args.command == "setup":
        asyncio.run(setup())
    elif args.command == "run":
        try:
            asyncio.run(run(args.speed))
        except KeyboardInterrupt:
            print("\nAvslutar sim-live.")
    else:
        asyncio.run(reset())


if __name__ == "__main__":
    main()
