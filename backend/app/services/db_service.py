"""Database service layer — all DB read/write operations for ScoreLock.

Centralizes upsert and query logic so Celery tasks and API routes
share the same data access patterns.
"""

from datetime import date, datetime, timedelta
from sqlalchemy import select, func, and_, or_, Integer
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import structlog

from app.core.database import async_session
from app.models.models import (
    League, Team, Fixture, Odds, Prediction,
    SentimentScore, Standing, MatchStatus,
    Article, ArticleType,
    AffiliateLink, AffiliateClick,
    UserPrediction,
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

    # Parse kickoff time (strip tzinfo — DB uses TIMESTAMP WITHOUT TIME ZONE)
    kickoff_str = fixture_info.get("date")
    kickoff = datetime.fromisoformat(kickoff_str).replace(tzinfo=None) if kickoff_str else datetime.utcnow()

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
    limit: int = 100,
) -> list[Fixture]:
    """Query fixtures with optional filters."""
    query = (
        select(Fixture)
        .options(
            selectinload(Fixture.league),
            selectinload(Fixture.home_team),
            selectinload(Fixture.away_team),
        )
        .order_by(Fixture.kickoff.desc())
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


# ── ML Training Data ──────────────────────────────────────

async def get_finished_fixtures_for_training(session: AsyncSession) -> list[dict]:
    """Get all finished fixtures with scores for model training."""
    result = await session.execute(
        select(Fixture)
        .where(
            Fixture.status == MatchStatus.FINISHED,
            Fixture.home_goals.is_not(None),
            Fixture.away_goals.is_not(None),
        )
        .order_by(Fixture.kickoff)
    )
    fixtures = list(result.scalars().all())

    return [
        {
            "fixture_id": f.id,
            "home_team_id": f.home_team_id,
            "away_team_id": f.away_team_id,
            "home_goals": f.home_goals,
            "away_goals": f.away_goals,
            "kickoff": f.kickoff,
            "season": f.season,
            "league_id": f.league_id,
        }
        for f in fixtures
    ]


async def get_upcoming_fixtures_for_prediction(
    session: AsyncSession,
    days_ahead: int = 2,
) -> list[Fixture]:
    """Get scheduled fixtures in the next N days that don't have predictions."""
    now = datetime.utcnow()
    cutoff = now + timedelta(days=days_ahead)

    # Subquery: does fixture already have a prediction?
    has_pred = (
        select(Prediction.id)
        .where(Prediction.fixture_id == Fixture.id)
        .exists()
    )

    result = await session.execute(
        select(Fixture)
        .where(
            Fixture.status == MatchStatus.SCHEDULED,
            Fixture.kickoff >= now,
            Fixture.kickoff <= cutoff,
            ~has_pred,
        )
        .options(
            selectinload(Fixture.league),
            selectinload(Fixture.home_team),
            selectinload(Fixture.away_team),
            selectinload(Fixture.odds),
        )
        .order_by(Fixture.kickoff)
    )
    return list(result.scalars().all())


async def upsert_prediction(
    session: AsyncSession,
    fixture_id: int,
    home_win_prob: float,
    draw_prob: float,
    away_win_prob: float,
    confidence: float,
    model_version: str,
    over_25_prob: float | None = None,
    expected_goals: float | None = None,
    is_value_home: bool = False,
    is_value_draw: bool = False,
    is_value_away: bool = False,
    value_edge: float | None = None,
    features_used: dict | None = None,
) -> Prediction:
    """Insert or update a prediction for a fixture."""
    # Check if prediction exists (avoids needing unique constraint migration)
    existing = await session.execute(
        select(Prediction).where(Prediction.fixture_id == fixture_id)
    )
    pred = existing.scalar_one_or_none()

    if pred:
        pred.home_win_prob = home_win_prob
        pred.draw_prob = draw_prob
        pred.away_win_prob = away_win_prob
        pred.confidence = confidence
        pred.over_25_prob = over_25_prob
        pred.expected_goals = expected_goals
        pred.model_version = model_version
        pred.is_value_home = is_value_home
        pred.is_value_draw = is_value_draw
        pred.is_value_away = is_value_away
        pred.value_edge = value_edge
        pred.features_used = features_used
        pred.created_at = datetime.utcnow()
    else:
        pred = Prediction(
            fixture_id=fixture_id,
            home_win_prob=home_win_prob,
            draw_prob=draw_prob,
            away_win_prob=away_win_prob,
            confidence=confidence,
            over_25_prob=over_25_prob,
            expected_goals=expected_goals,
            model_version=model_version,
            is_value_home=is_value_home,
            is_value_draw=is_value_draw,
            is_value_away=is_value_away,
            value_edge=value_edge,
            features_used=features_used,
        )
        session.add(pred)

    return pred


async def update_prediction_results(session: AsyncSession) -> int:
    """Mark predictions as correct/incorrect after matches finish.

    Returns count of predictions updated.
    """
    result = await session.execute(
        select(Prediction)
        .join(Fixture)
        .where(
            Fixture.status == MatchStatus.FINISHED,
            Prediction.was_correct.is_(None),
            Fixture.home_goals.is_not(None),
        )
        .options(selectinload(Prediction.fixture))
    )
    predictions = list(result.scalars().all())

    count = 0
    for pred in predictions:
        fixture = pred.fixture
        if fixture.home_goals is None or fixture.away_goals is None:
            continue

        # Actual result
        if fixture.home_goals > fixture.away_goals:
            actual = "H"
        elif fixture.home_goals == fixture.away_goals:
            actual = "D"
        else:
            actual = "A"

        # Predicted result (highest probability)
        probs = {"H": pred.home_win_prob, "D": pred.draw_prob, "A": pred.away_win_prob}
        predicted = max(probs, key=probs.get)

        pred.actual_result = actual
        pred.was_correct = predicted == actual
        count += 1

    return count


# ── Article operations ─────────────────────────────────────

async def get_articles(
    session: AsyncSession,
    article_type: ArticleType | None = None,
    league_id: int | None = None,
    language: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Article]:
    """Get published articles with optional filters, newest first."""
    q = select(Article).where(Article.published_at.is_not(None)).order_by(Article.published_at.desc())
    if article_type:
        q = q.where(Article.type == article_type)
    if league_id:
        q = q.where(Article.league_id == league_id)
    if language:
        q = q.where(Article.language == language)
    q = q.offset(offset).limit(limit)
    result = await session.execute(q)
    return list(result.scalars().all())


async def get_article_by_slug(session: AsyncSession, slug: str) -> Article | None:
    """Get a single article by its unique slug."""
    result = await session.execute(select(Article).where(Article.slug == slug))
    return result.scalar_one_or_none()


async def count_articles(
    session: AsyncSession,
    article_type: ArticleType | None = None,
    league_id: int | None = None,
) -> int:
    """Count articles with optional filters."""
    q = select(func.count(Article.id)).where(Article.published_at.is_not(None))
    if article_type:
        q = q.where(Article.type == article_type)
    if league_id:
        q = q.where(Article.league_id == league_id)
    result = await session.execute(q)
    return result.scalar_one()


# ── Affiliate operations ──────────────────────────────────

async def get_affiliate_links(
    session: AsyncSession,
    country: str = "SE",
    bookmaker: str | None = None,
) -> list[AffiliateLink]:
    """Get active affiliate links, ordered by priority (highest first)."""
    q = (
        select(AffiliateLink)
        .where(AffiliateLink.is_active.is_(True))
        .where(AffiliateLink.country == country)
        .order_by(AffiliateLink.priority.desc())
    )
    if bookmaker:
        q = q.where(AffiliateLink.bookmaker == bookmaker.lower())
    result = await session.execute(q)
    return list(result.scalars().all())


async def record_affiliate_click(
    session: AsyncSession,
    link_id: int,
    fixture_id: int | None = None,
    user_id: int | None = None,
    page_source: str | None = None,
    ip_hash: str | None = None,
    user_agent: str | None = None,
) -> AffiliateClick:
    """Record an affiliate link click."""
    click = AffiliateClick(
        link_id=link_id,
        fixture_id=fixture_id,
        user_id=user_id,
        page_source=page_source,
        ip_hash=ip_hash,
        user_agent=user_agent,
    )
    session.add(click)
    await session.flush()
    return click


async def get_affiliate_stats(
    session: AsyncSession,
) -> list[dict]:
    """Get aggregate click stats per bookmaker."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    links = await get_affiliate_links(session)
    stats = []

    for link in links:
        total_q = select(func.count(AffiliateClick.id)).where(AffiliateClick.link_id == link.id)
        today_q = total_q.where(AffiliateClick.clicked_at >= today_start)
        week_q = total_q.where(AffiliateClick.clicked_at >= week_start)
        month_q = total_q.where(AffiliateClick.clicked_at >= month_start)

        total = (await session.execute(total_q)).scalar_one()
        today = (await session.execute(today_q)).scalar_one()
        week = (await session.execute(week_q)).scalar_one()
        month = (await session.execute(month_q)).scalar_one()

        stats.append({
            "bookmaker": link.bookmaker,
            "bookmaker_display": link.bookmaker_display,
            "total_clicks": total,
            "clicks_today": today,
            "clicks_this_week": week,
            "clicks_this_month": month,
        })

    return stats


# ── Tipping League ─────────────────────────────────────────

async def create_user_prediction(
    session: AsyncSession,
    user_id: int,
    fixture_id: int,
    predicted_outcome: str,
    predicted_home_goals: int | None = None,
    predicted_away_goals: int | None = None,
) -> UserPrediction:
    """Create or update a user's prediction for a fixture."""
    # Check fixture exists and is still scheduled
    fixture = await session.get(Fixture, fixture_id)
    if not fixture:
        raise ValueError("Fixture not found")
    if fixture.status != MatchStatus.SCHEDULED:
        raise ValueError("Match has already started or finished")
    if fixture.kickoff <= datetime.utcnow():
        raise ValueError("Match has already kicked off")

    # Check existing prediction
    result = await session.execute(
        select(UserPrediction).where(
            UserPrediction.user_id == user_id,
            UserPrediction.fixture_id == fixture_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.predicted_outcome = predicted_outcome
        existing.predicted_home_goals = predicted_home_goals
        existing.predicted_away_goals = predicted_away_goals
        await session.flush()
        return existing

    prediction = UserPrediction(
        user_id=user_id,
        fixture_id=fixture_id,
        predicted_outcome=predicted_outcome,
        predicted_home_goals=predicted_home_goals,
        predicted_away_goals=predicted_away_goals,
    )
    session.add(prediction)
    await session.flush()
    return prediction


async def get_user_predictions(
    session: AsyncSession,
    user_id: int,
    scored_only: bool = False,
    limit: int = 50,
) -> list[UserPrediction]:
    """Get a user's predictions, optionally only scored ones."""
    q = (
        select(UserPrediction)
        .where(UserPrediction.user_id == user_id)
        .options(selectinload(UserPrediction.fixture).selectinload(Fixture.home_team))
        .options(selectinload(UserPrediction.fixture).selectinload(Fixture.away_team))
        .options(selectinload(UserPrediction.fixture).selectinload(Fixture.league))
        .order_by(UserPrediction.created_at.desc())
        .limit(limit)
    )
    if scored_only:
        q = q.where(UserPrediction.points_earned.isnot(None))
    result = await session.execute(q)
    return list(result.scalars().all())


async def score_user_predictions(session: AsyncSession, fixture_id: int) -> int:
    """Score all user predictions for a completed fixture. Returns count scored."""
    fixture = await session.get(Fixture, fixture_id)
    if not fixture or fixture.status != MatchStatus.FINISHED:
        return 0
    if fixture.home_goals is None or fixture.away_goals is None:
        return 0

    # Determine actual outcome
    if fixture.home_goals > fixture.away_goals:
        actual_outcome = "H"
    elif fixture.home_goals < fixture.away_goals:
        actual_outcome = "A"
    else:
        actual_outcome = "D"

    # Get unscored predictions for this fixture
    result = await session.execute(
        select(UserPrediction).where(
            UserPrediction.fixture_id == fixture_id,
            UserPrediction.points_earned.is_(None),
        )
    )
    predictions = list(result.scalars().all())

    scored_count = 0
    for pred in predictions:
        correct_outcome = pred.predicted_outcome == actual_outcome
        exact_score = (
            pred.predicted_home_goals is not None
            and pred.predicted_away_goals is not None
            and pred.predicted_home_goals == fixture.home_goals
            and pred.predicted_away_goals == fixture.away_goals
        )

        if exact_score:
            points = 3
        elif correct_outcome:
            points = 1
        else:
            points = 0

        pred.points_earned = points
        pred.was_correct_outcome = correct_outcome
        pred.was_exact_score = exact_score
        pred.scored_at = datetime.utcnow()
        scored_count += 1

    await session.flush()
    return scored_count


async def get_leaderboard(
    session: AsyncSession,
    limit: int = 50,
    days: int | None = None,
) -> list[dict]:
    """Get tipping league leaderboard. Optionally filter by last N days."""
    from app.models.models import User as UserModel

    q = (
        select(
            UserPrediction.user_id,
            UserModel.name,
            func.sum(UserPrediction.points_earned).label("total_points"),
            func.count(UserPrediction.id).label("total_tips"),
            func.sum(
                func.cast(UserPrediction.was_correct_outcome, Integer)
            ).label("correct_outcomes"),
            func.sum(
                func.cast(UserPrediction.was_exact_score, Integer)
            ).label("exact_scores"),
        )
        .join(UserModel, UserPrediction.user_id == UserModel.id)
        .where(UserPrediction.points_earned.isnot(None))
    )

    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        q = q.where(UserPrediction.scored_at >= cutoff)

    q = (
        q.group_by(UserPrediction.user_id, UserModel.name)
        .order_by(func.sum(UserPrediction.points_earned).desc())
        .limit(limit)
    )

    result = await session.execute(q)
    rows = result.all()

    leaderboard = []
    for row in rows:
        total_tips = row.total_tips or 0
        correct = row.correct_outcomes or 0
        accuracy = (correct / total_tips * 100) if total_tips > 0 else 0.0

        leaderboard.append({
            "user_id": row.user_id,
            "user_name": row.name,
            "total_points": row.total_points or 0,
            "total_tips": total_tips,
            "correct_outcomes": correct,
            "exact_scores": row.exact_scores or 0,
            "accuracy": round(accuracy, 1),
            "current_streak": 0,  # Calculated separately if needed
        })

    return leaderboard


async def get_ai_vs_user(session: AsyncSession, user_id: int) -> dict:
    """Compare user's tipping performance vs the AI model."""
    from app.models.models import User as UserModel

    # Get user's scored predictions
    user_preds = await get_user_predictions(session, user_id, scored_only=True, limit=500)

    user_total = len(user_preds)
    user_points = sum(p.points_earned or 0 for p in user_preds)
    user_correct = sum(1 for p in user_preds if p.was_correct_outcome)

    # Get AI predictions for the same fixtures
    fixture_ids = [p.fixture_id for p in user_preds]
    if fixture_ids:
        ai_result = await session.execute(
            select(Prediction)
            .where(Prediction.fixture_id.in_(fixture_ids))
            .where(Prediction.was_correct.isnot(None))
        )
        ai_preds = list(ai_result.scalars().all())
        ai_correct = sum(1 for p in ai_preds if p.was_correct)
        ai_total = len(ai_preds)
    else:
        ai_correct = 0
        ai_total = 0

    # Compare per fixture
    user_wins = 0
    ai_wins = 0
    ties = 0
    ai_fixture_map = {p.fixture_id: p.was_correct for p in ai_preds} if fixture_ids else {}

    for pred in user_preds:
        ai_was_correct = ai_fixture_map.get(pred.fixture_id)
        if ai_was_correct is None:
            continue
        if pred.was_correct_outcome and not ai_was_correct:
            user_wins += 1
        elif not pred.was_correct_outcome and ai_was_correct:
            ai_wins += 1
        else:
            ties += 1

    return {
        "user_total_points": user_points,
        "user_total_tips": user_total,
        "user_accuracy": round((user_correct / user_total * 100) if user_total > 0 else 0, 1),
        "ai_correct": ai_correct,
        "ai_total": ai_total,
        "ai_accuracy": round((ai_correct / ai_total * 100) if ai_total > 0 else 0, 1),
        "user_wins": user_wins,
        "ai_wins": ai_wins,
        "ties": ties,
    }


async def get_weekly_top_tipper(session: AsyncSession) -> dict | None:
    """Get the top tipper for the current week."""
    from app.models.models import User as UserModel

    week_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_start -= timedelta(days=week_start.weekday())

    q = (
        select(
            UserPrediction.user_id,
            UserModel.name,
            func.sum(UserPrediction.points_earned).label("points"),
            func.count(UserPrediction.id).label("tips"),
            func.sum(
                func.cast(UserPrediction.was_correct_outcome, Integer)
            ).label("correct"),
        )
        .join(UserModel, UserPrediction.user_id == UserModel.id)
        .where(
            UserPrediction.points_earned.isnot(None),
            UserPrediction.scored_at >= week_start,
        )
        .group_by(UserPrediction.user_id, UserModel.name)
        .order_by(func.sum(UserPrediction.points_earned).desc())
        .limit(1)
    )

    result = await session.execute(q)
    row = result.first()

    if not row:
        return None

    tips = row.tips or 0
    correct = row.correct or 0
    return {
        "user_id": row.user_id,
        "user_name": row.name,
        "points_this_week": row.points or 0,
        "tips_this_week": tips,
        "accuracy_this_week": round((correct / tips * 100) if tips > 0 else 0, 1),
    }
