"""add fantasy_ai_recommendations table for T8 (AI coach)

Revision ID: h4b9c2d6e103
Revises: g3a8b1c5d502
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "h4b9c2d6e103"
down_revision: str | None = "g3a8b1c5d502"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    ai_kind = sa.Enum(
        "transfer_in",
        "transfer_out",
        "captain",
        "formation",
        name="airecommendationkind",
    )

    op.create_table(
        "fantasy_ai_recommendations",
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
        sa.Column("kind", ai_kind, nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("reasoning_text", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("cached_until", sa.DateTime(), nullable=True),
        sa.Column("was_acted_upon", sa.Boolean(), nullable=True),
        sa.Column(
            "generated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_fantasy_ai_rec_team_id",
        "fantasy_ai_recommendations",
        ["team_id"],
    )
    op.create_index(
        "ix_fantasy_ai_rec_gameweek_id",
        "fantasy_ai_recommendations",
        ["gameweek_id"],
    )
    op.create_index(
        "ix_fantasy_ai_rec_kind",
        "fantasy_ai_recommendations",
        ["kind"],
    )
    op.create_index(
        "ix_fantasy_ai_rec_generated_at",
        "fantasy_ai_recommendations",
        ["generated_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_fantasy_ai_rec_generated_at",
        table_name="fantasy_ai_recommendations",
    )
    op.drop_index("ix_fantasy_ai_rec_kind", table_name="fantasy_ai_recommendations")
    op.drop_index(
        "ix_fantasy_ai_rec_gameweek_id",
        table_name="fantasy_ai_recommendations",
    )
    op.drop_index("ix_fantasy_ai_rec_team_id", table_name="fantasy_ai_recommendations")
    op.drop_table("fantasy_ai_recommendations")
    sa.Enum(name="airecommendationkind").drop(op.get_bind(), checkfirst=True)
