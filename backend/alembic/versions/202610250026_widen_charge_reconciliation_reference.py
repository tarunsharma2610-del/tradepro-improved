"""Widen durable canonical allocation reconciliation references.

Revision ID: 202610250026
Revises: 202610250025
Create Date: 2026-10-25
"""
from alembic import op
import sqlalchemy as sa

revision = "202610250026"
down_revision = "202610250025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # A complete reference includes a snapshot UUID, two SHA-256 fingerprints,
    # separators, and the allocation method version; 200 characters truncates
    # this required durable identity. Widen without changing existing values.
    with op.batch_alter_table("broker_charge_allocations") as batch_op:
        batch_op.alter_column(
            "reconciliation_reference",
            existing_type=sa.String(length=200),
            type_=sa.String(length=320),
            existing_nullable=True,
        )


def downgrade() -> None:
    # Do not silently truncate durable reconciliation identities on downgrade.
    bind = op.get_bind()
    too_long = bind.execute(sa.text(
        "SELECT COUNT(*) FROM broker_charge_allocations "
        "WHERE reconciliation_reference IS NOT NULL "
        "AND length(reconciliation_reference) > 200"
    )).scalar_one()
    if too_long:
        raise RuntimeError(
            "Cannot downgrade reconciliation_reference to 200 characters: "
            f"{too_long} durable reference(s) would be truncated."
        )
    with op.batch_alter_table("broker_charge_allocations") as batch_op:
        batch_op.alter_column(
            "reconciliation_reference",
            existing_type=sa.String(length=320),
            type_=sa.String(length=200),
            existing_nullable=True,
        )
