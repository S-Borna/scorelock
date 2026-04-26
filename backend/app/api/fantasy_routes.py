"""Fantasy routes — T1 foundation (seasons, gameweeks, player market).

All fantasy endpoints live here to keep the main routes file focused on
the public-facing platform endpoints. Mounted under /api/v1/fantasy in main.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.models import (
    FantasyGameweek,
    FantasyPlayerPricing,
    FantasySeason,
    Player,
    Team,
)
from app.schemas.schemas import (
    FantasyGameweekResponse,
    FantasyPlayerMarketBundle,
    FantasyPlayerMarketResponse,
    FantasySeasonDetailResponse,
    FantasySeasonResponse,
)

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
