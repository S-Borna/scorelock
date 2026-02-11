"""Client for football-data.org API — secondary data source for fixtures + standings.

API docs: https://docs.football-data.org/general/v4/index.html

Rate limits (free tier):
  - 10 requests/minute
  - Covers: PL, La Liga, Serie A, Bundesliga, Ligue 1, CL, EC
  - Does NOT cover: Allsvenskan, Europa League, Conference League

Strategy:
  - Use football-data.org as primary for fixtures + standings (generous quota)
  - Use API-Football only for live scores + leagues not in football-data.org
"""

import httpx
import structlog
from datetime import date, timedelta
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.quota_manager import get_quota_manager

logger = structlog.get_logger()
settings = get_settings()


# ── League ID mapping: football-data.org → our internal API-Football IDs ──

# football-data.org competition codes (free tier)
FD_COMPETITIONS = {
    "PL": {"fd_id": 2021, "api_football_id": 39, "name": "premier_league"},
    "PD": {"fd_id": 2014, "api_football_id": 140, "name": "la_liga"},
    "SA": {"fd_id": 2019, "api_football_id": 135, "name": "serie_a"},
    "BL1": {"fd_id": 2002, "api_football_id": 78, "name": "bundesliga"},
    "FL1": {"fd_id": 2015, "api_football_id": 61, "name": "ligue_1"},
    "CL": {"fd_id": 2001, "api_football_id": 2, "name": "champions_league"},
}

# Reverse lookup: api_football_id → FD competition code
API_FOOTBALL_TO_FD: dict[int, str] = {
    v["api_football_id"]: code for code, v in FD_COMPETITIONS.items()
}

# Leagues NOT covered by football-data.org free tier (must use API-Football)
FD_UNSUPPORTED_LEAGUES = {"allsvenskan", "europa_league", "conference_league"}


