"""Add account-scoped idempotent broker trade intake records.

Revision ID: 202610180005
Revises: 202610170004
Create Date: 2026-10-18
"""
from alembic import op
import sqlalchemy as sa


revision = "202610180005"
down_revision = "202610170004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "broker_trade_records",
        sa.Column("broker_connection_id", sa.Uuid(), nullable=False),
        sa.Column("broker_order_ref_id", sa.Uuid(), nullable=False),
        sa.Column("broker_trade_id", sa.String(length=100), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(18, 4), nullable=False),
        sa.Column("side", sa.String(length=4), nullable=False),
        sa.Column("instrument_token", sa.String(length=100), nullable=True),
        sa.Column("exchange_timestamp", sa.String(length=100), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["broker_connection_id"], ["broker_connections.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["broker_order_ref_id"], ["broker_orders.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "broker_connection_id", "broker_trade_id",
            name="uq_broker_trade_connection_trade_id",
        ),
    )
    op.create_index(
        "ix_broker_trade_records_broker_connection_id",
        "broker_trade_records", ["broker_connection_id"], unique=False,
    )
    op.create_index(
        "ix_broker_trade_records_broker_order_ref_id",
        "broker_trade_records", ["broker_order_ref_id"], unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_broker_trade_records_broker_order_ref_id", table_name="broker_trade_records")
    op.drop_index("ix_broker_trade_records_broker_connection_id", table_name="broker_trade_records")
    op.drop_table("broker_trade_records")
