"""Record whether execution charges are estimates or broker-reported.

Revision ID: 202610180008
Revises: 202610180007
Create Date: 2026-10-18
"""
from alembic import op
import sqlalchemy as sa


revision = "202610180008"
down_revision = "202610180007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("executions") as batch_op:
        batch_op.add_column(
            sa.Column(
                "charge_source",
                sa.String(length=30),
                server_default="PAPER_ESTIMATE",
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("charge_reference", sa.String(length=200), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("executions") as batch_op:
        batch_op.drop_column("charge_reference")
        batch_op.drop_column("charge_source")
