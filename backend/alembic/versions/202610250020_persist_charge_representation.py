"""Persist raw source label and representation mode for charge components.

Revision ID: 202610250020
Revises: 202610250019
Create Date: 2026-10-25
"""
from alembic import op
import sqlalchemy as sa

revision = "202610250020"
down_revision = "202610250019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "broker_charge_source_components",
        sa.Column("source_label", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "broker_charge_source_components",
        sa.Column("representation_mode", sa.String(length=50), nullable=True),
    )
    # Existing records have no reviewed representation declaration. Preserve
    # their auditability but do not infer a combined/split mode retroactively.
    op.execute(
        "UPDATE broker_charge_source_components "
        "SET source_label = component_name WHERE source_label IS NULL"
    )


def downgrade() -> None:
    op.drop_column("broker_charge_source_components", "representation_mode")
    op.drop_column("broker_charge_source_components", "source_label")
