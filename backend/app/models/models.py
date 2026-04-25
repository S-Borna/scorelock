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

    __table_args__ = (Index("ix_odds_fixture_bookmaker", "fixture_id", "bookmaker"),)


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
    type: Mapped[ArticleType] = mapped_column(SAEnum(ArticleType), index=True)
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
