"""Add replay fingerprints and database-enforced safety-event immutability.

Revision ID: 202610180011
Revises: 202610180010
Create Date: 2026-10-18
"""
from alembic import op
import sqlalchemy as sa


revision = "202610180011"
down_revision = "202610180010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Historical rows remain NULL and cannot be replayed as if their original
    # request payload were known. All new service writes must provide a SHA-256.
    with op.batch_alter_table("live_account_safety_events") as batch:
        batch.add_column(sa.Column("request_fingerprint", sa.String(64), nullable=True))
        batch.create_unique_constraint(
            "uq_live_account_safety_event_state_version",
            ["state_id", "state_version"],
        )

    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.execute("""
            CREATE OR REPLACE FUNCTION reject_live_account_safety_event_mutation()
            RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'live account safety events are append-only';
            END;
            $$ LANGUAGE plpgsql
        """)
        op.execute("""
            CREATE TRIGGER trg_live_account_safety_events_no_update
            BEFORE UPDATE ON live_account_safety_events
            FOR EACH ROW EXECUTE FUNCTION reject_live_account_safety_event_mutation()
        """)
        op.execute("""
            CREATE TRIGGER trg_live_account_safety_events_no_delete
            BEFORE DELETE ON live_account_safety_events
            FOR EACH ROW EXECUTE FUNCTION reject_live_account_safety_event_mutation()
        """)
    elif dialect == "sqlite":
        op.execute("""
            CREATE TRIGGER trg_live_account_safety_events_no_update
            BEFORE UPDATE ON live_account_safety_events
            BEGIN
                SELECT RAISE(ABORT, 'live account safety events are append-only');
            END
        """)
        op.execute("""
            CREATE TRIGGER trg_live_account_safety_events_no_delete
            BEFORE DELETE ON live_account_safety_events
            BEGIN
                SELECT RAISE(ABORT, 'live account safety events are append-only');
            END
        """)


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS trg_live_account_safety_events_no_update ON live_account_safety_events")
        op.execute("DROP TRIGGER IF EXISTS trg_live_account_safety_events_no_delete ON live_account_safety_events")
        op.execute("DROP FUNCTION IF EXISTS reject_live_account_safety_event_mutation()")
    elif dialect == "sqlite":
        op.execute("DROP TRIGGER IF EXISTS trg_live_account_safety_events_no_update")
        op.execute("DROP TRIGGER IF EXISTS trg_live_account_safety_events_no_delete")

    with op.batch_alter_table("live_account_safety_events") as batch:
        batch.drop_constraint("uq_live_account_safety_event_state_version", type_="unique")
        batch.drop_column("request_fingerprint")
