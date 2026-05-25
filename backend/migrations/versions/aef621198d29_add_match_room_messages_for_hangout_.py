"""add match_room_messages for hangout Steg 4

Revision ID: aef621198d29
Revises: l8a1c4d2e605
Create Date: 2026-05-25 13:02:23.993798

Notera: alembic autogenerate fångade omfattande pre-existerande modell-vs-DB-drift
(articles, bookmakers, fantasy_*, fixture_*, leagues, teams, user_motm_votes m.fl.
— index-namnkonventioner, JSON→JSONB, kolumntyper). Den driften är INTE en del av
denna ändring och har medvetet strippats bort. Migrationen skapar enbart den nya
match_room_messages-tabellen. Driften är flaggad som separat tech-debt.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'aef621198d29'
down_revision: Union[str, None] = 'l8a1c4d2e605'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'match_room_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fixture_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['fixture_id'], ['fixtures.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_match_room_messages_created_at'),
        'match_room_messages', ['created_at'], unique=False,
    )
    op.create_index(
        op.f('ix_match_room_messages_fixture_id'),
        'match_room_messages', ['fixture_id'], unique=False,
    )
    op.create_index(
        op.f('ix_match_room_messages_user_id'),
        'match_room_messages', ['user_id'], unique=False,
    )
    op.create_index(
        'ix_room_messages_fixture_created',
        'match_room_messages', ['fixture_id', 'created_at'], unique=False,
    )


def downgrade() -> None:
    op.drop_index('ix_room_messages_fixture_created', table_name='match_room_messages')
    op.drop_index(op.f('ix_match_room_messages_user_id'), table_name='match_room_messages')
    op.drop_index(op.f('ix_match_room_messages_fixture_id'), table_name='match_room_messages')
    op.drop_index(op.f('ix_match_room_messages_created_at'), table_name='match_room_messages')
    op.drop_table('match_room_messages')
