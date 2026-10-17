import uuid

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class PlatformSetting(BaseModel):
    """Admin-configured, platform-wide integration credentials — one shared
    WhatsApp Business token, Telegram bot token, AI provider key, News API
    key, etc. for the whole app (as opposed to broker_connections, which is
    per-user). Only a user with is_admin=True can read or write these, and
    only through the API — never over-the-wire in plaintext, always
    encrypted at rest with the same scheme as broker credentials.

    Known keys used elsewhere in the app (add more as later phases need
    them): "whatsapp_api_token", "telegram_bot_token", "ai_provider_api_key",
    "news_api_key".
    """

    __tablename__ = "platform_settings"

    key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    value_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by_user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"), nullable=True)
