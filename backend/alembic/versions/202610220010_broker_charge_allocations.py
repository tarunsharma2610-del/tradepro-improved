"""Add durable per-fill broker charge allocation ledger.

Revision ID: 202610220010
Revises: 202610210009
Create Date: 2026-10-22
"""
from alembic import op
import sqlalchemy as sa


revision = "202610220010"
down_revision = "202610210009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "broker_charge_allocations",
        sa.Column("evidence_id", sa.Uuid(), nullable=False),
        sa.Column("broker_connection_id", sa.Uuid(), nullable=False),
        sa.Column("broker_trade_record_id", sa.Uuid(), nullable=False),
        sa.Column("charge_component", sa.String(length=30), nullable=False),
        sa.Column("source_component_total", sa.Numeric(18, 2), nullable=False),
        sa.Column("allocated_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column("allocation_basis", sa.String(length=50), nullable=False),
        sa.Column("method_version", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="PENDING_RECONCILIATION", nullable=False),
        sa.Column("reconciliation_reference", sa.String(length=200), nullable=True),
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "charge_component IN ('brokerage', 'stt', 'exchange_charges', 'sebi_charges', 'stamp_duty', 'gst')",
            name="ck_charge_allocation_component",
        ),
        sa.CheckConstraint(
            "source_component_total >= 0 AND allocated_amount >= 0",
            name="ck_charge_allocation_nonnegative_amounts",
        ),
        sa.CheckConstraint("length(currency) = 3", name="ck_charge_allocation_currency_length"),
        sa.CheckConstraint(
            "status IN ('PENDING_RECONCILIATION', 'RECONCILED', 'REJECTED')",
            name="ck_charge_allocation_status",
        ),
        sa.ForeignKeyConstraint(["evidence_id"], ["broker_charge_evidence.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["broker_connection_id"], ["broker_connections.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["broker_trade_record_id"], ["broker_trade_records.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "evidence_id", "broker_trade_record_id", "charge_component",
            name="uq_charge_allocation_evidence_trade_component",
        ),
    )
    op.create_index("ix_broker_charge_allocations_evidence_id", "broker_charge_allocations", ["evidence_id"], unique=False)
    op.create_index("ix_broker_charge_allocations_broker_connection_id", "broker_charge_allocations", ["broker_connection_id"], unique=False)
    op.create_index("ix_broker_charge_allocations_broker_trade_record_id", "broker_charge_allocations", ["broker_trade_record_id"], unique=False)
    op.create_index("ix_broker_charge_allocations_status", "broker_charge_allocations", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_broker_charge_allocations_status", table_name="broker_charge_allocations")
    op.drop_index("ix_broker_charge_allocations_broker_trade_record_id", table_name="broker_charge_allocations")
    op.drop_index("ix_broker_charge_allocations_broker_connection_id", table_name="broker_charge_allocations")
    op.drop_index("ix_broker_charge_allocations_evidence_id", table_name="broker_charge_allocations")
    op.drop_table("broker_charge_allocations")
