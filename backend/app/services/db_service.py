"""Database service layer — all DB read/write operations for ScoreLock.

Centralizes upsert and query logic so Celery tasks and API routes
share the same data access patterns.
"""

from datetime import date, datetime, timedelta
from sqlalchemy import select, func, and_, or_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from app.core.database import async_session
from app.models.models import (
    League, Team, Fixture, Odds, Prediction,
    SentimentScore, Standing, MatchStatus,
)

logger = structlog.get_logger()

# ── Status mapping from API-Football ──────────────────────

API_STATUS_MAP: dict[str, MatchStatus] = {
    "TBD": MatchStatus.SCHEDULED,
    "NS": MatchStatus.SCHEDULED,
    "1H": MatchStatus.LIVE,
    "HT": MatchStatus.HALFTIME,
    "2H": MatchStatus.LIVE,
    "ET": MatchStatus.LIVE,
    "BT": MatchStatus.LIVE,
    "P": MatchStatus.LIVE,
    "SUSP": MatchStatus.LIVE,
    "INT": MatchStatus.LIVE,
    "FT": MatchStatus.FINISHED,
    "AET": MatchStatus.FINISHED,
    "PEN": MatchStatus.FINISHED,
    "PST": MatchStatus.POSTPONED,
    "CANC": MatchStatus.CANCELLED,
    "ABD": MatchStatus.CANCELLED,
    "AWD": MatchStatus.FINISHED,
    "WO": MatchStatus.FINISHED,
    "LIVE": MatchStatus.LIVE,
}


# ── League operations ─────────────────────────────────────

async def upsert_league(
    session: AsyncSession,
    api_id: int,
    name: str,
    country: str,
    logo_url: str | None,
    league_type: str,
    current_season: int | None,
    phase: int = 1,
) -> League:
    """Insert or update a league by API-Football ID."""
    stmt = pg_insert(League).values(
        api_football_id=api_id,
        name=name,
        country=country,
        logo_url=logo_url,
        type=league_type,
        current_season=current_season,
        is_active=True,
        phase=phase,
    ).on_conflict_do_update(
        index_elements=["api_football_id"],
        set_={
            "name": name,
            "country": country,
            "logo_url": logo_url,
            "current_season": current_season,
        },
    ).returning(League)
    result = await session.execute(stmt)
    return result.scalar_one()


async def get_all_leagues(session: AsyncSession) -> list[League]:
    """Get all active leagues."""
    result = await session.execute(
        select(League).where(League.is_active.is_(True)).order_by(League.phase, League.name)
    )
    return list(result.scalars().all())


async def get_league_by_api_id(session: AsyncSession, api_id: int) -> League | None:
    """Get a league by its API-Football ID."""
    result = await session.execute(
        select(League).where(League.api_football_id == api_id)
    )
    return result.scalar_one_or_none()


# ── Team operations ────────────────────────────────────────

async def upsert_team(
    session: AsyncSession,
    api_id: int,
    name: str,
    logo_url: str | None = None,
    country: str | None = None,
    venue_name: str | None = None,
    venue_capacity: int | None = None,
    short_name: str | None = None,
) -> Team:
    """Insert or update a team by API-Football ID."""
    stmt = pg_insert(Team).values(
        api_football_id=api_id,
        name=name,
        short_name=short_name or name[:10] if name else None,
        logo_url=logo_url,
        country=country,
        venue_name=venue_name,
        venue_capacity=venue_capacity,
    ).on_conflict_do_update(
        index_elements=["api_football_id"],
        set_={
            "name": name,
            "logo_url": logo_url,
            "venue_name": venue_name,
            "venue_capacity": venue_capacity,
        },
    ).returning(Team)
    result = await session.execute(stmt)
    return result.scalar_one()


async def get_team_by_api_id(session: AsyncSession, api_id: int) -> Team | None:
    """Get a team by its API-Football ID."""
    result = await session.execute(
        select(Team).where(Team.api_football_id == api_id)
    )
    return result.scalar_one_or_none()


async def ensure_team(session: AsyncSession, api_id: int, name: str, logo_url: str | None = None) -> Team:
    """Get or create a team — lightweight version for fixture processing."""
    team = await get_team_by_api_id(session, api_id)
    if team:
        return team
    return await upsert_team(session, api_id=api_id, name=name, logo_url=logo_url)


# ── Fixture operations ────────────────────────────────────

