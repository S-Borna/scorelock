"""AI match intelligence generator (Phase 5).

Generates Swedish-first narrative analysis per fixture in three kinds:
pre-match (day before), in-match (live during), post-match (within 24h).

Uses Claude Sonnet 4.6 via Anthropic SDK. Prompt caching declared on the
system block — activates automatically once the cumulative cached prefix
exceeds the model's minimum (~1024 tokens). For the lean MVP prompts this
is a no-op, but the structure is ready for richer context in later phases.
"""

import json
import structlog
from datetime import datetime
from typing import Any

from anthropic import AsyncAnthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.models import (
    Fixture,
    FixtureEvent,
    FixtureStatistics,
    IntelligenceKind,
    League,
    MatchIntelligence,
    Team,
)

logger = structlog.get_logger()
settings = get_settings()

MODEL_VERSION = "claude-sonnet-4-6"
PROVIDER = "anthropic"
DEFAULT_LANGUAGE = "sv"
MAX_OUTPUT_TOKENS = 1024


SYSTEM_PROMPT_SV = """Du är ScoreLocks svenska fotbollsanalytiker.

Skriv kort, konkret och taktiskt. Som en kunnig vän som förklarar matchen,
inte som en pressagent. Säg vad data visar — inte vad publiken vill höra.

Regler:
- Inga klichéer ("nervkitlande matchen", "nu gäller det").
- Inga emojier.
- Inga betting-uppmaningar.
- Hänvisa konkret till siffror och händelser från det data du fått.
- Skriv på svenska.

Svar måste vara ett JSON-objekt på exakt formen:
{
  "summary": "<en mening, max 120 tecken — kärnfrasen>",
  "body": "<150–250 ord, 2–4 stycken, separerade med dubbla radbrytningar>"
}

Returnera bara JSON. Inget annat."""


PRE_MATCH_TEMPLATE = """Pre-match-analys.

Match: {home_name} vs {away_name}
Liga: {league} ({round})
Avspark: {kickoff}

Skriv en analys av matchupen: vad är spelet om, vilka styrkor möts, var
ligger bristerna. Säg vad du ser i datan, även när det är sparsamt."""


IN_MATCH_TEMPLATE = """Live-analys.

{home_name} {home_score} – {away_score} {away_name}
Minut: {minute}'

Senaste händelser:
{events_block}

Statistik just nu:
- Hemma: {h_possession}% bollinnehav, {h_shots} skott, xG {h_xg}
- Borta: {a_possession}% bollinnehav, {a_shots} skott, xG {a_xg}

Skriv en kort live-analys av momentum: vem äger matchen nu och varför."""


POST_MATCH_TEMPLATE = """Post-match-analys.

Slutresultat: {home_name} {home_score} – {away_score} {away_name}
Liga: {league} ({round})

Händelser:
{events_block}

Slutstatistik:
- Hemma: {h_possession}% boll, {h_shots} skott ({h_shots_on} på mål), xG {h_xg}
- Borta: {a_possession}% boll, {a_shots} skott ({a_shots_on} på mål), xG {a_xg}

Skriv en post-match-analys: vad avgjorde, matchade resultatet underliggande
siffror eller var det en xG-överraskning, vem bar laget."""


def _format_events(events: list[FixtureEvent], home_team_id: int) -> str:
    """Render an event timeline as a compact bulleted Swedish summary."""
    if not events:
        return "(inga registrerade händelser)"
    icons = {
        "GOAL": "Mål",
        "PENALTY_GOAL": "Straffmål",
        "OWN_GOAL": "Självmål",
        "MISSED_PENALTY": "Missad straff",
        "YELLOW_CARD": "Gult kort",
        "RED_CARD": "Rött kort",
        "SECOND_YELLOW": "Andra gula",
        "SUBSTITUTION": "Byte",
    }
    lines: list[str] = []
    for e in events:
        side = "Hemma" if e.team_id == home_team_id else "Borta"
        label = icons.get(e.event_type, e.event_type.replace("_", " ").title())
        minute = f"{e.minute}'" if not e.stoppage else f"{e.minute}+{e.stoppage}'"
        descriptor = e.description or ""
        lines.append(
            f"- {minute} {side} — {label}{(': ' + descriptor) if descriptor else ''}"
        )
    return "\n".join(lines)


def _stat_value(row: FixtureStatistics | None, field: str) -> str:
    if row is None:
        return "–"
    val = getattr(row, field, None)
    if val is None:
        return "–"
    if isinstance(val, float):
        return f"{val:.1f}"
    return str(val)


