"""API routes for ScoreLock football analytics.

All routes query the database via the db_service layer.
"""

import asyncio
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.security import get_current_user, get_optional_user
from app.schemas.schemas import (
    FixtureResponse,
    FixtureDetail,
    PredictionResponse,
    ValueBetResponse,
    StandingResponse,
    LeagueResponse,
    SentimentResponse,
    TeamResponse,
    OddsResponse,
    ArticleResponse,
    ArticleListResponse,
    AffiliateLinkResponse,
    AffiliateClickCreate,
    AffiliateClickResponse,
    AffiliateStatsResponse,
    UserPredictionCreate,
    UserPredictionResponse,
    UserPredictionWithFixture,
    LeaderboardEntry,
    AIvsUserStats,
    WeeklyTopTipper,
    BroadcastResponse,
    FixtureEventResponse,
    FixtureStatisticsResponse,
    FixtureStatisticsBundle,
    LineupPlayerResponse,
    LineupResponse,
    FixtureLineupsBundle,
    MatchIntelligenceResponse,
    MatchIntelligenceBundle,
    FixtureDetailBundle,
    VenueResponse,
    RefereeResponse,
    MatchInfoResponse,
    OddsSnapshotResponse,
    OddsSnapshotsBundle,
    ValueBetLedgerEntry,
    ValueBetLedgerResponse,
    CommentaryEntryResponse,
    CommentaryFeedResponse,
    MomentumPointResponse,
    MomentumSeriesResponse,
    MOTMVoteRequest,
    MOTMTallyEntry,
    MOTMTallyResponse,
    TournamentGroupStanding,
    TournamentGroup,
    TournamentKnockoutStage,
    TournamentStructureResponse,
)
from app.services import db_service
from app.models.models import (
    User,
    ArticleType,
    Bookmaker,
    FixtureBroadcast,
    FixtureCommentary,
    FixtureEvent,
    FixtureMatchInfo,
    FixtureMomentum,
    FixtureStatistics,
    FixtureLineup,
    FixtureLineupPlayer,
    Fixture,
    IntelligenceKind,
    League,
    MatchIntelligence,
    OddsSnapshot,
    Player,
    Prediction,
    Referee,
    Team,
    UserMOTMVote,
    Venue,
)
from sqlalchemy.orm import aliased

router = APIRouter()


# ── Health ─────────────────────────────────────────────────


@router.get("/health")
async def health_check():
    """Service health check — validates DB + Redis connectivity.

    Does NOT use the get_db dependency so the endpoint always
    returns 200 even when the database is completely unreachable.
    Railway / k8s healthchecks need a response; downstream checks
    are reported as "ok" or "error" in the JSON body.
    """
    import redis as redis_lib
    from app.core.config import get_settings
    from app.core.database import async_session

    checks: dict = {"status": "ok", "service": "scorelock-api", "version": "0.1.0"}

    # DB check — short timeout so healthcheck never hangs
    try:
        async with asyncio.timeout(3):
            async with async_session() as session:
                await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
        checks["status"] = "degraded"

    # Redis check
    try:
        settings = get_settings()
        r = redis_lib.from_url(settings.redis_url, socket_timeout=2)
        r.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"
        checks["status"] = "degraded"

    return checks


# ── Leagues ────────────────────────────────────────────────


@router.get("/leagues", response_model=list[LeagueResponse])
async def get_leagues(db: AsyncSession = Depends(get_db)):
    """Get all active leagues covered by ScoreLock."""
    leagues = await db_service.get_all_leagues(db)
    return leagues


# ── Fixtures ───────────────────────────────────────────────


