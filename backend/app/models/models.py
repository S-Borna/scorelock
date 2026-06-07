"""Database models for ScoreLock football analytics."""

from datetime import datetime
from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    Date,
    DateTime,
    Text,
    ForeignKey,
    UniqueConstraint,
    Index,
    Enum as SAEnum,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
import enum
from datetime import date

from app.core.database import Base


# ── Enums ──────────────────────────────────────────────────


class MatchStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    HALFTIME = "halftime"
    FINISHED = "finished"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"
    # v0.6a3: provider-rikare states
    IN_PLAY = "in_play"
    IN_PROGRESS_EXTRA_TIME = "in_progress_extra_time"
    IN_PROGRESS_PENALTIES = "in_progress_penalties"
    SUSPENDED = "suspended"
    AWARDED = "awarded"


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    ELITE = "elite"


class ArticleType(str, enum.Enum):
    MATCH_PREVIEW = "match_preview"
    MATCH_REPORT = "match_report"
    ROUND_SUMMARY = "round_summary"
    VALUE_BET_ALERT = "value_bet_alert"
    NEWS_REWRITE = "news_rewrite"


class IntelligenceKind(str, enum.Enum):
    PRE_MATCH = "pre_match"
    IN_MATCH = "in_match"
    POST_MATCH = "post_match"


class FantasyScope(str, enum.Enum):
    SINGLE_LEAGUE = "single_league"
    CROSS_EUROPEAN = "cross_european"
    WORLD_CUP = "world_cup"
    DEMO = "demo"


class FantasyValueTrend(str, enum.Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class AIRecommendationKind(str, enum.Enum):
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    CAPTAIN = "captain"
    FORMATION = "formation"


# ── Users & Auth ───────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    name: Mapped[str | None] = mapped_column(String(100))
    tier: Mapped[SubscriptionTier] = mapped_column(
        SAEnum(SubscriptionTier), default=SubscriptionTier.FREE
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255))
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    predictions_viewed: Mapped[list["PredictionView"]] = relationship(
        back_populates="user"
    )


# ── Leagues & Teams ────────────────────────────────────────


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    api_football_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    country: Mapped[str] = mapped_column(String(100))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    type: Mapped[str] = mapped_column(String(50))  # "league" or "cup"
    current_season: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    phase: Mapped[int] = mapped_column(Integer, default=1)  # Launch phase 1/2/3

    # v0.6a3 extension
    sport_id: Mapped[int | None] = mapped_column(ForeignKey("sports.id"))
    country_id: Mapped[int | None] = mapped_column(ForeignKey("countries.id"))
    tier: Mapped[int | None] = mapped_column(Integer)
    slug: Mapped[str | None] = mapped_column(String(80))
    external_ids: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )

    # Relationships
    fixtures: Mapped[list["Fixture"]] = relationship(back_populates="league")
    standings: Mapped[list["Standing"]] = relationship(back_populates="league")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    api_football_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    short_name: Mapped[str | None] = mapped_column(String(10))
    logo_url: Mapped[str | None] = mapped_column(String(500))
    country: Mapped[str | None] = mapped_column(String(100))
    venue_name: Mapped[str | None] = mapped_column(String(200))
    venue_capacity: Mapped[int | None] = mapped_column(Integer)

    # v0.6a3 extension
    country_id: Mapped[int | None] = mapped_column(ForeignKey("countries.id"))
    slug: Mapped[str | None] = mapped_column(String(80))
    color_primary: Mapped[str | None] = mapped_column(String(7))
    color_secondary: Mapped[str | None] = mapped_column(String(7))
    external_ids: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    primary_venue_id: Mapped[int | None] = mapped_column(ForeignKey("venues.id"))

    # Relationships
    home_fixtures: Mapped[list["Fixture"]] = relationship(
        back_populates="home_team", foreign_keys="Fixture.home_team_id"
    )
    away_fixtures: Mapped[list["Fixture"]] = relationship(
        back_populates="away_team", foreign_keys="Fixture.away_team_id"
    )


# ── Fixtures (Matches) ────────────────────────────────────


class Fixture(Base):
    __tablename__ = "fixtures"

    id: Mapped[int] = mapped_column(primary_key=True)
    api_football_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)

    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), index=True)
    season: Mapped[int] = mapped_column(Integer)
    round: Mapped[str | None] = mapped_column(String(50))
    stage_name: Mapped[str | None] = mapped_column(String(50))
    group_letter: Mapped[str | None] = mapped_column(String(2))

    home_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    away_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)

    kickoff: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[MatchStatus] = mapped_column(
        SAEnum(MatchStatus), default=MatchStatus.SCHEDULED
    )

    # Scores
    home_goals: Mapped[int | None] = mapped_column(Integer)
    away_goals: Mapped[int | None] = mapped_column(Integer)
    home_goals_ht: Mapped[int | None] = mapped_column(Integer)
    away_goals_ht: Mapped[int | None] = mapped_column(Integer)

    # Match statistics (stored as JSON for flexibility)
    stats: Mapped[dict | None] = mapped_column(JSONB)

    # v0.6a3 extension
    season_id: Mapped[int | None] = mapped_column(ForeignKey("seasons.id"))
    venue_id: Mapped[int | None] = mapped_column(ForeignKey("venues.id"))
    referee_id: Mapped[int | None] = mapped_column(ForeignKey("referees.id"))
    external_ids: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    live_minute: Mapped[int | None] = mapped_column(Integer)
    live_stoppage: Mapped[int | None] = mapped_column(Integer)
    attendance: Mapped[int | None] = mapped_column(Integer)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    league: Mapped["League"] = relationship(back_populates="fixtures")
    home_team: Mapped["Team"] = relationship(
        back_populates="home_fixtures", foreign_keys=[home_team_id]
    )
    away_team: Mapped["Team"] = relationship(
        back_populates="away_fixtures", foreign_keys=[away_team_id]
    )
    odds: Mapped[list["Odds"]] = relationship(back_populates="fixture")
    predictions: Mapped[list["Prediction"]] = relationship(back_populates="fixture")

    __table_args__ = (Index("ix_fixture_kickoff_league", "kickoff", "league_id"),)


