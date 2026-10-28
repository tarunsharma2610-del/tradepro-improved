"""API-first paper-trade charges with the existing deterministic calculator as fallback.

The Upstox brokerage endpoint is an estimate, not booked accounting evidence.
Only a complete, internally consistent component breakdown is accepted. Missing,
null, invalid, unsupported, or inconsistent API fields fall back to calculate_costs.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from app.brokers.upstox.reconciliation_client import UpstoxReadOnlyReconciliationClient
from app.services.transaction_costs import CostBreakdown, Segment, Side, calculate_costs

PAISE = Decimal("0.01")


@dataclass(frozen=True)
class PaperTradeChargeEstimate:
    costs: CostBreakdown
    source: str
    fallback_reason: str | None = None


def _money(value: Any, field: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field} is missing or invalid")
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field} is missing or invalid") from exc
    if not amount.is_finite() or amount < 0 or amount != amount.quantize(PAISE):
        raise ValueError(f"{field} must be a nonnegative finite paise amount")
    return amount


def _parse_api_costs(payload: Any, *, segment: Segment, side: Side, quantity: int, price: Decimal) -> CostBreakdown:
    if not isinstance(payload, dict):
        raise ValueError("API response is not an object")
    data = payload.get("data")
    charges = data.get("charges") if isinstance(data, dict) else None
    if not isinstance(charges, dict):
        raise ValueError("API charge breakdown is missing")
    taxes = charges.get("taxes")
    other = charges.get("other_charges")
    if other is None:
        other = charges.get("otherTaxes")
    if not isinstance(taxes, dict) or not isinstance(other, dict):
        raise ValueError("API tax or other-charge breakdown is missing")

    brokerage = _money(charges.get("brokerage"), "brokerage")
    gst = _money(taxes.get("gst"), "gst")
    stt = _money(taxes.get("stt"), "stt")
    stamp_duty = _money(taxes.get("stamp_duty"), "stamp_duty")
    transaction = _money(other.get("transaction"), "transaction")
    clearing = _money(other.get("clearing"), "clearing")
    ipft = _money(other.get("ipft"), "ipft")
    sebi = _money(other.get("sebi_turnover"), "sebi_turnover")
    total = _money(charges.get("total"), "total")

    # The current CostBreakdown stores exchange transaction, clearing and IPFT
    # together. Do not accept an unexplained "others" amount or a total that
    # cannot be reconciled exactly to the represented components.
    if other.get("others") not in (None, 0, 0.0, "0", "0.00"):
        raise ValueError("API returned an unmodelled other-charge component")
    exchange_charges = transaction + clearing + ipft
    component_total = brokerage + gst + stt + stamp_duty + exchange_charges + sebi
    if component_total != total:
        raise ValueError("API total does not equal the supported component sum")

    gross_value = (price * Decimal(quantity)).quantize(PAISE, rounding=ROUND_HALF_UP)
    return CostBreakdown(
        gross_value=gross_value,
        brokerage=brokerage,
        stt=stt,
        exchange_charges=exchange_charges,
        sebi_charges=sebi,
        stamp_duty=stamp_duty,
        gst=gst,
        total_charges=total,
        side=Side(side),
    )


async def estimate_paper_trade_costs(
    access_token: str | None,
    *,
    instrument_token: str,
    quantity: int,
    segment: Segment,
    side: Side,
    price: Decimal,
    trade_date: date,
    client: UpstoxReadOnlyReconciliationClient | None = None,
) -> PaperTradeChargeEstimate:
    """Prefer a complete Upstox pre-trade estimate; otherwise use local rates."""
    fallback = calculate_costs(segment, side, quantity, price)
    if not access_token:
        return PaperTradeChargeEstimate(fallback, "HARDCODED_FALLBACK", "missing_access_token")

    product = "D" if segment == Segment.EQUITY_DELIVERY else "I"
    try:
        api = client or UpstoxReadOnlyReconciliationClient()
        result = await api.get_brokerage_estimate(
            access_token,
            instrument_token=instrument_token,
            quantity=quantity,
            product=product,
            transaction_type=Side(side).value,
            price=price,
        )
        if not result.ok:
            return PaperTradeChargeEstimate(fallback, "HARDCODED_FALLBACK", result.error_code or "api_unavailable")
        costs = _parse_api_costs(
            result.data, segment=segment, side=side, quantity=quantity, price=price
        )
        return PaperTradeChargeEstimate(costs, "UPSTOX_API_ESTIMATE")
    except (ValueError, TypeError, InvalidOperation, KeyError) as exc:
        return PaperTradeChargeEstimate(fallback, "HARDCODED_FALLBACK", str(exc))
    except Exception:
        # A transient HTTP/client failure must never prevent paper trading.
        return PaperTradeChargeEstimate(fallback, "HARDCODED_FALLBACK", "api_error")
