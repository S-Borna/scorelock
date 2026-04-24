"""Rate-limit wrapper skeleton for the provider abstraction layer.

`app.core.quota_manager` already exposes `get_quota_manager()` with
`can_call()` / `record_call()` primitives, used today by `football_data.py`
and `odds_api.py`. This module declares the shape the provider abstraction
will wrap in v0.5d; it intentionally does **not** import `quota_manager` at
module load time, so the skeleton remains free of runtime dependencies on
Redis or env vars.

v0.5d adds the actual wrapper class and wires it through the registry.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_SOFT_CAP_PCT: int = 90


@dataclass(frozen=True)
class QuotaBucket:
    """Describes a single quota bucket for a `(provider, window)` pair.

    Wired to `app.core.quota_manager` in v0.5d. Left as a placeholder
    descriptor in v0.5a.
    """

    provider: str
    window: str
    limit: int
    soft_cap_pct: int = DEFAULT_SOFT_CAP_PCT
