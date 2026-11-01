from decimal import Decimal

import pytest

from app.services.position_math import apply_fill
from app.services.transaction_costs import Side


def test_opening_a_long_position():
    result = apply_fill(position_quantity=0, position_avg_price=Decimal("0"), side=Side.BUY, fill_quantity=10, fill_price=Decimal("100"))
    assert result.new_quantity == 10
    assert result.new_avg_price == Decimal("100")
    assert result.realized_pnl == Decimal("0.00")


def test_adding_to_a_long_position_updates_weighted_average():
    # Already long 10 @ 100, buy 10 more @ 120 -> avg should be 110
    result = apply_fill(position_quantity=10, position_avg_price=Decimal("100"), side=Side.BUY, fill_quantity=10, fill_price=Decimal("120"))
    assert result.new_quantity == 20
    assert result.new_avg_price == Decimal("110")
    assert result.realized_pnl == Decimal("0.00")


def test_partial_close_of_long_realizes_proportional_pnl_and_keeps_avg_price():
    # Long 20 @ 100, sell 5 @ 130 -> realize (130-100)*5 = 150 profit, 15 left @ 100
    result = apply_fill(position_quantity=20, position_avg_price=Decimal("100"), side=Side.SELL, fill_quantity=5, fill_price=Decimal("130"))
    assert result.new_quantity == 15
    assert result.new_avg_price == Decimal("100")
    assert result.realized_pnl == Decimal("150.00")


def test_full_close_of_long_realizes_all_pnl_and_zeroes_out():
    result = apply_fill(position_quantity=10, position_avg_price=Decimal("100"), side=Side.SELL, fill_quantity=10, fill_price=Decimal("90"))
    assert result.new_quantity == 0
    assert result.new_avg_price == Decimal("0")
    assert result.realized_pnl == Decimal("-100.00")  # loss: (90-100)*10


def test_sell_larger_than_long_position_flips_to_short():
    # Long 10 @ 100, sell 15 @ 105 -> closes the 10 (realize (105-100)*10=50),
    # remaining 5 becomes a fresh short opened at the fill price.
    result = apply_fill(position_quantity=10, position_avg_price=Decimal("100"), side=Side.SELL, fill_quantity=15, fill_price=Decimal("105"))
    assert result.new_quantity == -5
    assert result.new_avg_price == Decimal("105")
    assert result.realized_pnl == Decimal("50.00")


def test_opening_a_short_position():
    result = apply_fill(position_quantity=0, position_avg_price=Decimal("0"), side=Side.SELL, fill_quantity=10, fill_price=Decimal("200"))
    assert result.new_quantity == -10
    assert result.new_avg_price == Decimal("200")
    assert result.realized_pnl == Decimal("0.00")


def test_covering_a_short_realizes_profit_when_price_fell():
    # Short 10 @ 200, buy 10 @ 180 to cover -> profit (200-180)*10 = 200
    result = apply_fill(position_quantity=-10, position_avg_price=Decimal("200"), side=Side.BUY, fill_quantity=10, fill_price=Decimal("180"))
    assert result.new_quantity == 0
    assert result.realized_pnl == Decimal("200.00")


def test_covering_a_short_realizes_loss_when_price_rose():
    result = apply_fill(position_quantity=-10, position_avg_price=Decimal("200"), side=Side.BUY, fill_quantity=10, fill_price=Decimal("220"))
    assert result.realized_pnl == Decimal("-200.00")


def test_buy_larger_than_short_flips_to_long():
    result = apply_fill(position_quantity=-5, position_avg_price=Decimal("200"), side=Side.BUY, fill_quantity=8, fill_price=Decimal("190"))
    assert result.new_quantity == 3
    assert result.new_avg_price == Decimal("190")
    assert result.realized_pnl == Decimal("50.00")  # (200-190)*5 covering the short



def test_trailing_stop_seeds_and_ratchets_long_watermark_without_trigger():
    from app.services.position_math import check_trailing_stop

    watermark, hit = check_trailing_stop(
        watermark=None,
        position_quantity=10,
        current_price=Decimal("100"),
        stop_pct=Decimal("5"),
    )
    assert watermark == Decimal("100")
    assert hit is False

    watermark, hit = check_trailing_stop(
        watermark=watermark,
        position_quantity=10,
        current_price=Decimal("110"),
        stop_pct=Decimal("5"),
    )
    assert watermark == Decimal("110")
    assert hit is False

    # A lower price does not lower a long trailing watermark.
    watermark, hit = check_trailing_stop(
        watermark=watermark,
        position_quantity=10,
        current_price=Decimal("106"),
        stop_pct=Decimal("5"),
    )
    assert watermark == Decimal("110")
    assert hit is False


def test_trailing_stop_triggers_long_at_or_below_ratchet_threshold():
    from app.services.position_math import check_trailing_stop

    watermark, hit = check_trailing_stop(
        watermark=Decimal("110"),
        position_quantity=10,
        current_price=Decimal("104.50"),
        stop_pct=Decimal("5"),
    )
    assert watermark == Decimal("110")
    assert hit is True


def test_trailing_stop_seeds_and_ratchets_short_watermark_without_trigger():
    from app.services.position_math import check_trailing_stop

    watermark, hit = check_trailing_stop(
        watermark=None,
        position_quantity=-10,
        current_price=Decimal("200"),
        stop_pct=Decimal("5"),
    )
    assert watermark == Decimal("200")
    assert hit is False

    watermark, hit = check_trailing_stop(
        watermark=watermark,
        position_quantity=-10,
        current_price=Decimal("180"),
        stop_pct=Decimal("5"),
    )
    assert watermark == Decimal("180")
    assert hit is False

    # A higher price does not raise a short trailing watermark.
    watermark, hit = check_trailing_stop(
        watermark=watermark,
        position_quantity=-10,
        current_price=Decimal("185"),
        stop_pct=Decimal("5"),
    )
    assert watermark == Decimal("180")
    assert hit is False


