import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class TelegramLink(BaseModel):
    """One row per user. `link_code` is a short-lived random token shown
    as part of a t.me deep link; when the user starts a chat with the bot
    and sends /start <code>, the worker's polling loop (see
    services/telegram_service.py) matches the code back to this row and
    fills in telegram_chat_id. Cleared after linking — it's single-use."""

    __tablename__ = "telegram_links"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True)
    link_code: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    linked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TelegramBotState(BaseModel):
    """Singleton row (always exactly one) tracking getUpdates polling
    offset — bot-level state, not per-user, so it doesn't belong on
    TelegramLink."""

    __tablename__ = "telegram_bot_state"

    last_update_id: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
