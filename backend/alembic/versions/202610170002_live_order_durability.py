"""add durable live-order intents, audit events, outbox and broker fill identities

Revision ID: 202610170002
Revises: 202610170001
Create Date: 2026-10-17

Phase 1 storage only. No live broker submission or reconciliation worker is enabled.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "202610170002"
down_revision = "202610170001"
branch_labels = None
depends_on = None

uuid_type = sa.Uuid(as_uuid=True)
json_type = sa.JSON()


def upgrade() -> None:
    op.create_table(
        "live_order_intents",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("portfolio_id", uuid_type, sa.ForeignKey("portfolios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("broker_connection_id", uuid_type, sa.ForeignKey("broker_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_idempotency_key", sa.String(128), nullable=False),
        sa.Column("request_hash", sa.String(64), nullable=False),
        sa.Column("order_snapshot", json_type, nullable=False),
        sa.Column("state", sa.String(32), server_default="CREATED", nullable=False),
        sa.Column("broker_order_id", sa.String(128), nullable=True),
        sa.Column("broker_tag", sa.String(64), nullable=True),
        sa.Column("submit_attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_submit_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_reconciled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(100), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "broker_connection_id", "client_idempotency_key", name="uq_live_intent_user_connection_key"),
        sa.UniqueConstraint("broker_connection_id", "broker_order_id", name="uq_live_intent_connection_broker_order"),
        sa.CheckConstraint("submit_attempt_count >= 0", name="ck_live_intent_attempt_count_nonnegative"),
        sa.CheckConstraint("version >= 1", name="ck_live_intent_version_positive"),
    )
    op.create_index("ix_live_order_intents_user_id", "live_order_intents", ["user_id"])
    op.create_index("ix_live_order_intents_portfolio_id", "live_order_intents", ["portfolio_id"])
    op.create_index("ix_live_order_intents_broker_connection_id", "live_order_intents", ["broker_connection_id"])
    op.create_index("ix_live_order_intents_state", "live_order_intents", ["state"])

    op.create_table(
        "live_order_events",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("intent_id", uuid_type, sa.ForeignKey("live_order_intents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("correlation_id", sa.String(100), nullable=True),
        sa.Column("actor_user_id", uuid_type, sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("safe_details", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_live_order_events_intent_id", "live_order_events", ["intent_id"])
    op.create_index("ix_live_order_events_event_type", "live_order_events", ["event_type"])

    op.create_table(
        "live_order_submit_outbox",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("intent_id", uuid_type, sa.ForeignKey("live_order_intents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(24), server_default="READY", nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("claim_token", uuid_type, nullable=True),
        sa.Column("claimed_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error_code", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("intent_id", name="uq_live_outbox_intent"),
        sa.CheckConstraint("attempt_count >= 0", name="ck_live_outbox_attempt_count_nonnegative"),
    )
    op.create_index("ix_live_order_submit_outbox_status", "live_order_submit_outbox", ["status"])

    op.create_table(
        "broker_fill_identities",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("broker_connection_id", uuid_type, sa.ForeignKey("broker_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("intent_id", uuid_type, sa.ForeignKey("live_order_intents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("broker_order_id", sa.String(128), nullable=False),
        sa.Column("broker_trade_id", sa.String(128), nullable=False),
        sa.Column("instrument_key", sa.String(128), nullable=False),
        sa.Column("side", sa.String(4), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price", sa.Numeric(18, 4), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("safe_details", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("broker_connection_id", "broker_trade_id", name="uq_broker_fill_connection_trade"),
        sa.CheckConstraint("quantity > 0", name="ck_broker_fill_quantity_positive"),
        sa.CheckConstraint("price > 0", name="ck_broker_fill_price_positive"),
    )
    op.create_index("ix_broker_fill_identities_broker_connection_id", "broker_fill_identities", ["broker_connection_id"])
    op.create_index("ix_broker_fill_identities_intent_id", "broker_fill_identities", ["intent_id"])


def downgrade() -> None:
    op.drop_index("ix_broker_fill_identities_intent_id", table_name="broker_fill_identities")
    op.drop_index("ix_broker_fill_identities_broker_connection_id", table_name="broker_fill_identities")
    op.drop_table("broker_fill_identities")
    op.drop_index("ix_live_order_submit_outbox_status", table_name="live_order_submit_outbox")
    op.drop_table("live_order_submit_outbox")
    op.drop_index("ix_live_order_events_event_type", table_name="live_order_events")
    op.drop_index("ix_live_order_events_intent_id", table_name="live_order_events")
    op.drop_table("live_order_events")
    op.drop_index("ix_live_order_intents_state", table_name="live_order_intents")
    op.drop_index("ix_live_order_intents_broker_connection_id", table_name="live_order_intents")
    op.drop_index("ix_live_order_intents_portfolio_id", table_name="live_order_intents")
    op.drop_index("ix_live_order_intents_user_id", table_name="live_order_intents")
    op.drop_table("live_order_intents")
