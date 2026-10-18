"""Add explicit safety permission grants to users.

Revision ID: 202610180012
Revises: 202610180011
Create Date: 2026-10-18
"""
from alembic import op
import sqlalchemy as sa


revision = "202610180012"
down_revision = "202610180011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "safety_permissions",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )
    # Remove the server default after existing rows are backfilled; new grants
    # must be assigned explicitly by trusted administrative tooling.
    op.alter_column("users", "safety_permissions", server_default=None)


def downgrade() -> None:
    op.drop_column("users", "safety_permissions")
