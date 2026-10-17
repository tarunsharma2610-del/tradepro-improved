from unittest.mock import AsyncMock, patch

import pytest

from app.repositories.telegram_link_repository import TelegramLinkRepository
from app.services.platform_settings_service import PlatformSettingsService
from app.services.telegram_notifier import TelegramResult
from app.services.telegram_service import TelegramService, TelegramServiceError


def _set_bot_token(db, admin_user, token="fake-bot-token"):
    PlatformSettingsService(db).set_setting(key="telegram_bot_token", value=token, description=None, admin_user_id=admin_user.id)


@pytest.mark.asyncio
async def test_start_link_fails_clearly_without_a_configured_bot_token(db_session, make_user):
    user = make_user()
    service = TelegramService(db_session)

    with pytest.raises(TelegramServiceError, match="No Telegram bot token"):
        await service.start_link(user.id)


@pytest.mark.asyncio
async def test_start_link_returns_a_real_deep_link_and_stores_the_code(db_session, make_user):
    user = make_user()
    admin = make_user(email="admin@example.com", is_admin=True)
    _set_bot_token(db_session, admin)
    service = TelegramService(db_session)

    with patch("app.services.telegram_service.telegram_notifier.get_me", new=AsyncMock(return_value=TelegramResult(ok=True, data={"username": "my_bot"}))):
        link_url = await service.start_link(user.id)

    assert link_url.startswith("https://t.me/my_bot?start=")

    link = TelegramLinkRepository(db_session).get_for_user(user.id)
    assert link.link_code is not None
    assert link.telegram_chat_id is None


@pytest.mark.asyncio
async def test_process_updates_completes_a_pending_link_on_matching_start_command(db_session, make_user):
    user = make_user()
    admin = make_user(email="admin2@example.com", is_admin=True)
    _set_bot_token(db_session, admin)
    service = TelegramService(db_session)

    with patch("app.services.telegram_service.telegram_notifier.get_me", new=AsyncMock(return_value=TelegramResult(ok=True, data={"username": "bot"}))):
        link_url = await service.start_link(user.id)
    code = link_url.split("start=")[1]

    fake_updates = TelegramResult(
        ok=True,
        data=[{"update_id": 1001, "message": {"chat": {"id": 999888}, "text": f"/start {code}"}}],
    )
    with (
        patch("app.services.telegram_service.telegram_notifier.get_updates", new=AsyncMock(return_value=fake_updates)),
        patch("app.services.telegram_service.telegram_notifier.send_message", new=AsyncMock(return_value=TelegramResult(ok=True))),
    ):
        completed = await service.process_updates()

    assert completed == 1
    link = TelegramLinkRepository(db_session).get_for_user(user.id)
    assert link.telegram_chat_id == 999888
    assert link.linked_at is not None
    assert link.link_code is None  # single-use, cleared


@pytest.mark.asyncio
async def test_process_updates_ignores_unrelated_messages(db_session, make_user):
    user = make_user()
    admin = make_user(email="admin3@example.com", is_admin=True)
    _set_bot_token(db_session, admin)
    service = TelegramService(db_session)

    with patch("app.services.telegram_service.telegram_notifier.get_me", new=AsyncMock(return_value=TelegramResult(ok=True, data={"username": "bot"}))):
        await service.start_link(user.id)

    fake_updates = TelegramResult(
        ok=True,
        data=[{"update_id": 5, "message": {"chat": {"id": 111}, "text": "hello there"}}],
    )
    with patch("app.services.telegram_service.telegram_notifier.get_updates", new=AsyncMock(return_value=fake_updates)):
        completed = await service.process_updates()

    assert completed == 0
    link = TelegramLinkRepository(db_session).get_for_user(user.id)
    assert link.telegram_chat_id is None  # unchanged — code never matched


@pytest.mark.asyncio
async def test_process_updates_advances_offset_even_with_no_matches(db_session, make_user):
    admin = make_user(email="admin4@example.com", is_admin=True)
    _set_bot_token(db_session, admin)
    service = TelegramService(db_session)

    fake_updates = TelegramResult(ok=True, data=[{"update_id": 77, "message": {"chat": {"id": 1}, "text": "hi"}}])
    with patch("app.services.telegram_service.telegram_notifier.get_updates", new=AsyncMock(return_value=fake_updates)):
        await service.process_updates()

    state = TelegramLinkRepository(db_session).get_bot_state()
    assert state.last_update_id == 77


def test_unlink_removes_the_link_row(db_session, make_user):
    user = make_user()
    service = TelegramService(db_session)
    TelegramLinkRepository(db_session).upsert_code(user.id, "some-code")

    service.unlink(user.id)

    assert TelegramLinkRepository(db_session).get_for_user(user.id) is None