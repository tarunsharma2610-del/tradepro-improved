"""enforce execution order and portfolio ownership consistency

Revision ID: 202611010038
Revises: 202611010037
Create Date: 2026-11-01
"""
from alembic import op
import sqlalchemy as sa

revision = "202611010038"
down_revision = "202611010037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Fail closed rather than silently rewriting any historical execution
    # whose portfolio does not match the referenced order.
    connection = op.get_bind()
    mismatches = connection.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM executions AS execution
            JOIN orders AS trading_order ON trading_order.id = execution.order_id
            WHERE execution.portfolio_id <> trading_order.portfolio_id
            """
        )
    ).scalar_one()
    if mismatches:
        raise RuntimeError(
            f"Cannot enforce execution ownership: found {mismatches} execution/order portfolio mismatches."
        )

    # The composite candidate key is required by the database FK below.
    with op.batch_alter_table("orders") as batch_op:
        batch_op.create_unique_constraint(
            "uq_orders_id_portfolio_id",
            ["id", "portfolio_id"],
        )

    with op.batch_alter_table("executions") as batch_op:
        batch_op.create_foreign_key(
            "fk_executions_order_portfolio",
            "orders",
            ["order_id", "portfolio_id"],
            ["id", "portfolio_id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("executions") as batch_op:
        batch_op.drop_constraint(
            "fk_executions_order_portfolio",
            type_="foreignkey",
        )

    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_constraint(
            "uq_orders_id_portfolio_id",
            type_="unique",
        )
