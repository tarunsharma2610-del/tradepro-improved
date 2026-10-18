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
    # Empty grants for all existing users: platform-admin status is not
    # implicitly upgraded to any safety permission.
    op.add_column(
        "users",
        sa.Column(
            "safety_permissions",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "safety_permissions")
