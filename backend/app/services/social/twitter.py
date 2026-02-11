"""Twitter/X integration — post match previews + value bet alerts.

Uses tweepy v2 (X API v2 Free tier):
  - 1,500 tweets/month (50/day)
  - Enough for ~8 leagues × 3-4 matches/day = ~25 tweets/day

Tweet format:
  ⚽ Arsenal vs Chelsea — Premier League
  🤖 ScoreLock-prognos: 2-1 (hemmaseger 52%)
  💰 Value bet: Arsenal ML @2.10 (edge: +3.2%)
  📊 Läs hela analysen → scorelock.saidborna.com/matches/123

  #PremierLeague #Arsenal #Chelsea
"""

import structlog
import tweepy
from app.core.config import get_settings

logger = structlog.get_logger()


def get_twitter_client() -> tweepy.Client | None:
    """Create Twitter API v2 client. Returns None if credentials missing."""
    settings = get_settings()
    if not settings.twitter_bearer_token:
        logger.warning("twitter_not_configured", reason="missing credentials")
        return None

    return tweepy.Client(
        bearer_token=settings.twitter_bearer_token,
        consumer_key=settings.twitter_api_key,
        consumer_secret=settings.twitter_api_secret,
        access_token=settings.twitter_access_token,
        access_token_secret=settings.twitter_access_token_secret,
    )


async def post_match_preview_tweet(
    home_team: str,
    away_team: str,
    league_name: str,
    prediction: str,
    home_win_pct: float | None,
    value_bet: str | None,
    match_url: str,
) -> dict:
    """Post a match preview tweet.

    Returns:
        dict with tweet_id on success, error on failure.
    """
    client = get_twitter_client()
    if not client:
        return {"status": "skipped", "reason": "twitter_not_configured"}

    # Build tweet text (max 280 chars)
    lines = [
        f"⚽ {home_team} vs {away_team} — {league_name}",
        f"🤖 ScoreLock-prognos: {prediction}",
    ]

    if home_win_pct is not None:
        lines[1] += f" ({home_win_pct:.0f}%)"

    if value_bet:
        lines.append(f"💰 {value_bet}")

    lines.append(f"📊 Läs analysen → {match_url}")

    # Add hashtags if space allows
    tags = _league_hashtags(league_name)
    team_tags = f"#{home_team.replace(' ', '')} #{away_team.replace(' ', '')}"
    tags_line = f"{tags} {team_tags}"

    tweet_body = "\n".join(lines)
    if len(tweet_body) + len(tags_line) + 2 <= 280:
        tweet_body += f"\n\n{tags_line}"

    # Truncate if still too long
    if len(tweet_body) > 280:
        tweet_body = tweet_body[:277] + "..."

    try:
        response = client.create_tweet(text=tweet_body)
        tweet_id = response.data["id"]
        logger.info("tweet_posted", tweet_id=tweet_id, teams=f"{home_team} vs {away_team}")
        return {"status": "ok", "tweet_id": tweet_id}
    except Exception as e:
        logger.error("tweet_failed", error=str(e), teams=f"{home_team} vs {away_team}")
        return {"status": "error", "error": str(e)}


async def post_value_bet_alert_tweet(
    matches: list[dict],
    article_url: str,
) -> dict:
    """Post a daily value bet alert tweet.

    Args:
        matches: list of {home, away, league, bet, odds, edge}
        article_url: link to the full value bet article
    """
    client = get_twitter_client()
    if not client:
        return {"status": "skipped", "reason": "twitter_not_configured"}

    lines = ["🔥 Dagens Value Bets — ScoreLock AI\n"]

    for m in matches[:4]:  # Max 4 to fit in tweet
        edge_str = f"+{m['edge']:.1f}%" if m.get("edge") else ""
        lines.append(f"💰 {m['home']} vs {m['away']}: {m['bet']} @{m['odds']:.2f} {edge_str}")

    if len(matches) > 4:
        lines.append(f"...+{len(matches) - 4} fler")

    lines.append(f"\n📊 Fullständig analys → {article_url}")
    lines.append("#ValueBets #Betting #Football")

    tweet_body = "\n".join(lines)
    if len(tweet_body) > 280:
        tweet_body = tweet_body[:277] + "..."

    try:
        response = client.create_tweet(text=tweet_body)
        tweet_id = response.data["id"]
        logger.info("value_bet_tweet_posted", tweet_id=tweet_id, count=len(matches))
        return {"status": "ok", "tweet_id": tweet_id}
    except Exception as e:
        logger.error("value_bet_tweet_failed", error=str(e))
        return {"status": "error", "error": str(e)}


def _league_hashtags(league_name: str) -> str:
    """Map league names to common hashtags."""
    mapping = {
        "Premier League": "#PremierLeague #PL",
        "La Liga": "#LaLiga",
        "Serie A": "#SerieA",
        "Bundesliga": "#Bundesliga",
        "Ligue 1": "#Ligue1",
        "Champions League": "#UCL",
        "Europa League": "#UEL",
        "Conference League": "#UECL",
        "Allsvenskan": "#Allsvenskan #SvFF",
    }
    return mapping.get(league_name, "#Football")