# ── Odds ───────────────────────────────────────────────────


class Odds(Base):
    __tablename__ = "odds"

    id: Mapped[int] = mapped_column(primary_key=True)
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id"), index=True)
    bookmaker: Mapped[str] = mapped_column(String(100))
    market: Mapped[str] = mapped_column(String(50))  # "1X2", "Over/Under 2.5", etc.

    home_odds: Mapped[float | None] = mapped_column(Float)
    draw_odds: Mapped[float | None] = mapped_column(Float)
    away_odds: Mapped[float | None] = mapped_column(Float)

    # For over/under markets
    over_odds: Mapped[float | None] = mapped_column(Float)
    under_odds: Mapped[float | None] = mapped_column(Float)
    line: Mapped[float | None] = mapped_column(Float)  # e.g., 2.5

    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    fixture: Mapped["Fixture"] = relationship(back_populates="odds")

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "bookmaker",
            "market",
            name="uq_odds_fixture_bookmaker_market",
        ),
    )


# ── ML Predictions ─────────────────────────────────────────


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id"), index=True)

    # Model outputs (probabilities)
    home_win_prob: Mapped[float] = mapped_column(Float)
    draw_prob: Mapped[float] = mapped_column(Float)
    away_win_prob: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float)  # 0.0–1.0

    # Over/Under
    over_25_prob: Mapped[float | None] = mapped_column(Float)
    expected_goals: Mapped[float | None] = mapped_column(Float)

    # Value bet flags
    is_value_home: Mapped[bool] = mapped_column(Boolean, default=False)
    is_value_draw: Mapped[bool] = mapped_column(Boolean, default=False)
    is_value_away: Mapped[bool] = mapped_column(Boolean, default=False)
    value_edge: Mapped[float | None] = mapped_column(Float)  # Biggest edge %

    # Model metadata
    model_version: Mapped[str] = mapped_column(String(50))
    features_used: Mapped[dict | None] = mapped_column(JSONB)

    # Result tracking (filled after match)
    actual_result: Mapped[str | None] = mapped_column(String(10))  # "H", "D", "A"
    was_correct: Mapped[bool | None] = mapped_column(Boolean)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    fixture: Mapped["Fixture"] = relationship(back_populates="predictions")


# ── Sentiment ──────────────────────────────────────────────


class SentimentScore(Base):
    __tablename__ = "sentiment_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)
    fixture_id: Mapped[int | None] = mapped_column(
        ForeignKey("fixtures.id"), index=True
    )

    score: Mapped[float] = mapped_column(Float)  # -1.0 (negative) to 1.0 (positive)
    buzz_score: Mapped[float] = mapped_column(Float)  # 0.0–1.0 (how much discussed)
    source: Mapped[str] = mapped_column(String(50))  # "news", "reddit", "twitter"
    summary: Mapped[str | None] = mapped_column(Text)
    raw_data: Mapped[dict | None] = mapped_column(JSONB)

    analyzed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ── Standings ──────────────────────────────────────────────


class Standing(Base):
    __tablename__ = "standings"

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), index=True)
    season: Mapped[int] = mapped_column(Integer)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), index=True)

    position: Mapped[int] = mapped_column(Integer)
    points: Mapped[int] = mapped_column(Integer)
    played: Mapped[int] = mapped_column(Integer)
    won: Mapped[int] = mapped_column(Integer)
    drawn: Mapped[int] = mapped_column(Integer)
    lost: Mapped[int] = mapped_column(Integer)
    goals_for: Mapped[int] = mapped_column(Integer)
    goals_against: Mapped[int] = mapped_column(Integer)
    goal_diff: Mapped[int] = mapped_column(Integer)
    form: Mapped[str | None] = mapped_column(String(20))  # "WWDLW"

    # Advanced stats
    xg_for: Mapped[float | None] = mapped_column(Float)
    xg_against: Mapped[float | None] = mapped_column(Float)

    # v0.6a3 extension
    season_id: Mapped[int | None] = mapped_column(ForeignKey("seasons.id"))
    zone: Mapped[str | None] = mapped_column(String(40))
    home_played: Mapped[int | None] = mapped_column(Integer)
    home_won: Mapped[int | None] = mapped_column(Integer)
    home_drawn: Mapped[int | None] = mapped_column(Integer)
    home_lost: Mapped[int | None] = mapped_column(Integer)
    home_goals_for: Mapped[int | None] = mapped_column(Integer)
    home_goals_against: Mapped[int | None] = mapped_column(Integer)
    away_played: Mapped[int | None] = mapped_column(Integer)
    away_won: Mapped[int | None] = mapped_column(Integer)
    away_drawn: Mapped[int | None] = mapped_column(Integer)
    away_lost: Mapped[int | None] = mapped_column(Integer)
    away_goals_for: Mapped[int | None] = mapped_column(Integer)
    away_goals_against: Mapped[int | None] = mapped_column(Integer)
    provider: Mapped[str | None] = mapped_column(String(50))

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    league: Mapped["League"] = relationship(back_populates="standings")

    __table_args__ = (
        UniqueConstraint("league_id", "season", "team_id", name="uq_standing"),
    )


