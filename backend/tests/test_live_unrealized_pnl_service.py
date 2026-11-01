from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.services.live_unrealized_pnl_service import calculate_live_unrealized_pnl


NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


def calculate(**overrides):
    values = {
        "quantity": 10,
        "average_price": Decimal("100"),
        "last_price": Decimal("110"),
        "quote_received_at": NOW - timedelta(seconds=2),
        "now": NOW,
        "max_quote_age_seconds": 15,
    }
    values.update(overrides)
    return calculate_live_unrealized_pnl(**values)


def test_long_position_unrealized_profit():
    result = calculate()
    assert result.unrealized_pnl == Decimal("100.00")
    assert result.quantity == 10
    assert result.quote_age_seconds == Decimal("2.0")


def test_long_position_unrealized_loss():
    assert calculate(last_price=Decimal("90")).unrealized_pnl == Decimal("-100.00")


def test_short_position_profit_and_loss_signs():
    profit = calculate(quantity=-10, last_price=Decimal("90"))
    loss = calculate(quantity=-10, last_price=Decimal("110"))
    assert profit.unrealized_pnl == Decimal("100.00")
    assert loss.unrealized_pnl == Decimal("-100.00")


def test_flat_position_returns_zero_only_with_zero_average_and_fresh_quote():
    result = calculate(quantity=0, average_price=Decimal("0"))
    assert result.unrealized_pnl == Decimal("0.00")


@pytest.mark.parametrize(
    "age",
    [timedelta(seconds=16), timedelta(seconds=-1)],
)
def test_stale_or_future_quote_fails_closed(age):
    with pytest.raises(ValueError, match="stale or future-dated"):
        calculate(quote_received_at=NOW - age)


@pytest.mark.parametrize(
    "overrides",
    [
        {"quantity": True},
        {"average_price": Decimal("NaN")},
        {"average_price": Decimal("0")},
        {"last_price": Decimal("0")},
        {"last_price": Decimal("Infinity")},
        {"quantity": 0, "average_price": Decimal("1")},
        {"max_quote_age_seconds": 0},
        {"quote_received_at": datetime(2026, 11, 1, 12, 0)},
        {"now": datetime(2026, 11, 1, 12, 0)},
    ],
)
def test_invalid_inputs_are_rejected(overrides):
    with pytest.raises(ValueError):
        calculate(**overrides)


def test_rounds_to_paise_using_half_up():
    result = calculate(quantity=1, average_price=Decimal("1"), last_price=Decimal("1.005"))
    assert result.unrealized_pnl == Decimal("0.01")
