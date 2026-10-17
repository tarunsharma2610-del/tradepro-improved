"""add durable manual-review issues for reconciliation

Revision ID: 202610170005
Revises: 202610170004
Create Date: 2026-10-17

Stores deduplicated safe issue metadata; no UI/API or broker write behavior.
"""
from alembic import op
import sqlalchemy as sa

revision = "202610170005"
down_revision = "202610170004"
branch_labels = None
depends_on = None

uuid_type = sa.Uuid(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "live_reconciliation_issues",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("broker_connection_id", uuid_type, sa.ForeignKey("broker_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_id", uuid_type, sa.ForeignKey("live_reconciliation_runs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("intent_id", uuid_type, sa.ForeignKey("live_order_intents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("issue_type", sa.String(50), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("broker_order_id", sa.String(128), nullable=True),
        sa.Column("broker_trade_id", sa.String(128), nullable=True),
        sa.Column("status", sa.String(16), server_default="OPEN", nullable=False),
        sa.Column("safe_details", sa.JSON(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("occurrence_count", sa.Integer(), server_default="1", nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "broker_connection_id", "fingerprint",
            name="uq_reconciliation_issue_connection_fingerprint",
        ),
        sa.CheckConstraint("occurrence_count >= 1", name="ck_reconciliation_issue_occurrence_positive"),
        sa.CheckConstraint("status IN ('OPEN', 'RESOLVED')", name="ck_reconciliation_issue_status"),
    )
    for column in ("user_id", "broker_connection_id", "run_id", "intent_id", "issue_type", "status"):
        op.create_index(f"ix_live_reconciliation_issues_{column}", "live_reconciliation_issues", [column])


def downgrade() -> None:
    for column in ("status", "issue_type", "intent_id", "run_id", "broker_connection_id", "user_id"):
        op.drop_index(f"ix_live_reconciliation_issues_{column}", table_name="live_reconciliation_issues")
    op.drop_table("live_reconciliation_issues")
