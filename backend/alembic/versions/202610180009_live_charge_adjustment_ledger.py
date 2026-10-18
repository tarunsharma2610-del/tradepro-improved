"""Add append-only, idempotent live charge adjustment ledger.

Revision ID: 202610180009
Revises: 202610180008
Create Date: 2026-10-18
"""
from alembic import op
import sqlalchemy as sa


revision = "202610180009"
down_revision = "202610180008"
branch_labels = None
depends_on = None


def _uuid_type():
    # SQLAlchemy Uuid remains portable across PostgreSQL and SQLite.
    return sa.Uuid(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "live_charge_adjustments",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "execution_id",
            _uuid_type(),
            sa.ForeignKey("executions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        # Historical identity snapshot intentionally has no FK: preserve audit
        # history and idempotency keys even if a broker connection is deleted.
        sa.Column("broker_connection_id", _uuid_type(), nullable=False),
        sa.Column("broker_trade_id", sa.String(length=100), nullable=False),
        sa.Column("adjustment_number", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=30), nullable=False, server_default="BROKER_REPORTED"),
        sa.Column("source_reference", sa.String(length=200), nullable=False),
        sa.Column("brokerage", sa.Numeric(18, 2), nullable=False),
        sa.Column("stt", sa.Numeric(18, 2), nullable=False),
        sa.Column("exchange_charges", sa.Numeric(18, 2), nullable=False),
        sa.Column("sebi_charges", sa.Numeric(18, 2), nullable=False),
        sa.Column("stamp_duty", sa.Numeric(18, 2), nullable=False),
        sa.Column("gst", sa.Numeric(18, 2), nullable=False),
        sa.Column("dp_charges", sa.Numeric(18, 2), nullable=False),
        sa.Column("previous_effective_total", sa.Numeric(18, 2), nullable=False),
        sa.Column("new_effective_total", sa.Numeric(18, 2), nullable=False),
        sa.Column("charge_delta", sa.Numeric(18, 2), nullable=False),
        sa.Column("net_realized_pnl_delta", sa.Numeric(18, 2), nullable=False),
        sa.UniqueConstraint(
            "broker_connection_id",
            "broker_trade_id",
            "source_reference",
            name="uq_live_charge_adjustment_trade_reference",
        ),
        sa.UniqueConstraint(
            "execution_id",
            "adjustment_number",
            name="uq_live_charge_adjustment_execution_number",
        ),
    )
    op.create_index(
        "ix_live_charge_adjustments_execution_id",
        "live_charge_adjustments",
        ["execution_id"],
    )
    op.create_index(
        "ix_live_charge_adjustments_broker_connection_id",
        "live_charge_adjustments",
        ["broker_connection_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_live_charge_adjustments_broker_connection_id", table_name="live_charge_adjustments")
    op.drop_index("ix_live_charge_adjustments_execution_id", table_name="live_charge_adjustments")
    op.drop_table("live_charge_adjustments")
