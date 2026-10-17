from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class NewsFeedSource(BaseModel):
    """Admin-managed, like platform_settings — one shared list of RSS
    sources for the whole platform, not per-user. Seeded with one
    independently-verified working feed (Business Standard); admins can
    add more through the API without a redeploy."""

    __tablename__ = "news_feed_sources"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    rss_url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
