"""Provider error taxonomy.

All errors raised by the provider abstraction layer inherit from `ProviderError`.
These classes are lightweight, safe to import, and carry no runtime dependencies.

Retry semantics (enforced by the registry / retry helper in v0.5d, not by the
errors themselves):
- ProviderUnavailable    — retryable with exponential backoff
- ProviderQuotaExhausted — not retried; triggers registry fallback
- ProviderAuthError      — not retried; opens the circuit breaker
- ProviderPayloadError   — not retried; opens the circuit breaker
- ProviderUnsupported    — not retried; fallback to next rule
- ProviderCircuitOpen    — not retried; fallback to next rule
"""

from __future__ import annotations


class ProviderError(Exception):
    """Base class for every provider-layer exception."""


class ProviderUnavailable(ProviderError):
    """Provider returned 5xx, timed out, or was otherwise unreachable."""


class ProviderQuotaExhausted(ProviderError):
    """Provider quota (per-minute, per-day, or per-month) has been exhausted."""


class ProviderAuthError(ProviderError):
    """Provider returned 401 or 403 — credentials invalid or revoked."""


class ProviderPayloadError(ProviderError):
    """Provider response did not match expected schema; normalization failed."""


class ProviderUnsupported(ProviderError):
    """Requested operation is not supported by this provider for the given scope."""


class ProviderCircuitOpen(ProviderError):
    """Circuit breaker for this (provider, operation) is currently open."""
