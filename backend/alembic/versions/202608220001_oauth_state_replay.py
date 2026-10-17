"""store one-time broker OAuth state nonce digests

Revision ID: 202608220001
Revises: 202608210001
Create Date: 2026-08-22
"""
from alembic import op
import sqlalchemy as sa

revision = "202608220001"
down_revision = "202608210001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("broker_connections", sa.Column("oauth_state_nonce_hash", sa.String(length=64), nullable=True))
    op.add_column("broker_connections", sa.Column("oauth_state_expires_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("broker_connections", "oauth_state_expires_at")
    op.drop_column("broker_connections", "oauth_state_nonce_hash")
