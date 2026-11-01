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
    op.add_column(
        "orders",
        sa.Column("paper_stop_event_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_orders_paper_stop_event_id",
        "orders",
        "paper_stop_events",
        ["paper_stop_event_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_unique_constraint(
        "uq_orders_paper_stop_event",
        "orders",
        ["paper_stop_event_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_orders_paper_stop_event", "orders", type_="unique")
    op.drop_constraint("fk_orders_paper_stop_event_id", "orders", type_="foreignkey")
    op.drop_column("orders", "paper_stop_event_id")
