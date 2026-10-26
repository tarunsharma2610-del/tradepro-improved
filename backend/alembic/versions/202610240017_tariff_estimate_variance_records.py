"""Persist append-only estimate-versus-actual variance comparisons.

Revision ID: 202610240017
Revises: 202610240016
"""
from alembic import op
import sqlalchemy as sa

revision = "202610240017"
down_revision = "202610240016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tariff_estimate_variance_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("estimate_snapshot_id", sa.Uuid(), sa.ForeignKey("tariff_estimate_snapshot_records.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_component_id", sa.Uuid(), sa.ForeignKey("broker_charge_source_components.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("evidence_id", sa.Uuid(), sa.ForeignKey("broker_charge_evidence.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("component_name", sa.String(length=30), nullable=False),
        sa.Column("estimate_snapshot_sha256", sa.String(length=64), nullable=False),
        sa.Column("evidence_source_sha256", sa.String(length=64), nullable=False),
        sa.Column("estimated_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("actual_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("variance_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("variance_percent", sa.Numeric(18, 6), nullable=True),
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column("status", sa.String(length=20), server_default="VARIANCE_ONLY", nullable=False),
        sa.CheckConstraint("currency = 'INR'", name="ck_tariff_estimate_variance_currency_inr"),
        sa.CheckConstraint("estimated_amount >= 0", name="ck_tariff_estimate_variance_estimated_nonnegative"),
        sa.CheckConstraint("actual_amount >= 0", name="ck_tariff_estimate_variance_actual_nonnegative"),
        sa.CheckConstraint("status = 'VARIANCE_ONLY'", name="ck_tariff_estimate_variance_status"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("estimate_snapshot_id", "source_component_id", name="uq_tariff_estimate_variance_snapshot_component"),
    )
    op.create_index("ix_tariff_estimate_variance_records_estimate_snapshot_id", "tariff_estimate_variance_records", ["estimate_snapshot_id"])
    op.create_index("ix_tariff_estimate_variance_records_source_component_id", "tariff_estimate_variance_records", ["source_component_id"])
    op.create_index("ix_tariff_estimate_variance_records_evidence_id", "tariff_estimate_variance_records", ["evidence_id"])

    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        op.execute("""
            CREATE FUNCTION reject_tariff_estimate_variance_mutation()
            RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'tariff estimate variance records are append-only';
            END;
            $$ LANGUAGE plpgsql
        """)
        op.execute("""
            CREATE TRIGGER trg_tariff_estimate_variance_immutable
            BEFORE UPDATE OR DELETE ON tariff_estimate_variance_records
            FOR EACH ROW EXECUTE FUNCTION reject_tariff_estimate_variance_mutation()
        """)
    elif dialect == "sqlite":
        op.execute("""
            CREATE TRIGGER trg_tariff_estimate_variance_no_update
            BEFORE UPDATE ON tariff_estimate_variance_records
            BEGIN
                SELECT RAISE(ABORT, 'tariff estimate variance records are append-only');
            END
        """)
        op.execute("""
            CREATE TRIGGER trg_tariff_estimate_variance_no_delete
            BEFORE DELETE ON tariff_estimate_variance_records
            BEGIN
                SELECT RAISE(ABORT, 'tariff estimate variance records are append-only');
            END
        """)
    else:
        raise RuntimeError(f"Unsupported database dialect for variance immutability: {dialect}")


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS trg_tariff_estimate_variance_immutable ON tariff_estimate_variance_records")
        op.execute("DROP FUNCTION IF EXISTS reject_tariff_estimate_variance_mutation()")
    elif dialect == "sqlite":
        op.execute("DROP TRIGGER IF EXISTS trg_tariff_estimate_variance_no_delete")
        op.execute("DROP TRIGGER IF EXISTS trg_tariff_estimate_variance_no_update")
    op.drop_index("ix_tariff_estimate_variance_records_evidence_id", table_name="tariff_estimate_variance_records")
    op.drop_index("ix_tariff_estimate_variance_records_source_component_id", table_name="tariff_estimate_variance_records")
    op.drop_index("ix_tariff_estimate_variance_records_estimate_snapshot_id", table_name="tariff_estimate_variance_records")
    op.drop_table("tariff_estimate_variance_records")
