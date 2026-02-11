"""OneSignal push notification integration.

Uses OneSignal REST API v1 — free tier supports:
  - Unlimited mobile push
  - 10k web push subscribers
  - Segments for targeting

Notification types:
  - match_preview: Upcoming big match
  - value_bet: Edge > 5% detected
  - match_result: Full-time result with prediction accuracy
"""

import httpx
import structlog
from app.core.config import get_settings

logger = structlog.get_logger()

ONESIGNAL_API = "https://onesignal.com/api/v1/notifications"


async def send_push_notification(
    title: str,
    message: str,
    url: str | None = None,
    segment: str = "All",
    data: dict | None = None,
) -> bool:
    """Send a push notification via OneSignal.

    Args:
        title: Notification title
        message: Body text
        url: Deep-link URL (opens in app/browser)
        segment: Target segment (All, Subscribed Users, etc.)
        data: Extra data payload

    Returns:
        True on success
    """
    settings = get_settings()
    if not settings.onesignal_app_id or not settings.onesignal_api_key:
        logger.warning("onesignal_not_configured")
        return False

    payload = {
        "app_id": settings.onesignal_app_id,
        "headings": {"en": title, "sv": title},
        "contents": {"en": message, "sv": message},
        "included_segments": [segment],
    }
    if url:
        payload["url"] = url
    if data:
        payload["data"] = data

    headers = {
        "Authorization": f"Basic {settings.onesignal_api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(ONESIGNAL_API, json=payload, headers=headers)
            resp.raise_for_status()
            result = resp.json()
            logger.info(
                "push_sent",
                recipients=result.get("recipients", 0),
                notification_id=result.get("id"),
            )
            return True
    except Exception as e:
        logger.error("push_failed", error=str(e))
        return False


async def push_match_preview(
    home_team: str,
    away_team: str,
    league: str,
    prediction: str,
    fixture_id: int,
) -> bool:
    """Push notification for an upcoming match preview."""
    return await send_push_notification(
        title=f"⚽ {home_team} vs {away_team}",
        message=f"🤖 {prediction} — {league}",
        url=f"https://scorelock.saidborna.com/matches/{fixture_id}",
        data={"type": "match_preview", "fixture_id": fixture_id},
    )


async def push_value_bet_alert(
    home_team: str,
    away_team: str,
    bet_description: str,
    fixture_id: int,
) -> bool:
    """Push notification for a high-edge value bet."""
    return await send_push_notification(
        title=f"💰 Value Bet: {home_team} vs {away_team}",
        message=bet_description,
        url=f"https://scorelock.saidborna.com/matches/{fixture_id}",
        data={"type": "value_bet", "fixture_id": fixture_id},
    )


async def push_match_result(
    home_team: str,
    away_team: str,
    score: str,
    prediction_correct: bool,
    fixture_id: int,
) -> bool:
    """Push notification for match result."""
    emoji = "✅" if prediction_correct else "❌"
    return await send_push_notification(
        title=f"{emoji} {home_team} {score} {away_team}",
        message=f"AI-prognos {'korrekt' if prediction_correct else 'fel'} — se analysen",
        url=f"https://scorelock.saidborna.com/matches/{fixture_id}",
        data={"type": "match_result", "fixture_id": fixture_id},
    )
