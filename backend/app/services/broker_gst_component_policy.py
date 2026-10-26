"""Cross-broker GST component policy primitives.

These are estimate-policy primitives, not actual invoice reconciliation. A policy
must be source-backed, effective-dated, independently approved and selected on
the full broker/exchange/segment/product tuple before calculation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable, Mapping

PAISE = Decimal("0.01")
GST_RATE = Decimal("18.00")
IPFT_MODES = frozenset({"COMBINED", "SEPARATE", "NOT_APPLICABLE"})
REVIEW_STATES = frozenset({"DRAFT", "REVIEWED", "APPROVED", "REJECTED"})


@dataclass(frozen=True)
class GstComponentPolicy:
    broker: str
    exchange: str
    segment: str
    product: str
    effective_from: date
    effective_to: date | None
    taxable_components: tuple[str, ...]
    ipft_mode: str
    source_url: str
    source_retrieved_on: date
    source_sha256: str
    review_status: str = "DRAFT"

    def __post_init__(self) -> None:
        for field in ("broker", "exchange", "segment", "product", "source_url", "source_sha256"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} is required.")
        if not self.taxable_components or any(
            not isinstance(name, str) or not name.strip() for name in self.taxable_components
        ):
            raise ValueError("An explicit non-empty taxable component set is required.")
        if len(set(self.taxable_components)) != len(self.taxable_components):
            raise ValueError("Taxable component names must be unique.")
        if self.ipft_mode not in IPFT_MODES:
            raise ValueError("IPFT mode must be COMBINED, SEPARATE or NOT_APPLICABLE.")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("Policy effective_to cannot precede effective_from.")
        if self.source_retrieved_on < self.effective_from and self.review_status != "APPROVED":
            raise ValueError("Future-effective policies require explicit approval.")
        if len(self.source_sha256) != 64 or any(
            c not in "0123456789abcdefABCDEF" for c in self.source_sha256
        ):
            raise ValueError("Policy source_sha256 must be a 64-character SHA-256.")
        if self.review_status not in REVIEW_STATES:
            raise ValueError("Unsupported policy review state.")
        components = set(self.taxable_components)
        if self.ipft_mode == "COMBINED":
            if "exchange_charges" not in components:
                raise ValueError("COMBINED IPFT mode requires canonical exchange_charges.")
            if "ipft" in components or "transaction_charges" in components:
                raise ValueError("COMBINED mode cannot also list separate transaction_charges/IPFT.")
        elif self.ipft_mode == "SEPARATE":
            if "transaction_charges" not in components or "ipft" not in components:
                raise ValueError("SEPARATE IPFT mode requires transaction_charges and ipft.")
            if "exchange_charges" in components:
                raise ValueError("SEPARATE mode cannot also list combined exchange_charges.")
        elif "ipft" in components:
            raise ValueError("NOT_APPLICABLE mode cannot list an IPFT component.")


def select_gst_component_policy(
    policies: Iterable[GstComponentPolicy],
    *,
    broker: str,
    exchange: str,
    segment: str,
    product: str,
    trade_date: date,
) -> GstComponentPolicy:
    key = (broker, exchange, segment, product)
    matches = [
        policy for policy in policies
        if (policy.broker, policy.exchange, policy.segment, policy.product) == key
        and policy.review_status == "APPROVED"
        and policy.effective_from <= trade_date
        and (policy.effective_to is None or trade_date <= policy.effective_to)
    ]
    if not matches:
        raise ValueError("No approved GST component policy matches the complete scope and date.")
    if len(matches) != 1:
        raise ValueError("Multiple approved GST component policies overlap.")
    return matches[0]


def calculate_gst_estimate(
    policy: GstComponentPolicy,
    *,
    components: Mapping[str, Decimal | str | int | float],
) -> tuple[Decimal, Decimal]:
    """Return (taxable base, GST) using an approved policy and exact component set."""
    if not isinstance(policy, GstComponentPolicy) or policy.review_status != "APPROVED":
        raise ValueError("Only an approved GST component policy can be calculated.")
    if not isinstance(components, dict) or set(components) != set(policy.taxable_components):
        raise ValueError("Input components must exactly match the approved taxable component set.")
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
    return base, gst
