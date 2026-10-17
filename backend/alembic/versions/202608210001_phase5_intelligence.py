"""phase 5: news intelligence, telegram/whatsapp notifications, ai assistant support

Revision ID: 202608210001
Revises: 202608200001
Create Date: 2026-08-21

"""
from alembic import op
import sqlalchemy as sa

revision = "202608210001"
down_revision = "202608200001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("whatsapp_number", sa.String(20), nullable=True))

    op.create_table(
        "news_feed_sources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("rss_url", sa.String(500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(500), nullable=True),
    )
    op.create_index("ix_news_feed_sources_rss_url", "news_feed_sources", ["rss_url"], unique=True)

    op.create_table(
        "news_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("source_id", sa.Uuid(), sa.ForeignKey("news_feed_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("link", sa.String(1000), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_news_items_source_id", "news_items", ["source_id"])
    op.create_index("ix_news_items_link", "news_items", ["link"], unique=True)

    op.create_table(
        "news_item_instruments",
        sa.Column("news_item_id", sa.Uuid(), sa.ForeignKey("news_items.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("instrument_id", sa.Uuid(), sa.ForeignKey("instruments.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "telegram_links",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("link_code", sa.String(32), nullable=True),
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_telegram_links_user_id", "telegram_links", ["user_id"], unique=True)
    op.create_index("ix_telegram_links_link_code", "telegram_links", ["link_code"])

    op.create_table(
        "telegram_bot_state",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_update_id", sa.BigInteger(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("telegram_bot_state")
    op.drop_table("telegram_links")
    op.drop_table("news_item_instruments")
    op.drop_table("news_items")
    op.drop_table("news_feed_sources")
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("whatsapp_number")
