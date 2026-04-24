"""Provider abstraction skeleton (v0.5a).

This package defines the contract for the provider abstraction layer described
in `docs/PROVIDER_ABSTRACTION_V0.4.md`. It contains only Protocols, dataclasses,
enums, and error classes. No concrete provider implementations, no registry
wiring, no runtime calls to any external service.

Runtime behavior is unchanged in v0.5a. No existing code imports from this
package. Adapters that wrap the current provider clients land in v0.5d.
"""

from __future__ import annotations

from app.providers.base import (
    BroadcastProvider,
    DateRange,
    LiveEventEnvelope,
    OddsMarket,
    OddsProvider,
    Operation,
    ProviderHealth,
    ProviderStatus,
    Scope,
    SportsDataProvider,
    WeatherProvider,
)
from app.providers.errors import (
    ProviderAuthError,
    ProviderCircuitOpen,
    ProviderError,
    ProviderPayloadError,
    ProviderQuotaExhausted,
    ProviderUnavailable,
    ProviderUnsupported,
)
from app.providers.normalization import (
    NormalizedBookmaker,
    NormalizedBroadcast,
    NormalizedCompetition,
    NormalizedCountry,
    NormalizedFixture,
    NormalizedLineup,
    NormalizedLineupPlayer,
    NormalizedMatchEvent,
    NormalizedMatchStatistics,
    NormalizedOddsSnapshot,
    NormalizedPlayer,
    NormalizedReferee,
    NormalizedSeason,
    NormalizedSport,
    NormalizedStanding,
    NormalizedTeam,
    NormalizedVenue,
    NormalizedWeatherSnapshot,
)
from app.providers.rate_limit import DEFAULT_SOFT_CAP_PCT, QuotaBucket
from app.providers.registry import (
    ProviderRegistry,
    ProviderRule,
    get_provider_registry,
)
from app.providers.retry import DEFAULT_RETRY_POLICY, RetryPolicy

__all__ = [
    # Base
    "Operation",
    "OddsMarket",
    "ProviderStatus",
    "ProviderHealth",
    "Scope",
    "DateRange",
    "LiveEventEnvelope",
    "SportsDataProvider",
    "OddsProvider",
    "BroadcastProvider",
    "WeatherProvider",
    # Errors
    "ProviderError",
    "ProviderUnavailable",
    "ProviderQuotaExhausted",
    "ProviderAuthError",
    "ProviderPayloadError",
    "ProviderUnsupported",
    "ProviderCircuitOpen",
    # Registry
    "ProviderRule",
    "ProviderRegistry",
    "get_provider_registry",
    # Retry
    "RetryPolicy",
    "DEFAULT_RETRY_POLICY",
    # Rate limit
    "QuotaBucket",
    "DEFAULT_SOFT_CAP_PCT",
    # Normalization placeholders
    "NormalizedSport",
    "NormalizedCountry",
    "NormalizedCompetition",
    "NormalizedSeason",
    "NormalizedTeam",
    "NormalizedPlayer",
    "NormalizedFixture",
    "NormalizedLineup",
    "NormalizedLineupPlayer",
    "NormalizedMatchEvent",
    "NormalizedMatchStatistics",
    "NormalizedStanding",
    "NormalizedOddsSnapshot",
    "NormalizedBookmaker",
    "NormalizedBroadcast",
    "NormalizedVenue",
    "NormalizedReferee",
    "NormalizedWeatherSnapshot",
]
