from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app import main


class _Query:
    def __init__(self, rows):
        self.rows = rows

    def join(self, *_args, **_kwargs):
        return self

    def filter(self, *_args, **_kwargs):
        return self

    def all(self):
        return self.rows


class _Session:
    def __init__(self, rows):
        self.rows = rows
        self.closed = False

    def query(self, *_args, **_kwargs):
        return _Query(self.rows)

    def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_startup_restores_all_persisted_feed_modes(monkeypatch):
    user_id = "user-1"
    rows = [
        SimpleNamespace(user_id=user_id, feed_mode="ltpc",
                        instrument=SimpleNamespace(instrument_key="NSE_INDEX|NIFTY50")),
        SimpleNamespace(user_id=user_id, feed_mode="full",
                        instrument=SimpleNamespace(instrument_key="NSE_FO|OPTION1")),
    ]
    session = _Session(rows)
    start = AsyncMock(side_effect=[
        SimpleNamespace(instrument_keys=["NSE_INDEX|NIFTY50"], connected=True),
        SimpleNamespace(instrument_keys=["NSE_INDEX|NIFTY50", "NSE_FO|OPTION1"], connected=True),
    ])
    monkeypatch.setattr(main, "SessionLocal", lambda: session)
    monkeypatch.setattr(main.market_data_stream_manager, "start", start)

    await main._restore_desired_market_streams()

    assert session.closed is True
    assert start.await_count == 2
    assert [call.kwargs["mode"] for call in start.await_args_list] == ["full", "ltpc"]


@pytest.mark.asyncio
async def test_startup_skips_ambiguous_instrument_mode_assignments(monkeypatch):
    user_id = "user-2"
    rows = [
        SimpleNamespace(user_id=user_id, feed_mode="ltpc",
                        instrument=SimpleNamespace(instrument_key="NSE_EQ|ABC")),
        SimpleNamespace(user_id=user_id, feed_mode="full",
                        instrument=SimpleNamespace(instrument_key="NSE_EQ|ABC")),
    ]
    session = _Session(rows)
    start = AsyncMock()
    monkeypatch.setattr(main, "SessionLocal", lambda: session)
    monkeypatch.setattr(main.market_data_stream_manager, "start", start)

    await main._restore_desired_market_streams()

    assert session.closed is True
    start.assert_not_awaited()
