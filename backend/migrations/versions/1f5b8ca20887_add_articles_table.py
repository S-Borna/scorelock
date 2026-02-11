"""add_articles_table

Revision ID: 1f5b8ca20887
Revises: 246c910cfb31
Create Date: 2026-02-11 00:45:05.978438

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1f5b8ca20887"
down_revision: Union[str, None] = "246c910cfb31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "articles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("language", sa.String(10), server_default="sv", nullable=False),
        sa.Column(
            "league_id", sa.Integer(), sa.ForeignKey("leagues.id"), nullable=True
        ),
        sa.Column(
            "fixture_id", sa.Integer(), sa.ForeignKey("fixtures.id"), nullable=True
        ),
        sa.Column("round", sa.String(50), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("meta_data", sa.JSON(), nullable=True),
        sa.Column(
            "auto_generated", sa.Boolean(), server_default="true", nullable=False
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_article_type_league", "articles", ["type", "league_id"])
    op.create_index("ix_article_published", "articles", ["published_at"])


def downgrade() -> None:
    op.drop_index("ix_article_published", table_name="articles")
    op.drop_index("ix_article_type_league", table_name="articles")
    op.drop_table("articles")
