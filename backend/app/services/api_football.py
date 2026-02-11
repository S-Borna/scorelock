"""Client for API-Football (api-sports.io) — primary data source.

API docs: https://www.api-football.com/documentation-v3

Rate limits:
  - Free: 100 requests/day
  - Ultra ($29/mo): 75,000 requests/day, 30 requests/minute
"""

import httpx
import structlog
from datetime import date
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# ── League IDs in API-Football ─────────────────────────────
# Phase 1
LEAGUE_IDS = {
    # Domestic leagues
    "premier_league": 39,
    "la_liga": 140,
    "serie_a": 135,
    "bundesliga": 78,
    "allsvenskan": 113,
    # European cups
    "champions_league": 2,
    "europa_league": 3,
    "conference_league": 848,
    # Phase 2 — International
    "euro_championship": 4,
    "euro_qualifiers": 960,
    "world_cup": 1,
    "wc_qualifiers_europe": 32,
    "wc_qualifiers_south_america": 34,
    "wc_qualifiers_africa": 29,
    "wc_qualifiers_asia": 30,
    "copa_america": 9,
    "africa_cup": 6,
    "nations_league": 5,
    # Phase 3
    "ligue_1": 61,
    "primeira_liga": 94,
    "eredivisie": 88,
    "super_lig": 203,
}

PHASE_1_LEAGUES = [
    "premier_league",
    "la_liga",
    "serie_a",
    "bundesliga",
    "allsvenskan",
    "champions_league",
    "europa_league",
    "conference_league",
]


class APIFootballClient:
    """Async client for API-Football REST API."""

    def __init__(self):
        self.base_url = settings.api_football_base_url
        self.headers = {
            "x-apisports-key": settings.api_football_key,
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=30.0,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _get(self, endpoint: str, params: dict | None = None) -> dict:
        """Make a GET request with retry logic."""
        async with self._client() as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            # Log remaining requests
            remaining = response.headers.get("x-ratelimit-requests-remaining", "?")
            logger.info(
                "api_football_request",
                endpoint=endpoint,
                params=params,
                remaining_requests=remaining,
            )

            if data.get("errors"):
                logger.error("api_football_error", errors=data["errors"])

            return data

    # ── Leagues ────────────────────────────────────────────

    async def get_leagues(self, country: str | None = None) -> list[dict]:
        """Get available leagues, optionally filtered by country."""
        params = {}
        if country:
            params["country"] = country
        data = await self._get("/leagues", params)
        return data.get("response", [])

    # ── Fixtures ───────────────────────────────────────────

    async def get_fixtures_by_date(
        self, match_date: date, league_id: int | None = None
    ) -> list[dict]:
        """Get all fixtures for a specific date."""
        params = {"date": match_date.isoformat()}
        if league_id:
            params["league"] = league_id
        data = await self._get("/fixtures", params)
        return data.get("response", [])

    async def get_fixtures_by_league(
        self, league_id: int, season: int, round_name: str | None = None
    ) -> list[dict]:
        """Get fixtures for a league and season."""
        params = {"league": league_id, "season": season}
        if round_name:
            params["round"] = round_name
        data = await self._get("/fixtures", params)
        return data.get("response", [])

    async def get_live_fixtures(self) -> list[dict]:
        """Get all currently live fixtures."""
        data = await self._get("/fixtures", {"live": "all"})
        return data.get("response", [])

    async def get_fixture_by_id(self, fixture_id: int) -> dict | None:
        """Get a single fixture with full details."""
        data = await self._get("/fixtures", {"id": fixture_id})
        results = data.get("response", [])
        return results[0] if results else None

    # ── Fixture Statistics ─────────────────────────────────

    async def get_fixture_statistics(self, fixture_id: int) -> list[dict]:
        """Get match statistics (shots, possession, etc.)."""
        data = await self._get("/fixtures/statistics", {"fixture": fixture_id})
        return data.get("response", [])

    # ── Head to Head ───────────────────────────────────────

    async def get_head_to_head(
        self, team1_id: int, team2_id: int, last: int = 10
    ) -> list[dict]:
        """Get head-to-head history between two teams."""
        h2h = f"{team1_id}-{team2_id}"
        data = await self._get("/fixtures/headtohead", {"h2h": h2h, "last": last})
        return data.get("response", [])

    # ── Teams ──────────────────────────────────────────────

    async def get_team(self, team_id: int) -> dict | None:
        """Get team information."""
        data = await self._get("/teams", {"id": team_id})
        results = data.get("response", [])
        return results[0] if results else None

    async def get_teams_by_league(self, league_id: int, season: int) -> list[dict]:
        """Get all teams in a league for a season."""
        data = await self._get("/teams", {"league": league_id, "season": season})
        return data.get("response", [])

    # ── Standings ──────────────────────────────────────────

    async def get_standings(self, league_id: int, season: int) -> list[dict]:
        """Get league standings."""
        data = await self._get("/standings", {"league": league_id, "season": season})
        results = data.get("response", [])
        if results:
            return results[0].get("league", {}).get("standings", [[]])[0]
        return []

    # ── Odds ───────────────────────────────────────────────

    async def get_odds(
        self, fixture_id: int, bookmaker: int | None = None
    ) -> list[dict]:
        """Get pre-match odds for a fixture."""
        params = {"fixture": fixture_id}
        if bookmaker:
            params["bookmaker"] = bookmaker
        data = await self._get("/odds", params)
        return data.get("response", [])

    # ── Players ────────────────────────────────────────────

    async def get_team_squad(self, team_id: int) -> list[dict]:
        """Get current squad for a team."""
        data = await self._get("/players/squads", {"team": team_id})
        results = data.get("response", [])
        if results:
            return results[0].get("players", [])
        return []

    async def get_injuries(
        self, league_id: int, season: int, fixture_id: int | None = None
    ) -> list[dict]:
        """Get injury/suspension data."""
        params = {"league": league_id, "season": season}
        if fixture_id:
            params["fixture"] = fixture_id
        data = await self._get("/injuries", params)
        return data.get("response", [])

    # ── Predictions (API-Football's own, for comparison) ───

    async def get_api_prediction(self, fixture_id: int) -> dict | None:
        """Get API-Football's built-in prediction for comparison."""
        data = await self._get("/predictions", {"fixture": fixture_id})
        results = data.get("response", [])
        return results[0] if results else None


# Singleton instance
api_football = APIFootballClient()