async def upsert_fixture(session: AsyncSession, data: dict, league: League) -> Fixture | None:
    """Upsert a single fixture from API-Football response format."""
    fixture_info = data.get("fixture", {})
    teams_info = data.get("teams", {})
    goals_info = data.get("goals", {})
    score_info = data.get("score", {})

    api_id = fixture_info.get("id")
    if not api_id:
        return None

    # Ensure teams exist
    home_api_id = teams_info.get("home", {}).get("id")
    away_api_id = teams_info.get("away", {}).get("id")
    if not home_api_id or not away_api_id:
        return None

    home_team = await ensure_team(
        session, home_api_id,
        teams_info["home"].get("name", "Unknown"),
        teams_info["home"].get("logo"),
    )
    away_team = await ensure_team(
        session, away_api_id,
        teams_info["away"].get("name", "Unknown"),
        teams_info["away"].get("logo"),
    )

    # Parse status
    status_short = fixture_info.get("status", {}).get("short", "NS")
    status = API_STATUS_MAP.get(status_short, MatchStatus.SCHEDULED)

    # Parse kickoff time
    kickoff_str = fixture_info.get("date")
    kickoff = datetime.fromisoformat(kickoff_str) if kickoff_str else datetime.utcnow()

    # Parse halftime score
    ht = score_info.get("halftime", {})

    league_info = data.get("league", {})
    season = league_info.get("season", datetime.utcnow().year)
    round_name = league_info.get("round")

    stmt = pg_insert(Fixture).values(
        api_football_id=api_id,
        league_id=league.id,
        season=season,
        round=round_name,
        home_team_id=home_team.id,
        away_team_id=away_team.id,
        kickoff=kickoff,
        status=status,
        home_goals=goals_info.get("home"),
        away_goals=goals_info.get("away"),
        home_goals_ht=ht.get("home"),
        away_goals_ht=ht.get("away"),
        updated_at=datetime.utcnow(),
    ).on_conflict_do_update(
        index_elements=["api_football_id"],
        set_={
            "status": status,
            "home_goals": goals_info.get("home"),
            "away_goals": goals_info.get("away"),
            "home_goals_ht": ht.get("home"),
            "away_goals_ht": ht.get("away"),
            "round": round_name,
            "updated_at": datetime.utcnow(),
        },
    ).returning(Fixture)
    result = await session.execute(stmt)
    return result.scalar_one()


async def upsert_fixtures_batch(session: AsyncSession, fixtures_data: list[dict], league: League) -> int:
    """Upsert a batch of fixtures. Returns count of processed fixtures."""
    count = 0
    for data in fixtures_data:
        fixture = await upsert_fixture(session, data, league)
        if fixture:
            count += 1
    return count


