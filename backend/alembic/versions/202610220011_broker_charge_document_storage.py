"""Add private storage key for broker charge evidence source documents.

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


def downgrade() -> None:
    op.drop_column("broker_charge_evidence", "storage_key")
