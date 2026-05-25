"""odds unik-constraint (fixture, bookmaker, market) — låser upp ON CONFLICT-upsert

Revision ID: b2f3a0dd5e01
Revises: aef621198d29
Create Date: 2026-05-25

upsert_odds använder ON CONFLICT men `odds` hade bara ett PLAIN index på
(fixture_id, bookmaker) — så upserten kastade och 0 odds persisterades.
Flera marknader (1X2, totals) per fixture+bookmaker måste samexistera → unik
grain är (fixture_id, bookmaker, market). Odds-tabellen är tom så bytet är säkert.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "b2f3a0dd5e01"
down_revision: Union[str, None] = "aef621198d29"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_odds_fixture_bookmaker", table_name="odds")
    op.create_unique_constraint(
        "uq_odds_fixture_bookmaker_market",
        "odds",
        ["fixture_id", "bookmaker", "market"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_odds_fixture_bookmaker_market", "odds", type_="unique"
    )
    op.create_index(
        "ix_odds_fixture_bookmaker", "odds", ["fixture_id", "bookmaker"]
    )
