"""bind trading mode to portfolios with PAPER-only execution guard

Revision ID: 202611010036
Revises: 202611010035
Create Date: 2026-11-01
"""
from alembic import op
import sqlalchemy as sa

revision = "202611010036"
down_revision = "202611010035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("portfolios") as batch_op:
        batch_op.add_column(
            sa.Column("trading_mode", sa.String(length=5), nullable=False, server_default="PAPER")
        )
        batch_op.create_check_constraint(
            "ck_portfolios_trading_mode",
            "trading_mode IN ('PAPER', 'LIVE')",
        )


def downgrade() -> None:
    with op.batch_alter_table("portfolios") as batch_op:
        batch_op.drop_constraint("ck_portfolios_trading_mode", type_="check")
        batch_op.drop_column("trading_mode")
