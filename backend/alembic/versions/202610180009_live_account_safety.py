"""Create persistent account-wide live kill-switch and circuit-breaker state.

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


def upgrade() -> None:
    op.create_table(
        "live_account_safety_states",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("broker", sa.String(length=50), nullable=False),
        sa.Column("kill_switch_tripped", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("kill_switch_reason", sa.String(length=500), nullable=True),
        sa.Column("kill_switch_tripped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("circuit_state", sa.String(length=20), server_default="CLOSED", nullable=False),
        sa.Column("consecutive_broker_errors", sa.Integer(), server_default="0", nullable=False),
        sa.Column("circuit_opened_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("circuit_reason", sa.String(length=500), nullable=True),
        sa.Column("last_broker_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_broker_error_code", sa.String(length=100), nullable=True),
        sa.Column("last_health_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "broker", name="uq_live_account_safety_user_broker"),
    )
    op.create_index("ix_live_account_safety_states_user_id", "live_account_safety_states", ["user_id"])

    op.create_table(
        "live_account_safety_events",
        sa.Column("state_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("consecutive_broker_errors", sa.Integer(), nullable=False),
        sa.Column("circuit_state", sa.String(length=20), nullable=False),
        sa.Column("kill_switch_tripped", sa.Boolean(), nullable=False),
        sa.Column("state_version", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["state_id"], ["live_account_safety_states.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("state_id", "idempotency_key", name="uq_live_account_safety_event_idempotency"),
    )
    op.create_index("ix_live_account_safety_events_state_id", "live_account_safety_events", ["state_id"])
    op.create_index("ix_live_account_safety_events_actor_user_id", "live_account_safety_events", ["actor_user_id"])


def downgrade() -> None:
    op.drop_index("ix_live_account_safety_events_actor_user_id", table_name="live_account_safety_events")
    op.drop_index("ix_live_account_safety_events_state_id", table_name="live_account_safety_events")
    op.drop_table("live_account_safety_events")
    op.drop_index("ix_live_account_safety_states_user_id", table_name="live_account_safety_states")
    op.drop_table("live_account_safety_states")
