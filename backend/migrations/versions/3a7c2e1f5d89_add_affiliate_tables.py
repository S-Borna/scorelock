"""add_affiliate_tables

Revision ID: 3a7c2e1f5d89
Revises: 1f5b8ca20887
Create Date: 2026-02-11 14:00:00.000000

"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3a7c2e1f5d89'
down_revision: str | None = '1f5b8ca20887'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Affiliate links table
    op.create_table(
        'affiliate_links',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('bookmaker', sa.String(100), nullable=False, index=True),
        sa.Column('bookmaker_display', sa.String(100), nullable=False),
        sa.Column('logo_url', sa.String(500), nullable=True),
        sa.Column('base_url', sa.String(1000), nullable=False),
        sa.Column('tracking_id', sa.String(255), nullable=True),
        sa.Column('market', sa.String(50), nullable=False, server_default='1X2'),
        sa.Column('country', sa.String(5), nullable=False, server_default='SE'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', index=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Affiliate clicks table
    op.create_table(
        'affiliate_clicks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('link_id', sa.Integer(), sa.ForeignKey('affiliate_links.id'), nullable=False, index=True),
        sa.Column('fixture_id', sa.Integer(), sa.ForeignKey('fixtures.id'), nullable=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True, index=True),
        sa.Column('page_source', sa.String(100), nullable=True),
        sa.Column('ip_hash', sa.String(64), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('clicked_at', sa.DateTime(), nullable=False, server_default=sa.text('now()'), index=True),
    )

    op.create_index('ix_affiliate_click_link_date', 'affiliate_clicks', ['link_id', 'clicked_at'])

    # Seed default Swedish bookmakers (placeholder URLs — replace with real affiliate URLs)
    op.execute("""
        INSERT INTO affiliate_links (bookmaker, bookmaker_display, base_url, tracking_id, market, country, is_active, priority) VALUES
        ('bet365', 'Bet365', 'https://www.bet365.com/#/IP/B1', 'scorelock_se', '1X2', 'SE', true, 100),
        ('unibet', 'Unibet', 'https://www.unibet.se/betting/sports', 'scorelock_se', '1X2', 'SE', true, 90),
        ('betsson', 'Betsson', 'https://www.betsson.com/sv/odds', 'scorelock_se', '1X2', 'SE', true, 80),
        ('leovegas', 'LeoVegas', 'https://www.leovegas.se/sport', 'scorelock_se', '1X2', 'SE', true, 70)
    """)


def downgrade() -> None:
    op.drop_index('ix_affiliate_click_link_date', table_name='affiliate_clicks')
    op.drop_table('affiliate_clicks')
    op.drop_table('affiliate_links')
