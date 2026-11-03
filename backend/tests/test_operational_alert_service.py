from unittest.mock import AsyncMock

import pytest

from app.services import operational_alert_service as ops


class _Redis:
    def __init__(self):
        self.keys = set()

    async def set(self, key, value, nx=False, ex=None):
        if nx and key in self.keys:
            return False
        self.keys.add(key)
        return True

    async def delete(self, key):
        self.keys.discard(key)


class _Db:
    def close(self):
        pass


class _Settings:
    def __init__(self, _db, values):
        self.values = values

    def get_decrypted(self, key):
        return self.values.get(key)


def _snapshot(*, dropped=0, exhausted=0, failures=0, rejected=0, workers=1):
    return {
        "worker_count": workers,
        "counters": {
            "market_quote_dispatch_dropped_unique_total": dropped,
            "market_quote_dispatch_exhausted_total": exhausted,
            "market_quote_dispatch_handler_failures_total": failures,
            "market_quote_dispatch_rejected_total": rejected,
        },
    }


def test_dispatch_alert_evaluator_uses_deltas_and_thresholds():
    previous = {
        "market_quote_dispatch_dropped_unique_total": 2,
        "market_quote_dispatch_exhausted_total": 0,
        "market_quote_dispatch_handler_failures_total": 4,
        "market_quote_dispatch_rejected_total": 10,
    }
    current = _snapshot(dropped=3, exhausted=1, failures=9, rejected=35)
    alerts = ops.evaluate_dispatch_alerts(current, previous)

    assert {fingerprint for fingerprint, _ in alerts} == {
        "dispatch_dropped",
        "dispatch_exhausted",
        "dispatch_handler_failures",
        "dispatch_rejections",
    }
    assert all("user_id" not in message and "instrument_key" not in message for _, message in alerts)


def test_dispatch_alert_evaluator_ignores_small_failure_and_rejection_deltas():
    previous = {
        "market_quote_dispatch_dropped_unique_total": 0,
        "market_quote_dispatch_exhausted_total": 0,
        "market_quote_dispatch_handler_failures_total": 0,
        "market_quote_dispatch_rejected_total": 0,
    }
    alerts = ops.evaluate_dispatch_alerts(
        _snapshot(failures=4, rejected=24), previous
    )
    assert alerts == []


@pytest.mark.asyncio
async def test_monitor_delivers_new_dispatch_alert_once(monkeypatch):
    snapshots = iter([
        _snapshot(dropped=0),
        _snapshot(dropped=1),
        _snapshot(dropped=1),
    ])

    async def read_metrics(_redis):
        return next(snapshots)

    monkeypatch.setattr(
        ops, "PlatformSettingsService",
        lambda db: _Settings(db, {
            "telegram_bot_token": "test-token",
            "ops_alert_telegram_chat_id": "-1001234567890",
        }),
    )
    send = AsyncMock(return_value=type("Result", (), {"ok": True, "error": None})())
    monkeypatch.setattr(ops.telegram_notifier, "send_message", send)

    monitor = ops.OperationalAlertMonitor(
        _Redis(), metrics_reader=read_metrics, session_factory=_Db
    )
    await monitor.run_once()  # baseline only
    await monitor.run_once()  # one dropped observation
    await monitor.run_once()  # no new delta

    send.assert_awaited_once()
    assert send.await_args.args[0] == "test-token"
    assert send.await_args.args[1] == -1001234567890
    assert "dropped 1 unique observation" in send.await_args.args[2]


@pytest.mark.asyncio
async def test_monitor_does_not_send_without_valid_admin_destination(monkeypatch):
    async def read_metrics(_redis):
        return _snapshot()

    monkeypatch.setattr(
        ops, "PlatformSettingsService",
        lambda db: _Settings(db, {
            "telegram_bot_token": "test-token",
            "ops_alert_telegram_chat_id": "not-a-chat-id",
        }),
    )
    send = AsyncMock()
    monkeypatch.setattr(ops.telegram_notifier, "send_message", send)

    monitor = ops.OperationalAlertMonitor(
        _Redis(), metrics_reader=read_metrics, session_factory=_Db
    )
    await monitor._send("invalid-destination", "test alert")

    send.assert_not_awaited()


@pytest.mark.asyncio
async def test_monitor_alerts_after_worker_heartbeat_absence_threshold(monkeypatch):
    now = [100.0]

    async def read_metrics(_redis):
        return _snapshot(workers=0)

    monkeypatch.setattr(
        ops, "PlatformSettingsService",
        lambda db: _Settings(db, {
            "telegram_bot_token": "test-token",
            "ops_alert_telegram_chat_id": "12345",
        }),
    )
    send = AsyncMock(return_value=type("Result", (), {"ok": True, "error": None})())
    monkeypatch.setattr(ops.telegram_notifier, "send_message", send)

    monitor = ops.OperationalAlertMonitor(
        _Redis(), metrics_reader=read_metrics, session_factory=_Db,
        no_worker_seconds=60, monotonic=lambda: now[0],
    )
    await monitor.run_once()
    now[0] += 59
    await monitor.run_once()
    send.assert_not_awaited()
    now[0] += 2
    await monitor.run_once()
    send.assert_awaited_once()
    assert "No active PAPER" in send.await_args.args[2]

@pytest.mark.asyncio
async def test_two_monitor_replicas_share_redis_alert_deduplication(monkeypatch):
    redis = _Redis()
    sent = []

    snapshots = iter([
        _snapshot(dropped=0),
        _snapshot(dropped=0),
        _snapshot(dropped=1),
        _snapshot(dropped=1),
    ])

    async def read_metrics(_redis):
        return next(snapshots)

    monkeypatch.setattr(
        ops, "PlatformSettingsService",
        lambda db: _Settings(db, {
            "telegram_bot_token": "test-token",
            "ops_alert_telegram_chat_id": "12345",
        }),
    )

    async def send(token, chat_id, message):
        sent.append((token, chat_id, message))
        return type("Result", (), {"ok": True, "error": None})()

    monkeypatch.setattr(ops.telegram_notifier, "send_message", send)
    first = ops.OperationalAlertMonitor(
        redis, metrics_reader=read_metrics, session_factory=_Db
    )
    second = ops.OperationalAlertMonitor(
        redis, metrics_reader=read_metrics, session_factory=_Db
    )

    # Both replicas establish the same initial counter baseline.
    await first.run_once()
    await second.run_once()
    # Both observe the same fleet counter delta; Redis NX allows one delivery.
    await first.run_once()
    await second.run_once()

    assert len(sent) == 1


@pytest.mark.asyncio
async def test_missing_destination_does_not_consume_alert_cooldown(monkeypatch):
    redis = _Redis()
    configured = {"token": None, "chat_id": None}
    sent = AsyncMock(return_value=type("Result", (), {"ok": True, "error": None})())

    monkeypatch.setattr(
        ops, "PlatformSettingsService",
        lambda db: _Settings(db, {
            "telegram_bot_token": configured["token"],
            "ops_alert_telegram_chat_id": configured["chat_id"],
        }),
    )
    monkeypatch.setattr(ops.telegram_notifier, "send_message", sent)
    monitor = ops.OperationalAlertMonitor(
        redis, session_factory=_Db
    )

    assert await monitor._send("config-retry", "test alert") is False
    assert not redis.keys

    configured["token"] = "test-token"
    configured["chat_id"] = "12345"
    assert await monitor._send("config-retry", "test alert") is True
    sent.assert_awaited_once()
