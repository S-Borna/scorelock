"""add fantasy team management tables for T2 (teams + team_players + transfers)

Revision ID: g3a8b1c5d502
Revises: f9a4c1e8b305
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa


revision: str = "g3a8b1c5d502"
down_revision: str | None = "f9a4c1e8b305"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "fantasy_teams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "season_id",
            sa.Integer(),
            sa.ForeignKey("fantasy_seasons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column(
            "formation",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'4-3-3'"),
        ),
        sa.Column(
            "captain_player_id",
            sa.Integer(),
            sa.ForeignKey("players.id"),
            nullable=True,
        ),
        sa.Column(
            "vice_captain_player_id",
            sa.Integer(),
            sa.ForeignKey("players.id"),
            nullable=True,
        ),
        sa.Column(
            "total_points",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "gameweek_points",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "transfers_made_total",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "free_transfers_available",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "bank_balance",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
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
        sa.UniqueConstraint("user_id", "season_id", name="uq_fantasy_team_user_season"),
    )
    op.create_index("ix_fantasy_teams_user_id", "fantasy_teams", ["user_id"])
    op.create_index("ix_fantasy_teams_season_id", "fantasy_teams", ["season_id"])

    op.create_table(
        "fantasy_team_players",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "team_id",
            sa.Integer(),
            sa.ForeignKey("fantasy_teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "player_id",
            sa.Integer(),
            sa.ForeignKey("players.id"),
            nullable=False,
        ),
        sa.Column("slot_position", sa.String(10), nullable=False),
        sa.Column(
            "is_starting",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("purchase_price", sa.Integer(), nullable=False),
        sa.UniqueConstraint("team_id", "player_id", name="uq_fantasy_team_player"),
    )
    op.create_index(
        "ix_fantasy_team_players_team_id",
        "fantasy_team_players",
        ["team_id"],
    )

    op.create_table(
        "fantasy_transfers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "team_id",
            sa.Integer(),
            sa.ForeignKey("fantasy_teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "gameweek_id",
            sa.Integer(),
            sa.ForeignKey("fantasy_gameweeks.id"),
            nullable=True,
        ),
        sa.Column(
            "player_in_id",
            sa.Integer(),
            sa.ForeignKey("players.id"),
            nullable=False,
        ),
        sa.Column(
            "player_out_id",
            sa.Integer(),
            sa.ForeignKey("players.id"),
            nullable=False,
        ),
        sa.Column("in_price", sa.Integer(), nullable=False),
        sa.Column("out_price", sa.Integer(), nullable=False),
        sa.Column(
            "was_free",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "point_cost",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_fantasy_transfers_team_id", "fantasy_transfers", ["team_id"])


def downgrade() -> None:
    op.drop_index("ix_fantasy_transfers_team_id", table_name="fantasy_transfers")
    op.drop_table("fantasy_transfers")
    op.drop_index("ix_fantasy_team_players_team_id", table_name="fantasy_team_players")
    op.drop_table("fantasy_team_players")
    op.drop_index("ix_fantasy_teams_season_id", table_name="fantasy_teams")
    op.drop_index("ix_fantasy_teams_user_id", table_name="fantasy_teams")
    op.drop_table("fantasy_teams")
