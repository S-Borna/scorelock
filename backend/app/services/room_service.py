"""DB-operationer för matchrummens chattmeddelanden (hangout / Steg 4).

Append-only textmeddelanden. Reaktioner och närvaro lever i Redis
(se app.core.room_realtime), inte här.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Fixture, MatchRoomMessage, User


def author_name(user: User) -> str:
    return user.name or user.email


async def fixture_exists(session: AsyncSession, fixture_id: int) -> bool:
    res = await session.execute(select(Fixture.id).where(Fixture.id == fixture_id))
    return res.scalar_one_or_none() is not None


async def post_message(
    session: AsyncSession, fixture_id: int, user: User, body: str
) -> MatchRoomMessage:
    msg = MatchRoomMessage(fixture_id=fixture_id, user_id=user.id, body=body)
    session.add(msg)
    await session.flush()
    return msg


async def get_messages(
    session: AsyncSession,
    fixture_id: int,
    limit: int = 50,
    before_id: int | None = None,
) -> list[tuple[MatchRoomMessage, str]]:
    """Senaste meddelandena för en fixture, nyast först. Returnerar
    (meddelande, författarnamn). Paginera bakåt via before_id."""
    q = (
        select(MatchRoomMessage, User.name, User.email)
        .join(User, User.id == MatchRoomMessage.user_id)
        .where(
            MatchRoomMessage.fixture_id == fixture_id,
            MatchRoomMessage.is_deleted.is_(False),
        )
    )
    if before_id is not None:
        q = q.where(MatchRoomMessage.id < before_id)
    q = q.order_by(MatchRoomMessage.id.desc()).limit(limit)
    res = await session.execute(q)
    return [(m, name or email) for (m, name, email) in res.all()]


async def soft_delete(
    session: AsyncSession, message_id: int, user: User
) -> bool:
    """Soft-deleta ett meddelande. Bara författaren själv (admin-delete
    är separat och uppskjutet)."""
    res = await session.execute(
        select(MatchRoomMessage).where(MatchRoomMessage.id == message_id)
    )
    msg = res.scalar_one_or_none()
    if msg is None or msg.user_id != user.id:
        return False
    msg.is_deleted = True
    await session.flush()
    return True
