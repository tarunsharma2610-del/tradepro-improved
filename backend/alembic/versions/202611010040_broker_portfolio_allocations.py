"""add exclusive owner-scoped broker to LIVE portfolio allocations

Revision ID: 202611010040
Revises: 202611010039
Create Date: 2026-11-01
"""
from alembic import op
import sqlalchemy as sa

revision = "202611010040"
down_revision = "202611010039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Composite foreign keys below enforce that the broker connection and
    # portfolio belong to the same user, and that the portfolio is LIVE.
    with op.batch_alter_table("portfolios") as batch_op:
        batch_op.create_unique_constraint("uq_portfolios_id_user", ["id", "user_id"])

    op.create_table(
        "broker_portfolio_allocations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("broker_connection_id", sa.Uuid(), nullable=False),
        sa.Column("portfolio_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("trading_mode", sa.String(length=5), server_default="LIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("broker_connection_id", name="uq_broker_portfolio_allocation_connection"),
        sa.UniqueConstraint("portfolio_id", name="uq_broker_portfolio_allocation_portfolio"),
        sa.CheckConstraint("trading_mode = 'LIVE'", name="ck_broker_portfolio_allocation_live_only"),
        sa.ForeignKeyConstraint(
            ["broker_connection_id", "user_id"],
            ["broker_connections.id", "broker_connections.user_id"],
            name="fk_broker_portfolio_allocation_connection_owner",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["portfolio_id", "user_id"],
            ["portfolios.id", "portfolios.user_id"],
            name="fk_broker_portfolio_allocation_portfolio_owner",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["portfolio_id", "trading_mode"],
            ["portfolios.id", "portfolios.trading_mode"],
            name="fk_broker_portfolio_allocation_live_portfolio",
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_broker_portfolio_allocations_broker_connection_id",
        "broker_portfolio_allocations", ["broker_connection_id"],
    )
    op.create_index(
        "ix_broker_portfolio_allocations_portfolio_id",
        "broker_portfolio_allocations", ["portfolio_id"],
    )
    op.create_index(
        "ix_broker_portfolio_allocations_user_id",
        "broker_portfolio_allocations", ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_broker_portfolio_allocations_user_id", table_name="broker_portfolio_allocations")
    op.drop_index("ix_broker_portfolio_allocations_portfolio_id", table_name="broker_portfolio_allocations")
    op.drop_index("ix_broker_portfolio_allocations_broker_connection_id", table_name="broker_portfolio_allocations")
    op.drop_table("broker_portfolio_allocations")
    with op.batch_alter_table("portfolios") as batch_op:
        batch_op.drop_constraint("uq_portfolios_id_user", type_="unique")
