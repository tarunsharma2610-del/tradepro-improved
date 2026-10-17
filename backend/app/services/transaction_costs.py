"""
Every rate here was checked against multiple current sources in August
2026, not pulled from training-data memory — F&O STT specifically was
raised again by Budget 2026, effective 1 April 2026, so a pre-2026 figure
would have been wrong. That said, these are exactly the kind of numbers
that change on a government/exchange schedule outside anyone's control:
treat this file as the one place to update when they do, and recheck it
periodically rather than assuming it stays correct indefinitely.

Sources (as of Aug 2026):
- STT: multiple broker/tax sources corroborating the Budget 2026 F&O hike
  (futures 0.02%→0.05%, options premium 0.10%→0.15%), effective 1 Apr 2026.
  Equity delivery/intraday STT unchanged.
- Exchange transaction charges: NSE revised its schedule effective
  1 Mar 2026 (NSE circular). Absolute per-segment rates below are indicative
  midpoints from post-revision secondary sources, NOT the primary circular's
  own rate table — verify against the live NSE/BSE fee schedule before this
  number matters for anything beyond an approximate simulation.
- SEBI turnover fee: Rs 10/crore (0.0001%), now GST-inclusive-eligible per
  an April 2025 change — well corroborated, low uncertainty.
- Stamp duty: standardized nationally since the 2020 reform; buy-side only.
- Upstox brokerage: sources disagreed specifically on whether equity
  delivery is free or a capped percentage — this file assumes the capped
  version (more conservative for P&L realism); confirm against Upstox's own
  live brokerage calculator before this feeds anything beyond simulation.
"""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum


class Segment(str, Enum):
    EQUITY_DELIVERY = "EQUITY_DELIVERY"
    EQUITY_INTRADAY = "EQUITY_INTRADAY"
    FUTURES = "FUTURES"
    OPTIONS = "OPTIONS"


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


TWO_DP = Decimal("0.01")


def _round(value: Decimal) -> Decimal:
    return value.quantize(TWO_DP, rounding=ROUND_HALF_UP)


# --- STT: percentage of turnover (equity, futures) or premium value (options) ---
_STT_RATE = {
    Segment.EQUITY_DELIVERY: {"BUY": Decimal("0.001"), "SELL": Decimal("0.001")},
    Segment.EQUITY_INTRADAY: {"BUY": Decimal("0"), "SELL": Decimal("0.00025")},
    Segment.FUTURES: {"BUY": Decimal("0"), "SELL": Decimal("0.0005")},  # raised from 0.0002, effective 1 Apr 2026
    Segment.OPTIONS: {"BUY": Decimal("0"), "SELL": Decimal("0.0015")},  # raised from 0.001, effective 1 Apr 2026
}

# --- Exchange transaction charges: percentage of turnover, both sides ---
_EXCHANGE_RATE = {
    Segment.EQUITY_DELIVERY: Decimal("0.0000316"),
    Segment.EQUITY_INTRADAY: Decimal("0.0000316"),
    Segment.FUTURES: Decimal("0.000018"),
    Segment.OPTIONS: Decimal("0.0004"),  # of premium value
}

_SEBI_RATE = Decimal("0.000001")  # Rs 10/crore, both sides, all segments

# --- Stamp duty: percentage of turnover, BUY side only ---
_STAMP_DUTY_RATE = {
    Segment.EQUITY_DELIVERY: Decimal("0.00015"),
    Segment.EQUITY_INTRADAY: Decimal("0.00003"),
    Segment.FUTURES: Decimal("0.00002"),
    Segment.OPTIONS: Decimal("0.00003"),
}

_GST_RATE = Decimal("0.18")  # on (brokerage + exchange charges + SEBI charges) only — not on STT or stamp duty


def _upstox_brokerage(segment: Segment, turnover: Decimal) -> Decimal:
    """Flat Rs 20 or a percentage cap, whichever is lower — see the module
    docstring re: delivery-brokerage source disagreement."""
    flat = Decimal("20")
    if segment == Segment.EQUITY_DELIVERY:
        return min(flat, turnover * Decimal("0.025"))
    if segment == Segment.EQUITY_INTRADAY:
        return min(flat, turnover * Decimal("0.0003"))
    return flat  # FUTURES, OPTIONS: flat per executed order


@dataclass
class CostBreakdown:
    gross_value: Decimal  # always positive: price * quantity
    brokerage: Decimal
    stt: Decimal
    exchange_charges: Decimal
    sebi_charges: Decimal
    stamp_duty: Decimal
    gst: Decimal
    total_charges: Decimal  # always positive: sum of the six components above
    side: Side

    @property
    def net_cash_impact(self) -> Decimal:
        """Signed effect on portfolio cash_balance: negative for a BUY
        (cash goes out, more than the raw price*qty because of charges),
        positive for a SELL (proceeds in, less than raw price*qty). This
        is the one number ExecutionService actually adds to cash_balance."""
        if self.side == Side.BUY:
            return -(self.gross_value + self.total_charges)
        return self.gross_value - self.total_charges


def calculate_costs(segment: Segment, side: Side, quantity: int, price: Decimal) -> CostBreakdown:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    if price <= 0:
        raise ValueError("price must be positive")

    side = Side(side)
    turnover = price * Decimal(quantity)

    brokerage = _round(_upstox_brokerage(segment, turnover))
    stt = _round(turnover * _STT_RATE[segment][side.value])
    exchange_charges = _round(turnover * _EXCHANGE_RATE[segment])
    sebi_charges = _round(turnover * _SEBI_RATE)
    stamp_duty = _round(turnover * _STAMP_DUTY_RATE[segment]) if side == Side.BUY else Decimal("0.00")
    gst = _round((brokerage + exchange_charges + sebi_charges) * _GST_RATE)
    total_charges = brokerage + stt + exchange_charges + sebi_charges + stamp_duty + gst

    return CostBreakdown(
        gross_value=_round(turnover),
        brokerage=brokerage,
        stt=stt,
        exchange_charges=exchange_charges,
        sebi_charges=sebi_charges,
        stamp_duty=stamp_duty,
        gst=gst,
        total_charges=total_charges,
        side=side,
    )
