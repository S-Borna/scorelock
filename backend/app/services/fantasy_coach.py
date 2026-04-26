"""AI fantasy coach — generates transfer / captain / formation recs via Sonnet 4.6.

Cache window: 4 hours per team (recommendations stale on team change).
Cost ceiling: ~$0.05 per generation (3 recs = 1 Claude call).
"""

import json
import structlog
from datetime import datetime, timedelta
from typing import Any

from anthropic import AsyncAnthropic
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.models import (
    AIRecommendationKind,
    FantasyAIRecommendation,
    FantasyPlayerPricing,
    FantasyTeam,
    FantasyTeamPlayer,
    Player,
)

logger = structlog.get_logger()
settings = get_settings()

MODEL_VERSION = "claude-sonnet-4-6"
CACHE_TTL_HOURS = 4
MAX_OUTPUT_TOKENS = 1500


SYSTEM_PROMPT_SV = """Du är ScoreLocks AI-coach för fantasy fotboll. Du analyserar
användarens trupp, marknadsdata och kommande matcher, och ger konkreta
rekommendationer på svenska.

Regler:
- Säg vad data visar — inte vad användaren vill höra.
- Inga klichéer ("nu gäller det", "spelet om").
- Hänvisa konkret till siffror (form, ownership, pris, matchups).
- Inga emojier.
- Svenska.

Du måste returnera ett JSON-objekt med exakt formen:
{
  "recommendations": [
    {
      "kind": "transfer_in" | "transfer_out" | "captain" | "formation",
      "player_in_id": number | null,
      "player_out_id": number | null,
      "captain_player_id": number | null,
      "formation": string | null,
      "expected_point_diff": number,
      "confidence": number (0.0-1.0),
      "reasoning_sv": "1-2 meningar svensk text"
    }
  ]
}

Max 3 rekommendationer. Endast spelare som finns i marknaden — använd id-numren
exakt som de är. Ge bara rec som faktiskt höjer poängen."""


def _format_team_for_prompt(team: FantasyTeam, players: list[dict]) -> str:
    lines = [
        f"Lag: {team.name} (formation {team.formation})",
        f"Bank: {team.bank_balance / 10:.1f}M, fria byten: {team.free_transfers_available}",
        f"Total poäng: {team.total_points}",
        "",
        "Spelare i truppen:",
    ]
    for p in players:
        cap = "(K) " if p["is_captain"] else "(V) " if p["is_vice_captain"] else ""
        bench = "" if p["is_starting"] else " [BÄNK]"
        lines.append(
            f"  id={p['player_id']}: {cap}{p['display_name']} "
            f"[{p['slot_position']}] €{p['current_price'] / 10:.1f}M{bench}"
        )
    return "\n".join(lines)


def _format_market_for_prompt(market: list[dict]) -> str:
    lines = ["Top tillgängliga spelare i marknaden (ej i truppen):"]
    for p in market[:30]:
        lines.append(
            f"  id={p['player_id']}: {p['display_name']} "
            f"[{p['position']}] €{p['current_price'] / 10:.1f}M  "
            f"ägd {p['selected_by_pct']:.1f}%  poäng {p['fantasy_points_total']}"
        )
    return "\n".join(lines)


async def _gather_team_state(
    db: AsyncSession, team: FantasyTeam
) -> tuple[list[dict], list[dict]]:
    """Build the (team_players, market_players) lists for prompt context."""
    team_rows = (
        await db.execute(
            select(
                FantasyTeamPlayer.player_id,
                FantasyTeamPlayer.slot_position,
                FantasyTeamPlayer.is_starting,
                FantasyTeamPlayer.purchase_price,
                Player.display_name,
                FantasyPlayerPricing.current_price,
            )
            .join(Player, Player.id == FantasyTeamPlayer.player_id)
            .outerjoin(
                FantasyPlayerPricing,
                (FantasyPlayerPricing.player_id == FantasyTeamPlayer.player_id)
                & (FantasyPlayerPricing.season_id == team.season_id),
            )
            .where(FantasyTeamPlayer.team_id == team.id)
        )
    ).all()

    team_players = [
        {
            "player_id": row.player_id,
            "display_name": row.display_name,
            "slot_position": row.slot_position,
            "is_starting": row.is_starting,
            "current_price": row.current_price or row.purchase_price,
            "is_captain": row.player_id == team.captain_player_id,
            "is_vice_captain": row.player_id == team.vice_captain_player_id,
        }
        for row in team_rows
    ]
    on_team_ids = {p["player_id"] for p in team_players}

    market_rows = (
        await db.execute(
            select(
                FantasyPlayerPricing.player_id,
                Player.display_name,
                Player.position_code,
                FantasyPlayerPricing.current_price,
                FantasyPlayerPricing.selected_by_pct,
                FantasyPlayerPricing.fantasy_points_total,
            )
            .join(Player, Player.id == FantasyPlayerPricing.player_id)
            .where(FantasyPlayerPricing.season_id == team.season_id)
            .order_by(desc(FantasyPlayerPricing.selected_by_pct))
        )
    ).all()

    market_players = [
        {
            "player_id": row.player_id,
            "display_name": row.display_name,
            "position": row.position_code or "?",
            "current_price": row.current_price,
            "selected_by_pct": row.selected_by_pct,
            "fantasy_points_total": row.fantasy_points_total,
        }
        for row in market_rows
        if row.player_id not in on_team_ids
    ]

    return team_players, market_players


