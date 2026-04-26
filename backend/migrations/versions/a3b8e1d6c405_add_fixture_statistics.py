"""add fixture_statistics table for Phase 3 (Stats Panel)

Revision ID: a3b8e1d6c405
Revises: f9c2e4a7b803
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa


revision: str = "a3b8e1d6c405"
down_revision: str | None = "f9c2e4a7b803"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "fixture_statistics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "fixture_id",
            sa.Integer(),
            sa.ForeignKey("fixtures.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("team_id", sa.Integer(), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("possession_pct", sa.Float(), nullable=True),
        sa.Column("shots_total", sa.Integer(), nullable=True),
        sa.Column("shots_on_target", sa.Integer(), nullable=True),
        sa.Column("shots_off_target", sa.Integer(), nullable=True),
        sa.Column("shots_blocked", sa.Integer(), nullable=True),
        sa.Column("corners", sa.Integer(), nullable=True),
        sa.Column("fouls", sa.Integer(), nullable=True),
        sa.Column("yellow_cards_count", sa.Integer(), nullable=True),
        sa.Column("red_cards_count", sa.Integer(), nullable=True),
        sa.Column("offsides", sa.Integer(), nullable=True),
        sa.Column("xg", sa.Float(), nullable=True),
        sa.Column("passes_total", sa.Integer(), nullable=True),
        sa.Column("passes_accurate", sa.Integer(), nullable=True),
        sa.Column("pass_accuracy_pct", sa.Float(), nullable=True),
        sa.Column("tackles", sa.Integer(), nullable=True),
        sa.Column("interceptions", sa.Integer(), nullable=True),
        sa.Column("blocks", sa.Integer(), nullable=True),
        sa.Column("clearances", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("as_of_minute", sa.Integer(), nullable=True),
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
        sa.UniqueConstraint(
            "fixture_id",
            "team_id",
            "provider",
            name="uq_fixture_stats_team_provider",
        ),
    )
    op.create_index(
        "ix_fixture_statistics_fixture_id",
        "fixture_statistics",
        ["fixture_id"],
    )

    # Seed: Manchester City 2-1 Arsenal (fixture 328) — final-state stats per team.
    # Plausible numbers for City home win. NOTE: fictional, not actual match data.
    # Wrapped in IF EXISTS guard so CI / fresh-DB envs without fixture 328 cleanly no-op.
    op.execute(
        """
        DO $$
        BEGIN
        IF EXISTS (SELECT 1 FROM fixtures WHERE id = 328) THEN

        INSERT INTO fixture_statistics
            (fixture_id, team_id, possession_pct, shots_total, shots_on_target,
             shots_off_target, shots_blocked, corners, fouls, yellow_cards_count,
             red_cards_count, offsides, xg, passes_total, passes_accurate,
             pass_accuracy_pct, tackles, interceptions, blocks, clearances,
             provider, as_of_minute, created_at, updated_at)
        VALUES
            (328, (SELECT id FROM teams WHERE name='Manchester City FC'),
             58.0, 14, 6, 5, 3, 7, 9, 1, 0, 2, 1.85,
             612, 553, 90.4, 14, 9, 8, 18,
             'manual_seed', NULL, now(), now()),
            (328, (SELECT id FROM teams WHERE name='Arsenal FC'),
             42.0, 11, 4, 4, 3, 4, 12, 2, 0, 3, 1.20,
             441, 376, 85.3, 19, 12, 11, 22,
             'manual_seed', NULL, now(), now());

        END IF;
        END$$;
        """
    )


def downgrade() -> None:
    op.drop_index("ix_fixture_statistics_fixture_id", table_name="fixture_statistics")
    op.drop_table("fixture_statistics")
