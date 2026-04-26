"""add fantasy foundation tables for T1 (seasons + gameweeks + pricing + stats)

Revision ID: f9a4c1e8b305
Revises: e7c3b9a0d216
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f9a4c1e8b305"
down_revision: str | None = "e7c3b9a0d216"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    fantasy_scope = sa.Enum(
        "single_league",
        "cross_european",
        "world_cup",
        "demo",
        name="fantasyscope",
    )
    fantasy_value_trend = sa.Enum(
        "up",
        "down",
        "stable",
        name="fantasyvaluetrend",
    )

    op.create_table(
        "fantasy_seasons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("scope", fantasy_scope, nullable=False),
        sa.Column(
            "primary_league_id",
            sa.Integer(),
            sa.ForeignKey("leagues.id"),
            nullable=True,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column(
            "total_budget_units",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1000"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "transfer_rules",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "point_weights",
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
    op.create_index("ix_fantasy_seasons_scope", "fantasy_seasons", ["scope"])
    op.create_index("ix_fantasy_seasons_is_active", "fantasy_seasons", ["is_active"])

    op.create_table(
        "fantasy_gameweeks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "season_id",
            sa.Integer(),
            sa.ForeignKey("fantasy_seasons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("gameweek_number", sa.Integer(), nullable=False),
        sa.Column("deadline_at", sa.DateTime(), nullable=False),
        sa.Column("first_kickoff_at", sa.DateTime(), nullable=False),
        sa.Column("last_kickoff_at", sa.DateTime(), nullable=False),
        sa.Column(
            "is_finalized",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.UniqueConstraint(
            "season_id",
            "gameweek_number",
            name="uq_fantasy_gameweek_number",
        ),
    )
    op.create_index(
        "ix_fantasy_gameweeks_season_id", "fantasy_gameweeks", ["season_id"]
    )
    op.create_index(
        "ix_fantasy_gameweeks_deadline_at", "fantasy_gameweeks", ["deadline_at"]
    )
    op.create_index(
        "ix_fantasy_gameweeks_is_finalized", "fantasy_gameweeks", ["is_finalized"]
    )

    op.create_table(
        "fantasy_gameweek_fixtures",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "gameweek_id",
            sa.Integer(),
            sa.ForeignKey("fantasy_gameweeks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "fixture_id",
            sa.Integer(),
            sa.ForeignKey("fixtures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "gameweek_id",
            "fixture_id",
            name="uq_fantasy_gw_fixture",
        ),
    )
    op.create_index(
        "ix_fantasy_gw_fixtures_gameweek_id",
        "fantasy_gameweek_fixtures",
        ["gameweek_id"],
    )
    op.create_index(
        "ix_fantasy_gw_fixtures_fixture_id",
        "fantasy_gameweek_fixtures",
        ["fixture_id"],
    )

    op.create_table(
        "fantasy_player_pricing",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "player_id",
            sa.Integer(),
            sa.ForeignKey("players.id"),
            nullable=False,
        ),
        sa.Column(
            "season_id",
            sa.Integer(),
            sa.ForeignKey("fantasy_seasons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("current_price", sa.Integer(), nullable=False),
        sa.Column("starting_price", sa.Integer(), nullable=False),
        sa.Column(
            "last_change_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "value_trend",
            fantasy_value_trend,
            nullable=False,
            server_default=sa.text("'stable'"),
        ),
        sa.Column(
            "selected_by_pct",
            sa.Float(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "fantasy_points_total",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.UniqueConstraint(
            "player_id",
            "season_id",
            name="uq_fantasy_player_pricing",
        ),
    )
    op.create_index(
        "ix_fantasy_player_pricing_player_id",
        "fantasy_player_pricing",
        ["player_id"],
    )
    op.create_index(
        "ix_fantasy_player_pricing_season_id",
        "fantasy_player_pricing",
        ["season_id"],
    )

    op.create_table(
        "fantasy_player_gameweek_stats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "player_id",
            sa.Integer(),
            sa.ForeignKey("players.id"),
            nullable=False,
        ),
        sa.Column(
            "gameweek_id",
            sa.Integer(),
            sa.ForeignKey("fantasy_gameweeks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "fixture_id",
            sa.Integer(),
            sa.ForeignKey("fixtures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "minutes_played",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("goals", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("assists", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "clean_sheet",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "yellow_cards", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "red_cards", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column("saves", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "goals_conceded",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "own_goals", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "penalties_missed",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "penalties_saved",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "bonus_points", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "points_earned", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.UniqueConstraint(
            "player_id",
            "gameweek_id",
            "fixture_id",
            name="uq_fantasy_player_gw_stats",
        ),
    )
    op.create_index(
        "ix_fantasy_player_gw_stats_player_id",
        "fantasy_player_gameweek_stats",
        ["player_id"],
    )
    op.create_index(
        "ix_fantasy_player_gw_stats_gameweek_id",
        "fantasy_player_gameweek_stats",
        ["gameweek_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_fantasy_player_gw_stats_gameweek_id",
        table_name="fantasy_player_gameweek_stats",
    )
    op.drop_index(
        "ix_fantasy_player_gw_stats_player_id",
        table_name="fantasy_player_gameweek_stats",
    )
    op.drop_table("fantasy_player_gameweek_stats")
    op.drop_index(
        "ix_fantasy_player_pricing_season_id",
        table_name="fantasy_player_pricing",
    )
    op.drop_index(
        "ix_fantasy_player_pricing_player_id",
        table_name="fantasy_player_pricing",
    )
    op.drop_table("fantasy_player_pricing")
    op.drop_index(
        "ix_fantasy_gw_fixtures_fixture_id",
        table_name="fantasy_gameweek_fixtures",
    )
    op.drop_index(
        "ix_fantasy_gw_fixtures_gameweek_id",
        table_name="fantasy_gameweek_fixtures",
    )
    op.drop_table("fantasy_gameweek_fixtures")
    op.drop_index("ix_fantasy_gameweeks_is_finalized", table_name="fantasy_gameweeks")
    op.drop_index("ix_fantasy_gameweeks_deadline_at", table_name="fantasy_gameweeks")
    op.drop_index("ix_fantasy_gameweeks_season_id", table_name="fantasy_gameweeks")
    op.drop_table("fantasy_gameweeks")
    op.drop_index("ix_fantasy_seasons_is_active", table_name="fantasy_seasons")
    op.drop_index("ix_fantasy_seasons_scope", table_name="fantasy_seasons")
    op.drop_table("fantasy_seasons")
    sa.Enum(name="fantasyvaluetrend").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="fantasyscope").drop(op.get_bind(), checkfirst=True)