def test_trailing_stop_triggers_short_at_or_above_ratchet_threshold():
    from app.services.position_math import check_trailing_stop

    watermark, hit = check_trailing_stop(
        watermark=Decimal("180"),
        position_quantity=-10,
        current_price=Decimal("189"),
        stop_pct=Decimal("5"),
    )
    assert watermark == Decimal("180")
    assert hit is True


@pytest.mark.parametrize(
    "kwargs",
    [
        {"position_quantity": 0, "current_price": Decimal("100"), "stop_pct": Decimal("5")},
        {"position_quantity": 10, "current_price": Decimal("0"), "stop_pct": Decimal("5")},
        {"position_quantity": 10, "current_price": Decimal("100"), "stop_pct": Decimal("0")},
        {"position_quantity": 10, "current_price": Decimal("100"), "stop_pct": Decimal("-1")},
        {"position_quantity": 10, "current_price": Decimal("100"), "stop_pct": Decimal("51")},
        {"position_quantity": 10, "current_price": Decimal("NaN"), "stop_pct": Decimal("5")},
    ],
)
def test_trailing_stop_rejects_invalid_inputs(kwargs):
    from app.services.position_math import check_trailing_stop

    with pytest.raises(ValueError):
        check_trailing_stop(watermark=None, **kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"position_quantity": True, "position_avg_price": Decimal("0"), "side": Side.BUY, "fill_quantity": 1, "fill_price": Decimal("10")},
        {"position_quantity": 0, "position_avg_price": Decimal("0"), "side": Side.BUY, "fill_quantity": 0, "fill_price": Decimal("10")},
        {"position_quantity": 0, "position_avg_price": Decimal("0"), "side": Side.BUY, "fill_quantity": -1, "fill_price": Decimal("10")},
        {"position_quantity": 0, "position_avg_price": Decimal("0"), "side": Side.BUY, "fill_quantity": True, "fill_price": Decimal("10")},
        {"position_quantity": 0, "position_avg_price": Decimal("0"), "side": "BUY", "fill_quantity": 1, "fill_price": Decimal("10")},
        {"position_quantity": 0, "position_avg_price": Decimal("0"), "side": Side.BUY, "fill_quantity": 1, "fill_price": Decimal("0")},
        {"position_quantity": 0, "position_avg_price": Decimal("0"), "side": Side.BUY, "fill_quantity": 1, "fill_price": Decimal("NaN")},
        {"position_quantity": 0, "position_avg_price": Decimal("NaN"), "side": Side.BUY, "fill_quantity": 1, "fill_price": Decimal("10")},
        {"position_quantity": 3, "position_avg_price": Decimal("0"), "side": Side.SELL, "fill_quantity": 1, "fill_price": Decimal("10")},
        {"position_quantity": 0, "position_avg_price": Decimal("1"), "side": Side.BUY, "fill_quantity": 1, "fill_price": Decimal("10")},
    ],
)
def test_apply_fill_rejects_invalid_position_and_fill_inputs(kwargs):
    with pytest.raises(ValueError):
        apply_fill(**kwargs)


@pytest.mark.parametrize(
    "fills,expected_quantity,expected_average,expected_realized",
    [
        (
            [(Side.BUY, 10, "100"), (Side.BUY, 5, "130"), (Side.SELL, 8, "140"), (Side.SELL, 7, "90")],
            0, "0", "205.00",
        ),
        (
            [(Side.SELL, 10, "200"), (Side.SELL, 5, "180"), (Side.BUY, 8, "170"), (Side.BUY, 7, "210")],
            0, "0", "205.00",
        ),
        (
            [(Side.BUY, 4, "100"), (Side.SELL, 7, "120"), (Side.BUY, 2, "110")],
            -1, "120", "80.00",
        ),
        (
            [(Side.SELL, 4, "100"), (Side.BUY, 7, "80"), (Side.SELL, 2, "90")],
            1, "90", "80.00",
        ),
    ],
)
def test_sequential_partial_fills_and_reversals_preserve_position_accounting_invariants(
    fills, expected_quantity, expected_average, expected_realized
):
    quantity = 0
    average = Decimal("0")
    cumulative_realized = Decimal("0")

    for side, fill_quantity, fill_price in fills:
        update = apply_fill(
            position_quantity=quantity,
            position_avg_price=average,
            side=side,
            fill_quantity=fill_quantity,
            fill_price=Decimal(fill_price),
        )
        quantity = update.new_quantity
        average = update.new_avg_price
        cumulative_realized += update.realized_pnl

        if quantity == 0:
            assert average == Decimal("0")
        else:
            assert average > 0
        assert update.realized_pnl == update.realized_pnl.quantize(Decimal("0.01"))

    assert quantity == expected_quantity
    assert average == Decimal(expected_average)
    assert cumulative_realized == Decimal(expected_realized)


def test_opening_and_adding_fills_do_not_realize_pnl_until_position_is_reduced():
    first = apply_fill(
        position_quantity=0, position_avg_price=Decimal("0"),
        side=Side.BUY, fill_quantity=3, fill_price=Decimal("100"),
    )
    second = apply_fill(
        position_quantity=first.new_quantity, position_avg_price=first.new_avg_price,
        side=Side.BUY, fill_quantity=2, fill_price=Decimal("110"),
    )
    assert first.realized_pnl == Decimal("0.00")
    assert second.realized_pnl == Decimal("0.00")
    assert second.new_quantity == 5
    assert second.new_avg_price == Decimal("104")
