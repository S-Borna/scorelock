"""Fantasy team service — squad validation, transfers, scoring rollup.

Squad rules (Premier League Fantasy-style):
- 15 players total: 2 GK, 5 DEF, 5 MID, 3 FWD
- 11 starters + 4 bench
- Total purchase price ≤ season.total_budget_units
- Captain must be among starters
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    FantasyPlayerPricing,
    FantasySeason,
    FantasyTeam,
    FantasyTeamPlayer,
    FantasyTransfer,
    Player,
)
from app.services.fantasy_scoring import _normalize_position

SQUAD_LIMITS = {
    "GK": 2,
    "DEF": 5,
    "MID": 5,
    "FWD": 3,
}
TOTAL_SQUAD_SIZE = sum(SQUAD_LIMITS.values())  # 15
STARTING_SIZE = 11
BENCH_SIZE = TOTAL_SQUAD_SIZE - STARTING_SIZE  # 4


class TeamValidationError(ValueError):
    """Raised when a fantasy team violates squad / budget rules."""


def validate_squad_composition(positions: list[str]) -> None:
    """Check that the 15 picked players satisfy 2/5/5/3 by position."""
    if len(positions) != TOTAL_SQUAD_SIZE:
        raise TeamValidationError(
            f"Squad must have exactly {TOTAL_SQUAD_SIZE} players, got {len(positions)}"
        )

    counts: dict[str, int] = {}
    for raw in positions:
        norm = _normalize_position(raw)
        counts[norm] = counts.get(norm, 0) + 1

    for pos, expected in SQUAD_LIMITS.items():
        actual = counts.get(pos, 0)
        if actual != expected:
            raise TeamValidationError(
                f"Squad must have {expected} {pos}-players, got {actual}"
            )


def validate_budget(total_price: int, budget: int) -> None:
    if total_price > budget:
        raise TeamValidationError(
            f"Total price {total_price / 10:.1f}M exceeds budget {budget / 10:.1f}M"
        )


def validate_starting_count(starting_flags: list[bool]) -> None:
    starting = sum(1 for f in starting_flags if f)
    if starting != STARTING_SIZE:
        raise TeamValidationError(
            f"Starting XI must be exactly {STARTING_SIZE}, got {starting}"
        )


async def fetch_player_pricing_map(
    db: AsyncSession, season_id: int, player_ids: list[int]
) -> dict[int, FantasyPlayerPricing]:
    rows = (
        (
            await db.execute(
                select(FantasyPlayerPricing).where(
                    FantasyPlayerPricing.season_id == season_id,
                    FantasyPlayerPricing.player_id.in_(player_ids),
                )
            )
        )
        .scalars()
        .all()
    )
    return {row.player_id: row for row in rows}


async def fetch_player_position_map(
    db: AsyncSession, player_ids: list[int]
) -> dict[int, str]:
    rows = (
        await db.execute(
            select(Player.id, Player.position_code).where(Player.id.in_(player_ids))
        )
    ).all()
    return {row.id: _normalize_position(row.position_code) for row in rows}


async def create_team(
    db: AsyncSession,
    user_id: int,
    season_id: int,
    name: str,
    formation: str,
    player_picks: list[dict],
) -> FantasyTeam:
    """Create a new fantasy team for a user.

    player_picks: list of dicts {player_id, is_starting}.
    """
    season = (
        await db.execute(select(FantasySeason).where(FantasySeason.id == season_id))
    ).scalar_one_or_none()
    if not season:
        raise TeamValidationError(f"Season {season_id} not found")

    existing = (
        await db.execute(
            select(FantasyTeam).where(
                FantasyTeam.user_id == user_id,
                FantasyTeam.season_id == season_id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise TeamValidationError("User already has a team for this season")

    player_ids = [p["player_id"] for p in player_picks]
    if len(set(player_ids)) != len(player_ids):
        raise TeamValidationError("Squad cannot contain duplicate players")

    pricing = await fetch_player_pricing_map(db, season_id, player_ids)
    positions = await fetch_player_position_map(db, player_ids)

    missing = [pid for pid in player_ids if pid not in pricing]
    if missing:
        raise TeamValidationError(
            f"Players not available in season {season_id}: {missing}"
        )

    validate_squad_composition([positions[pid] for pid in player_ids])
    validate_starting_count([p["is_starting"] for p in player_picks])

    total_price = sum(pricing[pid].current_price for pid in player_ids)
    validate_budget(total_price, season.total_budget_units)

    team = FantasyTeam(
        user_id=user_id,
        season_id=season_id,
        name=name,
        formation=formation,
        bank_balance=season.total_budget_units - total_price,
    )
    db.add(team)
    await db.flush()

    for pick in player_picks:
        db.add(
            FantasyTeamPlayer(
                team_id=team.id,
                player_id=pick["player_id"],
                slot_position=positions[pick["player_id"]],
                is_starting=pick["is_starting"],
                purchase_price=pricing[pick["player_id"]].current_price,
            )
        )

    await db.commit()
    await db.refresh(team)
    return team


async def apply_transfer(
    db: AsyncSession,
    team: FantasyTeam,
    player_in_id: int,
    player_out_id: int,
) -> FantasyTransfer:
    """Swap player_out for player_in on a team.

    Validates: same position, sufficient bank balance, player_out is on team,
    player_in is in season pricing and not already on team.
    """
    if player_in_id == player_out_id:
        raise TeamValidationError("player_in and player_out must differ")

    team_players = (
        (
            await db.execute(
                select(FantasyTeamPlayer).where(FantasyTeamPlayer.team_id == team.id)
            )
        )
        .scalars()
        .all()
    )
    on_team_ids = {tp.player_id for tp in team_players}
    if player_out_id not in on_team_ids:
        raise TeamValidationError(f"Player {player_out_id} is not on team")
    if player_in_id in on_team_ids:
        raise TeamValidationError(f"Player {player_in_id} already on team")

    pricing = await fetch_player_pricing_map(
        db, team.season_id, [player_in_id, player_out_id]
    )
    if player_in_id not in pricing:
        raise TeamValidationError(f"Player {player_in_id} not in season pricing")
    if player_out_id not in pricing:
        raise TeamValidationError(f"Player {player_out_id} not in season pricing")

    positions = await fetch_player_position_map(db, [player_in_id, player_out_id])
    if positions[player_in_id] != positions[player_out_id]:
        raise TeamValidationError(
            f"Position mismatch: in={positions[player_in_id]} "
            f"vs out={positions[player_out_id]}"
        )

    in_price = pricing[player_in_id].current_price
    out_price = pricing[player_out_id].current_price
    new_bank = team.bank_balance + out_price - in_price
    if new_bank < 0:
        raise TeamValidationError(
            f"Insufficient bank: need {(in_price - out_price) / 10:.1f}M, "
            f"have {team.bank_balance / 10:.1f}M"
        )

    out_team_player = next(tp for tp in team_players if tp.player_id == player_out_id)
    out_slot = out_team_player.slot_position
    out_starting = out_team_player.is_starting

    await db.delete(out_team_player)
    await db.flush()

    db.add(
        FantasyTeamPlayer(
            team_id=team.id,
            player_id=player_in_id,
            slot_position=out_slot,
            is_starting=out_starting,
            purchase_price=in_price,
        )
    )

    was_free = team.free_transfers_available > 0
    point_cost = 0 if was_free else 4

    transfer = FantasyTransfer(
        team_id=team.id,
        gameweek_id=None,
        player_in_id=player_in_id,
        player_out_id=player_out_id,
        in_price=in_price,
        out_price=out_price,
        was_free=was_free,
        point_cost=point_cost,
    )
    db.add(transfer)

    team.bank_balance = new_bank
    team.transfers_made_total += 1
    team.free_transfers_available = max(0, team.free_transfers_available - 1)

    if team.captain_player_id == player_out_id:
        team.captain_player_id = None
    if team.vice_captain_player_id == player_out_id:
        team.vice_captain_player_id = None

    await db.commit()
    await db.refresh(transfer)
    return transfer
