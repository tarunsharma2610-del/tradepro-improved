"""Compare source-reported GST with an explicitly supplied expected tax base.

This helper does not decide which charges belong in the taxable base. That policy
must be resolved from law, broker/product tariff and source evidence before calling.
It preserves the reported amount and returns any variance instead of rewriting it.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

PAISE = Decimal("0.01")


def _money(value: Decimal | str | int, *, label: str) -> Decimal:
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite nonnegative paise amount") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"{label} must be a finite nonnegative paise amount")
    if amount != amount.quantize(PAISE):
        raise ValueError(f"{label} must be expressed to paise precision")
    return amount.quantize(PAISE)


@dataclass(frozen=True)
class GstSourceVariance:
    source_label: str
    taxable_base: Decimal
    rate_percent: Decimal
    expected_tax: Decimal
    reported_tax: Decimal
    variance: Decimal
    matches: bool


def reconcile_reported_gst(
    *,
    source_label: str,
    explicitly_reviewed_taxable_base: Decimal | str | int,
    rate_percent: Decimal | str | int,
    source_reported_tax: Decimal | str | int,
) -> GstSourceVariance:
    """Compare source tax with tax on a caller-reviewed base; never infer the base."""
    if not isinstance(source_label, str) or not source_label.strip():
        raise ValueError("source_label is required")
    base = _money(explicitly_reviewed_taxable_base, label="taxable base")
    reported = _money(source_reported_tax, label="source-reported tax")
    try:
        rate = rate_percent if isinstance(rate_percent, Decimal) else Decimal(str(rate_percent))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("rate_percent must be finite and positive") from exc
    if not rate.is_finite() or rate <= 0 or rate > Decimal("100"):
        raise ValueError("rate_percent must be finite and between 0 and 100")
    expected = (base * rate / Decimal("100")).quantize(PAISE, rounding=ROUND_HALF_UP)
    variance = (reported - expected).quantize(PAISE)
    return GstSourceVariance(
        source_label=source_label.strip(),
        taxable_base=base,
        rate_percent=rate,
        expected_tax=expected,
        reported_tax=reported,
        variance=variance,
        matches=variance == Decimal("0.00"),
    )
