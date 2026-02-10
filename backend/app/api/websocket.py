"""WebSocket endpoint for live score updates.

Clients connect and receive real-time fixture updates sent from the Celery
worker whenever live scores change.  Uses an in-memory pub/sub approach
backed by the Redis pub/sub channel ``scorelock:live``.
"""

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import redis.asyncio as aioredis
import structlog

from app.core.config import get_settings

settings = get_settings()
logger = structlog.get_logger()

router = APIRouter()


class ConnectionManager:
    """Track active WebSocket connections and broadcast messages."""

    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
        logger.info("ws_connect", total=len(self.active))

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)
        logger.info("ws_disconnect", total=len(self.active))

    async def broadcast(self, message: dict):
        payload = json.dumps(message)
        gone: list[WebSocket] = []
        for ws in self.active:
            try:
                await ws.send_text(payload)
            except Exception:
                gone.append(ws)
        for ws in gone:
            self.active.remove(ws)


manager = ConnectionManager()


async def _redis_listener():
    """Subscribe to Redis ``scorelock:live`` channel and broadcast to WebSockets."""
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe("scorelock:live")
    logger.info("ws_redis_subscribed", channel="scorelock:live")

    try:
        async for msg in pubsub.listen():
            if msg["type"] == "message":
                try:
                    data = json.loads(msg["data"])
                    await manager.broadcast(data)
                except json.JSONDecodeError:
                    pass
    finally:
        await pubsub.unsubscribe("scorelock:live")
        await r.aclose()


_listener_task: asyncio.Task | None = None


def _ensure_listener():
    """Lazily start the Redis listener coroutine."""
    global _listener_task
    if _listener_task is None or _listener_task.done():
        _listener_task = asyncio.create_task(_redis_listener())


@router.websocket("/ws/live")
async def live_scores(ws: WebSocket):
    """WebSocket endpoint for live match updates.

    Clients receive JSON messages with structure::

        {
            "type": "score_update",
            "fixture_id": 12345,
            "home_goals": 2,
            "away_goals": 1,
            "status": "live",
            "minute": 67
        }
    """
    _ensure_listener()
    await manager.connect(ws)
    try:
        while True:
            # Keep connection alive; ignore client messages
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)


# ── Helper for Celery tasks to publish updates ─────────────

def publish_score_update(fixture_id: int, home_goals: int, away_goals: int,
                         status: str, minute: int | None = None):
    """Publish a score update to Redis pub/sub (called from sync Celery tasks).

    This uses synchronous Redis since Celery tasks run in sync context.
    """
    import redis
    r = redis.from_url(settings.redis_url, decode_responses=True)
    payload = json.dumps({
        "type": "score_update",
        "fixture_id": fixture_id,
        "home_goals": home_goals,
        "away_goals": away_goals,
        "status": status,
        "minute": minute,
    })
    r.publish("scorelock:live", payload)
    r.close()
