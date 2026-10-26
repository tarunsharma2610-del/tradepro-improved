"""Deterministic paise-exact total-charge calculation for persisted executions.

A missing DP/demat amount remains NULL and contributes nothing to the total;
callers must not use NULL as evidence that the charge was zero. Actual source
reconciliation remains a separate reviewed workflow.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

PAISE = Decimal("0.01")
CORE_CHARGE_FIELDS = (
    "brokerage",
    "stt",
    "exchange_charges",
    "sebi_charges",
    "stamp_duty",
    "gst",
)


def _amount(field: str, value: Any, *, optional: bool = False) -> Decimal | None:
    if value is None and optional:
        return None
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Execution charge {field} must be a finite nonnegative INR amount.") from exc
    if not amount.is_finite() or amount < 0 or amount != amount.quantize(PAISE, rounding=ROUND_HALF_UP):
        raise ValueError(f"Execution charge {field} must be a finite nonnegative INR amount in paise.")
    return amount


def calculate_execution_total_charges(
    *,
    brokerage: Any,
    stt: Any,
    exchange_charges: Any,
    sebi_charges: Any,
    stamp_duty: Any,
    gst: Any,
    demat_transaction_charges: Any = None,
) -> Decimal:
    """Sum six core components plus DP/demat only when its amount is explicit."""
    values = {
        "brokerage": brokerage,
        "stt": stt,
        "exchange_charges": exchange_charges,
        "sebi_charges": sebi_charges,
        "stamp_duty": stamp_duty,
        "gst": gst,
    }
    parsed = [_amount(name, value) for name, value in values.items()]
    demat = _amount("demat_transaction_charges", demat_transaction_charges, optional=True)
    total = sum((value for value in parsed if value is not None), Decimal("0.00"))
    if demat is not None:
        total += demat
    return total.quantize(PAISE, rounding=ROUND_HALF_UP)


def recompute_execution_total_charges(execution: Any) -> Decimal:
    """Recompute and assign Execution.total_charges from persisted component fields."""
    total = calculate_execution_total_charges(
        brokerage=execution.brokerage,
        stt=execution.stt,
        exchange_charges=execution.exchange_charges,
        sebi_charges=execution.sebi_charges,
        stamp_duty=execution.stamp_duty,
        gst=execution.gst,
        demat_transaction_charges=execution.demat_transaction_charges,
    )
    execution.total_charges = total
    return total
