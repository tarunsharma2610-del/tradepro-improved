from decimal import Decimal
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.repositories.portfolio_repository import PortfolioRepository
from app.services.ai_assistant_service import AIAssistantService, AssistantError
from app.services.instrument_service import InstrumentService
from app.services.platform_settings_service import PlatformSettingsService


@pytest.fixture()
def portfolio(db_session, make_user):
    user = make_user()
    return PortfolioRepository(db_session).create(user_id=user.id, name="Main", virtual_capital=Decimal("100000"))


def _mock_anthropic_response(text: str, status: int = 200):
    mock_resp = type("R", (), {"status_code": status, "json": lambda self: {"content": [{"type": "text", "text": text}]}, "text": text})()
    return patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_resp))


@pytest.mark.asyncio
async def test_no_api_key_configured_raises_clear_error(db_session, portfolio):
    service = AIAssistantService(db_session)
    with pytest.raises(AssistantError, match="No AI provider key"):
        await service.ask(portfolio, "How is my portfolio doing?")


@pytest.mark.asyncio
async def test_successful_call_returns_the_answer_text(db_session, portfolio, make_user):
    admin = make_user(email="admin@example.com", is_admin=True)
    PlatformSettingsService(db_session).set_setting(
        key="ai_provider_api_key", value="sk-ant-test-key-123", description=None, admin_user_id=admin.id
    )
    service = AIAssistantService(db_session)

    with _mock_anthropic_response("Your portfolio has no open positions yet."):
        answer = await service.ask(portfolio, "How is my portfolio doing?")

    assert answer == "Your portfolio has no open positions yet."


@pytest.mark.asyncio
async def test_context_includes_real_position_and_order_data(db_session, portfolio, make_user):
    admin = make_user(email="admin2@example.com", is_admin=True)
    PlatformSettingsService(db_session).set_setting(
        key="ai_provider_api_key", value="sk-ant-test-key-123", description=None, admin_user_id=admin.id
    )
    InstrumentService(db_session).seed_defaults()
    from app.repositories.instrument_repository import InstrumentRepository
    from app.models.position import Position

    instrument = InstrumentRepository(db_session).search("INFY")[0]
    position = Position(portfolio_id=portfolio.id, instrument_id=instrument.id, quantity=10, avg_price=Decimal("1500"), realized_pnl=Decimal("0"))
    db_session.add(position)
    db_session.commit()

    service = AIAssistantService(db_session)
    captured_body = {}

    async def capture_post(self, url, headers=None, json=None):
        captured_body.update(json)
        return type("R", (), {"status_code": 200, "json": lambda s: {"content": [{"type": "text", "text": "ok"}]}})()

    with patch("httpx.AsyncClient.post", new=capture_post):
        await service.ask(portfolio, "What am I holding?")

    user_message = captured_body["messages"][0]["content"]
    assert "INFY" in user_message
    assert "10 shares" in user_message
    assert "1500" in user_message


@pytest.mark.asyncio
async def test_api_error_response_raises_assistant_error_with_status(db_session, portfolio, make_user):
    admin = make_user(email="admin3@example.com", is_admin=True)
    PlatformSettingsService(db_session).set_setting(
        key="ai_provider_api_key", value="bad-key", description=None, admin_user_id=admin.id
    )
    service = AIAssistantService(db_session)

    with _mock_anthropic_response("invalid x-api-key", status=401):
        with pytest.raises(AssistantError, match="401"):
            await service.ask(portfolio, "test")


@pytest.mark.asyncio
async def test_network_error_raises_assistant_error_not_an_unhandled_exception(db_session, portfolio, make_user):
    admin = make_user(email="admin4@example.com", is_admin=True)
    PlatformSettingsService(db_session).set_setting(
        key="ai_provider_api_key", value="sk-ant-test", description=None, admin_user_id=admin.id
    )
    service = AIAssistantService(db_session)

    with patch("httpx.AsyncClient.post", new=AsyncMock(side_effect=httpx.ConnectError("boom"))):
        with pytest.raises(AssistantError, match="Network error"):
            await service.ask(portfolio, "test")
