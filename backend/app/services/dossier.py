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
