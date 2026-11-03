from app.api.v1.admin import market_data_metrics


def test_market_data_metrics_are_aggregate_process_local_and_paper_only():
    result = market_data_metrics(_admin=object())

    assert result["scope"] == "process_local"
    assert result["trading_mode"] == "PAPER"
    assert isinstance(result["counters"], dict)
    assert not any("user" in key or "instrument" in key for key in result["counters"])
