"""Add broker-scoped live positions, isolated from paper positions.

Revision ID: 202610180007
Revises: 202610180006
Create Date: 2026-10-18
"""
from alembic import op
import sqlalchemy as sa


revision = "202610180007"
down_revision = "202610180006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "live_positions",
        sa.Column("broker_connection_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("avg_price", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("realized_pnl", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["broker_connection_id"], ["broker_connections.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["instrument_id"], ["instruments.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "broker_connection_id",
            "instrument_id",
            name="uq_live_position_connection_instrument",
        ),
    )
    op.create_index(
        "ix_live_positions_broker_connection_id",
        "live_positions", ["broker_connection_id"], unique=False,
    )
    op.create_index(
        "ix_live_positions_instrument_id",
        "live_positions", ["instrument_id"], unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_live_positions_instrument_id", table_name="live_positions")
    op.drop_index("ix_live_positions_broker_connection_id", table_name="live_positions")
    op.drop_table("live_positions")
