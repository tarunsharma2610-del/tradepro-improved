from decimal import Decimal

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