def _build_user_prompt(
    team: FantasyTeam, team_players: list[dict], market: list[dict]
) -> str:
    return (
        _format_team_for_prompt(team, team_players)
        + "\n\n"
        + _format_market_for_prompt(market)
        + "\n\nGe upp till 3 konkreta rekommendationer baserat på datan ovan."
    )


def _parse_recs(raw: str) -> list[dict[str, Any]]:
    payload = json.loads(raw)
    recs = payload.get("recommendations", [])
    if not isinstance(recs, list):
        raise ValueError("recommendations must be a list")
    return recs[:3]


class FantasyCoach:
    """Stateless wrapper for Claude-driven fantasy coaching."""

    def __init__(self) -> None:
        self.client: AsyncAnthropic | None = None

    def _get_client(self) -> AsyncAnthropic:
        if self.client is None:
            if not settings.anthropic_api_key:
                raise RuntimeError("ANTHROPIC_API_KEY not configured")
            self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self.client

    async def get_or_generate(
        self,
        db: AsyncSession,
        team: FantasyTeam,
        force_regenerate: bool = False,
    ) -> list[FantasyAIRecommendation]:
        """Return cached recs if fresh, else generate new ones via Claude."""
        if not force_regenerate:
            cached = (
                (
                    await db.execute(
                        select(FantasyAIRecommendation)
                        .where(FantasyAIRecommendation.team_id == team.id)
                        .where(
                            FantasyAIRecommendation.cached_until >= datetime.utcnow()
                        )
                        .order_by(FantasyAIRecommendation.generated_at.desc())
                    )
                )
                .scalars()
                .all()
            )
            if cached:
                return cached

        team_players, market = await _gather_team_state(db, team)
        user_prompt = _build_user_prompt(team, team_players, market)

        client = self._get_client()
        response = await client.messages.create(
            model=MODEL_VERSION,
            max_tokens=MAX_OUTPUT_TOKENS,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT_SV,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_prompt}],
        )
        if not response.content:
            raise ValueError("Empty response from Claude")
        block = response.content[0]
        text = getattr(block, "text", "")
        if not text:
            raise ValueError("Response block is not a text block")

        logger.info(
            "fantasy_coach_generated",
            team_id=team.id,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
        )

        recs_data = _parse_recs(text.strip())
        cached_until = datetime.utcnow() + timedelta(hours=CACHE_TTL_HOURS)
        rows: list[FantasyAIRecommendation] = []

        # Clear stale cached recs for this team
        existing = (
            (
                await db.execute(
                    select(FantasyAIRecommendation).where(
                        FantasyAIRecommendation.team_id == team.id
                    )
                )
            )
            .scalars()
            .all()
        )
        for old in existing:
            await db.delete(old)
        await db.flush()

        for rec in recs_data:
            try:
                kind = AIRecommendationKind(rec.get("kind", "transfer_in"))
            except ValueError:
                continue
            row = FantasyAIRecommendation(
                team_id=team.id,
                gameweek_id=None,
                kind=kind,
                payload={
                    "player_in_id": rec.get("player_in_id"),
                    "player_out_id": rec.get("player_out_id"),
                    "captain_player_id": rec.get("captain_player_id"),
                    "formation": rec.get("formation"),
                    "expected_point_diff": rec.get("expected_point_diff"),
                },
                reasoning_text=str(rec.get("reasoning_sv", "")).strip(),
                confidence_score=float(rec.get("confidence", 0.5)),
                model_version=MODEL_VERSION,
                cached_until=cached_until,
            )
            db.add(row)
            rows.append(row)

        await db.commit()
        for r in rows:
            await db.refresh(r)
        return rows


_coach: FantasyCoach | None = None


def get_fantasy_coach() -> FantasyCoach:
    global _coach
    if _coach is None:
        _coach = FantasyCoach()
    return _coach
