"""add durable PAPER stop-event idempotency records

Revision ID: 202610300033
Revises: 202610300032
Create Date: 2026-10-30

Storage only. No event consumer or order execution is enabled by this migration.
"""
from alembic import op
import sqlalchemy as sa

revision = "202610300033"
down_revision = "202610300032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "paper_stop_events",
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("portfolio_id", sa.Uuid(), sa.ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("strategy_id", sa.Uuid(), sa.ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), sa.ForeignKey("instruments.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False, server_default="TRAILING_STOP"),
        sa.Column("quote_epoch", sa.String(length=128), nullable=False),
        sa.Column("quote_version", sa.Integer(), nullable=False),
        sa.Column("trigger_price", sa.Numeric(18, 4), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False, server_default="CLAIMED"),
        sa.Column("claim_token", sa.Uuid(), nullable=True),
        sa.Column("claimed_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error_code", sa.String(length=100), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "strategy_id", "event_type", "quote_epoch", "quote_version",
            name="uq_paper_stop_event_strategy_quote",
        ),
        sa.CheckConstraint("event_type IN ('TRAILING_STOP')", name="ck_paper_stop_event_type"),
        sa.CheckConstraint(
            "state IN ('CLAIMED', 'EXECUTING', 'COMPLETED', 'RETRYABLE', 'FAILED')",
            name="ck_paper_stop_event_state",
        ),
        sa.CheckConstraint("quote_version > 0", name="ck_paper_stop_event_quote_version"),
        sa.CheckConstraint("trigger_price > 0", name="ck_paper_stop_event_trigger_price"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_paper_stop_event_attempt_count"),
    )
    op.create_index("ix_paper_stop_events_user_state", "paper_stop_events", ["user_id", "state"])
    op.create_index("ix_paper_stop_events_portfolio_instrument", "paper_stop_events", ["portfolio_id", "instrument_id"])
    op.create_index("ix_paper_stop_events_claimed_until", "paper_stop_events", ["state", "claimed_until"])


def downgrade() -> None:
    op.drop_index("ix_paper_stop_events_claimed_until", table_name="paper_stop_events")
    op.drop_index("ix_paper_stop_events_portfolio_instrument", table_name="paper_stop_events")
    op.drop_index("ix_paper_stop_events_user_state", table_name="paper_stop_events")
    op.drop_table("paper_stop_events")
