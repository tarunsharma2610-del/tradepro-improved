"""Bind persisted live intents to the broker connection used at preflight.

Revision ID: 202610180013
Revises: 202610180012
Create Date: 2026-10-18
"""
from alembic import op
import sqlalchemy as sa


revision = "202610180013"
down_revision = "202610180012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Deliberately do not backfill legacy orders: the current connection may
    # differ from the account used when the intent was originally created.
    # Recovery fails closed for legacy rows until they are manually reconciled.
    with op.batch_alter_table("orders") as batch_op:
        batch_op.add_column(sa.Column("broker_connection_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_orders_broker_connection_id",
            "broker_connections",
            ["broker_connection_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index(
        "ix_orders_broker_connection_id",
        "orders",
        ["broker_connection_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_orders_broker_connection_id", table_name="orders")
    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_constraint("fk_orders_broker_connection_id", type_="foreignkey")
        batch_op.drop_column("broker_connection_id")
