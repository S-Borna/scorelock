"""extend leagues/teams/fixtures/standings + MatchStatus enum for Phase 7 v0.6a3

Revision ID: l8a1c4d2e605
Revises: k7d5e9f0a503
Create Date: 2026-04-27

Additive only. All new columns nullable so existing rows survive without backfill.
Backfill (sport_id/country_id/season_id from existing api_football_id-data) körs
separat i Phase 7.3 normalizer-task, inte i denna migration.

MatchStatus-enum utökas med 5 nya värden — PostgreSQL tillåter ADD VALUE men
inte DROP VALUE, så downgrade lämnar enum-värdena kvar. Acceptabelt eftersom
enum är additiv och inga rader pekar på de nya värdena förrän provider-sync
körs.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "l8a1c4d2e605"
down_revision: str | None = "k7d5e9f0a503"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # ── leagues ─────────────────────────────────────────────
    op.add_column(
        "leagues",
        sa.Column("sport_id", sa.Integer(), sa.ForeignKey("sports.id"), nullable=True),
    )
    op.add_column(
        "leagues",
        sa.Column(
            "country_id", sa.Integer(), sa.ForeignKey("countries.id"), nullable=True
        ),
    )
    op.add_column("leagues", sa.Column("tier", sa.Integer(), nullable=True))
    op.add_column("leagues", sa.Column("slug", sa.String(80), nullable=True))
    op.add_column(
        "leagues",
        sa.Column(
            "external_ids",
            JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.create_index(
        "ix_leagues_slug",
        "leagues",
        ["slug"],
        unique=True,
        postgresql_where=sa.text("slug IS NOT NULL"),
    )
    op.create_index("ix_leagues_sport_country", "leagues", ["sport_id", "country_id"])

    # ── teams ───────────────────────────────────────────────
    op.add_column(
        "teams",
        sa.Column(
            "country_id", sa.Integer(), sa.ForeignKey("countries.id"), nullable=True
        ),
    )
    op.add_column("teams", sa.Column("slug", sa.String(80), nullable=True))
    op.add_column("teams", sa.Column("color_primary", sa.String(7), nullable=True))
    op.add_column("teams", sa.Column("color_secondary", sa.String(7), nullable=True))
    op.add_column(
        "teams",
        sa.Column(
            "external_ids",
            JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column(
        "teams",
        sa.Column(
            "primary_venue_id",
            sa.Integer(),
            sa.ForeignKey("venues.id"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_teams_slug",
        "teams",
        ["slug"],
        unique=True,
        postgresql_where=sa.text("slug IS NOT NULL"),
    )

    # ── fixtures ────────────────────────────────────────────
    op.add_column(
        "fixtures",
        sa.Column(
            "season_id", sa.Integer(), sa.ForeignKey("seasons.id"), nullable=True
        ),
    )
    op.add_column(
        "fixtures",
        sa.Column("venue_id", sa.Integer(), sa.ForeignKey("venues.id"), nullable=True),
    )
    op.add_column(
        "fixtures",
        sa.Column(
            "referee_id", sa.Integer(), sa.ForeignKey("referees.id"), nullable=True
        ),
    )
    op.add_column(
        "fixtures",
        sa.Column(
            "external_ids",
            JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    op.add_column("fixtures", sa.Column("live_minute", sa.Integer(), nullable=True))
    op.add_column("fixtures", sa.Column("live_stoppage", sa.Integer(), nullable=True))
    op.add_column("fixtures", sa.Column("attendance", sa.Integer(), nullable=True))
    op.create_index("ix_fixtures_season", "fixtures", ["season_id"])

    # ── MatchStatus enum extension ──────────────────────────
    # SQLAlchemy SAEnum lagrar Python-Enum.name (UPPERCASE) i PostgreSQL — de
    # befintliga värdena är 'SCHEDULED'/'LIVE'/... så nya värden måste matcha.
    # PostgreSQL kräver COMMIT efter ADD VALUE innan värdet kan användas i
    # samma transaktion → autocommit-block.
    with op.get_context().autocommit_block():
        for value in (
            "IN_PLAY",
            "IN_PROGRESS_EXTRA_TIME",
            "IN_PROGRESS_PENALTIES",
            "SUSPENDED",
            "AWARDED",
        ):
            op.execute(
                f"ALTER TYPE matchstatus ADD VALUE IF NOT EXISTS '{value}'"
            )

    # ── standings ───────────────────────────────────────────
    op.add_column(
        "standings",
        sa.Column(
            "season_id", sa.Integer(), sa.ForeignKey("seasons.id"), nullable=True
        ),
    )
    op.add_column("standings", sa.Column("zone", sa.String(40), nullable=True))
    op.add_column("standings", sa.Column("home_played", sa.Integer(), nullable=True))
    op.add_column("standings", sa.Column("home_won", sa.Integer(), nullable=True))
    op.add_column("standings", sa.Column("home_drawn", sa.Integer(), nullable=True))
    op.add_column("standings", sa.Column("home_lost", sa.Integer(), nullable=True))
    op.add_column(
        "standings", sa.Column("home_goals_for", sa.Integer(), nullable=True)
    )
    op.add_column(
        "standings", sa.Column("home_goals_against", sa.Integer(), nullable=True)
    )
    op.add_column("standings", sa.Column("away_played", sa.Integer(), nullable=True))
    op.add_column("standings", sa.Column("away_won", sa.Integer(), nullable=True))
    op.add_column("standings", sa.Column("away_drawn", sa.Integer(), nullable=True))
    op.add_column("standings", sa.Column("away_lost", sa.Integer(), nullable=True))
    op.add_column(
        "standings", sa.Column("away_goals_for", sa.Integer(), nullable=True)
    )
    op.add_column(
        "standings", sa.Column("away_goals_against", sa.Integer(), nullable=True)
    )
    op.add_column("standings", sa.Column("provider", sa.String(50), nullable=True))
    op.create_index("ix_standings_season", "standings", ["season_id"])


def downgrade() -> None:
    # ── standings ───────────────────────────────────────────
    op.drop_index("ix_standings_season", table_name="standings")
    op.drop_column("standings", "provider")
    op.drop_column("standings", "away_goals_against")
    op.drop_column("standings", "away_goals_for")
    op.drop_column("standings", "away_lost")
    op.drop_column("standings", "away_drawn")
    op.drop_column("standings", "away_won")
    op.drop_column("standings", "away_played")
    op.drop_column("standings", "home_goals_against")
    op.drop_column("standings", "home_goals_for")
    op.drop_column("standings", "home_lost")
    op.drop_column("standings", "home_drawn")
    op.drop_column("standings", "home_won")
    op.drop_column("standings", "home_played")
    op.drop_column("standings", "zone")
    op.drop_column("standings", "season_id")

    # MatchStatus enum: PostgreSQL stödjer inte DROP VALUE. Värdena lämnas kvar
    # som dödvikt — påverkar inte funktionalitet eftersom inga rader använder
    # dem efter downgrade.

    # ── fixtures ────────────────────────────────────────────
    op.drop_index("ix_fixtures_season", table_name="fixtures")
    op.drop_column("fixtures", "attendance")
    op.drop_column("fixtures", "live_stoppage")
    op.drop_column("fixtures", "live_minute")
    op.drop_column("fixtures", "external_ids")
    op.drop_column("fixtures", "referee_id")
    op.drop_column("fixtures", "venue_id")
    op.drop_column("fixtures", "season_id")

    # ── teams ───────────────────────────────────────────────
    op.drop_index("ix_teams_slug", table_name="teams")
    op.drop_column("teams", "primary_venue_id")
    op.drop_column("teams", "external_ids")
    op.drop_column("teams", "color_secondary")
    op.drop_column("teams", "color_primary")
    op.drop_column("teams", "slug")
    op.drop_column("teams", "country_id")

    # ── leagues ─────────────────────────────────────────────
    op.drop_index("ix_leagues_sport_country", table_name="leagues")
    op.drop_index("ix_leagues_slug", table_name="leagues")
    op.drop_column("leagues", "external_ids")
    op.drop_column("leagues", "slug")
    op.drop_column("leagues", "tier")
    op.drop_column("leagues", "country_id")
    op.drop_column("leagues", "sport_id")
