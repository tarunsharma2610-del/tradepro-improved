"""add isolated live positions and broker provenance to executions

Revision ID: 202610180007
Revises: 202610180006
Create Date: 2026-10-18

Live positions are isolated by broker connection. Existing paper executions retain
NULL broker provenance and remain unaffected.
"""
from alembic import op
import sqlalchemy as sa

revision = "202610180007"
down_revision = "202610180006"
branch_labels = None
depends_on = None

uuid_type = sa.Uuid(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "live_positions",
        sa.Column("id", uuid_type, primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("broker_connection_id", uuid_type, sa.ForeignKey("broker_connections.id", ondelete="CASCADE"), nullable=False),
        sa.Column("instrument_id", uuid_type, sa.ForeignKey("instruments.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("avg_price", sa.Numeric(18, 4), server_default="0", nullable=False),
        sa.Column("realized_pnl", sa.Numeric(18, 2), server_default="0", nullable=False),
        sa.UniqueConstraint("broker_connection_id", "instrument_id", name="uq_live_position_connection_instrument"),
        sa.CheckConstraint("avg_price >= 0", name="ck_live_position_average_price_nonnegative"),
    )
    op.create_index("ix_live_positions_broker_connection_id", "live_positions", ["broker_connection_id"])
    op.create_index("ix_live_positions_instrument_id", "live_positions", ["instrument_id"])

    with op.batch_alter_table("executions") as batch_op:
        batch_op.add_column(sa.Column("strategy_realized_pnl", sa.Numeric(18, 2), nullable=True))
        batch_op.add_column(sa.Column("broker_order_ref_id", uuid_type, nullable=True))
        batch_op.add_column(sa.Column("broker_name", sa.String(50), nullable=True))
        batch_op.add_column(sa.Column("broker_connection_id", uuid_type, nullable=True))
        batch_op.add_column(sa.Column("broker_trade_id", sa.String(128), nullable=True))
        batch_op.create_foreign_key(
            "fk_executions_broker_order_ref_id_broker_orders",
            "broker_orders",
            ["broker_order_ref_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_executions_broker_connection_id_broker_connections",
            "broker_connections",
            ["broker_connection_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_executions_broker_order_ref_id", ["broker_order_ref_id"])
        batch_op.create_index("ix_executions_broker_connection_id", ["broker_connection_id"])
        batch_op.create_unique_constraint(
            "uq_execution_connection_broker_trade",
            ["broker_connection_id", "broker_trade_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("executions") as batch_op:
        batch_op.drop_constraint("uq_execution_connection_broker_trade", type_="unique")
        batch_op.drop_index("ix_executions_broker_connection_id")
        batch_op.drop_index("ix_executions_broker_order_ref_id")
        batch_op.drop_constraint("fk_executions_broker_connection_id_broker_connections", type_="foreignkey")
        batch_op.drop_constraint("fk_executions_broker_order_ref_id_broker_orders", type_="foreignkey")
        batch_op.drop_column("broker_trade_id")
        batch_op.drop_column("broker_connection_id")
        batch_op.drop_column("broker_name")
        batch_op.drop_column("broker_order_ref_id")
        batch_op.drop_column("strategy_realized_pnl")

    op.drop_index("ix_live_positions_instrument_id", table_name="live_positions")
    op.drop_index("ix_live_positions_broker_connection_id", table_name="live_positions")
    op.drop_table("live_positions")
