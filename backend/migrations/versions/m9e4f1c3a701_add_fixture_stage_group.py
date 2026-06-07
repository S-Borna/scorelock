"""fixtures.stage_name + group_letter — turneringsstruktur (VM 2026 + framtida cups)

Revision ID: m9e4f1c3a701
Revises: b2f3a0dd5e01
Create Date: 2026-06-07

VM 2026 har två-nivå-hierarki som befintliga round-fältet (String 50) inte räcker
för: stage (Group Stage / Round of 32 / R16 / QF / SF / Final / 3rd) + grupp
(A–L för 12 group-stage-grupper). Båda nullable så befintliga liga-fixtures
(Allsvenskan, PL, etc.) inte påverkas. Additivt — downgrade tar bort kolumnerna
rent.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "m9e4f1c3a701"
down_revision: Union[str, None] = "b2f3a0dd5e01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "fixtures",
        sa.Column("stage_name", sa.String(50), nullable=True),
    )
    op.add_column(
        "fixtures",
        sa.Column("group_letter", sa.String(2), nullable=True),
    )
    op.create_index(
        "ix_fixture_league_stage",
        "fixtures",
        ["league_id", "stage_name"],
    )


def downgrade() -> None:
    op.drop_index("ix_fixture_league_stage", table_name="fixtures")
    op.drop_column("fixtures", "group_letter")
    op.drop_column("fixtures", "stage_name")
