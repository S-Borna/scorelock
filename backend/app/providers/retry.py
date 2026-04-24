"""Shared retry configuration for the provider abstraction layer.

This module defines retry policy as data only. The actual wrapping of provider
calls with retry behavior lands in v0.5d. Current provider clients
(`api_football.py`, `football_data.py`, `odds_api.py`) keep their own
`tenacity` decorators unchanged; nothing imports from this module at runtime
in v0.5a.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.providers.errors import (
    ProviderAuthError,
    ProviderCircuitOpen,
    ProviderPayloadError,
    ProviderQuotaExhausted,
    ProviderUnavailable,
    ProviderUnsupported,
)


@dataclass(frozen=True)
class RetryPolicy:
    """Describes how the provider layer should retry a failing call.

    `retryable` names exception types that trigger exponential backoff.
    `non_retryable` names exception types that bypass retry and surface
    immediately (or trigger registry-level fallback / circuit open).
    """

    max_attempts: int = 5
    base_delay_seconds: float = 0.5
    max_delay_seconds: float = 8.0
    jitter_seconds: float = 0.25
    retryable: tuple[type[Exception], ...] = field(
        default_factory=lambda: (ProviderUnavailable,)
    )
    non_retryable: tuple[type[Exception], ...] = field(
        default_factory=lambda: (
            ProviderQuotaExhausted,
            ProviderAuthError,
            ProviderPayloadError,
            ProviderUnsupported,
            ProviderCircuitOpen,
        )
    )


DEFAULT_RETRY_POLICY = RetryPolicy()