async def _build_context(
    db: AsyncSession, fixture: Fixture, kind: IntelligenceKind
) -> dict[str, Any]:
    """Collect everything the prompt template might reference for one fixture."""
    home = await db.get(Team, fixture.home_team_id)
    away = await db.get(Team, fixture.away_team_id)
    league = await db.get(League, fixture.league_id)

    stats_rows = (
        (
            await db.execute(
                select(FixtureStatistics).where(
                    FixtureStatistics.fixture_id == fixture.id
                )
            )
        )
        .scalars()
        .all()
    )
    stats_by_team = {s.team_id: s for s in stats_rows}
    h_stats = stats_by_team.get(fixture.home_team_id)
    a_stats = stats_by_team.get(fixture.away_team_id)

    events = (
        (
            await db.execute(
                select(FixtureEvent)
                .where(FixtureEvent.fixture_id == fixture.id)
                .order_by(FixtureEvent.minute, FixtureEvent.stoppage)
            )
        )
        .scalars()
        .all()
    )

    if kind == IntelligenceKind.IN_MATCH:
        live_minute = max((e.minute for e in events), default=0) if events else 0
    else:
        live_minute = 90

    return {
        "home_name": home.name if home else "?",
        "away_name": away.name if away else "?",
        "league": league.name if league else "?",
        "round": fixture.round or "–",
        "kickoff": fixture.kickoff.strftime("%Y-%m-%d %H:%M UTC")
        if fixture.kickoff
        else "?",
        "home_score": fixture.home_goals if fixture.home_goals is not None else 0,
        "away_score": fixture.away_goals if fixture.away_goals is not None else 0,
        "minute": live_minute,
        "events_block": _format_events(events, fixture.home_team_id),
        "h_possession": _stat_value(h_stats, "possession_pct"),
        "a_possession": _stat_value(a_stats, "possession_pct"),
        "h_shots": _stat_value(h_stats, "shots_total"),
        "a_shots": _stat_value(a_stats, "shots_total"),
        "h_shots_on": _stat_value(h_stats, "shots_on_target"),
        "a_shots_on": _stat_value(a_stats, "shots_on_target"),
        "h_xg": _stat_value(h_stats, "xg"),
        "a_xg": _stat_value(a_stats, "xg"),
    }


def _build_user_prompt(kind: IntelligenceKind, ctx: dict[str, Any]) -> str:
    if kind == IntelligenceKind.PRE_MATCH:
        return PRE_MATCH_TEMPLATE.format(**ctx)
    if kind == IntelligenceKind.IN_MATCH:
        return IN_MATCH_TEMPLATE.format(**ctx)
    if kind == IntelligenceKind.POST_MATCH:
        return POST_MATCH_TEMPLATE.format(**ctx)
    raise ValueError(f"Unknown intelligence kind: {kind}")


def _parse_response(text: str) -> tuple[str, str]:
    """Extract summary + body from the JSON the model returned."""
    cleaned = text.strip()
    # Claude wrappar ofta JSON i ```json ... ``` — strippa fence före parsning,
    # annars failar json.loads och råtexten (med fence) hamnar i body.
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
        if cleaned[:4].lower() == "json":
            cleaned = cleaned[4:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        # Last-resort: treat the full output as the body.
        return (text[:120], text)
    summary = str(payload.get("summary", "")).strip()
    body = str(payload.get("body", "")).strip()
    if not summary or not body:
        raise ValueError("LLM response missing summary or body")
    return summary, body


class IntelligenceGenerator:
    """Generate match intelligence narratives via Claude Sonnet 4.6."""

    def __init__(self) -> None:
        self.client: AsyncAnthropic | None = None

    def _get_client(self) -> AsyncAnthropic:
        if self.client is None:
            if not settings.anthropic_api_key:
                raise RuntimeError("ANTHROPIC_API_KEY not configured")
            self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self.client

    async def _call_model(self, user_prompt: str) -> str:
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
            "intelligence_generated",
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            cache_read=getattr(response.usage, "cache_read_input_tokens", 0),
            cache_create=getattr(response.usage, "cache_creation_input_tokens", 0),
        )
        return text.strip()

    async def generate(
        self,
        db: AsyncSession,
        fixture_id: int,
        kind: IntelligenceKind,
        language: str = DEFAULT_LANGUAGE,
        force_regenerate: bool = False,
    ) -> MatchIntelligence:
        """Generate (or fetch existing) intelligence for fixture+kind+language."""
        if not force_regenerate:
            existing = (
                await db.execute(
                    select(MatchIntelligence).where(
                        MatchIntelligence.fixture_id == fixture_id,
                        MatchIntelligence.kind == kind,
                        MatchIntelligence.language == language,
                    )
                )
            ).scalar_one_or_none()
            if existing:
                return existing

        fixture = (
            await db.execute(select(Fixture).where(Fixture.id == fixture_id))
        ).scalar_one_or_none()
        if not fixture:
            raise ValueError(f"Fixture {fixture_id} not found")

        ctx = await _build_context(db, fixture, kind)
        user_prompt = _build_user_prompt(kind, ctx)
        raw = await self._call_model(user_prompt)
        summary, body = _parse_response(raw)

        existing = (
            await db.execute(
                select(MatchIntelligence).where(
                    MatchIntelligence.fixture_id == fixture_id,
                    MatchIntelligence.kind == kind,
                    MatchIntelligence.language == language,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            existing.summary = summary
            existing.body = body
            existing.model_version = MODEL_VERSION
            existing.provider = PROVIDER
            existing.as_of_minute = (
                ctx["minute"] if kind == IntelligenceKind.IN_MATCH else None
            )
            existing.generated_at = datetime.utcnow()
            existing.updated_at = datetime.utcnow()
            row = existing
        else:
            row = MatchIntelligence(
                fixture_id=fixture_id,
                kind=kind,
                language=language,
                summary=summary,
                body=body,
                model_version=MODEL_VERSION,
                provider=PROVIDER,
                as_of_minute=(
                    ctx["minute"] if kind == IntelligenceKind.IN_MATCH else None
                ),
                generated_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(row)

        await db.commit()
        await db.refresh(row)
        return row


_generator: IntelligenceGenerator | None = None


def get_intelligence_generator() -> IntelligenceGenerator:
    """Singleton accessor for the generator."""
    global _generator
    if _generator is None:
        _generator = IntelligenceGenerator()
    return _generator
