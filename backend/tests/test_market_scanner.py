from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.services.market_scanner import MarketScanner


def quote(user_id, **overrides):
    now = datetime.now(timezone.utc)
    data = {
        "user_id": str(user_id), "instrument_key": "NSE_EQ|INE002A01018",
        "epoch": "epoch-1", "version": 1, "ltp": 110.0,
        "exchange_timestamp_ms": int(now.timestamp() * 1000),
        "received_at": now.isoformat(),
        "ohlc": [{"interval": "1d", "close": 100.0}],
        "volume_traded_today": 125000, "open_interest": None,
        "total_buy_quantity": 600, "total_sell_quantity": 400,
        "option_greeks": {"delta": 0.62, "theta": None, "gamma": float("nan")},
        "depth": [{"bid_price": 109.9, "ask_price": 110.1, "bid_quantity": 250, "ask_quantity": 300}],
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
    assert result.best_bid_price == 109.9
    assert result.best_ask_price == 110.1
    assert round(result.spread_bps, 4) == round((0.2 / 110.0) * 10_000, 4)
    assert result.best_bid_quantity == 250
    assert result.best_ask_quantity == 300
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
        total_sell_quantity=None, option_greeks=None, depth=None,
    ))
    assert result is not None
    assert result.price_change_pct is None
    assert result.volume_traded_today is None
    assert result.buy_sell_imbalance is None
    assert result.option_greeks is None
    assert result.spread_bps is None
    assert result.best_bid_quantity is None
    assert result.best_ask_quantity is None


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
    monkeypatch.setattr(scanner_module.time, "monotonic", lambda: 100.0)
    result = scanner.process_quote(user_id, quote(user_id))
    assert result is not None
    monkeypatch.setattr(scanner_module.time, "monotonic", lambda: 115.1)

    assert scanner.latest(user_id, result.instrument_key) is None


def test_scanner_rejects_stale_receive_and_exchange_timestamps():
    user_id, scanner = uuid4(), MarketScanner(max_age_seconds=15)
    now = datetime.now(timezone.utc)
    stale = now - timedelta(seconds=16)
    assert scanner.process_quote(
        user_id,
        quote(
            user_id,
            received_at=stale.isoformat(),
            exchange_timestamp_ms=int(stale.timestamp() * 1000),
        ),
        now=now,
    ) is None

    assert scanner.process_quote(
        user_id,
        quote(
            user_id,
            exchange_timestamp_ms=int(stale.timestamp() * 1000),
        ),
        now=now,
    ) is None


def test_scanner_rejects_exchange_timestamp_beyond_future_clock_skew():
    user_id, scanner = uuid4(), MarketScanner(max_age_seconds=15)
    now = datetime.now(timezone.utc)
    future = now + timedelta(seconds=61)
    assert scanner.process_quote(
        user_id,
        quote(user_id, exchange_timestamp_ms=int(future.timestamp() * 1000)),
        now=now,
    ) is None


def test_scanner_accepts_exchange_timestamp_within_future_clock_skew():
    user_id, scanner = uuid4(), MarketScanner(max_age_seconds=15)
    now = datetime.now(timezone.utc)
    slight_future = now + timedelta(seconds=30)
    result = scanner.process_quote(
        user_id,
        quote(
            user_id,
            received_at=now.isoformat(),
            exchange_timestamp_ms=int(slight_future.timestamp() * 1000),
        ),
        now=now,
    )
    assert result is not None


def test_scanner_rejects_crossed_or_invalid_top_of_book_spread():
    user_id, scanner = uuid4(), MarketScanner()
    crossed = scanner.process_quote(user_id, quote(
        user_id,
        depth=[{"bid_price": 101.0, "ask_price": 100.0,
                "bid_quantity": 20, "ask_quantity": 30}],
    ))
    assert crossed is not None
    assert crossed.best_bid_price is None
    assert crossed.best_ask_price is None
    assert crossed.spread_bps is None
    assert crossed.best_bid_quantity == 20
    assert crossed.best_ask_quantity == 30

    invalid = scanner.process_quote(user_id, quote(
        user_id, version=2,
        depth=[{"bid_price": float("nan"), "ask_price": 100.0,
                "bid_quantity": -1, "ask_quantity": float("inf")}],
    ))
    assert invalid is not None
    assert invalid.spread_bps is None
    assert invalid.best_bid_quantity is None
    assert invalid.best_ask_quantity is None


def test_market_quality_filter_uses_explicit_thresholds_and_fails_closed():
    user_id, scanner = uuid4(), MarketScanner()
    observation = scanner.process_quote(user_id, quote(user_id))
    assert observation is not None
    assert scanner.passes_market_quality(
        observation, max_spread_bps=25, min_bid_quantity=200, min_ask_quantity=250
    )
    assert not scanner.passes_market_quality(
        observation, max_spread_bps=10, min_bid_quantity=200, min_ask_quantity=250
    )
    assert not scanner.passes_market_quality(
        observation, max_spread_bps=25, min_bid_quantity=300, min_ask_quantity=250
    )
    assert not scanner.passes_market_quality(
        observation, max_spread_bps=float("nan")
    )

    no_depth = scanner.process_quote(
        user_id, quote(user_id, version=2, depth=None)
    )
    assert no_depth is not None
    assert not scanner.passes_market_quality(no_depth, max_spread_bps=100)


