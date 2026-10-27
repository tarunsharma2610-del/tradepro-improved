"""Fail-closed, effective-dated tariff rule selection.

This registry intentionally ships without active rates. Rates must be added only
after review against a source and must identify their applicability dimensions.
It is a selection/provenance layer, not yet a complete charge calculator.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Iterable, Mapping


from app.services.broker_charge_allocation_service import allocate_component_total


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
    minimum_inr: Decimal | None = None
    maximum_inr: Decimal | None = None

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
        def normalize_cap(value: Decimal | None, field: str) -> Decimal | None:
            if value is None:
                return None
            try:
                parsed = value if isinstance(value, Decimal) else Decimal(str(value))
            except (InvalidOperation, TypeError, ValueError) as exc:
                raise ValueError(f"{field} must be a finite nonnegative decimal.") from exc
            if not parsed.is_finite() or parsed < 0:
                raise ValueError(f"{field} must be a finite nonnegative decimal.")
            if parsed != parsed.quantize(Decimal("0.01")):
                raise ValueError(f"{field} must be expressed to paise precision.")
            return parsed
        minimum = normalize_cap(self.minimum_inr, "Minimum brokerage")
        maximum = normalize_cap(self.maximum_inr, "Maximum brokerage")
        if (minimum is not None or maximum is not None) and (
            self.component.lower() != "brokerage"
            or self.calculation_basis != "ORDER_NOTIONAL"
            or self.rate_unit != "PERCENT"
        ):
            raise ValueError(
                "Minimum and maximum caps are supported only for order-notional percentage brokerage rules."
            )
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError("Minimum brokerage cannot exceed maximum brokerage.")
        object.__setattr__(self, "minimum_inr", minimum)
        object.__setattr__(self, "maximum_inr", maximum)
        if self.component.strip().lower() == "brokerage":
            if self.calculation_basis == "ORDER_FIXED" and self.rate_unit != "INR_FIXED":
                raise ValueError("ORDER_FIXED brokerage requires the INR_FIXED rate unit.")
            if self.calculation_basis == "ORDER_NOTIONAL" and self.rate_unit != "PERCENT":
                raise ValueError("ORDER_NOTIONAL brokerage requires the PERCENT rate unit.")
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


GENERIC_CALCULATION_BASES = frozenset({"ORDER_NOTIONAL", "PREMIUM", "NOTIONAL", "TURNOVER"})

# These components require product/event-specific legal or aggregation rules.
# They must never be treated as a plain rate × base calculation.
CONDITIONAL_COMPONENTS = frozenset({
    "stt",
    "ctt",
    "dp",
    "dp_charge",
    "dp_charges",
    "demat_transaction_charge",
    "depository_participant_charge",
    # IPFT is product-, exchange-, basis- and effective-date-specific. It must
    # use the guarded helper below, never a generic rate × arbitrary base.
    "ipft",
})


def _calculate_rate_amount(
    rule: TariffRule,
    base_value: Decimal | str | int | float,
) -> Decimal:
    """Apply a validated rule's unit to a finite nonnegative base."""
    try:
        base = base_value if isinstance(base_value, Decimal) else Decimal(str(base_value))
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


def calculate_stt_for_trade(
    rule: TariffRule,
    *,
    product: str,
    transaction_side: str,
    calculation_base: Decimal | str | int | float,
) -> Decimal:
    """Calculate only an explicitly scoped STT shape from an approved rule.

    This is estimate arithmetic, not legal advice or proof of booked charges.
    Unsupported exchange/product/side/base combinations fail closed.
    """
    if not isinstance(rule, TariffRule) or rule.component.lower() != "stt":
        raise ValueError("An STT tariff rule is required.")
    if rule.review_status != "APPROVED":
        raise ValueError("Only an approved tariff rule can be calculated.")
    if rule.exchange != "NSE":
        raise ValueError("STT calculation is enabled only for the reviewed NSE rule scope.")
    if product != rule.product or transaction_side != rule.transaction_side:
        raise ValueError("STT product and transaction side must exactly match the selected rule.")
    allowed_shapes = {
        ("DELIVERY", "BUY", "TURNOVER", "EQ"),
        ("DELIVERY", "SELL", "TURNOVER", "EQ"),
        ("INTRADAY", "SELL", "TURNOVER", "EQ"),
        ("FUTURES", "SELL", "TURNOVER", "FO"),
        ("OPTIONS", "SELL", "PREMIUM", "FO"),
        ("OPTIONS_EXERCISED", "BUY", "INTRINSIC_VALUE", "FO"),
    }
    if (product, transaction_side, rule.calculation_basis, rule.segment) not in allowed_shapes:
        raise ValueError("Unsupported STT product/side/calculation-basis combination.")
    if rule.rate_unit != "PERCENT":
        raise ValueError("STT requires a percentage-based approved rule.")
    return _calculate_rate_amount(rule, calculation_base)


