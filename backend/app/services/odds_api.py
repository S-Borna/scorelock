"""Client for The Odds API — real-time odds from 40+ bookmakers.

API docs: https://the-odds-api.com/liveapi/guides/v4/

Rate limits (free tier):
  - 500 requests/month
  - All major soccer leagues covered
  - Pre-match odds for 1X2, totals, spreads
"""

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.quota_manager import get_quota_manager

logger = structlog.get_logger()
settings = get_settings()


# ── Sport key mapping → our internal API-Football league IDs ──

ODDS_SPORT_KEYS: dict[str, dict] = {
    "soccer_epl": {
        "api_football_id": 39,
        "name": "premier_league",
    },
    "soccer_spain_la_liga": {
        "api_football_id": 140,
        "name": "la_liga",
    },
    "soccer_italy_serie_a": {
        "api_football_id": 135,
        "name": "serie_a",
    },
    "soccer_germany_bundesliga": {
        "api_football_id": 78,
        "name": "bundesliga",
    },
    "soccer_sweden_allsvenskan": {
        "api_football_id": 113,
        "name": "allsvenskan",
    },
    "soccer_uefa_champs_league": {
        "api_football_id": 2,
        "name": "champions_league",
    },
    "soccer_uefa_europa_league": {
        "api_football_id": 3,
        "name": "europa_league",
    },
    "soccer_france_ligue_one": {
        "api_football_id": 61,
        "name": "ligue_1",
    },
}

# Reverse: api_football_id → sport key
API_FOOTBALL_TO_SPORT_KEY: dict[int, str] = {
    v["api_football_id"]: k for k, v in ODDS_SPORT_KEYS.items()
}

# Market keys
MARKET_H2H = "h2h"           # 1X2 (head-to-head)
MARKET_TOTALS = "totals"     # Over/Under
MARKET_SPREADS = "spreads"   # Asian Handicap

# Regions to fetch (EU bookmakers most relevant)
DEFAULT_REGIONS = "eu,uk"