# ── Usage Tracking (for freemium gating) ───────────────────


class PredictionView(Base):
    __tablename__ = "prediction_views"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id"))
    viewed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="predictions_viewed")

    __table_args__ = (Index("ix_prediction_view_user_week", "user_id", "viewed_at"),)


# ── Articles (AI-generated content) ───────────────────────


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    # NOTE: lagras som VARCHAR i DB (inte PG-enum). ArticleType-värdena används i
    # appen för typsäkerhet, men SAEnum cast:ade i DB skapade drift mellan
    # kod-enum-värden ('round_summary') och DB-enum-typ → ProgrammingError vid
    # filtrering. String är säkrare och idempotent vid värde-tillägg.
    type: Mapped[str] = mapped_column(String(50), index=True)
    slug: Mapped[str] = mapped_column(String(300), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(5), default="sv")  # ISO 639-1

    # Linked entities (optional — not every article type has all)
    league_id: Mapped[int | None] = mapped_column(ForeignKey("leagues.id"), index=True)
    fixture_id: Mapped[int | None] = mapped_column(
        ForeignKey("fixtures.id"), index=True
    )
    round: Mapped[str | None] = mapped_column(String(50))

    # Metadata
    tags: Mapped[list | None] = mapped_column(JSONB)
    meta_data: Mapped[dict | None] = mapped_column(
        JSONB
    )  # model_version, prompt tokens, etc.
    auto_generated: Mapped[bool] = mapped_column(Boolean, default=True)

    published_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    league: Mapped["League | None"] = relationship()
    fixture: Mapped["Fixture | None"] = relationship()

    __table_args__ = (
        Index("ix_article_type_league", "type", "league_id"),
        Index("ix_article_published", "published_at"),
    )


# ── Affiliate Links ───────────────────────────────────────


class AffiliateLink(Base):
    __tablename__ = "affiliate_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    bookmaker: Mapped[str] = mapped_column(
        String(100), index=True
    )  # e.g. "bet365", "unibet"
    bookmaker_display: Mapped[str] = mapped_column(
        String(100)
    )  # e.g. "Bet365", "Unibet"
    logo_url: Mapped[str | None] = mapped_column(String(500))
    base_url: Mapped[str] = mapped_column(String(1000))  # Affiliate URL with tracking
    tracking_id: Mapped[str | None] = mapped_column(
        String(255)
    )  # Our affiliate tracking ID
    market: Mapped[str] = mapped_column(String(50), default="1X2")  # market type
    country: Mapped[str] = mapped_column(String(5), default="SE")  # SE, UK, etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)  # Higher = shown first

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    clicks: Mapped[list["AffiliateClick"]] = relationship(back_populates="link")


class AffiliateClick(Base):
    __tablename__ = "affiliate_clicks"

    id: Mapped[int] = mapped_column(primary_key=True)
    link_id: Mapped[int] = mapped_column(ForeignKey("affiliate_links.id"), index=True)
    fixture_id: Mapped[int | None] = mapped_column(
        ForeignKey("fixtures.id"), index=True
    )
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    page_source: Mapped[str | None] = mapped_column(
        String(100)
    )  # "value-bets", "article", "match"
    ip_hash: Mapped[str | None] = mapped_column(
        String(64)
    )  # Hashed IP for analytics (GDPR)
    user_agent: Mapped[str | None] = mapped_column(String(500))
    clicked_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    # Relationships
    link: Mapped["AffiliateLink"] = relationship(back_populates="clicks")

    __table_args__ = (Index("ix_affiliate_click_link_date", "link_id", "clicked_at"),)


# ── Tipping League (User Predictions) ─────────────────────


class UserPrediction(Base):
    __tablename__ = "user_predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id"), index=True)

    predicted_outcome: Mapped[str] = mapped_column(String(5))  # "H", "D", "A"
    predicted_home_goals: Mapped[int | None] = mapped_column(
        Integer
    )  # Exact score (optional)
    predicted_away_goals: Mapped[int | None] = mapped_column(Integer)

    # Scoring (filled after match finishes)
    points_earned: Mapped[int | None] = mapped_column(
        Integer
    )  # 3=exact, 1=correct outcome, 0=wrong
    was_correct_outcome: Mapped[bool | None] = mapped_column(Boolean)
    was_exact_score: Mapped[bool | None] = mapped_column(Boolean)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    scored_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Relationships
    user: Mapped["User"] = relationship()
    fixture: Mapped["Fixture"] = relationship()

    __table_args__ = (
        UniqueConstraint("user_id", "fixture_id", name="uq_user_fixture_prediction"),
        Index("ix_user_pred_user_created", "user_id", "created_at"),
    )


