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
    # Batch mode is required for SQLite's table-rebuild approach to constraints.
    with op.batch_alter_table("broker_charge_allocations") as batch:
        batch.add_column(sa.Column("canonical_component_id", sa.Uuid(), nullable=True))
        batch.create_foreign_key(
            "fk_broker_charge_allocations_canonical_component_id",
            "broker_charge_canonical_components",
            ["canonical_component_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        batch.create_index(
            "ix_broker_charge_allocations_canonical_component_id",
            ["canonical_component_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("broker_charge_allocations") as batch:
        batch.drop_index("ix_broker_charge_allocations_canonical_component_id")
        batch.drop_constraint(
            "fk_broker_charge_allocations_canonical_component_id",
            type_="foreignkey",
        )
        batch.drop_column("canonical_component_id")
