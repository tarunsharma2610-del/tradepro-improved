"""Persist reviewed charge evidence identity on executions.

Revision ID: 202610240014
Revises: 202610230013
Create Date: 2026-10-24
"""
from alembic import op
import sqlalchemy as sa


revision = "202610240014"
down_revision = "202610230013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "executions",
        sa.Column("charge_evidence_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_executions_charge_evidence_id_broker_charge_evidence",
        "executions",
        "broker_charge_evidence",
        ["charge_evidence_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_executions_charge_evidence_id",
        "executions",
        ["charge_evidence_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_executions_charge_evidence_id", table_name="executions")
    op.drop_constraint(
        "fk_executions_charge_evidence_id_broker_charge_evidence",
        "executions",
        type_="foreignkey",
    )
    op.drop_column("executions", "charge_evidence_id")
