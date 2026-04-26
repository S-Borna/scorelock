"""add fixture_commentary + fixture_momentum + user_motm_votes for Phase 10

Revision ID: k7d5e9f0a503
Revises: j6a1b3c8d402
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa


revision: str = "k7d5e9f0a503"
down_revision: str | None = "j6a1b3c8d402"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "fixture_commentary",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "fixture_id",
            sa.Integer(),
            sa.ForeignKey("fixtures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("minute", sa.Integer(), nullable=False),
        sa.Column("stoppage", sa.Integer(), nullable=True),
        sa.Column("comment_type", sa.String(30), nullable=False),
        sa.Column("text_en", sa.Text(), nullable=True),
        sa.Column("text_sv", sa.Text(), nullable=True),
        sa.Column(
            "is_translated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
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
            name="uq_commentary_provider_external",
        ),
    )
    op.create_index("ix_commentary_fixture_id", "fixture_commentary", ["fixture_id"])
    op.create_index(
        "ix_commentary_fixture_minute",
        "fixture_commentary",
        ["fixture_id", "minute", "stoppage"],
    )

    op.create_table(
        "fixture_momentum",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "fixture_id",
            sa.Integer(),
            sa.ForeignKey("fixtures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("match_minute", sa.Integer(), nullable=False),
        sa.Column("match_stoppage", sa.Integer(), nullable=True),
        sa.Column("home_momentum_pct", sa.Float(), nullable=False),
        sa.Column("away_momentum_pct", sa.Float(), nullable=False),
        sa.Column("source", sa.String(20), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("derivation_window_seconds", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_momentum_fixture_id", "fixture_momentum", ["fixture_id"])
    op.create_index("ix_momentum_observed_at", "fixture_momentum", ["observed_at"])
    op.create_index(
        "ix_momentum_fixture_minute",
        "fixture_momentum",
        ["fixture_id", "match_minute", "match_stoppage"],
    )

    op.create_table(
        "user_motm_votes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "fixture_id",
            sa.Integer(),
            sa.ForeignKey("fixtures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "voted_player_id",
            sa.Integer(),
            sa.ForeignKey("players.id"),
            nullable=False,
        ),
        sa.Column(
            "voted_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "is_locked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.UniqueConstraint("user_id", "fixture_id", name="uq_motm_vote_user_fixture"),
    )
    op.create_index("ix_motm_votes_user_id", "user_motm_votes", ["user_id"])
    op.create_index("ix_motm_votes_fixture_id", "user_motm_votes", ["fixture_id"])


def downgrade() -> None:
    op.drop_index("ix_motm_votes_fixture_id", table_name="user_motm_votes")
    op.drop_index("ix_motm_votes_user_id", table_name="user_motm_votes")
    op.drop_table("user_motm_votes")
    op.drop_index("ix_momentum_fixture_minute", table_name="fixture_momentum")
    op.drop_index("ix_momentum_observed_at", table_name="fixture_momentum")
    op.drop_index("ix_momentum_fixture_id", table_name="fixture_momentum")
    op.drop_table("fixture_momentum")
    op.drop_index("ix_commentary_fixture_minute", table_name="fixture_commentary")
    op.drop_index("ix_commentary_fixture_id", table_name="fixture_commentary")
    op.drop_table("fixture_commentary")