class FootballDataClient:
    """Async client for football-data.org REST API v4."""

    def __init__(self):
        self.base_url = settings.football_data_base_url
        self.headers = {
            "X-Auth-Token": settings.football_data_key,
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=30.0,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def _get(self, endpoint: str, params: dict | None = None) -> dict:
        """Make a GET request with retry + quota tracking."""
        quota = get_quota_manager()

        # Check per-minute quota
        if not await quota.can_call("football_data"):
            raise QuotaExhaustedError("football_data per-minute quota exhausted")

        # Check daily quota
        if not await quota.can_call("football_data_daily"):
            raise QuotaExhaustedError("football_data daily quota exhausted")

        async with self._client() as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            # Record both quotas
            await quota.record_call("football_data")
            await quota.record_call("football_data_daily")

            remaining = response.headers.get("X-Requests-Available-Minute", "?")
            logger.info(
                "football_data_request",
                endpoint=endpoint,
                remaining_per_min=remaining,
            )

            return data

    # ── Competitions ───────────────────────────────────────

    async def get_competition(self, code: str) -> dict:
        """Get competition details by code (e.g. 'PL', 'BL1')."""
        data = await self._get(f"/competitions/{code}")
        return data

    # ── Standings ──────────────────────────────────────────

    async def get_standings(self, code: str, season: int | None = None) -> list[dict]:
        """Get league standings.

        Args:
            code: Competition code (e.g. 'PL', 'BL1')
            season: Season year (e.g. 2024). None = current.

        Returns:
            List of standing entries with team, position, points, etc.
        """
        params = {}
        if season:
            params["season"] = season

        data = await self._get(f"/competitions/{code}/standings", params or None)
        standings = data.get("standings", [])

        # Get TOTAL table (not home/away splits)
        for table in standings:
            if table.get("type") == "TOTAL":
                return table.get("table", [])

        # Fallback: return first table
        if standings:
            return standings[0].get("table", [])
        return []

    # ── Matches (Fixtures) ─────────────────────────────────

    async def get_matches(
        self,
        code: str,
        date_from: date | None = None,
        date_to: date | None = None,
        status: str | None = None,
        matchday: int | None = None,
    ) -> list[dict]:
        """Get matches for a competition.

        Args:
            code: Competition code (e.g. 'PL')
            date_from: Start date filter
            date_to: End date filter
            status: Match status filter (SCHEDULED, LIVE, FINISHED, etc.)
            matchday: Matchday/round number

        Returns:
            List of match dicts from football-data.org API.
        """
        params = {}
        if date_from:
            params["dateFrom"] = date_from.isoformat()
        if date_to:
            params["dateTo"] = date_to.isoformat()
        if status:
            params["status"] = status
        if matchday:
            params["matchday"] = matchday

        data = await self._get(f"/competitions/{code}/matches", params or None)
        return data.get("matches", [])

    async def get_upcoming_matches(self, code: str, days_ahead: int = 14) -> list[dict]:
        """Get scheduled matches for the next N days."""
        today = date.today()
        end = today + timedelta(days=days_ahead)
        return await self.get_matches(
            code,
            date_from=today,
            date_to=end,
            status="SCHEDULED",
        )

    async def get_todays_matches(self, code: str) -> list[dict]:
        """Get today's matches across all statuses."""
        today = date.today()
        return await self.get_matches(code, date_from=today, date_to=today)

    # ── Teams ──────────────────────────────────────────────

    async def get_teams(self, code: str, season: int | None = None) -> list[dict]:
        """Get all teams in a competition."""
        params = {}
        if season:
            params["season"] = season
        data = await self._get(f"/competitions/{code}/teams", params or None)
        return data.get("teams", [])

    # ── Scorers ────────────────────────────────────────────

    async def get_scorers(self, code: str, limit: int = 10) -> list[dict]:
        """Get top scorers for a competition."""
        data = await self._get(f"/competitions/{code}/scorers", {"limit": limit})
        return data.get("scorers", [])

    # ── Data Normalization ─────────────────────────────────

    @staticmethod
    def normalize_match_to_fixture(match: dict, league_api_football_id: int) -> dict:
        """Convert a football-data.org match to our internal fixture format.

        Maps football-data.org response format → API-Football-compatible format
        so our existing db_service.upsert_fixture() can ingest it.

        Returns:
            Dict matching the shape expected by upsert_fixture(), or empty
            dict if data is incomplete.
        """
        home = match.get("homeTeam", {})
        away = match.get("awayTeam", {})
        score = match.get("score", {})
        ft = score.get("fullTime", {})
        ht = score.get("halfTime", {})

        # Map football-data.org status → API-Football status
        fd_status = match.get("status", "")
        status_map = {
            "SCHEDULED": "NS",  # Not Started
            "TIMED": "NS",
            "IN_PLAY": "1H",  # First Half (simplification)
            "PAUSED": "HT",  # Half Time
            "FINISHED": "FT",  # Full Time
            "POSTPONED": "PST",
            "CANCELLED": "CANC",
            "SUSPENDED": "SUSP",
            "AWARDED": "AWD",
        }

        # Use match ID from football-data.org (add offset to avoid collision
        # with API-Football IDs). football-data.org IDs are typically 6-digit,
        # API-Football IDs are also 6-digit. Use a large offset.
        fd_match_id = match.get("id", 0)
        # We store football-data.org IDs with a 2_000_000 offset
        api_football_id = fd_match_id + 2_000_000

        utc_date = match.get("utcDate", "")

        if not home.get("id") or not away.get("id"):
            return {}

        return {
            "fixture": {
                "id": api_football_id,
                "date": utc_date,
                "status": {
                    "short": status_map.get(fd_status, "NS"),
                },
            },
            "league": {
                "id": league_api_football_id,
                "round": f"Regular Season - {match.get('matchday', '?')}",
                "season": int(match.get("season", {}).get("startDate", "2024")[:4]),
            },
            "teams": {
                "home": {
                    "id": home.get("id", 0) + 2_000_000,  # Offset
                    "name": home.get("name", ""),
                    "logo": home.get("crest", ""),
                },
                "away": {
                    "id": away.get("id", 0) + 2_000_000,  # Offset
                    "name": away.get("name", ""),
                    "logo": away.get("crest", ""),
                },
            },
            "goals": {
                "home": ft.get("home"),
                "away": ft.get("away"),
            },
            "score": {
                "halftime": {
                    "home": ht.get("home"),
                    "away": ht.get("away"),
                },
                "fulltime": {
                    "home": ft.get("home"),
                    "away": ft.get("away"),
                },
            },
        }

    @staticmethod
    def normalize_standing(entry: dict, competition_code: str) -> dict:
        """Convert football-data.org standing → API-Football-compatible format.

        Returns dict compatible with db_service.upsert_standing().
        """
        team = entry.get("team", {})
        return {
            "team": {
                "id": team.get("id", 0) + 2_000_000,
                "name": team.get("name", ""),
                "logo": team.get("crest", ""),
            },
            "rank": entry.get("position", 0),
            "points": entry.get("points", 0),
            "all": {
                "played": entry.get("playedGames", 0),
                "win": entry.get("won", 0),
                "draw": entry.get("draw", 0),
                "lose": entry.get("lost", 0),
                "goals": {
                    "for": entry.get("goalsFor", 0),
                    "against": entry.get("goalsAgainst", 0),
                },
            },
            "form": entry.get("form", ""),
            "goalsDiff": entry.get("goalDifference", 0),
        }


class QuotaExhaustedError(Exception):
    """Raised when API quota is exhausted."""

    pass


# Singleton instance
football_data = FootballDataClient()
