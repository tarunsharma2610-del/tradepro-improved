"""Persist canonical live-accounting component-set version.

Revision ID: 202610250022
Revises: 202610250021
Create Date: 2026-10-25
"""
from alembic import op
import sqlalchemy as sa

revision = "202610250022"
down_revision = "202610250021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Do not backfill: legacy and evidence-only rows have no verified canonical
    # component-set declaration and must fail closed until independently reviewed.
    op.add_column(
        "broker_charge_source_components",
        sa.Column("component_set_version", sa.String(length=80), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("broker_charge_source_components", "component_set_version")
