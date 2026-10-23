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
    # Batch mode is required for SQLite migration round-trips because SQLite
    # cannot add a foreign-key constraint with ALTER TABLE ADD CONSTRAINT.
    with op.batch_alter_table("executions") as batch_op:
        batch_op.add_column(sa.Column("charge_evidence_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_executions_charge_evidence_id_broker_charge_evidence",
            "broker_charge_evidence",
            ["charge_evidence_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            "ix_executions_charge_evidence_id",
            ["charge_evidence_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("executions") as batch_op:
        batch_op.drop_index("ix_executions_charge_evidence_id")
        batch_op.drop_constraint(
            "fk_executions_charge_evidence_id_broker_charge_evidence",
            type_="foreignkey",
        )
        batch_op.drop_column("charge_evidence_id")
