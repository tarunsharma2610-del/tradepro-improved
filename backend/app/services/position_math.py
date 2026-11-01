"""
Pure position-update logic, deliberately kept separate from any DB code so
it's trivial to unit-test every scenario: opening, adding, partial close,
full close, and flipping from long to short (or short to long) in a single
fill. `quantity` is signed throughout: positive = long, negative = short.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.services.transaction_costs import Side

TWO_DP = Decimal("0.01")


@dataclass
class PositionUpdate:
    new_quantity: int
    new_avg_price: Decimal
    realized_pnl: Decimal  # attributable to this fill only


def check_trailing_stop(
    *, watermark: Decimal | None, position_quantity: int, current_price: Decimal, stop_pct: Decimal
) -> tuple[Decimal, bool]:
    """Pure trailing-stop check, shared by live strategy execution
    (strategy_execution_service.py) and backtesting (backtest_engine.py) —
    exactly the kind of logic the architecture rules require to NOT be
    reimplemented per-context. Returns (new_watermark, stop_hit).

    watermark=None means no watermark yet (e.g., right after entry) —
    current_price seeds it."""
    if isinstance(position_quantity, bool) or not isinstance(position_quantity, int) or position_quantity == 0:
        raise ValueError("Trailing stop requires a non-zero integer position quantity.")
    if not current_price.is_finite() or current_price <= 0:
        raise ValueError("Trailing-stop price must be finite and positive.")
    if watermark is not None and (not watermark.is_finite() or watermark <= 0):
        raise ValueError("Trailing-stop watermark must be finite and positive.")
    if not stop_pct.is_finite() or not Decimal("0") < stop_pct <= Decimal("50"):
        raise ValueError("Trailing-stop percentage must be greater than 0 and at most 50.")

    effective_watermark = watermark if watermark is not None else current_price
    stop_fraction = stop_pct / Decimal("100")

    if position_quantity > 0:  # long: watermark tracks the high, stop sits below it
        new_watermark = max(effective_watermark, current_price)
        stop_price = new_watermark * (1 - stop_fraction)
        hit = current_price <= stop_price
    else:  # short: watermark tracks the low, stop sits above it
        new_watermark = min(effective_watermark, current_price)
        stop_price = new_watermark * (1 + stop_fraction)
        hit = current_price >= stop_price

    return new_watermark, hit


def apply_fill(
    *, position_quantity: int, position_avg_price: Decimal, side: Side, fill_quantity: int, fill_price: Decimal
) -> PositionUpdate:
    """Apply one positive-price, positive-quantity fill to a signed position.

    Reject malformed inputs before arithmetic so invalid broker or caller data
    cannot silently create a nonsensical position or realized-P&L value.
    """
    if isinstance(position_quantity, bool) or not isinstance(position_quantity, int):
        raise ValueError("Position quantity must be an integer.")
    if isinstance(fill_quantity, bool) or not isinstance(fill_quantity, int) or fill_quantity <= 0:
        raise ValueError("Fill quantity must be a positive integer.")
    if not isinstance(side, Side):
        raise ValueError("Fill side must be a valid Side.")
    if not isinstance(position_avg_price, Decimal) or not position_avg_price.is_finite():
        raise ValueError("Position average price must be a finite Decimal.")
    if not isinstance(fill_price, Decimal) or not fill_price.is_finite() or fill_price <= 0:
        raise ValueError("Fill price must be a finite positive Decimal.")
    if position_quantity == 0:
        if position_avg_price != 0:
            raise ValueError("A flat position must have a zero average price.")
    elif position_avg_price <= 0:
        raise ValueError("An open position must have a positive average price.")

    signed_fill = fill_quantity if side == Side.BUY else -fill_quantity
    new_quantity = position_quantity + signed_fill

    same_direction_or_flat = position_quantity == 0 or (position_quantity > 0) == (signed_fill > 0)

    if same_direction_or_flat:
        # Opening or adding to a position in the same direction: no P&L
        # realized yet, just a new weighted-average entry price.
        total_cost = (abs(position_quantity) * position_avg_price) + (fill_quantity * fill_price)
        new_avg_price = (total_cost / abs(new_quantity)) if new_quantity != 0 else Decimal("0")
        return PositionUpdate(new_quantity=new_quantity, new_avg_price=new_avg_price, realized_pnl=Decimal("0.00"))

    # Opposite direction: this fill closes some or all of the existing
    # position (and may flip past zero into the opposite direction).
    closing_quantity = min(fill_quantity, abs(position_quantity))
    if position_quantity > 0:
        # Was long, now selling: profit if fill price > entry price.
        pnl = (fill_price - position_avg_price) * closing_quantity
    else:
        # Was short, now buying to cover: profit if entry price > fill price.
        pnl = (position_avg_price - fill_price) * closing_quantity
    realized_pnl = pnl.quantize(TWO_DP, rounding=ROUND_HALF_UP)

    if new_quantity == 0:
        return PositionUpdate(new_quantity=0, new_avg_price=Decimal("0"), realized_pnl=realized_pnl)

    flipped = (position_quantity > 0) != (new_quantity > 0)
    if flipped:
        # The fill was bigger than the old position: it's now a fresh
        # position in the other direction, opened at the fill price.
        return PositionUpdate(new_quantity=new_quantity, new_avg_price=fill_price, realized_pnl=realized_pnl)

    # Partial close: direction unchanged, remaining quantity keeps the
    # original average price (only the closed portion realizes P&L).
    return PositionUpdate(new_quantity=new_quantity, new_avg_price=position_avg_price, realized_pnl=realized_pnl)
