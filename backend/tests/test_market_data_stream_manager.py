import asyncio
from uuid import uuid4

import pytest

from app.services import market_data_stream_manager as stream_manager_module


@pytest.mark.asyncio
async def test_concurrent_start_requests_share_one_per_user_stream(monkeypatch):
    manager = stream_manager_module.MarketDataStreamManager()
    user_id = uuid4()
    start_entered = asyncio.Event()
    allow_start = asyncio.Event()
    created = []

    class FakeStreamer:
        def __init__(self, _token_provider, instrument_keys, on_tick=None, mode="full"):
            self.instrument_keys = list(instrument_keys)
            self.subscriptions = {mode: set(instrument_keys)}
            self.mode = mode
            self.running = False
            self.subscribe_calls = []

        @property
        def subscriptions_by_mode(self):
            return {mode: sorted(keys) for mode, keys in self.subscriptions.items() if keys}

        async def start(self):
            start_entered.set()
            await allow_start.wait()
            self.running = True

        async def subscribe(self, instrument_keys, mode):
            self.subscribe_calls.append((list(instrument_keys), mode))
            self.subscriptions.setdefault(mode, set()).update(instrument_keys)
            self.instrument_keys = sorted(set(self.instrument_keys) | set(instrument_keys))

        async def stop(self):
            self.running = False

    def streamer_factory(*args, **kwargs):
        instance = FakeStreamer(*args, **kwargs)
        created.append(instance)
        return instance

    monkeypatch.setattr(stream_manager_module, "UpstoxMarketDataStreamer", streamer_factory)
    monkeypatch.setattr(stream_manager_module, "RedisMarketQuotePublisher", lambda *_args: object())
    monkeypatch.setattr(manager, "_redis_client", lambda: object())

    first = asyncio.create_task(manager.start(user_id, ["NSE_EQ|AAA"], "ltpc"))
    await start_entered.wait()
    second = asyncio.create_task(manager.start(user_id, ["NSE_FO|BBB"], "full"))
    await asyncio.sleep(0)
    allow_start.set()

    first_stream, second_stream = await asyncio.gather(first, second)

    assert first_stream is second_stream
    assert len(created) == 1
    assert created[0].subscribe_calls == [(["NSE_FO|BBB"], "full")]
    assert manager.get(user_id) is created[0]
    assert await manager.stop(user_id) is True
    assert manager.get(user_id) is None


@pytest.mark.asyncio
async def test_failed_stream_start_removes_unusable_registry_entry(monkeypatch):
    manager = stream_manager_module.MarketDataStreamManager()
    user_id = uuid4()

    class FailedStreamer:
        running = False

        def __init__(self, *_args, **_kwargs):
            pass

        async def start(self):
            raise RuntimeError("simulated upstream startup failure")

    monkeypatch.setattr(stream_manager_module, "UpstoxMarketDataStreamer", FailedStreamer)
    monkeypatch.setattr(stream_manager_module, "RedisMarketQuotePublisher", lambda *_args: object())
    monkeypatch.setattr(manager, "_redis_client", lambda: object())

    with pytest.raises(RuntimeError, match="upstream startup failure"):
        await manager.start(user_id, ["NSE_EQ|AAA"], "ltpc")

    assert manager.get(user_id) is None
