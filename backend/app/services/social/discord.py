"""Discord integration — post to channels via webhook.

No bot token needed — just a webhook URL per channel.
Supports rich embeds with match data, predictions, and links.
"""

import aiohttp
import structlog
from app.core.config import get_settings

logger = structlog.get_logger()


async def post_to_discord(
    content: str | None = None,
    embed: dict | None = None,
    webhook_url: str | None = None,
) -> dict:
    """Post a message or embed to Discord via webhook.

    Args:
        content: Plain text message
        embed: Discord embed object (title, description, color, fields, etc.)
        webhook_url: Override webhook URL (defaults to config)
    """
    settings = get_settings()
    url = webhook_url or settings.discord_webhook_url

    if not url:
        logger.warning("discord_not_configured")
        return {"status": "skipped", "reason": "discord_not_configured"}

    payload: dict = {}
    if content:
        payload["content"] = content
    if embed:
        payload["embeds"] = [embed]

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status in (200, 204):
                    logger.info("discord_posted", status=resp.status)
                    return {"status": "ok"}
                else:
                    body = await resp.text()
                    logger.error("discord_failed", status=resp.status, body=body[:200])
                    return {"status": "error", "code": resp.status, "body": body[:200]}
    except Exception as e:
        logger.error("discord_error", error=str(e))
        return {"status": "error", "error": str(e)}


async def post_match_preview_discord(
    home_team: str,
    away_team: str,
    league_name: str,
    kickoff: str,
    prediction: str,
    home_win_pct: float | None,
    draw_pct: float | None,
    away_win_pct: float | None,
    value_bet: str | None,
    match_url: str,
) -> dict:
    """Post a rich match preview embed to Discord."""
    color = 0x10B981  # ScoreLock green

    fields = [
        {"name": "🤖 Prognos", "value": prediction, "inline": True},
    ]

    if home_win_pct is not None:
        fields.append(
            {
                "name": "📊 Sannolikheter",
                "value": f"H: {home_win_pct:.0f}% | D: {draw_pct:.0f}% | B: {away_win_pct:.0f}%",
                "inline": True,
            }
        )

    if value_bet:
        fields.append({"name": "💰 Value Bet", "value": value_bet, "inline": False})

    embed = {
        "title": f"⚽ {home_team} vs {away_team}",
        "description": f"**{league_name}** — {kickoff}",
        "url": match_url,
        "color": color,
        "fields": fields,
        "footer": {"text": "ScoreLock AI — scorelock.saidborna.com"},
    }

    return await post_to_discord(embed=embed)


async def post_value_bet_alert_discord(
    matches: list[dict],
    article_url: str,
) -> dict:
    """Post a daily value bet alert embed to Discord #value-bets channel."""
    settings = get_settings()
    vb_webhook = settings.discord_webhook_valuebets or settings.discord_webhook_url

    lines = []
    for m in matches[:8]:
        edge_str = f" (edge: +{m['edge']:.1f}%)" if m.get("edge") else ""
        lines.append(
            f"💰 **{m['home']} vs {m['away']}**: {m['bet']} @{m['odds']:.2f}{edge_str}"
        )

    embed = {
        "title": "🔥 Dagens Value Bets — ScoreLock AI",
        "description": "\n".join(lines),
        "url": article_url,
        "color": 0xF59E0B,
        "footer": {"text": "ScoreLock AI — scorelock.saidborna.com"},
    }

    return await post_to_discord(embed=embed, webhook_url=vb_webhook)