# ── Reference Data (v0.6a1) ────────────────────────────────


class Sport(Base):
    """Top-level sport lookup. Football-only at launch; multi-sport extensibility per provider abstraction."""

    __tablename__ = "sports"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    icon_ref: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Country(Base):
    """ISO 3166-1 country lookup. Used by competitions, teams, players, referees, venues, broadcasts."""

    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(primary_key=True)
    iso_2: Mapped[str] = mapped_column(String(2), unique=True, index=True)
    iso_3: Mapped[str] = mapped_column(String(3), unique=True)
    display_name: Mapped[str] = mapped_column(String(100))
    display_name_sv: Mapped[str | None] = mapped_column(String(100))
    flag_ref: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Season(Base):
    """Season identity per league. Replaces denormalized season INT column on fixtures/standings.

    FK points at `leagues.id` for now. The `leagues` table is the canonical lookup
    through v0.6f; the rename to `competitions` is deferred to v0.7+ per
    docs/METADATA_SCHEMA_V0.5C.md.
    """

    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(primary_key=True)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), index=True)
    year_start: Mapped[int] = mapped_column(Integer)
    label: Mapped[str] = mapped_column(String(20))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    external_ids: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("league_id", "year_start", name="uq_season_league_year"),
        Index("ix_season_current", "league_id", "is_current"),
    )


# ── Provider Identity / Audit (v0.6a2) ─────────────────────


class ProviderPayload(Base):
    """Immutable raw provider response store.

    Source-of-truth for replay-normalization, conflict debugging, legal evidence.
    Regular Postgres table in v0.6; hypertable promotion deferred to v0.7+ per
    docs/METADATA_SCHEMA_V0.5C.md.
    """

    __tablename__ = "provider_payloads"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(50), index=True)
    operation: Mapped[str] = mapped_column(String(50), index=True)
    entity_type: Mapped[str] = mapped_column(String(20), index=True)
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)
    canonical_table: Mapped[str | None] = mapped_column(String(50))
    canonical_id: Mapped[int | None] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSONB)
    payload_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    retained_until: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    is_schema_drift: Mapped[bool] = mapped_column(Boolean, default=False)
    error_summary: Mapped[str | None] = mapped_column(Text)


class ProviderEntityMapping(Base):
    """Provider external-ID ↔ canonical internal-ID mapping.

    Truth source for provider identity. One row per (provider, entity_type, external_id)
    triple. Reverse lookup via (canonical_table, canonical_id).
    """

    __tablename__ = "provider_entity_mappings"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(50), index=True)
    entity_type: Mapped[str] = mapped_column(String(20), index=True)
    external_id: Mapped[str] = mapped_column(String(255))
    canonical_table: Mapped[str] = mapped_column(String(50))
    canonical_id: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "entity_type",
            "external_id",
            name="uq_provider_entity_external",
        ),
        Index("ix_pem_canonical", "canonical_table", "canonical_id"),
        Index("ix_pem_provider_entity", "provider", "entity_type"),
    )


class ProviderConflict(Base):
    """Provider field-divergence log.

    Written when two providers report conflicting values for the same canonical
    entity field. Surfaced in admin UI for resolution.
    """

    __tablename__ = "provider_conflicts"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(50), index=True)
    entity_type: Mapped[str] = mapped_column(String(20), index=True)
    external_id: Mapped[str | None] = mapped_column(String(255))
    canonical_table: Mapped[str | None] = mapped_column(String(50))
    canonical_id: Mapped[int | None] = mapped_column(Integer)
    field_name: Mapped[str] = mapped_column(String(100))
    existing_value: Mapped[dict | None] = mapped_column(JSONB)
    incoming_value: Mapped[dict | None] = mapped_column(JSONB)
    severity: Mapped[str] = mapped_column(String(20), default="medium")
    status: Mapped[str] = mapped_column(String(20), default="open")
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    resolution_notes: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index("ix_pc_status_severity", "status", "severity"),
        Index("ix_pc_canonical", "canonical_table", "canonical_id"),
    )


# ── Commentary + Momentum + MOTM-poll (Phase 10) ──────────


class FixtureCommentary(Base):
    """Live commentary feed for a fixture. Bilingual (sv + en)."""

    __tablename__ = "fixture_commentary"

    id: Mapped[int] = mapped_column(primary_key=True)
    fixture_id: Mapped[int] = mapped_column(
        ForeignKey("fixtures.id", ondelete="CASCADE"), index=True
    )
    minute: Mapped[int] = mapped_column(Integer)
    stoppage: Mapped[int | None] = mapped_column(Integer)
    comment_type: Mapped[str] = mapped_column(String(30))
    text_en: Mapped[str | None] = mapped_column(Text)
    text_sv: Mapped[str | None] = mapped_column(Text)
    is_translated: Mapped[bool] = mapped_column(Boolean, default=False)
    provider: Mapped[str] = mapped_column(String(50))
    external_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "provider",
            "external_id",
            name="uq_commentary_provider_external",
        ),
        Index(
            "ix_commentary_fixture_minute",
            "fixture_id",
            "minute",
            "stoppage",
        ),
    )


