"""Enforce append-only tariff estimate snapshots at the database layer.

Revision ID: 202610240016
Revises: 202610240015
"""
from alembic import op

revision = "202610240016"
down_revision = "202610240015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        op.execute("""
            CREATE FUNCTION reject_tariff_estimate_snapshot_mutation()
            RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'tariff estimate snapshots are append-only';
            END;
            $$ LANGUAGE plpgsql
        """)
        op.execute("""
            CREATE TRIGGER trg_tariff_estimate_snapshot_immutable
            BEFORE UPDATE OR DELETE ON tariff_estimate_snapshot_records
            FOR EACH ROW EXECUTE FUNCTION reject_tariff_estimate_snapshot_mutation()
        """)
    elif dialect == "sqlite":
        op.execute("""
            CREATE TRIGGER trg_tariff_estimate_snapshot_no_update
            BEFORE UPDATE ON tariff_estimate_snapshot_records
            BEGIN
                SELECT RAISE(ABORT, 'tariff estimate snapshots are append-only');
            END
        """)
        op.execute("""
            CREATE TRIGGER trg_tariff_estimate_snapshot_no_delete
            BEFORE DELETE ON tariff_estimate_snapshot_records
            BEGIN
                SELECT RAISE(ABORT, 'tariff estimate snapshots are append-only');
            END
        """)
    else:
        raise RuntimeError(f"Unsupported database dialect for snapshot immutability: {dialect}")


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS trg_tariff_estimate_snapshot_immutable ON tariff_estimate_snapshot_records")
        op.execute("DROP FUNCTION IF EXISTS reject_tariff_estimate_snapshot_mutation()")
    elif dialect == "sqlite":
        op.execute("DROP TRIGGER IF EXISTS trg_tariff_estimate_snapshot_no_delete")
        op.execute("DROP TRIGGER IF EXISTS trg_tariff_estimate_snapshot_no_update")
