"""Add separately encrypted Upstox Analytics Token.

Revision ID: 202610300031
Revises: 202610270030
Create Date: 2026-10-30
"""
from alembic import op
import sqlalchemy as sa

revision = "202610300031"
down_revision = "202610270030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("broker_connections", sa.Column("analytics_token_encrypted", sa.Text(), nullable=True))
    op.add_column("broker_connections", sa.Column("analytics_token_expires_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("broker_connections", "analytics_token_expires_at")
    op.drop_column("broker_connections", "analytics_token_encrypted")
