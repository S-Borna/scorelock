"""Stripe subscription routes — checkout, portal, webhook."""

import asyncio
import stripe
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import User, SubscriptionTier

settings = get_settings()
stripe.api_key = settings.stripe_secret_key
logger = structlog.get_logger()

router = APIRouter(prefix="/stripe", tags=["stripe"])


# ── Create Checkout Session ────────────────────────────────

@router.post("/checkout")
async def create_checkout_session(
    tier: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe Checkout session for Pro or Elite subscription."""
    price_map = {
        "pro": settings.stripe_price_pro,
        "elite": settings.stripe_price_elite,
    }
    price_id = price_map.get(tier)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid tier. Choose 'pro' or 'elite'.")

    # Create or reuse Stripe customer (run sync Stripe call in thread)
    if not user.stripe_customer_id:
        customer = await asyncio.to_thread(
            stripe.Customer.create,
            email=user.email,
            metadata={"user_id": str(user.id)},
        )
        user.stripe_customer_id = customer.id
        await db.commit()

    session = await asyncio.to_thread(
        stripe.checkout.Session.create,
        customer=user.stripe_customer_id,
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.base_url}/account?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.base_url}/pricing",
        metadata={"user_id": str(user.id), "tier": tier},
    )

    return {"checkout_url": session.url}


# ── Customer Portal ────────────────────────────────────────

@router.post("/portal")
async def create_portal_session(
    user: User = Depends(get_current_user),
):
    """Create a Stripe Customer Portal session to manage subscription."""
    if not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No active subscription")

    session = await asyncio.to_thread(
        stripe.billing_portal.Session.create,
        customer=user.stripe_customer_id,
        return_url=f"{settings.base_url}/account",
    )

    return {"portal_url": session.url}


# ── Webhook ────────────────────────────────────────────────

@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Stripe webhook events for subscription lifecycle."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except (ValueError, stripe.SignatureVerificationError):
        logger.warning("stripe_invalid_signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(data, db)
    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(data, db)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(data, db)

    return {"status": "ok"}


async def _handle_checkout_completed(session: dict, db: AsyncSession):
    """Activate subscription after successful checkout."""
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")
    tier_str = session.get("metadata", {}).get("tier", "pro")

    tier = SubscriptionTier.PRO if tier_str == "pro" else SubscriptionTier.ELITE

    result = await db.execute(
        select(User).where(User.stripe_customer_id == customer_id)
    )
    user = result.scalar_one_or_none()
    if user:
        user.tier = tier
        user.stripe_subscription_id = subscription_id
        await db.commit()
        logger.info("stripe_checkout_completed", user_id=user.id, tier=tier_str)


async def _handle_subscription_updated(subscription: dict, db: AsyncSession):
    """Handle plan changes (upgrade/downgrade)."""
    customer_id = subscription.get("customer")
    status = subscription.get("status")

    if status != "active":
        return

    # Determine tier from price
    items = subscription.get("items", {}).get("data", [])
    price_id = items[0]["price"]["id"] if items else None

    tier = SubscriptionTier.FREE
    if price_id == settings.stripe_price_pro:
        tier = SubscriptionTier.PRO
    elif price_id == settings.stripe_price_elite:
        tier = SubscriptionTier.ELITE

    result = await db.execute(
        select(User).where(User.stripe_customer_id == customer_id)
    )
    user = result.scalar_one_or_none()
    if user:
        user.tier = tier
        await db.commit()
        logger.info("stripe_subscription_updated", user_id=user.id, tier=tier.value)


async def _handle_subscription_deleted(subscription: dict, db: AsyncSession):
    """Downgrade user when subscription is cancelled."""
    customer_id = subscription.get("customer")

    result = await db.execute(
        select(User).where(User.stripe_customer_id == customer_id)
    )
    user = result.scalar_one_or_none()
    if user:
        user.tier = SubscriptionTier.FREE
        user.stripe_subscription_id = None
        await db.commit()
        logger.info("stripe_subscription_deleted", user_id=user.id)
