"""v0.6a1 add reference data tables (sports, countries, seasons)

Revision ID: b6a1f5d4c302
Revises: 5b8d3a2f7e91
Create Date: 2026-04-25

Adds three additive lookup tables and seeds minimal reference rows. No changes
to existing tables. Per docs/METADATA_SCHEMA_V0.5C.md § Migration Plan v0.6a1.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b6a1f5d4c302"
down_revision: str | None = "5b8d3a2f7e91"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "sports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("icon_ref", sa.String(255), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_sports_code", "sports", ["code"], unique=True)

    op.create_table(
        "countries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("iso_2", sa.String(2), nullable=False),
        sa.Column("iso_3", sa.String(3), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("display_name_sv", sa.String(100), nullable=True),
        sa.Column("flag_ref", sa.String(255), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_countries_iso_2", "countries", ["iso_2"], unique=True)
    op.create_index("ix_countries_iso_3", "countries", ["iso_3"], unique=True)

    op.create_table(
        "seasons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "league_id",
            sa.Integer(),
            sa.ForeignKey("leagues.id"),
            nullable=False,
        ),
        sa.Column("year_start", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(20), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column(
            "is_current", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "external_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("league_id", "year_start", name="uq_season_league_year"),
    )
    op.create_index("ix_seasons_league_id", "seasons", ["league_id"])
    op.create_index("ix_season_current", "seasons", ["league_id", "is_current"])

    op.execute(
        """
        INSERT INTO sports (code, display_name, is_active, created_at)
        VALUES ('football', 'Football', true, now())
        """
    )

    op.execute(
        """
        INSERT INTO countries (iso_2, iso_3, display_name, display_name_sv, is_active, created_at) VALUES
        ('SE', 'SWE', 'Sweden', 'Sverige', true, now()),
        ('GB', 'GBR', 'United Kingdom', 'Storbritannien', true, now()),
        ('ES', 'ESP', 'Spain', 'Spanien', true, now()),
        ('IT', 'ITA', 'Italy', 'Italien', true, now()),
        ('DE', 'DEU', 'Germany', 'Tyskland', true, now()),
        ('FR', 'FRA', 'France', 'Frankrike', true, now())
        """
    )

    # Seed seasons from existing leagues with non-null current_season.
    # Label format: "YYYY/yy" where yy = last two digits of (year_start + 1).
    op.execute(
        """
        INSERT INTO seasons (league_id, year_start, label, is_current, external_ids, created_at)
        SELECT
            id,
            current_season,
            current_season::text || '/' || lpad(((current_season + 1) % 100)::text, 2, '0'),
            true,
            '{}'::jsonb,
            now()
        FROM leagues
        WHERE current_season IS NOT NULL
        ON CONFLICT (league_id, year_start) DO NOTHING
        """
    )


def downgrade() -> None:
    op.drop_index("ix_season_current", table_name="seasons")
    op.drop_index("ix_seasons_league_id", table_name="seasons")
    op.drop_table("seasons")
    op.drop_index("ix_countries_iso_3", table_name="countries")
    op.drop_index("ix_countries_iso_2", table_name="countries")
    op.drop_table("countries")
    op.drop_index("ix_sports_code", table_name="sports")
    op.drop_table("sports")
