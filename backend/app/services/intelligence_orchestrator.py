"""ScoreLock intelligens-orkestrator — det resilienta, kostnads-bundna genererings-navet.

Kedjan per (fixture, fas): cache-gate → dossier → modell-routing → Max-primär
(claude -p) → API-fallback (Anthropic) → spara i match_intelligence.

Miljö-medveten, samma kod båda hållen:
- host/box (claude + Max-auth finns) → platt Max-kostnad via claude -p.
- prod/Docker (ingen claude) → Anthropic-API.
Fallbacken triggas av ClaudeCLIError (inkl. saknad binär). Sätt
settings.intelligence_use_cli=False på prod för att hoppa över subprocess-försöket helt.

Claude resonerar STRIKT från dossiern (vår egen data), aldrig egen träningskunskap.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime

import structlog
from anthropic import AsyncAnthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.models import IntelligenceKind, MatchIntelligence
from app.services import claude_cli
from app.services.dossier import (
    build_inmatch_dossier,
    build_postmatch_dossier,
    build_prematch_dossier,
)

logger = structlog.get_logger()
settings = get_settings()

DEFAULT_LANGUAGE = "sv"
MAX_OUTPUT_TOKENS = 1024
PROVIDER_CLI = "claude-cli-max"
PROVIDER_API = "anthropic"

# Logisk modell → CLI-alias (claude -p) resp. kanoniskt Anthropic-API-id.
_CLI_MODEL = {"sonnet": "sonnet", "haiku": "haiku"}
_API_MODEL = {
    "sonnet": "claude-sonnet-4-6",
    "haiku": "claude-haiku-4-5-20251001",
}

_DOSSIER_BUILDERS = {
    IntelligenceKind.PRE_MATCH: build_prematch_dossier,
    IntelligenceKind.IN_MATCH: build_inmatch_dossier,
    IntelligenceKind.POST_MATCH: build_postmatch_dossier,
}


GROUNDING_SYSTEM = """Du är ScoreLocks svenska fotbollsanalytiker.

Du får ett DOSSIER i JSON — all data ScoreLock har om matchen (form, tabell, odds,
vår ML-models prediktion, händelser, statistik). Det är din ENDA källa.

Hårda regler:
- Resonera ENBART utifrån dossierns siffror. Hämta ALDRIG fakta ur eget minne
  (spelarnamn, transfers, gamla resultat) som inte står i dossiern.
- Citera de exakta siffrorna du använder (sannolikheter, odds, mål, minut).
- Står det "saknas" för ett fält: säg att datan saknas — gissa inte.
- När vår modell och marknadens implicita odds skiljer sig: lyft divergensen och
  vad den betyder (value-edge), neutralt, utan betting-uppmaning.
- Inga klichéer, inga emojier, ingen hype. Kunnig vän, inte pressagent. Svenska.

