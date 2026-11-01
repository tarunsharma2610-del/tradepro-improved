"""persist immutable broker position snapshots

Revision ID: 202611010042
Revises: 202611010041
Create Date: 2026-11-01
"""
from alembic import op
import sqlalchemy as sa

revision = "202611010042"
down_revision = "202611010041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "broker_position_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("broker_connection_id", sa.Uuid(), nullable=False),
        sa.Column("portfolio_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("trading_mode", sa.String(length=5), server_default="LIVE", nullable=False),
        sa.Column("positions", sa.JSON(), nullable=False),
        sa.Column("raw_response", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("trading_mode = 'LIVE'", name="ck_broker_position_snapshot_live_only"),
        sa.ForeignKeyConstraint(
            ["broker_connection_id", "user_id"],
            ["broker_connections.id", "broker_connections.user_id"],
            name="fk_broker_position_snapshot_connection_owner",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["portfolio_id", "user_id"],
            ["portfolios.id", "portfolios.user_id"],
            name="fk_broker_position_snapshot_portfolio_owner",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["portfolio_id", "trading_mode"],
            ["portfolios.id", "portfolios.trading_mode"],
            name="fk_broker_position_snapshot_live_portfolio",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_broker_position_snapshots_broker_connection_id", "broker_position_snapshots", ["broker_connection_id"])
    op.create_index("ix_broker_position_snapshots_portfolio_id", "broker_position_snapshots", ["portfolio_id"])
    op.create_index("ix_broker_position_snapshots_user_id", "broker_position_snapshots", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_broker_position_snapshots_user_id", table_name="broker_position_snapshots")
    op.drop_index("ix_broker_position_snapshots_portfolio_id", table_name="broker_position_snapshots")
    op.drop_index("ix_broker_position_snapshots_broker_connection_id", table_name="broker_position_snapshots")
    op.drop_table("broker_position_snapshots")
