"""Rate limiting middleware for ScoreLock API.

Implements per-user and per-IP rate limiting using Redis.
Free tier gets fewer requests; Pro/Elite get higher limits.
"""

import time
import structlog
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# ── Rate Limits (requests per minute) ──────────────────────

TIER_LIMITS: dict[str, int] = {
    "free": 30,
    "pro": 120,
    "elite": 300,
    "anonymous": 20,
}

# Paths exempt from rate limiting
EXEMPT_PATHS: set[str] = {
    "/api/v1/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/metrics",
}

RATE_LIMIT_WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redis-backed sliding window rate limiter."""

    def __init__(self, app, redis_client=None) -> None:  # noqa: ANN001
        super().__init__(app)
        self.redis = redis_client

    async def _get_redis(self):
        """Lazy-initialize Redis connection."""
        if self.redis is None:
            import redis.asyncio as aioredis
            self.redis = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
            )
        return self.redis

    def _get_client_key(self, request: Request) -> tuple[str, str]:
        """Extract rate limit key and tier from request.

        Returns:
            (key, tier) tuple for rate limiting.
        """
        # Try to get user from JWT token (set by auth dependency)
        user = getattr(request.state, "user", None)
        if user:
            tier = getattr(user, "tier", "free")
            tier_value = tier.value if hasattr(tier, "value") else str(tier)
            return f"rl:user:{user.id}", tier_value

        # Fall back to IP-based limiting
        client_ip = request.client.host if request.client else "unknown"
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()

        return f"rl:ip:{client_ip}", "anonymous"

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint,
    ) -> Response:
        """Check rate limit before processing request."""
        # Skip exempt paths
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        # Skip non-API paths
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        try:
            redis = await self._get_redis()
            key, tier = self._get_client_key(request)
            limit = TIER_LIMITS.get(tier, TIER_LIMITS["anonymous"])

            now = time.time()
            window_start = now - RATE_LIMIT_WINDOW_SECONDS

            pipe = redis.pipeline()
            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)
            # Count current requests in window
            pipe.zcard(key)
            # Add current request
            pipe.zadd(key, {str(now): now})
            # Set expiry on the key
            pipe.expire(key, RATE_LIMIT_WINDOW_SECONDS + 1)
            results = await pipe.execute()

            current_count = results[1]

            if current_count >= limit:
                logger.warning(
                    "rate_limit_exceeded",
                    key=key,
                    tier=tier,
                    limit=limit,
                    current=current_count,
                )
                retry_after = int(RATE_LIMIT_WINDOW_SECONDS - (now - window_start))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. {limit} requests per minute for {tier} tier.",
                    headers={"Retry-After": str(max(1, retry_after))},
                )

            response = await call_next(request)

            # Add rate limit headers
            remaining = max(0, limit - current_count - 1)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(now + RATE_LIMIT_WINDOW_SECONDS))

            return response

        except HTTPException:
            raise
        except Exception as exc:
            # Don't block requests if Redis is down
            logger.error("rate_limit_error", error=str(exc))
            return await call_next(request)
