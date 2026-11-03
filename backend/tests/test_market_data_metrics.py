from app.api.v1.admin import market_data_metrics
from app.services.market_data_metrics import snapshot
from app.services.market_quote_dispatcher import MarketQuoteDispatcher


class _Observation:
    def __init__(self, instrument_key, version):
        self.user_id = "opaque-test-user"
        self.instrument_key = instrument_key
        self.epoch = "epoch-1"
        self.version = version


def test_market_data_metrics_are_aggregate_process_local_and_paper_only():
    result = market_data_metrics(_admin=object())

    assert result["scope"] == "process_local"
    assert result["trading_mode"] == "PAPER"
    assert isinstance(result["counters"], dict)
    assert not any("user" in key or "instrument" in key for key in result["counters"])


def test_dispatcher_updates_operational_counters_for_accept_coalesce_drop_and_reject():
    before = snapshot()["counters"]
    dispatcher = MarketQuoteDispatcher(max_pending_keys=1)

    assert dispatcher.publish(_Observation("NSE_EQ|ONE", 1))
    assert dispatcher.publish(_Observation("NSE_EQ|ONE", 2))
    assert not dispatcher.publish(_Observation("NSE_EQ|TWO", 1))
    assert not dispatcher.publish(_Observation("NSE_EQ|ONE", 1))

    after = snapshot()["counters"]
    assert after["market_quote_dispatch_accepted_unique_total"] - before.get(
        "market_quote_dispatch_accepted_unique_total", 0
    ) == 1
    assert after["market_quote_dispatch_coalesced_total"] - before.get(
        "market_quote_dispatch_coalesced_total", 0
    ) == 1
    assert after["market_quote_dispatch_dropped_unique_total"] - before.get(
        "market_quote_dispatch_dropped_unique_total", 0
    ) == 1
    assert after["market_quote_dispatch_rejected_total"] - before.get(
        "market_quote_dispatch_rejected_total", 0
    ) == 1
    assert "opaque-test-user" not in repr(after)
    assert "NSE_EQ|ONE" not in repr(after)


def test_metric_names_are_allowlisted_to_prevent_unbounded_cardinality():
    import pytest
    from app.services.market_data_metrics import increment

    with pytest.raises(ValueError, match="Unknown market-data metric"):
        increment("market_quote_dispatch_user_secret_123")


def test_snapshot_exposes_fixed_zero_initialized_counter_set():
    from app.services.market_data_metrics import _ALLOWED_COUNTERS, snapshot

    result = snapshot()
    assert result["scope"] == "process_local"
    assert result["trading_mode"] == "PAPER"
    assert len(result["counters"]) == len(_ALLOWED_COUNTERS)
    assert all(isinstance(value, int) and value >= 0 for value in result["counters"].values())
