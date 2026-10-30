from datetime import datetime, timezone
from uuid import uuid4

from app.services.market_scanner import MarketScanner


def quote(user_id, **overrides):
    data = {
        "user_id": str(user_id), "instrument_key": "NSE_EQ|INE002A01018",
        "epoch": "epoch-1", "version": 1, "ltp": 110.0,
        "exchange_timestamp_ms": 1_800_000_000_000,
        "received_at": datetime.now(timezone.utc).isoformat(),
        "ohlc": [{"interval": "1d", "close": 100.0}],
        "volume_traded_today": 125000, "open_interest": None,
        "total_buy_quantity": 600, "total_sell_quantity": 400,
        "option_greeks": {"delta": 0.62, "theta": None, "gamma": float("nan")},
    }
    data.update(overrides)
    return data


def test_scanner_computes_observation_without_trade_signal():
    user_id, scanner = uuid4(), MarketScanner()
    result = scanner.process_quote(user_id, quote(user_id))
    assert result is not None
    assert result.price_change_pct == 10.0
    assert result.volume_traded_today == 125000
    assert result.open_interest is None
    assert result.buy_sell_imbalance == 0.2
    assert result.option_greeks == {"delta": 0.62}
    assert not hasattr(result, "signal")
    assert scanner.latest(user_id, result.instrument_key) == result


def test_scanner_rejects_cross_user_and_non_monotonic_updates():
    user_id, scanner = uuid4(), MarketScanner()
    assert scanner.process_quote(user_id, quote(uuid4())) is None
    assert scanner.process_quote(user_id, quote(user_id)) is not None
    assert scanner.process_quote(user_id, quote(user_id, version=1)) is None
    assert scanner.process_quote(user_id, quote(user_id, version=2)) is not None


def test_scanner_preserves_missing_values():
    user_id, scanner = uuid4(), MarketScanner()
    result = scanner.process_quote(user_id, quote(
        user_id, ohlc=[{"interval": "1m", "close": 100.0}],
        volume_traded_today=None, total_buy_quantity=None,
        total_sell_quantity=None, option_greeks=None,
    ))
    assert result is not None
    assert result.price_change_pct is None
    assert result.volume_traded_today is None
    assert result.buy_sell_imbalance is None
    assert result.option_greeks is None


def test_scanner_rejects_invalid_boundary_fields():
    user_id, scanner = uuid4(), MarketScanner()
    for overrides in (
        {"ltp": 0}, {"ltp": float("nan")}, {"version": True},
        {"exchange_timestamp_ms": 0}, {"received_at": "2026-10-30T10:00:00"},
    ):
        assert scanner.process_quote(user_id, quote(user_id, **overrides)) is None


def test_scanner_accepts_new_epoch_after_redis_restart():
    user_id, scanner = uuid4(), MarketScanner()
    assert scanner.process_quote(user_id, quote(user_id, version=8, epoch="old")) is not None
    result = scanner.process_quote(user_id, quote(user_id, version=1, epoch="new"))
    assert result is not None and result.version == 1 and result.epoch == "new"


def test_scanner_expires_stale_observations(monkeypatch):
    from app.services import market_scanner as scanner_module

    user_id, scanner = uuid4(), MarketScanner(max_age_seconds=15)
    result = scanner.process_quote(user_id, quote(user_id))
    assert result is not None
    monkeypatch.setattr(scanner_module.time, "monotonic", lambda: 15.1)

    assert scanner.latest(user_id, result.instrument_key) is None
