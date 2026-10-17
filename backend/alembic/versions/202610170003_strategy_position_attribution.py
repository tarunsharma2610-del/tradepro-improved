"""track strategy-owned position allocations and strategy-specific realized P&L

Revision ID: 202610170003
Revises: 202610170002
Create Date: 2026-10-17
"""
from alembic import op
import sqlalchemy as sa


revision = "202610170003"
down_revision = "202610170002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("executions", sa.Column("strategy_realized_pnl", sa.Numeric(18, 2), nullable=True))
    op.create_table(
        "strategy_positions",
        sa.Column("strategy_id", sa.Uuid(), nullable=False),
        sa.Column("portfolio_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_price", sa.Numeric(18, 4), nullable=False, server_default="0"),
        sa.Column("realized_pnl", sa.Numeric(18, 2), nullable=False, server_default="0"),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["strategy_id"], ["strategies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["portfolio_id"], ["portfolios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("strategy_id", name="uq_strategy_position_strategy_id"),
    )
    op.create_index("ix_strategy_positions_portfolio_id", "strategy_positions", ["portfolio_id"], unique=False)
    op.create_index("ix_strategy_positions_instrument_id", "strategy_positions", ["instrument_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_strategy_positions_instrument_id", table_name="strategy_positions")
    op.drop_index("ix_strategy_positions_portfolio_id", table_name="strategy_positions")
    op.drop_table("strategy_positions")
    op.drop_column("executions", "strategy_realized_pnl")
