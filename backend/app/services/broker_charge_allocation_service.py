"""Deterministic, paise-exact allocation math for reviewed charge components.

This module only allocates a supplied source total over explicitly supplied
weights. Callers are responsible for establishing that the allocation basis is
authorized for the relevant charge component and preserving reviewed evidence.
It does not parse contract notes or promote live-fill accounting.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Mapping

PAISE = Decimal("0.01")
SUPPORTED_BASES = frozenset({"QUANTITY", "NOTIONAL", "EXPLICIT_REVIEWED"})
METHOD_VERSION = "largest-remainder-v1"


def _money(value: Decimal | str | int | float) -> Decimal:
    # Convert floats through str to avoid importing their binary representation.
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("Money and weights must be finite decimal values.") from exc
    if not amount.is_finite():
        raise ValueError("Money and weights must be finite decimal values.")
    return amount


def allocate_component_total(
    source_total: Decimal | str | int | float,
    weights: Mapping[str, Decimal | str | int | float],
    *,
    allocation_basis: str,
) -> dict[str, Decimal]:
    """Allocate a nonnegative source total exactly to fill IDs using largest remainder.

    Rounding ties are resolved by ascending stable fill ID. The caller must
    choose a component-appropriate, reviewed basis; this function cannot infer
    whether quantity or notional is legally/contractually appropriate.
    """
    total = _money(source_total)
    if total < 0:
        raise ValueError("Source charge total cannot be negative.")
    if total != total.quantize(PAISE):
        raise ValueError("Source charge total must be expressed to paise precision.")
    if allocation_basis not in SUPPORTED_BASES:
        raise ValueError("An explicitly supported reviewed allocation basis is required.")
    if not weights:
        raise ValueError("At least one fill weight is required.")
    if any(not isinstance(fill_id, str) or not fill_id.strip() for fill_id in weights):
        raise ValueError("Every allocation target requires a non-empty stable fill ID.")

    normalized = {fill_id: _money(weight) for fill_id, weight in weights.items()}
    if any(weight < 0 for weight in normalized.values()):
        raise ValueError("Allocation weights cannot be negative.")
    weight_sum = sum(normalized.values(), Decimal("0"))
    if weight_sum <= 0:
        raise ValueError("At least one allocation weight must be positive.")

    total_paise = int(total / PAISE)
    exact_paise = {
        fill_id: (Decimal(total_paise) * weight / weight_sum)
        for fill_id, weight in normalized.items()
    }
    base_paise = {
        fill_id: int(value.to_integral_value(rounding="ROUND_FLOOR"))
        for fill_id, value in exact_paise.items()
    }
    residual = total_paise - sum(base_paise.values())
    # Zero-weight fills are excluded from residual distribution. Otherwise a
    # zero-weight ID that sorts first could receive a paise when all positive
    # weights have tied fractional remainders.
    ranked = sorted(
        (fill_id for fill_id, weight in normalized.items() if weight > 0),
        key=lambda fill_id: (-(exact_paise[fill_id] - base_paise[fill_id]), fill_id),
    )
    for fill_id in ranked[:residual]:
        base_paise[fill_id] += 1

    result = {
        fill_id: (Decimal(paise) * PAISE).quantize(PAISE)
        for fill_id, paise in sorted(base_paise.items())
    }
    if sum(result.values(), Decimal("0")) != total:
        raise RuntimeError("Allocation arithmetic failed source-total reconciliation.")
    return result


def capped_order_brokerage_total(
    per_fill_uncapped_charges: Mapping[str, Decimal | str | int | float],
    order_cap: Decimal | str | int | float,
) -> Decimal:
    """Return the order-level brokerage total after applying a supplied cap.

    This helper performs arithmetic only. The caller must supply per-fill
    uncapped brokerage amounts calculated from the correct effective-dated
    tariff and a cap applicable to that exact order/product. It deliberately
    does not split the capped total back across fills or authorize promotion.
    """
    if not per_fill_uncapped_charges:
        raise ValueError("At least one fill charge is required.")
    if any(not isinstance(fill_id, str) or not fill_id.strip() for fill_id in per_fill_uncapped_charges):
        raise ValueError("Every fill requires a non-empty stable fill ID.")

    charges = {
        fill_id: _money(charge)
        for fill_id, charge in per_fill_uncapped_charges.items()
    }
    if any(charge < 0 for charge in charges.values()):
        raise ValueError("Uncapped brokerage charges cannot be negative.")
    if any(charge != charge.quantize(PAISE) for charge in charges.values()):
        raise ValueError("Uncapped brokerage charges must be expressed to paise precision.")

    cap = _money(order_cap)
    if cap < 0:
        raise ValueError("Order brokerage cap cannot be negative.")
    if cap != cap.quantize(PAISE):
        raise ValueError("Order brokerage cap must be expressed to paise precision.")

    uncapped_total = sum(charges.values(), Decimal("0"))
    return min(uncapped_total, cap).quantize(PAISE)


def gst_on_explicit_taxable_base(
    taxable_base: Decimal | str | int | float,
    gst_rate_percent: Decimal | str | int | float,
) -> Decimal:
    """Calculate GST on an explicitly established taxable service-charge base.

    This is arithmetic only: callers must determine the legally applicable
    taxable base and effective-dated rate from verified tariff/tax rules.
    The helper does not infer which components are taxable or authorize
    allocation of the resulting order-level amount across fills.
    """
    base = _money(taxable_base)
    rate = _money(gst_rate_percent)
    if base < 0:
        raise ValueError("GST taxable base cannot be negative.")
    if base != base.quantize(PAISE):
        raise ValueError("GST taxable base must be expressed to paise precision.")
    if rate < 0 or rate > Decimal("100"):
        raise ValueError("GST rate percent must be between 0 and 100.")
    tax = (base * rate / Decimal("100")).quantize(PAISE, rounding=ROUND_HALF_UP)
    return tax


def stamp_duty_for_explicit_buyer_side(
    transaction_value: Decimal | str | int | float,
    stamp_duty_rate_percent: Decimal | str | int | float,
    *,
    transaction_side: str,
) -> Decimal:
    """Calculate stamp duty only when the caller establishes buyer-side eligibility.

    The caller must supply the correct transaction value basis and effective-
    dated segment/product rate. This helper rejects non-buy-side transactions;
    it does not infer eligibility from order metadata or authorize fill-level
    allocation of the resulting order-level charge.
    """
    side = transaction_side.strip().upper() if isinstance(transaction_side, str) else ""
    if side != "BUY":
        raise ValueError("Stamp duty calculation requires an eligible BUY side.")
    value = _money(transaction_value)
    rate = _money(stamp_duty_rate_percent)
    if value < 0:
        raise ValueError("Stamp duty transaction value cannot be negative.")
    if value != value.quantize(PAISE):
        raise ValueError("Stamp duty transaction value must be expressed to paise precision.")
    if rate < 0 or rate > Decimal("100"):
        raise ValueError("Stamp duty rate percent must be between 0 and 100.")
    return (value * rate / Decimal("100")).quantize(PAISE, rounding=ROUND_HALF_UP)


def transaction_tax_on_explicit_base(
    taxable_value: Decimal | str | int | float,
    rate_percent: Decimal | str | int | float,
    *,
    tax_kind: str,
) -> Decimal:
    """Calculate a supplied-rate transaction tax amount without inferring tariffs.

    The caller must determine whether STT or CTT applies, the correct product,
    transaction side, value basis, exemption and effective-dated rate. This
    helper only validates and performs percentage arithmetic; it does not
    allocate order-level tax to fills or authorize accounting promotion.
    """
    kind = tax_kind.strip().upper() if isinstance(tax_kind, str) else ""
    if kind not in {"STT", "CTT"}:
        raise ValueError("Transaction tax kind must be STT or CTT.")
    value = _money(taxable_value)
    rate = _money(rate_percent)
    if value < 0:
        raise ValueError("Transaction tax value cannot be negative.")
    if value != value.quantize(PAISE):
        raise ValueError("Transaction tax value must be expressed to paise precision.")
    if rate < 0 or rate > Decimal("100"):
        raise ValueError("Transaction tax rate percent must be between 0 and 100.")
    return (value * rate / Decimal("100")).quantize(PAISE, rounding=ROUND_HALF_UP)
