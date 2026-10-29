"""Public-schedule GST estimates for source-backed, unapproved tariff candidates.

This module deliberately allows DRAFT/REVIEWED policies only for estimates.
It never changes review state and its result cannot be promoted to actual-charge
accounting. Actual reconciliation must use source-reported invoice amounts.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Mapping

from app.services.broker_gst_component_policy import GstComponentPolicy, GST_RATE, PAISE

PUBLIC_SCHEDULE_ESTIMATE_ONLY = "PUBLIC_SCHEDULE_ESTIMATE_ONLY"


@dataclass(frozen=True)
class PublicScheduleGstEstimate:
    source_kind: str
    broker: str
    exchange: str
    segment: str
    product: str
    trade_date: date
    taxable_components: tuple[str, ...]
    taxable_base: Decimal
    gst_amount: Decimal
    source_url: str
    source_sha256: str


def calculate_public_schedule_gst_estimate(
    policy: GstComponentPolicy,
    *,
    trade_date: date,
    components: Mapping[str, Decimal | str | int | float],
) -> PublicScheduleGstEstimate:
    """Calculate a labelled estimate without conferring accounting approval.

    Only the exact component set declared by the source-backed policy is accepted.
    The trade date must be inside that policy's effective window. REJECTED policies
    cannot be used even for estimates; DRAFT/REVIEWED policies remain estimate-only.
    """
    if not isinstance(policy, GstComponentPolicy):
        raise ValueError("A source-backed GST component policy is required.")
    if policy.review_status == "REJECTED":
        raise ValueError("Rejected GST policies cannot be used for estimates.")
    if not isinstance(trade_date, date):
        raise ValueError("trade_date must be explicit.")
    if trade_date < policy.effective_from or (
        policy.effective_to is not None and trade_date > policy.effective_to
    ):
        raise ValueError("Trade date falls outside the GST policy effective window.")
    if not isinstance(components, dict) or set(components) != set(policy.taxable_components):
        raise ValueError("Input components must exactly match the candidate taxable component set.")

    parsed: dict[str, Decimal] = {}
    for name, value in components.items():
        try:
            amount = value if isinstance(value, Decimal) else Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError(f"GST component {name} must be a finite nonnegative amount.") from exc
        if not amount.is_finite() or amount < 0:
            raise ValueError(f"GST component {name} must be a finite nonnegative amount.")
        parsed[name] = amount

    base = sum(parsed.values(), Decimal("0.00")).quantize(PAISE, rounding=ROUND_HALF_UP)
    gst = (base * GST_RATE / Decimal("100")).quantize(PAISE, rounding=ROUND_HALF_UP)
    return PublicScheduleGstEstimate(
        source_kind=PUBLIC_SCHEDULE_ESTIMATE_ONLY,
        broker=policy.broker,
        exchange=policy.exchange,
        segment=policy.segment,
        product=policy.product,
        trade_date=trade_date,
        taxable_components=tuple(sorted(policy.taxable_components)),
        taxable_base=base,
        gst_amount=gst,
        source_url=policy.source_url,
        source_sha256=policy.source_sha256,
    )
