"""Expand source-component vocabulary for documented Upstox charge fields.

Revision ID: 202610250019
Revises: 202610240018
Create Date: 2026-10-25
"""
from alembic import op
import sqlalchemy as sa

revision = "202610250019"
down_revision = "202610240018"
branch_labels = None
depends_on = None

COMPONENTS = (
    "'brokerage', 'stt', 'exchange_charges', 'transaction_charges', "
    "'clearing_charges', 'ipft', 'other_charges', 'demat_transaction_charges', "
    "'sebi_charges', 'stamp_duty', 'gst'"
)
OLD_COMPONENTS = "'brokerage', 'stt', 'exchange_charges', 'sebi_charges', 'stamp_duty', 'gst'"


def _replace_check(table: str, name: str, column: str, expression: str) -> None:
    dialect = op.get_bind().dialect.name
    if dialect == "sqlite":
        # SQLite cannot drop a CHECK constraint in place; batch mode rebuilds
        # the table while preserving rows, foreign keys and the other constraints.
        with op.batch_alter_table(table, recreate="always") as batch:
            batch.drop_constraint(name, type_="check")
            batch.create_check_constraint(name, expression)
    else:
        op.drop_constraint(name, table, type_="check")
        op.create_check_constraint(name, table, expression)


def upgrade() -> None:
    _replace_check(
        "broker_charge_source_components",
        "ck_charge_source_component_name",
        "component_name",
        f"component_name IN ({COMPONENTS})",
    )
    _replace_check(
        "broker_charge_allocations",
        "ck_charge_allocation_component",
        "charge_component",
        f"charge_component IN ({COMPONENTS})",
    )


def downgrade() -> None:
    # Downgrade is intentionally strict: rows using the expanded vocabulary
    # must be reviewed/removed before returning to the older six-component schema.
    bind = op.get_bind()
    for table, column in (
        ("broker_charge_source_components", "component_name"),
        ("broker_charge_allocations", "charge_component"),
    ):
        count = bind.execute(
            sa.text(
                f"SELECT COUNT(*) FROM {table} WHERE {column} IN "
                "('transaction_charges', 'clearing_charges', 'ipft', "
                "'other_charges', 'demat_transaction_charges')"
            )
        ).scalar_one()
        if count:
            raise RuntimeError(
                f"Cannot downgrade {table}: expanded charge components are present."
            )
    _replace_check(
        "broker_charge_allocations",
        "ck_charge_allocation_component",
        "charge_component",
        f"charge_component IN ({OLD_COMPONENTS})",
    )
    _replace_check(
        "broker_charge_source_components",
        "ck_charge_source_component_name",
        "component_name",
        f"component_name IN ({OLD_COMPONENTS})",
    )
