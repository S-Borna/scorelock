"""add players + fixture_events tables for Phase 2 (Event Timeline)

Revision ID: f9c2e4a7b803
Revises: e4d7c2a8b510
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f9c2e4a7b803"
down_revision: str | None = "e4d7c2a8b510"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("canonical_name", sa.String(150), nullable=False),
        sa.Column("display_name", sa.String(150), nullable=False),
        sa.Column("position_code", sa.String(10), nullable=True),
        sa.Column(
            "current_team_id",
            sa.Integer(),
            sa.ForeignKey("teams.id"),
            nullable=True,
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
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_players_canonical_name", "players", ["canonical_name"])
    op.create_index("ix_players_current_team_id", "players", ["current_team_id"])

    op.create_table(
        "fixture_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "fixture_id",
            sa.Integer(),
            sa.ForeignKey("fixtures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("minute", sa.Integer(), nullable=False),
        sa.Column("stoppage", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(30), nullable=False),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=True),
        sa.Column(
            "primary_player_id",
            sa.Integer(),
            sa.ForeignKey("players.id"),
            nullable=True,
        ),
        sa.Column(
            "secondary_player_id",
            sa.Integer(),
            sa.ForeignKey("players.id"),
            nullable=True,
        ),
        sa.Column(
            "player_in_id",
            sa.Integer(),
            sa.ForeignKey("players.id"),
            nullable=True,
        ),
        sa.Column(
            "player_out_id",
            sa.Integer(),
            sa.ForeignKey("players.id"),
            nullable=True,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "fixture_id",
            "provider",
            "external_id",
            name="uq_fixture_event_provider_external",
        ),
    )
    op.create_index("ix_fixture_events_fixture_id", "fixture_events", ["fixture_id"])
    op.create_index("ix_fixture_events_event_type", "fixture_events", ["event_type"])
    op.create_index(
        "ix_fixture_events_fixture_minute",
        "fixture_events",
        ["fixture_id", "minute", "stoppage"],
    )
    # Demo seed extracted to backend/scripts/seed_demo_data.sql — run `make seed-demo` locally.


def downgrade() -> None:
    op.drop_index("ix_fixture_events_fixture_minute", table_name="fixture_events")
    op.drop_index("ix_fixture_events_event_type", table_name="fixture_events")
    op.drop_index("ix_fixture_events_fixture_id", table_name="fixture_events")
    op.drop_table("fixture_events")
    op.drop_index("ix_players_current_team_id", table_name="players")
    op.drop_index("ix_players_canonical_name", table_name="players")
    op.drop_table("players")