def calculate_ipft_estimate_for_scope(
    rules: Iterable[TariffRule],
    *,
    broker: str,
    exchange: str,
    segment: str,
    product: str,
    transaction_side: str,
    trade_date: date,
    premium_value_base: Decimal | str | int | float,
) -> tuple[TariffRule, Decimal]:
    """Estimate NSE equity-options IPFT using one explicit premium-value scope.

    The caller must supply a premium-value base whose aggregation scope matches
    the selected source rule (for example, a documented side/period scope).
    This helper does not decide aggregation, allocate aggregate amounts to fills,
    or establish actual booked charges. It deliberately supports only NSE equity
    options and a rupees-per-crore premium-value rule.
    """
    if exchange != "NSE" or segment != "FO" or product != "OPTIONS":
        raise ValueError("IPFT estimate supports only NSE equity options in FO.")
    if transaction_side not in {"BUY", "SELL"}:
        raise ValueError("IPFT estimate requires an explicit BUY or SELL side.")
    rule = select_tariff_rule(
        rules,
        component="ipft",
        broker=broker,
        exchange=exchange,
        segment=segment,
        product=product,
        transaction_side=transaction_side,
        calculation_basis="PREMIUM",
        trade_date=trade_date,
    )
    if rule.rate_unit != "INR_PER_CRORE":
        raise ValueError("NSE equity-options IPFT requires INR_PER_CRORE.")
    amount = _calculate_rate_amount(rule, premium_value_base)
    return rule, amount


def calculate_tariff_amount(
    rule: TariffRule,
    *,
    calculation_base: Decimal | str | int | float,
) -> Decimal:
    """Calculate a simple rule only when its basis is explicitly supported.

    Conditional, order-capped, stamp-duty, and GST-composition rules must use
    their specialized guarded entry points. Treating an unfamiliar basis as a
    generic percentage would silently apply the wrong tariff semantics.
    """
    if not isinstance(rule, TariffRule):
        raise ValueError("A validated tariff rule is required.")
    if rule.review_status != "APPROVED":
        raise ValueError("Only an approved tariff rule can be calculated.")
    normalized_component = rule.component.strip().lower()
    if (
        rule.calculation_basis not in GENERIC_CALCULATION_BASES
        or normalized_component in {"gst", "stamp_duty"}
        or normalized_component in CONDITIONAL_COMPONENTS
    ):
        raise ValueError(
            "Unsupported tariff calculation shape; use its specialized guarded entry point."
        )
    return _calculate_rate_amount(rule, calculation_base)


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
    # Reject forbidden sides before selection so the caller cannot hide an
    # ineligible stamp-duty request behind a generic "no matching rule" error.
    if component.lower() == "stamp_duty" and transaction_side != "BUY":
        raise ValueError("Stamp duty calculation requires an explicitly eligible BUY side.")
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
    if rule.component.lower() == "brokerage" and rule.calculation_basis in {"ORDER_NOTIONAL", "ORDER_FIXED"}:
        amount = calculate_order_brokerage(rule, order_notional=calculation_base)
    elif rule.component.lower() == "stamp_duty":
        amount = calculate_stamp_duty_for_trade(
            rule,
            transaction_side=transaction_side,
            product=product,
            calculation_base=calculation_base,
        )
    elif rule.component.lower() == "gst":
        raise ValueError(
            "GST composition requires calculate_gst_on_explicit_components with an explicit component set that is approved."
        )
    else:
        amount = calculate_tariff_amount(rule, calculation_base=calculation_base)
    return rule, amount

def calculate_order_brokerage(
    rule: TariffRule,
    *,
    order_notional: Decimal | str | int | float,
) -> Decimal:
    """Calculate order-level brokerage using caps embedded in the approved rule.

    Caps are tariff provenance, not caller-controlled inputs. This returns one
    order amount and does not allocate it among fills.
    """
    if not isinstance(rule, TariffRule) or rule.component.lower() != "brokerage":
        raise ValueError("Order brokerage requires an approved brokerage rule.")
    if rule.review_status != "APPROVED":
        raise ValueError("Only an approved tariff rule can be calculated.")
    if rule.calculation_basis == "ORDER_FIXED" and rule.rate_unit == "INR_FIXED":
        # Flat per-executed-order brokerage (e.g. equity delivery/options).
        # Validate the supplied base anyway, but do not use it to scale a fixed fee.
        _calculate_rate_amount(rule, order_notional)
        amount = rule.rate.quantize(PAISE, rounding="ROUND_HALF_UP")
        if rule.minimum_inr is not None or rule.maximum_inr is not None:
            raise ValueError("Fixed per-order brokerage cannot use percentage caps.")
        return amount
    if rule.calculation_basis != "ORDER_NOTIONAL" or rule.rate_unit != "PERCENT":
        raise ValueError("Order brokerage requires ORDER_FIXED/INR_FIXED or ORDER_NOTIONAL/PERCENT.")
    amount = calculate_tariff_amount(rule, calculation_base=order_notional)
    if rule.minimum_inr is not None:
        amount = max(amount, rule.minimum_inr)
    if rule.maximum_inr is not None:
        amount = min(amount, rule.maximum_inr)
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
    if rule.review_status != "APPROVED":
        raise ValueError("Only an approved tariff rule can be calculated.")
    if rule.rate != Decimal("18"):
        raise ValueError("Supported Indian brokerage/market-charge GST calculations require an 18 percent rate.")
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
        if amount != amount.quantize(PAISE):
            raise ValueError(f"Taxable component {name} must be expressed to paise precision.")
        taxable_base += amount
    taxable_base = taxable_base.quantize(PAISE, rounding="ROUND_HALF_UP")
    gst_amount = _calculate_rate_amount(rule, taxable_base)
    return taxable_base, gst_amount


