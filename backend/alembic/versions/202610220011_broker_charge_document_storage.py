"""Add contract-note storage and uploader provenance to evidence records.

Revision ID: 202610220011
Revises: 202610220010
Create Date: 2026-10-22
"""
from alembic import op
import sqlalchemy as sa

revision = "202610220011"
down_revision = "202610220010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Batch mode supports adding the FK on SQLite while preserving PostgreSQL
    # behavior in the migration CI matrix.
    with op.batch_alter_table("broker_charge_evidence") as batch_op:
        batch_op.add_column(sa.Column("storage_key", sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column("received_by_user_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_charge_evidence_received_by_user_id_users",
            "users",
            ["received_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    with op.batch_alter_table("broker_charge_evidence") as batch_op:
        batch_op.drop_constraint(
            "fk_charge_evidence_received_by_user_id_users", type_="foreignkey"
        )
        batch_op.drop_column("received_by_user_id")
        batch_op.drop_column("storage_key")
