"""API routes for ScoreLock football analytics."""

from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.schemas import (
    FixtureResponse,
    FixtureDetail,
    PredictionResponse,
    ValueBetResponse,
    StandingResponse,
    LeagueResponse,
    SentimentResponse,
)

router = APIRouter()


# ── Health ─────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "scorelock-api"}


# ── Leagues ────────────────────────────────────────────────

@router.get("/leagues", response_model=list[LeagueResponse])
async def get_leagues():
    """Get all active leagues covered by ScoreLock."""
    # TODO: Query from database
    return []


# ── Fixtures ───────────────────────────────────────────────

@router.get("/fixtures", response_model=list[FixtureResponse])
async def get_fixtures(
    date: date | None = Query(None, description="Filter by date (YYYY-MM-DD)"),
    league_id: int | None = Query(None, description="Filter by league"),
    status: str | None = Query(None, description="Filter by status"),
):
    """Get fixtures with optional filters."""
    # TODO: Query fixtures from database with filters
    return []


@router.get("/fixtures/{fixture_id}", response_model=FixtureDetail)
async def get_fixture_detail(fixture_id: int):
    """Get full fixture detail including prediction, odds, and stats."""
    # TODO: Fetch fixture with joins on odds, predictions
    raise HTTPException(status_code=404, detail="Fixture not found")


@router.get("/fixtures/live", response_model=list[FixtureResponse])
async def get_live_fixtures():
    """Get currently live fixtures."""
    # TODO: Query fixtures where status = 'live'
    return []


# ── Predictions ────────────────────────────────────────────

@router.get("/predictions/today", response_model=list[PredictionResponse])
async def get_todays_predictions():
    """Get ML predictions for today's matches."""
    # TODO: Query predictions joined with today's fixtures
    return []


@router.get("/predictions/{fixture_id}", response_model=PredictionResponse)
async def get_prediction(fixture_id: int):
    """Get prediction for a specific fixture."""
    # TODO: Query prediction by fixture_id
    raise HTTPException(status_code=404, detail="Prediction not found")


@router.get("/predictions/accuracy")
async def get_prediction_accuracy(
    league_id: int | None = None,
    days: int = Query(30, ge=7, le=365),
):
    """Get model accuracy stats over the last N days."""
    # TODO: Calculate accuracy, Brier score, ROI from predictions table
    return {
        "period_days": days,
        "total_predictions": 0,
        "correct": 0,
        "accuracy": 0.0,
        "brier_score": 0.0,
        "roi_percent": 0.0,
    }


# ── Value Bets ─────────────────────────────────────────────

@router.get("/value-bets", response_model=list[ValueBetResponse])
async def get_value_bets(
    min_edge: float = Query(5.0, description="Minimum edge % to show"),
    league_id: int | None = None,
):
    """
    Get matches where our model identifies value vs bookmaker odds.

    A value bet exists when our model's probability > bookmaker's
    implied probability by at least `min_edge` percent.
    """
    # TODO: Query predictions where is_value_* = True and edge >= min_edge
    return []


# ── Head to Head ───────────────────────────────────────────

@router.get("/h2h/{team1_id}/{team2_id}")
async def get_head_to_head(team1_id: int, team2_id: int, last: int = 10):
    """Get head-to-head history and analysis between two teams."""
    # TODO: Query historical fixtures between these teams
    # TODO: Calculate stats (wins, goals, trends)
    return {
        "team1_id": team1_id,
        "team2_id": team2_id,
        "matches": [],
        "summary": {
            "team1_wins": 0,
            "draws": 0,
            "team2_wins": 0,
            "avg_goals": 0.0,
        },
    }


# ── Standings ──────────────────────────────────────────────

@router.get("/standings/{league_id}", response_model=list[StandingResponse])
async def get_standings(league_id: int, season: int | None = None):
    """Get league standings with xG data."""
    # TODO: Query standings from database
    return []


# ── Sentiment ──────────────────────────────────────────────

@router.get("/sentiment/{team_id}", response_model=list[SentimentResponse])
async def get_team_sentiment(team_id: int, days: int = Query(7, ge=1, le=30)):
    """Get sentiment analysis for a team over the last N days."""
    # TODO: Query sentiment scores from database
    return []


@router.get("/sentiment/match/{fixture_id}")
async def get_match_sentiment(fixture_id: int):
    """Get sentiment comparison for both teams in a fixture."""
    # TODO: Get sentiment for both teams, return comparison
    return {
        "fixture_id": fixture_id,
        "home_sentiment": None,
        "away_sentiment": None,
    }
