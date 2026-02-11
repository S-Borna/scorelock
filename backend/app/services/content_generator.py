"""AI Content Engine — generates articles using Claude.

This is ScoreLock's USP: turning raw data (fixtures, standings, predictions,
odds, sentiment) into readable, SEO-friendly articles on Swedish.

Article types:
  - Match Preview:     Day before match, 400–600 words
  - Match Report:      2h after match, 300–500 words
  - Round Summary:     After round completes, 800–1200 words
  - Value Bet Alert:   Daily on matchdays, 300–400 words
  - News Rewrite:      RSS EN → original SV article
"""

import re
import unicodedata
from datetime import datetime, timezone

import anthropic
import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import async_session
from app.models.models import (
    Article, ArticleType, Fixture, League, Team, Prediction,
    Odds, Standing, SentimentScore, MatchStatus,
)
from app.services import db_service

logger = structlog.get_logger()
settings = get_settings()


# ── Slug generation ────────────────────────────────────────

def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    return text[:250]


def make_article_slug(article_type: ArticleType, context_str: str, date_str: str) -> str:
    """Create a unique slug: type-context-date."""
    return slugify(f"{article_type.value}-{context_str}-{date_str}")


# ── Claude API wrapper ─────────────────────────────────────

async def _call_claude(system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> str:
    """Call Anthropic Claude API and return the text response.

    Returns empty string on failure (never crashes content pipeline).
    """
    if not settings.anthropic_api_key:
        logger.warning("anthropic_key_missing", msg="Skipping content generation")
        return ""

    try:
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = message.content[0].text if message.content else ""
        logger.info(
            "claude_content_generated",
            tokens_in=message.usage.input_tokens,
            tokens_out=message.usage.output_tokens,
            length=len(text),
        )
        return text.strip()
    except Exception as exc:
        logger.error("claude_api_error", error=str(exc))
        return ""


# ── Data gathering helpers ─────────────────────────────────

async def _get_fixture_context(session: AsyncSession, fixture: Fixture) -> dict:
    """Gather all context data for a fixture (form, H2H, standings, odds, sentiment)."""
    # Teams
    home_team = await session.get(Team, fixture.home_team_id)
    away_team = await session.get(Team, fixture.away_team_id)
    league = await session.get(League, fixture.league_id)

    # Standing positions
    standings = await db_service.get_standings(session, fixture.league_id)
    home_standing = next((s for s in standings if s.team_id == fixture.home_team_id), None)
    away_standing = next((s for s in standings if s.team_id == fixture.away_team_id), None)

    # H2H (last 5)
    h2h = await db_service.get_h2h_fixtures(
        session, fixture.home_team_id, fixture.away_team_id, last=5
    )

    # Prediction
    prediction = await db_service.get_prediction_by_fixture(session, fixture.id)

    # Odds (latest per market)
    odds_q = await session.execute(
        select(Odds).where(Odds.fixture_id == fixture.id).order_by(Odds.fetched_at.desc())
    )
    odds_list = list(odds_q.scalars().all())

    # Sentiment
    home_sentiment = await db_service.get_team_sentiment(session, fixture.home_team_id, days=3)
    away_sentiment = await db_service.get_team_sentiment(session, fixture.away_team_id, days=3)

    def _format_form(standing) -> str:
        if not standing or not standing.form:
            return "okänd"
        return standing.form

    def _format_standing(standing) -> str:
        if not standing:
            return "ej tillgänglig"
        return (
            f"#{standing.position} ({standing.points}p, "
            f"{standing.won}V-{standing.drawn}O-{standing.lost}F, "
            f"MÅL: {standing.goals_for}-{standing.goals_against})"
        )

    def _format_h2h(fixtures: list) -> str:
        if not fixtures:
            return "Inga tidigare möten i databasen."
        lines = []
        for f in fixtures[:5]:
            ht = f.home_goals if f.home_goals is not None else "?"
            at = f.away_goals if f.away_goals is not None else "?"
            lines.append(f"  {home_team.name} {ht}–{at} {away_team.name}")
        return "\n".join(lines)

    def _format_odds(odds: list) -> str:
        h2h_odds = [o for o in odds if o.market == "1X2"]
        if not h2h_odds:
            return "Inga odds tillgängliga."
        o = h2h_odds[0]
        return f"Hemma {o.home_odds:.2f} | Oavgjort {o.draw_odds:.2f} | Borta {o.away_odds:.2f} ({o.bookmaker})"

    def _format_prediction(pred) -> str:
        if not pred:
            return "Ingen prediktion tillgänglig."
        return (
            f"Hemma {pred.home_win_prob*100:.1f}% | "
            f"Oavgjort {pred.draw_prob*100:.1f}% | "
            f"Borta {pred.away_win_prob*100:.1f}% "
            f"(konfidens {pred.confidence*100:.0f}%, xG {pred.expected_goals or 'N/A'})"
        )

    def _avg_sentiment(scores: list) -> str:
        if not scores:
            return "ingen data"
        avg = sum(s.score for s in scores) / len(scores)
        if avg > 0.2:
            return f"positiv ({avg:+.2f})"
        elif avg < -0.2:
            return f"negativ ({avg:+.2f})"
        return f"neutral ({avg:+.2f})"

    return {
        "home_team": home_team.name if home_team else "Hemmalag",
        "away_team": away_team.name if away_team else "Bortalag",
        "league_name": league.name if league else "Liga",
        "kickoff": fixture.kickoff.strftime("%Y-%m-%d %H:%M UTC"),
        "round": fixture.round or "Okänd omgång",
        "home_standing": _format_standing(home_standing),
        "away_standing": _format_standing(away_standing),
        "home_form": _format_form(home_standing),
        "away_form": _format_form(away_standing),
        "h2h": _format_h2h(h2h),
        "odds": _format_odds(odds_list),
        "prediction": _format_prediction(prediction),
        "home_sentiment": _avg_sentiment(home_sentiment),
        "away_sentiment": _avg_sentiment(away_sentiment),
        "home_goals": fixture.home_goals,
        "away_goals": fixture.away_goals,
        "home_goals_ht": fixture.home_goals_ht,
        "away_goals_ht": fixture.away_goals_ht,
        "status": fixture.status.value,
        "prediction_obj": prediction,
    }


# ── Article existence check ────────────────────────────────

async def _article_exists(session: AsyncSession, slug: str) -> bool:
    """Check if an article with this slug already exists."""
    result = await session.execute(select(Article.id).where(Article.slug == slug))
    return result.scalar_one_or_none() is not None


async def _save_article(
    session: AsyncSession,
    article_type: ArticleType,
    slug: str,
    title: str,
    body: str,
    summary: str | None = None,
    league_id: int | None = None,
    fixture_id: int | None = None,
    round_str: str | None = None,
    tags: list | None = None,
    meta_data: dict | None = None,
) -> Article | None:
    """Save an article to the database. Returns None if slug exists."""
    if await _article_exists(session, slug):
        logger.info("article_already_exists", slug=slug)
        return None

    article = Article(
        type=article_type,
        slug=slug,
        title=title,
        summary=summary,
        body=body,
        language="sv",
        league_id=league_id,
        fixture_id=fixture_id,
        round=round_str,
        tags=tags or [],
        meta_data=meta_data or {},
        auto_generated=True,
        published_at=datetime.now(timezone.utc),
    )
    session.add(article)
    await session.commit()
    await session.refresh(article)
    logger.info("article_saved", slug=slug, type=article_type.value, id=article.id)
    return article


# ══════════════════════════════════════════════════════════
# 3.3  MATCH PREVIEW
# ══════════════════════════════════════════════════════════

PREVIEW_SYSTEM = """Du är ScoreLocks AI-sportjournalist. Du skriver förhandsanalyser
av fotbollsmatcher på svenska. Din stil är kunnig, engagerande och datadriven.

Regler:
- Skriv 400–600 ord.
- Börja med en fängslande rubrik (# Rubrik).
- Inkludera: formanalys (senaste 5), inbördes möten, tabellposition, eventuella skade-/avstängningsrykten
  från sentimentdata, odds-analys, ScoreLocks ML-prognos med motivering.
- Avsluta med en tydlig prognos (t.ex. "ScoreLocks prognos: Arsenal 2–1 Chelsea").
- Om det finns value bet (modellens sannolikhet > 5% över bookmakerens), nämn det.
- Skriv INTE "Jag" eller "Vi". Skriv i tredje person (ScoreLock, modellen, analysverktyget).
- Inkludera ALDRIG affiliate-länkar eller URL:er.
- Formatera i Markdown."""

PREVIEW_USER = """Skriv en förhandsanalys för denna match:

**{home_team} vs {away_team}**
Liga: {league_name}
Omgång: {round}
Avspark: {kickoff}

**Tabellposition:**
{home_team}: {home_standing}
{away_team}: {away_standing}

**Senaste form (VOFN):**
{home_team}: {home_form}
{away_team}: {away_form}

**Inbördes möten (senaste 5):**
{h2h}

**Odds:**
{odds}

**ScoreLocks ML-prediktion:**
{prediction}

**Nyhetssentiment:**
{home_team}: {home_sentiment}
{away_team}: {away_sentiment}"""


async def generate_match_preview(session: AsyncSession, fixture: Fixture) -> Article | None:
    """Generate a match preview article for an upcoming fixture."""
    ctx = await _get_fixture_context(session, fixture)
    date_str = fixture.kickoff.strftime("%Y-%m-%d")
    slug = make_article_slug(
        ArticleType.MATCH_PREVIEW,
        f"{slugify(ctx['home_team'])}-vs-{slugify(ctx['away_team'])}",
        date_str,
    )

    if await _article_exists(session, slug):
        return None

    body = await _call_claude(
        PREVIEW_SYSTEM,
        PREVIEW_USER.format(**ctx),
        max_tokens=1500,
    )
    if not body:
        return None

    # Extract title from first markdown heading
    title = _extract_title(body) or f"{ctx['home_team']} vs {ctx['away_team']} — Förhandsanalys"
    summary = body[:200].replace("#", "").strip() + "..."

    return await _save_article(
        session,
        ArticleType.MATCH_PREVIEW,
        slug=slug,
        title=title,
        body=body,
        summary=summary,
        league_id=fixture.league_id,
        fixture_id=fixture.id,
        round_str=fixture.round,
        tags=[ctx["home_team"], ctx["away_team"], ctx["league_name"], "förhandsanalys"],
    )


# ══════════════════════════════════════════════════════════
# 3.4  MATCH REPORT
# ══════════════════════════════════════════════════════════

REPORT_SYSTEM = """Du är ScoreLocks AI-sportjournalist. Du skriver matchreferat
på svenska. Din stil är livlig, faktarik och berättande.

Regler:
- Skriv 300–500 ord.
- Börja med en fängslande rubrik (# Rubrik) som fångar matchens händelse.
- Inkludera: slutresultat, halvtidsresultat, nyckelmoment, tabellpåverkan,
  jämförelse med ScoreLocks ML-prognos.
- Om ML-prognosen var korrekt, nämn det ("ScoreLocks modell förutspådde...").
- Om den var fel, analysera varför kort.
- Skriv INTE "Jag" eller "Vi". Tredje person.
- Formatera i Markdown."""

REPORT_USER = """Skriv ett matchreferat:

**Resultat: {home_team} {home_goals}–{away_goals} {away_team}**
Halvtid: {home_goals_ht}–{away_goals_ht}
Liga: {league_name}
Omgång: {round}

**Tabellpositioner före match:**
{home_team}: {home_standing}
{away_team}: {away_standing}

**ScoreLocks ML-prediktion före match:**
{prediction}

**Nyhetssentiment (före match):**
{home_team}: {home_sentiment}
{away_team}: {away_sentiment}"""


async def generate_match_report(session: AsyncSession, fixture: Fixture) -> Article | None:
    """Generate a match report for a finished fixture."""
    if fixture.status != MatchStatus.FINISHED:
        return None
    if fixture.home_goals is None or fixture.away_goals is None:
        return None

    ctx = await _get_fixture_context(session, fixture)
    date_str = fixture.kickoff.strftime("%Y-%m-%d")
    slug = make_article_slug(
        ArticleType.MATCH_REPORT,
        f"{slugify(ctx['home_team'])}-vs-{slugify(ctx['away_team'])}",
        date_str,
    )

    if await _article_exists(session, slug):
        return None

    body = await _call_claude(
        REPORT_SYSTEM,
        REPORT_USER.format(**ctx),
        max_tokens=1200,
    )
    if not body:
        return None

    title = _extract_title(body) or f"{ctx['home_team']} {ctx['home_goals']}–{ctx['away_goals']} {ctx['away_team']}"
    summary = body[:200].replace("#", "").strip() + "..."

    return await _save_article(
        session,
        ArticleType.MATCH_REPORT,
        slug=slug,
        title=title,
        body=body,
        summary=summary,
        league_id=fixture.league_id,
        fixture_id=fixture.id,
        round_str=fixture.round,
        tags=[ctx["home_team"], ctx["away_team"], ctx["league_name"], "matchreferat"],
    )


# ══════════════════════════════════════════════════════════
# 3.5  ROUND SUMMARY
# ══════════════════════════════════════════════════════════

ROUNDUP_SYSTEM = """Du är ScoreLocks AI-sportjournalist. Du skriver omgångssammanfattningar
på svenska. Din stil är analytisk, underhållande och översiktlig.

Regler:
- Skriv 800–1200 ord.
- Börja med en rubrik (# Rubrik) som fångar omgångens tema.
- Struktur:
  1. Kort intro — omgångens narrativ (2-3 meningar)
  2. Alla resultat i en lista
  3. Omgångens hjälte (bästa prestation)
  4. Omgångens besvikelse
  5. Tabellanalys — hur ställningen ser ut nu
  6. Förhandsblick nästa omgång
- Använd fakta från indata.
- Skriv INTE "Jag" eller "Vi". Tredje person.
- Formatera i Markdown."""

ROUNDUP_USER = """Skriv en omgångssammanfattning:

**{league_name} — {round}**

**Resultat denna omgång:**
{results}

**Tabell efter omgången (topp 6):**
{standings_top}

**ScoreLocks ML-accuracy denna omgång:**
{accuracy_summary}"""


async def generate_round_summary(
    session: AsyncSession, league_id: int, round_str: str
) -> Article | None:
    """Generate a round summary article after all matches in a round are finished."""
    league = await session.get(League, league_id)
    if not league:
        return None

    slug = make_article_slug(
        ArticleType.ROUND_SUMMARY,
        f"{slugify(league.name)}-{slugify(round_str)}",
        datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    )

    if await _article_exists(session, slug):
        return None

    # Get all fixtures in this round
    fixtures_q = await session.execute(
        select(Fixture)
        .where(Fixture.league_id == league_id, Fixture.round == round_str)
        .order_by(Fixture.kickoff)
    )
    fixtures = list(fixtures_q.scalars().all())

    if not fixtures:
        return None

    # Check all are finished
    unfinished = [f for f in fixtures if f.status != MatchStatus.FINISHED]
    if unfinished:
        logger.info("round_not_complete", league=league.name, round=round_str, remaining=len(unfinished))
        return None

    # Format results
    results_lines = []
    correct_predictions = 0
    total_predictions = 0
    for f in fixtures:
        home = await session.get(Team, f.home_team_id)
        away = await session.get(Team, f.away_team_id)
        h_name = home.name if home else "?"
        a_name = away.name if away else "?"
        hg = f.home_goals if f.home_goals is not None else "?"
        ag = f.away_goals if f.away_goals is not None else "?"
        results_lines.append(f"- {h_name} {hg}–{ag} {a_name}")

        # Check prediction accuracy
        pred = await db_service.get_prediction_by_fixture(session, f.id)
        if pred and pred.was_correct is not None:
            total_predictions += 1
            if pred.was_correct:
                correct_predictions += 1

    results = "\n".join(results_lines) if results_lines else "Inga resultat."

    # Standings top 6
    standings = await db_service.get_standings(session, league_id)
    standings_lines = []
    for s in sorted(standings, key=lambda x: x.position)[:6]:
        team = await session.get(Team, s.team_id)
        t_name = team.name if team else "?"
        standings_lines.append(f"  {s.position}. {t_name} — {s.points}p ({s.won}V-{s.drawn}O-{s.lost}F)")
    standings_top = "\n".join(standings_lines) if standings_lines else "Ej tillgänglig."

    accuracy = "Ingen data." if total_predictions == 0 else (
        f"{correct_predictions}/{total_predictions} korrekta ({correct_predictions/total_predictions*100:.0f}%)"
    )

    body = await _call_claude(
        ROUNDUP_SYSTEM,
        ROUNDUP_USER.format(
            league_name=league.name,
            round=round_str,
            results=results,
            standings_top=standings_top,
            accuracy_summary=accuracy,
        ),
        max_tokens=2500,
    )
    if not body:
        return None

    title = _extract_title(body) or f"{league.name} — {round_str}: Sammanfattning"
    summary = body[:200].replace("#", "").strip() + "..."

    return await _save_article(
        session,
        ArticleType.ROUND_SUMMARY,
        slug=slug,
        title=title,
        body=body,
        summary=summary,
        league_id=league_id,
        round_str=round_str,
        tags=[league.name, round_str, "omgångssammanfattning"],
    )


# ══════════════════════════════════════════════════════════
# 3.6  VALUE BET ARTICLE
# ══════════════════════════════════════════════════════════

VALUEBET_SYSTEM = """Du är ScoreLocks AI-sportanalytiker. Du skriver value bet-analyser
på svenska. Din stil är analytisk, ärlig och balanserad.

Regler:
- Skriv 300–400 ord.
- Börja med en rubrik (# Rubrik) som fångar essensen.
- För varje value bet: förklara VARFÖR modellen ser värde (form, H2H, statistik).
- Visa modellens sannolikhet vs bookmakerens implicita sannolikhet.
- Nämn kelly criterion-andelen (hur stor del av bankrollen).
- DISCLAIMER på slutet: "Spela ansvarsfullt. Stödlinjen: 020-819 100. 18+."
- Skriv INTE "Jag" eller "Vi". Tredje person.
- Inkludera ALDRIG specifika affiliate-länkar.
- Formatera i Markdown."""

VALUEBET_USER = """Skriv en value bet-analys för dagens bästa value bets:

**Datum: {date}**

{value_bets_text}"""


async def generate_value_bet_article(session: AsyncSession) -> Article | None:
    """Generate a daily value bet alert article."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = make_article_slug(ArticleType.VALUE_BET_ALERT, "dagliga-value-bets", today)

    if await _article_exists(session, slug):
        return None

    # Get upcoming fixtures with value bets
    from datetime import date as date_type, timedelta
    tomorrow = date_type.today() + timedelta(days=1)
    fixtures_q = await session.execute(
        select(Fixture)
        .where(
            Fixture.kickoff >= datetime.now(timezone.utc),
            Fixture.kickoff <= datetime.now(timezone.utc) + timedelta(days=2),
            Fixture.status == MatchStatus.SCHEDULED,
        )
        .order_by(Fixture.kickoff)
    )
    fixtures = list(fixtures_q.scalars().all())

    value_bets = []
    for f in fixtures:
        pred = await db_service.get_prediction_by_fixture(session, f.id)
        if not pred:
            continue
        if not (pred.is_value_home or pred.is_value_draw or pred.is_value_away):
            continue

        home = await session.get(Team, f.home_team_id)
        away = await session.get(Team, f.away_team_id)
        league = await session.get(League, f.league_id)

        # Get best odds
        odds_q = await session.execute(
            select(Odds).where(Odds.fixture_id == f.id, Odds.market == "1X2")
            .order_by(Odds.fetched_at.desc()).limit(1)
        )
        odds = odds_q.scalar_one_or_none()

        vb_info = {
            "match": f"{home.name if home else '?'} vs {away.name if away else '?'}",
            "league": league.name if league else "?",
            "kickoff": f.kickoff.strftime("%H:%M"),
            "prediction": f"H {pred.home_win_prob*100:.0f}% | D {pred.draw_prob*100:.0f}% | A {pred.away_win_prob*100:.0f}%",
            "edge": f"{pred.value_edge:.1f}%" if pred.value_edge else "?",
        }

        if pred.is_value_home:
            vb_info["bet"] = f"Hemma ({odds.home_odds:.2f})" if odds and odds.home_odds else "Hemma"
        elif pred.is_value_draw:
            vb_info["bet"] = f"Oavgjort ({odds.draw_odds:.2f})" if odds and odds.draw_odds else "Oavgjort"
        else:
            vb_info["bet"] = f"Borta ({odds.away_odds:.2f})" if odds and odds.away_odds else "Borta"

        value_bets.append(vb_info)

    if not value_bets:
        logger.info("no_value_bets_for_article")
        return None

    # Format for prompt
    vb_text_parts = []
    for i, vb in enumerate(value_bets[:5], 1):  # Max 5 bets per article
        vb_text_parts.append(
            f"**{i}. {vb['match']}** ({vb['league']}, {vb['kickoff']})\n"
            f"   ML-prediktion: {vb['prediction']}\n"
            f"   Rekommendation: {vb['bet']}\n"
            f"   Edge: {vb['edge']}"
        )
    vb_text = "\n\n".join(vb_text_parts)

    body = await _call_claude(
        VALUEBET_SYSTEM,
        VALUEBET_USER.format(date=today, value_bets_text=vb_text),
        max_tokens=1000,
    )
    if not body:
        return None

    title = _extract_title(body) or f"Value Bets — {today}"
    summary = body[:200].replace("#", "").strip() + "..."

    return await _save_article(
        session,
        ArticleType.VALUE_BET_ALERT,
        slug=slug,
        title=title,
        body=body,
        summary=summary,
        tags=["value bets", today],
    )


# ══════════════════════════════════════════════════════════
# 3.7  NEWS REWRITER
# ══════════════════════════════════════════════════════════

REWRITE_SYSTEM = """Du är ScoreLocks AI-sportjournalist. Du skriver om nyhetsartiklar
till original svensk text. Du ÖVERSÄTTER INTE — du omskriver till en ny, original artikel.

Regler:
- Skriv 200–400 ord i en ny vinkel.
- Börja med en rubrik (# Rubrik) på svenska.
- Behåll alla fakta men formulera om allt med egna ord.
- Lägg till kontext där det är möjligt (tabellposition, form, etc.).
- Citera ALDRIG originalkällan ordagrant.
- Nämn källan i slutet: "(Baserat på rapportering från {source})"
- Formatera i Markdown."""

REWRITE_USER = """Omskriv denna nyhetsartikel till en original svensk text:

**Källa:** {source}
**Originalrubrik:** {title}
**Innehåll:**
{content}

**Kontext att inkludera:**
{context}"""


async def generate_news_rewrite(
    session: AsyncSession,
    source: str,
    original_title: str,
    original_content: str,
    context: str = "",
) -> Article | None:
    """Rewrite an English news article as an original Swedish article."""
    slug = make_article_slug(
        ArticleType.NEWS_REWRITE,
        slugify(original_title)[:80],
        datetime.now(timezone.utc).strftime("%Y%m%d-%H%M"),
    )

    if await _article_exists(session, slug):
        return None

    body = await _call_claude(
        REWRITE_SYSTEM,
        REWRITE_USER.format(
            source=source,
            title=original_title,
            content=original_content,
            context=context or "Ingen ytterligare kontext.",
        ),
        max_tokens=1000,
    )
    if not body:
        return None

    title = _extract_title(body) or original_title
    summary = body[:200].replace("#", "").strip() + "..."

    return await _save_article(
        session,
        ArticleType.NEWS_REWRITE,
        slug=slug,
        title=title,
        body=body,
        summary=summary,
        tags=["nyhet", source],
        meta_data={"original_source": source, "original_title": original_title},
    )


# ── Helpers ────────────────────────────────────────────────

def _extract_title(body: str) -> str | None:
    """Extract the first markdown heading from the body text."""
    for line in body.split("\n"):
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return None
