"""Allow optional DP/demat canonical snapshots while keeping promotion blocked.

Revision ID: 202610260027
Revises: 202610250026
Create Date: 2026-10-26
"""
from alembic import op
import sqlalchemy as sa

revision = "202610260027"
down_revision = "202610250026"
branch_labels = None
depends_on = None

CORE_COMPONENTS = "'brokerage', 'stt', 'exchange_charges', 'sebi_charges', 'stamp_duty', 'gst'"
EXTENDED_COMPONENTS = CORE_COMPONENTS + ", 'demat_transaction_charges'"
CONSTRAINT = "ck_charge_canonical_component_name"


def _replace_check(expression: str) -> None:
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("broker_charge_canonical_components", recreate="always") as batch:
            batch.drop_constraint(CONSTRAINT, type_="check")
            batch.create_check_constraint(CONSTRAINT, expression)
    else:
        op.drop_constraint(CONSTRAINT, "broker_charge_canonical_components", type_="check")
        op.create_check_constraint(CONSTRAINT, "broker_charge_canonical_components", expression)


def upgrade() -> None:
    _replace_check(f"canonical_component IN ({EXTENDED_COMPONENTS})")


def downgrade() -> None:
    count = op.get_bind().execute(sa.text(
        "SELECT COUNT(*) FROM broker_charge_canonical_components "
        "WHERE canonical_component = 'demat_transaction_charges'"
    )).scalar_one()
    if count:
        raise RuntimeError(
            "Cannot downgrade canonical component vocabulary while DP/demat snapshots exist."
        )
    _replace_check(f"canonical_component IN ({CORE_COMPONENTS})")
