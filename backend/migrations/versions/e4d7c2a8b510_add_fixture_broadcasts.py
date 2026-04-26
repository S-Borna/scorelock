"""add fixture_broadcasts table + SE seed for Phase 1 (Where to Watch)

Revision ID: e4d7c2a8b510
Revises: c8e2b4a6d105
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa


revision: str = "e4d7c2a8b510"
down_revision: str | None = "c8e2b4a6d105"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "fixture_broadcasts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "fixture_id",
            sa.Integer(),
            sa.ForeignKey("fixtures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("country_iso_2", sa.String(2), nullable=False),
        sa.Column("provider_type", sa.String(20), nullable=False),
        sa.Column("channel_name", sa.String(150), nullable=False),
        sa.Column("watch_url", sa.String(1000), nullable=True),
        sa.Column("language_iso_2", sa.String(2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_fixture_broadcasts_fixture_id", "fixture_broadcasts", ["fixture_id"]
    )
    op.create_index(
        "ix_fixture_broadcasts_country_iso_2",
        "fixture_broadcasts",
        ["country_iso_2"],
    )
    op.create_index(
        "ix_fixture_broadcasts_fixture_country",
        "fixture_broadcasts",
        ["fixture_id", "country_iso_2"],
    )

    # Seed: SE broadcasts for the 5 most recent fixtures per league.
    # Real Sweden TV-rights mapping (as of 2025): Viaplay = Premier League,
    # TV4 Sport = Allsvenskan, C More = La Liga.
    op.execute(
        """
        INSERT INTO fixture_broadcasts
            (fixture_id, country_iso_2, provider_type, channel_name, watch_url, language_iso_2, created_at)
        SELECT f.id, 'SE', 'STREAMING', 'Viaplay', 'https://viaplay.se/sport', 'sv', now()
        FROM fixtures f JOIN leagues l ON l.id = f.league_id
        WHERE l.name = 'Premier League'
        ORDER BY f.kickoff DESC
        LIMIT 5
        """
    )
    op.execute(
        """
        INSERT INTO fixture_broadcasts
            (fixture_id, country_iso_2, provider_type, channel_name, watch_url, language_iso_2, created_at)
        SELECT f.id, 'SE', 'TV', 'TV4 Sport', 'https://www.tv4play.se/sport', 'sv', now()
        FROM fixtures f JOIN leagues l ON l.id = f.league_id
        WHERE l.name = 'Allsvenskan'
        ORDER BY f.kickoff DESC
        LIMIT 5
        """
    )
    op.execute(
        """
        INSERT INTO fixture_broadcasts
            (fixture_id, country_iso_2, provider_type, channel_name, watch_url, language_iso_2, created_at)
        SELECT f.id, 'SE', 'STREAMING', 'C More Fotboll', 'https://www.cmore.se/sport', 'sv', now()
        FROM fixtures f JOIN leagues l ON l.id = f.league_id
        WHERE l.name = 'La Liga'
        ORDER BY f.kickoff DESC
        LIMIT 5
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_fixture_broadcasts_fixture_country", table_name="fixture_broadcasts"
    )
    op.drop_index(
        "ix_fixture_broadcasts_country_iso_2", table_name="fixture_broadcasts"
    )
    op.drop_index("ix_fixture_broadcasts_fixture_id", table_name="fixture_broadcasts")
    op.drop_table("fixture_broadcasts")
