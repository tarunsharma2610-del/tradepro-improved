"""Persist the representation contract version used for source review.

Revision ID: 202610250021
Revises: 202610250020
Create Date: 2026-10-25
"""
from alembic import op
import sqlalchemy as sa

revision = "202610250021"
down_revision = "202610250020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable by design: old records have no reliable declaration and must not
    # be retroactively assigned the current contract version.
    op.add_column(
        "broker_charge_source_components",
        sa.Column("representation_contract_version", sa.String(length=80), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("broker_charge_source_components", "representation_contract_version")
