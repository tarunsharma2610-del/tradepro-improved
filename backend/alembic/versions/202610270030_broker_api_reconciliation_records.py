"""Persist immutable, owner-scoped aggregate broker API reconciliation snapshots.

Revision ID: 202610270030
Revises: 202610270029
Create Date: 2026-10-27
"""
from alembic import op
import sqlalchemy as sa

revision = "202610270030"
down_revision = "202610270029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "broker_api_reconciliation_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("broker_connection_id", sa.Uuid(), sa.ForeignKey("broker_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("broker", sa.String(32), nullable=False),
        sa.Column("endpoint", sa.String(200), nullable=False),
        sa.Column("api_version", sa.String(32), server_default="v2", nullable=False),
        sa.Column("request_scope_json", sa.Text(), nullable=False),
        sa.Column("fetched_at", sa.String(40), nullable=False),
        sa.Column("fetch_status", sa.String(32), nullable=False),
        sa.Column("http_status_code", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(100), nullable=True),
        sa.Column("evidence_kind", sa.String(40), server_default="AGGREGATE_RECONCILIATION_ONLY", nullable=False),
        sa.Column("per_fill_actual", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("response_sha256", sa.String(64), nullable=False),
        sa.Column("response_json", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.String(64), nullable=False),
        sa.CheckConstraint("length(idempotency_key) = 64", name="ck_broker_api_reconciliation_key_sha256"),
        sa.CheckConstraint("length(response_sha256) = 64", name="ck_broker_api_reconciliation_response_sha256"),
        sa.CheckConstraint("evidence_kind = 'AGGREGATE_RECONCILIATION_ONLY'", name="ck_broker_api_reconciliation_kind"),
        sa.CheckConstraint("per_fill_actual = false", name="ck_broker_api_reconciliation_not_per_fill_actual"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_broker_api_reconciliation_idempotency_key"),
    )
    op.create_index("ix_broker_api_reconciliation_user_id", "broker_api_reconciliation_records", ["user_id"])
    op.create_index("ix_broker_api_reconciliation_connection_id", "broker_api_reconciliation_records", ["broker_connection_id"])


def downgrade() -> None:
    op.drop_index("ix_broker_api_reconciliation_connection_id", table_name="broker_api_reconciliation_records")
    op.drop_index("ix_broker_api_reconciliation_user_id", table_name="broker_api_reconciliation_records")
    op.drop_table("broker_api_reconciliation_records")
