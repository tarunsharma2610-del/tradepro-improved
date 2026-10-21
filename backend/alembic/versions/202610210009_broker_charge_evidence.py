"""Add metadata ledger for broker charge source documents.

Revision ID: 202610210009
Revises: 202610180008
Create Date: 2026-10-21
"""
from alembic import op
import sqlalchemy as sa


revision = "202610210009"
down_revision = "202610180008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "broker_charge_evidence",
        sa.Column("broker_connection_id", sa.Uuid(), nullable=False),
        sa.Column("source_kind", sa.String(length=30), server_default="CONTRACT_NOTE", nullable=False),
        sa.Column("broker_report_reference", sa.String(length=200), nullable=True),
        sa.Column("report_date", sa.Date(), nullable=True),
        sa.Column("segment", sa.String(length=50), nullable=True),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("source_sha256", sa.String(length=64), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("parser_version", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="RECEIVED", nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Uuid(), nullable=True),
        sa.Column("review_note", sa.String(length=500), nullable=True),
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("byte_size > 0", name="ck_charge_evidence_byte_size_positive"),
        sa.CheckConstraint("length(source_sha256) = 64", name="ck_charge_evidence_sha256_length"),
        sa.CheckConstraint("status IN ('RECEIVED', 'REVIEWED', 'REJECTED')", name="ck_charge_evidence_status"),
        sa.ForeignKeyConstraint(["broker_connection_id"], ["broker_connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint(
            "broker_connection_id", "source_sha256",
            name="uq_charge_evidence_connection_sha256",
        ),
    )
    op.create_index(
        "ix_broker_charge_evidence_broker_connection_id",
        "broker_charge_evidence", ["broker_connection_id"], unique=False,
    )
    op.create_index(
        "ix_broker_charge_evidence_report_date",
        "broker_charge_evidence", ["report_date"], unique=False,
    )
    op.create_index(
        "ix_broker_charge_evidence_status",
        "broker_charge_evidence", ["status"], unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_broker_charge_evidence_status", table_name="broker_charge_evidence")
    op.drop_index("ix_broker_charge_evidence_report_date", table_name="broker_charge_evidence")
    op.drop_index("ix_broker_charge_evidence_broker_connection_id", table_name="broker_charge_evidence")
    op.drop_table("broker_charge_evidence")