class FixtureMomentum(Base):
    """Time-series of pressure / momentum per fixture.

    `home_momentum_pct + away_momentum_pct` should sum to ~100. Source can be
    provider-supplied or derived from event-stream + xG.
    """

    __tablename__ = "fixture_momentum"

    id: Mapped[int] = mapped_column(primary_key=True)
    fixture_id: Mapped[int] = mapped_column(
        ForeignKey("fixtures.id", ondelete="CASCADE"), index=True
    )
    observed_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    match_minute: Mapped[int] = mapped_column(Integer)
    match_stoppage: Mapped[int | None] = mapped_column(Integer)
    home_momentum_pct: Mapped[float] = mapped_column(Float)
    away_momentum_pct: Mapped[float] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(20))
    provider: Mapped[str] = mapped_column(String(50))
    derivation_window_seconds: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index(
            "ix_momentum_fixture_minute",
            "fixture_id",
            "match_minute",
            "match_stoppage",
        ),
    )


class UserMOTMVote(Base):
    """User's Man of the Match vote per fixture. One vote per user per fixture."""

    __tablename__ = "user_motm_votes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    fixture_id: Mapped[int] = mapped_column(
        ForeignKey("fixtures.id", ondelete="CASCADE"), index=True
    )
    voted_player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    voted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        UniqueConstraint("user_id", "fixture_id", name="uq_motm_vote_user_fixture"),
    )


# ── Bookmakers + Odds-snapshots (Phase 9: value-bet ledger) ─


class Bookmaker(Base):
    """Sportsbook source for odds. Our model compares against these."""

    __tablename__ = "bookmakers"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    logo_ref: Mapped[str | None] = mapped_column(String(500))
    license_country_id: Mapped[str | None] = mapped_column(String(2))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    external_ids: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class OddsSnapshot(Base):
    """One snapshot of a bookmaker's odds for a (fixture, market) at a point in time.

    Regular table for now. Hypertable promotion (TimescaleDB) deferred to v0.7+
    once Railway-prod TimescaleDB-extension is verified.

    `outcomes` JSONB shape per market:
      H2H: {home: 1.85, draw: 3.40, away: 4.50}
      TOTALS: {over: 1.95, under: 1.85, line: 2.5}
      BTTS: {yes: 1.75, no: 2.10}
    """

    __tablename__ = "odds_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    fixture_id: Mapped[int] = mapped_column(
        ForeignKey("fixtures.id", ondelete="CASCADE"), index=True
    )
    bookmaker_id: Mapped[int] = mapped_column(ForeignKey("bookmakers.id"))
    market_code: Mapped[str] = mapped_column(String(20), index=True)
    taken_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    is_in_play: Mapped[bool] = mapped_column(Boolean, default=False)
    is_suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    market_line: Mapped[float | None] = mapped_column(Float)
    region: Mapped[str | None] = mapped_column(String(10))
    outcomes: Mapped[dict] = mapped_column(JSONB)
    provider: Mapped[str] = mapped_column(String(50))
    external_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index(
            "ix_odds_snapshots_fixture_taken",
            "fixture_id",
            "taken_at",
        ),
        Index(
            "ix_odds_snapshots_fixture_market_taken",
            "fixture_id",
            "market_code",
            "taken_at",
        ),
    )


# ── Venue + Referee (Phase 2: Match info-rad) ──────────────


class Venue(Base):
    """Stadium / arena. Used by fixtures for "match info"-rad on match-detail."""

    __tablename__ = "venues"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(150), index=True)
    display_name: Mapped[str] = mapped_column(String(150))
    country_iso_2: Mapped[str | None] = mapped_column(String(2), index=True)
    city: Mapped[str | None] = mapped_column(String(100))
    capacity: Mapped[int | None] = mapped_column(Integer)
    surface: Mapped[str | None] = mapped_column(String(50))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    image_ref: Mapped[str | None] = mapped_column(String(500))
    external_ids: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Referee(Base):
    """Match referee. Career stats may be null until provider data is wired."""

    __tablename__ = "referees"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(150), index=True)
    display_name: Mapped[str] = mapped_column(String(150))
    nationality_iso_2: Mapped[str | None] = mapped_column(String(2))
    career_games_count: Mapped[int | None] = mapped_column(Integer)
    career_yellows_per_game: Mapped[float | None] = mapped_column(Float)
    career_reds_per_game: Mapped[float | None] = mapped_column(Float)
    external_ids: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FixtureMatchInfo(Base):
    """Lightweight (fixture, venue, referee) mapping table.

    Will be replaced by direct FK columns on `fixtures` in Phase 7 (v0.6a3).
    For now this avoids touching the fixtures schema before provider integration.
    """

    __tablename__ = "fixture_match_info"

    id: Mapped[int] = mapped_column(primary_key=True)
    fixture_id: Mapped[int] = mapped_column(
        ForeignKey("fixtures.id", ondelete="CASCADE"), unique=True, index=True
    )
    venue_id: Mapped[int | None] = mapped_column(ForeignKey("venues.id"))
    referee_id: Mapped[int | None] = mapped_column(ForeignKey("referees.id"))
    provider: Mapped[str] = mapped_column(String(50), default="manual_seed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


# ── Broadcasts (Phase 1: Where to Watch) ───────────────────


class FixtureBroadcast(Base):
    """TV / streaming / radio broadcast info per (fixture, country).

    `country_iso_2` is a string (not FK to countries) for Phase 1 simplicity.
    `affiliate_link_id` deferred — TV affiliates not modeled yet.
    """

    __tablename__ = "fixture_broadcasts"

    id: Mapped[int] = mapped_column(primary_key=True)
    fixture_id: Mapped[int] = mapped_column(
        ForeignKey("fixtures.id", ondelete="CASCADE"), index=True
    )
    country_iso_2: Mapped[str] = mapped_column(String(2), index=True)
    provider_type: Mapped[str] = mapped_column(String(20))
    channel_name: Mapped[str] = mapped_column(String(150))
    watch_url: Mapped[str | None] = mapped_column(String(1000))
    language_iso_2: Mapped[str | None] = mapped_column(String(2))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index(
            "ix_fixture_broadcasts_fixture_country",
            "fixture_id",
            "country_iso_2",
        ),
    )


