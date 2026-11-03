from decimal import Decimal

from app.services.candle_parsing import parse_candles


def _official_style_payload():
    # Mirrors Upstox's documented V3 row layout and newest-first response.
    return {
        "status": "success",
        "data": {
            "candles": [
                ["2025-01-12T15:15:00+05:30", 2305.3, 2307.05, 2301.0, 2304.65, 559982, 0],
                ["2025-01-12T15:10:00+05:30", 2309.1, 2310.75, 2305.25, 2305.3, 740124, 0],
            ]
        },
    }


def test_documented_upstox_candle_rows_are_normalized_oldest_first():
    candles = parse_candles(_official_style_payload())

    assert candles is not None
    assert len(candles) == 2
    assert candles[0].timestamp.isoformat() == "2025-01-12T15:10:00+05:30"
    assert candles[0].open == Decimal("2309.1")
    assert candles[0].high == Decimal("2310.75")
    assert candles[0].low == Decimal("2305.25")
    assert candles[0].close == Decimal("2305.3")
    assert candles[0].volume == 740124
    assert candles[1].timestamp.isoformat() == "2025-01-12T15:15:00+05:30"


def test_parser_rejects_unsuccessful_or_missing_status():
    payload = _official_style_payload()
    payload["status"] = "error"
    assert parse_candles(payload) is None
    assert parse_candles({"data": payload["data"]}) is None


def test_parser_rejects_malformed_rows_and_naive_timestamps():
    payload = _official_style_payload()
    payload["data"]["candles"][0] = ["2025-01-12T15:15:00", 1, 1, 1, 1, 1, 0]
    assert parse_candles(payload) is None

    payload = _official_style_payload()
    payload["data"]["candles"][0] = ["2025-01-12T15:15:00+05:30", 1, 1, 1, 1, 1]
    assert parse_candles(payload) is None


def test_parser_rejects_invalid_ohlc_nonfinite_prices_and_negative_volume():
    payload = _official_style_payload()
    payload["data"]["candles"][0] = ["2025-01-12T15:15:00+05:30", 10, 8, 9, 10, 1, 0]
    assert parse_candles(payload) is None

    payload = _official_style_payload()
    payload["data"]["candles"][0] = ["2025-01-12T15:15:00+05:30", "NaN", 10, 9, 10, 1, 0]
    assert parse_candles(payload) is None

    payload = _official_style_payload()
    payload["data"]["candles"][0] = ["2025-01-12T15:15:00+05:30", 10, 10, 9, 10, -1, 0]
    assert parse_candles(payload) is None


def test_parser_rejects_duplicate_timestamps_and_fractional_volume():
    payload = _official_style_payload()
    payload["data"]["candles"][1][0] = payload["data"]["candles"][0][0]
    assert parse_candles(payload) is None

    payload = _official_style_payload()
    payload["data"]["candles"][0][5] = 1.5
    assert parse_candles(payload) is None
