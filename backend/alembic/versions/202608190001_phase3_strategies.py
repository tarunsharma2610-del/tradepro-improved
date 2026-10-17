"""phase 3: strategies

Revision ID: 202608190001
Revises: 202608180001
Create Date: 2026-08-19

"""
from alembic import op
import sqlalchemy as sa

revision = "202608190001"
down_revision = "202608180001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "strategies",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("portfolio_id", sa.Uuid(), sa.ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("segment", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("rsi_weight", sa.Numeric(4, 2), nullable=False, server_default="1"),
        sa.Column("sma_crossover_weight", sa.Numeric(4, 2), nullable=False, server_default="1"),
        sa.Column("macd_weight", sa.Numeric(4, 2), nullable=False, server_default="1"),
        sa.Column("volume_spike_weight", sa.Numeric(4, 2), nullable=False, server_default="1"),
        sa.Column("momentum_weight", sa.Numeric(4, 2), nullable=False, server_default="1"),
        sa.Column("entry_score_threshold", sa.Numeric(4, 2), nullable=False, server_default="0.5"),
        sa.Column("exit_score_threshold", sa.Numeric(4, 2), nullable=False, server_default="-0.3"),
        sa.Column("trailing_stop_pct", sa.Numeric(5, 2), nullable=False, server_default="2"),
        sa.Column("max_daily_loss", sa.Numeric(18, 2), nullable=False),
        sa.Column("paused_until", sa.Date(), nullable=True),
        sa.Column("current_watermark", sa.Numeric(18, 4), nullable=True),
        sa.Column("last_evaluated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_strategies_portfolio_id", "strategies", ["portfolio_id"])
    op.create_index("ix_strategies_instrument_id", "strategies", ["instrument_id"])

    # strategy_id on orders was already a column (Phase 2 modeled it ahead
    # of time, unused) — link it to strategies now that the table exists.
    # batch_alter_table: SQLite can't ALTER TABLE ADD CONSTRAINT directly
    # (it needs the copy-and-recreate strategy); this is a no-op wrapper
    # on Postgres, which supports it natively.
    with op.batch_alter_table("orders") as batch_op:
        batch_op.create_foreign_key("fk_orders_strategy_id", "strategies", ["strategy_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_constraint("fk_orders_strategy_id", type_="foreignkey")
    op.drop_table("strategies")
