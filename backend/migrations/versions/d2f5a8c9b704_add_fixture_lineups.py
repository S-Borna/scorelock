"""add fixture_lineups + fixture_lineup_players for Phase 4 (Lineups + Pitch View)

Revision ID: d2f5a8c9b704
Revises: a3b8e1d6c405
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa


revision: str = "d2f5a8c9b704"
down_revision: str | None = "a3b8e1d6c405"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "fixture_lineups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "fixture_id",
            sa.Integer(),
            sa.ForeignKey("fixtures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("formation", sa.String(20), nullable=True),
        sa.Column("coach_name", sa.String(150), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False),
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
            name="uq_fixture_lineup_team_provider",
        ),
    )
    op.create_index(
        "ix_fixture_lineups_fixture_id",
        "fixture_lineups",
        ["fixture_id"],
    )

    op.create_table(
        "fixture_lineup_players",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "lineup_id",
            sa.Integer(),
            sa.ForeignKey("fixture_lineups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "player_id",
            sa.Integer(),
            sa.ForeignKey("players.id"),
            nullable=False,
        ),
        sa.Column("shirt_number", sa.Integer(), nullable=True),
        sa.Column("position_label", sa.String(10), nullable=True),
        sa.Column("grid_x", sa.Integer(), nullable=True),
        sa.Column("grid_y", sa.Integer(), nullable=True),
        sa.Column(
            "is_starting",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "is_captain",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "lineup_id",
            "player_id",
            name="uq_lineup_player",
        ),
    )
    op.create_index(
        "ix_fixture_lineup_players_lineup_id",
        "fixture_lineup_players",
        ["lineup_id"],
    )
    # Demo seed extracted to backend/scripts/seed_demo_data.sql — run `make seed-demo` locally.


def downgrade() -> None:
    op.drop_index(
        "ix_fixture_lineup_players_lineup_id",
        table_name="fixture_lineup_players",
    )
    op.drop_table("fixture_lineup_players")
    op.drop_index("ix_fixture_lineups_fixture_id", table_name="fixture_lineups")
    op.drop_table("fixture_lineups")
