import gzip
import json
from datetime import date
from decimal import Decimal

import pytest

from app.repositories.instrument_repository import InstrumentRepository
from app.schemas.instrument import InstrumentOut
from app.services.instrument_service import InstrumentService


class FakeResponse:
    def __init__(self, status_code: int, content: bytes = b""):
        self.status_code = status_code
        self.content = content


class FakeAsyncClient:
    def __init__(self, response):
        self.response = response
        self.requested_url = None
        self.requested_kwargs = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def get(self, url, **kwargs):
        self.requested_url = url
        self.requested_kwargs = kwargs
        return self.response


def _record(segment, exchange, instrument_type, key, symbol, **extra):
    return {
        "segment": segment,
        "exchange": exchange,
        "instrument_type": instrument_type,
        "instrument_key": key,
        "trading_symbol": symbol,
        "name": extra.pop("name", symbol),
        "lot_size": extra.pop("lot_size", 1),
        "tick_size": extra.pop("tick_size", 0.05),
        **extra,
    }


@pytest.mark.asyncio
async def test_sync_from_upstox_imports_supported_exchanges_and_derivatives(db_session, monkeypatch):
    records = [
        _record("NSE_EQ", "NSE", "EQ", "NSE_EQ|INE002A01018", "RELIANCE"),
        _record("BSE_EQ", "BSE", "EQ", "BSE_EQ|INE002A01018", "RELIANCE"),
        _record("NSE_INDEX", "NSE", "INDEX", "NSE_INDEX|Nifty 50", "NIFTY"),
        _record("BSE_INDEX", "BSE", "INDEX", "BSE_INDEX|SENSEX", "SENSEX"),
        _record(
            "NSE_FO", "NSE", "FUT", "NSE_FO|FUT123", "NIFTY FUT",
            expiry=1798675200000, underlying_symbol="NIFTY",
        ),
        _record(
            "NSE_FO", "NSE", "CE", "NSE_FO|OPT123", "NIFTY 25000 CE",
            expiry=1798675200000, strike_price=25000,
            underlying_symbol="NIFTY",
        ),
        _record(
            "BSE_FO", "BSE", "PE", "BSE_FO|SENSEXOPT", "SENSEX 80000 PE",
            expiry=1798675200000, strike_price=80000,
            underlying_symbol="SENSEX",
        ),
        _record("NCD_FO", "NSE", "FUT", "NCD_FO|NCD123", "BOND FUT", expiry=1798675200000),
        _record("BCD_FO", "BSE", "FUT", "BCD_FO|BCD123", "BOND BSE FUT", expiry=1798675200000),
        _record("NSE_COM", "NSE", "FUT", "NSE_COM|COM123", "COM FUT", expiry=1798675200000),
        _record("MCX_FO", "MCX", "FUT", "MCX_FO|GOLD123", "GOLD FUT", expiry=1798675200000),
        # Unsupported instrument types and malformed segment/key combinations are skipped.
        _record("NSE_EQ", "NSE", "UNKNOWN", "NSE_EQ|UNKNOWN", "UNKNOWN"),
        _record("NSE_FO", "NSE", "FUT", "BSE_FO|WRONG", "WRONG"),
        _record("UNSUPPORTED", "NSE", "EQ", "UNSUPPORTED|ABC", "ABC"),
        _record("NSE_FO", "NSE", "FUT", "NSE_FO|BAD_EXPIRY", "BAD FUT", expiry=10**100),
        _record("NSE_FO", "NSE", "PE", "NSE_FO|NO_STRIKE", "BAD OPTION", expiry=1798675200000),
        _record("NSE_EQ", "BSE", "EQ", "NSE_EQ|WRONG_EXCHANGE", "WRONG"),
    ]
    response = FakeResponse(200, gzip.compress(json.dumps(records).encode("utf-8")))
    fake_client = FakeAsyncClient(response)
    monkeypatch.setattr(
        "app.services.instrument_service.httpx.AsyncClient",
        lambda **kwargs: fake_client,
    )

    ok, message = await InstrumentService(db_session).sync_from_upstox()

    assert ok is True
    assert message == "Synced 11 instruments across supported NSE, BSE and MCX segments."
    assert fake_client.requested_url == (
        "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz"
    )
    assert fake_client.requested_kwargs == {"follow_redirects": True}

    repo = InstrumentRepository(db_session)
    assert repo.count() == 11
    assert repo.get_by_key("NSE_EQ|INE002A01018").instrument_type == "EQUITY"
    assert repo.get_by_key("BSE_EQ|INE002A01018").exchange == "BSE"
    assert repo.get_by_key("NSE_INDEX|Nifty 50").instrument_type == "INDEX"
    assert repo.get_by_key("BSE_INDEX|SENSEX").instrument_type == "INDEX"

    future = repo.get_by_key("NSE_FO|FUT123")
    assert future.instrument_type == "FUTURES"
    assert future.expiry == date(2026, 12, 31)
    assert future.option_type is None

    option = repo.get_by_key("NSE_FO|OPT123")
    assert option.instrument_type == "OPTIONS"
    assert option.option_type == "CE"
    assert option.strike_price == Decimal("25000")
    option_response = InstrumentOut.model_validate(option)
    assert option_response.expiry == date(2026, 12, 31)
    assert option_response.strike_price == 25000
    assert option_response.option_type == "CE"

    bse_option = repo.get_by_key("BSE_FO|SENSEXOPT")
    assert bse_option.exchange == "BSE"
    assert bse_option.instrument_type == "OPTIONS"
    assert bse_option.option_type == "PE"

    assert repo.get_by_key("NCD_FO|NCD123").exchange == "NSE"
    assert repo.get_by_key("BCD_FO|BCD123").exchange == "BSE"
    assert repo.get_by_key("NSE_COM|COM123").segment == "NSE_COM"

    commodity_future = repo.get_by_key("MCX_FO|GOLD123")
    assert commodity_future.exchange == "MCX"
    assert commodity_future.instrument_type == "FUTURES"


