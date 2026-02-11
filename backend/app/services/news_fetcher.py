"""Football news fetcher — aggregates RSS feeds for sentiment analysis.

Scrapes RSS feeds from major football news sources to gather recent
text about specific teams. This feeds into the sentiment analyzer.
"""

import asyncio
import xml.etree.ElementTree as ET
import httpx
import structlog

logger = structlog.get_logger()

# ── RSS Feed Sources ───────────────────────────────────────

RSS_FEEDS: list[dict[str, str]] = [
    # English sources
    {"name": "BBC Football", "url": "https://feeds.bbci.co.uk/sport/football/rss.xml"},
    {"name": "Guardian Football", "url": "https://www.theguardian.com/football/rss"},
    {"name": "ESPN FC", "url": "https://www.espn.com/espn/rss/soccer/news"},
    {"name": "Sky Sports Football", "url": "https://www.skysports.com/rss/12040"},
    {"name": "Goal.com", "url": "https://www.goal.com/feeds/en/news"},
    # Swedish sources
    {
        "name": "SVT Sport Fotboll",
        "url": "https://www.svt.se/nyheter/sport/fotboll/rss.xml",
    },
    {"name": "Fotbollskanalen", "url": "https://www.fotbollskanalen.se/rss/"},
    {
        "name": "Aftonbladet Sport",
        "url": "https://rss.aftonbladet.se/rss2/small/pages/sections/sportbladet/",
    },
    # European sources
    {"name": "UEFA", "url": "https://www.uefa.com/rssfeed/uefachampionsleague/rss.xml"},
    {"name": "Transfermarkt News", "url": "https://www.transfermarkt.com/rss/news"},
]

FETCH_TIMEOUT_SECONDS = 10
MAX_ARTICLES_PER_TEAM = 15
MAX_AGE_DAYS = 3


async def _fetch_feed(client: httpx.AsyncClient, feed: dict[str, str]) -> list[dict]:
    """Fetch and parse a single RSS feed, returning article dicts."""
    articles: list[dict] = []
    try:
        response = await client.get(feed["url"], timeout=FETCH_TIMEOUT_SECONDS)
        response.raise_for_status()

        root = ET.fromstring(response.text)

        # Standard RSS 2.0 structure
        for item in root.iter("item"):
            title_el = item.find("title")
            desc_el = item.find("description")
            pub_date_el = item.find("pubDate")

            title = (
                title_el.text.strip() if title_el is not None and title_el.text else ""
            )
            description = (
                desc_el.text.strip() if desc_el is not None and desc_el.text else ""
            )
            pub_date = (
                pub_date_el.text.strip()
                if pub_date_el is not None and pub_date_el.text
                else ""
            )

            if title:
                articles.append(
                    {
                        "title": title,
                        "description": _strip_html(description),
                        "source": feed["name"],
                        "pub_date": pub_date,
                    }
                )

    except httpx.HTTPStatusError as exc:
        logger.warning(
            "rss_http_error", feed=feed["name"], status=exc.response.status_code
        )
    except ET.ParseError:
        logger.warning("rss_parse_error", feed=feed["name"])
    except Exception as exc:
        logger.warning("rss_fetch_failed", feed=feed["name"], error=str(exc))

    return articles


def _strip_html(text: str) -> str:
    """Remove HTML tags from text (simple regex-free approach)."""
    result: list[str] = []
    in_tag = False
    for char in text:
        if char == "<":
            in_tag = True
        elif char == ">":
            in_tag = False
        elif not in_tag:
            result.append(char)
    return "".join(result).strip()


def _matches_team(text: str, team_name: str) -> bool:
    """Check if article text mentions the team (case-insensitive).

    Uses team name and common short forms.
    """
    text_lower = text.lower()
    team_lower = team_name.lower()

    # Full name match
    if team_lower in text_lower:
        return True

    # Try last word (e.g. "Manchester United" → "United", "Real Madrid" → "Madrid")
    parts = team_lower.split()
    if len(parts) > 1:
        # Match on distinctive part (skip generic words)
        generic = {"fc", "sc", "cf", "afc", "ac", "as", "ss", "bk", "if", "fk", "sk"}
        for part in parts:
            if part not in generic and len(part) > 3 and part in text_lower:
                return True

    return False


async def fetch_team_news(team_name: str) -> list[dict]:
    """Fetch recent news articles mentioning a specific team.

    Args:
        team_name: The team to search for (e.g. "Manchester United").

    Returns:
        List of article dicts with title, description, source.
    """
    async with httpx.AsyncClient(
        headers={"User-Agent": "ScoreLock/1.0 (Football Analytics)"},
        follow_redirects=True,
    ) as client:
        tasks = [_fetch_feed(client, feed) for feed in RSS_FEEDS]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    all_articles: list[dict] = []
    for result in results:
        if isinstance(result, list):
            all_articles.extend(result)

    # Filter for articles mentioning this team
    matching = [
        article
        for article in all_articles
        if _matches_team(
            f"{article['title']} {article['description']}",
            team_name,
        )
    ]

    # Sort by recency (newest first) and cap
    matching.sort(key=lambda a: a.get("pub_date", ""), reverse=True)
    return matching[:MAX_ARTICLES_PER_TEAM]


def format_articles_for_analysis(articles: list[dict]) -> str:
    """Format articles into a single text block for the LLM.

    Returns empty string if no articles found.
    """
    if not articles:
        return ""

    parts: list[str] = []
    for article in articles:
        source = article.get("source", "Unknown")
        title = article.get("title", "")
        desc = article.get("description", "")
        parts.append(f"[{source}] {title}\n{desc}")

    return "\n---\n".join(parts)
