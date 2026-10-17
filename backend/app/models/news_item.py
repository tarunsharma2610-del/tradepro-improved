import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import BaseModel

news_item_instruments = Table(
    "news_item_instruments",
    Base.metadata,
    Column("news_item_id", Uuid, ForeignKey("news_items.id", ondelete="CASCADE"), primary_key=True),
    Column("instrument_id", Uuid, ForeignKey("instruments.id", ondelete="CASCADE"), primary_key=True),
)


class NewsItem(BaseModel):
    """Deduplicated by `link` (a news source rarely reuses a URL). Tagged
    with whichever instruments' trading_symbol or name appear in the
    title/summary — simple keyword matching, not NLP/NER, and deliberately
    so: see services/news_service.py for why that's an honest tradeoff
    here rather than a corner cut."""

    __tablename__ = "news_items"

    source_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("news_feed_sources.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    link: Mapped[str] = mapped_column(String(1000), unique=True, index=True, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    instruments: Mapped[list["Instrument"]] = relationship(secondary=news_item_instruments, lazy="joined")
