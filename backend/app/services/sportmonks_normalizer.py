"""SportMonks normalizer — Phase 7.3.

Tar Normalized*-objekt från SportMonksProvider och persisterar till DB.

Ansvar:
- find_or_create för team/league/player/fixture via provider_entity_mappings
- lazy backfill av country_id/season_id på touched rader
- upsert lineups + lineup_players + events + statistics
- raw payload audit till provider_payloads

Bygger på SportMonksProvider-output i Phase 7.2. Konsumeras av sync-task i
Phase 7.4. Track S-1 (Allsvenskan-pipeline) använder samma helpers genom
SwedishSourceProvider.

Static-mode: alla payloads gäller fixture 19425203 (Inter-Cagliari) — den
används som test-fixture för end-to-end-validering.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select, and_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Country,
    Fixture,
    FixtureEvent,
    FixtureLineup,
    FixtureLineupPlayer,
    FixtureStatistics,
    League,
    MatchStatus,
    Player,
    ProviderEntityMapping,
    ProviderPayload,
    Season,
    Team,
)
from app.providers.normalization import (
    NormalizedFixture,
    NormalizedLineup,
    NormalizedMatchEvent,
    NormalizedMatchStatistics,
    NormalizedPlayer,
)
from app.providers.sportmonks import SportMonksProvider


logger = logging.getLogger(__name__)


PROVIDER = "sportmonks"


# ── SportMonks stat-type-id → FixtureStatistics-kolumn ──────────────────
# Verifierat mot Components-payloads + SportMonks /core/types?codes=...
_STAT_TYPE_TO_COLUMN: dict[int, str] = {
    34: "corners",
    41: "shots_off_target",
    42: "shots_on_target",
    44: None,  # dangerous-attacks — not stored, skip
    45: "possession_pct",
    47: None,  # penalties — skip
    51: None,  # ball-safe — skip
    52: None,  # attacks — skip
    56: "offsides",
    78: "shots_blocked",
    80: "passes_total",
    81: "passes_accurate",
    82: "pass_accuracy_pct",
    83: "red_cards_count",
    84: "yellow_cards_count",
    86: None,  # saves — skip
    6: "fouls",
    9676: "tackles",
    9677: "interceptions",
    5304: "xg",
}


# ── SportMonks country_id → ISO-2 (small map för augusti-launch-ligor) ──
# Lazy: utöka när nya ligor seedas. SE-fokus + Big-5.
_SPORTMONKS_COUNTRY_TO_ISO2: dict[int, str] = {
    251: "IT",   # Italy
    32: "ES",    # Spain
    11: "DE",    # Germany
    21: "FR",    # France
    462: "GB",   # England (SportMonks använder GB för PL)
    1161: "SE",  # Sweden
    320: "NL",   # Netherlands
    1218: "PT",  # Portugal
    584: "BE",   # Belgium
}


# ── Mapping & audit helpers ────────────────────────────────────────────


async def get_canonical_id(
    session: AsyncSession,
    entity_type: str,
    external_id: str,
) -> int | None:
    """Slå upp canonical-ID för (sportmonks, entity_type, external_id)."""
    stmt = select(ProviderEntityMapping.canonical_id).where(
        and_(
            ProviderEntityMapping.provider == PROVIDER,
            ProviderEntityMapping.entity_type == entity_type,
            ProviderEntityMapping.external_id == str(external_id),
        )
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def record_mapping(
    session: AsyncSession,
    entity_type: str,
    external_id: str,
    canonical_table: str,
    canonical_id: int,
    confidence: float = 1.0,
    source: str = "sportmonks_normalizer",
) -> None:
    """Upsert provider_entity_mappings-rad för spårbarhet."""
    stmt = (
        pg_insert(ProviderEntityMapping)
        .values(
            provider=PROVIDER,
            entity_type=entity_type,
            external_id=str(external_id),
            canonical_table=canonical_table,
            canonical_id=canonical_id,
            confidence=confidence,
            source=source,
        )
        .on_conflict_do_update(
            constraint="uq_provider_entity_external",
            set_={
                "canonical_table": canonical_table,
                "canonical_id": canonical_id,
                "confidence": confidence,
                "source": source,
                "updated_at": datetime.utcnow(),
            },
        )
    )
    await session.execute(stmt)


async def record_payload(
    session: AsyncSession,
    operation: str,
    entity_type: str,
    external_id: str,
    payload: dict[str, Any],
    canonical_table: str | None = None,
    canonical_id: int | None = None,
) -> None:
    """Audit-spår till provider_payloads. Hash för dedupering vid retry."""
    payload_json = json.dumps(payload, sort_keys=True, default=str)
    payload_hash = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    stmt = pg_insert(ProviderPayload).values(
        provider=PROVIDER,
        operation=operation,
        entity_type=entity_type,
        external_id=str(external_id),
        canonical_table=canonical_table,
        canonical_id=canonical_id,
        payload=payload,
        payload_hash=payload_hash,
        fetched_at=datetime.utcnow(),
    )
    await session.execute(stmt)


# ── Country backfill ────────────────────────────────────────────────────


async def resolve_country_id(
    session: AsyncSession,
    sportmonks_country_id: int | None,
) -> int | None:
    """Mappa SportMonks-country-id → ScoreLock countries.id via ISO-2."""
    if sportmonks_country_id is None:
        return None
    iso2 = _SPORTMONKS_COUNTRY_TO_ISO2.get(sportmonks_country_id)
    if iso2 is None:
        logger.warning(
            "Unknown SportMonks country_id=%s — skip country-backfill",
            sportmonks_country_id,
        )
        return None
    result = await session.execute(
        select(Country.id).where(Country.iso_2 == iso2)
    )
    canonical_id = result.scalar_one_or_none()
    if canonical_id is not None:
        await record_mapping(
            session,
            entity_type="country",
            external_id=str(sportmonks_country_id),
            canonical_table="countries",
            canonical_id=canonical_id,
        )
    return canonical_id


# ── League find-or-create ───────────────────────────────────────────────


async def find_or_create_league(
    session: AsyncSession,
    league_external_id: str,
    league_payload: dict[str, Any] | None = None,
) -> League:
    """Slå upp eller skapa League. Backfillar country_id + sport_id om saknas."""
    # 1. Mapping-träff
    mapped_id = await get_canonical_id(session, "league", league_external_id)
    if mapped_id is not None:
        league = await session.get(League, mapped_id)
        if league is not None:
            return await _maybe_backfill_league(session, league, league_payload)

    # 2. Fuzzy match på namn (för befintliga leagues utan SportMonks-mapping)
    if league_payload:
        name = league_payload.get("name")
        if name:
            result = await session.execute(
                select(League).where(League.name.ilike(name))
            )
            league = result.scalar_one_or_none()
            if league is not None:
                await record_mapping(
                    session,
                    entity_type="league",
                    external_id=str(league_external_id),
                    canonical_table="leagues",
                    canonical_id=league.id,
                    confidence=0.9,
                    source="sportmonks_name_fuzzy",
                )
                return await _maybe_backfill_league(session, league, league_payload)

    # 3. Skapa ny
    payload = league_payload or {}
    name = payload.get("name") or f"sportmonks-league-{league_external_id}"
    league = League(
        api_football_id=int(league_external_id) * -1,  # negative för att undvika krock
        name=name,
        country=str(payload.get("country_id") or ""),
        logo_url=payload.get("image_path"),
        type=payload.get("type") or "league",
        current_season=None,
        is_active=True,
        phase=2,
        external_ids={"sportmonks": str(league_external_id)},
    )
    session.add(league)
    await session.flush()
    await record_mapping(
        session,
        entity_type="league",
        external_id=str(league_external_id),
        canonical_table="leagues",
        canonical_id=league.id,
        source="sportmonks_create",
    )
    return await _maybe_backfill_league(session, league, league_payload)


async def _maybe_backfill_league(
    session: AsyncSession,
    league: League,
    league_payload: dict[str, Any] | None,
) -> League:
    """Backfilla country_id + external_ids om de saknas och payload har data."""
    dirty = False
    if league_payload:
        sportmonks_id = str(league_payload.get("id") or "")
        if sportmonks_id and league.external_ids.get("sportmonks") != sportmonks_id:
            league.external_ids = {**league.external_ids, "sportmonks": sportmonks_id}
            dirty = True
        if league.country_id is None and league_payload.get("country_id"):
            country_id = await resolve_country_id(
                session, league_payload["country_id"]
            )
            if country_id:
                league.country_id = country_id
                dirty = True
    if dirty:
        await session.flush()
    return league


# ── Team find-or-create ─────────────────────────────────────────────────


async def find_or_create_team(
    session: AsyncSession,
    team_external_id: str,
    team_payload: dict[str, Any] | None = None,
) -> Team:
    """Slå upp eller skapa Team. Backfillar country_id + venue + external_ids."""
    mapped_id = await get_canonical_id(session, "team", team_external_id)
    if mapped_id is not None:
        team = await session.get(Team, mapped_id)
        if team is not None:
            return await _maybe_backfill_team(session, team, team_payload)

    if team_payload:
        name = team_payload.get("name")
        if name:
            result = await session.execute(
                select(Team).where(Team.name.ilike(name))
            )
            team = result.scalar_one_or_none()
            if team is not None:
                await record_mapping(
                    session,
                    entity_type="team",
                    external_id=str(team_external_id),
                    canonical_table="teams",
                    canonical_id=team.id,
                    confidence=0.9,
                    source="sportmonks_name_fuzzy",
                )
                return await _maybe_backfill_team(session, team, team_payload)

    payload = team_payload or {}
    name = payload.get("name") or f"sportmonks-team-{team_external_id}"
    team = Team(
        api_football_id=int(team_external_id) * -1,  # negative undviker krock
        name=name,
        short_name=payload.get("short_code"),
        logo_url=payload.get("image_path"),
        country=None,
        venue_name=None,
        venue_capacity=None,
        external_ids={"sportmonks": str(team_external_id)},
    )
    session.add(team)
    await session.flush()
    await record_mapping(
        session,
        entity_type="team",
        external_id=str(team_external_id),
        canonical_table="teams",
        canonical_id=team.id,
        source="sportmonks_create",
    )
    return await _maybe_backfill_team(session, team, team_payload)


async def _maybe_backfill_team(
    session: AsyncSession,
    team: Team,
    team_payload: dict[str, Any] | None,
) -> Team:
    dirty = False
    if team_payload:
        sportmonks_id = str(team_payload.get("id") or "")
        if sportmonks_id and team.external_ids.get("sportmonks") != sportmonks_id:
            team.external_ids = {**team.external_ids, "sportmonks": sportmonks_id}
            dirty = True
        if team.country_id is None and team_payload.get("country_id"):
            country_id = await resolve_country_id(
                session, team_payload["country_id"]
            )
            if country_id:
                team.country_id = country_id
                dirty = True
    if dirty:
        await session.flush()
    return team


# ── Player find-or-create ───────────────────────────────────────────────


async def find_or_create_player(
    session: AsyncSession,
    player_external_id: str,
    player_payload: dict[str, Any] | None = None,
    current_team_id: int | None = None,
) -> Player:
    """Slå upp eller skapa Player. Players finns inte i seed pre-Phase 7 — skapa generously."""
    if not player_external_id:
        raise ValueError("player_external_id required")

    mapped_id = await get_canonical_id(session, "player", player_external_id)
    if mapped_id is not None:
        player = await session.get(Player, mapped_id)
        if player is not None:
            return player

    payload = player_payload or {}
    display_name = (
        payload.get("display_name")
        or payload.get("name")
        or payload.get("common_name")
        or f"sportmonks-player-{player_external_id}"
    )
    canonical_name = payload.get("common_name") or display_name
    position_code = (payload.get("position") or {}).get("code")
    if not position_code:
        position_code = payload.get("position_code")

    player = Player(
        canonical_name=canonical_name,
        display_name=display_name,
        position_code=position_code,
        current_team_id=current_team_id,
        external_ids={"sportmonks": str(player_external_id)},
    )
    session.add(player)
    await session.flush()
    await record_mapping(
        session,
        entity_type="player",
        external_id=str(player_external_id),
        canonical_table="players",
        canonical_id=player.id,
        source="sportmonks_create",
    )
    return player


# ── Season find-or-create ───────────────────────────────────────────────


async def find_or_create_season(
    session: AsyncSession,
    season_external_id: str | None,
    league_id: int,
) -> Season | None:
    """Mappa SportMonks season_id → Season-rad. Skapa om saknas."""
    if not season_external_id:
        return None
    mapped_id = await get_canonical_id(session, "season", season_external_id)
    if mapped_id is not None:
        return await session.get(Season, mapped_id)

    # Skapa minimal season-rad — year_start/label kan uppdateras vid Calendar-fetch
    year_start = datetime.utcnow().year
    season = Season(
        league_id=league_id,
        year_start=year_start,
        label=f"{year_start}/{year_start + 1}",
        is_current=True,
        external_ids={"sportmonks": str(season_external_id)},
    )
    session.add(season)
    await session.flush()
    await record_mapping(
        session,
        entity_type="season",
        external_id=str(season_external_id),
        canonical_table="seasons",
        canonical_id=season.id,
        source="sportmonks_create",
    )
    return season


# ── Fixture find-or-create ──────────────────────────────────────────────


async def find_or_create_fixture(
    session: AsyncSession,
    nf: NormalizedFixture,
    league: League,
    home_team: Team,
    away_team: Team,
    season: Season | None,
) -> Fixture:
    """Slå upp eller skapa Fixture. Uppdaterar score/status/live-state om finns."""
    mapped_id = await get_canonical_id(session, "fixture", nf.external_id)
    fixture: Fixture | None = None
    if mapped_id is not None:
        fixture = await session.get(Fixture, mapped_id)

    if fixture is None:
        fixture = Fixture(
            api_football_id=int(nf.external_id) * -1,
            league_id=league.id,
            season=season.year_start if season else nf.kickoff.year,
            round=None,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            kickoff=nf.kickoff.replace(tzinfo=None),
            status=MatchStatus[nf.status],
            home_goals=nf.home_score,
            away_goals=nf.away_score,
            home_goals_ht=nf.home_score_ht,
            away_goals_ht=nf.away_score_ht,
            external_ids={"sportmonks": nf.external_id},
            season_id=season.id if season else None,
            live_minute=nf.live_minute,
            live_stoppage=nf.live_stoppage,
            attendance=nf.attendance,
        )
        session.add(fixture)
        await session.flush()
        await record_mapping(
            session,
            entity_type="fixture",
            external_id=nf.external_id,
            canonical_table="fixtures",
            canonical_id=fixture.id,
            source="sportmonks_create",
        )
    else:
        # Uppdatera mutable fält
        fixture.status = MatchStatus[nf.status]
        fixture.home_goals = nf.home_score
        fixture.away_goals = nf.away_score
        fixture.home_goals_ht = nf.home_score_ht
        fixture.away_goals_ht = nf.away_score_ht
        if nf.live_minute is not None:
            fixture.live_minute = nf.live_minute
        if nf.live_stoppage is not None:
            fixture.live_stoppage = nf.live_stoppage
        if nf.attendance is not None:
            fixture.attendance = nf.attendance
        if season is not None and fixture.season_id is None:
            fixture.season_id = season.id
        fixture.external_ids = {
            **fixture.external_ids,
            "sportmonks": nf.external_id,
        }
    await session.flush()
    return fixture


# ── Lineup upsert ───────────────────────────────────────────────────────


async def upsert_lineup(
    session: AsyncSession,
    fixture: Fixture,
    nl: NormalizedLineup,
    team: Team,
    player_payloads_by_external_id: dict[str, dict[str, Any]] | None = None,
) -> FixtureLineup:
    """Upsert FixtureLineup + ersätt FixtureLineupPlayers helt."""
    # Hitta befintlig lineup för (fixture, team, provider)
    result = await session.execute(
        select(FixtureLineup).where(
            and_(
                FixtureLineup.fixture_id == fixture.id,
                FixtureLineup.team_id == team.id,
                FixtureLineup.provider == PROVIDER,
            )
        )
    )
    lineup = result.scalar_one_or_none()
    if lineup is None:
        lineup = FixtureLineup(
            fixture_id=fixture.id,
            team_id=team.id,
            formation=nl.formation,
            coach_name=nl.manager_name,
            provider=PROVIDER,
        )
        session.add(lineup)
        await session.flush()
    else:
        if nl.formation:
            lineup.formation = nl.formation
        if nl.manager_name:
            lineup.coach_name = nl.manager_name
        # Radera gamla lineup-players (replace-all-strategi)
        await session.execute(
            FixtureLineupPlayer.__table__.delete().where(
                FixtureLineupPlayer.lineup_id == lineup.id
            )
        )
        await session.flush()

    payloads = player_payloads_by_external_id or {}
    for nlp in nl.players:
        if not nlp.player_external_id:
            continue
        player = await find_or_create_player(
            session,
            player_external_id=nlp.player_external_id,
            player_payload=payloads.get(nlp.player_external_id, {"display_name": nlp.player_name, "position_code": nlp.position_code}),
            current_team_id=team.id,
        )
        session.add(
            FixtureLineupPlayer(
                lineup_id=lineup.id,
                player_id=player.id,
                shirt_number=nlp.shirt_number,
                position_label=nlp.position_code,
                grid_x=nlp.grid_x,
                grid_y=nlp.grid_y,
                is_starting=nlp.is_starter,
                is_captain=nlp.is_captain,
            )
        )
    await session.flush()
    return lineup


# ── Events upsert ───────────────────────────────────────────────────────


async def upsert_events(
    session: AsyncSession,
    fixture: Fixture,
    events: list[NormalizedMatchEvent],
    team_id_by_external: dict[str, int],
) -> int:
    """Upsert events idempotent — skip om redan finns med samma external_id."""
    written = 0
    for ev in events:
        if not ev.external_id:
            continue
        team_id = (
            team_id_by_external.get(ev.team_external_id)
            if ev.team_external_id
            else None
        )
        primary_player_id = None
        if ev.primary_player_external_id:
            player = await find_or_create_player(
                session, ev.primary_player_external_id
            )
            primary_player_id = player.id
        secondary_player_id = None
        if ev.secondary_player_external_id:
            player = await find_or_create_player(
                session, ev.secondary_player_external_id
            )
            secondary_player_id = player.id

        stmt = (
            pg_insert(FixtureEvent)
            .values(
                fixture_id=fixture.id,
                minute=ev.minute or 0,
                stoppage=ev.stoppage,
                event_type=ev.event_type,
                team_id=team_id,
                primary_player_id=primary_player_id,
                secondary_player_id=secondary_player_id,
                description=ev.info,
                provider=PROVIDER,
                external_id=ev.external_id,
            )
            .on_conflict_do_update(
                constraint="uq_fixture_event_provider_external",
                set_={
                    "minute": ev.minute or 0,
                    "stoppage": ev.stoppage,
                    "event_type": ev.event_type,
                    "team_id": team_id,
                    "primary_player_id": primary_player_id,
                    "secondary_player_id": secondary_player_id,
                    "description": ev.info,
                },
            )
        )
        await session.execute(stmt)
        written += 1
    return written


# ── Statistics upsert ───────────────────────────────────────────────────


def _stats_to_columns(
    stats: dict[int, float | int | None],
) -> dict[str, float | int]:
    """Mappa SportMonks stat-type-IDs till FixtureStatistics-kolumner."""
    out: dict[str, float | int] = {}
    for type_id, value in stats.items():
        column = _STAT_TYPE_TO_COLUMN.get(type_id)
        if column is None or value is None:
            continue
        try:
            if column.endswith("_pct") or column == "xg":
                out[column] = float(value)
            else:
                out[column] = int(value)
        except (TypeError, ValueError):
            continue
    return out


async def upsert_statistics(
    session: AsyncSession,
    fixture: Fixture,
    team_stats: list[NormalizedMatchStatistics],
    team_id_by_external: dict[str, int],
) -> int:
    """Upsert FixtureStatistics per (fixture, team)."""
    written = 0
    for ns in team_stats:
        team_id = team_id_by_external.get(ns.team_external_id)
        if team_id is None:
            logger.warning(
                "Stats för okänt team external_id=%s — skip",
                ns.team_external_id,
            )
            continue
        columns = _stats_to_columns(ns.stats)
        if not columns:
            continue

        # Hitta eller skapa
        result = await session.execute(
            select(FixtureStatistics).where(
                and_(
                    FixtureStatistics.fixture_id == fixture.id,
                    FixtureStatistics.team_id == team_id,
                )
            )
        )
        stat_row = result.scalar_one_or_none()
        if stat_row is None:
            stat_row = FixtureStatistics(
                fixture_id=fixture.id,
                team_id=team_id,
                provider=PROVIDER,
                as_of_minute=ns.as_of_minute,
                **columns,
            )
            session.add(stat_row)
        else:
            stat_row.provider = PROVIDER
            stat_row.as_of_minute = ns.as_of_minute or stat_row.as_of_minute
            for col, val in columns.items():
                setattr(stat_row, col, val)
        written += 1
    await session.flush()
    return written


# ── High-level orchestrator ─────────────────────────────────────────────


async def sync_fixture_detail(
    session: AsyncSession,
    provider: SportMonksProvider,
    fixture_external_id: str,
) -> Fixture:
    """End-to-end sync av en fixture från SportMonks till DB.

    Steg:
    1. fetch_fixture_detail → audit raw payload + parse
    2. find_or_create league (med country-backfill)
    3. find_or_create home + away teams
    4. find_or_create season
    5. find_or_create fixture (idempotent score/status-update)
    6. fetch_lineups → find_or_create players + upsert lineups
    7. fetch_events → upsert events (idempotent on external_id)
    8. fetch_statistics → upsert statistics per team

    Returnerar: Fixture (komplett, persisted, flushed).
    """
    nf = await provider.fetch_fixture_detail(fixture_external_id)
    league_payload = nf.raw_payload.get("league") or {}
    home_payload = next(
        (
            p
            for p in (nf.raw_payload.get("participants") or [])
            if p.get("meta", {}).get("location") == "home"
        ),
        {},
    )
    away_payload = next(
        (
            p
            for p in (nf.raw_payload.get("participants") or [])
            if p.get("meta", {}).get("location") == "away"
        ),
        {},
    )

    # 1. Audit raw payload
    await record_payload(
        session,
        operation="fixture_detail",
        entity_type="fixture",
        external_id=fixture_external_id,
        payload=nf.raw_payload,
    )

    # 2-4. Hierarki
    league = await find_or_create_league(
        session, nf.league_external_id, league_payload
    )
    home_team = await find_or_create_team(
        session, nf.home_team_external_id, home_payload
    )
    away_team = await find_or_create_team(
        session, nf.away_team_external_id, away_payload
    )
    season = await find_or_create_season(
        session, nf.season_external_id, league.id
    )

    # 5. Fixture
    fixture = await find_or_create_fixture(
        session, nf, league, home_team, away_team, season
    )

    # Bygg team-mapping för events + statistics
    team_id_by_external = {
        nf.home_team_external_id: home_team.id,
        nf.away_team_external_id: away_team.id,
    }

    # 6. Lineups
    lineups = await provider.fetch_lineups(fixture_external_id)
    # Bygg player-payload-lookup från lineup-payload (för bättre player-data)
    lineup_payload = (
        provider._load_payload("LineUp.json") if provider.is_static else None
    )
    player_payloads: dict[str, dict[str, Any]] = {}
    if lineup_payload:
        for row in lineup_payload.get("lineups") or []:
            pid = row.get("player_id")
            if pid and "player" in row:
                player_payloads[str(pid)] = row["player"]

    for nl in lineups:
        team = home_team if nl.team_external_id == str(home_team.external_ids.get("sportmonks", nf.home_team_external_id)) else away_team
        # Säkrare: matcha på SportMonks-id
        if nl.team_external_id == nf.home_team_external_id:
            team = home_team
        elif nl.team_external_id == nf.away_team_external_id:
            team = away_team
        else:
            logger.warning(
                "Lineup för okänt team external_id=%s — skip",
                nl.team_external_id,
            )
            continue
        await upsert_lineup(session, fixture, nl, team, player_payloads)

    # 7. Events
    events = await provider.fetch_events(fixture_external_id)
    written_events = await upsert_events(
        session, fixture, events, team_id_by_external
    )
    logger.info("Synkade %d events för fixture %s", written_events, nf.external_id)

    # 8. Statistics
    stats = await provider.fetch_statistics_per_team(fixture_external_id)
    written_stats = await upsert_statistics(
        session, fixture, stats, team_id_by_external
    )
    logger.info(
        "Synkade %d stat-rows för fixture %s", written_stats, nf.external_id
    )

    return fixture
