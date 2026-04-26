"""add fixture_statistics table for Phase 3 (Stats Panel)

Revision ID: a3b8e1d6c405
Revises: f9c2e4a7b803
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa


revision: str = "a3b8e1d6c405"
down_revision: str | None = "f9c2e4a7b803"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "fixture_statistics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "fixture_id",
            sa.Integer(),
            sa.ForeignKey("fixtures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("possession_pct", sa.Float(), nullable=True),
        sa.Column("shots_total", sa.Integer(), nullable=True),
        sa.Column("shots_on_target", sa.Integer(), nullable=True),
        sa.Column("shots_off_target", sa.Integer(), nullable=True),
        sa.Column("shots_blocked", sa.Integer(), nullable=True),
        sa.Column("corners", sa.Integer(), nullable=True),
        sa.Column("fouls", sa.Integer(), nullable=True),
        sa.Column("yellow_cards_count", sa.Integer(), nullable=True),
        sa.Column("red_cards_count", sa.Integer(), nullable=True),
        sa.Column("offsides", sa.Integer(), nullable=True),
        sa.Column("xg", sa.Float(), nullable=True),
        sa.Column("passes_total", sa.Integer(), nullable=True),
        sa.Column("passes_accurate", sa.Integer(), nullable=True),
        sa.Column("pass_accuracy_pct", sa.Float(), nullable=True),
        sa.Column("tackles", sa.Integer(), nullable=True),
        sa.Column("interceptions", sa.Integer(), nullable=True),
        sa.Column("blocks", sa.Integer(), nullable=True),
        sa.Column("clearances", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("as_of_minute", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "fixture_id",
            "team_id",
            "provider",
            name="uq_fixture_stats_team_provider",
        ),
    )
    op.create_index(
        "ix_fixture_statistics_fixture_id",
        "fixture_statistics",
        ["fixture_id"],
    )
    # Demo seed extracted to backend/scripts/seed_demo_data.sql — run `make seed-demo` locally.


def downgrade() -> None:
    op.drop_index("ix_fixture_statistics_fixture_id", table_name="fixture_statistics")
    op.drop_table("fixture_statistics")
