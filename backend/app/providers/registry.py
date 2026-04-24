"""Provider registry.

Resolves an `(operation, scope)` tuple to an ordered chain of provider rules.
The default registry is empty; rules are populated in v0.5d when concrete
providers are wrapped behind the abstraction.

This module:
- imports no concrete provider client
- requires no environment variables
- performs no I/O
- is safe to import from any context (tests, tools, scripts)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

from app.providers.base import Operation, Scope


@dataclass(frozen=True)
class ProviderRule:
    """One entry in a provider fallback chain for a given operation."""

    provider: str
    scope: Scope = field(default_factory=Scope.global_)
    prefer_push: bool = False
    requires_tier: str | None = None


class ProviderRegistry:
    """Operation → ordered list of `ProviderRule`.

    The v0.5a instance is empty. v0.5d replaces the factory below with a
    populated registry that encodes the fallback chains defined in
    `docs/PROVIDER_ABSTRACTION_V0.4.md`.
    """

    def __init__(self) -> None:
        self._rules: dict[Operation, list[ProviderRule]] = {}

    def register(self, operation: Operation, rule: ProviderRule) -> None:
        """Append a rule to the chain for the given operation."""
        self._rules.setdefault(operation, []).append(rule)

    def chain_for(self, operation: Operation) -> list[ProviderRule]:
        """Return the rule chain for an operation (empty list if none registered)."""
        return list(self._rules.get(operation, ()))

    def operations(self) -> frozenset[Operation]:
        """Operations with at least one registered rule."""
        return frozenset(self._rules.keys())

    def is_empty(self) -> bool:
        """True when no rules are registered for any operation."""
        return not self._rules


_registry: ProviderRegistry | None = None
_registry_lock = Lock()


def get_provider_registry() -> ProviderRegistry:
    """Return the process-wide provider registry singleton.

    v0.5a returns an empty registry. Never raises. Never performs I/O.
    """
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = ProviderRegistry()
    return _registry
