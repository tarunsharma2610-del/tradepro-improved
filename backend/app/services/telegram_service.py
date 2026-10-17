import secrets
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.telegram_link_repository import TelegramLinkRepository
from app.services import telegram_notifier
from app.services.platform_settings_service import PlatformSettingsService


class TelegramServiceError(Exception):
    pass


class TelegramService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = TelegramLinkRepository(db)
        self.platform_settings = PlatformSettingsService(db)

    async def start_link(self, user_id: UUID) -> str:
        """Returns a t.me deep link. Opening it and hitting Start in
        Telegram sends /start <code> to the bot, which process_updates()
        (called periodically by the worker) picks up to complete the
        link — see module docstring in models/telegram_link.py."""
        bot_token = self.platform_settings.get_decrypted("telegram_bot_token")
        if not bot_token:
            raise TelegramServiceError("No Telegram bot token configured — an admin needs to set one in platform settings.")

        me_result = await telegram_notifier.get_me(bot_token)
        if not me_result.ok:
            raise TelegramServiceError(f"Could not verify the bot token with Telegram: {me_result.error}")
        username = me_result.data.get("username")
        if not username:
            raise TelegramServiceError("Telegram didn't return a bot username for this token.")

        code = secrets.token_urlsafe(12)
        self.repo.upsert_code(user_id, code)
        return f"https://t.me/{username}?start={code}"

    def unlink(self, user_id: UUID) -> None:
        link = self.repo.get_for_user(user_id)
        if link:
            self.repo.delete(link)

    async def process_updates(self) -> int:
        """Called periodically by the worker. Looks for '/start <code>'
        messages and completes any matching pending link. Returns how
        many links were completed this pass."""
        bot_token = self.platform_settings.get_decrypted("telegram_bot_token")
        if not bot_token:
            return 0

        state = self.repo.get_bot_state()
        result = await telegram_notifier.get_updates(bot_token, offset=state.last_update_id + 1)
        if not result.ok:
            return 0

        completed = 0
        max_update_id = state.last_update_id
        for update in result.data:
            max_update_id = max(max_update_id, update.get("update_id", max_update_id))
            message = update.get("message", {})
            text = message.get("text", "")
            chat_id = message.get("chat", {}).get("id")
            if not text.startswith("/start ") or chat_id is None:
                continue

            code = text.removeprefix("/start ").strip()
            link = self.repo.get_by_code(code)
            if link is None:
                continue

            link.telegram_chat_id = chat_id
            link.linked_at = datetime.now(timezone.utc)
            link.link_code = None  # single-use
            self.repo.save(link)
            completed += 1
            await telegram_notifier.send_message(bot_token, chat_id, "Linked! You'll get trade notifications here.")

        state.last_update_id = max_update_id
        self.repo.save_bot_state(state)
        return completed
