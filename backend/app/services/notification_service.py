"""
Called from strategy_execution_service.py after a fill — deliberately
fire-and-forget from the caller's perspective: a notification failing (no
channel configured, Telegram/WhatsApp API error) must never fail or roll
back the trade itself. Notifications are a side effect of trading, not a
precondition for it.
"""

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.telegram_link_repository import TelegramLinkRepository
from app.services import telegram_notifier, whatsapp_notifier
from app.services.platform_settings_service import PlatformSettingsService

logger = logging.getLogger("trading_platform.notifications")


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        self.platform_settings = PlatformSettingsService(db)
        self.telegram_links = TelegramLinkRepository(db)

    async def notify_user(self, user_id: UUID, message: str) -> None:
        await self._try_telegram(user_id, message)
        await self._try_whatsapp(user_id, message)

    async def _try_telegram(self, user_id: UUID, message: str) -> None:
        link = self.telegram_links.get_for_user(user_id)
        if not link or not link.telegram_chat_id:
            return
        bot_token = self.platform_settings.get_decrypted("telegram_bot_token")
        if not bot_token:
            return
        result = await telegram_notifier.send_message(bot_token, link.telegram_chat_id, message)
        if not result.ok:
            logger.warning("Telegram notification failed for user=%s: %s", user_id, result.error)

    async def _try_whatsapp(self, user_id: UUID, message: str) -> None:
        user = self.db.get(User, user_id)
        if not user or not user.whatsapp_number:
            return
        token = self.platform_settings.get_decrypted("whatsapp_api_token")
        phone_number_id = self.platform_settings.get_decrypted("whatsapp_phone_number_id")
        if not token or not phone_number_id:
            return
        result = await whatsapp_notifier.send_message(token, phone_number_id, user.whatsapp_number, message)
        if not result.ok:
            logger.warning("WhatsApp notification failed for user=%s: %s", user_id, result.error)
