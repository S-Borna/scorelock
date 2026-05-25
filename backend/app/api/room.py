"""Matchrum-endpoints (hangout / Steg 4).

REST-ytan: hämta historik, skicka meddelande, reagera, rapportera, ta bort.
Realtids-distribution sker via Redis-kanalen scorelock:room:{fixture_id} som
WS-endpointen /ws/room/{fixture_id} lyssnar på.
"""
from __future__ import annotations

from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import room_realtime as rt
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import MatchRoomMessage, User
from app.services import room_service as rs

logger = structlog.get_logger()
router = APIRouter()


class RoomMessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=500)


class RoomMessageOut(BaseModel):
    id: int
    fixture_id: int
    user_id: int
    author_name: str
    body: str
    created_at: datetime


class RoomReactionIn(BaseModel):
    emoji: str = Field(min_length=1, max_length=8)


def _to_out(msg: MatchRoomMessage, name: str) -> RoomMessageOut:
    return RoomMessageOut(
        id=msg.id,
        fixture_id=msg.fixture_id,
        user_id=msg.user_id,
        author_name=name,
        body=msg.body,
        created_at=msg.created_at,
    )


@router.get(
    "/fixtures/{fixture_id}/room/messages",
    response_model=list[RoomMessageOut],
)
async def list_messages(
    fixture_id: int,
    limit: int = Query(50, ge=1, le=100),
    before_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    rows = await rs.get_messages(db, fixture_id, limit=limit, before_id=before_id)
    return [_to_out(m, name) for (m, name) in rows]


@router.post(
    "/fixtures/{fixture_id}/room/messages",
    response_model=RoomMessageOut,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    fixture_id: int,
    payload: RoomMessageCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not await rs.fixture_exists(db, fixture_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Fixture not found")
    body = payload.body.strip()
    if not body:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Empty message")
    if not await rt.allow_send(user.id):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Du skickar för snabbt — ta det lugnt"
        )
    msg = await rs.post_message(db, fixture_id, user, body)
    await db.commit()
    out = _to_out(msg, rs.author_name(user))
    await rt.publish_room_event(
        fixture_id, {"type": "message", **out.model_dump(mode="json")}
    )
    return out


@router.post("/fixtures/{fixture_id}/room/reactions")
async def react(
    fixture_id: int,
    payload: RoomReactionIn,
    user: User = Depends(get_current_user),
):
    counts = await rt.add_reaction(fixture_id, payload.emoji)
    await rt.publish_room_event(
        fixture_id, {"type": "reaction", "emoji": payload.emoji, "counts": counts}
    )
    return {"counts": counts}


@router.delete("/fixtures/{fixture_id}/room/messages/{message_id}")
async def delete_message(
    fixture_id: int,
    message_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ok = await rs.soft_delete(db, message_id, user)
    if not ok:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Meddelandet finns inte eller är inte ditt"
        )
    await db.commit()
    await rt.publish_room_event(
        fixture_id, {"type": "delete", "message_id": message_id}
    )
    return {"status": "deleted"}


@router.post("/fixtures/{fixture_id}/room/messages/{message_id}/report")
async def report_message(
    fixture_id: int,
    message_id: int,
    user: User = Depends(get_current_user),
):
    logger.info(
        "room_message_reported",
        fixture_id=fixture_id,
        message_id=message_id,
        reporter_id=user.id,
    )
    return {"status": "reported"}
