"""Persist immutable estimate-only tariff snapshots.

Revision ID: 202610240015
Revises: 202610240014
Create Date: 2026-10-24
"""
from alembic import op
import sqlalchemy as sa

revision = "202610240015"
down_revision = "202610240014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tariff_estimate_snapshot_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("snapshot_sha256", sa.String(length=64), nullable=False),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="ESTIMATE_ONLY", nullable=False),
        sa.CheckConstraint("length(idempotency_key) = 64", name="ck_tariff_estimate_snapshot_key_sha256"),
        sa.CheckConstraint("length(snapshot_sha256) = 64", name="ck_tariff_estimate_snapshot_digest_sha256"),
        sa.CheckConstraint("status = 'ESTIMATE_ONLY'", name="ck_tariff_estimate_snapshot_estimate_only"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_tariff_estimate_snapshot_idempotency_key"),
    )


def downgrade() -> None:
    op.drop_table("tariff_estimate_snapshot_records")
