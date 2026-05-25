"""ScoreLock-dossier: samlar all vår egen data per match till ett strukturerat
block som grundar både ScoreLock AI (ML) och ScoreLock Claude (analys).

Principen: allt Claude resonerar kring ska komma härifrån — aldrig dess egen
träningskunskap. Saknad data markeras explicit (null/"saknas") så prompten kan
flagga det i stället för att gissa.

v1: pre-match-dossier för en fixture, byggt från befintliga tabeller
(predictions, odds, fixtures, standings, teams).
"""
from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Fixture,
    FixtureEvent,
    FixtureStatistics,
    MatchStatus,
    Odds,
    Prediction,
    Standing,
    Team,
)

_FORM_N = 6


async def _recent_form(
    session: AsyncSession, team_id: int, before_kickoff, limit: int = _FORM_N
) -> list[dict]:
    """Senaste spelade matcherna för ett lag (resultat sett från lagets håll)."""
    q = (
        select(Fixture)
        .where(
            or_(Fixture.home_team_id == team_id, Fixture.away_team_id == team_id),
            Fixture.status == MatchStatus.FINISHED,
            Fixture.kickoff < before_kickoff,
        )
        .order_by(Fixture.kickoff.desc())
        .limit(limit)
    )
    rows = (await session.execute(q)).scalars().all()
    out: list[dict] = []
    for f in rows:
        is_home = f.home_team_id == team_id
        gf = (f.home_goals if is_home else f.away_goals) or 0
        ga = (f.away_goals if is_home else f.home_goals) or 0
        res = "V" if gf > ga else "O" if gf == ga else "F"
        out.append(
            {
                "datum": f.kickoff.date().isoformat() if f.kickoff else None,
                "hemma": is_home,
                "resultat": res,
                "mål": f"{gf}-{ga}",
            }
        )
    return out


async def _team_name(session: AsyncSession, team_id: int) -> str:
    t = await session.get(Team, team_id)
    return t.name if t else "?"