def aggregate_gst_invoice_components(
    *,
    igst: Decimal | str | int | float | None = None,
    cgst: Decimal | str | int | float | None = None,
    sgst: Decimal | str | int | float | None = None,
) -> tuple[str, Decimal]:
    """Normalize invoice GST tax lines without inferring taxability or tax rates.

    Accept either an IGST line, or the paired CGST + SGST lines. Mixed
    interstate/intrastate tax lines and incomplete CGST/SGST pairs fail closed.
    The return value is (tax_mode, total_gst); the caller remains responsible
    for invoice provenance, jurisdiction, taxable-base and statutory review.
    """
    def parse_line(name: str, value: Decimal | str | int | float) -> Decimal:
        try:
            amount = value if isinstance(value, Decimal) else Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError(f"{name} must be a finite nonnegative paise amount.") from exc
        if not amount.is_finite() or amount < 0 or amount != amount.quantize(PAISE):
            raise ValueError(f"{name} must be a finite nonnegative paise amount.")
        return amount

    has_igst = igst is not None
    has_cgst = cgst is not None
    has_sgst = sgst is not None
    if has_igst and (has_cgst or has_sgst):
        raise ValueError("Invoice GST cannot mix IGST with CGST/SGST lines.")
    if has_igst:
        return "IGST", parse_line("IGST", igst)
    if has_cgst != has_sgst:
        raise ValueError("Intrastate GST requires both CGST and SGST lines.")
    if not has_cgst:
        raise ValueError("At least an IGST line or a CGST/SGST pair is required.")
    total = parse_line("CGST", cgst) + parse_line("SGST", sgst)
    return "CGST_SGST", total.quantize(PAISE, rounding="ROUND_HALF_UP")


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
    if rule.rate_unit != "PERCENT":
        raise ValueError("Stamp duty requires an explicitly percentage-based approved rule.")
    if rule.review_status != "APPROVED":
        raise ValueError("Only an approved tariff rule can be calculated.")
    if not rule.rate.is_finite() or rule.rate < 0 or rule.rate > Decimal("100"):
        raise ValueError("Stamp duty rate percent must be finite and between 0 and 100.")
    try:
        base = calculation_base if isinstance(calculation_base, Decimal) else Decimal(str(calculation_base))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Stamp duty calculation base must be a finite nonnegative decimal.") from exc
    if not base.is_finite() or base < 0:
        raise ValueError("Stamp duty calculation base must be a finite nonnegative decimal.")
    if base != base.quantize(PAISE):
        raise ValueError("Stamp duty calculation base must be expressed to paise precision.")
    return _calculate_rate_amount(rule, base)



def calculate_order_brokerage_allocation(
    rule: TariffRule,
    *,
    order_notional: Decimal | str | int | float,
    reviewed_fill_weights: Mapping[str, Decimal | str | int | float],
) -> dict[str, Decimal]:
    """Propose a deterministic split of one order-level brokerage estimate.

    The brokerage rate and minimum/maximum cap are applied once to the whole
    order, then the resulting paise-exact amount is distributed using caller-
    supplied, independently reviewed fill weights. This is estimate/allocation
    math only: it does not prove broker-booked amounts, choose the legally
    correct weights, persist evidence, or authorize live accounting promotion.
    """
    if not isinstance(reviewed_fill_weights, Mapping) or not reviewed_fill_weights:
        raise ValueError("A nonempty independently reviewed fill-weight mapping is required.")
    total = calculate_order_brokerage(rule, order_notional=order_notional)
    allocations = allocate_component_total(
        total,
        reviewed_fill_weights,
        allocation_basis="EXPLICIT_REVIEWED",
    )
    if sum(allocations.values(), Decimal("0")) != total:
        raise RuntimeError("Per-fill brokerage estimate does not reconcile to the capped order total.")
    return allocations
