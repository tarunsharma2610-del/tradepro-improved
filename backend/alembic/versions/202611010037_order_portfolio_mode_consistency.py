"""enforce order trading mode matches its portfolio

Revision ID: 202611010037
Revises: 202611010036
Create Date: 2026-11-01
"""
from alembic import op
import sqlalchemy as sa

revision = "202611010037"
down_revision = "202611010036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A composite candidate key lets the database enforce that an order's
    # declared mode is the same mode as its owning portfolio.
    with op.batch_alter_table("portfolios") as batch_op:
        batch_op.create_unique_constraint(
            "uq_portfolios_id_trading_mode",
            ["id", "trading_mode"],
        )

    with op.batch_alter_table("orders") as batch_op:
        batch_op.create_check_constraint(
            "ck_orders_trading_mode",
            "trading_mode IN ('PAPER', 'LIVE')",
        )
        batch_op.create_foreign_key(
            "fk_orders_portfolio_trading_mode",
            "portfolios",
            ["portfolio_id", "trading_mode"],
            ["id", "trading_mode"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_constraint("fk_orders_portfolio_trading_mode", type_="foreignkey")
        batch_op.drop_constraint("ck_orders_trading_mode", type_="check")

    with op.batch_alter_table("portfolios") as batch_op:
        batch_op.drop_constraint("uq_portfolios_id_trading_mode", type_="unique")
