"""Distinguish unknown DP/demat charges from confirmed non-applicability.

Revision ID: 202610270029
Revises: 202610260028
Create Date: 2026-10-27
"""
from alembic import op
import sqlalchemy as sa

revision = "202610270029"
down_revision = "202610260028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "executions",
        sa.Column(
            "demat_charge_status",
            sa.String(length=20),
            nullable=False,
            server_default="UNKNOWN",
        ),
    )
    # Preserve any previously persisted explicit amount as known; NULL remains unknown.
    op.execute(sa.text(
        "UPDATE executions SET demat_charge_status = 'KNOWN' "
        "WHERE demat_transaction_charges IS NOT NULL"
    ))
    op.create_check_constraint(
        "ck_execution_demat_charge_status",
        "executions",
        "demat_charge_status IN ('UNKNOWN', 'NOT_APPLICABLE', 'KNOWN')",
    )
    op.create_check_constraint(
        "ck_execution_demat_charge_state_amount",
        "executions",
        "((demat_charge_status = 'KNOWN' AND demat_transaction_charges IS NOT NULL) "
        "OR (demat_charge_status IN ('UNKNOWN', 'NOT_APPLICABLE') "
        "AND demat_transaction_charges IS NULL))",
    )


def downgrade() -> None:
    known_count = op.get_bind().execute(sa.text(
        "SELECT COUNT(*) FROM executions WHERE demat_charge_status = 'KNOWN'"
    )).scalar_one()
    if known_count:
        raise RuntimeError(
            "Cannot downgrade while known execution DP/demat charge states are persisted."
        )
    op.drop_constraint("ck_execution_demat_charge_state_amount", "executions", type_="check")
    op.drop_constraint("ck_execution_demat_charge_status", "executions", type_="check")
    op.drop_column("executions", "demat_charge_status")
