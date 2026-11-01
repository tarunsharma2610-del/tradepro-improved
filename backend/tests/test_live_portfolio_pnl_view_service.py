from datetime import datetime, timedelta, timezone

from app.services.live_portfolio_pnl_view_service import build_live_unrealized_pnl_view


NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


def quote(ltp="110", age=2):
    return {"ltp": ltp, "received_at": (NOW - timedelta(seconds=age)).isoformat()}


def test_complete_portfolio_sums_long_and_short_using_fresh_quotes():
    result = build_live_unrealized_pnl_view(
        broker_positions=[
            {"instrument_key": "NSE_EQ|AAA", "quantity": 10, "average_price": "100.0000"},
            {"instrument_key": "NSE_FO|BBB", "quantity": -5, "average_price": "200.0000"},
        ],
        quotes_by_instrument={
            "NSE_EQ|AAA": quote("110"),
            "NSE_FO|BBB": quote("190"),
        },
        now=NOW,
    )
    assert result["complete"] is True
    assert result["total_unrealized_pnl"] == "150.00"
    assert [row["status"] for row in result["rows"]] == ["AVAILABLE", "AVAILABLE"]


def test_missing_or_stale_quote_makes_total_unavailable_not_partial():
    result = build_live_unrealized_pnl_view(
        broker_positions=[
            {"instrument_key": "NSE_EQ|AAA", "quantity": 10, "average_price": "100"},
            {"instrument_key": "NSE_EQ|BBB", "quantity": 5, "average_price": "200"},
        ],
        quotes_by_instrument={"NSE_EQ|AAA": quote("110"), "NSE_EQ|BBB": quote("210", age=16)},
        now=NOW,
    )
    assert result["complete"] is False
    assert result["total_unrealized_pnl"] is None
    assert result["unavailable_position_count"] == 1
    assert result["rows"][1]["status"] == "QUOTE_OR_PRICE_INVALID_OR_STALE"


def test_flat_positions_do_not_require_a_quote():
    result = build_live_unrealized_pnl_view(
        broker_positions=[{"instrument_key": "NSE_EQ|AAA", "quantity": 0, "average_price": "0"}],
        quotes_by_instrument={},
        now=NOW,
    )
    assert result["complete"] is True
    assert result["total_unrealized_pnl"] == "0.00"


def test_unknown_or_malformed_rows_fail_closed():
    result = build_live_unrealized_pnl_view(
        broker_positions=[None, {"instrument_key": "NSE_EQ|AAA", "quantity": True, "average_price": "100"}],
        quotes_by_instrument={},
        now=NOW,
    )
    assert result["complete"] is False
    assert result["total_unrealized_pnl"] is None
    assert [row["status"] for row in result["rows"]] == ["INVALID_BROKER_POSITION", "INVALID_QUANTITY"]


def test_missing_instrument_key_is_not_guessed_from_symbol():
    result = build_live_unrealized_pnl_view(
        broker_positions=[{"trading_symbol": "ABC", "quantity": 2, "average_price": "10"}],
        quotes_by_instrument={"NSE_EQ|ABC": quote("11")},
        now=NOW,
    )
    assert result["complete"] is False
    assert result["rows"][0]["status"] == "MISSING_INSTRUMENT_KEY"
