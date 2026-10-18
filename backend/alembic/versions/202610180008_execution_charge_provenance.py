"""Persist explicit execution charge provenance and DP charges.

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
                nullable=False,
                server_default="PAPER_ESTIMATE",
            )
        )
        batch_op.add_column(sa.Column("charge_reference", sa.String(length=200), nullable=True))
        batch_op.add_column(
            sa.Column("dp_charges", sa.Numeric(18, 2), nullable=False, server_default="0")
        )


def downgrade() -> None:
    with op.batch_alter_table("executions") as batch_op:
        batch_op.drop_column("dp_charges")
        batch_op.drop_column("charge_reference")
        batch_op.drop_column("charge_source")