# ── Players + Events (Phase 2: Event Timeline) ─────────────


class Player(Base):
    """Player identity (minimal for Phase 2 — extended in later phases)."""

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(150), index=True)
    display_name: Mapped[str] = mapped_column(String(150))
    position_code: Mapped[str | None] = mapped_column(String(10))
    current_team_id: Mapped[int | None] = mapped_column(
        ForeignKey("teams.id"), index=True
    )
    external_ids: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class FixtureEvent(Base):
    """Match event timeline row. Goals, cards, subs, VAR — minute-ordered, append-only."""

    __tablename__ = "fixture_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    fixture_id: Mapped[int] = mapped_column(
        ForeignKey("fixtures.id", ondelete="CASCADE"), index=True
    )
    minute: Mapped[int] = mapped_column(Integer)
    stoppage: Mapped[int | None] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(30), index=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    primary_player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    secondary_player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    player_in_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    player_out_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    description: Mapped[str | None] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String(50))
    external_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "provider",
            "external_id",
            name="uq_fixture_event_provider_external",
        ),
        Index(
            "ix_fixture_events_fixture_minute",
            "fixture_id",
            "minute",
            "stoppage",
        ),
    )


# ── Fantasy Foundation (T1: seasons, gameweeks, pricing) ──


class FantasySeason(Base):
    """A fantasy season — single league, cross-european, world cup, or demo."""

    __tablename__ = "fantasy_seasons"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    scope: Mapped[FantasyScope] = mapped_column(
        SAEnum(
            FantasyScope,
            name="fantasyscope",
            values_callable=lambda c: [e.value for e in c],
        ),
        index=True,
    )
    primary_league_id: Mapped[int | None] = mapped_column(ForeignKey("leagues.id"))
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    total_budget_units: Mapped[int] = mapped_column(Integer, default=1000)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    transfer_rules: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    point_weights: Mapped[dict] = mapped_column(
        JSONB, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FantasyGameweek(Base):
    """A single matchweek within a fantasy season."""

    __tablename__ = "fantasy_gameweeks"

    id: Mapped[int] = mapped_column(primary_key=True)
    season_id: Mapped[int] = mapped_column(
        ForeignKey("fantasy_seasons.id", ondelete="CASCADE"), index=True
    )
    gameweek_number: Mapped[int] = mapped_column(Integer)
    deadline_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    first_kickoff_at: Mapped[datetime] = mapped_column(DateTime)
    last_kickoff_at: Mapped[datetime] = mapped_column(DateTime)
    is_finalized: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    __table_args__ = (
        UniqueConstraint(
            "season_id", "gameweek_number", name="uq_fantasy_gameweek_number"
        ),
    )


class FantasyGameweekFixture(Base):
    """Maps real fixtures to fantasy gameweeks (many-to-one)."""

    __tablename__ = "fantasy_gameweek_fixtures"

    id: Mapped[int] = mapped_column(primary_key=True)
    gameweek_id: Mapped[int] = mapped_column(
        ForeignKey("fantasy_gameweeks.id", ondelete="CASCADE"), index=True
    )
    fixture_id: Mapped[int] = mapped_column(
        ForeignKey("fixtures.id", ondelete="CASCADE"), index=True
    )

    __table_args__ = (
        UniqueConstraint("gameweek_id", "fixture_id", name="uq_fantasy_gw_fixture"),
    )


class FantasyPlayerPricing(Base):
    """Per-season per-player pricing + ownership state.

    Price units: 10 = €1.0M (e.g. 50 = €5.0M, 145 = €14.5M).
    """

    __tablename__ = "fantasy_player_pricing"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    season_id: Mapped[int] = mapped_column(
        ForeignKey("fantasy_seasons.id", ondelete="CASCADE"), index=True
    )
    current_price: Mapped[int] = mapped_column(Integer)
    starting_price: Mapped[int] = mapped_column(Integer)
    last_change_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    value_trend: Mapped[FantasyValueTrend] = mapped_column(
        SAEnum(
            FantasyValueTrend,
            name="fantasyvaluetrend",
            values_callable=lambda c: [e.value for e in c],
        ),
        default=FantasyValueTrend.STABLE,
    )
    selected_by_pct: Mapped[float] = mapped_column(Float, default=0.0)
    fantasy_points_total: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint("player_id", "season_id", name="uq_fantasy_player_pricing"),
    )


