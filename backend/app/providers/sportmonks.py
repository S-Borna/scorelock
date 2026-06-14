"""SportMonks Football API v3 provider — Phase 7.2.

Implementerar `SportsDataProvider`-protokollet i `app.providers.base`.

Två modes:
- **static**: läser från `/competitor-ref/sportmonks/payloads/*.json` (default
  pre-augusti). Möjliggör Phase 7-design utan tier-upgrade.
- **live**: httpx mot `https://api.sportmonks.com/v3/football` med
  `SPORTMONKS_KEY`. Aktiveras via `SPORTMONKS_USE_STATIC_FIXTURES=false`.

Toggle är ett env-flag-byte — inga UI- eller endpoint-ändringar krävs när
augusti-tier landar.

Static-payload-filer (förvarade som SportMonks Components UI-export, pretty
names med mellanslag):

    Match Centre.json          fixture detail (header + scores + venue + state)
    LineUp.json                lineups + xglineup + per-player details + events
    Events timeline.json       events[] (goals + cards + subs + VAR)
    xG Match.json              fixture med xgfixture[] team-level xG-suite
    Trends.json                per-minute running stat rollups
    Pressure Index.json        pressure[].participant time-series 0-100
    Standings.json             list[20] standings + form embedded
    Calendar.json              50 fixtures (team-schedule)
    Livescore.json             list[6] in-play fixtures
    Team Squad.json            24 players per team
    News Page.json             prematchNews + postmatchNews lines
    ...

Static-mode ignorerar fixture_external_id-arg eftersom alla payloads gäller
fixture 19425203 (Inter-Cagliari) — det är design-referensen.
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from app.core.config import Settings
from app.providers.base import (
    DateRange,
    LiveEventEnvelope,
    Operation,
    ProviderHealth,
    ProviderStatus,
    Scope,
)
from app.providers.errors import (
    ProviderAuthError,
    ProviderPayloadError,
    ProviderUnavailable,
    ProviderUnsupported,
)
from app.providers.normalization import (
    NormalizedFixture,
    NormalizedLineup,
    NormalizedLineupPlayer,
    NormalizedMatchEvent,
    NormalizedMatchStatistics,
    NormalizedPlayer,
    NormalizedStanding,
    NormalizedTeam,
)


logger = logging.getLogger(__name__)


# ── SportMonks state.developer_name → ScoreLock MatchStatus.name ────────
# Värden mappas till MatchStatus-enumets .name (UPPERCASE) — som SAEnum
# lagrar i Postgres. Nya värden från v0.6a3-migrationen finns med.
_STATE_MAP: dict[str, str] = {
    "NS": "SCHEDULED",
    "PENDING": "SCHEDULED",
    "TBA": "SCHEDULED",
    "INPLAY_1ST_HALF": "IN_PLAY",
    "INPLAY_2ND_HALF": "IN_PLAY",
    "HT": "HALFTIME",
    "INPLAY_ET": "IN_PROGRESS_EXTRA_TIME",
    "INPLAY_ET_2ND_HALF": "IN_PROGRESS_EXTRA_TIME",
    "BREAK_ET": "IN_PROGRESS_EXTRA_TIME",
    "PEN_BREAK": "IN_PROGRESS_PENALTIES",
    "INPLAY_PENALTIES": "IN_PROGRESS_PENALTIES",
    "FT": "FINISHED",
    "AET": "FINISHED",
    "AP": "FINISHED",
    "POSTPONED": "POSTPONED",
    "POSTP": "POSTPONED",
    "CANCELLED": "CANCELLED",
    "CANC": "CANCELLED",
    "ABANDONED": "SUSPENDED",
    "INTERRUPTED": "SUSPENDED",
    "SUSPENDED": "SUSPENDED",
    "AWARDED": "AWARDED",
    "AWARDED_AFTER_PENALTIES": "AWARDED",
}


# ── SportMonks event type.developer_name → ScoreLock event_type CHECK ──
_EVENT_TYPE_MAP: dict[str, str] = {
    "GOAL": "GOAL",
    "OWNGOAL": "OWN_GOAL",
    "OWN_GOAL": "OWN_GOAL",
    "PENALTY": "PENALTY_GOAL",
    "MISSED_PENALTY": "MISSED_PENALTY",
    "YELLOWCARD": "YELLOW_CARD",
    "REDCARD": "RED_CARD",
    "YELLOWREDCARD": "SECOND_YELLOW",
    "SUBSTITUTION": "SUBSTITUTION",
    "SUBSTITUTION_OFF": "SUBSTITUTION",
    "SUBSTITUTION_ON": "SUBSTITUTION",
    "VAR": "VAR_GOAL_AWARDED",  # info-fältet preciserar; default-fall hanteras nedan
    "VAR_CARD": "VAR_RED_CARD",
}

# Filnamn-konvention i Components-payload-katalogen (med mellanslag)
_FIXTURE_DETAIL_FILE = "Match Centre.json"
_LINEUP_FILE = "LineUp.json"
_EVENTS_FILE = "Events timeline.json"
_XG_FIXTURE_FILE = "xG Match.json"
_TRENDS_FILE = "Trends.json"
_PRESSURE_FILE = "Pressure Index.json"
_STANDINGS_FILE = "Standings.json"
_LIVE_STANDINGS_FILE = "Live Standings.json"
_CALENDAR_FILE = "Calendar.json"
_LIVESCORE_FILE = "Livescore.json"
_TEAM_SQUAD_FILE = "Team Squad.json"


class SportMonksProvider:
    """SportsDataProvider-implementation för SportMonks v3."""

    name: str = "sportmonks"
    supports: frozenset[Operation] = frozenset(
        {
            Operation.FIXTURES,
            Operation.LIVE_FIXTURES,
            Operation.STANDINGS,
            Operation.TEAMS,
            Operation.PLAYERS,
            Operation.LINEUPS,
            Operation.EVENTS,
            Operation.STATISTICS,
        }
    )

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._static_dir: Path | None = (
            Path(settings.sportmonks_static_payload_dir)
            if settings.sportmonks_use_static_fixtures
            else None
        )
        self._base_url = settings.sportmonks_base_url
        self._api_token = settings.sportmonks_api_token
        # Lazy httpx-client — bara live-mode bygger en
        self._client: httpx.AsyncClient | None = None

    # ── Settings / mode ─────────────────────────────────────

    @property
    def is_static(self) -> bool:
        return self._static_dir is not None

    # ── Internal helpers ────────────────────────────────────

    def _load_payload(self, filename: str) -> Any:
        if self._static_dir is None:
            raise ProviderUnsupported(
                "Static payload requested but provider runs in live mode"
            )
        path = self._static_dir / filename
        if not path.exists():
            raise ProviderPayloadError(
                f"Static payload missing: {path}"
            )
        try:
            with path.open(encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as exc:
            raise ProviderPayloadError(
                f"Invalid JSON in static payload {path}: {exc}"
            ) from exc

    async def _fetch_live(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self._api_token:
            raise ProviderAuthError(
                "SPORTMONKS_API_TOKEN env var not configured"
            )
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=15.0,
                headers={"Accept": "application/json"},
            )
        # SportMonks v3-konvention: api_token via query-param
        merged_params = {"api_token": self._api_token, **(params or {})}
        try:
            resp = await self._client.get(path, params=merged_params)
        except httpx.HTTPError as exc:
            raise ProviderUnavailable(
                f"SportMonks request failed: {exc}"
            ) from exc
        if resp.status_code in (401, 403):
            raise ProviderAuthError(
                f"SportMonks {resp.status_code}: {resp.text[:200]}"
            )
        if resp.status_code == 429:
            raise ProviderUnavailable("SportMonks rate-limited (429)")
        if resp.status_code >= 500:
            raise ProviderUnavailable(
                f"SportMonks 5xx: {resp.status_code}"
            )
        if resp.status_code >= 400:
            raise ProviderPayloadError(
                f"SportMonks {resp.status_code}: {resp.text[:200]}"
            )
        try:
            return resp.json()
        except ValueError as exc:
            raise ProviderPayloadError(
                f"SportMonks returned non-JSON: {exc}"
            ) from exc

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ── Parsers (raw payload → Normalized*) ─────────────────

    @staticmethod
    def _parse_kickoff(value: str | None) -> datetime:
        if not value:
            raise ProviderPayloadError("Missing starting_at on fixture payload")
        # SportMonks-format "2026-04-17 18:45:00" (UTC)
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(
            tzinfo=timezone.utc
        )

    @staticmethod
    def _map_status(state: dict[str, Any] | None) -> str:
        if not state:
            return "SCHEDULED"
        dev_name = state.get("developer_name") or state.get("state") or "NS"
        return _STATE_MAP.get(dev_name.upper(), "SCHEDULED")

    @staticmethod
    def _participants_split(
        participants: list[dict[str, Any]],
    ) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
        home = next(
            (p for p in participants if p.get("meta", {}).get("location") == "home"),
            None,
        )
        away = next(
            (p for p in participants if p.get("meta", {}).get("location") == "away"),
            None,
        )
        return home, away

    @staticmethod
    def _score_for(
        scores: list[dict[str, Any]],
        participant_id: int,
        description: str,
    ) -> int | None:
        for s in scores:
            if (
                s.get("participant_id") == participant_id
                and s.get("description") == description
            ):
                inner = s.get("score") or {}
                value = inner.get("goals")
                if value is not None:
                    return int(value)
        return None

    def _parse_fixture(self, payload: dict[str, Any]) -> NormalizedFixture:
        participants = payload.get("participants") or []
        home, away = self._participants_split(participants)
        if home is None or away is None:
            raise ProviderPayloadError(
                f"Fixture {payload.get('id')} missing home/away participant"
            )
        scores = payload.get("scores") or []
        venue = payload.get("venue") or {}
        # Live-minut: perioden med ticking=True bär aktuell minut (periods-include)
        ticking = next(
            (p for p in (payload.get("periods") or []) if p.get("ticking")), None
        )
        return NormalizedFixture(
            external_id=str(payload["id"]),
            league_external_id=str(payload.get("league_id") or ""),
            season_external_id=(
                str(payload["season_id"]) if payload.get("season_id") else None
            ),
            home_team_external_id=str(home["id"]),
            away_team_external_id=str(away["id"]),
            name=payload.get("name") or "",
            kickoff=self._parse_kickoff(payload.get("starting_at")),
            status=self._map_status(payload.get("state")),
            home_score=self._score_for(scores, home["id"], "CURRENT"),
            away_score=self._score_for(scores, away["id"], "CURRENT"),
            home_score_ht=self._score_for(scores, home["id"], "1ST_HALF"),
            away_score_ht=self._score_for(scores, away["id"], "1ST_HALF"),
            length_minutes=payload.get("length"),
            venue_external_id=str(venue["id"]) if venue.get("id") else None,
            referee_external_id=None,  # populated when /referees include är aktiv
            attendance=None,
            live_minute=ticking.get("minutes") if ticking else None,
            live_stoppage=None,
            raw_payload=payload,
        )

    def _parse_lineup_player(
        self,
        raw: dict[str, Any],
        num_rows: int = 0,
        max_col_in_row: dict[int, int] | None = None,
    ) -> NormalizedLineupPlayer:
        player = raw.get("player") or {}
        formation_field: str | None = raw.get("formation_field")
        grid_x = grid_y = None
        row_n: int | None = None
        if formation_field and ":" in formation_field:
            try:
                rr, cc = formation_field.split(":", 1)
                row_n = int(rr)
                col_n = int(cc)
                # Skala 1-N row, 1-M col → 0-100 percent (UI förväntar percent).
                if num_rows > 0 and max_col_in_row:
                    max_c = max_col_in_row.get(row_n, 1) or 1
                    grid_x = int(round((col_n - 0.5) / max_c * 100))
                    grid_y = int(round((row_n - 0.5) / num_rows * 100))
                else:
                    grid_x = col_n
                    grid_y = row_n
            except (ValueError, TypeError):
                grid_x = grid_y = None
                row_n = None
        # Position-code: prefer payload, fallback derivation från row-index.
        position_code = (raw.get("position") or {}).get("code") or raw.get(
            "position_name"
        )
        if not position_code and row_n is not None:
            if row_n == 1:
                position_code = "GK"
            elif row_n == num_rows and num_rows > 1:
                position_code = "FWD"
            elif row_n == 2:
                position_code = "DEF"
            else:
                position_code = "MID"
        details = raw.get("details") or []
        rating = None
        is_captain = False
        minutes_played = None
        for d in details:
            type_id = (d.get("type") or {}).get("id")
            value = d.get("value")
            if type_id == 118:  # rating
                try:
                    rating = float(value)
                except (TypeError, ValueError):
                    rating = None
            elif type_id == 40 and value:
                is_captain = True
            elif type_id == 119:  # minutes-played type-id
                try:
                    minutes_played = int(value)
                except (TypeError, ValueError):
                    minutes_played = None
        return NormalizedLineupPlayer(
            player_external_id=str(raw.get("player_id") or player.get("id") or ""),
            player_name=(
                player.get("display_name")
                or player.get("name")
                or player.get("common_name")
                or ""
            ),
            position_code=position_code,
            shirt_number=raw.get("jersey_number"),
            is_starter=bool(raw.get("type_id") == 11 or raw.get("formation_position")),
            is_captain=is_captain,
            formation_field=formation_field,
            grid_x=grid_x,
            grid_y=grid_y,
            rating=rating,
            minutes_played=minutes_played,
        )

    def _parse_lineups(
        self, payload: dict[str, Any], fixture_external_id: str
    ) -> list[NormalizedLineup]:
        lineups_raw = payload.get("lineups") or []
        coaches_raw = payload.get("coaches") or []
        coach_by_team: dict[int, str] = {}
        for c in coaches_raw:
            tid = (c.get("meta") or {}).get("participant_id")
            name = c.get("display_name") or c.get("name")
            if tid and name:
                coach_by_team[int(tid)] = name

        # SportMonks: rader per spelare; gruppera på participant_id
        by_team: dict[int, list[dict[str, Any]]] = {}
        for row in lineups_raw:
            team_id = row.get("team_id") or row.get("participant_id")
            if team_id is None:
                continue
            by_team.setdefault(int(team_id), []).append(row)

        out: list[NormalizedLineup] = []
        for team_id, rows in by_team.items():
            # Härled formation från starters: count per row, format "{def}-{mid}-{fwd}".
            row_counts: dict[int, int] = {}
            max_col_in_row: dict[int, int] = {}
            for r in rows:
                ff = r.get("formation_field")
                if not ff or ":" not in ff:
                    continue
                try:
                    rr, cc = ff.split(":", 1)
                    rr_i, cc_i = int(rr), int(cc)
                except (ValueError, TypeError):
                    continue
                row_counts[rr_i] = row_counts.get(rr_i, 0) + 1
                max_col_in_row[rr_i] = max(max_col_in_row.get(rr_i, 0), cc_i)

            formation: str | None = None
            num_rows = max(row_counts.keys()) if row_counts else 0
            if num_rows >= 2:
                # Hoppa över row 1 (GK) — formation skrivs på defenders/onwards.
                formation = "-".join(
                    str(row_counts[rr]) for rr in sorted(row_counts) if rr > 1
                ) or None

            players = tuple(
                self._parse_lineup_player(r, num_rows, max_col_in_row)
                for r in rows
            )
            out.append(
                NormalizedLineup(
                    fixture_external_id=fixture_external_id,
                    team_external_id=str(team_id),
                    formation=formation,
                    state="CONFIRMED",  # SportMonks ger bara confirmed lineups
                    manager_name=coach_by_team.get(team_id),
                    players=players,
                )
            )
        return out

    def _parse_events(
        self, payload: dict[str, Any], fixture_external_id: str
    ) -> list[NormalizedMatchEvent]:
        events_raw = payload.get("events") or []
        out: list[NormalizedMatchEvent] = []
        for ev in events_raw:
            type_obj = ev.get("type") or {}
            dev_name = (type_obj.get("developer_name") or "").upper()
            mapped = _EVENT_TYPE_MAP.get(dev_name)
            if mapped is None:
                # Filtrera bort PERIOD_START/END och okända typer från första pass
                continue
            out.append(
                NormalizedMatchEvent(
                    fixture_external_id=fixture_external_id,
                    external_id=str(ev.get("id")),
                    minute=ev.get("minute"),
                    stoppage=ev.get("extra_minute"),
                    event_type=mapped,
                    team_external_id=(
                        str(ev["participant_id"])
                        if ev.get("participant_id")
                        else None
                    ),
                    primary_player_external_id=(
                        str(ev["player_id"]) if ev.get("player_id") else None
                    ),
                    secondary_player_external_id=(
                        str(ev["related_player_id"])
                        if ev.get("related_player_id")
                        else None
                    ),
                    info=ev.get("info"),
                    addition=ev.get("addition"),
                    result=ev.get("result"),
                )
            )
        return out

    def _parse_statistics(
        self, payload: dict[str, Any], fixture_external_id: str
    ) -> list[NormalizedMatchStatistics]:
        # Components-payloads (Trends.json) använder `trends[]`; live-API med
        # `?include=statistics.type` använder `statistics[]`. Acceptera båda.
        stats_raw = payload.get("statistics") or payload.get("trends") or []
        # SportMonks lägger en rad per (participant, type, minute) — vi vill ha
        # senaste (max minute) per (participant, type)
        latest: dict[tuple[int, int], dict[str, Any]] = {}
        for row in stats_raw:
            participant_id = row.get("participant_id")
            type_id = row.get("type_id")
            minute = row.get("minute") or 0
            if participant_id is None or type_id is None:
                continue
            key = (int(participant_id), int(type_id))
            existing = latest.get(key)
            if existing is None or (existing.get("minute") or 0) < minute:
                latest[key] = row

        per_team: dict[int, dict[int, Any]] = {}
        as_of: dict[int, int] = {}
        for (participant_id, type_id), row in latest.items():
            # Live-API lägger värdet i nästlad `data.value`; trends/components
            # använder platt `value`. Acceptera båda.
            data = row.get("data")
            value = data.get("value") if isinstance(data, dict) else row.get("value")
            per_team.setdefault(participant_id, {})[type_id] = value
            minute = row.get("minute") or 0
            if minute > as_of.get(participant_id, 0):
                as_of[participant_id] = minute

        out: list[NormalizedMatchStatistics] = []
        for participant_id, stat_map in per_team.items():
            out.append(
                NormalizedMatchStatistics(
                    fixture_external_id=fixture_external_id,
                    team_external_id=str(participant_id),
                    stats=stat_map,
                    as_of_minute=as_of.get(participant_id),
                )
            )
        return out

    def _parse_team(self, raw: dict[str, Any]) -> NormalizedTeam:
        return NormalizedTeam(
            external_id=str(raw["id"]),
            name=raw.get("name") or "",
            short_code=raw.get("short_code"),
            country_external_id=(
                str(raw["country_id"]) if raw.get("country_id") else None
            ),
            founded=raw.get("founded"),
            image_ref=raw.get("image_path"),
            venue_external_id=(
                str(raw["venue_id"]) if raw.get("venue_id") else None
            ),
        )

    def _parse_standing(
        self, raw: dict[str, Any], league_external_id: str
    ) -> NormalizedStanding:
        details = raw.get("details") or []

        def _detail_value(type_codes: tuple[str, ...]) -> int:
            # SportMonks codes är kebab-case ("overall-matches-played",
            # "overall-won"). Normalisera båda former för robusthet.
            for d in details:
                code_raw = (d.get("type") or {}).get("code") or ""
                code = code_raw.lower().replace("-", "_")
                if code in type_codes:
                    try:
                        return int(d.get("value") or 0)
                    except (TypeError, ValueError):
                        return 0
            return 0

        return NormalizedStanding(
            league_external_id=league_external_id,
            season_external_id=(
                str(raw["season_id"]) if raw.get("season_id") else None
            ),
            team_external_id=str(raw.get("participant_id") or ""),
            position=int(raw.get("position") or 0),
            points=int(raw.get("points") or 0),
            played=_detail_value(
                ("overall_matches_played", "overall_played", "matches_played")
            ),
            won=_detail_value(("overall_won", "won")),
            drawn=_detail_value(("overall_draw", "draw", "overall_drawn")),
            lost=_detail_value(("overall_lost", "lost")),
            goals_for=_detail_value(
                ("overall_goals_scored", "overall_scored", "goals_scored")
            ),
            goals_against=_detail_value(
                ("overall_goals_conceded", "overall_conceded", "goals_conceded")
            ),
            form=raw.get("form"),
            zone=(raw.get("rule") or {}).get("type", {}).get("name"),
        )

    # ── Public Provider API ─────────────────────────────────

    async def fetch_fixture_detail(
        self, fixture_external_id: str
    ) -> NormalizedFixture:
        if self.is_static:
            payload = self._load_payload(_FIXTURE_DETAIL_FILE)
            return self._parse_fixture(payload)
        data = await self._fetch_live(
            f"/fixtures/{fixture_external_id}",
            params={
                "include": (
                    "participants;league;venue;state;scores;events.type;"
                    "events.player;lineups.player;lineups.details.type"
                )
            },
        )
        return self._parse_fixture(data.get("data", data))

    async def fetch_fixtures(
        self,
        league_external_id: str,
        season: int,
        window: DateRange | None = None,
    ) -> list[NormalizedFixture]:
        if self.is_static:
            payload = self._load_payload(_CALENDAR_FILE)
            # Calendar.json är list[league] — fixturer ligger i nested-shape.
            # För nu: hämta alla list-rader som ser ut som fixture-objekt.
            if isinstance(payload, list):
                return [
                    self._parse_fixture(item)
                    for item in payload
                    if isinstance(item, dict) and item.get("participants")
                ]
            return []
        # Live: /fixtures/between/{start}/{end}/{league_external_id}
        if window is None:
            raise ProviderUnsupported(
                "Live fetch_fixtures requires DateRange window"
            )
        data = await self._fetch_live(
            f"/fixtures/between/"
            f"{window.start.date().isoformat()}/{window.end.date().isoformat()}",
            params={
                "filters": f"fixtureLeagues:{league_external_id}",
                "include": "participants;league;venue;state;scores",
            },
        )
        items = data.get("data") or []
        return self._parse_fixtures_safe(items)

    def _parse_fixtures_safe(
        self, items: list[Any]
    ) -> list[NormalizedFixture]:
        """Parsa en batch fixture-payloads och hoppa enskilda trasiga.

        En korrupt live-payload (saknad participant, ogiltig state etc.) får
        ALDRIG ta ner hela inplay-cykeln — annars stannar uppdateringen av
        alla andra pågående matcher mitt i en omgång. Logga + skippa per item.
        """
        parsed: list[NormalizedFixture] = []
        for item in items:
            try:
                parsed.append(self._parse_fixture(item))
            except ProviderPayloadError as exc:
                logger.warning(
                    "sportmonks_fixture_payload_skipped: %s (id=%s)",
                    exc,
                    item.get("id") if isinstance(item, dict) else None,
                )
        return parsed

    async def fetch_live_fixtures(
        self,
        scope: Scope | None = None,
    ) -> list[NormalizedFixture]:
        if self.is_static:
            payload = self._load_payload(_LIVESCORE_FILE)
            if isinstance(payload, list):
                return [self._parse_fixture(item) for item in payload]
            return []
        data = await self._fetch_live(
            "/livescores/inplay",
            params={"include": "participants;league;state;scores;periods"},
        )
        items = data.get("data") or []
        return self._parse_fixtures_safe(items)

    async def fetch_lineup(
        self, fixture_external_id: str
    ) -> NormalizedLineup:
        # Protocol kräver single NormalizedLineup — returnera home-laget.
        # Använd `fetch_lineups` för båda lagen.
        all_lineups = await self.fetch_lineups(fixture_external_id)
        if not all_lineups:
            raise ProviderPayloadError(
                f"No lineup data for fixture {fixture_external_id}"
            )
        return all_lineups[0]

    async def fetch_lineups(
        self, fixture_external_id: str
    ) -> list[NormalizedLineup]:
        if self.is_static:
            payload = self._load_payload(_LINEUP_FILE)
            return self._parse_lineups(payload, fixture_external_id)
        data = await self._fetch_live(
            f"/fixtures/{fixture_external_id}",
            params={
                "include": "lineups.player;lineups.details.type;lineups.position;coaches"
            },
        )
        return self._parse_lineups(data.get("data") or {}, fixture_external_id)

    async def fetch_events(
        self, fixture_external_id: str
    ) -> list[NormalizedMatchEvent]:
        if self.is_static:
            payload = self._load_payload(_EVENTS_FILE)
            return self._parse_events(payload, fixture_external_id)
        data = await self._fetch_live(
            f"/fixtures/{fixture_external_id}",
            params={"include": "events.type;events.player;events.period"},
        )
        return self._parse_events(data.get("data") or {}, fixture_external_id)

    async def fetch_statistics(
        self, fixture_external_id: str
    ) -> NormalizedMatchStatistics:
        # Protocol-mismatch som med fetch_lineup — Protocol returnerar single
        # men SportMonks ger en per lag. Returnera home-laget; använd
        # `fetch_statistics_per_team` för båda.
        all_stats = await self.fetch_statistics_per_team(fixture_external_id)
        if not all_stats:
            raise ProviderPayloadError(
                f"No statistics data for fixture {fixture_external_id}"
            )
        return all_stats[0]

    async def fetch_statistics_per_team(
        self, fixture_external_id: str
    ) -> list[NormalizedMatchStatistics]:
        if self.is_static:
            payload = self._load_payload(_TRENDS_FILE)
            return self._parse_statistics(payload, fixture_external_id)
        data = await self._fetch_live(
            f"/fixtures/{fixture_external_id}",
            params={"include": "statistics.type;statistics.participant"},
        )
        return self._parse_statistics(data.get("data") or {}, fixture_external_id)

    async def fetch_standings(
        self,
        league_external_id: str,
        season: int,
    ) -> list[NormalizedStanding]:
        if self.is_static:
            payload = self._load_payload(_STANDINGS_FILE)
            if isinstance(payload, list):
                return [
                    self._parse_standing(row, league_external_id) for row in payload
                ]
            return []
        data = await self._fetch_live(
            f"/standings/seasons/{season}",
            params={"include": "participant;form;rule.type;details.type"},
        )
        items = data.get("data") or []
        return [self._parse_standing(row, league_external_id) for row in items]

    async def fetch_teams(
        self,
        league_external_id: str,
        season: int,
    ) -> list[NormalizedTeam]:
        if self.is_static:
            # Standings.json har participant-data per lag — pluka ut
            payload = self._load_payload(_STANDINGS_FILE)
            if not isinstance(payload, list):
                return []
            seen: dict[int, NormalizedTeam] = {}
            for row in payload:
                p = row.get("participant") or {}
                if p.get("id") and p["id"] not in seen:
                    seen[p["id"]] = self._parse_team(p)
            return list(seen.values())
        raise ProviderUnsupported(
            "fetch_teams live-mode kräver tier-uppgradering — implementeras Phase 11"
        )

    async def fetch_players(
        self,
        team_external_id: str,
    ) -> list[NormalizedPlayer]:
        if self.is_static:
            payload = self._load_payload(_TEAM_SQUAD_FILE)
            if not isinstance(payload, list):
                return []
            out: list[NormalizedPlayer] = []
            for row in payload:
                player = row.get("player") or {}
                if not player.get("id"):
                    continue
                pos = row.get("position") or {}
                out.append(
                    NormalizedPlayer(
                        external_id=str(player["id"]),
                        name=player.get("display_name")
                        or player.get("name")
                        or "",
                        common_name=player.get("common_name"),
                        nationality_external_id=(
                            str(player["nationality_id"])
                            if player.get("nationality_id")
                            else None
                        ),
                        position_code=pos.get("code") or pos.get("name"),
                        date_of_birth=None,
                        image_ref=player.get("image_path"),
                    )
                )
            return out
        raise ProviderUnsupported(
            "fetch_players live-mode kräver tier-uppgradering — implementeras Phase 11"
        )

    async def stream_live(
        self,
        scope: Scope | None = None,
    ) -> AsyncIterator[LiveEventEnvelope]:
        # Push-feed deferred till Phase 8 (WebSocket-pipeline)
        raise ProviderUnsupported("stream_live ej implementerad — Phase 8")
        yield  # type: ignore[unreachable]

    async def health(self) -> ProviderHealth:
        if self.is_static:
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.HEALTHY,
                latency_ms=0.0,
                last_error=None,
            )
        if not self._api_token:
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.DISABLED,
                last_error="SPORTMONKS_API_TOKEN not configured",
            )
        try:
            await self._fetch_live("/leagues", params={"per_page": 1})
            return ProviderHealth(
                provider=self.name, status=ProviderStatus.HEALTHY
            )
        except ProviderAuthError as exc:
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.DISABLED,
                last_error=str(exc),
            )
        except ProviderUnavailable as exc:
            return ProviderHealth(
                provider=self.name,
                status=ProviderStatus.UNAVAILABLE,
                last_error=str(exc),
            )