@pytest.mark.asyncio
async def test_sync_from_upstox_preserves_catalog_when_download_fails(db_session, monkeypatch):
    repo = InstrumentRepository(db_session)
    repo.upsert(
        instrument_key="NSE_EQ|EXISTING",
        exchange="NSE",
        segment="NSE_EQ",
        instrument_type="EQUITY",
        trading_symbol="EXISTING",
        name="Existing instrument",
        lot_size=1,
        tick_size=Decimal("0.05"),
        expiry=None,
        strike_price=None,
        option_type=None,
        is_active=True,
    )
    fake_client = FakeAsyncClient(FakeResponse(503))
    monkeypatch.setattr(
        "app.services.instrument_service.httpx.AsyncClient",
        lambda **kwargs: fake_client,
    )

    ok, message = await InstrumentService(db_session).sync_from_upstox()

    assert ok is False
    assert "503" in message
    assert repo.count() == 1
    assert repo.get_by_key("NSE_EQ|EXISTING") is not None


@pytest.mark.asyncio
async def test_sync_from_upstox_rejects_malformed_or_unsupported_master_without_writes(
    db_session, monkeypatch
):
    malformed_client = FakeAsyncClient(FakeResponse(200, b"not gzip"))
    monkeypatch.setattr(
        "app.services.instrument_service.httpx.AsyncClient",
        lambda **kwargs: malformed_client,
    )
    ok, _ = await InstrumentService(db_session).sync_from_upstox()
    assert ok is False
    assert InstrumentRepository(db_session).count() == 0

    unsupported = [_record("UNKNOWN", "NSE", "EQ", "UNKNOWN|1", "UNKNOWN")]
    response = FakeResponse(200, gzip.compress(json.dumps(unsupported).encode("utf-8")))
    monkeypatch.setattr(
        "app.services.instrument_service.httpx.AsyncClient",
        lambda **kwargs: FakeAsyncClient(response),
    )
    ok, message = await InstrumentService(db_session).sync_from_upstox()
    assert ok is False
    assert "no supported" in message
    assert InstrumentRepository(db_session).count() == 0
