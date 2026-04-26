"""Pydantic schemas for API request/response validation."""

from datetime import date, datetime
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


# ── Broadcasts (Phase 1: Where to Watch) ──────────────────


class BroadcastResponse(BaseModel):
    id: int
    provider_type: str
    channel_name: str
    watch_url: str | None
    language_iso_2: str | None
    country_iso_2: str

    model_config = {"from_attributes": True}


# ── Fixture Events (Phase 2: Event Timeline) ──────────────


class FixtureEventResponse(BaseModel):
    id: int
    minute: int
    stoppage: int | None
    event_type: str
    team_id: int | None
    primary_player_name: str | None
    secondary_player_name: str | None
    player_in_name: str | None
    player_out_name: str | None
    description: str | None

    model_config = {"from_attributes": True}


# ── Fixture Statistics (Phase 3: Stats Panel) ─────────────


class FixtureStatisticsResponse(BaseModel):
    team_id: int
    possession_pct: float | None
    shots_total: int | None
    shots_on_target: int | None
    shots_off_target: int | None
    shots_blocked: int | None
    corners: int | None
    fouls: int | None
    yellow_cards_count: int | None
    red_cards_count: int | None
    offsides: int | None
    xg: float | None
    passes_total: int | None
    passes_accurate: int | None
    pass_accuracy_pct: float | None
    tackles: int | None
    interceptions: int | None
    blocks: int | None
    clearances: int | None

    model_config = {"from_attributes": True}


class FixtureStatisticsBundle(BaseModel):
    home: FixtureStatisticsResponse | None
    away: FixtureStatisticsResponse | None


# ── Fixture Lineups (Phase 4: Lineups + Pitch View) ───────


class LineupPlayerResponse(BaseModel):
    display_name: str
    shirt_number: int | None
    position_label: str | None
    grid_x: int | None
    grid_y: int | None
    is_starting: bool
    is_captain: bool

    model_config = {"from_attributes": True}


class LineupResponse(BaseModel):
    team_id: int
    formation: str | None
    coach_name: str | None
    starters: list[LineupPlayerResponse]
    substitutes: list[LineupPlayerResponse]


class FixtureLineupsBundle(BaseModel):
    home: LineupResponse | None
    away: LineupResponse | None


# ── Match Intelligence (Phase 5: AI narrative cards) ──────


class MatchIntelligenceResponse(BaseModel):
    kind: str
    language: str
    summary: str
    body: str
    model_version: str
    provider: str
    as_of_minute: int | None
    generated_at: datetime

    model_config = {"from_attributes": True}


class MatchIntelligenceBundle(BaseModel):
    pre_match: MatchIntelligenceResponse | None
    in_match: MatchIntelligenceResponse | None
    post_match: MatchIntelligenceResponse | None


# ── Fantasy Foundation (T1: seasons, gameweeks, market) ────


class FantasyGameweekResponse(BaseModel):
    id: int
    gameweek_number: int
    deadline_at: datetime
    first_kickoff_at: datetime
    last_kickoff_at: datetime
    is_finalized: bool

    model_config = {"from_attributes": True}


class FantasySeasonResponse(BaseModel):
    id: int
    name: str
    scope: str
    primary_league_id: int | None
    start_date: date
    end_date: date
    total_budget_units: int
    is_active: bool
    transfer_rules: dict
    point_weights: dict

    model_config = {"from_attributes": True}


class FantasySeasonDetailResponse(FantasySeasonResponse):
    gameweeks: list[FantasyGameweekResponse]


class FantasyPlayerMarketResponse(BaseModel):
    player_id: int
    display_name: str
    position_code: str | None
    team_id: int | None
    team_name: str | None
    team_logo_url: str | None
    league_id: int | None
    current_price: int
    starting_price: int
    value_trend: str
    selected_by_pct: float
    fantasy_points_total: int


class FantasyPlayerMarketBundle(BaseModel):
    season_id: int
    total_count: int
    players: list[FantasyPlayerMarketResponse]


# ── Fantasy Team management (T2) ──────────────────────────


