"""add user_predictions table for tipping league

Revision ID: 5b8d3a2f7e91
Revises: 3a7c2e1f5d89
Create Date: 2026-02-11
"""

from alembic import op
import sqlalchemy as sa

revision = "5b8d3a2f7e91"
down_revision = "3a7c2e1f5d89"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_predictions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True
        ),
        sa.Column(
            "fixture_id",
            sa.Integer,
            sa.ForeignKey("fixtures.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("predicted_outcome", sa.String(5), nullable=False),  # H, D, A
        sa.Column("predicted_home_goals", sa.Integer, nullable=True),
        sa.Column("predicted_away_goals", sa.Integer, nullable=True),
        sa.Column("points_earned", sa.Integer, nullable=True),
        sa.Column("was_correct_outcome", sa.Boolean, nullable=True),
        sa.Column("was_exact_score", sa.Boolean, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("scored_at", sa.DateTime, nullable=True),
        sa.UniqueConstraint("user_id", "fixture_id", name="uq_user_fixture_prediction"),
    )
    op.create_index(
        "ix_user_pred_user_created", "user_predictions", ["user_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_user_pred_user_created")
    op.drop_table("user_predictions")
