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
    op.add_column(
        "broker_charge_evidence",
        sa.Column("storage_key", sa.String(length=500), nullable=True),
    )
    op.add_column(
        "broker_charge_evidence",
        sa.Column("received_by_user_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_charge_evidence_received_by_user_id_users",
        "broker_charge_evidence",
        "users",
        ["received_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_charge_evidence_received_by_user_id_users",
        "broker_charge_evidence",
        type_="foreignkey",
    )
    op.drop_column("broker_charge_evidence", "received_by_user_id")
    op.drop_column("broker_charge_evidence", "storage_key")
