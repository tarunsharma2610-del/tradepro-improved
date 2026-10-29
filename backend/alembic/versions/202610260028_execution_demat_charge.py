"""Add optional DP/demat charge persistence to executions.

Revision ID: 202610260028
Revises: 202610260027
Create Date: 2026-10-26
"""
from alembic import op
import sqlalchemy as sa

revision = "202610260028"
down_revision = "202610260027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "executions",
        sa.Column("demat_transaction_charges", sa.Numeric(18, 2), nullable=True),
    )


def downgrade() -> None:
    count = op.get_bind().execute(sa.text(
        "SELECT COUNT(*) FROM executions WHERE demat_transaction_charges IS NOT NULL"
    )).scalar_one()
    if count:
        raise RuntimeError(
            "Cannot downgrade while execution DP/demat charge values are persisted."
        )
    op.drop_column("executions", "demat_transaction_charges")
