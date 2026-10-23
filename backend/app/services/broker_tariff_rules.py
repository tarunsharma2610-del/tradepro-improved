"""Fail-closed, effective-dated tariff rule selection.

This registry intentionally ships without active rates. Rates must be added only
after review against a source and must identify their applicability dimensions.
It is a selection/provenance layer, not yet a complete charge calculator.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Iterable


RATE_UNITS = frozenset({"PERCENT", "INR_PER_CRORE", "INR_FIXED"})
REVIEW_STATES = frozenset({"DRAFT", "REVIEWED", "APPROVED", "REJECTED"})


@dataclass(frozen=True)
class TariffRule:
    component: str
    broker: str
    exchange: str
    segment: str
    product: str
    transaction_side: str
    calculation_basis: str
    rate: Decimal
    rate_unit: str
    effective_from: date
    effective_to: date | None
    source_url: str
    source_retrieved_on: date
    source_sha256: str
    review_status: str

    def __post_init__(self) -> None:
        required = {
            "component": self.component,
            "broker": self.broker,
            "exchange": self.exchange,
            "segment": self.segment,
            "product": self.product,
            "transaction_side": self.transaction_side,
            "calculation_basis": self.calculation_basis,
            "source_url": self.source_url,
            "source_sha256": self.source_sha256,
        }
        if any(not isinstance(value, str) or not value.strip() for value in required.values()):
            raise ValueError("Tariff rule applicability and provenance fields are required.")
        try:
            rate = self.rate if isinstance(self.rate, Decimal) else Decimal(str(self.rate))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError("Tariff rate must be a finite nonnegative decimal.") from exc
        if not rate.is_finite() or rate < 0:
            raise ValueError("Tariff rate must be a finite nonnegative decimal.")
        object.__setattr__(self, "rate", rate)
        if self.rate_unit not in RATE_UNITS:
            raise ValueError("Unsupported tariff rate unit.")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("Tariff effective_to cannot precede effective_from.")
        if self.source_retrieved_on < self.effective_from:
            # This can occur for a future announced rate, but it needs an explicit
            # reviewed future-effective rule; do not silently accept it.
            if self.review_status != "APPROVED":
                raise ValueError("Future-effective tariff requires explicit APPROVED status.")
        if len(self.source_sha256) != 64 or any(c not in "0123456789abcdefABCDEF" for c in self.source_sha256):
            raise ValueError("Tariff source_sha256 must be a 64-character hexadecimal SHA-256.")
        if self.review_status not in REVIEW_STATES:
            raise ValueError("Unsupported tariff review status.")


def select_tariff_rule(
    rules: Iterable[TariffRule],
    *,
    component: str,
    broker: str,
    exchange: str,
    segment: str,
    product: str,
    transaction_side: str,
    calculation_basis: str,
    trade_date: date,
) -> TariffRule:
    """Select exactly one approved rule for the complete applicability tuple.

    No wildcards or closest-match fallbacks are allowed. Zero matches or
    overlapping approved rules raise ValueError, preserving fail-closed behavior.
    """
    key = (
        component, broker, exchange, segment, product,
        transaction_side, calculation_basis,
    )
    matches = [
        rule for rule in rules
        if (
            rule.component, rule.broker, rule.exchange, rule.segment, rule.product,
            rule.transaction_side, rule.calculation_basis,
        ) == key
        and rule.review_status == "APPROVED"
        and rule.effective_from <= trade_date
        and (rule.effective_to is None or trade_date <= rule.effective_to)
    ]
    if not matches:
        raise ValueError("No approved tariff rule matches the complete trade scope and date.")
    if len(matches) != 1:
        raise ValueError("Multiple approved tariff rules overlap for the same trade scope and date.")
    return matches[0]
