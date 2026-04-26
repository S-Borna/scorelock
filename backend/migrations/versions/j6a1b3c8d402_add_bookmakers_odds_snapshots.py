"""add bookmakers + odds_snapshots for Phase 9 (value-bet ledger)

Revision ID: j6a1b3c8d402
Revises: i5c2d3e4f201
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "j6a1b3c8d402"
down_revision: str | None = "i5c2d3e4f201"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "bookmakers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("logo_ref", sa.String(500), nullable=True),
        sa.Column("license_country_id", sa.String(2), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
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
    )
    op.create_index("ix_bookmakers_code", "bookmakers", ["code"])
    op.create_index("ix_bookmakers_is_active", "bookmakers", ["is_active"])

    op.create_table(
        "odds_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "fixture_id",
            sa.Integer(),
            sa.ForeignKey("fixtures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "bookmaker_id",
            sa.Integer(),
            sa.ForeignKey("bookmakers.id"),
            nullable=False,
        ),
        sa.Column("market_code", sa.String(20), nullable=False),
        sa.Column("taken_at", sa.DateTime(), nullable=False),
        sa.Column(
            "is_in_play",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_suspended",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("market_line", sa.Float(), nullable=True),
        sa.Column("region", sa.String(10), nullable=True),
        sa.Column(
            "outcomes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_odds_snapshots_fixture_id", "odds_snapshots", ["fixture_id"])
    op.create_index("ix_odds_snapshots_market_code", "odds_snapshots", ["market_code"])
    op.create_index("ix_odds_snapshots_taken_at", "odds_snapshots", ["taken_at"])
    op.create_index(
        "ix_odds_snapshots_fixture_taken",
        "odds_snapshots",
        ["fixture_id", "taken_at"],
    )
    op.create_index(
        "ix_odds_snapshots_fixture_market_taken",
        "odds_snapshots",
        ["fixture_id", "market_code", "taken_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_odds_snapshots_fixture_market_taken", table_name="odds_snapshots")
    op.drop_index("ix_odds_snapshots_fixture_taken", table_name="odds_snapshots")
    op.drop_index("ix_odds_snapshots_taken_at", table_name="odds_snapshots")
    op.drop_index("ix_odds_snapshots_market_code", table_name="odds_snapshots")
    op.drop_index("ix_odds_snapshots_fixture_id", table_name="odds_snapshots")
    op.drop_table("odds_snapshots")
    op.drop_index("ix_bookmakers_is_active", table_name="bookmakers")
    op.drop_index("ix_bookmakers_code", table_name="bookmakers")
    op.drop_table("bookmakers")