class FantasyPlayerGameweekStats(Base):
    """Per-(player, gameweek, fixture) stats and computed fantasy points.

    Fantasy points calculated by app.services.fantasy_scoring.compute_points().
    """

    __tablename__ = "fantasy_player_gameweek_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    gameweek_id: Mapped[int] = mapped_column(
        ForeignKey("fantasy_gameweeks.id", ondelete="CASCADE"), index=True
    )
    fixture_id: Mapped[int] = mapped_column(
        ForeignKey("fixtures.id", ondelete="CASCADE")
    )
    minutes_played: Mapped[int] = mapped_column(Integer, default=0)
    goals: Mapped[int] = mapped_column(Integer, default=0)
    assists: Mapped[int] = mapped_column(Integer, default=0)
    clean_sheet: Mapped[bool] = mapped_column(Boolean, default=False)
    yellow_cards: Mapped[int] = mapped_column(Integer, default=0)
    red_cards: Mapped[int] = mapped_column(Integer, default=0)
    saves: Mapped[int] = mapped_column(Integer, default=0)
    goals_conceded: Mapped[int] = mapped_column(Integer, default=0)
    own_goals: Mapped[int] = mapped_column(Integer, default=0)
    penalties_missed: Mapped[int] = mapped_column(Integer, default=0)
    penalties_saved: Mapped[int] = mapped_column(Integer, default=0)
    bonus_points: Mapped[int] = mapped_column(Integer, default=0)
    points_earned: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        UniqueConstraint(
            "player_id",
            "gameweek_id",
            "fixture_id",
            name="uq_fantasy_player_gw_stats",
        ),
    )


# ── Fantasy Team management (T2) ──────────────────────────


class FantasyTeam(Base):
    """A user's fantasy team for one season. Squad of 15 (2 GK, 5 DEF, 5 MID, 3 FWD)."""

    __tablename__ = "fantasy_teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    season_id: Mapped[int] = mapped_column(
        ForeignKey("fantasy_seasons.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(150))
    formation: Mapped[str] = mapped_column(String(20), default="4-3-3")
    captain_player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    vice_captain_player_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    gameweek_points: Mapped[int] = mapped_column(Integer, default=0)
    transfers_made_total: Mapped[int] = mapped_column(Integer, default=0)
    free_transfers_available: Mapped[int] = mapped_column(Integer, default=1)
    bank_balance: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint("user_id", "season_id", name="uq_fantasy_team_user_season"),
    )


class FantasyTeamPlayer(Base):
    """One player in a fantasy team. Squad position (GK/DEF/MID/FWD) + starting flag."""

    __tablename__ = "fantasy_team_players"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(
        ForeignKey("fantasy_teams.id", ondelete="CASCADE"), index=True
    )
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    slot_position: Mapped[str] = mapped_column(String(10))
    is_starting: Mapped[bool] = mapped_column(Boolean, default=True)
    purchase_price: Mapped[int] = mapped_column(Integer)

    __table_args__ = (
        UniqueConstraint("team_id", "player_id", name="uq_fantasy_team_player"),
    )


class FantasyAIRecommendation(Base):
    """AI coach recommendation for a fantasy team — transfer / captain / formation rec."""

    __tablename__ = "fantasy_ai_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(
        ForeignKey("fantasy_teams.id", ondelete="CASCADE"), index=True
    )
    gameweek_id: Mapped[int | None] = mapped_column(
        ForeignKey("fantasy_gameweeks.id"), index=True
    )
    kind: Mapped[AIRecommendationKind] = mapped_column(
        SAEnum(
            AIRecommendationKind,
            name="airecommendationkind",
            values_callable=lambda c: [e.value for e in c],
        ),
        index=True,
    )
    payload: Mapped[dict] = mapped_column(JSONB)
    reasoning_text: Mapped[str] = mapped_column(Text)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(50))
    cached_until: Mapped[datetime | None] = mapped_column(DateTime)
    was_acted_upon: Mapped[bool | None] = mapped_column(Boolean)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


class FantasyTransfer(Base):
    """A single transfer event — player_out swapped for player_in."""

    __tablename__ = "fantasy_transfers"

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(
        ForeignKey("fantasy_teams.id", ondelete="CASCADE"), index=True
    )
    gameweek_id: Mapped[int | None] = mapped_column(ForeignKey("fantasy_gameweeks.id"))
    player_in_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    player_out_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    in_price: Mapped[int] = mapped_column(Integer)
    out_price: Mapped[int] = mapped_column(Integer)
    was_free: Mapped[bool] = mapped_column(Boolean, default=True)
    point_cost: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ── Match Intelligence (Phase 5: AI narrative cards) ───────


