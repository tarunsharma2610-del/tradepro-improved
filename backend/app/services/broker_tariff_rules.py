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


PAISE = Decimal("0.01")


def calculate_tariff_amount(
    rule: TariffRule,
    *,
    calculation_base: Decimal | str | int | float,
) -> Decimal:
    """Calculate one rule's amount using its declared unit and explicit base.

    The caller must already have selected an approved rule for the trade scope.
    INR_PER_CRORE means rate rupees per INR 10,000,000 of base; it is deliberately
    distinct from PERCENT to prevent silent unit confusion. Fixed rules ignore
    the base magnitude but still require a finite nonnegative explicit base.
    """
    if not isinstance(rule, TariffRule):
        raise ValueError("A validated tariff rule is required.")
    if rule.review_status != "APPROVED":
        raise ValueError("Only an approved tariff rule can be calculated.")

    try:
        base = calculation_base if isinstance(calculation_base, Decimal) else Decimal(str(calculation_base))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Calculation base must be a finite nonnegative decimal.") from exc
    if not base.is_finite() or base < 0:
        raise ValueError("Calculation base must be a finite nonnegative decimal.")

    if rule.rate_unit == "PERCENT":
        amount = base * rule.rate / Decimal("100")
    elif rule.rate_unit == "INR_PER_CRORE":
        amount = base * rule.rate / Decimal("10000000")
    elif rule.rate_unit == "INR_FIXED":
        amount = rule.rate
    else:  # Defensive guard if a rule object is mutated or deserialized unsafely.
        raise ValueError("Unsupported tariff rate unit.")
    return amount.quantize(PAISE, rounding="ROUND_HALF_UP")


def calculate_charge_for_trade(
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
    calculation_base: Decimal | str | int | float,
) -> tuple[TariffRule, Decimal]:
    """Select exactly one approved effective tariff and calculate its amount.

    This is the safe composition entry point for callers that have an explicit
    trade scope. It does not persist a charge or allocate it across fills.
    """
    rule = select_tariff_rule(
        rules,
        component=component,
        broker=broker,
        exchange=exchange,
        segment=segment,
        product=product,
        transaction_side=transaction_side,
        calculation_basis=calculation_basis,
        trade_date=trade_date,
    )
    return rule, calculate_tariff_amount(rule, calculation_base=calculation_base)

def calculate_order_brokerage(
    rule: TariffRule,
    *,
    order_notional: Decimal | str | int | float,
    minimum_inr: Decimal | str | int | float | None = None,
    maximum_inr: Decimal | str | int | float | None = None,
) -> Decimal:
    """Calculate brokerage once at order scope, applying explicit order min/cap.

    This helper intentionally returns one order-level amount. It does not split
    that amount among fills; any distribution needs a separately reviewed policy.
    Minimum and maximum values must come from the selected, reviewed tariff
    source and must not be inferred from this helper.
    """
    if (
        not isinstance(rule, TariffRule)
        or rule.component.lower() != "brokerage"
        or rule.calculation_basis != "ORDER_NOTIONAL"
        or rule.rate_unit != "PERCENT"
    ):
        raise ValueError("Order brokerage requires an approved ORDER_NOTIONAL percent rule.")
    amount = calculate_tariff_amount(rule, calculation_base=order_notional)

    def optional_amount(value: Decimal | str | int | float | None, field: str) -> Decimal | None:
        if value is None:
            return None
        try:
            parsed = value if isinstance(value, Decimal) else Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError(f"{field} must be a finite nonnegative decimal.") from exc
        if not parsed.is_finite() or parsed < 0:
            raise ValueError(f"{field} must be a finite nonnegative decimal.")
        return parsed

    minimum = optional_amount(minimum_inr, "Minimum brokerage")
    maximum = optional_amount(maximum_inr, "Maximum brokerage")
    if minimum is not None and maximum is not None and minimum > maximum:
        raise ValueError("Minimum brokerage cannot exceed maximum brokerage.")
    if minimum is not None:
        amount = max(amount, minimum)
    if maximum is not None:
        amount = min(amount, maximum)
    return amount.quantize(PAISE, rounding="ROUND_HALF_UP")


def calculate_gst_on_explicit_components(
    rule: TariffRule,
    *,
    taxable_components: dict[str, Decimal | str | int | float],
    approved_taxable_component_names: tuple[str, ...] | list[str],
) -> tuple[Decimal, Decimal]:
    """Calculate GST only from an explicit, caller-approved component set.

    Returns (taxable_base, GST amount). The caller must source and review the
    included component names and GST rate; this function does not determine tax
    law, add excluded components, or allocate the resulting GST across fills.
    """
    if (
        not isinstance(rule, TariffRule)
        or rule.component.lower() != "gst"
        or rule.calculation_basis != "GST_TAXABLE_COMPONENT_SUM"
        or rule.rate_unit != "PERCENT"
    ):
        raise ValueError("GST requires an approved GST_TAXABLE_COMPONENT_SUM percent rule.")
    if not isinstance(taxable_components, dict) or not taxable_components:
        raise ValueError("An explicit nonempty taxable component mapping is required.")
    if not isinstance(approved_taxable_component_names, (tuple, list)) or not approved_taxable_component_names:
        raise ValueError("An explicit approved taxable component set is required.")
    names = list(approved_taxable_component_names)
    if any(not isinstance(name, str) or not name.strip() for name in names):
        raise ValueError("Approved taxable component names must be nonempty strings.")
    if len(names) != len(set(names)):
        raise ValueError("Approved taxable component names must be unique.")
    if set(taxable_components) != set(names):
        raise ValueError("Taxable components must exactly match the approved component set.")

    taxable_base = Decimal("0")
    for name in names:
        value = taxable_components[name]
        try:
            amount = value if isinstance(value, Decimal) else Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError(f"Taxable component {name} must be a finite nonnegative decimal.") from exc
        if not amount.is_finite() or amount < 0:
            raise ValueError(f"Taxable component {name} must be a finite nonnegative decimal.")
        taxable_base += amount
    taxable_base = taxable_base.quantize(PAISE, rounding="ROUND_HALF_UP")
    gst_amount = calculate_tariff_amount(rule, calculation_base=taxable_base)
    return taxable_base, gst_amount

def calculate_stamp_duty_for_trade(
    rule: TariffRule,
    *,
    transaction_side: str,
    product: str,
    calculation_base: Decimal | str | int | float,
) -> Decimal:
    """Calculate stamp duty only for an explicit eligible buy-side trade base.

    This guards the calculation shape, not the legal tariff itself. The rate and
    effective date must come from a reviewed, approved source rule. Options use
    an explicitly identified premium base; futures use an explicitly identified
    turnover base. No side, product, or base is inferred.
    """
    if not isinstance(rule, TariffRule) or rule.component.lower() != "stamp_duty":
        raise ValueError("A stamp_duty tariff rule is required.")
    if transaction_side != "BUY" or rule.transaction_side != "BUY":
        raise ValueError("Stamp duty calculation requires an explicitly eligible BUY side.")
    if product != rule.product:
        raise ValueError("Product must exactly match the selected stamp duty rule.")
    allowed_bases = {
        ("OPTIONS", "OPTION_PREMIUM"),
        ("FUTURES", "FUTURES_TURNOVER"),
    }
    if (product, rule.calculation_basis) not in allowed_bases:
        raise ValueError("Stamp duty requires OPTIONS/OPTION_PREMIUM or FUTURES/FUTURES_TURNOVER.")
    return calculate_tariff_amount(rule, calculation_base=calculation_base)

