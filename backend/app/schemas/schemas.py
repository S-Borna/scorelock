"""Pydantic schemas for API request/response validation."""

from datetime import datetime, date
from pydantic import BaseModel, EmailStr


# ── Auth ───────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    name: str | None
    tier: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Leagues ────────────────────────────────────────────────

class LeagueResponse(BaseModel):
    id: int
    name: str
    country: str
    logo_url: str | None
    type: str
    current_season: int | None

    model_config = {"from_attributes": True}


# ── Teams ──────────────────────────────────────────────────

class TeamResponse(BaseModel):
    id: int
    name: str
    short_name: str | None
    logo_url: str | None
    country: str | None

    model_config = {"from_attributes": True}


# ── Fixtures ───────────────────────────────────────────────

class FixtureResponse(BaseModel):
    id: int
    league: LeagueResponse
    home_team: TeamResponse
    away_team: TeamResponse
    kickoff: datetime
    status: str
    home_goals: int | None
    away_goals: int | None
    round: str | None

    model_config = {"from_attributes": True}


class FixtureDetail(FixtureResponse):
    """Extended fixture with stats, odds, and prediction."""
    home_goals_ht: int | None
    away_goals_ht: int | None
    stats: dict | None
    prediction: "PredictionResponse | None"
    odds: list["OddsResponse"]


# ── Odds ───────────────────────────────────────────────────

class OddsResponse(BaseModel):
    bookmaker: str
    market: str
    home_odds: float | None
    draw_odds: float | None
    away_odds: float | None
    over_odds: float | None
    under_odds: float | None
    line: float | None
    fetched_at: datetime

    model_config = {"from_attributes": True}


# ── Predictions ────────────────────────────────────────────

class PredictionResponse(BaseModel):
    fixture_id: int
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    confidence: float
    over_25_prob: float | None
    expected_goals: float | None
    is_value_home: bool
    is_value_draw: bool
    is_value_away: bool
    value_edge: float | None
    model_version: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ValueBetResponse(BaseModel):
    """A match where our model disagrees with bookmaker odds."""
    fixture: FixtureResponse
    prediction: PredictionResponse
    best_odds: OddsResponse
    edge_percent: float  # How much our model disagrees
    suggested_bet: str  # "Home", "Draw", "Away"
    kelly_fraction: float  # Suggested bet size (Kelly Criterion)


# ── Sentiment ──────────────────────────────────────────────

class SentimentResponse(BaseModel):
    team_id: int
    score: float
    buzz_score: float
    source: str
    summary: str | None
    analyzed_at: datetime

    model_config = {"from_attributes": True}


# ── Standings ──────────────────────────────────────────────

class StandingResponse(BaseModel):
    position: int
    team: TeamResponse
    points: int
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_diff: int
    form: str | None
    xg_for: float | None
    xg_against: float | None

    model_config = {"from_attributes": True}


# Rebuild models for forward references
FixtureDetail.model_rebuild()
