"""Normalized domain types — provider payload → canonical shape.

Provider-adapters returnerar instanser av dessa dataklasser. Normalizer-task
i Phase 7.3 mappar dem till DB-rader + provider_entity_mappings.

Fält tillagda i Phase 7.2 — minimal subset för fixture/lineup/event/statistics/
team/standing-flödet. Resten landar när ytterligare entiteter behövs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class NormalizedSport:
    external_id: str
    code: str
    display_name: str


@dataclass(frozen=True)
class NormalizedCountry:
    external_id: str
    iso_2: str | None
    iso_3: str | None
    display_name: str


@dataclass(frozen=True)
class NormalizedCompetition:
    external_id: str
    name: str
    country_external_id: str | None
    type: str
    tier: int | None = None


@dataclass(frozen=True)
class NormalizedSeason:
    external_id: str
    league_external_id: str
    year_start: int
    label: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_current: bool = False


@dataclass(frozen=True)
class NormalizedTeam:
    external_id: str
    name: str
    short_code: str | None = None
    country_external_id: str | None = None
    founded: int | None = None
    image_ref: str | None = None
    venue_external_id: str | None = None


@dataclass(frozen=True)
class NormalizedPlayer:
    external_id: str
    name: str
    common_name: str | None = None
    nationality_external_id: str | None = None
    position_code: str | None = None
    date_of_birth: datetime | None = None
    image_ref: str | None = None


@dataclass(frozen=True)
class NormalizedFixture:
    external_id: str
    league_external_id: str
    season_external_id: str | None
    home_team_external_id: str
    away_team_external_id: str
    name: str
    kickoff: datetime
    status: str  # canonical MatchStatus.name (UPPERCASE)
    home_score: int | None = None
    away_score: int | None = None
    home_score_ht: int | None = None
    away_score_ht: int | None = None
    length_minutes: int | None = None
    venue_external_id: str | None = None
    referee_external_id: str | None = None
    attendance: int | None = None
    live_minute: int | None = None
    live_stoppage: int | None = None
    raw_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class NormalizedLineupPlayer:
    player_external_id: str
    player_name: str
    position_code: str | None
    shirt_number: int | None
    is_starter: bool
    is_captain: bool
    formation_field: str | None  # SportMonks-format "row:col" — pixel-perfect pitch
    grid_x: int | None = None
    grid_y: int | None = None
    rating: float | None = None
    minutes_played: int | None = None


@dataclass(frozen=True)
class NormalizedLineup:
    fixture_external_id: str
    team_external_id: str
    formation: str | None
    state: str  # 'PROJECTED' | 'CONFIRMED'
    manager_name: str | None
    players: tuple[NormalizedLineupPlayer, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class NormalizedMatchEvent:
    fixture_external_id: str
    external_id: str
    minute: int | None
    stoppage: int | None
    event_type: str
    team_external_id: str | None
    primary_player_external_id: str | None = None
    secondary_player_external_id: str | None = None
    info: str | None = None
    addition: str | None = None
    result: str | None = None  # score-state efter event ("3-0")


@dataclass(frozen=True)
class NormalizedMatchStatistics:
    fixture_external_id: str
    team_external_id: str
    # type_id → value mapping (raw SportMonks stat-type-IDs)
    stats: dict[int, float | int | None] = field(default_factory=dict)
    as_of_minute: int | None = None


@dataclass(frozen=True)
class NormalizedStanding:
    league_external_id: str
    season_external_id: str | None
    team_external_id: str
    position: int
    points: int
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    form: str | None = None
    zone: str | None = None


@dataclass(frozen=True)
class NormalizedOddsSnapshot:
    """Canonical odds snapshot. Fields land when odds-provider integreras."""


@dataclass(frozen=True)
class NormalizedBookmaker:
    """Canonical bookmaker identity. Fields land när odds-provider integreras."""


@dataclass(frozen=True)
class NormalizedBroadcast:
    """Canonical broadcast entry. Fields land när broadcast-provider integreras."""


@dataclass(frozen=True)
class NormalizedVenue:
    external_id: str
    name: str
    city: str | None = None
    country_external_id: str | None = None
    capacity: int | None = None
    surface: str | None = None
    latitude: float | None = None
    longitude: float | None = None


@dataclass(frozen=True)
class NormalizedReferee:
    external_id: str
    name: str
    nationality_external_id: str | None = None


@dataclass(frozen=True)
class NormalizedWeatherSnapshot:
    """Canonical weather snapshot. Fields land när weather-provider integreras."""