async def get_fixtures(
    session: AsyncSession,
    match_date: date | None = None,
    league_id: int | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[Fixture]:
    """Query fixtures with optional filters."""
    query = (
        select(Fixture)
        .options(
            selectinload(Fixture.league),
            selectinload(Fixture.home_team),
            selectinload(Fixture.away_team),
        )
        .order_by(Fixture.kickoff)
        .limit(limit)
    )

    if match_date:
        start = datetime.combine(match_date, datetime.min.time())
        end = datetime.combine(match_date, datetime.max.time())
        query = query.where(Fixture.kickoff.between(start, end))

    if league_id:
        query = query.where(Fixture.league_id == league_id)

    if status:
        try:
            match_status = MatchStatus(status)
            query = query.where(Fixture.status == match_status)
        except ValueError:
            pass

    result = await session.execute(query)
    return list(result.scalars().all())


async def get_fixture_by_id(session: AsyncSession, fixture_id: int) -> Fixture | None:
    """Get a fixture with all relationships loaded."""
    result = await session.execute(
        select(Fixture)
        .where(Fixture.id == fixture_id)
        .options(
            selectinload(Fixture.league),
            selectinload(Fixture.home_team),
            selectinload(Fixture.away_team),
            selectinload(Fixture.odds),
            selectinload(Fixture.predictions),
        )
    )
    return result.scalar_one_or_none()


async def get_live_fixtures(session: AsyncSession) -> list[Fixture]:
    """Get all currently live fixtures."""
    result = await session.execute(
        select(Fixture)
        .where(Fixture.status.in_([MatchStatus.LIVE, MatchStatus.HALFTIME]))
        .options(
            selectinload(Fixture.league),
            selectinload(Fixture.home_team),
            selectinload(Fixture.away_team),
        )
        .order_by(Fixture.kickoff)
    )
    return list(result.scalars().all())


# ── Odds operations ───────────────────────────────────────

async def upsert_odds(
    session: AsyncSession,
    fixture_id: int,
    bookmaker: str,
    market: str,
    home_odds: float | None = None,
    draw_odds: float | None = None,
    away_odds: float | None = None,
    over_odds: float | None = None,
    under_odds: float | None = None,
    line: float | None = None,
) -> Odds:
    """Insert or update odds for a fixture-bookmaker combination."""
    stmt = pg_insert(Odds).values(
        fixture_id=fixture_id,
        bookmaker=bookmaker,
        market=market,
        home_odds=home_odds,
        draw_odds=draw_odds,
        away_odds=away_odds,
        over_odds=over_odds,
        under_odds=under_odds,
        line=line,
        fetched_at=datetime.utcnow(),
    ).on_conflict_do_update(
        constraint="ix_odds_fixture_bookmaker",
        set_={
            "home_odds": home_odds,
            "draw_odds": draw_odds,
            "away_odds": away_odds,
            "over_odds": over_odds,
            "under_odds": under_odds,
            "fetched_at": datetime.utcnow(),
        },
    ).returning(Odds)
    result = await session.execute(stmt)
    return result.scalar_one()


# ── Standing operations ───────────────────────────────────

async def upsert_standing(session: AsyncSession, data: dict, league: League, season: int) -> Standing | None:
    """Upsert a single standing entry from API-Football format."""
    team_data = data.get("team", {})
    team_api_id = team_data.get("id")
    if not team_api_id:
        return None

    team = await ensure_team(session, team_api_id, team_data.get("name", "Unknown"), team_data.get("logo"))

    all_info = data.get("all", {})
    goals = all_info.get("goals", {})

    stmt = pg_insert(Standing).values(
        league_id=league.id,
        season=season,
        team_id=team.id,
        position=data.get("rank", 0),
        points=data.get("points", 0),
        played=all_info.get("played", 0),
        won=all_info.get("win", 0),
        drawn=all_info.get("draw", 0),
        lost=all_info.get("lose", 0),
        goals_for=goals.get("for", 0),
        goals_against=goals.get("against", 0),
        goal_diff=data.get("goalsDiff", 0),
        form=data.get("form"),
        updated_at=datetime.utcnow(),
    ).on_conflict_do_update(
        constraint="uq_standing",
        set_={
            "position": data.get("rank", 0),
            "points": data.get("points", 0),
            "played": all_info.get("played", 0),
            "won": all_info.get("win", 0),
            "drawn": all_info.get("draw", 0),
            "lost": all_info.get("lose", 0),
            "goals_for": goals.get("for", 0),
            "goals_against": goals.get("against", 0),
            "goal_diff": data.get("goalsDiff", 0),
            "form": data.get("form"),
            "updated_at": datetime.utcnow(),
        },
    ).returning(Standing)
    result = await session.execute(stmt)
    return result.scalar_one()


async def get_standings(session: AsyncSession, league_id: int, season: int | None = None) -> list[Standing]:
    """Get standings for a league, optionally by season."""
    query = (
        select(Standing)
        .where(Standing.league_id == league_id)
        .options(selectinload(Standing.league))
        .order_by(Standing.position)
    )
    if season:
        query = query.where(Standing.season == season)
    else:
        # Get the latest season
        sub = select(func.max(Standing.season)).where(Standing.league_id == league_id)
        query = query.where(Standing.season == sub.scalar_subquery())

    result = await session.execute(query)
    return list(result.scalars().all())


# ── Prediction operations ─────────────────────────────────

async def get_predictions_for_date(session: AsyncSession, target_date: date) -> list[Prediction]:
    """Get predictions for fixtures on a specific date."""
    start = datetime.combine(target_date, datetime.min.time())
    end = datetime.combine(target_date, datetime.max.time())
    result = await session.execute(
        select(Prediction)
        .join(Fixture)
        .where(Fixture.kickoff.between(start, end))
        .options(selectinload(Prediction.fixture))
    )
    return list(result.scalars().all())


async def get_prediction_by_fixture(session: AsyncSession, fixture_id: int) -> Prediction | None:
    """Get prediction for a specific fixture."""
    result = await session.execute(
        select(Prediction).where(Prediction.fixture_id == fixture_id)
    )
    return result.scalar_one_or_none()


# ── Sentiment operations ──────────────────────────────────

async def get_team_sentiment(session: AsyncSession, team_id: int, days: int = 7) -> list[SentimentScore]:
    """Get sentiment scores for a team over the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    result = await session.execute(
        select(SentimentScore)
        .where(and_(SentimentScore.team_id == team_id, SentimentScore.analyzed_at >= cutoff))
        .order_by(SentimentScore.analyzed_at.desc())
    )
    return list(result.scalars().all())


# ── H2H operations ────────────────────────────────────────

async def get_h2h_fixtures(session: AsyncSession, team1_id: int, team2_id: int, last: int = 10) -> list[Fixture]:
    """Get head-to-head fixtures between two teams."""
    result = await session.execute(
        select(Fixture)
        .where(
            or_(
                and_(Fixture.home_team_id == team1_id, Fixture.away_team_id == team2_id),
                and_(Fixture.home_team_id == team2_id, Fixture.away_team_id == team1_id),
            ),
            Fixture.status == MatchStatus.FINISHED,
        )
        .options(
            selectinload(Fixture.league),
            selectinload(Fixture.home_team),
            selectinload(Fixture.away_team),
        )
        .order_by(Fixture.kickoff.desc())
        .limit(last)
    )
    return list(result.scalars().all())
