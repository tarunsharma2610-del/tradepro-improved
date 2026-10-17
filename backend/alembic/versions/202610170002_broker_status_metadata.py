"""add broker status tracking metadata for future reconciliation

Revision ID: 202610170002
Revises: 202610170001
Create Date: 2026-10-17
"""
from alembic import op
import sqlalchemy as sa

revision = "202610170002"
down_revision = "202610170001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.add_column(sa.Column("broker_order_id", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("broker_status", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("broker_status_checked_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("broker_status_error", sa.String(length=500), nullable=True))
        batch_op.create_index("ix_orders_broker_order_id", ["broker_order_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_index("ix_orders_broker_order_id")
        batch_op.drop_column("broker_status_error")
        batch_op.drop_column("broker_status_checked_at")
        batch_op.drop_column("broker_status")
        batch_op.drop_column("broker_order_id")
