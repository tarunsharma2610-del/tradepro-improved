"""Persist desired user-scoped market-data subscriptions.

Revision ID: 202610300032
Revises: 202610300031
Create Date: 2026-10-30
"""
from alembic import op
import sqlalchemy as sa

revision = "202610300032"
down_revision = "202610300031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A unique index permits the composite tenant-scoped FK on SQLite and PostgreSQL.
    op.create_index("uq_broker_connection_id_user", "broker_connections", ["id", "user_id"], unique=True)
    op.create_table(
        "market_data_subscriptions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("broker_connection_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("feed_mode", sa.String(length=24), server_default="ltpc", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "feed_mode IN ('ltpc', 'option_greeks', 'full')",
            name="ck_market_subscription_feed_mode",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["broker_connection_id", "user_id"],
            ["broker_connections.id", "broker_connections.user_id"],
            ondelete="CASCADE",
            name="fk_market_subscription_broker_user",
        ),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "broker_connection_id", "instrument_id", "feed_mode",
            name="uq_market_subscription_user_broker_instrument_mode",
        ),
    )
    op.create_index("ix_market_data_subscriptions_user_id", "market_data_subscriptions", ["user_id"])
    op.create_index("ix_market_data_subscriptions_broker_connection_id", "market_data_subscriptions", ["broker_connection_id"])
    op.create_index("ix_market_data_subscriptions_instrument_id", "market_data_subscriptions", ["instrument_id"])


def downgrade() -> None:
    op.drop_index("ix_market_data_subscriptions_instrument_id", table_name="market_data_subscriptions")
    op.drop_index("ix_market_data_subscriptions_broker_connection_id", table_name="market_data_subscriptions")
    op.drop_index("ix_market_data_subscriptions_user_id", table_name="market_data_subscriptions")
    op.drop_table("market_data_subscriptions")
    op.drop_index("uq_broker_connection_id_user", table_name="broker_connections")
