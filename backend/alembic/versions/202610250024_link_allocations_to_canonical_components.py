"""Link per-fill allocations to reviewed canonical source snapshots.

Revision ID: 202610250024
Revises: 202610250023
Create Date: 2026-10-25
"""
from alembic import op
import sqlalchemy as sa

revision = "202610250024"
down_revision = "202610250023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing allocations remain NULL: do not infer a canonical source snapshot
    # for historical rows without a reviewed source-to-canonical association.
    op.add_column(
        "broker_charge_allocations",
        sa.Column("canonical_component_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_broker_charge_allocations_canonical_component_id",
        "broker_charge_allocations",
        "broker_charge_canonical_components",
        ["canonical_component_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "ix_broker_charge_allocations_canonical_component_id",
        "broker_charge_allocations",
        ["canonical_component_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_broker_charge_allocations_canonical_component_id",
        table_name="broker_charge_allocations",
    )
    op.drop_constraint(
        "fk_broker_charge_allocations_canonical_component_id",
        "broker_charge_allocations",
        type_="foreignkey",
    )
    op.drop_column("broker_charge_allocations", "canonical_component_id")
