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
