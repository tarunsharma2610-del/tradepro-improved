from decimal import Decimal

import pytest

from app.services.transaction_costs import Segment, Side, calculate_costs


def test_gst_is_exactly_18pct_of_brokerage_exchange_sebi_only():
    """GST must not be charged on STT or stamp duty — they're direct
    taxes, not a service Upstox is rendering."""
    costs = calculate_costs(Segment.EQUITY_INTRADAY, Side.SELL, 100, Decimal("1000"))
    expected_gst = ((costs.brokerage + costs.exchange_charges + costs.sebi_charges) * Decimal("0.18")).quantize(Decimal("0.01"))
    assert costs.gst == expected_gst


def test_total_charges_equals_sum_of_components():
    costs = calculate_costs(Segment.EQUITY_DELIVERY, Side.BUY, 10, Decimal("2500"))
    assert costs.total_charges == (
        costs.brokerage + costs.stt + costs.exchange_charges + costs.sebi_charges + costs.stamp_duty + costs.gst
    )


def test_equity_delivery_stt_charged_both_sides():
    buy = calculate_costs(Segment.EQUITY_DELIVERY, Side.BUY, 10, Decimal("1000"))
    sell = calculate_costs(Segment.EQUITY_DELIVERY, Side.SELL, 10, Decimal("1000"))
    assert buy.stt > 0
    assert sell.stt > 0
    assert buy.stt == sell.stt  # same 0.1% rate both sides


def test_equity_intraday_stt_sell_side_only():
    buy = calculate_costs(Segment.EQUITY_INTRADAY, Side.BUY, 10, Decimal("1000"))
    sell = calculate_costs(Segment.EQUITY_INTRADAY, Side.SELL, 10, Decimal("1000"))
    assert buy.stt == Decimal("0.00")
    assert sell.stt > 0


def test_futures_and_options_stt_sell_side_only_and_options_pricier():
    """Post-Budget-2026 rates: options premium STT (0.15%) is higher than
    futures STT (0.05%) — this is a real, deliberate policy asymmetry, not
    a bug, so the test locks in the relationship rather than exact values
    that will need updating again on the next Finance Bill."""
    fut_buy = calculate_costs(Segment.FUTURES, Side.BUY, 50, Decimal("20000"))
    fut_sell = calculate_costs(Segment.FUTURES, Side.SELL, 50, Decimal("20000"))
    opt_sell = calculate_costs(Segment.OPTIONS, Side.SELL, 50, Decimal("200"))

    assert fut_buy.stt == Decimal("0.00")
    assert fut_sell.stt > 0

    fut_rate = fut_sell.stt / fut_sell.gross_value
    opt_rate = opt_sell.stt / opt_sell.gross_value
    assert opt_rate > fut_rate


def test_stamp_duty_buy_side_only():
    buy = calculate_costs(Segment.EQUITY_DELIVERY, Side.BUY, 10, Decimal("1000"))
    sell = calculate_costs(Segment.EQUITY_DELIVERY, Side.SELL, 10, Decimal("1000"))
    assert buy.stamp_duty > 0
    assert sell.stamp_duty == Decimal("0.00")


def test_brokerage_never_exceeds_the_flat_cap():
    """Whichever-is-lower pricing: a huge order shouldn't produce
    brokerage above the Rs 20 flat cap."""
    costs = calculate_costs(Segment.EQUITY_DELIVERY, Side.BUY, 100000, Decimal("5000"))
    assert costs.brokerage <= Decimal("20.00")


def test_net_cash_impact_sign_matches_direction():
    buy = calculate_costs(Segment.EQUITY_DELIVERY, Side.BUY, 10, Decimal("1000"))
    sell = calculate_costs(Segment.EQUITY_DELIVERY, Side.SELL, 10, Decimal("1000"))

    assert buy.net_cash_impact < 0  # cash leaves the portfolio
    assert sell.net_cash_impact > 0  # cash enters the portfolio

    # A buy always costs strictly more than the raw price*qty (charges add on top).
    assert abs(buy.net_cash_impact) > buy.gross_value
    # A sell always nets strictly less than the raw price*qty (charges come off).
    assert sell.net_cash_impact < sell.gross_value


def test_all_components_are_decimal_and_non_negative():
    costs = calculate_costs(Segment.OPTIONS, Side.SELL, 75, Decimal("150"))
    for field in ["gross_value", "brokerage", "stt", "exchange_charges", "sebi_charges", "stamp_duty", "gst", "total_charges"]:
        value = getattr(costs, field)
        assert isinstance(value, Decimal)
        assert value >= 0


def test_rejects_non_positive_quantity_or_price():
    with pytest.raises(ValueError):
        calculate_costs(Segment.EQUITY_DELIVERY, Side.BUY, 0, Decimal("100"))
    with pytest.raises(ValueError):
        calculate_costs(Segment.EQUITY_DELIVERY, Side.BUY, 10, Decimal("0"))
