"""add durable client order idempotency key

Revision ID: 202610170001
Revises: 202608220001
Create Date: 2026-10-17
"""
from alembic import op
import sqlalchemy as sa

revision = "202610170001"
down_revision = "202608220001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Batch mode supports SQLite CI as well as PostgreSQL deployments.
    with op.batch_alter_table("orders") as batch_op:
        batch_op.add_column(sa.Column("idempotency_key", sa.String(length=100), nullable=True))
        batch_op.create_unique_constraint(
            "uq_orders_portfolio_idempotency_key",
            ["portfolio_id", "idempotency_key"],
        )


def downgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_constraint("uq_orders_portfolio_idempotency_key", type_="unique")
        batch_op.drop_column("idempotency_key")
