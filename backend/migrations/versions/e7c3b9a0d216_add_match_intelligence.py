"""add match_intelligence table for Phase 5 (AI narrative cards)

Revision ID: e7c3b9a0d216
Revises: d2f5a8c9b704
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa


revision: str = "e7c3b9a0d216"
down_revision: str | None = "d2f5a8c9b704"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    intelligence_kind = sa.Enum(
        "pre_match",
        "in_match",
        "post_match",
        name="intelligencekind",
    )

    op.create_table(
        "match_intelligence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "fixture_id",
            sa.Integer(),
            sa.ForeignKey("fixtures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", intelligence_kind, nullable=False),
        sa.Column(
            "language",
            sa.String(5),
            nullable=False,
            server_default=sa.text("'sv'"),
        ),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("as_of_minute", sa.Integer(), nullable=True),
        sa.Column(
            "generated_at",
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
            "kind",
            "language",
            name="uq_match_intelligence_kind_lang",
        ),
    )
    op.create_index(
        "ix_match_intelligence_fixture_id",
        "match_intelligence",
        ["fixture_id"],
    )
    op.create_index(
        "ix_match_intelligence_kind",
        "match_intelligence",
        ["kind"],
    )
    op.create_index(
        "ix_match_intel_fixture_kind",
        "match_intelligence",
        ["fixture_id", "kind"],
    )
    # Demo seed extracted to backend/scripts/seed_demo_data.sql — run `make seed-demo` locally.


def downgrade() -> None:
    op.drop_index("ix_match_intel_fixture_kind", table_name="match_intelligence")
    op.drop_index("ix_match_intelligence_kind", table_name="match_intelligence")
    op.drop_index("ix_match_intelligence_fixture_id", table_name="match_intelligence")
    op.drop_table("match_intelligence")
    sa.Enum(name="intelligencekind").drop(op.get_bind(), checkfirst=True)
