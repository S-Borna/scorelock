"""Protocol interfaces + core types for the provider abstraction layer.

This module defines only:
- Operation       — authoritative enum of provider operations
- OddsMarket      — enum of odds market types
- ProviderStatus  — coarse health status enum
- Scope           — scope descriptor used by the registry
- ProviderHealth  — status report shape per provider
- DateRange       — optional filter for fixture queries
- LiveEventEnvelope — placeholder wrapper for push-feed events
- 4 Protocol interfaces:
    SportsDataProvider, OddsProvider, BroadcastProvider, WeatherProvider

No concrete provider implementations live here. Implementations land in v0.5d.
Until then, no runtime code imports from this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import AsyncIterator, Protocol, runtime_checkable

from app.providers.normalization import (
    NormalizedBookmaker,
    NormalizedBroadcast,
    NormalizedFixture,
    NormalizedLineup,
    NormalizedMatchEvent,
    NormalizedMatchStatistics,
    NormalizedOddsSnapshot,
    NormalizedPlayer,
    NormalizedStanding,
    NormalizedTeam,
    NormalizedVenue,
    NormalizedWeatherSnapshot,
)


class Operation(str, Enum):
    """Authoritative list of operations the provider abstraction supports."""

    FIXTURES = "fixtures"
    LIVE_FIXTURES = "live_fixtures"
    STANDINGS = "standings"
    TEAMS = "teams"
    PLAYERS = "players"
    LINEUPS = "lineups"
    EVENTS = "events"
    STATISTICS = "statistics"
    ODDS = "odds"
    IN_PLAY_ODDS = "in_play_odds"
    BROADCASTS = "broadcasts"
    WEATHER = "weather"


class OddsMarket(str, Enum):
    """Odds market identifiers used by `OddsProvider`."""

    H2H = "h2h"
    TOTALS = "totals"
    SPREADS = "spreads"
    BTTS = "btts"
    CORRECT_SCORE = "correct_score"
    NEXT_GOAL = "next_goal"


class ProviderStatus(str, Enum):
    """Coarse health status reported by each provider."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"


@dataclass(frozen=True)
class Scope:
    """Scope descriptor used by the registry to select a provider rule.

    Kind conventions (enforced by the registry in v0.5d):
    - 'global'    — applies to all entities
    - 'country'   — value is an ISO 3166-1 alpha-2 code
    - 'league'    — value is a single league code
    - 'league_in' — value is a comma-separated list of league codes
    """

    kind: str = "global"
    value: str | None = None

    @classmethod
    def global_(cls) -> "Scope":
        return cls(kind="global", value=None)


@dataclass(frozen=True)
class ProviderHealth:
    """Status report for a single provider."""

    provider: str
    status: ProviderStatus
    latency_ms: float | None = None
    last_error: str | None = None
    quota_remaining: dict[str, int] | None = None
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class DateRange:
    """Inclusive UTC date range used as an optional filter on fixture queries."""

    start: datetime
    end: datetime


@dataclass(frozen=True)
class LiveEventEnvelope:
    """Wrapper for a single push-feed event. Fields land in v0.5d."""


@runtime_checkable
class SportsDataProvider(Protocol):
    """Provider for fixtures, teams, players, lineups, events, statistics."""

    name: str
    supports: frozenset[Operation]

    async def fetch_fixtures(
        self,
        league_external_id: str,
        season: int,
        window: DateRange | None = None,
    ) -> list[NormalizedFixture]: ...

    async def fetch_fixture_detail(
        self,
        fixture_external_id: str,
    ) -> NormalizedFixture: ...

    async def fetch_live_fixtures(
        self,
        scope: Scope | None = None,
    ) -> list[NormalizedFixture]: ...

    async def fetch_standings(
        self,
        league_external_id: str,
        season: int,
    ) -> list[NormalizedStanding]: ...

    async def fetch_teams(
        self,
        league_external_id: str,
        season: int,
    ) -> list[NormalizedTeam]: ...

    async def fetch_players(
        self,
        team_external_id: str,
    ) -> list[NormalizedPlayer]: ...

    async def fetch_lineup(
        self,
        fixture_external_id: str,
    ) -> NormalizedLineup: ...

    async def fetch_events(
        self,
        fixture_external_id: str,
    ) -> list[NormalizedMatchEvent]: ...

    async def fetch_statistics(
        self,
        fixture_external_id: str,
    ) -> NormalizedMatchStatistics: ...

    async def stream_live(
        self,
        scope: Scope | None = None,
    ) -> AsyncIterator[LiveEventEnvelope]: ...

    async def health(self) -> ProviderHealth: ...


@runtime_checkable
class OddsProvider(Protocol):
    """Provider for pre-match and in-play odds."""

    name: str
    supports: frozenset[OddsMarket]

    async def fetch_odds(
        self,
        fixture_external_ids: list[str],
        markets: list[OddsMarket],
        regions: list[str] | None = None,
    ) -> list[NormalizedOddsSnapshot]: ...

    async def fetch_in_play_odds(
        self,
        fixture_external_id: str,
        markets: list[OddsMarket],
    ) -> list[NormalizedOddsSnapshot]: ...

    async def fetch_bookmakers(
        self,
        regions: list[str] | None = None,
    ) -> list[NormalizedBookmaker]: ...

    async def health(self) -> ProviderHealth: ...


@runtime_checkable
class BroadcastProvider(Protocol):
    """Provider for TV / streaming broadcast availability per region."""

    name: str
    supported_countries: frozenset[str]

    async def fetch_broadcasts(
        self,
        fixture_external_id: str,
        countries: list[str] | None = None,
    ) -> list[NormalizedBroadcast]: ...

    async def health(self) -> ProviderHealth: ...


@runtime_checkable
class WeatherProvider(Protocol):
    """Provider for kickoff weather at a venue."""

    name: str

    async def fetch_weather(
        self,
        venue: NormalizedVenue,
        at: datetime,
    ) -> NormalizedWeatherSnapshot: ...

    async def health(self) -> ProviderHealth: ...
