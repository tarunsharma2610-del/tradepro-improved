"""Persist explicit single-fill and order-fill-set tariff variance scopes.

Revision ID: 202610240018
Revises: 202610240017
"""
from alembic import op
import sqlalchemy as sa

revision = "202610240018"
down_revision = "202610240017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tariff_estimate_snapshot_records",
        sa.Column("comparison_scope", sa.String(length=20), server_default="TRADE_FILL", nullable=False),
    )
    op.add_column(
        "tariff_estimate_snapshot_records",
        sa.Column("source_fill_ids_json", sa.Text(), nullable=True),
    )
    op.add_column(
        "tariff_estimate_snapshot_records",
        sa.Column("source_fill_set_sha256", sa.String(length=64), nullable=True),
    )
    op.create_check_constraint(
        "ck_tariff_estimate_snapshot_comparison_scope",
        "tariff_estimate_snapshot_records",
        "comparison_scope IN ('TRADE_FILL', 'ORDER_FILL_SET')",
    )

    op.add_column(
        "tariff_estimate_variance_records",
        sa.Column("comparison_scope", sa.String(length=20), server_default="TRADE_FILL", nullable=False),
    )
    op.add_column(
        "tariff_estimate_variance_records",
        sa.Column("source_fill_set_sha256", sa.String(length=64), nullable=True),
    )
    # Backfill the newly recorded scope digest for existing single-fill variance rows.
    op.execute("""
        UPDATE tariff_estimate_variance_records
        SET source_fill_set_sha256 = (
            SELECT eligible_fill_set_sha256
            FROM broker_charge_source_components
            WHERE broker_charge_source_components.id = tariff_estimate_variance_records.source_component_id
        )
        WHERE source_fill_set_sha256 IS NULL
    """)
    op.create_check_constraint(
        "ck_tariff_estimate_variance_comparison_scope",
        "tariff_estimate_variance_records",
        "comparison_scope IN ('TRADE_FILL', 'ORDER_FILL_SET')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_tariff_estimate_variance_comparison_scope",
        "tariff_estimate_variance_records",
        type_="check",
    )
    op.drop_column("tariff_estimate_variance_records", "source_fill_set_sha256")
    op.drop_column("tariff_estimate_variance_records", "comparison_scope")
    op.drop_constraint(
        "ck_tariff_estimate_snapshot_comparison_scope",
        "tariff_estimate_snapshot_records",
        type_="check",
    )
    op.drop_column("tariff_estimate_snapshot_records", "source_fill_set_sha256")
    op.drop_column("tariff_estimate_snapshot_records", "source_fill_ids_json")
    op.drop_column("tariff_estimate_snapshot_records", "comparison_scope")
