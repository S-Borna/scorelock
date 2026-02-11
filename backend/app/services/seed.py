"""Seed script — populate leagues and teams from API-Football.

Usage (inside container):
    python -m app.services.seed

This uses ~16 API requests (8 leagues + 8 team lists).
Safe on the Free plan (100 requests/day).
"""

import asyncio

import structlog

from app.core.database import async_session
from app.services.api_football import APIFootballClient, LEAGUE_IDS, PHASE_1_LEAGUES
from app.services.db_service import upsert_league, upsert_team

logger = structlog.get_logger()

# Free plan: 10 requests/minute — add delay between calls
API_DELAY_SECONDS = 7.0

# Phase mapping for leagues
LEAGUE_PHASES: dict[str, int] = {
    **{name: 1 for name in PHASE_1_LEAGUES},
    "euro_championship": 2, "euro_qualifiers": 2,
    "world_cup": 2, "wc_qualifiers_europe": 2,
    "wc_qualifiers_south_america": 2, "wc_qualifiers_africa": 2,
    "wc_qualifiers_asia": 2, "copa_america": 2,
    "africa_cup": 2, "nations_league": 2,
    "ligue_1": 3, "primeira_liga": 3, "eredivisie": 3, "super_lig": 3,
}


async def seed_leagues(client: APIFootballClient, leagues_to_seed: list[str] | None = None) -> dict[str, int]:
    """Seed leagues into the database. Returns {league_name: db_id}."""
    targets = leagues_to_seed or PHASE_1_LEAGUES
    league_map: dict[str, int] = {}

    async with async_session() as session:
        for league_name in targets:
            api_id = LEAGUE_IDS.get(league_name)
            if not api_id:
                logger.warning("unknown_league", league=league_name)
                continue

            # Fetch by specific league ID to avoid one big request
            specific = await client._get("/leagues", {"id": api_id})
            entries = specific.get("response", [])
            league_info = entries[0] if entries else None
            await asyncio.sleep(API_DELAY_SECONDS)

            if not league_info:
                logger.warning("league_not_found", league=league_name, api_id=api_id)
                continue

            league_data = league_info.get("league", {})
            country_data = league_info.get("country", {})
            seasons = league_info.get("seasons", [])

            # Find current season
            current_season = None
            for s in seasons:
                if s.get("current"):
                    current_season = s.get("year")
                    break

            league = await upsert_league(
                session,
                api_id=league_data.get("id"),
                name=league_data.get("name", league_name),
                country=country_data.get("name", "Unknown"),
                logo_url=league_data.get("logo"),
                league_type=league_data.get("type", "league"),
                current_season=current_season,
                phase=LEAGUE_PHASES.get(league_name, 1),
            )
            league_map[league_name] = league.id
            logger.info(
                "seeded_league",
                league=league.name,
                country=country_data.get("name"),
                season=current_season,
                db_id=league.id,
            )

        await session.commit()

    return league_map


async def seed_teams(client: APIFootballClient, league_map: dict[str, int] | None = None) -> int:
    """Seed teams for all Phase 1 leagues. Returns total teams seeded."""
    total = 0
    # Free plan only supports seasons 2022-2024,
    # so we use 2024 for team data (same teams, stable enough)
    SEED_SEASON = 2024

    async with async_session() as session:
        for league_name in PHASE_1_LEAGUES:
            api_id = LEAGUE_IDS[league_name]

            try:
                teams = await client.get_teams_by_league(api_id, SEED_SEASON)
                await asyncio.sleep(API_DELAY_SECONDS)
            except Exception as exc:
                logger.error("team_fetch_failed", league=league_name, error=str(exc))
                continue

            for entry in teams:
                team_data = entry.get("team", {})
                venue_data = entry.get("venue", {})
                team_api_id = team_data.get("id")
                if not team_api_id:
                    continue

                await upsert_team(
                    session,
                    api_id=team_api_id,
                    name=team_data.get("name", "Unknown"),
                    logo_url=team_data.get("logo"),
                    country=team_data.get("country"),
                    venue_name=venue_data.get("name"),
                    venue_capacity=venue_data.get("capacity"),
                    short_name=team_data.get("code"),
                )
                total += 1

            logger.info("seeded_teams", league=league_name, count=len(teams))

        await session.commit()

    return total


async def seed_all() -> None:
    """Run full seed: leagues → teams."""
    client = APIFootballClient()

    logger.info("seed_started")

    # 1. Seed leagues (8 requests — one per league via direct ID lookup)
    league_map = await seed_leagues(client)
    logger.info("leagues_seeded", count=len(league_map))

    # 2. Seed teams (8 requests — one per league)
    team_count = await seed_teams(client, league_map)
    logger.info("teams_seeded", count=team_count)

    logger.info("seed_complete", leagues=len(league_map), teams=team_count)


if __name__ == "__main__":
    asyncio.run(seed_all())
