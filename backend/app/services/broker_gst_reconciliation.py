"""Compare broker-reported GST estimates with the independent statutory GST estimate.

This is a comparison/reporting primitive only: it does not promote estimate
values into booked per-fill accounting or declare an invoice legally correct.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable, Any

from app.services.broker_charge_api_normalization import normalize_charge_api_field
from app.services.statutory_stock_broking_gst import (
    GstValuationLine,
    calculate_statutory_stock_broking_gst,
)

PAISE = Decimal("0.01")


@dataclass(frozen=True)
class GstEstimateComparison:
    api_state: str
    api_reported_gst: Decimal | None
    engine_estimated_gst: Decimal
    variance_api_minus_engine: Decimal | None
    status: str
    taxable_base: Decimal
    tax_type: str
    engine_valuation_basis: str = "CGST_ACT_SECTION_15_AND_RULE_33"
    evidence_class: str = "ESTIMATE_COMPARISON"


def compare_broker_gst_estimate(
    payload: dict[str, Any],
    *,
    gst_field: str,
    valuation_lines: Iterable[GstValuationLine],
    supplier_state_code: str,
    recipient_state_code_in_supplier_records: str | None,
    tolerance: Decimal | str = Decimal("0.01"),
) -> GstEstimateComparison:
    """Compare an API GST estimate with a separately calculated GST estimate.

    Missing/null/invalid API fields remain unavailable; numeric zero remains a
    real reported value. A variance is surfaced, never silently reconciled.
    """
    normalized = normalize_charge_api_field(payload, gst_field)
    try:
        allowed_tolerance = tolerance if isinstance(tolerance, Decimal) else Decimal(str(tolerance))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("GST comparison tolerance must be a finite nonnegative amount.") from exc
    if not allowed_tolerance.is_finite() or allowed_tolerance < 0:
        raise ValueError("GST comparison tolerance must be a finite nonnegative amount.")
    if allowed_tolerance != allowed_tolerance.quantize(PAISE):
        raise ValueError("GST comparison tolerance must be expressed to paise precision.")

    engine = calculate_statutory_stock_broking_gst(
        valuation_lines,
        supplier_state_code=supplier_state_code,
        recipient_state_code_in_supplier_records=recipient_state_code_in_supplier_records,
    )
    state = normalized["state"]
    if state in {"MISSING", "NULL", "INVALID"}:
        return GstEstimateComparison(
            api_state=state,
            api_reported_gst=None,
            engine_estimated_gst=engine.total_gst,
            variance_api_minus_engine=None,
            status="API_GST_UNAVAILABLE_REVIEW",
            taxable_base=engine.taxable_base,
            tax_type=engine.tax_type,
        )

    api_amount = Decimal(normalized["decimal_value"])
    if api_amount != api_amount.quantize(PAISE):
        return GstEstimateComparison(
            api_state="INVALID",
            api_reported_gst=None,
            engine_estimated_gst=engine.total_gst,
            variance_api_minus_engine=None,
            status="API_GST_INVALID_REVIEW",
            taxable_base=engine.taxable_base,
            tax_type=engine.tax_type,
        )
    variance = (api_amount - engine.total_gst).quantize(PAISE, rounding=ROUND_HALF_UP)
    status = ("MATCH_EXACT" if variance == Decimal("0.00") else "ROUNDING_VARIANCE_REQUIRES_REVIEW" if abs(variance) <= allowed_tolerance else "VARIANCE_REQUIRES_REVIEW")
    return GstEstimateComparison(
        api_state=state,
        api_reported_gst=api_amount,
        engine_estimated_gst=engine.total_gst,
        variance_api_minus_engine=variance,
        status=status,
        taxable_base=engine.taxable_base,
        tax_type=engine.tax_type,
    )
