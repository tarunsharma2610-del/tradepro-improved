import gzip
import json

import pytest

from app.repositories.instrument_repository import InstrumentRepository
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


@pytest.mark.asyncio
async def test_sync_from_upstox_imports_nse_equities_and_skips_other_segments(db_session, monkeypatch):
    records = [
        {
            "segment": "NSE_EQ",
            "exchange": "NSE",
            "instrument_type": "EQ",
            "instrument_key": "NSE_EQ|INE002A01018",
            "trading_symbol": "RELIANCE",
            "name": "RELIANCE INDUSTRIES LTD",
            "lot_size": 1,
            "tick_size": 5.0,
        },
        {
            "segment": "NSE_FO",
            "exchange": "NSE",
            "instrument_type": "FUT",
            "instrument_key": "NSE_FO|12345",
            "trading_symbol": "RELIANCE FUT",
            "name": "RELIANCE FUTURE",
            "lot_size": 250,
            "tick_size": 0.05,
        },
    ]
    response = FakeResponse(200, gzip.compress(json.dumps(records).encode("utf-8")))
    fake_client = FakeAsyncClient(response)
    monkeypatch.setattr(
        "app.services.instrument_service.httpx.AsyncClient",
        lambda **kwargs: fake_client,
    )

    ok, message = await InstrumentService(db_session).sync_from_upstox()

    assert ok is True
    assert message == "Synced 1 NSE equity instruments."
    assert fake_client.requested_url == (
        "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz"
    )
    assert fake_client.requested_kwargs == {"follow_redirects": True}

    repo = InstrumentRepository(db_session)
    imported = repo.get_by_key("NSE_EQ|INE002A01018")
    assert imported is not None
    assert imported.trading_symbol == "RELIANCE"
    assert imported.exchange == "NSE"
    assert imported.instrument_type == "EQUITY"
    assert str(imported.tick_size) == "5.0000"
    assert repo.get_by_key("NSE_FO|12345") is None


@pytest.mark.asyncio
async def test_sync_from_upstox_preserves_catalog_when_download_fails(db_session, monkeypatch):
    fake_client = FakeAsyncClient(FakeResponse(503))
    monkeypatch.setattr(
        "app.services.instrument_service.httpx.AsyncClient",
        lambda **kwargs: fake_client,
    )

    ok, message = await InstrumentService(db_session).sync_from_upstox()

    assert ok is False
    assert "503" in message
    assert InstrumentRepository(db_session).count() == 0
