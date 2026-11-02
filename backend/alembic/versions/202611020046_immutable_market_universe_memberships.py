"""enforce immutable market universe membership snapshots

Revision ID: 202611020046
Revises: 202611020045
"""
from alembic import op

revision = "202611020046"
down_revision = "202611020045"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        op.execute("""
            CREATE FUNCTION reject_market_universe_membership_mutation()
            RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'market universe membership snapshots are immutable';
            END;
            $$ LANGUAGE plpgsql
        """)
        op.execute("""
            CREATE TRIGGER trg_market_universe_membership_immutable
            BEFORE UPDATE OR DELETE ON market_universe_memberships
            FOR EACH ROW EXECUTE FUNCTION reject_market_universe_membership_mutation()
        """)
        op.execute("""
            CREATE FUNCTION reject_market_universe_snapshot_content_mutation()
            RETURNS trigger AS $$
            BEGIN
                IF OLD.universe_key IS DISTINCT FROM NEW.universe_key
                   OR OLD.as_of_date IS DISTINCT FROM NEW.as_of_date
                   OR OLD.source IS DISTINCT FROM NEW.source
                   OR OLD.member_count IS DISTINCT FROM NEW.member_count THEN
                    RAISE EXCEPTION 'market universe snapshot content is immutable';
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql
        """)
        op.execute("""
            CREATE TRIGGER trg_market_universe_snapshot_content_immutable
            BEFORE UPDATE ON market_universe_snapshots
            FOR EACH ROW EXECUTE FUNCTION reject_market_universe_snapshot_content_mutation()
        """)
        op.execute("""
            CREATE FUNCTION reject_market_universe_snapshot_delete()
            RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'market universe snapshots are retained for audit';
            END;
            $$ LANGUAGE plpgsql
        """)
        op.execute("""
            CREATE TRIGGER trg_market_universe_snapshot_no_delete
            BEFORE DELETE ON market_universe_snapshots
            FOR EACH ROW EXECUTE FUNCTION reject_market_universe_snapshot_delete()
        """)
    elif dialect == "sqlite":
        op.execute("""
            CREATE TRIGGER trg_market_universe_membership_no_update
            BEFORE UPDATE ON market_universe_memberships
            BEGIN
                SELECT RAISE(ABORT, 'market universe membership snapshots are immutable');
            END
        """)
        op.execute("""
            CREATE TRIGGER trg_market_universe_membership_no_delete
            BEFORE DELETE ON market_universe_memberships
            BEGIN
                SELECT RAISE(ABORT, 'market universe membership snapshots are immutable');
            END
        """)
        op.execute("""
            CREATE TRIGGER trg_market_universe_snapshot_content_no_update
            BEFORE UPDATE OF universe_key, as_of_date, source, member_count ON market_universe_snapshots
            BEGIN
                SELECT RAISE(ABORT, 'market universe snapshot content is immutable');
            END
        """)
        op.execute("""
            CREATE TRIGGER trg_market_universe_snapshot_no_delete
            BEFORE DELETE ON market_universe_snapshots
            BEGIN
                SELECT RAISE(ABORT, 'market universe snapshots are retained for audit');
            END
        """)
    else:
        raise RuntimeError(f"Unsupported database dialect for market universe immutability: {dialect}")


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS trg_market_universe_snapshot_no_delete ON market_universe_snapshots")
        op.execute("DROP FUNCTION IF EXISTS reject_market_universe_snapshot_delete()")
        op.execute("DROP TRIGGER IF EXISTS trg_market_universe_snapshot_content_immutable ON market_universe_snapshots")
        op.execute("DROP FUNCTION IF EXISTS reject_market_universe_snapshot_content_mutation()")
        op.execute("DROP TRIGGER IF EXISTS trg_market_universe_membership_immutable ON market_universe_memberships")
        op.execute("DROP FUNCTION IF EXISTS reject_market_universe_membership_mutation()")
    elif dialect == "sqlite":
        op.execute("DROP TRIGGER IF EXISTS trg_market_universe_snapshot_no_delete")
        op.execute("DROP TRIGGER IF EXISTS trg_market_universe_snapshot_content_no_update")
        op.execute("DROP TRIGGER IF EXISTS trg_market_universe_membership_no_delete")
        op.execute("DROP TRIGGER IF EXISTS trg_market_universe_membership_no_update")
