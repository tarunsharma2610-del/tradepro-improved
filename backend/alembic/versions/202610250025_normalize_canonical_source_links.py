"""Normalize canonical snapshot membership in original source component rows.

Revision ID: 202610250025
Revises: 202610250024
Create Date: 2026-10-25
"""
import json
from uuid import UUID, uuid4

from alembic import op
import sqlalchemy as sa

revision = "202610250025"
down_revision = "202610250024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "broker_charge_canonical_source_links",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("canonical_component_id", sa.Uuid(), nullable=False),
        sa.Column("source_component_id", sa.Uuid(), nullable=False),
        sa.Column("source_ordinal", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["canonical_component_id"], ["broker_charge_canonical_components.id"],
            name="fk_charge_canonical_source_link_snapshot", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_component_id"], ["broker_charge_source_components.id"],
            name="fk_charge_canonical_source_link_source", ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "canonical_component_id", "source_component_id",
            name="uq_charge_canonical_source_link_pair",
        ),
        sa.UniqueConstraint(
            "canonical_component_id", "source_ordinal",
            name="uq_charge_canonical_source_link_ordinal",
        ),
    )
    op.create_index(
        "ix_broker_charge_canonical_source_links_canonical_component_id",
        "broker_charge_canonical_source_links", ["canonical_component_id"], unique=False,
    )
    op.create_index(
        "ix_broker_charge_canonical_source_links_source_component_id",
        "broker_charge_canonical_source_links", ["source_component_id"], unique=False,
    )

    # Backfill only from each snapshot's persisted, ordered source-ID manifest.
    # Do not derive membership from component names or amounts during migration.
    bind = op.get_bind()
    snapshots = sa.Table(
        "broker_charge_canonical_components", sa.MetaData(),
        sa.Column("id", sa.Uuid()),
        sa.Column("source_component_ids_json", sa.Text()),
    )
    links = sa.Table(
        "broker_charge_canonical_source_links", sa.MetaData(),
        sa.Column("id", sa.Uuid()),
        sa.Column("canonical_component_id", sa.Uuid()),
        sa.Column("source_component_id", sa.Uuid()),
        sa.Column("source_ordinal", sa.Integer()),
    )
    for snapshot in bind.execute(sa.select(snapshots.c.id, snapshots.c.source_component_ids_json)):
        try:
            source_ids = json.loads(snapshot.source_component_ids_json)
            parsed = [UUID(value) for value in source_ids]
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"Cannot safely normalize source manifest for canonical snapshot {snapshot.id}"
            ) from exc
        if not parsed or len(parsed) != len(set(parsed)):
            raise RuntimeError(
                f"Canonical snapshot {snapshot.id} has an empty or duplicate source manifest"
            )
        for ordinal, source_id in enumerate(parsed):
            bind.execute(links.insert().values(
                id=uuid4(),
                canonical_component_id=snapshot.id,
                source_component_id=source_id,
                source_ordinal=ordinal,
            ))


def downgrade() -> None:
    op.drop_index(
        "ix_broker_charge_canonical_source_links_source_component_id",
        table_name="broker_charge_canonical_source_links",
    )
    op.drop_index(
        "ix_broker_charge_canonical_source_links_canonical_component_id",
        table_name="broker_charge_canonical_source_links",
    )
    op.drop_table("broker_charge_canonical_source_links")
