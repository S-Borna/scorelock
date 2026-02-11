"""Smart API quota budget system.

Tracks API call counts per source using Redis counters with TTL.
Hard-stops at configurable thresholds (default 90%) to prevent overuse.

Usage:
    quota = QuotaManager(redis_url)
    if await quota.can_call("api_football"):
        await quota.record_call("api_football")
        # ... make the actual call
    else:
        logger.warning("quota_exhausted", source="api_football")
"""

import redis.asyncio as aioredis
import structlog
from datetime import datetime, timezone

from app.core.config import get_settings

logger = structlog.get_logger()


# ── Quota Definitions ──────────────────────────────────────

QUOTA_LIMITS: dict[str, dict] = {
    "api_football": {
        "limit": 100,          # 100 requests/day (free plan)
        "period": "daily",
        "hard_stop_pct": 0.90,  # Stop at 90 calls
    },
    "football_data": {
        "limit": 10,           # 10 requests/minute (free plan)
        "period": "minute",
        "hard_stop_pct": 0.90,
    },
    "football_data_daily": {
        "limit": 14400,        # ~10/min * 1440min = theoretical daily max
        "period": "daily",
        "hard_stop_pct": 0.95,
    },
    "the_odds_api": {
        "limit": 500,          # 500 requests/month (free plan)
        "period": "monthly",
        "hard_stop_pct": 0.90,
    },
}


def _redis_key(source: str, period: str) -> str:
    """Generate Redis key based on source and period."""
    now = datetime.now(timezone.utc)
    if period == "minute":
        suffix = now.strftime("%Y%m%d%H%M")
    elif period == "daily":
        suffix = now.strftime("%Y%m%d")
    elif period == "monthly":
        suffix = now.strftime("%Y%m")
    else:
        suffix = now.strftime("%Y%m%d")
    return f"quota:{source}:{suffix}"


def _ttl_seconds(period: str) -> int:
    """TTL for the Redis key."""
    if period == "minute":
        return 120       # 2 minutes (buffer)
    elif period == "daily":
        return 90_000    # 25 hours (buffer)
    elif period == "monthly":
        return 2_700_000  # ~31 days
    return 90_000


class QuotaManager:
    """Manages API call quotas via Redis counters."""

    def __init__(self):
        settings = get_settings()
        self._redis_url = settings.redis_url

    async def _get_redis(self) -> aioredis.Redis:
        return aioredis.from_url(self._redis_url, decode_responses=True)

    async def can_call(self, source: str) -> bool:
        """Check if we can make another API call for this source.

        Returns True if under quota, False if at/over hard stop.
        """
        config = QUOTA_LIMITS.get(source)
        if not config:
            return True  # Unknown source = no limit

        key = _redis_key(source, config["period"])
        hard_stop = int(config["limit"] * config["hard_stop_pct"])

        try:
            r = await self._get_redis()
            current = await r.get(key)
            await r.aclose()
            count = int(current) if current else 0
            return count < hard_stop
        except Exception as exc:
            logger.warning("quota_check_failed", source=source, error=str(exc))
            return True  # Fail open if Redis is down

    async def record_call(self, source: str, cost: int = 1) -> int:
        """Record an API call. Returns new count.

        Args:
            source: API source name (e.g. "api_football")
            cost: Number of quota units consumed (usually 1)

        Returns:
            Current count after incrementing.
        """
        config = QUOTA_LIMITS.get(source)
        if not config:
            return 0

        key = _redis_key(source, config["period"])
        ttl = _ttl_seconds(config["period"])

        try:
            r = await self._get_redis()
            pipe = r.pipeline()
            pipe.incrby(key, cost)
            pipe.expire(key, ttl)
            results = await pipe.execute()
            await r.aclose()
            new_count = results[0]

            # Log warning when approaching limit
            hard_stop = int(config["limit"] * config["hard_stop_pct"])
            if new_count >= hard_stop * 0.8:
                logger.warning(
                    "quota_approaching_limit",
                    source=source,
                    current=new_count,
                    limit=config["limit"],
                    hard_stop=hard_stop,
                    pct=round(new_count / config["limit"] * 100, 1),
                )

            return new_count
        except Exception as exc:
            logger.warning("quota_record_failed", source=source, error=str(exc))
            return 0

    async def get_usage(self, source: str) -> dict:
        """Get current usage for a source.

        Returns:
            Dict with count, limit, hard_stop, remaining, pct_used.
        """
        config = QUOTA_LIMITS.get(source)
        if not config:
            return {"source": source, "error": "unknown_source"}

        key = _redis_key(source, config["period"])
        try:
            r = await self._get_redis()
            current = await r.get(key)
            await r.aclose()
            count = int(current) if current else 0
        except Exception:
            count = 0

        limit = config["limit"]
        hard_stop = int(limit * config["hard_stop_pct"])
        return {
            "source": source,
            "period": config["period"],
            "count": count,
            "limit": limit,
            "hard_stop": hard_stop,
            "remaining": max(0, hard_stop - count),
            "pct_used": round(count / limit * 100, 1) if limit else 0,
        }

    async def get_all_usage(self) -> list[dict]:
        """Get usage stats for all tracked sources."""
        results = []
        for source in QUOTA_LIMITS:
            usage = await self.get_usage(source)
            results.append(usage)
        return results


# ── Singleton ──────────────────────────────────────────────

_quota_manager: QuotaManager | None = None


def get_quota_manager() -> QuotaManager:
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = QuotaManager()
    return _quota_manager