Svar = ett JSON-objekt på EXAKT formen:
{"summary": "<en mening, max 120 tecken>", "body": "<150-250 ord, 2-4 stycken med dubbla radbrytningar>"}
Returnera bara JSON."""


_KIND_INSTRUCTION = {
    IntelligenceKind.PRE_MATCH: (
        "Pre-match. Vad är spelet om? Vad säger form, tabelläge och vår modell "
        "jämfört med marknadens odds? Var ligger osäkerheten?"
    ),
    IntelligenceKind.IN_MATCH: (
        "Live. Vem äger matchen just nu utifrån ställning, minut, händelser och "
        "statistik? Stämmer läget med vår pre-match-prediktion eller överraskar det?"
    ),
    IntelligenceKind.POST_MATCH: (
        "Post-match. Vad avgjorde? Matchade slutresultatet de underliggande siffrorna "
        "och vår modells förväntan, eller var det en överraskning?"
    ),
}


def pick_model(kind: IntelligenceKind, dossier: dict) -> str:
    """Modell-routing: live/post + stormatch → Sonnet; rutin-pre-match → Haiku."""
    if kind in (IntelligenceKind.IN_MATCH, IntelligenceKind.POST_MATCH):
        return "sonnet"
    tabell = dossier.get("tabell", {})
    for side in ("hemmalag", "bortalag"):
        st = tabell.get(side)
        if isinstance(st, dict) and (st.get("position") or 99) <= 4:
            return "sonnet"
    return "haiku"


def _build_user_prompt(kind: IntelligenceKind, dossier: dict) -> str:
    return (
        f"{_KIND_INSTRUCTION[kind]}\n\nDOSSIER:\n"
        f"{json.dumps(dossier, ensure_ascii=False, indent=2)}"
    )


def _loads_lenient(text: str) -> dict:
    """Parsa JSON, strippa ev. ```json-fence (API kan wrappa svaret)."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
        if cleaned[:4].lower() == "json":
            cleaned = cleaned[4:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
    return json.loads(cleaned)


def _parse(payload: dict) -> tuple[str, str]:
    summary = str(payload.get("summary", "")).strip()
    body = str(payload.get("body", "")).strip()
    if not summary or not body:
        raise ValueError("LLM-svar saknar summary/body")
    return summary, body


async def _via_cli(system: str, user_prompt: str, model: str) -> dict:
    """Max-primär: claude -p på host (blockerande subprocess → kör i tråd)."""
    return await asyncio.to_thread(
        claude_cli.generate_json, system, user_prompt, _CLI_MODEL[model]
    )


async def _via_api(system: str, user_prompt: str, model: str) -> dict:
    """API-fallback: Anthropic-SDK (prod). Kräver ANTHROPIC_API_KEY."""
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY saknas — ingen API-fallback möjlig")
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    resp = await client.messages.create(
        model=_API_MODEL[model],
        max_tokens=MAX_OUTPUT_TOKENS,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user_prompt}],
    )
    if not resp.content:
        raise ValueError("Tomt svar från Anthropic-API")
    return _loads_lenient(getattr(resp.content[0], "text", ""))


async def generate_intelligence(
    session: AsyncSession,
    fixture_id: int,
    kind: IntelligenceKind,
    language: str = DEFAULT_LANGUAGE,
    force: bool = False,
) -> MatchIntelligence:
    """Generera (eller hämta cachad) dossier-grundad analys för (fixture, fas, språk).

    Cache-gate gör volymen = antal matcher, inte matcher × användare. Genereras EN
    gång, lagras, serveras därefter ur DB utan LLM-anrop.
    """
    if not force:
        existing = (
            await session.execute(
                select(MatchIntelligence).where(
                    MatchIntelligence.fixture_id == fixture_id,
                    MatchIntelligence.kind == kind,
                    MatchIntelligence.language == language,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing

    dossier = await _DOSSIER_BUILDERS[kind](session, fixture_id)
    model = pick_model(kind, dossier)
    user_prompt = _build_user_prompt(kind, dossier)

    if settings.intelligence_use_cli:
        try:
            payload = await _via_cli(GROUNDING_SYSTEM, user_prompt, model)
            provider = PROVIDER_CLI
        except claude_cli.ClaudeCLIError as exc:
            logger.warning(
                "intel_cli_fallback_api", fixture=fixture_id, kind=kind.value, err=str(exc)
            )
            payload = await _via_api(GROUNDING_SYSTEM, user_prompt, model)
            provider = PROVIDER_API
    else:
        payload = await _via_api(GROUNDING_SYSTEM, user_prompt, model)
        provider = PROVIDER_API

    summary, body = _parse(payload)
    as_of_minute = None
    if kind == IntelligenceKind.IN_MATCH:
        minute = dossier.get("live", {}).get("minut")
        as_of_minute = minute if isinstance(minute, int) else None

    now = datetime.utcnow()
    existing = (
        await session.execute(
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
        existing.model_version = _API_MODEL[model]
        existing.provider = provider
        existing.as_of_minute = as_of_minute
        existing.generated_at = now
        existing.updated_at = now
        row = existing
    else:
        row = MatchIntelligence(
            fixture_id=fixture_id,
            kind=kind,
            language=language,
            summary=summary,
            body=body,
            model_version=_API_MODEL[model],
            provider=provider,
            as_of_minute=as_of_minute,
            generated_at=now,
            updated_at=now,
        )
        session.add(row)

    await session.commit()
    await session.refresh(row)
    logger.info(
        "intelligence_generated",
        fixture=fixture_id,
        kind=kind.value,
        model=_API_MODEL[model],
        provider=provider,
    )
    return row
