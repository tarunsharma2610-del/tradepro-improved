"""Scope broker child-order and execution trade IDs to broker connections.

Revision ID: 202610180006
Revises: 202610180005
Create Date: 2026-10-18
"""
from alembic import op
import sqlalchemy as sa


revision = "202610180006"
down_revision = "202610180005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable connection IDs preserve legacy orphan rows; ingestion fails
    # closed if a child order cannot be tied to the correct user connection.
    with op.batch_alter_table("broker_orders") as batch_op:
        batch_op.drop_constraint("uq_broker_orders_broker_order_id", type_="unique")
        batch_op.add_column(sa.Column("broker_connection_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_broker_orders_broker_connection_id", "broker_connections",
            ["broker_connection_id"], ["id"], ondelete="SET NULL",
        )
        batch_op.create_unique_constraint(
            "uq_broker_orders_connection_order_id",
            ["broker_connection_id", "broker_order_id"],
        )

    op.execute(sa.text("""
        UPDATE broker_orders
        SET broker_connection_id = (
            SELECT bc.id
            FROM orders o
            JOIN portfolios p ON p.id = o.portfolio_id
            JOIN broker_connections bc
              ON bc.user_id = p.user_id AND bc.broker = broker_orders.broker_name
            WHERE o.id = broker_orders.order_id
            LIMIT 1
        )
        WHERE broker_connection_id IS NULL
          AND (
              SELECT COUNT(*)
              FROM orders o
              JOIN portfolios p ON p.id = o.portfolio_id
              JOIN broker_connections bc
                ON bc.user_id = p.user_id AND bc.broker = broker_orders.broker_name
              WHERE o.id = broker_orders.order_id
          ) = 1
    """))
    op.create_index(
        "ix_broker_orders_broker_connection_id",
        "broker_orders", ["broker_connection_id"], unique=False,
    )

    with op.batch_alter_table("executions") as batch_op:
        batch_op.drop_constraint("uq_executions_broker_trade_id", type_="unique")
        batch_op.add_column(sa.Column("broker_connection_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_executions_broker_connection_id", "broker_connections",
            ["broker_connection_id"], ["id"], ondelete="SET NULL",
        )
        batch_op.create_unique_constraint(
            "uq_executions_connection_trade_id",
            ["broker_connection_id", "broker_trade_id"],
        )

    op.execute(sa.text("""
        UPDATE executions
        SET broker_connection_id = (
            SELECT bo.broker_connection_id
            FROM broker_orders bo
            WHERE bo.id = executions.broker_order_ref_id
        )
        WHERE broker_order_ref_id IS NOT NULL
          AND broker_connection_id IS NULL
          AND (
              SELECT COUNT(*)
              FROM broker_orders bo
              JOIN orders o ON o.id = bo.order_id
              JOIN portfolios p ON p.id = o.portfolio_id
              JOIN broker_connections bc
                ON bc.user_id = p.user_id AND bc.broker = bo.broker_name
              WHERE bo.id = executions.broker_order_ref_id
          ) = 1
    """))
    op.create_index(
        "ix_executions_broker_connection_id",
        "executions", ["broker_connection_id"], unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_executions_broker_connection_id", table_name="executions")
    with op.batch_alter_table("executions") as batch_op:
        batch_op.drop_constraint("uq_executions_connection_trade_id", type_="unique")
        batch_op.drop_constraint("fk_executions_broker_connection_id", type_="foreignkey")
        batch_op.drop_column("broker_connection_id")
        batch_op.create_unique_constraint(
            "uq_executions_broker_trade_id", ["broker_name", "broker_trade_id"]
        )

    op.drop_index("ix_broker_orders_broker_connection_id", table_name="broker_orders")
    with op.batch_alter_table("broker_orders") as batch_op:
        batch_op.drop_constraint("uq_broker_orders_connection_order_id", type_="unique")
        batch_op.drop_constraint("fk_broker_orders_broker_connection_id", type_="foreignkey")
        batch_op.drop_column("broker_connection_id")
        batch_op.create_unique_constraint(
            "uq_broker_orders_broker_order_id", ["broker_name", "broker_order_id"]
        )
