"""Persist reviewed per-fill allocation weights for charge source components.

Revision ID: 202610230013
Revises: 202610220012
Create Date: 2026-10-23
"""
from alembic import op
import sqlalchemy as sa

revision = "202610230013"
down_revision = "202610220012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "broker_charge_source_components",
        sa.Column("eligible_fill_weights_json", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("broker_charge_source_components", "eligible_fill_weights_json")
