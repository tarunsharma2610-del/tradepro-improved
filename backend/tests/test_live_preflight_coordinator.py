from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.brokers.base import BrokerCallResult
from app.core.config import settings
from app.models.broker_connection import BrokerConnection
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.instrument_service import InstrumentService
from app.services.live_execution_service import LiveExecutionBlocked, LiveOrderIntent
from app.services.live_preflight_coordinator import LivePreflightCoordinator


NOW = datetime(2026, 10, 19, 5, 0, tzinfo=timezone.utc)


class ReadOnlyUpstoxAdapter:
    def __init__(self, *, fail=None, quote_timestamp="2026-10-19T10:30:00+05:30"):
        self.fail = fail
        self.quote_timestamp = quote_timestamp
        self.calls = []

    def _result(self, endpoint, data):
        self.calls.append(endpoint)
        if self.fail == endpoint:
            return BrokerCallResult(ok=False, error="mock endpoint failure")
        return BrokerCallResult(ok=True, data={"status": "success", "data": data})

    async def get_market_holidays(self, access_token):
        return self._result("holidays", [])

    async def get_market_timings(self, access_token, market_date):
        return self._result("timings", [
            {"exchange": "NSE", "start_time": 1792381500000, "end_time": 1792404000000}
        ])

    async def get_positions(self, access_token):
        return self._result("positions", [])

    async def get_full_market_quote(self, access_token, instrument_keys):
        key = instrument_keys[0]
        return self._result("quote", {
            key.replace("|", ":"): {
                "instrument_token": key,
                "last_price": 100,
                "timestamp": self.quote_timestamp,
            }
        })

    async def get_funds_and_margin(self, access_token):
        return self._result("funds", {
            "available_to_trade": {
                "total": 100000,
                "cash_available_to_trade": {
                    "total": 100000,
                    "margin_used": {"loss": {"realised": 0, "unrealised": 0}},
                },
                "pledge_available_to_trade": {"total": 0},
            },
            "unavailable_to_trade": {
                "cash_unavailable_to_trade": {
                    "unsettled_profit": {"todays_profit": 0, "previous_days": 0}
                }
            },
        })

    async def get_margin_details(self, access_token, instruments):
        return self._result("margin", {
            "required_margin": 200,
            "final_margin": 200,
            "margins": [{
                "span_margin": 0, "exposure_margin": 0, "equity_margin": 200,
                "net_buy_premium": 0, "additional_margin": 0, "total_margin": 200,
                "tender_margin": 0,
            }],
        })


@pytest.fixture()
def context(db_session, make_user, monkeypatch):
    user = make_user()
    portfolio = PortfolioRepository(db_session).create(
        user_id=user.id, name="Preflight coordinator", virtual_capital=Decimal("100000")
    )
    InstrumentService(db_session).seed_defaults()
    instrument = InstrumentRepository(db_session).search("RELIANCE")[0]
    db_session.add(BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="encrypted-key",
        api_secret_encrypted="encrypted-secret",
        redirect_uri="https://example.invalid/callback",
        access_token_encrypted="encrypted-token",
        access_token_expires_at=datetime(2026, 10, 19, 18, 0, tzinfo=timezone.utc),
        is_connected=True,
    ))
    db_session.commit()
    monkeypatch.setattr(settings, "TRADING_MODE", "LIVE")
    monkeypatch.setattr(settings, "LIVE_ORDER_SUBMISSION_ENABLED", True)
    monkeypatch.setattr(settings, "AUTOMATED_ENTRIES_ENABLED", False)
    monkeypatch.setattr(BrokerCredentialsService, "get_access_token", lambda *_: "test-token")
    return db_session, user, portfolio, instrument


def _intent(portfolio, instrument):
    return LiveOrderIntent(
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        side="BUY",
        order_type="MARKET",
        segment="EQUITY_DELIVERY",
        quantity=2,
    )


@pytest.mark.asyncio
async def test_coordinator_composes_read_only_snapshots_into_preflight(context):
    db, user, portfolio, instrument = context
    adapter = ReadOnlyUpstoxAdapter()
    coordinator = LivePreflightCoordinator(db, adapter=adapter, clock=lambda: NOW)

    plan = await coordinator.preflight(
        user.id, _intent(portfolio, instrument), user_confirmed=True
    )

    assert plan.user_id == user.id
    assert plan.portfolio_id == portfolio.id
    assert plan.instrument_key == instrument.instrument_key
    assert plan.broker_name == "upstox"
    assert {"holidays", "timings", "positions", "quote", "funds", "margin"}.issubset(adapter.calls)
    assert not any("place_order" in endpoint for endpoint in adapter.calls)


@pytest.mark.asyncio
async def test_coordinator_fails_closed_if_read_only_provider_fails(context):
    db, user, portfolio, instrument = context
    adapter = ReadOnlyUpstoxAdapter(fail="funds")
    coordinator = LivePreflightCoordinator(db, adapter=adapter, clock=lambda: NOW)

    with pytest.raises(LiveExecutionBlocked, match="snapshots could not be validated"):
        await coordinator.preflight(
            user.id, _intent(portfolio, instrument), user_confirmed=True
        )

    assert not any("place_order" in endpoint for endpoint in adapter.calls)


@pytest.mark.asyncio
async def test_coordinator_rejects_stale_exchange_quote(context):
    db, user, portfolio, instrument = context
    adapter = ReadOnlyUpstoxAdapter(quote_timestamp="2026-10-19T09:00:00+05:30")
    coordinator = LivePreflightCoordinator(db, adapter=adapter, clock=lambda: NOW)

    with pytest.raises(LiveExecutionBlocked, match="risk gate rejected"):
        await coordinator.preflight(
            user.id, _intent(portfolio, instrument), user_confirmed=True
        )


@pytest.mark.asyncio
async def test_coordinator_live_interlock_stops_before_broker_calls(context, monkeypatch):
    db, user, portfolio, instrument = context
    monkeypatch.setattr(settings, "LIVE_ORDER_SUBMISSION_ENABLED", False)
    adapter = ReadOnlyUpstoxAdapter()
    coordinator = LivePreflightCoordinator(db, adapter=adapter, clock=lambda: NOW)

    with pytest.raises(LiveExecutionBlocked, match="remains disabled"):
        await coordinator.preflight(
            user.id, _intent(portfolio, instrument), user_confirmed=True
        )

    assert adapter.calls == []
