"""Ephemeral realtids-state för matchrummen (hangout / Steg 4).

Reaktioner och närvaro persisteras inte i Postgres — de lever i Redis med TTL.
En per-fixture pub/sub-kanal ``scorelock:room:{fixture_id}`` distribuerar
meddelanden, reaktioner och mål-events till anslutna WebSocket-klienter.
"""
from __future__ import annotations

import json
import time

import redis.asyncio as aioredis

from app.core.config import get_settings

PRESENCE_TTL = 30  # sek; klienten heartbeatar inom detta fönster
REACTION_TTL = 6 * 3600  # reaktions-räknare lever matchen ut
SEND_WINDOW = 10  # sek
SEND_MAX = 5  # max meddelanden per fönster per user


def room_channel(fixture_id: int) -> str:
    return f"scorelock:room:{fixture_id}"


async def _redis() -> aioredis.Redis:
    return aioredis.from_url(get_settings().redis_url, decode_responses=True)


async def publish_room_event(fixture_id: int, event: dict) -> None:
    r = await _redis()
    try:
        await r.publish(room_channel(fixture_id), json.dumps(event))
    finally:
        await r.aclose()


async def mark_present(fixture_id: int, user_key: str) -> int:
    """Registrera/förnya närvaro och returnera antal aktiva just nu.

    Sorted set med timestamp-score; utgångna medlemmar rensas vid varje anrop
    (Redis saknar per-medlems-TTL).
    """
    r = await _redis()
    try:
        key = f"room:{fixture_id}:presence"
        now = time.time()
        await r.zadd(key, {user_key: now})
        await r.expire(key, PRESENCE_TTL * 4)
        await r.zremrangebyscore(key, "-inf", now - PRESENCE_TTL)
        return int(await r.zcard(key))
    finally:
        await r.aclose()


async def mark_absent(fixture_id: int, user_key: str) -> int:
    r = await _redis()
    try:
        key = f"room:{fixture_id}:presence"
        await r.zrem(key, user_key)
        return int(await r.zcard(key))
    finally:
        await r.aclose()


async def presence_count(fixture_id: int) -> int:
    r = await _redis()
    try:
        key = f"room:{fixture_id}:presence"
        await r.zremrangebyscore(key, "-inf", time.time() - PRESENCE_TTL)
        return int(await r.zcard(key))
    finally:
        await r.aclose()


async def add_reaction(fixture_id: int, emoji: str) -> dict[str, int]:
    """Öka reaktions-räknaren och returnera alla räknare för fixturen."""
    r = await _redis()
    try:
        key = f"room:{fixture_id}:reactions"
        await r.hincrby(key, emoji, 1)
        await r.expire(key, REACTION_TTL)
        raw = await r.hgetall(key)
        return {k: int(v) for k, v in raw.items()}
    finally:
        await r.aclose()


async def get_reactions(fixture_id: int) -> dict[str, int]:
    r = await _redis()
    try:
        raw = await r.hgetall(f"room:{fixture_id}:reactions")
        return {k: int(v) for k, v in raw.items()}
    finally:
        await r.aclose()


async def allow_send(user_id: int) -> bool:
    """Per-user send-rate-limit: max SEND_MAX meddelanden per SEND_WINDOW sek."""
    r = await _redis()
    try:
        key = f"room:rate:{user_id}"
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, SEND_WINDOW)
        return count <= SEND_MAX
    finally:
        await r.aclose()
