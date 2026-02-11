"""Fetch historical fixture data from API-Football for model training.

Incrementally fetches finished fixtures for tracked leagues and seasons.
Rate-limited to respect API-Football Free plan (100 req/day, 10 req/min).

Usage:
    docker compose exec backend python -m app.services.historical
    docker compose exec backend python -m app.services.historical --dry-run
"""

import asyncio
import time
import structlog

from app.core.database import async_session
from app.services.api_football import api_football, LEAGUE_IDS, PHASE_1_LEAGUES
from app.services.db_service import (
    get_league_by_api_id,
    upsert_fixtures_batch,
    upsert_standing,
)

logger = structlog.get_logger()

# Free plan: seasons 2022-2024 (current + 2 previous)
HISTORICAL_SEASONS = [2022, 2023, 2024]

# Rate limiting for Free plan
API_DELAY_SECONDS = 7.0


async def fetch_historical_fixtures(
    leagues: list[str] | None = None,
    seasons: list[int] | None = None,
    dry_run: bool = False,
) -> dict:
    """Fetch historical fixtures for specified leagues and seasons.

    Each league+season is a single API call returning all fixtures.

    Returns:
        Summary dict with counts and errors.
    """
    leagues = leagues or list(PHASE_1_LEAGUES)
    seasons = seasons or HISTORICAL_SEASONS

    total_fixtures = 0
    total_requests = 0
    errors: list[str] = []

    async with async_session() as session:
        for league_name in leagues:
            api_id = LEAGUE_IDS.get(league_name)
            if not api_id:
                logger.warning("unknown_league", league=league_name)
                continue

            league = await get_league_by_api_id(session, api_id)
            if not league:
                logger.warning("league_not_in_db", league=league_name, api_id=api_id)
                continue

            for season in seasons:
                logger.info(
                    "fetching_historical",
                    league=league_name,
                    season=season,
                    api_id=api_id,
                )

                if dry_run:
                    logger.info("dry_run_skip", league=league_name, season=season)
                    continue

                try:
                    time.sleep(API_DELAY_SECONDS)
                    total_requests += 1

                    fixtures = await api_football.get_fixtures_by_league(api_id, season)

                    if not fixtures:
                        logger.warning("no_fixtures", league=league_name, season=season)
                        continue

                    count = await upsert_fixtures_batch(session, fixtures, league)
                    total_fixtures += count

                    logger.info(
                        "historical_upserted",
                        league=league_name,
                        season=season,
                        fetched=len(fixtures),
                        upserted=count,
                    )

                except Exception as exc:
                    error_msg = f"{league_name}/{season}: {exc}"
                    logger.error("historical_fetch_failed", error=error_msg)
                    errors.append(error_msg)

        await session.commit()

    summary = {
        "total_fixtures": total_fixtures,
        "total_requests": total_requests,
        "leagues_processed": len(leagues),
        "seasons_processed": len(seasons),
        "errors": errors,
    }
    logger.info("historical_fetch_complete", **summary)
    return summary


async def fetch_historical_standings(
    leagues: list[str] | None = None,
    seasons: list[int] | None = None,
) -> dict:
    """Fetch historical standings for specified leagues and seasons."""
    leagues = leagues or list(PHASE_1_LEAGUES)
    seasons = seasons or HISTORICAL_SEASONS

    total_standings = 0
    total_requests = 0
    errors: list[str] = []

    async with async_session() as session:
        for league_name in leagues:
            api_id = LEAGUE_IDS.get(league_name)
            if not api_id:
                continue

            league = await get_league_by_api_id(session, api_id)
            if not league:
                continue

            for season in seasons:
                logger.info("fetching_standings", league=league_name, season=season)

                try:
                    time.sleep(API_DELAY_SECONDS)
                    total_requests += 1

                    standings = await api_football.get_standings(api_id, season)
                    for entry in standings:
                        await upsert_standing(session, entry, league, season)
                        total_standings += 1

                    logger.info(
                        "standings_upserted",
                        league=league_name,
                        season=season,
                        count=len(standings),
                    )

                except Exception as exc:
                    error_msg = f"{league_name}/{season}: {exc}"
                    logger.error("standings_fetch_failed", error=error_msg)
                    errors.append(error_msg)

        await session.commit()

    return {
        "total_standings": total_standings,
        "total_requests": total_requests,
        "errors": errors,
    }


# ── CLI entry point ────────────────────────────────────────


async def main() -> None:
    """Fetch all historical data (fixtures + standings)."""
    import sys

    print("=" * 60)
    print("ScoreLock — Historical Data Fetcher")
    print("=" * 60)
    print(f"Leagues: {', '.join(PHASE_1_LEAGUES)}")
    print(f"Seasons: {HISTORICAL_SEASONS}")
    est_calls = len(PHASE_1_LEAGUES) * len(HISTORICAL_SEASONS) * 2
    print(f"Estimated API calls: {est_calls}")
    print(f"Estimated time: ~{est_calls * 7 // 60} minutes")
    print("=" * 60)

    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("\nDRY RUN — no API calls will be made\n")

    # Fetch specific leagues/seasons if provided
    league_args = [a for a in sys.argv[1:] if not a.startswith("--")]
    leagues = league_args if league_args else None

    # Phase 1: Fixtures
    print("\nFetching historical fixtures...")
    fixture_result = await fetch_historical_fixtures(leagues=leagues, dry_run=dry_run)
    print(f"  Fixtures upserted: {fixture_result['total_fixtures']}")
    print(f"  API requests used: {fixture_result['total_requests']}")

    if fixture_result["errors"]:
        print(f"  Errors: {len(fixture_result['errors'])}")
        for e in fixture_result["errors"]:
            print(f"    - {e}")

    # Phase 2: Standings
    if not dry_run:
        print("\nFetching historical standings...")
        standings_result = await fetch_historical_standings(leagues=leagues)
        print(f"  Standings upserted: {standings_result['total_standings']}")
        print(f"  API requests used: {standings_result['total_requests']}")

    print("\nHistorical data fetch complete!")


if __name__ == "__main__":
    asyncio.run(main())
