"""v0.6a2 add provider identity schema (payloads, entity_mappings, conflicts)

Revision ID: c8e2b4a6d105
Revises: b6a1f5d4c302
Create Date: 2026-04-26

Adds three additive provider identity / audit tables:
  - provider_payloads: raw provider response store
  - provider_entity_mappings: external-ID ↔ canonical-ID truth source
  - provider_conflicts: field divergence log

No changes to existing tables. No FK from any existing table to these.
Per docs/METADATA_SCHEMA_V0.5C.md § Migration Plan v0.6a2.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c8e2b4a6d105"
down_revision: str | None = "b6a1f5d4c302"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "provider_payloads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("operation", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("canonical_table", sa.String(50), nullable=True),
        sa.Column("canonical_id", sa.Integer(), nullable=True),
        sa.Column(
            "payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False
        ),
        sa.Column("payload_hash", sa.String(64), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), nullable=False),
        sa.Column("retained_until", sa.DateTime(), nullable=True),
        sa.Column(
            "is_schema_drift",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("error_summary", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_provider_payloads_provider", "provider_payloads", ["provider"]
    )
    op.create_index(
        "ix_provider_payloads_operation", "provider_payloads", ["operation"]
    )
    op.create_index(
        "ix_provider_payloads_entity_type", "provider_payloads", ["entity_type"]
    )
    op.create_index(
        "ix_provider_payloads_external_id", "provider_payloads", ["external_id"]
    )
    op.create_index(
        "ix_provider_payloads_payload_hash", "provider_payloads", ["payload_hash"]
    )
    op.create_index(
        "ix_provider_payloads_fetched_at", "provider_payloads", ["fetched_at"]
    )
    op.create_index(
        "ix_provider_payloads_retained_until",
        "provider_payloads",
        ["retained_until"],
    )

    op.create_table(
        "provider_entity_mappings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("canonical_table", sa.String(50), nullable=False),
        sa.Column("canonical_id", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
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
            "provider",
            "entity_type",
            "external_id",
            name="uq_provider_entity_external",
        ),
    )
    op.create_index(
        "ix_provider_entity_mappings_provider",
        "provider_entity_mappings",
        ["provider"],
    )
    op.create_index(
        "ix_provider_entity_mappings_entity_type",
        "provider_entity_mappings",
        ["entity_type"],
    )
    op.create_index(
        "ix_pem_canonical",
        "provider_entity_mappings",
        ["canonical_table", "canonical_id"],
    )
    op.create_index(
        "ix_pem_provider_entity",
        "provider_entity_mappings",
        ["provider", "entity_type"],
    )

    op.create_table(
        "provider_conflicts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("canonical_table", sa.String(50), nullable=True),
        sa.Column("canonical_id", sa.Integer(), nullable=True),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column(
            "existing_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "incoming_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column(
            "severity",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'medium'"),
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'open'"),
        ),
        sa.Column(
            "detected_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_provider_conflicts_provider", "provider_conflicts", ["provider"]
    )
    op.create_index(
        "ix_provider_conflicts_entity_type",
        "provider_conflicts",
        ["entity_type"],
    )
    op.create_index(
        "ix_pc_status_severity", "provider_conflicts", ["status", "severity"]
    )
    op.create_index(
        "ix_pc_canonical",
        "provider_conflicts",
        ["canonical_table", "canonical_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_pc_canonical", table_name="provider_conflicts")
    op.drop_index("ix_pc_status_severity", table_name="provider_conflicts")
    op.drop_index(
        "ix_provider_conflicts_entity_type", table_name="provider_conflicts"
    )
    op.drop_index("ix_provider_conflicts_provider", table_name="provider_conflicts")
    op.drop_table("provider_conflicts")

    op.drop_index(
        "ix_pem_provider_entity", table_name="provider_entity_mappings"
    )
    op.drop_index("ix_pem_canonical", table_name="provider_entity_mappings")
    op.drop_index(
        "ix_provider_entity_mappings_entity_type",
        table_name="provider_entity_mappings",
    )
    op.drop_index(
        "ix_provider_entity_mappings_provider",
        table_name="provider_entity_mappings",
    )
    op.drop_table("provider_entity_mappings")

    op.drop_index(
        "ix_provider_payloads_retained_until", table_name="provider_payloads"
    )
    op.drop_index(
        "ix_provider_payloads_fetched_at", table_name="provider_payloads"
    )
    op.drop_index(
        "ix_provider_payloads_payload_hash", table_name="provider_payloads"
    )
    op.drop_index(
        "ix_provider_payloads_external_id", table_name="provider_payloads"
    )
    op.drop_index(
        "ix_provider_payloads_entity_type", table_name="provider_payloads"
    )
    op.drop_index(
        "ix_provider_payloads_operation", table_name="provider_payloads"
    )
    op.drop_index("ix_provider_payloads_provider", table_name="provider_payloads")
    op.drop_table("provider_payloads")
