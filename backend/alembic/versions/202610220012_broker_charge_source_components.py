"""Add auditable, reviewed source component records for contract notes.

Revision ID: 202610220012
Revises: 202610220011
Create Date: 2026-10-22
"""
from alembic import op
import sqlalchemy as sa

revision = "202610220012"
down_revision = "202610220011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "broker_charge_source_components",
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("component_name", sa.String(length=30), nullable=False),
        sa.Column("revision", sa.Integer(), server_default="1", nullable=False),
        sa.Column("source_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column("extraction_method", sa.String(length=30), server_default="MANUAL_TRANSCRIPTION", nullable=False),
        sa.Column("parser_version", sa.String(length=50), server_default="manual-transcription-v1", nullable=False),
        sa.Column("source_locator", sa.String(length=200), nullable=False),
        sa.Column("eligible_fill_ids_json", sa.Text(), nullable=True),
        sa.Column("eligible_fill_set_sha256", sa.String(length=64), nullable=True),
        sa.Column("rounding_policy", sa.String(length=50), nullable=True),
        sa.Column("allocation_basis", sa.String(length=50), nullable=True),
        sa.Column("extracted_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="PENDING_REVIEW", nullable=False),
        sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "component_name IN ('brokerage', 'stt', 'exchange_charges', 'sebi_charges', 'stamp_duty', 'gst')",
            name="ck_charge_source_component_name",
        ),
        sa.CheckConstraint("source_amount >= 0", name="ck_charge_source_component_amount_nonnegative"),
        sa.CheckConstraint("revision > 0", name="ck_charge_source_component_revision_positive"),
        sa.CheckConstraint("currency = 'INR'", name="ck_charge_source_component_currency_inr"),
        sa.CheckConstraint(
            "extraction_method IN ('MANUAL_TRANSCRIPTION', 'PARSER')",
            name="ck_charge_source_component_extraction_method",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING_REVIEW', 'VERIFIED', 'REJECTED')",
            name="ck_charge_source_component_status",
        ),
        sa.ForeignKeyConstraint(["evidence_id"], ["broker_charge_evidence.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["extracted_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evidence_id", "component_name", "revision", name="uq_charge_source_component_evidence_name_revision"),
    )
    op.create_index("ix_broker_charge_source_components_evidence_id", "broker_charge_source_components", ["evidence_id"], unique=False)
    op.create_index("ix_broker_charge_source_components_status", "broker_charge_source_components", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_broker_charge_source_components_status", table_name="broker_charge_source_components")
    op.drop_index("ix_broker_charge_source_components_evidence_id", table_name="broker_charge_source_components")
    op.drop_table("broker_charge_source_components")
