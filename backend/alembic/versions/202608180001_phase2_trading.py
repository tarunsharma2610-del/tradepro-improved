"""phase 2: instruments, portfolios, orders, positions, executions

Revision ID: 202608180001
Revises: 202608170001
Create Date: 2026-08-18

"""
from alembic import op
import sqlalchemy as sa

revision = "202608180001"
down_revision = "202608170001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "instruments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("instrument_key", sa.String(100), nullable=False),
        sa.Column("exchange", sa.String(20), nullable=False),
        sa.Column("segment", sa.String(20), nullable=False),
        sa.Column("instrument_type", sa.String(20), nullable=False),
        sa.Column("trading_symbol", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("lot_size", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("tick_size", sa.Numeric(10, 4), nullable=False, server_default="0.05"),
        sa.Column("expiry", sa.Date(), nullable=True),
        sa.Column("strike_price", sa.Numeric(18, 4), nullable=True),
        sa.Column("option_type", sa.String(2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_instruments_instrument_key", "instruments", ["instrument_key"], unique=True)
    op.create_index("ix_instruments_trading_symbol", "instruments", ["trading_symbol"])

    op.create_table(
        "portfolios",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("virtual_capital", sa.Numeric(18, 2), nullable=False),
        sa.Column("cash_balance", sa.Numeric(18, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_portfolios_user_id", "portfolios", ["user_id"])

    op.create_table(
        "orders",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("portfolio_id", sa.Uuid(), sa.ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("side", sa.String(4), nullable=False),
        sa.Column("order_type", sa.String(10), nullable=False),
        sa.Column("segment", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("limit_price", sa.Numeric(18, 4), nullable=True),
        sa.Column("status", sa.String(15), nullable=False, server_default="PENDING"),
        sa.Column("rejection_reason", sa.String(500), nullable=True),
        sa.Column("trading_mode", sa.String(5), nullable=False, server_default="PAPER"),
        sa.Column("execution_reason", sa.String(20), nullable=False, server_default="MANUAL"),
        sa.Column("strategy_id", sa.Uuid(), nullable=True),
        sa.Column("placed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("filled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_orders_portfolio_id", "orders", ["portfolio_id"])
    op.create_index("ix_orders_instrument_id", "orders", ["instrument_id"])

    op.create_table(
        "positions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("portfolio_id", sa.Uuid(), sa.ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_price", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("realized_pnl", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.UniqueConstraint("portfolio_id", "instrument_id", name="uq_position_portfolio_instrument"),
    )
    op.create_index("ix_positions_portfolio_id", "positions", ["portfolio_id"])
    op.create_index("ix_positions_instrument_id", "positions", ["instrument_id"])

    op.create_table(
        "executions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("order_id", sa.Uuid(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("portfolio_id", sa.Uuid(), sa.ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("side", sa.String(4), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(18, 4), nullable=False),
        sa.Column("gross_value", sa.Numeric(18, 2), nullable=False),
        sa.Column("brokerage", sa.Numeric(18, 2), nullable=False),
        sa.Column("stt", sa.Numeric(18, 2), nullable=False),
        sa.Column("exchange_charges", sa.Numeric(18, 2), nullable=False),
        sa.Column("sebi_charges", sa.Numeric(18, 2), nullable=False),
        sa.Column("stamp_duty", sa.Numeric(18, 2), nullable=False),
        sa.Column("gst", sa.Numeric(18, 2), nullable=False),
        sa.Column("total_charges", sa.Numeric(18, 2), nullable=False),
        sa.Column("realized_pnl", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_executions_order_id", "executions", ["order_id"])
    op.create_index("ix_executions_portfolio_id", "executions", ["portfolio_id"])


def downgrade() -> None:
    op.drop_table("executions")
    op.drop_table("positions")
    op.drop_table("orders")
    op.drop_table("portfolios")
    op.drop_table("instruments")
