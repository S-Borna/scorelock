"""Fantasy routes — T1 foundation (seasons, gameweeks, player market).

All fantasy endpoints live here to keep the main routes file focused on
the public-facing platform endpoints. Mounted under /api/v1/fantasy in main.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import (
    FantasyAIRecommendation,
    FantasyGameweek,
    FantasyPlayerPricing,
    FantasySeason,
    FantasyTeam,
    FantasyTeamPlayer,
    Player,
    Team,
    User,
)
from app.schemas.schemas import (
    FantasyAIRecommendationResponse,
    FantasyAIRecommendationsBundle,
    FantasyGameweekResponse,
    FantasyPlayerMarketBundle,
    FantasyPlayerMarketResponse,
    FantasySeasonDetailResponse,
    FantasySeasonResponse,
    FantasyTeamCaptainRequest,
    FantasyTeamCreateRequest,
    FantasyTeamPatchRequest,
    FantasyTeamPlayerEntry,
    FantasyTeamResponse,
    FantasyTeamViceCaptainRequest,
    FantasyTransferRequest,
    FantasyTransferResponse,
)
from app.services import fantasy_team as team_service

router = APIRouter()


# ── Seasons ────────────────────────────────────────────────


@router.get("/seasons", response_model=list[FantasySeasonResponse])
async def list_fantasy_seasons(
    only_active: bool = Query(True, description="Only return active seasons"),
    db: AsyncSession = Depends(get_db),
):
    """Return all fantasy seasons."""
    stmt = select(FantasySeason).order_by(FantasySeason.start_date.desc())
    if only_active:
        stmt = stmt.where(FantasySeason.is_active.is_(True))
    rows = (await db.execute(stmt)).scalars().all()
    return [
        FantasySeasonResponse(
            id=r.id,
            name=r.name,
            scope=r.scope.value if hasattr(r.scope, "value") else str(r.scope),
            primary_league_id=r.primary_league_id,
            start_date=r.start_date,
            end_date=r.end_date,
            total_budget_units=r.total_budget_units,
            is_active=r.is_active,
            transfer_rules=r.transfer_rules,
            point_weights=r.point_weights,
        )
        for r in rows
    ]


@router.get("/seasons/{season_id}", response_model=FantasySeasonDetailResponse)
async def get_fantasy_season(
    season_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return a single fantasy season with its gameweeks."""
    season = (
        await db.execute(select(FantasySeason).where(FantasySeason.id == season_id))
    ).scalar_one_or_none()
    if not season:
        raise HTTPException(status_code=404, detail="Fantasy season not found")

    gws = (
        (
            await db.execute(
                select(FantasyGameweek)
                .where(FantasyGameweek.season_id == season_id)
                .order_by(FantasyGameweek.gameweek_number)
            )
        )
        .scalars()
        .all()
    )

    return FantasySeasonDetailResponse(
        id=season.id,
        name=season.name,
        scope=season.scope.value
        if hasattr(season.scope, "value")
        else str(season.scope),
        primary_league_id=season.primary_league_id,
        start_date=season.start_date,
        end_date=season.end_date,
        total_budget_units=season.total_budget_units,
        is_active=season.is_active,
        transfer_rules=season.transfer_rules,
        point_weights=season.point_weights,
        gameweeks=[FantasyGameweekResponse.model_validate(gw) for gw in gws],
    )