async def _standing(session: AsyncSession, league_id: int, team_id: int) -> dict | None:
    row = (
        await session.execute(
            select(Standing)
            .where(Standing.league_id == league_id, Standing.team_id == team_id)
            .order_by(Standing.season.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if row is None:
        return None
    ppg = round(row.points / row.played, 2) if row.played else None
    return {
        "position": row.position,
        "poäng": row.points,
        "spelade": row.played,
        "poäng_per_match": ppg,
        "mål_diff": row.goal_diff,
    }


def _implied(odds_val: float | None) -> float | None:
    return round(1.0 / odds_val, 4) if odds_val and odds_val > 0 else None


async def build_prematch_dossier(session: AsyncSession, fixture_id: int) -> dict:
    """Bygg pre-match-dossier. Returnerar strukturerad data + explicita 'saknas'."""
    fixture = await session.get(Fixture, fixture_id)
    if fixture is None:
        raise ValueError(f"Fixture {fixture_id} finns inte")

    home_name = await _team_name(session, fixture.home_team_id)
    away_name = await _team_name(session, fixture.away_team_id)

    # ScoreLock AI:s prediktion
    pred = (
        await session.execute(
            select(Prediction).where(Prediction.fixture_id == fixture_id)
        )
    ).scalar_one_or_none()
    prediction = (
        {
            "hemmavinst": round(pred.home_win_prob, 3),
            "oavgjort": round(pred.draw_prob, 3),
            "bortavinst": round(pred.away_win_prob, 3),
            "förväntade_mål_modell": pred.expected_goals,
            "over_2_5_sannolikhet": pred.over_25_prob,
            "konfidens": round(pred.confidence, 3),
            "value_edge_pct": pred.value_edge,
            "modell": pred.model_version,
        }
        if pred
        else None
    )

    # Bästa 1X2-odds + implicit sannolikhet (marknadssignal)
    odds_row = (
        await session.execute(
            select(Odds)
            .where(Odds.fixture_id == fixture_id, Odds.market == "1X2")
            .order_by(Odds.fetched_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    odds = (
        {
            "bookmaker": odds_row.bookmaker,
            "hemma": odds_row.home_odds,
            "oavgjort": odds_row.draw_odds,
            "borta": odds_row.away_odds,
            "marknad_implicit": {
                "hemma": _implied(odds_row.home_odds),
                "oavgjort": _implied(odds_row.draw_odds),
                "borta": _implied(odds_row.away_odds),
            },
        }
        if odds_row
        else None
    )

    return {
        "match": {
            "hemmalag": home_name,
            "bortalag": away_name,
            "liga_id": fixture.league_id,
            "omgång": fixture.round,
            "avspark": fixture.kickoff.isoformat() if fixture.kickoff else None,
        },
        "scorelock_ai_prediktion": prediction or "saknas (modell ej körd för matchen)",
        "odds": odds or "saknas (inga odds hämtade)",
        "form": {
            "hemmalag": await _recent_form(
                session, fixture.home_team_id, fixture.kickoff
            )
            or "saknas (för få spelade matcher i vår data)",
            "bortalag": await _recent_form(
                session, fixture.away_team_id, fixture.kickoff
            )
            or "saknas (för få spelade matcher i vår data)",
        },
        "tabell": {
            "hemmalag": await _standing(
                session, fixture.league_id, fixture.home_team_id
            )
            or "saknas",
            "bortalag": await _standing(
                session, fixture.league_id, fixture.away_team_id
            )
            or "saknas",
        },
    }


async def _events(session: AsyncSession, fixture_id: int, home_team_id: int) -> list[dict]:
    """Händelse-timeline (mål/kort/byten) i minut-ordning, sett hemma/borta."""
    rows = (
        (
            await session.execute(
                select(FixtureEvent)
                .where(FixtureEvent.fixture_id == fixture_id)
                .order_by(FixtureEvent.minute, FixtureEvent.stoppage)
            )
        )
        .scalars()
        .all()
    )
    out: list[dict] = []
    for e in rows:
        minute = f"{e.minute}'" if not e.stoppage else f"{e.minute}+{e.stoppage}'"
        out.append(
            {
                "minut": minute,
                "sida": "hemma" if e.team_id == home_team_id else "borta",
                "typ": e.event_type,
                "beskrivning": e.description or None,
            }
        )
    return out


def _stat_row(row: FixtureStatistics | None) -> dict | str:
    """Plocka ut de stat-fält vi faktiskt har; markera xG som saknad om null."""
    if row is None:
        return "saknas"
    return {
        "bollinnehav_pct": row.possession_pct,
        "skott": row.shots_total,
        "skott_på_mål": row.shots_on_target,
        "hörnor": row.corners,
        "xg": row.xg if row.xg is not None else "saknas (ej i SportMonks-planen)",
    }


async def _stats(
    session: AsyncSession, fixture_id: int, home_team_id: int, away_team_id: int
) -> dict:
    rows = (
        (
            await session.execute(
                select(FixtureStatistics).where(
                    FixtureStatistics.fixture_id == fixture_id
                )
            )
        )
        .scalars()
        .all()
    )
    by_team = {s.team_id: s for s in rows}
    return {
        "hemmalag": _stat_row(by_team.get(home_team_id)),
        "bortalag": _stat_row(by_team.get(away_team_id)),
    }


def _live_minute(fixture: Fixture, events: list[dict]) -> int | None:
    """Live-minut: helst fixturens parsade minut, annars senaste händelsens minut."""
    if fixture.live_minute is not None:
        return fixture.live_minute
    if events:
        try:
            return max(int(e["minut"].split("+")[0].rstrip("'")) for e in events)
        except (ValueError, KeyError):
            return None
    return None


async def build_inmatch_dossier(session: AsyncSession, fixture_id: int) -> dict:
    """In-match-dossier: pre-match-kontext + live ställning/minut/händelser/statistik."""
    base = await build_prematch_dossier(session, fixture_id)
    fixture = await session.get(Fixture, fixture_id)
    events = await _events(session, fixture_id, fixture.home_team_id)
    base["fas"] = "in_match"
    base["live"] = {
        "ställning": f"{fixture.home_goals or 0}-{fixture.away_goals or 0}",
        "minut": _live_minute(fixture, events) or "saknas",
        "status": fixture.status.value,
        "händelser_hittills": events or "inga registrerade händelser",
        "statistik_nu": await _stats(
            session, fixture_id, fixture.home_team_id, fixture.away_team_id
        ),
    }
    return base


async def build_postmatch_dossier(session: AsyncSession, fixture_id: int) -> dict:
    """Post-match-dossier: pre-match-kontext + slutresultat/händelser/slutstatistik +
    modellens förväntan vs faktiskt utfall."""
    base = await build_prematch_dossier(session, fixture_id)
    fixture = await session.get(Fixture, fixture_id)
    events = await _events(session, fixture_id, fixture.home_team_id)
    home_goals = fixture.home_goals or 0
    away_goals = fixture.away_goals or 0

    # Modell-förväntan vs faktiskt: jämför vår prediktion mot utfallet.
    pred = base.get("scorelock_ai_prediktion")
    modell_vs_utfall: dict | str = "saknas (ingen modell-prediktion för matchen)"
    if isinstance(pred, dict):
        faktiskt = "hemmavinst" if home_goals > away_goals else (
            "bortavinst" if away_goals > home_goals else "oavgjort"
        )
        modell_vs_utfall = {
            "modellens_troligaste": max(
                ("hemmavinst", "oavgjort", "bortavinst"),
                key=lambda k: pred.get(k, 0),
            ),
            "faktiskt_utfall": faktiskt,
            "förväntade_mål_modell": pred.get("förväntade_mål_modell"),
            "faktiska_mål_totalt": home_goals + away_goals,
        }

    base["fas"] = "post_match"
    base["slutresultat"] = f"{home_goals}-{away_goals}"
    base["händelser"] = events or "inga registrerade händelser"
    base["slutstatistik"] = await _stats(
        session, fixture_id, fixture.home_team_id, fixture.away_team_id
    )
    base["modell_vs_utfall"] = modell_vs_utfall
    return base
