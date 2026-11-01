"""add unique PAPER stop-event reference to orders

Revision ID: 202611010034
Revises: 202610300033
Create Date: 2026-11-01

The nullable unique reference makes duplicate order creation for one stop
event impossible at the database boundary. It does not enable a consumer.
"""
from alembic import op
import sqlalchemy as sa

revision = "202611010034"
down_revision = "202610300033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Batch mode is required for SQLite's table-rebuild implementation when
    # adding a foreign key; it also behaves correctly on PostgreSQL.
    with op.batch_alter_table("orders") as batch_op:
        batch_op.add_column(sa.Column("paper_stop_event_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_orders_paper_stop_event_id",
            "paper_stop_events",
            ["paper_stop_event_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch_op.create_unique_constraint(
            "uq_orders_paper_stop_event",
            ["paper_stop_event_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_constraint("uq_orders_paper_stop_event", type_="unique")
        batch_op.drop_constraint("fk_orders_paper_stop_event_id", type_="foreignkey")
        batch_op.drop_column("paper_stop_event_id")
