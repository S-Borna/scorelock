"""add venues + referees + fixture_match_info for Phase 2 (match info-rad)

Revision ID: i5c2d3e4f201
Revises: h4b9c2d6e103
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "i5c2d3e4f201"
down_revision: str | None = "h4b9c2d6e103"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "venues",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("canonical_name", sa.String(150), nullable=False),
        sa.Column("display_name", sa.String(150), nullable=False),
        sa.Column("country_iso_2", sa.String(2), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("surface", sa.String(50), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("image_ref", sa.String(500), nullable=True),
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
    op.create_index("ix_venues_canonical_name", "venues", ["canonical_name"])
    op.create_index("ix_venues_country_iso_2", "venues", ["country_iso_2"])

    op.create_table(
        "referees",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("canonical_name", sa.String(150), nullable=False),
        sa.Column("display_name", sa.String(150), nullable=False),
        sa.Column("nationality_iso_2", sa.String(2), nullable=True),
        sa.Column("career_games_count", sa.Integer(), nullable=True),
        sa.Column("career_yellows_per_game", sa.Float(), nullable=True),
        sa.Column("career_reds_per_game", sa.Float(), nullable=True),
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
    op.create_index("ix_referees_canonical_name", "referees", ["canonical_name"])

    op.create_table(
        "fixture_match_info",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "fixture_id",
            sa.Integer(),
            sa.ForeignKey("fixtures.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "venue_id",
            sa.Integer(),
            sa.ForeignKey("venues.id"),
            nullable=True,
        ),
        sa.Column(
            "referee_id",
            sa.Integer(),
            sa.ForeignKey("referees.id"),
            nullable=True,
        ),
        sa.Column(
            "provider",
            sa.String(50),
            nullable=False,
            server_default=sa.text("'manual_seed'"),
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
    op.create_index(
        "ix_fixture_match_info_fixture_id",
        "fixture_match_info",
        ["fixture_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_fixture_match_info_fixture_id", table_name="fixture_match_info")
    op.drop_table("fixture_match_info")
    op.drop_index("ix_referees_canonical_name", table_name="referees")
    op.drop_table("referees")
    op.drop_index("ix_venues_country_iso_2", table_name="venues")
    op.drop_index("ix_venues_canonical_name", table_name="venues")
    op.drop_table("venues")
