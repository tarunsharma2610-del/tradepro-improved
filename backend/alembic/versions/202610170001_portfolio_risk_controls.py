"""add manually configurable portfolio risk controls

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
    op.add_column("portfolios", sa.Column("risk_controls_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("portfolios", sa.Column("max_daily_loss", sa.Numeric(18, 2), nullable=True))
    op.add_column("portfolios", sa.Column("max_open_exposure", sa.Numeric(18, 2), nullable=True))
    op.add_column("portfolios", sa.Column("max_order_value", sa.Numeric(18, 2), nullable=True))
    op.add_column("portfolios", sa.Column("max_open_positions", sa.Integer(), nullable=True))
    op.add_column("portfolios", sa.Column("max_orders_per_day", sa.Integer(), nullable=True))
    op.alter_column("portfolios", "risk_controls_enabled", server_default=None)


def downgrade() -> None:
    op.drop_column("portfolios", "max_orders_per_day")
    op.drop_column("portfolios", "max_open_positions")
    op.drop_column("portfolios", "max_order_value")
    op.drop_column("portfolios", "max_open_exposure")
    op.drop_column("portfolios", "max_daily_loss")
    op.drop_column("portfolios", "risk_controls_enabled")
