"""Placeholder normalized domain types.

These are lightweight dataclasses used as type hints for the Protocol interfaces
defined in `base.py`. They intentionally carry no fields yet — concrete field
definitions land in v0.5c alongside the metadata schema migrations.

Real normalization functions (provider payload → canonical object) are
implemented in v0.5d. This module contains no transformation logic and no
dependency on any provider client.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NormalizedSport:
    """Canonical sport identity. Fields land in v0.5c."""


@dataclass(frozen=True)
class NormalizedCountry:
    """Canonical country identity. Fields land in v0.5c."""


@dataclass(frozen=True)
class NormalizedCompetition:
    """Canonical competition identity. Fields land in v0.5c."""


@dataclass(frozen=True)
class NormalizedSeason:
    """Canonical season identity. Fields land in v0.5c."""


@dataclass(frozen=True)
class NormalizedTeam:
    """Canonical team identity. Fields land in v0.5c."""


@dataclass(frozen=True)
class NormalizedPlayer:
    """Canonical player identity. Fields land in v0.5c."""


@dataclass(frozen=True)
class NormalizedFixture:
    """Canonical fixture. Fields land in v0.5c."""


@dataclass(frozen=True)
class NormalizedLineup:
    """Canonical lineup. Fields land in v0.5c."""


@dataclass(frozen=True)
class NormalizedLineupPlayer:
    """Canonical lineup player. Fields land in v0.5c."""


@dataclass(frozen=True)
class NormalizedMatchEvent:
    """Canonical match event. Fields land in v0.5c."""


@dataclass(frozen=True)
class NormalizedMatchStatistics:
    """Canonical per-fixture statistics. Fields land in v0.5c."""


@dataclass(frozen=True)
class NormalizedStanding:
    """Canonical standings entry. Fields land in v0.5c."""


@dataclass(frozen=True)
class NormalizedOddsSnapshot:
    """Canonical odds snapshot. Fields land in v0.5c."""


@dataclass(frozen=True)
class NormalizedBookmaker:
    """Canonical bookmaker identity. Fields land in v0.5c."""


@dataclass(frozen=True)
class NormalizedBroadcast:
    """Canonical broadcast entry. Fields land in v0.5c."""


@dataclass(frozen=True)
class NormalizedVenue:
    """Canonical venue. Fields land in v0.5c."""


@dataclass(frozen=True)
class NormalizedReferee:
    """Canonical referee. Fields land in v0.5c."""


@dataclass(frozen=True)
class NormalizedWeatherSnapshot:
    """Canonical weather snapshot. Fields land in v0.5c."""