class FantasyTeamPlayerEntry(BaseModel):
    player_id: int
    display_name: str
    position_code: str | None
    slot_position: str
    is_starting: bool
    purchase_price: int
    current_price: int
    team_name: str | None
    team_logo_url: str | None
    is_captain: bool
    is_vice_captain: bool


class FantasyTeamResponse(BaseModel):
    id: int
    user_id: int
    season_id: int
    name: str
    formation: str
    captain_player_id: int | None
    vice_captain_player_id: int | None
    total_points: int
    gameweek_points: int
    transfers_made_total: int
    free_transfers_available: int
    bank_balance: int
    squad_value: int
    players: list[FantasyTeamPlayerEntry]


class FantasyTeamCreateRequest(BaseModel):
    season_id: int
    name: str
    formation: str = "4-3-3"
    player_picks: list[dict]


class FantasyTeamCaptainRequest(BaseModel):
    captain_player_id: int


class FantasyTeamViceCaptainRequest(BaseModel):
    vice_captain_player_id: int


class FantasyTeamPatchRequest(BaseModel):
    name: str | None = None
    formation: str | None = None


class FantasyTransferRequest(BaseModel):
    player_in_id: int
    player_out_id: int


class FantasyTransferResponse(BaseModel):
    id: int
    team_id: int
    player_in_id: int
    player_out_id: int
    in_price: int
    out_price: int
    was_free: bool
    point_cost: int
    completed_at: datetime

    model_config = {"from_attributes": True}


# ── Fantasy AI coach (T8) ─────────────────────────────────


class FantasyAIRecommendationResponse(BaseModel):
    id: int
    kind: str
    payload: dict
    reasoning_text: str
    confidence_score: float | None
    model_version: str
    cached_until: datetime | None
    generated_at: datetime

    model_config = {"from_attributes": True}


class FantasyAIRecommendationsBundle(BaseModel):
    team_id: int
    recommendations: list[FantasyAIRecommendationResponse]
    cached: bool


# ── Match info-rad (Phase 2) ──────────────────────────────


class VenueResponse(BaseModel):
    id: int
    canonical_name: str
    display_name: str
    country_iso_2: str | None
    city: str | None
    capacity: int | None
    surface: str | None
    image_ref: str | None

    model_config = {"from_attributes": True}


class RefereeResponse(BaseModel):
    id: int
    canonical_name: str
    display_name: str
    nationality_iso_2: str | None
    career_games_count: int | None
    career_yellows_per_game: float | None
    career_reds_per_game: float | None

    model_config = {"from_attributes": True}


class MatchInfoResponse(BaseModel):
    venue: VenueResponse | None
    referee: RefereeResponse | None


# ── Bookmakers + odds-snapshots + value-bet ledger (Phase 9) ─


class BookmakerResponse(BaseModel):
    id: int
    code: str
    display_name: str
    logo_ref: str | None
    license_country_id: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class OddsSnapshotResponse(BaseModel):
    id: int
    bookmaker_code: str
    bookmaker_display: str
    market_code: str
    taken_at: datetime
    is_in_play: bool
    is_suspended: bool
    market_line: float | None
    outcomes: dict


class OddsSnapshotsBundle(BaseModel):
    fixture_id: int
    market_code: str
    snapshots: list[OddsSnapshotResponse]


class ValueBetLedgerEntry(BaseModel):
    prediction_id: int
    fixture_id: int
    home_team_name: str
    away_team_name: str
    league_name: str | None
    kickoff: datetime
    market: str
    suggested_bet: str
    model_probability: float
    best_odds: float | None
    best_bookmaker: str | None
    edge_percent: float | None
    status: str
    actual_result: str | None
    was_correct: bool | None
    model_version: str
    created_at: datetime


class ValueBetLedgerResponse(BaseModel):
    total: int
    win_count: int
    loss_count: int
    pending_count: int
    win_rate_percent: float
    avg_edge_percent: float | None
    entries: list[ValueBetLedgerEntry]


# Rebuild models for forward references
FixtureDetail.model_rebuild()
