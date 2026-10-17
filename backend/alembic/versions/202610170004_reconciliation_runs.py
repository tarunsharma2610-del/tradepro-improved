"""add durable read-only reconciliation run summaries

Revision ID: 202610170004
Revises: 202610170003
Create Date: 2026-10-17

Stores count-only run summaries; it does not enable scheduling or broker writes.
"""
from alembic import op
import sqlalchemy as sa

revision = "202610170004"
down_revision = "202610170003"
branch_labels = None
depends_on = None

uuid_type = sa.Uuid(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "live_reconciliation_runs",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("broker_connection_id", uuid_type, sa.ForeignKey("broker_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), server_default="RUNNING", nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("summary", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('RUNNING', 'COMPLETED', 'COMPLETED_WITH_CONFLICTS', 'FAILED', 'LEASE_LOST')",
            name="ck_reconciliation_run_status",
        ),
    )
    op.create_index("ix_live_reconciliation_runs_user_id", "live_reconciliation_runs", ["user_id"])
    op.create_index("ix_live_reconciliation_runs_broker_connection_id", "live_reconciliation_runs", ["broker_connection_id"])
    op.create_index("ix_live_reconciliation_runs_status", "live_reconciliation_runs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_live_reconciliation_runs_status", table_name="live_reconciliation_runs")
    op.drop_index("ix_live_reconciliation_runs_broker_connection_id", table_name="live_reconciliation_runs")
    op.drop_index("ix_live_reconciliation_runs_user_id", table_name="live_reconciliation_runs")
    op.drop_table("live_reconciliation_runs")
