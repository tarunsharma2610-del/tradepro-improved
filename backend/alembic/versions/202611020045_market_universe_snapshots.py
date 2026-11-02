"""add auditable market universe snapshots

Revision ID: 202611020045
Revises: 202611020044
Create Date: 2026-11-02
"""
from alembic import op
import sqlalchemy as sa

revision = "202611020045"
down_revision = "202611020044"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_universe_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("universe_key", sa.String(length=50), nullable=False),
        sa.Column("as_of_date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("member_count", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("universe_key", "as_of_date", name="uq_market_universe_snapshot_date"),
    )
    op.create_index("ix_market_universe_active", "market_universe_snapshots", ["universe_key", "is_active"])\n    op.create_index(\n        "uq_market_universe_one_active", "market_universe_snapshots", ["universe_key"],\n        unique=True, postgresql_where=sa.text("is_active = true"),\n        sqlite_where=sa.text("is_active = 1"),\n    )
    op.create_table(
        "market_universe_memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("snapshot_id", sa.Uuid(), nullable=False),
        sa.Column("instrument_id", sa.Uuid(), nullable=False),
        sa.Column("trading_symbol", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["snapshot_id"], ["market_universe_snapshots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["instrument_id"], ["instruments.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("snapshot_id", "instrument_id", name="uq_market_universe_member_instrument"),
        sa.UniqueConstraint("snapshot_id", "trading_symbol", name="uq_market_universe_member_symbol"),
    )
    op.create_index("ix_market_universe_membership_snapshot", "market_universe_memberships", ["snapshot_id"])


def downgrade() -> None:
    op.drop_index("ix_market_universe_membership_snapshot", table_name="market_universe_memberships")
    op.drop_table("market_universe_memberships")
    op.drop_index("uq_market_universe_one_active", table_name="market_universe_snapshots")\n    op.drop_index("ix_market_universe_active", table_name="market_universe_snapshots")
    op.drop_table("market_universe_snapshots")
