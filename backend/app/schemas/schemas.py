"""Pydantic schemas for API request/response validation."""

from datetime import datetime
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


# ── Articles ───────────────────────────────────────────────

class ArticleResponse(BaseModel):
    id: int
    type: str
    slug: str
    title: str
    summary: str | None
    body: str
    language: str
    league_id: int | None
    fixture_id: int | None
    round: str | None
    tags: list | None
    auto_generated: bool
    published_at: datetime | None

    model_config = {"from_attributes": True}


class ArticleListResponse(BaseModel):
    articles: list[ArticleResponse]
    total: int
    limit: int
    offset: int


# ── Affiliate ──────────────────────────────────────────────

class AffiliateLinkResponse(BaseModel):
    id: int
    bookmaker: str
    bookmaker_display: str
    logo_url: str | None
    base_url: str
    tracking_id: str | None
    market: str
    country: str
    priority: int

    model_config = {"from_attributes": True}


class AffiliateClickCreate(BaseModel):
    link_id: int
    fixture_id: int | None = None
    page_source: str | None = None


class AffiliateClickResponse(BaseModel):
    id: int
    link_id: int
    fixture_id: int | None
    page_source: str | None
    clicked_at: datetime

    model_config = {"from_attributes": True}


class AffiliateStatsResponse(BaseModel):
    bookmaker: str
    bookmaker_display: str
    total_clicks: int
    clicks_today: int
    clicks_this_week: int
    clicks_this_month: int


# ── Tipping League ─────────────────────────────────────────

class UserPredictionCreate(BaseModel):
    fixture_id: int
    predicted_outcome: str  # "H", "D", "A"
    predicted_home_goals: int | None = None
    predicted_away_goals: int | None = None


class UserPredictionResponse(BaseModel):
    id: int
    user_id: int
    fixture_id: int
    predicted_outcome: str
    predicted_home_goals: int | None
    predicted_away_goals: int | None
    points_earned: int | None
    was_correct_outcome: bool | None
    was_exact_score: bool | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserPredictionWithFixture(UserPredictionResponse):
    fixture: FixtureResponse


class LeaderboardEntry(BaseModel):
    user_id: int
    user_name: str | None
    total_points: int
    total_tips: int
    correct_outcomes: int
    exact_scores: int
    accuracy: float  # 0-100%
    current_streak: int


class AIvsUserStats(BaseModel):
    user_total_points: int
    user_total_tips: int
    user_accuracy: float
    ai_correct: int
    ai_total: int
    ai_accuracy: float
    user_wins: int  # Tips where user beat AI
    ai_wins: int
    ties: int


class WeeklyTopTipper(BaseModel):
    user_id: int
    user_name: str | None
    points_this_week: int
    tips_this_week: int
    accuracy_this_week: float


# ── Prediction Cards (M8) ─────────────────────────────────

class PredictionCardRequest(BaseModel):
    fixture_id: int


# Rebuild models for forward references
FixtureDetail.model_rebuild()
