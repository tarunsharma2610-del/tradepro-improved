from unittest.mock import AsyncMock, patch

import pytest

from app.repositories.telegram_link_repository import TelegramLinkRepository
from app.services.notification_service import NotificationService
from app.services.platform_settings_service import PlatformSettingsService


@pytest.mark.asyncio
async def test_notify_user_is_a_silent_noop_with_no_channels_configured(db_session, make_user):
    user = make_user()
    service = NotificationService(db_session)

    with (
        patch("app.services.notification_service.telegram_notifier.send_message", new=AsyncMock()) as tg_send,
        patch("app.services.notification_service.whatsapp_notifier.send_message", new=AsyncMock()) as wa_send,
    ):
        await service.notify_user(user.id, "test message")

    tg_send.assert_not_called()
    wa_send.assert_not_called()


@pytest.mark.asyncio
async def test_notify_user_sends_telegram_when_linked_and_token_configured(db_session, make_user):
    user = make_user()
    admin = make_user(email="admin@example.com", is_admin=True)
    PlatformSettingsService(db_session).set_setting(key="telegram_bot_token", value="tok", description=None, admin_user_id=admin.id)

    link = TelegramLinkRepository(db_session).upsert_code(user.id, "code")
    link.telegram_chat_id = 555
    TelegramLinkRepository(db_session).save(link)

    service = NotificationService(db_session)
    from app.services.telegram_notifier import TelegramResult

    with patch("app.services.notification_service.telegram_notifier.send_message", new=AsyncMock(return_value=TelegramResult(ok=True))) as tg_send:
        await service.notify_user(user.id, "Trade filled")

    tg_send.assert_called_once_with("tok", 555, "Trade filled")


@pytest.mark.asyncio
async def test_notify_user_sends_whatsapp_when_number_and_credentials_configured(db_session, make_user):
    user = make_user()
    user.whatsapp_number = "+919876543210"
    db_session.add(user)
    db_session.commit()

    admin = make_user(email="admin2@example.com", is_admin=True)
    settings_service = PlatformSettingsService(db_session)
    settings_service.set_setting(key="whatsapp_api_token", value="wa-tok", description=None, admin_user_id=admin.id)
    settings_service.set_setting(key="whatsapp_phone_number_id", value="123456", description=None, admin_user_id=admin.id)

    service = NotificationService(db_session)
    from app.services.whatsapp_notifier import WhatsAppResult

    with patch("app.services.notification_service.whatsapp_notifier.send_message", new=AsyncMock(return_value=WhatsAppResult(ok=True))) as wa_send:
        await service.notify_user(user.id, "Trade filled")

    wa_send.assert_called_once_with("wa-tok", "123456", "+919876543210", "Trade filled")


@pytest.mark.asyncio
async def test_notify_user_does_not_send_whatsapp_without_the_phone_number_id_even_if_token_is_set(db_session, make_user):
    """Both credentials are required — a token alone isn't enough, per
    the WhatsApp Cloud API's actual requirements."""
    user = make_user()
    user.whatsapp_number = "+919876543210"
    db_session.add(user)
    db_session.commit()

    admin = make_user(email="admin3@example.com", is_admin=True)
    PlatformSettingsService(db_session).set_setting(key="whatsapp_api_token", value="wa-tok", description=None, admin_user_id=admin.id)
    # phone_number_id deliberately NOT set

    service = NotificationService(db_session)
    with patch("app.services.notification_service.whatsapp_notifier.send_message", new=AsyncMock()) as wa_send:
        await service.notify_user(user.id, "Trade filled")

    wa_send.assert_not_called()


@pytest.mark.asyncio
async def test_a_failed_channel_send_does_not_raise(db_session, make_user):
    """notify_user must never propagate an exception up into the trading
    flow — see the module docstring."""
    user = make_user()
    admin = make_user(email="admin4@example.com", is_admin=True)
    PlatformSettingsService(db_session).set_setting(key="telegram_bot_token", value="tok", description=None, admin_user_id=admin.id)
    link = TelegramLinkRepository(db_session).upsert_code(user.id, "code")
    link.telegram_chat_id = 555
    TelegramLinkRepository(db_session).save(link)

    service = NotificationService(db_session)
    from app.services.telegram_notifier import TelegramResult

    with patch("app.services.notification_service.telegram_notifier.send_message", new=AsyncMock(return_value=TelegramResult(ok=False, error="rate limited"))):
        await service.notify_user(user.id, "test")  # should not raise
