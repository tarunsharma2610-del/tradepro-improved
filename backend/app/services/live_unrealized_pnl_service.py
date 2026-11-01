"""Fail-closed LIVE unrealized P&L calculation from a fresh validated quote.

This module is pure accounting logic. Redis snapshot validation remains the
responsibility of RedisMarketQuoteConsumer; this layer independently checks
the quote timestamp before calculating displayable P&L.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP


CENT = Decimal("0.01")


@dataclass(frozen=True)
class UnrealizedPnLResult:
    quantity: int
    average_price: Decimal
    last_price: Decimal
    unrealized_pnl: Decimal
    quote_age_seconds: Decimal


def calculate_live_unrealized_pnl(
    *,
    quantity: int,
    average_price: Decimal,
    last_price: Decimal,
    quote_received_at: datetime,
    now: datetime,
    max_quote_age_seconds: int = 15,
) -> UnrealizedPnLResult:
    """Calculate signed-position P&L only when its quote is demonstrably fresh.

    Positive quantity is long, negative quantity is short. Missing, stale,
    future-dated, malformed or non-finite inputs raise ValueError so callers
    cannot silently substitute a stale price or display a fabricated zero.
    """
    if isinstance(quantity, bool) or not isinstance(quantity, int):
        raise ValueError("LIVE position quantity must be an integer.")
    if not isinstance(average_price, Decimal) or not average_price.is_finite():
        raise ValueError("LIVE average price must be a finite Decimal.")
    if not isinstance(last_price, Decimal) or not last_price.is_finite() or last_price <= 0:
        raise ValueError("LIVE market price must be a finite positive Decimal.")
    if quantity == 0:
        if average_price != 0:
            raise ValueError("A flat LIVE position must have zero average price.")
    elif average_price <= 0:
        raise ValueError("An open LIVE position must have a positive average price.")
    if isinstance(max_quote_age_seconds, bool) or not isinstance(max_quote_age_seconds, int) or max_quote_age_seconds <= 0:
        raise ValueError("Maximum quote age must be a positive integer.")
    if not isinstance(quote_received_at, datetime) or not isinstance(now, datetime):
        raise ValueError("Quote and evaluation timestamps are required.")
    if quote_received_at.tzinfo is None or quote_received_at.utcoffset() is None:
        raise ValueError("Quote timestamp must be timezone-aware.")
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Evaluation timestamp must be timezone-aware.")

    age = Decimal(str((now.astimezone(timezone.utc) - quote_received_at.astimezone(timezone.utc)).total_seconds()))
    if age < 0 or age > Decimal(max_quote_age_seconds):
        raise ValueError("LIVE market quote is stale or future-dated; unrealized P&L is unavailable.")

    pnl = (last_price - average_price) * quantity
    return UnrealizedPnLResult(
        quantity=quantity,
        average_price=average_price,
        last_price=last_price,
        unrealized_pnl=pnl.quantize(CENT, rounding=ROUND_HALF_UP),
        quote_age_seconds=age,
    )
