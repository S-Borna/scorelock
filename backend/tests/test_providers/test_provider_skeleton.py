"""Tests for the v0.5a provider abstraction skeleton.

Verifies that:
- the package imports cleanly with no runtime dependencies
- `Operation` enum exposes the expected values
- the default registry is empty and safe to use
- every subclass error is catchable under `ProviderError`
- Protocol classes import and are distinct
- `RetryPolicy` exposes the expected error taxonomies

These tests require neither paid API keys nor database nor network.
"""

from __future__ import annotations

import pytest

from app.providers import (
    DEFAULT_RETRY_POLICY,
    BroadcastProvider,
    NormalizedFixture,
    OddsProvider,
    Operation,
    ProviderAuthError,
    ProviderCircuitOpen,
    ProviderError,
    ProviderHealth,
    ProviderPayloadError,
    ProviderQuotaExhausted,
    ProviderRegistry,
    ProviderRule,
    ProviderStatus,
    ProviderUnavailable,
    ProviderUnsupported,
    RetryPolicy,
    Scope,
    SportsDataProvider,
    WeatherProvider,
    get_provider_registry,
)


def test_operation_enum_has_expected_members() -> None:
    """Operation enum exposes the 12 operations from the v0.4 design."""
    expected = {
        "fixtures",
        "live_fixtures",
        "standings",
        "teams",
        "players",
        "lineups",
        "events",
        "statistics",
        "odds",
        "in_play_odds",
        "broadcasts",
        "weather",
    }
    assert {op.value for op in Operation} == expected


def test_operation_values_are_strings() -> None:
    """Operation members are `str` subclasses for serialization friendliness."""
    assert Operation.FIXTURES.value == "fixtures"
    assert isinstance(Operation.FIXTURES, str)


def test_default_registry_is_empty() -> None:
    """A fresh `ProviderRegistry` is empty and chain lookups return []."""
    registry = ProviderRegistry()
    assert registry.is_empty()
    assert registry.operations() == frozenset()
    for op in Operation:
        assert registry.chain_for(op) == []


def test_registry_register_and_read_back() -> None:
    """Registering a rule makes it observable via `chain_for()`."""
    registry = ProviderRegistry()
    rule = ProviderRule(provider="mock", scope=Scope.global_())
    registry.register(Operation.FIXTURES, rule)
    assert registry.chain_for(Operation.FIXTURES) == [rule]
    assert registry.chain_for(Operation.STANDINGS) == []


def test_get_provider_registry_returns_singleton() -> None:
    """Consecutive calls to `get_provider_registry()` yield the same object."""
    a = get_provider_registry()
    b = get_provider_registry()
    assert a is b
    assert isinstance(a, ProviderRegistry)


def test_provider_error_hierarchy() -> None:
    """Every subclass is catchable under `ProviderError` and raisable."""
    subclasses = (
        ProviderUnavailable,
        ProviderQuotaExhausted,
        ProviderAuthError,
        ProviderPayloadError,
        ProviderUnsupported,
        ProviderCircuitOpen,
    )
    for exc_cls in subclasses:
        assert issubclass(exc_cls, ProviderError)
        with pytest.raises(ProviderError):
            raise exc_cls("test")


def test_provider_protocols_are_importable_and_distinct() -> None:
    """Four Protocol classes import and are distinct objects."""
    protocols = {SportsDataProvider, OddsProvider, BroadcastProvider, WeatherProvider}
    assert len(protocols) == 4
    for proto in protocols:
        assert hasattr(proto, "__mro__")


def test_provider_health_defaults() -> None:
    """`ProviderHealth` fills `checked_at` with a timezone-aware UTC datetime."""
    health = ProviderHealth(provider="mock", status=ProviderStatus.HEALTHY)
    assert health.provider == "mock"
    assert health.status == ProviderStatus.HEALTHY
    assert health.checked_at is not None
    assert health.checked_at.tzinfo is not None


def test_default_retry_policy_shape() -> None:
    """`DEFAULT_RETRY_POLICY` encodes the retry taxonomy from the v0.4 design."""
    assert isinstance(DEFAULT_RETRY_POLICY, RetryPolicy)
    assert ProviderUnavailable in DEFAULT_RETRY_POLICY.retryable
    for non_retry_cls in (
        ProviderQuotaExhausted,
        ProviderAuthError,
        ProviderPayloadError,
        ProviderUnsupported,
        ProviderCircuitOpen,
    ):
        assert non_retry_cls in DEFAULT_RETRY_POLICY.non_retryable


def test_normalized_placeholder_instantiates() -> None:
    """Placeholder `NormalizedFixture` instantiates with no fields."""
    assert NormalizedFixture() is not None


def test_scope_global_factory() -> None:
    """`Scope.global_()` returns the canonical global scope."""
    s = Scope.global_()
    assert s.kind == "global"
    assert s.value is None
