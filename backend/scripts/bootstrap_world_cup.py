"""VM 2026 bootstrap — seed liga 732 + säsong + nationslag + alla fixtures.

Idempotent: kan köras flera gånger. Använder befintliga normalizer-helpers
(find_or_create_league/team/season) som upsertar via provider_entity_mappings.
Sätter därutöver stage_name + group_letter på Fixture-rader (12 grupper A–L
+ 7 stages: Group Stage, Round of 32, R16, QF, SF, 3rd Place Final, Final).

Kör:
    docker compose exec backend python -m scripts.bootstrap_world_cup

Verifierar live: 48 lag, 12 grupper, 104 fixtures (8 jun 2026 enligt SportMonks).
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy import select

from app.core.database import async_session
from app.models.models import Fixture, League, MatchStatus, Season
from app.services.sportmonks_normalizer import (
    find_or_create_league,
    find_or_create_season,
    find_or_create_team,
    record_mapping,
    record_payload,
)


WC_LEAGUE_EXT = "732"
WC_SEASON_LABEL = "2026"
WC_YEAR_START = 2026

# SportMonks stage_id → mänskligt namn
_STAGE_NAMES: dict[int, str] = {
    77478590: "Group Stage",
    77479086: "Round of 32",
    77479087: "Round of 16",
    77479088: "Quarter-finals",
    77479089: "Semi-finals",
    77479090: "Final",
    77479091: "3rd Place Final",
}

# SportMonks group_id → grupp-bokstav A..L (12 grupper för VM 2026, 48-lags-format)
_GROUP_LETTERS: dict[int, str] = {
    253019 + i: chr(ord("A") + i) for i in range(12)
}

# SportMonks state-id → ScoreLock MatchStatus
_STATE_TO_STATUS: dict[int, MatchStatus] = {
    1: MatchStatus.SCHEDULED,  # NS — Not Started
    2: MatchStatus.LIVE,       # INPLAY_1ST_HALF
    3: MatchStatus.LIVE,       # INPLAY_2ND_HALF
    4: MatchStatus.LIVE,       # INPLAY_ET
    5: MatchStatus.FINISHED,   # FT
    6: MatchStatus.LIVE,       # AET_BREAK
    7: MatchStatus.LIVE,       # INPLAY_PEN
    8: MatchStatus.FINISHED,   # AET
    9: MatchStatus.POSTPONED,  # POSTPONED
    10: MatchStatus.CANCELLED, # CANCELLED
    11: MatchStatus.FINISHED,  # ABANDONED — räknas som färdig (resultat står)
    12: MatchStatus.AWARDED,   # AWARDED
    14: MatchStatus.FINISHED,  # FT_PEN
    22: MatchStatus.HALFTIME,  # HT
    25: MatchStatus.LIVE,      # EXTRA_TIME
    26: MatchStatus.LIVE,      # PEN_LIVE
}


def _map_status(state: dict[str, Any] | None) -> MatchStatus:
    if not state:
        return MatchStatus.SCHEDULED
    return _STATE_TO_STATUS.get(state.get("id"), MatchStatus.SCHEDULED)


def _round_label(group_letter: str | None, round_payload: dict | None, stage_name: str) -> str:
    """Skapa läsbar round-label: 'Grupp A — Omgång 1' eller 'Åttondelsfinaler'."""
    if group_letter and round_payload:
        rnum = round_payload.get("name", "")
        return f"Grupp {group_letter} — Omgång {rnum}".strip()
    sv_stage = {
        "Group Stage": "Gruppspel",
        "Round of 32": "Sextondelsfinal",
        "Round of 16": "Åttondelsfinal",
        "Quarter-finals": "Kvartsfinal",
        "Semi-finals": "Semifinal",
        "Final": "Final",
        "3rd Place Final": "Bronsmatch",
    }
    return sv_stage.get(stage_name, stage_name)


async def fetch_all_wc_fixtures(token: str) -> list[dict[str, Any]]:
    """Hämta alla VM 2026-fixtures via /fixtures/between, paginerat."""
    base = "https://api.sportmonks.com/v3/football/fixtures/between/2026-06-01/2026-07-31"
    params = {
        "api_token": token,
        "filters": f"fixtureLeagues:{WC_LEAGUE_EXT}",
        "include": "participants;stage;group;round;state;league",
        "per_page": 50,
    }
    fixtures: list[dict[str, Any]] = []
    page = 1
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            resp = await client.get(base, params={**params, "page": page})
            resp.raise_for_status()
            data = resp.json()
            fixtures.extend(data.get("data", []))
            if not data.get("pagination", {}).get("has_more"):
                break
            page += 1
            if page > 10:
                break
    return fixtures


async def upsert_wc_season(session, league: League) -> Season:
    """Skapa eller hämta WC 2026-säsongen (year_start=2026, label='2026')."""
    result = await session.execute(
        select(Season).where(
            Season.league_id == league.id,
            Season.year_start == WC_YEAR_START,
        )
    )
    season = result.scalar_one_or_none()
    if season is not None:
        # Idempotent: säkerställ label + is_current
        season.label = WC_SEASON_LABEL
        season.is_current = True
        season.start_date = datetime(2026, 6, 11).date()
        season.end_date = datetime(2026, 7, 19).date()
        return season

    season = Season(
        league_id=league.id,
        year_start=WC_YEAR_START,
        label=WC_SEASON_LABEL,
        is_current=True,
        start_date=datetime(2026, 6, 11).date(),
        end_date=datetime(2026, 7, 19).date(),
        external_ids={"sportmonks": "wc-2026"},
    )
    session.add(season)
    await session.flush()
    return season


async def upsert_wc_fixture(
    session, league: League, season: Season, payload: dict[str, Any]
) -> Fixture | None:
    """Upserta en VM-match. Returnera None om TBD/saknar deltagare."""
    fid = str(payload["id"])

    # Stage + group
    stage_id = payload.get("stage_id")
    stage_name = _STAGE_NAMES.get(stage_id, "Unknown")
    group_id = payload.get("group_id")
    group_letter = _GROUP_LETTERS.get(group_id) if group_id else None
    round_label = _round_label(group_letter, payload.get("round"), stage_name)

    # Deltagare
    parts = {
        (p.get("meta") or {}).get("location"): p
        for p in (payload.get("participants") or [])
    }
    home_p, away_p = parts.get("home"), parts.get("away")
    if not home_p or not away_p:
        return None  # TBD-platser (vinnare av X vs Y) — hoppas, fyller på efter ompar

    home = await find_or_create_team(session, str(home_p["id"]), home_p)
    away = await find_or_create_team(session, str(away_p["id"]), away_p)

    # Status + tider
    status = _map_status(payload.get("state"))
    kickoff = datetime.fromisoformat(payload["starting_at"].replace(" ", "T"))

    # Resultat (om matchen är klar)
    scores = payload.get("scores", []) or []
    home_goals = away_goals = None
    home_ht = away_ht = None
    for s in scores:
        desc = (s.get("description") or "").upper()
        sc = s.get("score") or {}
        if desc == "CURRENT":
            home_goals = sc.get("goals") if sc.get("participant") == "home" else home_goals
            away_goals = sc.get("goals") if sc.get("participant") == "away" else away_goals
        elif desc == "1ST_HALF":
            home_ht = sc.get("goals") if sc.get("participant") == "home" else home_ht
            away_ht = sc.get("goals") if sc.get("participant") == "away" else away_ht

    # Idempotent upsert via external_id
    api_football_id = -int(fid)
    result = await session.execute(
        select(Fixture).where(Fixture.api_football_id == api_football_id)
    )
    fixture = result.scalar_one_or_none()
    if fixture is None:
        fixture = Fixture(
            api_football_id=api_football_id,
            league_id=league.id,
            season=season.year_start,
            season_id=season.id,
            round=round_label,
            stage_name=stage_name,
            group_letter=group_letter,
            home_team_id=home.id,
            away_team_id=away.id,
            kickoff=kickoff,
            status=status,
            home_goals=home_goals,
            away_goals=away_goals,
            home_goals_ht=home_ht,
            away_goals_ht=away_ht,
            external_ids={"sportmonks": fid},
        )
        session.add(fixture)
        await session.flush()
        await record_mapping(
            session,
            entity_type="fixture",
            external_id=fid,
            canonical_table="fixtures",
            canonical_id=fixture.id,
            source="bootstrap_world_cup",
        )
    else:
        fixture.league_id = league.id
        fixture.season_id = season.id
        fixture.round = round_label
        fixture.stage_name = stage_name
        fixture.group_letter = group_letter
        fixture.home_team_id = home.id
        fixture.away_team_id = away.id
        fixture.kickoff = kickoff
        fixture.status = status
        if home_goals is not None:
            fixture.home_goals = home_goals
        if away_goals is not None:
            fixture.away_goals = away_goals
        if home_ht is not None:
            fixture.home_goals_ht = home_ht
        if away_ht is not None:
            fixture.away_goals_ht = away_ht
        fixture.external_ids = {**(fixture.external_ids or {}), "sportmonks": fid}

    await session.flush()
    return fixture


async def run() -> None:
    token = os.environ.get("SPORTMONKS_API_TOKEN")
    if not token:
        raise SystemExit("SPORTMONKS_API_TOKEN saknas")

    print("== VM 2026 bootstrap ==")
    print("Hämtar fixtures från SportMonks /fixtures/between (paginerat)...")
    payloads = await fetch_all_wc_fixtures(token)
    print(f"  → {len(payloads)} fixture-payloads hämtade")

    # Konstruera ett league-payload utifrån vad SportMonks returnerar (eller manuellt)
    league_payload: dict[str, Any] = (
        payloads[0].get("league") if payloads else {}
    ) or {}
    league_payload = {
        "id": int(WC_LEAGUE_EXT),
        "name": league_payload.get("name") or "FIFA World Cup",
        "type": "cup",
        "image_path": league_payload.get("image_path"),
        "country_id": league_payload.get("country_id"),
    }

    async with async_session() as session:
        # 1) League
        league = await find_or_create_league(session, WC_LEAGUE_EXT, league_payload)
        league.type = "cup"
        if league.name in (None, "", "sportmonks-league-732"):
            league.name = "FIFA World Cup"
        await session.flush()
        print(f"  liga: id={league.id} '{league.name}' (type={league.type})")

        # 2) Season
        season = await upsert_wc_season(session, league)
        print(f"  säsong: id={season.id} year_start={season.year_start} label='{season.label}'")

        # 3) Fixtures + lag
        ok = skip = errors = 0
        for payload in payloads:
            try:
                f = await upsert_wc_fixture(session, league, season, payload)
                if f is None:
                    skip += 1
                else:
                    ok += 1
            except Exception as exc:  # noqa: BLE001 — logga + fortsätt
                errors += 1
                print(f"    fel {payload.get('id')}: {type(exc).__name__}: {str(exc)[:80]}")

        await session.commit()

        # Sammanställning
        total_teams = await session.execute(
            select(Fixture.home_team_id).where(Fixture.league_id == league.id).distinct()
        )
        team_count = len({r[0] for r in total_teams.all()})

    print(f"\nKLART: {ok} fixtures persistade · {skip} TBD-platser hoppade · {errors} fel")
    print(f"  → {team_count} unika lag länkade till VM-ligan ({league.id})")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