class MatchIntelligence(Base):
    """AI-generated narrative analysis per (fixture, kind, language).

    Three kinds: pre-match (day before), in-match (live during,
    pinned to as_of_minute), post-match (within 24h after final whistle).
    Idempotent insert — UNIQUE(fixture_id, kind, language).
    """

    __tablename__ = "match_intelligence"

    id: Mapped[int] = mapped_column(primary_key=True)
    fixture_id: Mapped[int] = mapped_column(
        ForeignKey("fixtures.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[IntelligenceKind] = mapped_column(
        SAEnum(
            IntelligenceKind,
            name="intelligencekind",
            values_callable=lambda enum_cls: [e.value for e in enum_cls],
        ),
        index=True,
    )
    language: Mapped[str] = mapped_column(String(5), default="sv")
    summary: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text)
    model_version: Mapped[str] = mapped_column(String(50))
    provider: Mapped[str] = mapped_column(String(50))
    as_of_minute: Mapped[int | None] = mapped_column(Integer)
    generated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "kind",
            "language",
            name="uq_match_intelligence_kind_lang",
        ),
        Index("ix_match_intel_fixture_kind", "fixture_id", "kind"),
    )


# ── Lineups (Phase 4: Lineups + Pitch View) ────────────────


class FixtureLineup(Base):
    """Per-team starting lineup metadata for a fixture (formation + coach)."""

    __tablename__ = "fixture_lineups"

    id: Mapped[int] = mapped_column(primary_key=True)
    fixture_id: Mapped[int] = mapped_column(
        ForeignKey("fixtures.id", ondelete="CASCADE"), index=True
    )
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    formation: Mapped[str | None] = mapped_column(String(20))
    coach_name: Mapped[str | None] = mapped_column(String(150))
    provider: Mapped[str] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "team_id",
            "provider",
            name="uq_fixture_lineup_team_provider",
        ),
    )


class FixtureLineupPlayer(Base):
    """One row per player in a lineup (starter or substitute).

    Pitch position lives in (grid_x, grid_y) — 0–100 per side, where (50, 5) is GK
    near own goal and (50, 85) is striker. Frontend mirrors away-side coordinates.
    """

    __tablename__ = "fixture_lineup_players"

    id: Mapped[int] = mapped_column(primary_key=True)
    lineup_id: Mapped[int] = mapped_column(
        ForeignKey("fixture_lineups.id", ondelete="CASCADE"), index=True
    )
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    shirt_number: Mapped[int | None] = mapped_column(Integer)
    position_label: Mapped[str | None] = mapped_column(String(10))
    grid_x: Mapped[int | None] = mapped_column(Integer)
    grid_y: Mapped[int | None] = mapped_column(Integer)
    is_starting: Mapped[bool] = mapped_column(Boolean, default=True)
    is_captain: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            "lineup_id",
            "player_id",
            name="uq_lineup_player",
        ),
    )


# ── Fixture Statistics (Phase 3: Stats Panel) ──────────────


class FixtureStatistics(Base):
    """Aggregated match statistics per (fixture, team). One row per team per fixture per provider."""

    __tablename__ = "fixture_statistics"

    id: Mapped[int] = mapped_column(primary_key=True)
    fixture_id: Mapped[int] = mapped_column(
        ForeignKey("fixtures.id", ondelete="CASCADE"), index=True
    )
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    possession_pct: Mapped[float | None] = mapped_column(Float)
    shots_total: Mapped[int | None] = mapped_column(Integer)
    shots_on_target: Mapped[int | None] = mapped_column(Integer)
    shots_off_target: Mapped[int | None] = mapped_column(Integer)
    shots_blocked: Mapped[int | None] = mapped_column(Integer)
    corners: Mapped[int | None] = mapped_column(Integer)
    fouls: Mapped[int | None] = mapped_column(Integer)
    yellow_cards_count: Mapped[int | None] = mapped_column(Integer)
    red_cards_count: Mapped[int | None] = mapped_column(Integer)
    offsides: Mapped[int | None] = mapped_column(Integer)
    xg: Mapped[float | None] = mapped_column(Float)
    passes_total: Mapped[int | None] = mapped_column(Integer)
    passes_accurate: Mapped[int | None] = mapped_column(Integer)
    pass_accuracy_pct: Mapped[float | None] = mapped_column(Float)
    tackles: Mapped[int | None] = mapped_column(Integer)
    interceptions: Mapped[int | None] = mapped_column(Integer)
    blocks: Mapped[int | None] = mapped_column(Integer)
    clearances: Mapped[int | None] = mapped_column(Integer)
    provider: Mapped[str] = mapped_column(String(50))
    as_of_minute: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "fixture_id",
            "team_id",
            "provider",
            name="uq_fixture_stats_team_provider",
        ),
    )


# ── Matchrum (hangout / Steg 4) ────────────────────────────


class MatchRoomMessage(Base):
    """Ett chattmeddelande i en matchs hangout-rum. Rummet = fixture.

    Reaktioner och närvaro är ephemeral (Redis) — bara textmeddelanden
    persisteras här. Append-only; moderation via is_deleted (soft-delete).
    """

    __tablename__ = "match_room_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    fixture_id: Mapped[int] = mapped_column(ForeignKey("fixtures.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    body: Mapped[str] = mapped_column(Text)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    __table_args__ = (
        Index("ix_room_messages_fixture_created", "fixture_id", "created_at"),
    )