class OddsAPIClient:
    """Async client for The Odds API v4."""

    def __init__(self):
        self.base_url = settings.the_odds_api_base_url
        self.api_key = settings.the_odds_api_key

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def _get(self, endpoint: str, params: dict | None = None) -> list | dict:
        """Make a GET request with quota tracking."""
        quota = get_quota_manager()

        if not await quota.can_call("the_odds_api"):
            raise QuotaExhaustedError("the_odds_api monthly quota exhausted")

        base_params = {"apiKey": self.api_key}
        if params:
            base_params.update(params)

        async with self._client() as client:
            response = await client.get(endpoint, params=base_params)
            response.raise_for_status()
            data = response.json()

            await quota.record_call("the_odds_api")

            # The Odds API returns remaining quota in headers
            remaining = response.headers.get("x-requests-remaining", "?")
            used = response.headers.get("x-requests-used", "?")
            logger.info(
                "odds_api_request",
                endpoint=endpoint,
                remaining=remaining,
                used=used,
            )

            return data

    # ── Sports ─────────────────────────────────────────────

    async def get_sports(self) -> list[dict]:
        """List all available sports/leagues."""
        return await self._get("/sports")

    # ── Odds ───────────────────────────────────────────────

    async def get_odds(
        self,
        sport_key: str,
        markets: str = MARKET_H2H,
        regions: str = DEFAULT_REGIONS,
    ) -> list[dict]:
        """Get pre-match odds for a sport/league.

        Args:
            sport_key: e.g. 'soccer_epl', 'soccer_spain_la_liga'
            markets: Comma-separated market types ('h2h', 'totals', 'spreads')
            regions: Comma-separated regions ('eu', 'uk', 'us', 'au')

        Returns:
            List of event dicts with bookmaker odds.
        """
        return await self._get(
            f"/sports/{sport_key}/odds",
            {
                "markets": markets,
                "regions": regions,
                "oddsFormat": "decimal",
            },
        )

    async def get_h2h_and_totals(
        self,
        sport_key: str,
        regions: str = DEFAULT_REGIONS,
    ) -> list[dict]:
        """Get both 1X2 and Over/Under odds in a single call (saves quota)."""
        return await self._get(
            f"/sports/{sport_key}/odds",
            {
                "markets": f"{MARKET_H2H},{MARKET_TOTALS}",
                "regions": regions,
                "oddsFormat": "decimal",
            },
        )

    async def get_event_odds(
        self,
        sport_key: str,
        event_id: str,
        markets: str = MARKET_H2H,
        regions: str = DEFAULT_REGIONS,
    ) -> dict:
        """Get odds for a specific event."""
        return await self._get(
            f"/sports/{sport_key}/events/{event_id}/odds",
            {
                "markets": markets,
                "regions": regions,
                "oddsFormat": "decimal",
            },
        )

    # ── Data Normalization ─────────────────────────────────

    @staticmethod
    def extract_best_odds(event: dict) -> dict:
        """Extract best available odds across all bookmakers for an event.

        Returns:
            Dict with home/draw/away best odds + bookmaker names,
            and over/under if available.
        """
        best = {
            "home_odds": 0.0,
            "draw_odds": 0.0,
            "away_odds": 0.0,
            "home_bookmaker": "",
            "draw_bookmaker": "",
            "away_bookmaker": "",
            "over_25_odds": 0.0,
            "under_25_odds": 0.0,
            "over_bookmaker": "",
            "under_bookmaker": "",
        }

        home_team = event.get("home_team", "")
        away_team = event.get("away_team", "")

        for bookmaker in event.get("bookmakers", []):
            bm_name = bookmaker.get("title", "Unknown")

            for market in bookmaker.get("markets", []):
                market_key = market.get("key", "")

                if market_key == "h2h":
                    for outcome in market.get("outcomes", []):
                        name = outcome.get("name", "")
                        price = outcome.get("price", 0.0)

                        if name == home_team and price > best["home_odds"]:
                            best["home_odds"] = price
                            best["home_bookmaker"] = bm_name
                        elif name == away_team and price > best["away_odds"]:
                            best["away_odds"] = price
                            best["away_bookmaker"] = bm_name
                        elif name == "Draw" and price > best["draw_odds"]:
                            best["draw_odds"] = price
                            best["draw_bookmaker"] = bm_name

                elif market_key == "totals":
                    for outcome in market.get("outcomes", []):
                        name = outcome.get("name", "")
                        point = outcome.get("point", 0)
                        price = outcome.get("price", 0.0)

                        # Only track 2.5 line
                        if point == 2.5:
                            if name == "Over" and price > best["over_25_odds"]:
                                best["over_25_odds"] = price
                                best["over_bookmaker"] = bm_name
                            elif name == "Under" and price > best["under_25_odds"]:
                                best["under_25_odds"] = price
                                best["under_bookmaker"] = bm_name

        return best

    @staticmethod
    def match_event_to_fixture(
        event: dict, fixture_name_map: dict[str, int]
    ) -> int | None:
        """Try to match an Odds API event to a fixture ID in our DB.

        Uses fuzzy team name matching.

        Args:
            event: Odds API event dict
            fixture_name_map: {"home_team vs away_team": fixture_id}

        Returns:
            fixture_id if matched, None otherwise.
        """
        home = event.get("home_team", "").lower().strip()
        away = event.get("away_team", "").lower().strip()

        # Try exact match
        key = f"{home} vs {away}"
        if key in fixture_name_map:
            return fixture_name_map[key]

        # Try partial match (team name in fixture key)
        for fixture_key, fixture_id in fixture_name_map.items():
            parts = fixture_key.split(" vs ")
            if len(parts) == 2:
                if (home in parts[0] or parts[0] in home) and (
                    away in parts[1] or parts[1] in away
                ):
                    return fixture_id

        return None


class QuotaExhaustedError(Exception):
    """Raised when API quota is exhausted."""
    pass


# Singleton
odds_api = OddsAPIClient()
