"""Seed "ScoreLock AI" tippare så /leaderboard inte är tom vid VM-launch.

Idempotent:
- Skapar user "ScoreLock AI" (ai@scorelock.saidborna.com, tier ELITE) om den saknas.
- För varje VM-fixture (league_id=12) som har en Prediction-rad: skapa eller
  uppdatera UserPrediction (user_id, fixture_id) -> predicted_outcome (H/D/A
  efter högsta prob) + confidence från Prediction.

Kör:
    docker compose exec backend python -m scripts.seed_ai_tipster

Verifierar via DISTINCT counts efter körning.
"""
from __future__ import annotations

import asyncio
import secrets

from sqlalchemy import func, select

from app.core.database import async_session
from app.core.security import hash_password
from app.models.models import (
    Fixture,
    Prediction,
    SubscriptionTier,
    User,
    UserPrediction,
)

AI_EMAIL = "ai@scorelock.saidborna.com"
AI_NAME = "ScoreLock AI"
VM_LEAGUE_ID = 12


def pick_outcome(home: float, draw: float, away: float) -> tuple[str, float]:
    """Returnera (H/D/A, prob) baserat på högsta sannolikheten."""
    best = max(("H", home), ("D", draw), ("A", away), key=lambda t: t[1])
    return best[0], best[1]


async def main() -> None:
    async with async_session() as session:
        # 1. Hitta eller skapa AI-user
        result = await session.execute(select(User).where(User.email == AI_EMAIL))
        ai_user = result.scalar_one_or_none()

        if ai_user is None:
            ai_user = User(
                email=AI_EMAIL,
                hashed_password=hash_password(secrets.token_urlsafe(32)),
                name=AI_NAME,
                tier=SubscriptionTier.ELITE,
                is_active=True,
            )
            session.add(ai_user)
            await session.flush()
            print(f"created user id={ai_user.id} email={AI_EMAIL}")
        else:
            print(f"existing user id={ai_user.id} email={AI_EMAIL}")

        # 2. Hämta alla VM-predictions (joinade med fixtures för league-filter)
        stmt = (
            select(Prediction, Fixture.id)
            .join(Fixture, Fixture.id == Prediction.fixture_id)
            .where(Fixture.league_id == VM_LEAGUE_ID)
        )
        rows = (await session.execute(stmt)).all()
        print(f"VM predictions found: {len(rows)}")

        # 3. Upsert UserPrediction per fixture
        created = 0
        updated = 0
        for pred, fixture_id in rows:
            outcome, prob = pick_outcome(
                pred.home_win_prob, pred.draw_prob, pred.away_win_prob
            )

            existing = await session.execute(
                select(UserPrediction).where(
                    UserPrediction.user_id == ai_user.id,
                    UserPrediction.fixture_id == fixture_id,
                )
            )
            existing_row = existing.scalar_one_or_none()

            if existing_row is None:
                session.add(
                    UserPrediction(
                        user_id=ai_user.id,
                        fixture_id=fixture_id,
                        predicted_outcome=outcome,
                    )
                )
                created += 1
            else:
                existing_row.predicted_outcome = outcome
                updated += 1

        await session.commit()
        print(f"user_predictions created={created} updated={updated}")

        # 4. Verifiera totalcount
        total = await session.execute(
            select(func.count(UserPrediction.id)).where(
                UserPrediction.user_id == ai_user.id
            )
        )
        print(f"total user_predictions for ai user: {total.scalar_one()}")


if __name__ == "__main__":
    asyncio.run(main())