def test_historical_momentum_uses_validated_upstox_candles_and_shared_indicator():
    from app.services.market_scanner import MarketScanner

    rows = []
    for index in reversed(range(12)):
        close = 100 + index
        stamp = f"2026-11-03T10:{index:02d}:00+05:30"
        rows.append([stamp, close, close + 1, close - 1, close, 1000, 0])
    payload = {"status": "success", "data": {"candles": rows}}
    score = MarketScanner.historical_momentum_from_response(payload, period=10)
    assert score is not None
    assert score > 0

    assert MarketScanner.historical_momentum_from_response(
        {"status": "error", "data": {"candles": rows}}, period=10
    ) is None
    assert MarketScanner.historical_momentum_from_response(
        {"status": "success", "data": {"candles": rows[:5]}}, period=10
    ) is None
    assert MarketScanner.historical_momentum_from_response(payload, period=0) is None


def test_historical_momentum_rejects_malformed_candle_rows():
    rows = [["2026-11-03T10:00:00+05:30", 100, 101, 99, 100, 1000, 0]]
    payload = {"status": "success", "data": {"candles": rows}}
    assert MarketScanner.historical_momentum_from_response(payload, period=1) is None


def test_relative_volume_uses_same_time_slot_across_distinct_sessions():
    from datetime import datetime, timedelta, timezone
    from decimal import Decimal

    rows = []
    today = datetime(2026, 11, 3, 10, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    cursor = today
    sessions = 0
    while sessions < 20:
        cursor -= timedelta(days=1)
        if cursor.weekday() >= 5:
            continue
        rows.append([cursor.isoformat(), 100, 101, 99, 100, 1000, 0])
        # A different intraday slot must not contaminate the baseline.
        rows.append([(cursor + timedelta(minutes=5)).isoformat(), 100, 101, 99, 100, 9000, 0])
        sessions += 1
    rows.append([today.isoformat(), 100, 101, 99, 100, 2500, 0])
    payload = {"status": "success", "data": {"candles": list(reversed(rows))}}

    result = MarketScanner.relative_volume_from_response(payload, lookback_sessions=20)
    assert result == Decimal("2.5")


def test_relative_volume_fails_closed_for_incomplete_or_zero_baseline():
    from datetime import datetime, timedelta, timezone

    today = datetime(2026, 11, 3, 10, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    short_rows = []
    for days_ago in range(3, 0, -1):
        stamp = (today - timedelta(days=days_ago)).isoformat()
        short_rows.append([stamp, 100, 101, 99, 100, 1000, 0])
    short_rows.append([today.isoformat(), 100, 101, 99, 100, 2000, 0])
    short_payload = {"status": "success", "data": {"candles": list(reversed(short_rows))}}
    assert MarketScanner.relative_volume_from_response(
        short_payload, lookback_sessions=5
    ) is None

    zero_rows = []
    for days_ago in range(3, 0, -1):
        stamp = (today - timedelta(days=days_ago)).isoformat()
        zero_rows.append([stamp, 100, 101, 99, 100, 0, 0])
    zero_rows.append([today.isoformat(), 100, 101, 99, 100, 2000, 0])
    zero_payload = {"status": "success", "data": {"candles": list(reversed(zero_rows))}}
    assert MarketScanner.relative_volume_from_response(
        zero_payload, lookback_sessions=3
    ) is None


def test_opportunity_ranking_is_weighted_explainable_and_deterministic():
    candidates = [
        {"instrument_key": "NSE_EQ|BBB", "factors": {"momentum": 0.8, "relative_volume": 0.6, "liquidity": 1.0}},
        {"instrument_key": "NSE_EQ|AAA", "factors": {"momentum": 0.8, "relative_volume": 0.6, "liquidity": 1.0}},
        {"instrument_key": "NSE_EQ|CCC", "factors": {"momentum": 0.2, "relative_volume": 0.2, "liquidity": 0.2}},
    ]
    weights = {"momentum": 0.5, "relative_volume": 0.3, "liquidity": 0.2}
    ranked = MarketScanner.rank_opportunities(candidates, weights=weights)

    assert [item["instrument_key"] for item in ranked] == [
        "NSE_EQ|AAA", "NSE_EQ|BBB", "NSE_EQ|CCC"
    ]
    assert [item["rank"] for item in ranked] == [1, 2, 3]
    assert ranked[0]["score"] == 0.78
    assert ranked[0]["weighted_contributions"] == {
        "momentum": 0.4, "relative_volume": 0.18, "liquidity": 0.2
    }


def test_opportunity_ranking_rejects_invalid_weights_and_excludes_bad_factors():
    valid = {"instrument_key": "NSE_EQ|AAA", "factors": {"momentum": 1, "relative_volume": 1, "liquidity": 1}}
    invalid = {"instrument_key": "NSE_EQ|BAD", "factors": {"momentum": float("nan"), "relative_volume": 1, "liquidity": 1}}
    weights = {"momentum": 1, "relative_volume": 1, "liquidity": 1}

    assert MarketScanner.rank_opportunities([valid], weights={"momentum": -1, "relative_volume": 1, "liquidity": 1}) == []
    assert MarketScanner.rank_opportunities([valid], weights={"momentum": 0, "relative_volume": 0, "liquidity": 0}) == []
    assert MarketScanner.rank_opportunities([valid], weights={"momentum": 1}) == []
    ranked = MarketScanner.rank_opportunities([invalid, valid], weights=weights)
    assert [item["instrument_key"] for item in ranked] == ["NSE_EQ|AAA"]


def test_opportunity_ranking_ignores_duplicate_instrument_keys():
    candidate = {"instrument_key": "NSE_EQ|AAA", "factors": {"momentum": 0.5, "relative_volume": 0.5, "liquidity": 0.5}}
    ranked = MarketScanner.rank_opportunities(
        [candidate, candidate], weights={"momentum": 1, "relative_volume": 1, "liquidity": 1}
    )
    assert len(ranked) == 1
