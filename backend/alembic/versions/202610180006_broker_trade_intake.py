"""add broker child-order and trade-intake records for reconciliation

Revision ID: 202610180006
Revises: 202610170005
Create Date: 2026-10-18

Storage only: this migration does not submit orders or promote fills to accounting.
"""
from alembic import op
import sqlalchemy as sa

revision = "202610180006"
down_revision = "202610170005"
branch_labels = None
depends_on = None

uuid_type = sa.Uuid(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "broker_orders",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("broker_connection_id", uuid_type, sa.ForeignKey("broker_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("order_id", uuid_type, sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("broker_name", sa.String(50), nullable=False),
        sa.Column("broker_order_id", sa.String(128), nullable=False),
        sa.Column("requested_quantity", sa.Integer(), nullable=False),
        sa.Column("filled_quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.UniqueConstraint("broker_connection_id", "broker_order_id", name="uq_broker_order_connection_order"),
        sa.CheckConstraint("requested_quantity > 0", name="ck_broker_order_requested_quantity_positive"),
        sa.CheckConstraint(
            "filled_quantity >= 0 AND filled_quantity <= requested_quantity",
            name="ck_broker_order_filled_quantity_bounds",
        ),
    )
    op.create_index("ix_broker_orders_broker_connection_id", "broker_orders", ["broker_connection_id"])
    op.create_index("ix_broker_orders_order_id", "broker_orders", ["order_id"])

    op.create_table(
        "broker_trade_records",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("broker_connection_id", uuid_type, sa.ForeignKey("broker_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("broker_order_ref_id", uuid_type, sa.ForeignKey("broker_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("broker_trade_id", sa.String(128), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(18, 4), nullable=False),
        sa.Column("side", sa.String(4), nullable=False),
        sa.Column("instrument_token", sa.String(128), nullable=False),
        sa.Column("exchange_timestamp", sa.String(100), nullable=False),
        sa.UniqueConstraint("broker_connection_id", "broker_trade_id", name="uq_broker_trade_connection_trade"),
        sa.CheckConstraint("quantity > 0", name="ck_broker_trade_quantity_positive"),
        sa.CheckConstraint("price > 0", name="ck_broker_trade_price_positive"),
        sa.CheckConstraint("side IN ('BUY', 'SELL')", name="ck_broker_trade_side"),
    )
    op.create_index("ix_broker_trade_records_broker_connection_id", "broker_trade_records", ["broker_connection_id"])
    op.create_index("ix_broker_trade_records_broker_order_ref_id", "broker_trade_records", ["broker_order_ref_id"])


def downgrade() -> None:
    op.drop_index("ix_broker_trade_records_broker_order_ref_id", table_name="broker_trade_records")
    op.drop_index("ix_broker_trade_records_broker_connection_id", table_name="broker_trade_records")
    op.drop_table("broker_trade_records")
    op.drop_index("ix_broker_orders_order_id", table_name="broker_orders")
    op.drop_index("ix_broker_orders_broker_connection_id", table_name="broker_orders")
    op.drop_table("broker_orders")
