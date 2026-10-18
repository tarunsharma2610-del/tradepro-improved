"""Persist account-wide live kill switch and broker circuit breaker.

Revision ID: 202610180010
Revises: 202610180009
Create Date: 2026-10-18
"""
from alembic import op
import sqlalchemy as sa


revision = "202610180010"
down_revision = "202610180009"
branch_labels = None
depends_on = None


def _uuid_type():
    return sa.Uuid(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "live_account_safety_states",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", _uuid_type(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("broker", sa.String(50), nullable=False),
        sa.Column("kill_switch_tripped", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("kill_switch_reason", sa.String(500), nullable=True),
        sa.Column("kill_switch_tripped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("circuit_state", sa.String(20), nullable=False, server_default="CLOSED"),
        sa.Column("consecutive_broker_errors", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("circuit_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("circuit_reason", sa.String(500), nullable=True),
        sa.Column("last_broker_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_broker_error_code", sa.String(100), nullable=True),
        sa.Column("last_health_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("user_id", "broker", name="uq_live_account_safety_user_broker"),
    )
    op.create_index("ix_live_account_safety_states_user_id", "live_account_safety_states", ["user_id"])

    op.create_table(
        "live_account_safety_events",
        sa.Column("id", _uuid_type(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "state_id", _uuid_type(),
            sa.ForeignKey("live_account_safety_states.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("actor_user_id", _uuid_type(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("reason", sa.String(500), nullable=True),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("consecutive_broker_errors", sa.Integer(), nullable=False),
        sa.Column("circuit_state", sa.String(20), nullable=False),
        sa.Column("kill_switch_tripped", sa.Boolean(), nullable=False),
        sa.Column("state_version", sa.Integer(), nullable=False),
        sa.UniqueConstraint(
            "state_id", "idempotency_key",
            name="uq_live_account_safety_event_idempotency",
        ),
    )
    op.create_index("ix_live_account_safety_events_state_id", "live_account_safety_events", ["state_id"])
    op.create_index("ix_live_account_safety_events_actor_user_id", "live_account_safety_events", ["actor_user_id"])


def downgrade() -> None:
    op.drop_index("ix_live_account_safety_events_actor_user_id", table_name="live_account_safety_events")
    op.drop_index("ix_live_account_safety_events_state_id", table_name="live_account_safety_events")
    op.drop_table("live_account_safety_events")
    op.drop_index("ix_live_account_safety_states_user_id", table_name="live_account_safety_states")
    op.drop_table("live_account_safety_states")
