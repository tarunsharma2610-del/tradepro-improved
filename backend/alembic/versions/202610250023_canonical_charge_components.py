"""Add durable canonical charge component snapshots.

Revision ID: 202610250023
Revises: 202610250022
Create Date: 2026-10-25
"""
from alembic import op
import sqlalchemy as sa

revision = "202610250023"
down_revision = "202610250022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "broker_charge_canonical_components",
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.Column("canonical_component", sa.String(length=30), nullable=False),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column("source_component_ids_json", sa.Text(), nullable=False),
        sa.Column("source_snapshot_sha256", sa.String(length=64), nullable=False),
        sa.Column("mapping_version", sa.String(length=80), nullable=False),
        sa.Column("representation_contract_version", sa.String(length=80), nullable=True),
        sa.Column("canonical_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column("component_set_version", sa.String(length=80), nullable=False),
        sa.Column("eligible_fill_ids_json", sa.Text(), nullable=True),
        sa.Column("eligible_fill_weights_json", sa.Text(), nullable=True),
        sa.Column("eligible_fill_set_sha256", sa.String(length=64), nullable=True),
        sa.Column("rounding_policy", sa.String(length=50), nullable=True),
        sa.Column("allocation_basis", sa.String(length=50), nullable=True),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="PENDING_REVIEW", nullable=False),
        sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "canonical_component IN ('brokerage', 'stt', 'exchange_charges', 'sebi_charges', 'stamp_duty', 'gst')",
            name="ck_charge_canonical_component_name",
        ),
        sa.CheckConstraint("canonical_amount >= 0", name="ck_charge_canonical_amount_nonnegative"),
        sa.CheckConstraint("revision > 0", name="ck_charge_canonical_revision_positive"),
        sa.CheckConstraint("currency = 'INR'", name="ck_charge_canonical_currency_inr"),
        sa.CheckConstraint("status IN ('PENDING_REVIEW', 'VERIFIED', 'REJECTED')", name="ck_charge_canonical_status"),
        sa.ForeignKeyConstraint(["evidence_id"], ["broker_charge_evidence.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evidence_id", "canonical_component", "revision", name="uq_charge_canonical_component_evidence_name_revision"),
        sa.UniqueConstraint("evidence_id", "canonical_component", "source_snapshot_sha256", name="uq_charge_canonical_component_source_snapshot"),
    )
    op.create_index(
        "ix_broker_charge_canonical_components_evidence_id",
        "broker_charge_canonical_components", ["evidence_id"], unique=False,
    )
    op.create_index(
        "ix_broker_charge_canonical_components_status",
        "broker_charge_canonical_components", ["status"], unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_broker_charge_canonical_components_status", table_name="broker_charge_canonical_components")
    op.drop_index("ix_broker_charge_canonical_components_evidence_id", table_name="broker_charge_canonical_components")
    op.drop_table("broker_charge_canonical_components")
