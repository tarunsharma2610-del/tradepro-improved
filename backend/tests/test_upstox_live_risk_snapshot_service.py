from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from app.brokers.base import BrokerCallResult
from app.brokers.upstox.risk_snapshot_parsing import (
    parse_full_market_quote,
    parse_market_holidays,
    parse_market_timings,
    parse_open_positions,
)
from app.models.instrument import Instrument
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.instrument_service import InstrumentService
from app.services.live_execution_service import LiveOrderIntent
from app.services.upstox_live_risk_snapshot_service import UpstoxLiveRiskSnapshotService


NOW = datetime(2026, 10, 19, 5, 0, tzinfo=timezone.utc)


class FakeUpstoxAdapter:
    def __init__(self, *, positions=None, holidays=None, timings=None, quote_overrides=None, fail=None):
        self.positions = positions if positions is not None else []
        self.holidays = holidays if holidays is not None else []
        self.timings = timings if timings is not None else [
            {"exchange": "NSE", "start_time": 1792381500000, "end_time": 1792404000000}
        ]
        self.quote_overrides = quote_overrides or {}
        self.fail = fail
        self.calls = []

    def _result(self, name, data):
        self.calls.append(name)
        if self.fail == name:
            return BrokerCallResult(ok=False, error="simulated provider failure")
        return BrokerCallResult(ok=True, data={"status": "success", "data": data})

    async def get_market_holidays(self, access_token):
        return self._result("holidays", self.holidays)

    async def get_market_timings(self, access_token, market_date):
        return self._result("timings", self.timings)

    async def get_positions(self, access_token):
        return self._result("positions", self.positions)

    async def get_full_market_quote(self, access_token, instrument_keys):
        key = instrument_keys[0]
        row = self.quote_overrides.get(key, {
            "instrument_token": key,
            "last_price": 100,
            "timestamp": "2026-10-19T10:30:00+05:30",
        })
        return self._result("quote:" + key, {key.replace("|", ":"): row})

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
                "span_margin": 0,
                "exposure_margin": 0,
                "equity_margin": 200,
                "net_buy_premium": 0,
                "additional_margin": 0,
                "total_margin": 200,
                "tender_margin": 0,
            }],
        })


@pytest.fixture()
def snapshot_context(db_session, make_user):
    user = make_user()
    portfolio = PortfolioRepository(db_session).create(
        user_id=user.id, name="Risk snapshots", virtual_capital=Decimal("100000")
    )
    InstrumentService(db_session).seed_defaults()
    instrument = InstrumentRepository(db_session).search("RELIANCE")[0]
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


def test_full_quote_parser_requires_matching_key_and_exchange_timestamp():
    payload = {"status": "success", "data": {
        "NSE_EQ:RELIANCE": {
            "instrument_token": "NSE_EQ|INE002A01018",
            "last_price": 123.45,
            "timestamp": "2026-10-19T10:30:00+05:30",
        }
    }}
    parsed = parse_full_market_quote(payload, "NSE_EQ|INE002A01018")
    assert parsed.last_price == Decimal("123.45")
    assert parsed.observed_at == NOW

    with pytest.raises(ValueError, match="exactly one matching"):
        parse_full_market_quote(payload, "NSE_EQ|NOT-THIS-INSTRUMENT")


def test_full_quote_parser_rejects_missing_or_naive_timestamp():
    payload = {"status": "success", "data": {
        "quote": {"instrument_token": "NSE_EQ|A", "last_price": 100, "timestamp": "2026-10-19T10:30:00"}
    }}
    with pytest.raises(ValueError, match="timezone offset"):
        parse_full_market_quote(payload, "NSE_EQ|A")


def test_positions_parser_preserves_signed_quantity_and_skips_flat_rows():
    parsed = parse_open_positions({"status": "success", "data": [
        {"instrument_token": "NSE_EQ|A", "quantity": 5},
        {"instrument_token": "NSE_EQ|B", "quantity": -2},
        {"instrument_token": "NSE_EQ|C", "quantity": 0},
    ]})
    assert [(row.instrument_key, row.quantity) for row in parsed] == [
        ("NSE_EQ|A", 5), ("NSE_EQ|B", -2)
    ]


def test_positions_parser_rejects_duplicate_instrument_rows():
    with pytest.raises(ValueError, match="Duplicate broker position"):
        parse_open_positions({"status": "success", "data": [
            {"instrument_token": "NSE_EQ|A", "quantity": 1},
            {"instrument_token": "NSE_EQ|A", "quantity": 2},
        ]})


def test_market_calendar_parsers_support_holidays_and_special_sessions():
    holiday_rows = parse_market_holidays({"status": "success", "data": [
        {"date": "2026-10-19", "holiday_type": "SPECIAL_TIMING", "closed_exchanges": [],
         "open_exchanges": [{"exchange": "NSE", "start_time": 1792381500000, "end_time": 1792404000000}]}
    ]})
    assert holiday_rows[0].market_date == date(2026, 10, 19)
    assert holiday_rows[0].open_exchanges[0][0] == "NSE"

    timings = parse_market_timings({"status": "success", "data": [
        {"exchange": "NSE", "start_time": 1792381500000, "end_time": 1792404000000}
    ]}, date(2026, 10, 19))
    assert timings.opens_at < timings.closes_at


@pytest.mark.asyncio
async def test_collector_returns_only_validated_read_only_snapshots(snapshot_context):
    db, user, portfolio, instrument = snapshot_context
    adapter = FakeUpstoxAdapter(positions=[
        {"instrument_token": "NSE_EQ|OTHER", "quantity": 3}
    ])
    collector = UpstoxLiveRiskSnapshotService(db, adapter, "test-token")

    snapshots = await collector.collect(user.id, instrument, _intent(portfolio, instrument), now=NOW)

    assert snapshots.quote_snapshots[instrument.instrument_key].price == Decimal("100")
    assert [(p.instrument_key, p.quantity, p.market_price) for p in snapshots.positions] == [
        ("NSE_EQ|OTHER", 3, Decimal("100"))
    ]
    assert snapshots.funds.cash_available == Decimal("100000")
    assert snapshots.margin.required_margin == Decimal("200")
    assert snapshots.session.is_open is True
    assert "positions" in adapter.calls and "funds" in adapter.calls and "margin" in adapter.calls
    assert not any("place_order" in name for name in adapter.calls)


@pytest.mark.asyncio
async def test_collector_fails_closed_when_any_required_read_only_endpoint_fails(snapshot_context):
    db, user, portfolio, instrument = snapshot_context
    adapter = FakeUpstoxAdapter(fail="funds")
    collector = UpstoxLiveRiskSnapshotService(db, adapter, "test-token")

    with pytest.raises(ValueError, match="funds and margin lookup failed"):
        await collector.collect(user.id, instrument, _intent(portfolio, instrument), now=NOW)


@pytest.mark.asyncio
async def test_collector_honors_official_trading_holiday(snapshot_context):
    db, user, portfolio, instrument = snapshot_context
    adapter = FakeUpstoxAdapter(holidays=[
        {"date": "2026-10-19", "holiday_type": "TRADING_HOLIDAY",
         "closed_exchanges": ["NSE"], "open_exchanges": []}
    ])
    collector = UpstoxLiveRiskSnapshotService(db, adapter, "test-token")

    snapshots = await collector.collect(user.id, instrument, _intent(portfolio, instrument), now=NOW)

    assert snapshots.session.is_open is False
    assert "trading holiday" in snapshots.session.reason.lower()
    assert "timings" not in adapter.calls