@router.get(
    "/seasons/{season_id}/current-gw",
    response_model=FantasyGameweekResponse | None,
)
async def get_current_gameweek(
    season_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return the current/next gameweek for a season (next one with deadline > now)."""
    now = datetime.utcnow()
    row = (
        await db.execute(
            select(FantasyGameweek)
            .where(FantasyGameweek.season_id == season_id)
            .where(FantasyGameweek.deadline_at >= now)
            .order_by(FantasyGameweek.gameweek_number)
            .limit(1)
        )
    ).scalar_one_or_none()
    if row is None:
        # Fall back to the latest gameweek if all are past
        row = (
            await db.execute(
                select(FantasyGameweek)
                .where(FantasyGameweek.season_id == season_id)
                .order_by(FantasyGameweek.gameweek_number.desc())
                .limit(1)
            )
        ).scalar_one_or_none()
    if row is None:
        return None
    return FantasyGameweekResponse.model_validate(row)


# ── Player market ──────────────────────────────────────────


@router.get(
    "/seasons/{season_id}/players",
    response_model=FantasyPlayerMarketBundle,
)
async def get_player_market(
    season_id: int,
    league_id: int | None = Query(None, description="Filter by league"),
    position: str | None = Query(
        None, description="Filter by position (GK/DEF/MID/FWD)"
    ),
    max_price: int | None = Query(None, description="Max price (units)"),
    min_price: int | None = Query(None, description="Min price (units)"),
    sort: str = Query(
        "price_desc",
        description="Sort: price_desc, price_asc, points_desc, ownership_desc",
    ),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Return the player market for a season with filters + sorting."""
    season = (
        await db.execute(select(FantasySeason).where(FantasySeason.id == season_id))
    ).scalar_one_or_none()
    if not season:
        raise HTTPException(status_code=404, detail="Fantasy season not found")

    base = (
        select(
            Player.id.label("player_id"),
            Player.display_name,
            Player.position_code,
            Player.current_team_id.label("team_id"),
            Team.name.label("team_name"),
            Team.logo_url.label("team_logo_url"),
            FantasyPlayerPricing.current_price,
            FantasyPlayerPricing.starting_price,
            FantasyPlayerPricing.value_trend,
            FantasyPlayerPricing.selected_by_pct,
            FantasyPlayerPricing.fantasy_points_total,
        )
        .select_from(FantasyPlayerPricing)
        .join(Player, FantasyPlayerPricing.player_id == Player.id)
        .outerjoin(Team, Player.current_team_id == Team.id)
        .where(FantasyPlayerPricing.season_id == season_id)
    )

    # league_id filter not supported in T1 — players have no direct league FK.
    # Resolved when fixtures-based league mapping is added in a later phase.
    _ = league_id

    if max_price is not None:
        base = base.where(FantasyPlayerPricing.current_price <= max_price)
    if min_price is not None:
        base = base.where(FantasyPlayerPricing.current_price >= min_price)
    if position:
        base = base.where(Player.position_code.ilike(f"{position}%"))

    sort_map = {
        "price_desc": FantasyPlayerPricing.current_price.desc(),
        "price_asc": FantasyPlayerPricing.current_price.asc(),
        "points_desc": FantasyPlayerPricing.fantasy_points_total.desc(),
        "ownership_desc": FantasyPlayerPricing.selected_by_pct.desc(),
    }
    order = sort_map.get(sort, FantasyPlayerPricing.current_price.desc())
    base = base.order_by(order)

    count_stmt = (
        select(func.count(FantasyPlayerPricing.id))
        .select_from(FantasyPlayerPricing)
        .where(FantasyPlayerPricing.season_id == season_id)
    )
    if max_price is not None:
        count_stmt = count_stmt.where(FantasyPlayerPricing.current_price <= max_price)
    if min_price is not None:
        count_stmt = count_stmt.where(FantasyPlayerPricing.current_price >= min_price)
    total_count = (await db.execute(count_stmt)).scalar() or 0

    rows = (await db.execute(base.limit(limit).offset(offset))).all()

    players = [
        FantasyPlayerMarketResponse(
            player_id=row.player_id,
            display_name=row.display_name,
            position_code=row.position_code,
            team_id=row.team_id,
            team_name=row.team_name,
            team_logo_url=row.team_logo_url,
            league_id=None,
            current_price=row.current_price,
            starting_price=row.starting_price,
            value_trend=row.value_trend.value
            if hasattr(row.value_trend, "value")
            else str(row.value_trend),
            selected_by_pct=row.selected_by_pct,
            fantasy_points_total=row.fantasy_points_total,
        )
        for row in rows
    ]

    return FantasyPlayerMarketBundle(
        season_id=season_id,
        total_count=total_count,
        players=players,
    )


# ── Team management (T2) ──────────────────────────────────


async def _build_team_response(
    db: AsyncSession, team: FantasyTeam
) -> FantasyTeamResponse:
    """Hydrate a FantasyTeam into the wire response, with pricing + player meta."""
    players_query = (
        select(
            FantasyTeamPlayer.player_id,
            FantasyTeamPlayer.slot_position,
            FantasyTeamPlayer.is_starting,
            FantasyTeamPlayer.purchase_price,
            Player.display_name,
            Player.position_code,
            Player.current_team_id,
            Team.name.label("team_name"),
            Team.logo_url.label("team_logo_url"),
            FantasyPlayerPricing.current_price,
        )
        .select_from(FantasyTeamPlayer)
        .join(Player, FantasyTeamPlayer.player_id == Player.id)
        .outerjoin(Team, Player.current_team_id == Team.id)
        .outerjoin(
            FantasyPlayerPricing,
            (FantasyPlayerPricing.player_id == FantasyTeamPlayer.player_id)
            & (FantasyPlayerPricing.season_id == team.season_id),
        )
        .where(FantasyTeamPlayer.team_id == team.id)
    )
    rows = (await db.execute(players_query)).all()

    entries = [
        FantasyTeamPlayerEntry(
            player_id=row.player_id,
            display_name=row.display_name,
            position_code=row.position_code,
            slot_position=row.slot_position,
            is_starting=row.is_starting,
            purchase_price=row.purchase_price,
            current_price=row.current_price or row.purchase_price,
            team_name=row.team_name,
            team_logo_url=row.team_logo_url,
            is_captain=row.player_id == team.captain_player_id,
            is_vice_captain=row.player_id == team.vice_captain_player_id,
        )
        for row in rows
    ]

    squad_value = sum(e.current_price for e in entries)

    return FantasyTeamResponse(
        id=team.id,
        user_id=team.user_id,
        season_id=team.season_id,
        name=team.name,
        formation=team.formation,
        captain_player_id=team.captain_player_id,
        vice_captain_player_id=team.vice_captain_player_id,
        total_points=team.total_points,
        gameweek_points=team.gameweek_points,
        transfers_made_total=team.transfers_made_total,
        free_transfers_available=team.free_transfers_available,
        bank_balance=team.bank_balance,
        squad_value=squad_value,
        players=entries,
    )


@router.post("/teams", response_model=FantasyTeamResponse)
async def create_fantasy_team(
    body: FantasyTeamCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new fantasy team for the current user."""
    try:
        team = await team_service.create_team(
            db,
            user_id=user.id,
            season_id=body.season_id,
            name=body.name,
            formation=body.formation,
            player_picks=body.player_picks,
        )
    except team_service.TeamValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return await _build_team_response(db, team)


@router.get("/teams/mine", response_model=FantasyTeamResponse)
async def get_my_team(
    season_id: int = Query(..., description="Season id"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the current user's team for the given season."""
    team = (
        await db.execute(
            select(FantasyTeam).where(
                FantasyTeam.user_id == user.id,
                FantasyTeam.season_id == season_id,
            )
        )
    ).scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="No team for this season")
    return await _build_team_response(db, team)


@router.get("/teams/{team_id}", response_model=FantasyTeamResponse)
async def get_team_by_id(
    team_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Public team view (read-only — used for mini-league leaderboards)."""
    team = (
        await db.execute(select(FantasyTeam).where(FantasyTeam.id == team_id))
    ).scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return await _build_team_response(db, team)


@router.patch("/teams/{team_id}", response_model=FantasyTeamResponse)
async def patch_team(
    team_id: int,
    body: FantasyTeamPatchRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update team name and/or formation (owner only)."""
    team = (
        await db.execute(select(FantasyTeam).where(FantasyTeam.id == team_id))
    ).scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your team")
    if body.name is not None:
        team.name = body.name
    if body.formation is not None:
        team.formation = body.formation
    await db.commit()
    await db.refresh(team)
    return await _build_team_response(db, team)


@router.put("/teams/{team_id}/captain", response_model=FantasyTeamResponse)
async def set_captain(
    team_id: int,
    body: FantasyTeamCaptainRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Set the team captain (must be a starting player on the team)."""
    team = (
        await db.execute(select(FantasyTeam).where(FantasyTeam.id == team_id))
    ).scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your team")

    starting = (
        (
            await db.execute(
                select(FantasyTeamPlayer.player_id).where(
                    FantasyTeamPlayer.team_id == team_id,
                    FantasyTeamPlayer.is_starting.is_(True),
                )
            )
        )
        .scalars()
        .all()
    )
    if body.captain_player_id not in starting:
        raise HTTPException(
            status_code=400,
            detail="Captain must be one of the starting XI",
        )

    team.captain_player_id = body.captain_player_id
    if team.vice_captain_player_id == body.captain_player_id:
        team.vice_captain_player_id = None

    await db.commit()
    await db.refresh(team)
    return await _build_team_response(db, team)


@router.put("/teams/{team_id}/vice-captain", response_model=FantasyTeamResponse)
async def set_vice_captain(
    team_id: int,
    body: FantasyTeamViceCaptainRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Set the team vice-captain (must be a starting player on the team)."""
    team = (
        await db.execute(select(FantasyTeam).where(FantasyTeam.id == team_id))
    ).scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your team")

    starting = (
        (
            await db.execute(
                select(FantasyTeamPlayer.player_id).where(
                    FantasyTeamPlayer.team_id == team_id,
                    FantasyTeamPlayer.is_starting.is_(True),
                )
            )
        )
        .scalars()
        .all()
    )
    if body.vice_captain_player_id not in starting:
        raise HTTPException(
            status_code=400,
            detail="Vice-captain must be one of the starting XI",
        )
    if body.vice_captain_player_id == team.captain_player_id:
        raise HTTPException(
            status_code=400,
            detail="Vice-captain must differ from captain",
        )

    team.vice_captain_player_id = body.vice_captain_player_id
    await db.commit()
    await db.refresh(team)
    return await _build_team_response(db, team)


@router.post("/teams/{team_id}/transfer", response_model=FantasyTransferResponse)
async def make_transfer(
    team_id: int,
    body: FantasyTransferRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Swap player_out for player_in. Same position required, sufficient bank."""
    team = (
        await db.execute(select(FantasyTeam).where(FantasyTeam.id == team_id))
    ).scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your team")
    try:
        transfer = await team_service.apply_transfer(
            db,
            team=team,
            player_in_id=body.player_in_id,
            player_out_id=body.player_out_id,
        )
    except team_service.TeamValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return FantasyTransferResponse.model_validate(transfer)


# ── AI coach (T8) ─────────────────────────────────────────


@router.get(
    "/teams/{team_id}/ai/recommendations",
    response_model=FantasyAIRecommendationsBundle,
)
async def list_ai_recommendations(
    team_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Return cached AI coach recs for a team (no Claude call)."""
    rows = (
        (
            await db.execute(
                select(FantasyAIRecommendation)
                .where(FantasyAIRecommendation.team_id == team_id)
                .order_by(FantasyAIRecommendation.generated_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return FantasyAIRecommendationsBundle(
        team_id=team_id,
        recommendations=[
            FantasyAIRecommendationResponse.model_validate(r).model_copy(
                update={"model_version": "ScoreLock AI"}
            )
            for r in rows
        ],
        cached=True,
    )


@router.post(
    "/teams/{team_id}/ai/recommendations",
    response_model=FantasyAIRecommendationsBundle,
)
async def generate_ai_recommendations(
    team_id: int,
    force: bool = Query(False, description="Bypass cache and call Claude"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate (or fetch cached) AI coach recs via Sonnet 4.6."""
    team = (
        await db.execute(select(FantasyTeam).where(FantasyTeam.id == team_id))
    ).scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your team")

    from app.services.fantasy_coach import get_fantasy_coach

    coach = get_fantasy_coach()
    try:
        rows = await coach.get_or_generate(db, team, force_regenerate=force)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    return FantasyAIRecommendationsBundle(
        team_id=team_id,
        recommendations=[
            FantasyAIRecommendationResponse.model_validate(r).model_copy(
                update={"model_version": "ScoreLock AI"}
            )
            for r in rows
        ],
        cached=not force,
    )
