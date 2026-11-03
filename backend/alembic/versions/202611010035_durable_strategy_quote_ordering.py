"""persist the last accepted quote identity for PAPER strategy evaluation

Revision ID: 202611010035
Revises: 202611010034
Create Date: 2026-11-01
"""
from alembic import op
import sqlalchemy as sa

revision = "202611010035"
down_revision = "202611010034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("strategies") as batch_op:
        batch_op.add_column(sa.Column("last_quote_epoch", sa.String(length=128), nullable=True))
        batch_op.add_column(sa.Column("last_quote_version", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("last_quote_received_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("last_quote_exchange_timestamp_ms", sa.BigInteger(), nullable=True))
        batch_op.create_check_constraint(
            "ck_strategies_quote_identity_complete",
            "((last_quote_epoch IS NULL AND last_quote_version IS NULL "
            "AND last_quote_received_at IS NULL AND last_quote_exchange_timestamp_ms IS NULL) "
            "OR (last_quote_epoch IS NOT NULL AND length(last_quote_epoch) BETWEEN 1 AND 128 "
            "AND last_quote_version IS NOT NULL AND last_quote_version > 0 "
            "AND last_quote_received_at IS NOT NULL "
            "AND last_quote_exchange_timestamp_ms IS NOT NULL "
            "AND last_quote_exchange_timestamp_ms > 0))",
        )


def downgrade() -> None:
    with op.batch_alter_table("strategies") as batch_op:
        batch_op.drop_constraint("ck_strategies_quote_identity_complete", type_="check")
        batch_op.drop_column("last_quote_exchange_timestamp_ms")
        batch_op.drop_column("last_quote_received_at")
        batch_op.drop_column("last_quote_version")
        batch_op.drop_column("last_quote_epoch")
