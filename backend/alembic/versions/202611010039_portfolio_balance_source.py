"""distinguish simulated and broker-sourced portfolio balances

Revision ID: 202611010039
Revises: 202611010038
Create Date: 2026-11-01
"""
from alembic import op
import sqlalchemy as sa

revision = "202611010039"
down_revision = "202611010038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing portfolios are PAPER by the preceding mode migration, so the
    # safe historical classification is SIMULATED. New LIVE portfolios are
    # explicitly created with UNAVAILABLE until a verified broker sync.
    with op.batch_alter_table("portfolios") as batch_op:
        batch_op.add_column(
            sa.Column(
                "balance_source",
                sa.String(length=16),
                nullable=False,
                server_default="SIMULATED",
            )
        )
        batch_op.create_check_constraint(
            "ck_portfolios_balance_source",
            "balance_source IN ('SIMULATED', 'UNAVAILABLE', 'BROKER')",
        )
        batch_op.create_check_constraint(
            "ck_portfolios_balance_source_mode",
            "(trading_mode = 'PAPER' AND balance_source = 'SIMULATED') OR "
            "(trading_mode = 'LIVE' AND balance_source IN ('UNAVAILABLE', 'BROKER'))",
        )


def downgrade() -> None:
    with op.batch_alter_table("portfolios") as batch_op:
        batch_op.drop_constraint("ck_portfolios_balance_source_mode", type_="check")
        batch_op.drop_constraint("ck_portfolios_balance_source", type_="check")
        batch_op.drop_column("balance_source")
