"""add per-connection lease for read-only reconciliation worker

Revision ID: 202610170003
Revises: 202610170002
Create Date: 2026-10-17

The lease prevents concurrent workers from polling one broker connection at once.
It does not authorize or dispatch broker order writes.
"""
from alembic import op
import sqlalchemy as sa

revision = "202610170003"
down_revision = "202610170002"
branch_labels = None
depends_on = None

uuid_type = sa.Uuid(as_uuid=True)
json_type = sa.JSON()


def upgrade() -> None:
    op.create_table(
        "live_reconciliation_leases",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("user_id", uuid_type, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("broker_connection_id", uuid_type, sa.ForeignKey("broker_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lease_token", uuid_type, nullable=True),
        sa.Column("claimed_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("generation", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error_code", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("broker_connection_id", name="uq_reconciliation_lease_connection"),
        sa.CheckConstraint("generation >= 0", name="ck_reconciliation_lease_generation_nonnegative"),
    )
    op.create_index(
        "ix_live_reconciliation_leases_user_id", "live_reconciliation_leases", ["user_id"]
    )
    op.create_index(
        "ix_live_reconciliation_leases_broker_connection_id",
        "live_reconciliation_leases",
        ["broker_connection_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_live_reconciliation_leases_broker_connection_id",
        table_name="live_reconciliation_leases",
    )
    op.drop_index("ix_live_reconciliation_leases_user_id", table_name="live_reconciliation_leases")
    op.drop_table("live_reconciliation_leases")
