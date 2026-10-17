"""phase 4: backtest_runs, backtest_trades

Revision ID: 202608200001
Revises: 202608190001
Create Date: 2026-08-20

"""
from alembic import op
import sqlalchemy as sa

revision = "202608200001"
down_revision = "202608190001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "backtest_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("segment", sa.String(20), nullable=False),
        sa.Column("from_date", sa.Date(), nullable=False),
        sa.Column("to_date", sa.Date(), nullable=False),
        sa.Column("initial_capital", sa.Numeric(18, 2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("rsi_weight", sa.Numeric(4, 2), nullable=False, server_default="1"),
        sa.Column("sma_crossover_weight", sa.Numeric(4, 2), nullable=False, server_default="1"),
        sa.Column("macd_weight", sa.Numeric(4, 2), nullable=False, server_default="1"),
        sa.Column("volume_spike_weight", sa.Numeric(4, 2), nullable=False, server_default="1"),
        sa.Column("momentum_weight", sa.Numeric(4, 2), nullable=False, server_default="1"),
        sa.Column("entry_score_threshold", sa.Numeric(4, 2), nullable=False, server_default="0.5"),
        sa.Column("exit_score_threshold", sa.Numeric(4, 2), nullable=False, server_default="-0.3"),
        sa.Column("trailing_stop_pct", sa.Numeric(5, 2), nullable=False, server_default="2"),
        sa.Column("slippage_bps", sa.Numeric(6, 2), nullable=False, server_default="5"),
        sa.Column("status", sa.String(15), nullable=False, server_default="PENDING"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("final_capital", sa.Numeric(18, 2), nullable=True),
        sa.Column("net_pnl", sa.Numeric(18, 2), nullable=True),
        sa.Column("max_drawdown_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("total_trades", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("win_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("loss_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("candles_evaluated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_backtest_runs_user_id", "backtest_runs", ["user_id"])
    op.create_index("ix_backtest_runs_instrument_id", "backtest_runs", ["instrument_id"])

    op.create_table(
        "backtest_trades",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("backtest_run_id", sa.Uuid(), sa.ForeignKey("backtest_runs.id", ondelete="CASCADE"), nullable=False),
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
        sa.Column("candle_index", sa.Integer(), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_backtest_trades_backtest_run_id", "backtest_trades", ["backtest_run_id"])


def downgrade() -> None:
    op.drop_table("backtest_trades")
    op.drop_table("backtest_runs")