@router.get("/fixtures", response_model=list[FixtureResponse])
async def get_fixtures(
    match_date: date | None = Query(
        None, alias="date", description="Filter by date (YYYY-MM-DD)"
    ),
    league_id: int | None = Query(None, description="Filter by league"),
    status: str | None = Query(None, description="Filter by status"),
    date_from: date | None = Query(None, description="Inkl. fr.o.m. (YYYY-MM-DD)"),
    date_to: date | None = Query(None, description="Inkl. t.o.m. (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=500, description="Max antal rader"),
    db: AsyncSession = Depends(get_db),
):
    """Get fixtures with optional filters.

    Smart default: om INGET datumfilter ges (match_date/date_from/date_to),
    defaultar vi date_from=today så konsumentlistor visar kommande matcher
    i stället för historiska. ASC-sort + this default = framsidan ser VM-
    matcherna istället för 2023-säsongens spegelbild.
    """
    if match_date is None and date_from is None and date_to is None:
        from datetime import date as _date
        date_from = _date.today()

    fixtures = await db_service.get_fixtures(
        db,
        match_date=match_date,
        league_id=league_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    return fixtures


@router.get("/fixtures/live", response_model=list[FixtureResponse])
async def get_live_fixtures(db: AsyncSession = Depends(get_db)):
    """Get currently live fixtures."""
    fixtures = await db_service.get_live_fixtures(db)
    return fixtures


@router.get("/fixtures/{fixture_id}", response_model=FixtureDetail)
async def get_fixture_detail(fixture_id: int, db: AsyncSession = Depends(get_db)):
    """Get full fixture detail including prediction, odds, and stats."""
    fixture = await db_service.get_fixture_by_id(db, fixture_id)
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    # Build the detail response
    prediction = fixture.predictions[0] if fixture.predictions else None

    return FixtureDetail(
        id=fixture.id,
        league=LeagueResponse.model_validate(fixture.league),
        home_team=TeamResponse.model_validate(fixture.home_team),
        away_team=TeamResponse.model_validate(fixture.away_team),
        kickoff=fixture.kickoff,
        status=fixture.status.value,
        home_goals=fixture.home_goals,
        away_goals=fixture.away_goals,
        round=fixture.round,
        home_goals_ht=fixture.home_goals_ht,
        away_goals_ht=fixture.away_goals_ht,
        stats=fixture.stats,
        prediction=PredictionResponse.model_validate(prediction)
        if prediction
        else None,
        odds=[OddsResponse.model_validate(o) for o in fixture.odds],
    )


@router.get("/fixtures/{fixture_id}/detail", response_model=FixtureDetailBundle)
async def get_fixture_detail_bundle(
    fixture_id: int, db: AsyncSession = Depends(get_db)
):
    """Bundlad match-detalj — allt sidan behöver i ETT svar.

    Ersätter ~15 separata fan-out-anrop (en HTTP-runda i stället för 15 → bort med
    rate-limit-trycket + skörheten). Sub-resurserna hämtas in-process i samma session;
    saknade delar degraderar till tomma defaults precis som de enskilda endpointsen.
    get_fixture_detail 404:ar om matchen inte finns.
    """
    fixture = await get_fixture_detail(fixture_id, db)

    articles_resp = await list_articles(
        article_type=None, league_id=None, language=None, limit=5, offset=0, db=db
    )
    home_name = fixture.home_team.name
    away_name = fixture.away_team.name
    articles = [
        a
        for a in articles_resp.articles
        if a.fixture_id == fixture.id
        or (a.tags and (home_name in a.tags or away_name in a.tags))
    ][:3]

    return FixtureDetailBundle(
        fixture=fixture,
        match_info=await get_fixture_match_info(fixture_id, db),
        broadcasts=await get_fixture_broadcasts(fixture_id, "SE", db),
        events=await get_fixture_events(fixture_id, db),
        statistics=await get_fixture_statistics(fixture_id, db),
        lineups=await get_fixture_lineups(fixture_id, db),
        odds_snapshots=await get_fixture_odds_snapshots(fixture_id, "h2h", 240, db),
        commentary=await get_fixture_commentary(fixture_id, db),
        momentum=await get_fixture_momentum(fixture_id, db),
        motm=await get_motm_tally(fixture_id, None, db),
        intelligence=await get_fixture_intelligence(fixture_id, "sv", db),
        articles=articles,
        home_sentiment=await get_team_sentiment(fixture.home_team.id, days=7, db=db),
        away_sentiment=await get_team_sentiment(fixture.away_team.id, days=7, db=db),
        affiliate_links=await get_affiliate_links(country="SE", bookmaker=None, db=db),
    )


@router.get(
    "/fixtures/{fixture_id}/broadcasts",
    response_model=list[BroadcastResponse],
)
async def get_fixture_broadcasts(
    fixture_id: int,
    country: str = "SE",
    db: AsyncSession = Depends(get_db),
):
    """Return TV / streaming broadcasts for a fixture in the given country."""
    result = await db.execute(
        select(FixtureBroadcast)
        .where(FixtureBroadcast.fixture_id == fixture_id)
        .where(FixtureBroadcast.country_iso_2 == country.upper())
        .order_by(FixtureBroadcast.provider_type, FixtureBroadcast.channel_name)
    )
    return result.scalars().all()


@router.get(
    "/fixtures/{fixture_id}/statistics",
    response_model=FixtureStatisticsBundle,
)
async def get_fixture_statistics(
    fixture_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return per-team final-state statistics for a fixture (home + away)."""
    fx_row = (
        await db.execute(
            select(Fixture.home_team_id, Fixture.away_team_id).where(
                Fixture.id == fixture_id
            )
        )
    ).first()
    if fx_row is None:
        raise HTTPException(status_code=404, detail="Fixture not found")
    home_team_id, away_team_id = fx_row
    rows = (
        (
            await db.execute(
                select(FixtureStatistics).where(
                    FixtureStatistics.fixture_id == fixture_id
                )
            )
        )
        .scalars()
        .all()
    )
    by_team = {r.team_id: r for r in rows}
    return FixtureStatisticsBundle(
        home=(
            FixtureStatisticsResponse.model_validate(by_team[home_team_id])
            if home_team_id in by_team
            else None
        ),
        away=(
            FixtureStatisticsResponse.model_validate(by_team[away_team_id])
            if away_team_id in by_team
            else None
        ),
    )


@router.get(
    "/fixtures/{fixture_id}/odds/snapshots",
    response_model=OddsSnapshotsBundle,
)
async def get_fixture_odds_snapshots(
    fixture_id: int,
    market: str = Query("h2h", description="Market code (h2h, totals, btts)"),
    since_hours: int = Query(48, ge=1, le=720, description="Lookback window"),
    db: AsyncSession = Depends(get_db),
):
    """Return chronological odds snapshots for a fixture+market for sparkline rendering."""
    cutoff = datetime.utcnow() - __import__("datetime").timedelta(hours=since_hours)
    rows = (
        await db.execute(
            select(
                OddsSnapshot.id,
                OddsSnapshot.market_code,
                OddsSnapshot.taken_at,
                OddsSnapshot.is_in_play,
                OddsSnapshot.is_suspended,
                OddsSnapshot.market_line,
                OddsSnapshot.outcomes,
                Bookmaker.code.label("bookmaker_code"),
                Bookmaker.display_name.label("bookmaker_display"),
            )
            .join(Bookmaker, Bookmaker.id == OddsSnapshot.bookmaker_id)
            .where(OddsSnapshot.fixture_id == fixture_id)
            .where(OddsSnapshot.market_code == market.lower())
            .where(OddsSnapshot.taken_at >= cutoff)
            .order_by(OddsSnapshot.taken_at)
        )
    ).all()
    return OddsSnapshotsBundle(
        fixture_id=fixture_id,
        market_code=market.lower(),
        snapshots=[
            OddsSnapshotResponse(
                id=row.id,
                bookmaker_code=row.bookmaker_code,
                bookmaker_display=row.bookmaker_display,
                market_code=row.market_code,
                taken_at=row.taken_at,
                is_in_play=row.is_in_play,
                is_suspended=row.is_suspended,
                market_line=row.market_line,
                outcomes=row.outcomes,
            )
            for row in rows
        ],
    )


@router.get(
    "/value-bets/ledger",
    response_model=ValueBetLedgerResponse,
)
async def get_value_bet_ledger(
    status: str = Query(
        "all",
        description="Filter: all, win, loss, pending",
    ),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Return all value-bet-flagged predictions with outcomes (USP #3: transparent ledger)."""
    base = (
        select(
            Prediction.id.label("prediction_id"),
            Prediction.fixture_id,
            Prediction.home_win_prob,
            Prediction.draw_prob,
            Prediction.away_win_prob,
            Prediction.is_value_home,
            Prediction.is_value_draw,
            Prediction.is_value_away,
            Prediction.value_edge,
            Prediction.actual_result,
            Prediction.was_correct,
            Prediction.model_version,
            Prediction.created_at,
            Fixture.kickoff,
            Fixture.status.label("fixture_status"),
            Team.name.label("home_team_name"),
            League.name.label("league_name"),
        )
        .select_from(Prediction)
        .join(Fixture, Fixture.id == Prediction.fixture_id)
        .outerjoin(Team, Team.id == Fixture.home_team_id)
        .outerjoin(League, League.id == Fixture.league_id)
        .where(
            (Prediction.is_value_home.is_(True))
            | (Prediction.is_value_draw.is_(True))
            | (Prediction.is_value_away.is_(True))
        )
        .order_by(Prediction.created_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(base)).all()

    away_team_query = (
        await db.execute(
            select(Fixture.id, Team.name)
            .join(Team, Team.id == Fixture.away_team_id)
            .where(Fixture.id.in_([r.fixture_id for r in rows]) if rows else False)
        )
    ).all()
    away_by_fixture = {r.id: r.name for r in away_team_query}

    entries: list[ValueBetLedgerEntry] = []
    win = loss = pending = 0
    edges: list[float] = []

    for row in rows:
        if row.is_value_home:
            suggested = "Home"
            model_prob = row.home_win_prob
        elif row.is_value_draw:
            suggested = "Draw"
            model_prob = row.draw_prob
        else:
            suggested = "Away"
            model_prob = row.away_win_prob

        if row.was_correct is True:
            entry_status = "win"
            win += 1
        elif row.was_correct is False:
            entry_status = "loss"
            loss += 1
        else:
            entry_status = "pending"
            pending += 1

        if row.value_edge is not None:
            edges.append(float(row.value_edge))

        entries.append(
            ValueBetLedgerEntry(
                prediction_id=row.prediction_id,
                fixture_id=row.fixture_id,
                home_team_name=row.home_team_name or "?",
                away_team_name=away_by_fixture.get(row.fixture_id, "?"),
                league_name=row.league_name,
                kickoff=row.kickoff,
                market="1X2",
                suggested_bet=suggested,
                model_probability=float(model_prob),
                best_odds=None,
                best_bookmaker=None,
                edge_percent=float(row.value_edge) if row.value_edge else None,
                status=entry_status,
                actual_result=row.actual_result,
                was_correct=row.was_correct,
                model_version=row.model_version,
                created_at=row.created_at,
            )
        )

    if status != "all":
        entries = [e for e in entries if e.status == status]

    total = win + loss + pending
    settled = win + loss
    win_rate = (win / settled * 100) if settled > 0 else 0.0
    avg_edge = (sum(edges) / len(edges)) if edges else None

    return ValueBetLedgerResponse(
        total=total,
        win_count=win,
        loss_count=loss,
        pending_count=pending,
        win_rate_percent=round(win_rate, 2),
        avg_edge_percent=round(avg_edge, 2) if avg_edge is not None else None,
        entries=entries,
    )


@router.get(
    "/fixtures/{fixture_id}/match-info",
    response_model=MatchInfoResponse,
)
async def get_fixture_match_info(
    fixture_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return venue + referee for a fixture (or nulls if no mapping seeded)."""
    row = (
        await db.execute(
            select(FixtureMatchInfo).where(FixtureMatchInfo.fixture_id == fixture_id)
        )
    ).scalar_one_or_none()
    if row is None:
        return MatchInfoResponse(venue=None, referee=None)

    venue = (
        (
            await db.execute(select(Venue).where(Venue.id == row.venue_id))
        ).scalar_one_or_none()
        if row.venue_id
        else None
    )
    referee = (
        (
            await db.execute(select(Referee).where(Referee.id == row.referee_id))
        ).scalar_one_or_none()
        if row.referee_id
        else None
    )

    return MatchInfoResponse(
        venue=VenueResponse.model_validate(venue) if venue else None,
        referee=RefereeResponse.model_validate(referee) if referee else None,
    )


@router.get(
    "/fixtures/{fixture_id}/commentary",
    response_model=CommentaryFeedResponse,
)
async def get_fixture_commentary(
    fixture_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return chronological commentary feed for a fixture."""
    rows = (
        (
            await db.execute(
                select(FixtureCommentary)
                .where(FixtureCommentary.fixture_id == fixture_id)
                .order_by(FixtureCommentary.minute, FixtureCommentary.stoppage)
            )
        )
        .scalars()
        .all()
    )
    return CommentaryFeedResponse(
        fixture_id=fixture_id,
        entries=[CommentaryEntryResponse.model_validate(r) for r in rows],
    )


@router.get(
    "/fixtures/{fixture_id}/momentum",
    response_model=MomentumSeriesResponse,
)
async def get_fixture_momentum(
    fixture_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return momentum time-series (home/away pressure %) for a fixture."""
    rows = (
        (
            await db.execute(
                select(FixtureMomentum)
                .where(FixtureMomentum.fixture_id == fixture_id)
                .order_by(FixtureMomentum.match_minute, FixtureMomentum.match_stoppage)
            )
        )
        .scalars()
        .all()
    )
    return MomentumSeriesResponse(
        fixture_id=fixture_id,
        points=[MomentumPointResponse.model_validate(r) for r in rows],
    )


@router.get(
    "/fixtures/{fixture_id}/motm-tally",
    response_model=MOTMTallyResponse,
)
async def get_motm_tally(
    fixture_id: int,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Return Man of the Match vote tally + the current user's vote (if any)."""
    from sqlalchemy import func

    rows = (
        await db.execute(
            select(
                UserMOTMVote.voted_player_id,
                Player.display_name,
                Team.name.label("team_name"),
                func.count(UserMOTMVote.id).label("vote_count"),
            )
            .join(Player, Player.id == UserMOTMVote.voted_player_id)
            .outerjoin(Team, Team.id == Player.current_team_id)
            .where(UserMOTMVote.fixture_id == fixture_id)
            .group_by(UserMOTMVote.voted_player_id, Player.display_name, Team.name)
            .order_by(func.count(UserMOTMVote.id).desc())
        )
    ).all()
    total = sum(r.vote_count for r in rows)
    tally = [
        MOTMTallyEntry(
            player_id=r.voted_player_id,
            display_name=r.display_name,
            team_name=r.team_name,
            vote_count=r.vote_count,
            vote_share_percent=round((r.vote_count / total * 100), 1) if total else 0.0,
        )
        for r in rows
    ]

    user_vote_id: int | None = None
    if user:
        user_vote = (
            await db.execute(
                select(UserMOTMVote.voted_player_id).where(
                    UserMOTMVote.user_id == user.id,
                    UserMOTMVote.fixture_id == fixture_id,
                )
            )
        ).scalar_one_or_none()
        user_vote_id = user_vote

    return MOTMTallyResponse(
        fixture_id=fixture_id,
        total_votes=total,
        user_voted_player_id=user_vote_id,
        tally=tally,
    )


@router.post(
    "/fixtures/{fixture_id}/motm-vote",
    response_model=MOTMTallyResponse,
)
async def cast_motm_vote(
    fixture_id: int,
    body: MOTMVoteRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cast (or update) Man of the Match vote. One vote per user per fixture."""
    fixture = (
        await db.execute(select(Fixture).where(Fixture.id == fixture_id))
    ).scalar_one_or_none()
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    player = (
        await db.execute(select(Player).where(Player.id == body.voted_player_id))
    ).scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    existing = (
        await db.execute(
            select(UserMOTMVote).where(
                UserMOTMVote.user_id == user.id,
                UserMOTMVote.fixture_id == fixture_id,
            )
        )
    ).scalar_one_or_none()

    if existing:
        if existing.is_locked:
            raise HTTPException(
                status_code=400,
                detail="Vote is locked (poll closed)",
            )
        existing.voted_player_id = body.voted_player_id
        existing.voted_at = datetime.utcnow()
    else:
        db.add(
            UserMOTMVote(
                user_id=user.id,
                fixture_id=fixture_id,
                voted_player_id=body.voted_player_id,
            )
        )

    await db.commit()

    return await get_motm_tally(fixture_id, user, db)


@router.get(
    "/fixtures/{fixture_id}/intelligence",
    response_model=MatchIntelligenceBundle,
)
async def get_fixture_intelligence(
    fixture_id: int,
    language: str = "sv",
    db: AsyncSession = Depends(get_db),
):
    """Return AI narrative cards for a fixture (pre/in/post-match) in the given language."""
    rows = (
        (
            await db.execute(
                select(MatchIntelligence)
                .where(MatchIntelligence.fixture_id == fixture_id)
                .where(MatchIntelligence.language == language)
            )
        )
        .scalars()
        .all()
    )
    by_kind: dict[str, MatchIntelligence] = {row.kind.value: row for row in rows}

    def to_response(kind_value: str) -> MatchIntelligenceResponse | None:
        row = by_kind.get(kind_value)
        if row is None:
            return None
        return MatchIntelligenceResponse(
            kind=row.kind.value,
            language=row.language,
            summary=row.summary,
            body=row.body,
            model_version=row.model_version,
            provider=row.provider,
            as_of_minute=row.as_of_minute,
            generated_at=row.generated_at,
        )

    return MatchIntelligenceBundle(
        pre_match=to_response("pre_match"),
        in_match=to_response("in_match"),
        post_match=to_response("post_match"),
    )


@router.post(
    "/admin/intelligence/generate/{fixture_id}/{kind}",
    response_model=MatchIntelligenceResponse,
)
async def trigger_intelligence_generation(
    fixture_id: int,
    kind: str,
    language: str = "sv",
    force: bool = False,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually generate AI intelligence for a fixture (admin only).

    `kind` must be one of: pre_match, in_match, post_match.
    `force=true` regenerates even if a row already exists.
    """
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    try:
        kind_enum = IntelligenceKind(kind)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid kind. Choose from: {[k.value for k in IntelligenceKind]}",
        )

    from app.services.intelligence_orchestrator import generate_intelligence

    try:
        row = await generate_intelligence(
            db,
            fixture_id=fixture_id,
            kind=kind_enum,
            language=language,
            force=force,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    return MatchIntelligenceResponse(
        kind=row.kind.value,
        language=row.language,
        summary=row.summary,
        body=row.body,
        model_version=row.model_version,
        provider=row.provider,
        as_of_minute=row.as_of_minute,
        generated_at=row.generated_at,
    )


@router.post("/admin/intelligence/prewarm-tournament/{league_id}")
async def trigger_tournament_prewarm(
    league_id: int,
    limit: int = Query(200, ge=1, le=500, description="Max antal matcher per körning"),
    user: User = Depends(get_current_user),
):
    """Köa pre-match-generering för alla SCHEDULED-matcher i en cup-liga (VM/EM/CL).

    Skickar uppgiften till Celery-workern som kör det offline. Returnerar
    omedelbart med task-ID. Använd FÖRE turneringen startar för att fylla
    cachen med analyser så ingen besökare träffar cold-start.
    """
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")

    from app.services.tasks import prewarm_tournament_intelligence

    async_result = prewarm_tournament_intelligence.delay(league_id=league_id, limit=limit)
    return {
        "status": "queued",
        "task_id": async_result.id,
        "league_id": league_id,
        "limit": limit,
        "hint": "Spåra resultatet via celery-worker-loggarna eller GET /admin/intelligence/{fixture_id}/...",
    }


@router.get(
    "/fixtures/{fixture_id}/lineups",
    response_model=FixtureLineupsBundle,
)
async def get_fixture_lineups(
    fixture_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return per-team lineups (starters + bench) with formation + pitch coords."""
    fx_row = (
        await db.execute(
            select(Fixture.home_team_id, Fixture.away_team_id).where(
                Fixture.id == fixture_id
            )
        )
    ).first()
    if fx_row is None:
        raise HTTPException(status_code=404, detail="Fixture not found")
    home_team_id, away_team_id = fx_row

    lineups = (
        (
            await db.execute(
                select(FixtureLineup).where(FixtureLineup.fixture_id == fixture_id)
            )
        )
        .scalars()
        .all()
    )
    if not lineups:
        return FixtureLineupsBundle(home=None, away=None)

    lineup_ids = [lu.id for lu in lineups]
    rows = (
        await db.execute(
            select(
                FixtureLineupPlayer.lineup_id,
                FixtureLineupPlayer.player_id,
                FixtureLineupPlayer.shirt_number,
                FixtureLineupPlayer.position_label,
                FixtureLineupPlayer.grid_x,
                FixtureLineupPlayer.grid_y,
                FixtureLineupPlayer.is_starting,
                FixtureLineupPlayer.is_captain,
                Player.display_name,
            )
            .join(Player, FixtureLineupPlayer.player_id == Player.id)
            .where(FixtureLineupPlayer.lineup_id.in_(lineup_ids))
        )
    ).all()

    players_by_lineup: dict[int, list[LineupPlayerResponse]] = {
        lu.id: [] for lu in lineups
    }
    for row in rows:
        players_by_lineup[row.lineup_id].append(
            LineupPlayerResponse(
                player_id=row.player_id,
                display_name=row.display_name,
                shirt_number=row.shirt_number,
                position_label=row.position_label,
                grid_x=row.grid_x,
                grid_y=row.grid_y,
                is_starting=row.is_starting,
                is_captain=row.is_captain,
            )
        )

    def build(team_id: int) -> LineupResponse | None:
        for lu in lineups:
            if lu.team_id == team_id:
                roster = players_by_lineup.get(lu.id, [])
                starters = [p for p in roster if p.is_starting]
                substitutes = [p for p in roster if not p.is_starting]
                starters.sort(
                    key=lambda p: (p.grid_y or 0, p.grid_x or 0, p.shirt_number or 0)
                )
                substitutes.sort(key=lambda p: p.shirt_number or 999)
                return LineupResponse(
                    team_id=lu.team_id,
                    formation=lu.formation,
                    coach_name=lu.coach_name,
                    starters=starters,
                    substitutes=substitutes,
                )
        return None

    return FixtureLineupsBundle(home=build(home_team_id), away=build(away_team_id))


@router.get(
    "/fixtures/{fixture_id}/events",
    response_model=list[FixtureEventResponse],
)
async def get_fixture_events(
    fixture_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return chronological event timeline (goals/cards/subs/VAR) for a fixture."""
    primary = aliased(Player)
    secondary = aliased(Player)
    player_in = aliased(Player)
    player_out = aliased(Player)
    stmt = (
        select(
            FixtureEvent.id,
            FixtureEvent.minute,
            FixtureEvent.stoppage,
            FixtureEvent.event_type,
            FixtureEvent.team_id,
            primary.display_name.label("primary_player_name"),
            secondary.display_name.label("secondary_player_name"),
            player_in.display_name.label("player_in_name"),
            player_out.display_name.label("player_out_name"),
            FixtureEvent.description,
        )
        .outerjoin(primary, FixtureEvent.primary_player_id == primary.id)
        .outerjoin(secondary, FixtureEvent.secondary_player_id == secondary.id)
        .outerjoin(player_in, FixtureEvent.player_in_id == player_in.id)
        .outerjoin(player_out, FixtureEvent.player_out_id == player_out.id)
        .where(FixtureEvent.fixture_id == fixture_id)
        .order_by(FixtureEvent.minute, FixtureEvent.stoppage)
    )
    result = await db.execute(stmt)
    return [
        FixtureEventResponse.model_validate(row, from_attributes=True)
        for row in result.mappings()
    ]


# ── Predictions ────────────────────────────────────────────


@router.get("/predictions/today", response_model=list[PredictionResponse])
async def get_todays_predictions(db: AsyncSession = Depends(get_db)):
    """Get ML predictions for today's matches."""
    predictions = await db_service.get_predictions_for_date(db, date.today())
    return predictions


@router.get("/predictions/accuracy")
async def get_prediction_accuracy(
    league_id: int | None = None,
    days: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive model accuracy stats over the last N days.

    Returns overall accuracy, per-league breakdown, calibration,
    value bet performance, and model version info.
    """
    from sqlalchemy import select, func, and_, case
    from app.models.models import Prediction, Fixture, League

    cutoff = datetime.utcnow() - __import__("datetime").timedelta(days=days)

    # ── Overall accuracy ──
    base_filter = and_(
        Prediction.created_at >= cutoff,
        Prediction.was_correct.is_not(None),
    )
    query = (
        select(
            func.count(Prediction.id).label("total"),
            func.sum(case((Prediction.was_correct.is_(True), 1), else_=0)).label(
                "correct"
            ),
            func.avg(Prediction.confidence).label("avg_confidence"),
        )
        .join(Fixture)
        .where(base_filter)
    )
    if league_id:
        query = query.where(Fixture.league_id == league_id)

    result = await db.execute(query)
    row = result.one()
    total = row.total or 0
    correct = row.correct or 0
    accuracy = (correct / total * 100) if total > 0 else 0.0

    # ── Per-league breakdown ──
    league_query = (
        select(
            Fixture.league_id,
            League.name.label("league_name"),
            func.count(Prediction.id).label("total"),
            func.sum(case((Prediction.was_correct.is_(True), 1), else_=0)).label(
                "correct"
            ),
        )
        .join(Fixture, Prediction.fixture_id == Fixture.id)
        .join(League, Fixture.league_id == League.id)
        .where(base_filter)
        .group_by(Fixture.league_id, League.name)
        .order_by(func.count(Prediction.id).desc())
    )
    league_result = await db.execute(league_query)
    per_league = [
        {
            "league_id": r.league_id,
            "league_name": r.league_name,
            "total": r.total,
            "correct": r.correct or 0,
            "accuracy": round((r.correct or 0) / r.total * 100, 2) if r.total else 0,
        }
        for r in league_result.all()
    ]

    # ── Value bet performance ──
    vb_query = (
        select(
            func.count(Prediction.id).label("total"),
            func.sum(case((Prediction.was_correct.is_(True), 1), else_=0)).label(
                "correct"
            ),
            func.avg(Prediction.value_edge).label("avg_edge"),
        )
        .join(Fixture)
        .where(
            base_filter,
            Prediction.value_edge.is_not(None),
            Prediction.value_edge > 0,
        )
    )
    vb_result = await db.execute(vb_query)
    vb_row = vb_result.one()
    vb_total = vb_row.total or 0
    vb_correct = vb_row.correct or 0

    # ── Model version info ──
    version_query = (
        select(
            Prediction.model_version,
            func.count(Prediction.id).label("count"),
            func.sum(case((Prediction.was_correct.is_(True), 1), else_=0)).label(
                "correct"
            ),
        )
        .where(base_filter)
        .group_by(Prediction.model_version)
        .order_by(func.count(Prediction.id).desc())
    )
    version_result = await db.execute(version_query)
    per_version = [
        {
            "version": r.model_version,
            "predictions": r.count,
            "correct": r.correct or 0,
            "accuracy": round((r.correct or 0) / r.count * 100, 2) if r.count else 0,
        }
        for r in version_result.all()
    ]

    return {
        "period_days": days,
        "overall": {
            "total_predictions": total,
            "correct": correct,
            "accuracy": round(accuracy, 2),
            "avg_confidence": round(float(row.avg_confidence or 0), 4),
        },
        "per_league": per_league,
        "value_bets": {
            "total": vb_total,
            "correct": vb_correct,
            "accuracy": round((vb_correct / vb_total * 100) if vb_total else 0, 2),
            "avg_edge": round(float(vb_row.avg_edge or 0), 2),
        },
        "per_model_version": per_version,
    }


@router.get("/predictions/{fixture_id}", response_model=PredictionResponse)
async def get_prediction(fixture_id: int, db: AsyncSession = Depends(get_db)):
    """Get prediction for a specific fixture."""
    prediction = await db_service.get_prediction_by_fixture(db, fixture_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction


# ── Value Bets ─────────────────────────────────────────────


@router.get("/value-bets", response_model=list[ValueBetResponse])
async def get_value_bets(
    min_edge: float = Query(5.0, description="Minimum edge % to show"),
    league_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get matches where our model identifies value vs bookmaker odds."""
    from sqlalchemy import select, or_
    from app.models.models import MatchStatus, Prediction, Fixture

    query = (
        select(Prediction)
        .join(Fixture)
        .where(
            or_(
                Prediction.is_value_home.is_(True),
                Prediction.is_value_draw.is_(True),
                Prediction.is_value_away.is_(True),
            ),
            Prediction.value_edge >= min_edge,
            Fixture.status == MatchStatus.SCHEDULED,
        )
    )
    if league_id:
        query = query.where(Fixture.league_id == league_id)

    result = await db.execute(query)
    predictions = list(result.scalars().all())

    # Build value bet responses (requires fixture + odds data loaded)
    value_bets = []
    for pred in predictions:
        fixture = await db_service.get_fixture_by_id(db, pred.fixture_id)
        if not fixture or not fixture.odds:
            continue

        best_odds = fixture.odds[0]  # Use first available bookmaker
        suggested = (
            "Home" if pred.is_value_home else ("Draw" if pred.is_value_draw else "Away")
        )

        from app.ml.predictor import MatchPrediction

        model_pred = MatchPrediction(
            home_win_prob=pred.home_win_prob,
            draw_prob=pred.draw_prob,
            away_win_prob=pred.away_win_prob,
            confidence=pred.confidence,
            over_25_prob=pred.over_25_prob or 0.5,
            expected_goals=pred.expected_goals or 2.5,
        )

        kelly = 0.0
        if best_odds.home_odds and best_odds.draw_odds and best_odds.away_odds:
            from app.ml.predictor import identify_value_bets

            vb = identify_value_bets(
                model_pred,
                {
                    "home": best_odds.home_odds,
                    "draw": best_odds.draw_odds,
                    "away": best_odds.away_odds,
                },
            )
            kelly = vb.get("kelly_fraction", 0.0)

        value_bets.append(
            ValueBetResponse(
                fixture=FixtureResponse.model_validate(fixture),
                prediction=PredictionResponse.model_validate(pred),
                best_odds=OddsResponse.model_validate(best_odds),
                edge_percent=pred.value_edge or 0.0,
                suggested_bet=suggested,
                kelly_fraction=kelly,
            )
        )

    return value_bets


# ── Head to Head ───────────────────────────────────────────


@router.get("/h2h/{team1_id}/{team2_id}")
async def get_head_to_head(
    team1_id: int, team2_id: int, last: int = 10, db: AsyncSession = Depends(get_db)
):
    """Get head-to-head history and analysis between two teams."""
    fixtures = await db_service.get_h2h_fixtures(db, team1_id, team2_id, last)

    team1_wins = sum(
        1
        for f in fixtures
        if (f.home_team_id == team1_id and (f.home_goals or 0) > (f.away_goals or 0))
        or (f.away_team_id == team1_id and (f.away_goals or 0) > (f.home_goals or 0))
    )
    team2_wins = sum(
        1
        for f in fixtures
        if (f.home_team_id == team2_id and (f.home_goals or 0) > (f.away_goals or 0))
        or (f.away_team_id == team2_id and (f.away_goals or 0) > (f.home_goals or 0))
    )
    draws = len(fixtures) - team1_wins - team2_wins
    total_goals = sum((f.home_goals or 0) + (f.away_goals or 0) for f in fixtures)
    avg_goals = total_goals / len(fixtures) if fixtures else 0.0

    return {
        "team1_id": team1_id,
        "team2_id": team2_id,
        "matches": [FixtureResponse.model_validate(f) for f in fixtures],
        "summary": {
            "total_matches": len(fixtures),
            "team1_wins": team1_wins,
            "draws": draws,
            "team2_wins": team2_wins,
            "avg_goals": round(avg_goals, 2),
        },
    }


# ── Standings ──────────────────────────────────────────────


@router.get("/standings/{league_id}", response_model=list[StandingResponse])
async def get_standings(
    league_id: int, season: int | None = None, db: AsyncSession = Depends(get_db)
):
    """Get league standings with xG data."""
    standings = await db_service.get_standings(db, league_id, season)
    if not standings:
        raise HTTPException(status_code=404, detail="Standings not found")

    # We need to load the team for each standing
    result = []
    for s in standings:
        from sqlalchemy import select
        from app.models.models import Team

        team_result = await db.execute(select(Team).where(Team.id == s.team_id))
        team = team_result.scalar_one_or_none()
        if not team:
            continue
        result.append(
            StandingResponse(
                position=s.position,
                team=TeamResponse.model_validate(team),
                points=s.points,
                played=s.played,
                won=s.won,
                drawn=s.drawn,
                lost=s.lost,
                goals_for=s.goals_for,
                goals_against=s.goals_against,
                goal_diff=s.goal_diff,
                form=s.form,
                xg_for=s.xg_for,
                xg_against=s.xg_against,
            )
        )

    return result


# ── Tournament structure (cup-format som VM) ───────────────


@router.get(
    "/tournaments/{league_id}/structure",
    response_model=TournamentStructureResponse,
)
async def get_tournament_structure(
    league_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Hela turneringen i ETT svar: grupper med beräknade ställningar + alla knockout-stages.

    Designat för cup-typ-ligor (VM, EM, CL). Returnerar 404 om ligan inte finns.
    Group-standings beräknas on-the-fly från färdigspelade group-stage-fixtures.
    """
    from app.models.models import Fixture, League, MatchStatus, Season, Team

    league_row = await db.execute(select(League).where(League.id == league_id))
    league = league_row.scalar_one_or_none()
    if league is None:
        raise HTTPException(status_code=404, detail="League not found")

    season_row = await db.execute(
        select(Season)
        .where(Season.league_id == league_id)
        .order_by(Season.year_start.desc())
        .limit(1)
    )
    season = season_row.scalar_one_or_none()

    fixtures_row = await db.execute(
        select(Fixture)
        .where(Fixture.league_id == league_id)
        .options(
            selectinload(Fixture.league),
            selectinload(Fixture.home_team),
            selectinload(Fixture.away_team),
        )
        .order_by(Fixture.kickoff.asc())
    )
    fixtures = list(fixtures_row.scalars().all())

    # ── Group-stage: bygg grupp-ställningar from färdiga matcher ──
    group_fixtures: dict[str, list[Fixture]] = {}
    for f in fixtures:
        if f.group_letter:
            group_fixtures.setdefault(f.group_letter, []).append(f)

    def _empty_row(team: Team) -> dict:
        return {
            "team": team,
            "points": 0,
            "played": 0,
            "won": 0,
            "drawn": 0,
            "lost": 0,
            "goals_for": 0,
            "goals_against": 0,
        }

    groups: list[TournamentGroup] = []
    for letter in sorted(group_fixtures.keys()):
        gfix = group_fixtures[letter]
        # alla unika lag i gruppen (4 i ett vanligt VM-format)
        teams_by_id: dict[int, dict] = {}
        for f in gfix:
            for t in (f.home_team, f.away_team):
                if t.id not in teams_by_id:
                    teams_by_id[t.id] = _empty_row(t)
        # räkna spelade matcher
        finished = (MatchStatus.FINISHED, MatchStatus.AWARDED)
        for f in gfix:
            if f.status not in finished:
                continue
            if f.home_goals is None or f.away_goals is None:
                continue
            h = teams_by_id[f.home_team_id]
            a = teams_by_id[f.away_team_id]
            h["played"] += 1
            a["played"] += 1
            h["goals_for"] += f.home_goals
            h["goals_against"] += f.away_goals
            a["goals_for"] += f.away_goals
            a["goals_against"] += f.home_goals
            if f.home_goals > f.away_goals:
                h["won"] += 1
                h["points"] += 3
                a["lost"] += 1
            elif f.home_goals < f.away_goals:
                a["won"] += 1
                a["points"] += 3
                h["lost"] += 1
            else:
                h["drawn"] += 1
                a["drawn"] += 1
                h["points"] += 1
                a["points"] += 1

        rows = list(teams_by_id.values())
        for r in rows:
            r["goal_diff"] = r["goals_for"] - r["goals_against"]
        rows.sort(
            key=lambda r: (
                -r["points"],
                -r["goal_diff"],
                -r["goals_for"],
                r["team"].name,
            )
        )
        standings = [
            TournamentGroupStanding(
                team=TeamResponse.model_validate(r["team"]),
                points=r["points"],
                played=r["played"],
                won=r["won"],
                drawn=r["drawn"],
                lost=r["lost"],
                goals_for=r["goals_for"],
                goals_against=r["goals_against"],
                goal_diff=r["goal_diff"],
            )
            for r in rows
        ]
        groups.append(
            TournamentGroup(
                letter=letter,
                standings=standings,
                fixtures=[FixtureResponse.model_validate(f) for f in gfix],
            )
        )

    # ── Knockouts: gruppera per stage_name, sortera enligt naturlig progression ──
    _KO_ORDER = {
        "Round of 32": 1,
        "Round of 16": 2,
        "Quarter-finals": 3,
        "Semi-finals": 4,
        "3rd Place Final": 5,
        "Final": 6,
    }
    knockout_buckets: dict[str, list[Fixture]] = {}
    for f in fixtures:
        if f.stage_name and f.stage_name in _KO_ORDER:
            knockout_buckets.setdefault(f.stage_name, []).append(f)

    knockouts = [
        TournamentKnockoutStage(
            stage_name=name,
            fixtures=[FixtureResponse.model_validate(f) for f in sorted(kfix, key=lambda x: x.kickoff)],
        )
        for name, kfix in sorted(
            knockout_buckets.items(), key=lambda kv: _KO_ORDER[kv[0]]
        )
    ]

    return TournamentStructureResponse(
        league=LeagueResponse.model_validate(league),
        season_label=season.label if season else "",
        season_start=season.start_date if season else None,
        season_end=season.end_date if season else None,
        groups=groups,
        knockouts=knockouts,
    )


# ── Sentiment ──────────────────────────────────────────────


@router.get("/sentiment/{team_id}", response_model=list[SentimentResponse])
async def get_team_sentiment(
    team_id: int, days: int = Query(7, ge=1, le=30), db: AsyncSession = Depends(get_db)
):
    """Get sentiment analysis for a team over the last N days."""
    scores = await db_service.get_team_sentiment(db, team_id, days)
    return scores


@router.get("/sentiment/match/{fixture_id}")
async def get_match_sentiment(fixture_id: int, db: AsyncSession = Depends(get_db)):
    """Get sentiment comparison for both teams in a fixture."""
    fixture = await db_service.get_fixture_by_id(db, fixture_id)
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    home_sentiment = await db_service.get_team_sentiment(
        db, fixture.home_team_id, days=7
    )
    away_sentiment = await db_service.get_team_sentiment(
        db, fixture.away_team_id, days=7
    )

    def avg_score(scores: list) -> float | None:
        if not scores:
            return None
        return round(sum(s.score for s in scores) / len(scores), 3)

    return {
        "fixture_id": fixture_id,
        "home_sentiment": avg_score(home_sentiment),
        "away_sentiment": avg_score(away_sentiment),
        "home_detail": [SentimentResponse.model_validate(s) for s in home_sentiment],
        "away_detail": [SentimentResponse.model_validate(s) for s in away_sentiment],
    }


# ── Admin — manual task triggers ───────────────────────────

ADMIN_EMAILS: set[str] = {
    "REDACTED-EMAIL",
    "REDACTED-EMAIL",
    "admin@scorelock.saidborna.com",
}


@router.post("/admin/trigger/{task_name}")
async def trigger_task(
    task_name: str,
    user: User = Depends(get_current_user),
):
    """Manually trigger a Celery task (admin only).

    Available tasks: standings, fixtures, predictions, sentiment, odds, train
    """
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    from app.core.celery_app import celery_app

    task_map = {
        "standings": "app.services.tasks.update_standings",
        "fixtures": "app.services.tasks.fetch_daily_fixtures",
        "predictions": "app.services.tasks.run_daily_predictions",
        "sentiment": "app.services.tasks.run_sentiment_analysis",
        "odds": "app.services.tasks.fetch_odds_updates",
        "train": "app.services.tasks.train_model",
        "content-previews": "app.services.tasks.generate_content_previews",
        "content-reports": "app.services.tasks.generate_content_reports",
        "content-round-summaries": "app.services.tasks.generate_content_round_summaries",
        "content-value-bets": "app.services.tasks.generate_content_value_bets",
        "content-news-rewrites": "app.services.tasks.generate_content_news_rewrites",
    }

    if task_name not in task_map:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown task. Choose from: {', '.join(task_map.keys())}",
        )

    result = celery_app.send_task(task_map[task_name])
    return {"status": "queued", "task_id": result.id, "task_name": task_name}


@router.post("/admin/trigger/sportmonks-sync/{fixture_external_id}")
async def trigger_sportmonks_sync(
    fixture_external_id: str,
    user: User = Depends(get_current_user),
):
    """Trigger SportMonks sync för en specifik fixture (admin only).

    Static-mode (default): ignorerar fixture_external_id, läser från
    competitor-ref payload-filer. Live-mode: hämtar via SportMonks v3 API.

    Idempotent — re-trigger uppdaterar mutable fält utan dupliacering.
    """
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    from app.core.celery_app import celery_app

    result = celery_app.send_task(
        "app.services.tasks.sportmonks_sync_fixture",
        args=[fixture_external_id],
    )
    return {
        "status": "queued",
        "task_id": result.id,
        "task_name": "sportmonks_sync_fixture",
        "fixture_external_id": fixture_external_id,
    }


@router.get("/admin/quota")
async def get_quota_status(user: User = Depends(get_current_user)):
    """Get API quota usage across all data sources (admin only)."""
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")

    from app.core.quota_manager import get_quota_manager

    quota = get_quota_manager()
    usage = await quota.get_all_usage()
    return {"quotas": usage}


@router.get("/admin/debug/api-test")
async def debug_api_test(
    league_id: int = Query(39, description="API-Football league ID"),
    season: int = Query(2025, description="Season year"),
    user: User = Depends(get_current_user),
):
    """Test API-Football endpoint directly — returns raw JSON (admin only, 1 API call)."""
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")

    from app.services.api_football import api_football
    from app.core.config import get_settings
    from app.services.tasks import _detect_season
    import httpx

    s = get_settings()
    key = s.api_football_key
    key_status = (
        f"{key[:4]}...{key[-4:]}" if len(key) > 8 else ("SET" if key else "EMPTY")
    )

    try:
        async with httpx.AsyncClient(
            base_url=api_football.base_url,
            headers=api_football.headers,
            timeout=30.0,
        ) as client:
            resp = await client.get(
                "/fixtures", params={"league": league_id, "season": season}
            )
            data = resp.json()
            return {
                "api_key_status": key_status,
                "base_url": api_football.base_url,
                "detected_season": _detect_season(date.today().year, "premier_league"),
                "requested": {"league_id": league_id, "season": season},
                "status_code": resp.status_code,
                "errors": data.get("errors"),
                "results_count": data.get("results", 0),
                "paging": data.get("paging"),
                "first_3": data.get("response", [])[:3],
                "headers": {
                    "x-ratelimit-requests-remaining": resp.headers.get(
                        "x-ratelimit-requests-remaining"
                    ),
                    "x-ratelimit-requests-limit": resp.headers.get(
                        "x-ratelimit-requests-limit"
                    ),
                },
            }
    except Exception as exc:
        return {"error": str(exc)}


@router.post("/admin/fix-league-metadata")
async def fix_league_metadata(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """One-shot: update league display names, logos, and countries."""
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")

    from app.models.models import League as LeagueModel

    LEAGUE_META = {
        # Match by slug OR display name (idempotent)
        "premier_league": {
            "display": "Premier League",
            "logo_url": "https://crests.football-data.org/PL.png",
            "country": "England",
            "league_type": "league",
        },
        "Premier League": {
            "display": "Premier League",
            "logo_url": "https://crests.football-data.org/PL.png",
            "country": "England",
            "league_type": "league",
        },
        "la_liga": {
            "display": "La Liga",
            "logo_url": "https://crests.football-data.org/laliga.png",
            "country": "Spain",
            "league_type": "league",
        },
        "La Liga": {
            "display": "La Liga",
            "logo_url": "https://crests.football-data.org/laliga.png",
            "country": "Spain",
            "league_type": "league",
        },
        "serie_a": {
            "display": "Serie A",
            "logo_url": "https://crests.football-data.org/c111.png",
            "country": "Italy",
            "league_type": "league",
        },
        "Serie A": {
            "display": "Serie A",
            "logo_url": "https://crests.football-data.org/c111.png",
            "country": "Italy",
            "league_type": "league",
        },
        "bundesliga": {
            "display": "Bundesliga",
            "logo_url": "https://crests.football-data.org/BL1.png",
            "country": "Germany",
            "league_type": "league",
        },
        "Bundesliga": {
            "display": "Bundesliga",
            "logo_url": "https://crests.football-data.org/BL1.png",
            "country": "Germany",
            "league_type": "league",
        },
        "ligue_1": {
            "display": "Ligue 1",
            "logo_url": "https://crests.football-data.org/FL1.png",
            "country": "France",
            "league_type": "league",
        },
        "Ligue 1": {
            "display": "Ligue 1",
            "logo_url": "https://crests.football-data.org/FL1.png",
            "country": "France",
            "league_type": "league",
        },
        "champions_league": {
            "display": "Champions League",
            "logo_url": "https://crests.football-data.org/CL.png",
            "country": "Europe",
            "league_type": "cup",
        },
        "Champions League": {
            "display": "Champions League",
            "logo_url": "https://crests.football-data.org/CL.png",
            "country": "Europe",
            "league_type": "cup",
        },
        "europa_league": {
            "display": "Europa League",
            "logo_url": "https://crests.football-data.org/CL.png",
            "country": "Europe",
            "league_type": "cup",
        },
        "Europa League": {
            "display": "Europa League",
            "logo_url": "https://crests.football-data.org/CL.png",
            "country": "Europe",
            "league_type": "cup",
        },
        "conference_league": {
            "display": "Conference League",
            "logo_url": "https://crests.football-data.org/CL.png",
            "country": "Europe",
            "league_type": "cup",
        },
        "Conference League": {
            "display": "Conference League",
            "logo_url": "https://crests.football-data.org/CL.png",
            "country": "Europe",
            "league_type": "cup",
        },
        "allsvenskan": {
            "display": "Allsvenskan",
            "logo_url": "https://crests.football-data.org/BL1.png",
            "country": "Sweden",
            "league_type": "league",
        },
        "Allsvenskan": {
            "display": "Allsvenskan",
            "logo_url": "https://crests.football-data.org/BL1.png",
            "country": "Sweden",
            "league_type": "league",
        },
    }

    updated = []
    from sqlalchemy import select

    result = await db.execute(select(LeagueModel))
    leagues = list(result.scalars().all())

    for league in leagues:
        meta = LEAGUE_META.get(league.name)
        if meta:
            league.logo_url = meta["logo_url"]
            league.country = meta["country"]
            league.type = meta["league_type"]
            league.name = meta["display"]
            updated.append(meta["display"])

    await db.commit()
    return {"updated": updated}


@router.get("/admin/debug/db-stats")
async def debug_db_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get database fixture/standings counts by season (admin only)."""
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")

    from sqlalchemy import func, select as sa_select
    from app.models.models import Fixture, Standing, League, Team

    # Count fixtures by season
    fixture_stats = await db.execute(
        sa_select(Fixture.season, func.count(Fixture.id))
        .group_by(Fixture.season)
        .order_by(Fixture.season.desc())
    )
    fixtures_by_season = [{"season": s, "count": c} for s, c in fixture_stats.all()]

    # Count standings by season
    standing_stats = await db.execute(
        sa_select(Standing.season, func.count(Standing.id))
        .group_by(Standing.season)
        .order_by(Standing.season.desc())
    )
    standings_by_season = [{"season": s, "count": c} for s, c in standing_stats.all()]

    # League count
    league_count = await db.execute(sa_select(func.count(League.id)))
    team_count = await db.execute(sa_select(func.count(Team.id)))

    # Date range of fixtures
    date_range = await db.execute(
        sa_select(func.min(Fixture.kickoff), func.max(Fixture.kickoff))
    )
    min_date, max_date = date_range.one()

    return {
        "fixtures_by_season": fixtures_by_season,
        "standings_by_season": standings_by_season,
        "total_leagues": league_count.scalar(),
        "total_teams": team_count.scalar(),
        "fixture_date_range": {
            "earliest": str(min_date) if min_date else None,
            "latest": str(max_date) if max_date else None,
        },
    }


@router.post("/admin/dev/trigger-score-update/{fixture_id}")
async def trigger_score_update(
    fixture_id: int,
    home_goals: int = 0,
    away_goals: int = 0,
    status: str = "live",
    minute: int | None = None,
    user: User = Depends(get_current_user),
):
    """Publish a manual score-update event to the live WebSocket channel (admin only).

    Test-only endpoint. Lets us verify the live-pipeline end-to-end without waiting
    for real live fixtures. Connected WebSocket clients receive a `score_update`
    payload identical to what `update_live_scores` produces in prod.
    """
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    from app.api.websocket import publish_score_update

    publish_score_update(
        fixture_id=fixture_id,
        home_goals=home_goals,
        away_goals=away_goals,
        status=status,
        minute=minute,
    )
    return {
        "status": "published",
        "fixture_id": fixture_id,
        "home_goals": home_goals,
        "away_goals": away_goals,
        "status_value": status,
        "minute": minute,
    }


@router.post("/admin/sync-now")
async def admin_sync_now(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetch fixtures + standings synchronously via football-data.org (admin only).
    Uses ~11 football-data.org calls (6 fixtures + 5 standings). Current season!
    """
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")

    from app.services.football_data import (
        football_data,
        FD_COMPETITIONS,
        FootballDataClient,
    )
    from app.services.api_football import LEAGUE_IDS, PHASE_1_LEAGUES
    from app.services.db_service import (
        upsert_fixtures_batch,
        get_league_by_api_id,
        upsert_league,
        upsert_standing,
    )
    from app.services.tasks import _detect_season

    current_year = date.today().year
    results = {
        "fixtures": {},
        "standings": {},
        "errors": [],
        "source": "football-data.org",
    }

    # Build reverse map
    fd_name_to_code = {v["name"]: code for code, v in FD_COMPETITIONS.items()}

    # ── Fixtures ──
    for league_name in PHASE_1_LEAGUES:
        api_id = LEAGUE_IDS[league_name]
        league = await get_league_by_api_id(db, api_id)
        if not league:
            league = await upsert_league(
                db,
                api_id=api_id,
                name=league_name,
                country=league_name,
                logo_url=None,
                league_type="cup"
                if league_name
                in ("champions_league", "europa_league", "conference_league")
                else "league",
                current_season=current_year,
            )

        fd_code = fd_name_to_code.get(league_name)
        if not fd_code:
            results["fixtures"][league_name] = {
                "skipped": True,
                "reason": "Not in football-data.org",
            }
            continue

        try:
            matches = await football_data.get_matches(fd_code)
            normalized = [
                FootballDataClient.normalize_match_to_fixture(m, api_id)
                for m in matches
            ]
            normalized = [n for n in normalized if n]
            if normalized:
                count = await upsert_fixtures_batch(db, normalized, league)
                results["fixtures"][league_name] = {
                    "fetched": len(matches),
                    "upserted": count,
                }
            else:
                results["fixtures"][league_name] = {
                    "fetched": 0,
                    "error": "empty after normalization",
                }
        except Exception as exc:
            results["errors"].append(f"{league_name}: {str(exc)}")

    # ── Standings (domestic leagues only) ──
    STANDINGS_LEAGUES = ["premier_league", "la_liga", "serie_a", "bundesliga"]
    for league_name in STANDINGS_LEAGUES:
        api_id = LEAGUE_IDS[league_name]
        league = await get_league_by_api_id(db, api_id)
        if not league:
            continue

        fd_code = fd_name_to_code.get(league_name)
        if not fd_code:
            continue

        season = _detect_season(current_year, league_name)

        try:
            standings = await football_data.get_standings(fd_code)
            count = 0
            for entry in standings:
                normalized = FootballDataClient.normalize_standing(entry, fd_code)
                result = await upsert_standing(db, normalized, league, season)
                if result:
                    count += 1
            results["standings"][league_name] = {"season": season, "count": count}
        except Exception as exc:
            results["errors"].append(f"standings/{league_name}: {str(exc)}")

    await db.commit()
    return results


# ── Articles (AI Content Engine) ──────────────────────────


@router.get("/articles", response_model=ArticleListResponse)
async def list_articles(
    article_type: str | None = Query(
        None,
        description="Filter by type: MATCH_PREVIEW, MATCH_REPORT, ROUND_SUMMARY, VALUE_BET_ALERT, NEWS_REWRITE",
    ),
    league_id: int | None = Query(None, description="Filter by league ID"),
    language: str | None = Query(None, description="Filter by language (e.g. sv)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List published articles with optional filters."""
    a_type = None
    if article_type:
        try:
            a_type = ArticleType(article_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid type. Choose from: {[t.value for t in ArticleType]}",
            )

    articles = await db_service.get_articles(
        db, a_type, league_id, language, limit, offset
    )
    total = await db_service.count_articles(db, a_type, league_id)
    return ArticleListResponse(
        articles=[ArticleResponse.model_validate(a) for a in articles],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/articles/{slug}", response_model=ArticleResponse)
async def get_article(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single article by slug."""
    article = await db_service.get_article_by_slug(db, slug)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return ArticleResponse.model_validate(article)


# ── Affiliate System ──────────────────────────────────────


@router.get("/affiliate/links", response_model=list[AffiliateLinkResponse])
async def get_affiliate_links(
    country: str = Query("SE", description="Country code (e.g. SE, UK)"),
    bookmaker: str | None = Query(None, description="Filter by bookmaker slug"),
    db: AsyncSession = Depends(get_db),
):
    """Get active affiliate links for a given country."""
    links = await db_service.get_affiliate_links(db, country, bookmaker)
    return [AffiliateLinkResponse.model_validate(link) for link in links]


@router.post("/affiliate/click", response_model=AffiliateClickResponse)
async def record_click(
    click: AffiliateClickCreate,
    request: Request,
    user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Record an affiliate link click (called by frontend before redirect)."""
    import hashlib

    ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:16]
    ua = request.headers.get("user-agent", "")[:500]

    result = await db_service.record_affiliate_click(
        db,
        link_id=click.link_id,
        fixture_id=click.fixture_id,
        user_id=user.id if user else None,
        page_source=click.page_source,
        ip_hash=ip_hash,
        user_agent=ua,
    )
    await db.commit()
    return AffiliateClickResponse.model_validate(result)


@router.get("/admin/affiliate/stats", response_model=list[AffiliateStatsResponse])
async def get_affiliate_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get affiliate click statistics (admin only)."""
    if user.email not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Admin access required")
    stats = await db_service.get_affiliate_stats(db)
    return stats


# ── Tipping League ────────────────────────────────────────


@router.post("/tips", response_model=UserPredictionResponse)
async def create_tip(
    tip: UserPredictionCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a prediction (tip) for a match. Can update before kickoff."""
    if tip.predicted_outcome not in ("H", "D", "A"):
        raise HTTPException(status_code=400, detail="outcome must be H, D, or A")
    try:
        result = await db_service.create_user_prediction(
            db,
            user_id=user.id,
            fixture_id=tip.fixture_id,
            predicted_outcome=tip.predicted_outcome,
            predicted_home_goals=tip.predicted_home_goals,
            predicted_away_goals=tip.predicted_away_goals,
        )
        await db.commit()
        return UserPredictionResponse.model_validate(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tips/mine", response_model=list[UserPredictionWithFixture])
async def get_my_tips(
    scored_only: bool = Query(False, description="Only show scored tips"),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's tips."""
    preds = await db_service.get_user_predictions(
        db, user.id, scored_only=scored_only, limit=limit
    )
    return [UserPredictionWithFixture.model_validate(p) for p in preds]


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    days: int | None = Query(
        None, description="Filter by last N days (null = all time)"
    ),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Get the tipping league leaderboard."""
    return await db_service.get_leaderboard(db, limit=limit, days=days)


@router.get("/tips/ai-vs-me", response_model=AIvsUserStats)
async def ai_vs_me(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compare the user's tipping accuracy against the AI model."""
    stats = await db_service.get_ai_vs_user(db, user.id)
    return stats


@router.get("/tips/weekly-top", response_model=WeeklyTopTipper | None)
async def weekly_top_tipper(
    db: AsyncSession = Depends(get_db),
):
    """Get the top tipper for the current week."""
    return await db_service.get_weekly_top_tipper(db)


# ── Prediction Cards (M8) ─────────────────────────────────


@router.get("/prediction-card/{fixture_id}")
async def get_prediction_card(
    fixture_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Generate a shareable prediction card image for a fixture.

    Returns a PNG image (1200×630 OG-image format).
    """
    from fastapi.responses import Response
    from app.models.models import Fixture, Prediction, ValueBet
    from app.services.social.prediction_card import generate_prediction_card
    from sqlalchemy import select

    # Get fixture
    result = await db.execute(select(Fixture).where(Fixture.id == fixture_id))
    fixture = result.scalar_one_or_none()
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    # Get prediction
    pred_result = await db.execute(
        select(Prediction).where(Prediction.fixture_id == fixture_id)
    )
    pred = pred_result.scalar_one_or_none()

    # Get value bet
    vb_result = await db.execute(
        select(ValueBet)
        .where(ValueBet.fixture_id == fixture_id)
        .order_by(ValueBet.edge.desc())
        .limit(1)
    )
    vb = vb_result.scalar_one_or_none()

    prediction_text = "Ingen prognos tillgänglig"
    home_pct = draw_pct = away_pct = None
    if pred:
        prediction_text = pred.predicted_outcome or "—"
        home_pct = pred.home_win_probability
        draw_pct = pred.draw_probability
        away_pct = pred.away_win_probability

    value_bet_text = None
    if vb:
        value_bet_text = f"{vb.bet_type} @{vb.odds:.2f} (edge: +{vb.edge:.1f}%)"

    kickoff_str = (
        fixture.kickoff.strftime("%Y-%m-%d %H:%M UTC") if fixture.kickoff else "TBD"
    )

    image_bytes = generate_prediction_card(
        home_team=fixture.home_team,
        away_team=fixture.away_team,
        league_name=fixture.league_name or "League",
        kickoff=kickoff_str,
        prediction=prediction_text,
        home_win_pct=home_pct,
        draw_pct=draw_pct,
        away_win_pct=away_pct,
        value_bet=value_bet_text,
    )

    return Response(
        content=image_bytes,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Content-Disposition": f"inline; filename=scorelock-{fixture_id}.png",
        },
    )
