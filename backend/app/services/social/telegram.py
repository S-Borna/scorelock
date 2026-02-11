"""Telegram integration — post to channel via Bot API.

Requires:
  - TELEGRAM_BOT_TOKEN: From @BotFather
  - TELEGRAM_CHAT_ID: Channel ID (e.g., @scorelock or numeric ID)
"""

import aiohttp
import structlog
from app.core.config import get_settings

logger = structlog.get_logger()

TELEGRAM_API = "https://api.telegram.org"


async def send_telegram_message(
    text: str,
    parse_mode: str = "HTML",
    chat_id: str | None = None,
) -> dict:
    """Send a message to Telegram channel.

    Args:
        text: Message text (HTML or Markdown)
        parse_mode: "HTML" or "MarkdownV2"
        chat_id: Override chat ID (defaults to config)
    """
    settings = get_settings()
    token = settings.telegram_bot_token
    target = chat_id or settings.telegram_chat_id

    if not token or not target:
        logger.warning("telegram_not_configured")
        return {"status": "skipped", "reason": "telegram_not_configured"}

    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    payload = {
        "chat_id": target,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": False,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                if data.get("ok"):
                    msg_id = data["result"]["message_id"]
                    logger.info("telegram_sent", message_id=msg_id)
                    return {"status": "ok", "message_id": msg_id}
                else:
                    logger.error("telegram_failed", error=data)
                    return {
                        "status": "error",
                        "error": data.get("description", "unknown"),
                    }
    except Exception as e:
        logger.error("telegram_error", error=str(e))
        return {"status": "error", "error": str(e)}


async def post_match_preview_telegram(
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
    """Post a match preview to Telegram."""
    lines = [
        f"⚽ <b>{home_team} vs {away_team}</b>",
        f"🏆 {league_name} — {kickoff}",
        "",
        f"🤖 <b>Prognos:</b> {prediction}",
    ]

    if home_win_pct is not None:
        lines.append(
            f"📊 H: {home_win_pct:.0f}% | D: {draw_pct:.0f}% | B: {away_win_pct:.0f}%"
        )

    if value_bet:
        lines.append(f"💰 <b>Value:</b> {value_bet}")

    lines.append("")
    lines.append(f'📊 <a href="{match_url}">Läs hela analysen</a>')

    return await send_telegram_message("\n".join(lines))


async def post_value_bet_alert_telegram(
    matches: list[dict],
    article_url: str,
) -> dict:
    """Post daily value bet alert to Telegram."""
    lines = ["🔥 <b>Dagens Value Bets — ScoreLock AI</b>\n"]

    for m in matches[:6]:
        edge_str = f" (edge: +{m['edge']:.1f}%)" if m.get("edge") else ""
        lines.append(
            f"💰 <b>{m['home']} vs {m['away']}</b>: {m['bet']} @{m['odds']:.2f}{edge_str}"
        )

    if len(matches) > 6:
        lines.append(f"...+{len(matches) - 6} fler")

    lines.append(f'\n📊 <a href="{article_url}">Fullständig analys</a>')

    return await send_telegram_message("\n".join(lines))
