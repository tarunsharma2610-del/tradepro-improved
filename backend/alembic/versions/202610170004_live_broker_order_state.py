"""Additive data model for broker child orders and deduplicated live trades.

Revision ID: 202610170004
Revises: 202610170003
Create Date: 2026-10-17
"""
from alembic import op
import sqlalchemy as sa


revision = "202610170004"
down_revision = "202610170003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extend the status column before adding the future PARTIALLY_FILLED and
    # SUBMISSION_UNKNOWN states. Batch mode also supports existing SQLite DBs.
    with op.batch_alter_table("orders") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=15),
            type_=sa.String(length=30),
            existing_nullable=False,
        )
        batch_op.add_column(sa.Column("broker_tag", sa.String(length=40), nullable=True))
        batch_op.create_unique_constraint("uq_orders_broker_tag", ["broker_tag"])

    op.create_table(
        "broker_orders",
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("broker_name", sa.String(length=20), nullable=False),
        sa.Column("broker_order_id", sa.String(length=100), nullable=False),
        sa.Column("broker_tag", sa.String(length=40), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="UNKNOWN"),
        sa.Column("requested_quantity", sa.Integer(), nullable=True),
        sa.Column("filled_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("average_fill_price", sa.Numeric(18, 4), nullable=True),
        sa.Column("status_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("broker_name", "broker_order_id", name="uq_broker_orders_broker_order_id"),
    )
    op.create_index("ix_broker_orders_order_id", "broker_orders", ["order_id"], unique=False)
    op.create_index("ix_broker_orders_broker_tag", "broker_orders", ["broker_tag"], unique=False)

    with op.batch_alter_table("executions") as batch_op:
        batch_op.add_column(sa.Column("broker_order_ref_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("broker_name", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("broker_trade_id", sa.String(length=100), nullable=True))
        batch_op.create_foreign_key(
            "fk_executions_broker_order_ref_id",
            "broker_orders",
            ["broker_order_ref_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_unique_constraint(
            "uq_executions_broker_trade_id", ["broker_name", "broker_trade_id"]
        )

    op.create_index("ix_executions_broker_order_ref_id", "executions", ["broker_order_ref_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_executions_broker_order_ref_id", table_name="executions")
    with op.batch_alter_table("executions") as batch_op:
        batch_op.drop_constraint("uq_executions_broker_trade_id", type_="unique")
        batch_op.drop_constraint("fk_executions_broker_order_ref_id", type_="foreignkey")
        batch_op.drop_column("broker_trade_id")
        batch_op.drop_column("broker_name")
        batch_op.drop_column("broker_order_ref_id")

    op.drop_index("ix_broker_orders_broker_tag", table_name="broker_orders")
    op.drop_index("ix_broker_orders_order_id", table_name="broker_orders")
    op.drop_table("broker_orders")

    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_constraint("uq_orders_broker_tag", type_="unique")
        batch_op.drop_column("broker_tag")
        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=30),
            type_=sa.String(length=15),
            existing_nullable=False,
        )
