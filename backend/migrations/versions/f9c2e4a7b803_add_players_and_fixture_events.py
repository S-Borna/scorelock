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

    # Seed: Manchester City 2-1 Arsenal (fixture_id=328, FINISHED, 2026-04-19).
    # 22 starting players + 6 bench players + 10 events. Plausible 2025/26 roster.
    op.execute(
        """
        INSERT INTO players (canonical_name, display_name, position_code, current_team_id, external_ids, created_at, updated_at)
        SELECT name, display, pos, (SELECT id FROM teams WHERE teams.name=team_name), '{}'::jsonb, now(), now()
        FROM (VALUES
            -- Manchester City starting XI (4-3-3)
            ('Ederson Moraes',     'Ederson',     'GK',  'Manchester City FC'),
            ('Kyle Walker',        'Walker',      'DEF', 'Manchester City FC'),
            ('John Stones',        'Stones',      'DEF', 'Manchester City FC'),
            ('Rúben Dias',         'Dias',        'DEF', 'Manchester City FC'),
            ('Nathan Aké',         'Aké',         'DEF', 'Manchester City FC'),
            ('Rodri Hernández',    'Rodri',       'MID', 'Manchester City FC'),
            ('Kevin De Bruyne',    'De Bruyne',   'MID', 'Manchester City FC'),
            ('Bernardo Silva',     'B. Silva',    'MID', 'Manchester City FC'),
            ('Phil Foden',         'Foden',       'FWD', 'Manchester City FC'),
            ('Erling Haaland',     'Haaland',     'FWD', 'Manchester City FC'),
            ('Jérémy Doku',        'Doku',        'FWD', 'Manchester City FC'),
            -- Manchester City bench (subs only)
            ('Joško Gvardiol',     'Gvardiol',    'DEF', 'Manchester City FC'),
            ('Mateo Kovačić',      'Kovačić',     'MID', 'Manchester City FC'),
            -- Arsenal starting XI (4-3-3)
            ('David Raya',         'Raya',        'GK',  'Arsenal FC'),
            ('Ben White',           'White',      'DEF', 'Arsenal FC'),
            ('William Saliba',      'Saliba',     'DEF', 'Arsenal FC'),
            ('Gabriel Magalhães',   'Gabriel',    'DEF', 'Arsenal FC'),
            ('Riccardo Calafiori',  'Calafiori',  'DEF', 'Arsenal FC'),
            ('Declan Rice',         'Rice',       'MID', 'Arsenal FC'),
            ('Martin Ødegaard',     'Ødegaard',   'MID', 'Arsenal FC'),
            ('Mikel Merino',        'Merino',     'MID', 'Arsenal FC'),
            ('Bukayo Saka',         'Saka',       'FWD', 'Arsenal FC'),
            ('Kai Havertz',         'Havertz',    'FWD', 'Arsenal FC'),
            ('Leandro Trossard',    'Trossard',   'FWD', 'Arsenal FC'),
            -- Arsenal bench (subs only)
            ('Gabriel Martinelli',  'Martinelli', 'FWD', 'Arsenal FC'),
            ('Gabriel Jesus',       'Jesus',      'FWD', 'Arsenal FC')
        ) AS seed(name, display, pos, team_name)
        """
    )

    # Events for fixture 328 — Manchester City 2-1 Arsenal
    op.execute(
        """
        INSERT INTO fixture_events
            (fixture_id, minute, stoppage, event_type, team_id, primary_player_id, secondary_player_id, player_in_id, player_out_id, description, provider, external_id, created_at)
        VALUES
            (328, 12, NULL, 'YELLOW_CARD',
                (SELECT id FROM teams WHERE name='Manchester City FC'),
                (SELECT id FROM players WHERE canonical_name='Rodri Hernández'),
                NULL, NULL, NULL, 'Tactical foul', 'manual_seed', 'mc-ars-1', now()),
            (328, 17, NULL, 'GOAL',
                (SELECT id FROM teams WHERE name='Manchester City FC'),
                (SELECT id FROM players WHERE canonical_name='Erling Haaland'),
                (SELECT id FROM players WHERE canonical_name='Phil Foden'),
                NULL, NULL, 'Header from corner, assist Foden', 'manual_seed', 'mc-ars-2', now()),
            (328, 24, NULL, 'YELLOW_CARD',
                (SELECT id FROM teams WHERE name='Arsenal FC'),
                (SELECT id FROM players WHERE canonical_name='Bukayo Saka'),
                NULL, NULL, NULL, 'Dissent', 'manual_seed', 'mc-ars-3', now()),
            (328, 53, NULL, 'GOAL',
                (SELECT id FROM teams WHERE name='Manchester City FC'),
                (SELECT id FROM players WHERE canonical_name='Kevin De Bruyne'),
                (SELECT id FROM players WHERE canonical_name='Bernardo Silva'),
                NULL, NULL, 'Curled finish from edge of box', 'manual_seed', 'mc-ars-4', now()),
            (328, 58, NULL, 'SUBSTITUTION',
                (SELECT id FROM teams WHERE name='Arsenal FC'),
                NULL, NULL,
                (SELECT id FROM players WHERE canonical_name='Gabriel Martinelli'),
                (SELECT id FROM players WHERE canonical_name='Leandro Trossard'),
                NULL, 'manual_seed', 'mc-ars-5', now()),
            (328, 67, NULL, 'YELLOW_CARD',
                (SELECT id FROM teams WHERE name='Arsenal FC'),
                (SELECT id FROM players WHERE canonical_name='Riccardo Calafiori'),
                NULL, NULL, NULL, 'Late challenge', 'manual_seed', 'mc-ars-6', now()),
            (328, 71, NULL, 'GOAL',
                (SELECT id FROM teams WHERE name='Arsenal FC'),
                (SELECT id FROM players WHERE canonical_name='Bukayo Saka'),
                (SELECT id FROM players WHERE canonical_name='Martin Ødegaard'),
                NULL, NULL, 'Cut inside, low finish', 'manual_seed', 'mc-ars-7', now()),
            (328, 75, NULL, 'SUBSTITUTION',
                (SELECT id FROM teams WHERE name='Manchester City FC'),
                NULL, NULL,
                (SELECT id FROM players WHERE canonical_name='Mateo Kovačić'),
                (SELECT id FROM players WHERE canonical_name='Kevin De Bruyne'),
                NULL, 'manual_seed', 'mc-ars-8', now()),
            (328, 78, NULL, 'SUBSTITUTION',
                (SELECT id FROM teams WHERE name='Arsenal FC'),
                NULL, NULL,
                (SELECT id FROM players WHERE canonical_name='Gabriel Jesus'),
                (SELECT id FROM players WHERE canonical_name='Kai Havertz'),
                NULL, 'manual_seed', 'mc-ars-9', now()),
            (328, 82, NULL, 'SUBSTITUTION',
                (SELECT id FROM teams WHERE name='Manchester City FC'),
                NULL, NULL,
                (SELECT id FROM players WHERE canonical_name='Joško Gvardiol'),
                (SELECT id FROM players WHERE canonical_name='Jérémy Doku'),
                NULL, 'manual_seed', 'mc-ars-10', now())
        """
    )


def downgrade() -> None:
    op.drop_index("ix_fixture_events_fixture_minute", table_name="fixture_events")
    op.drop_index("ix_fixture_events_event_type", table_name="fixture_events")
    op.drop_index("ix_fixture_events_fixture_id", table_name="fixture_events")
    op.drop_table("fixture_events")
    op.drop_index("ix_players_current_team_id", table_name="players")
    op.drop_index("ix_players_canonical_name", table_name="players")
    op.drop_table("players")
