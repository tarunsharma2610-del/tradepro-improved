"""Statutory GST valuation primitives for stock-broking services.

This service applies the CGST Act section 15 default valuation and the conditional
CGST Rule 33 pure-agent exclusion. It deliberately does not infer a pure-agent
relationship from a charge name (STT, stamp duty, exchange fee, SEBI, IPFT, etc.).
A broker/product tariff may provide a separate estimate policy; this statutory
engine is not a substitute for that source-specific policy or invoice evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Iterable

PAISE = Decimal("0.01")
GST_RATE_PERCENT = Decimal("18.00")
HALF_RATE_PERCENT = Decimal("9.00")


@dataclass(frozen=True)
class PureAgentEvidence:
    """Evidence flags for the cumulative Rule 33 pure-agent conditions.

    All flags must be true before the related third-party recovery is excluded.
    These flags are assertions to be backed by source documents; they are not
    automatically established merely because a broker calls a row a tax/fee.
    """

    recipient_authorized_payment: bool
    agreement_identifies_pure_agent: bool
    recipient_is_liable_for_third_party_payment: bool
    payment_is_on_recipient_behalf: bool
    separately_indicated_on_invoice: bool
    procured_in_addition_to_own_service: bool
    no_title_to_procured_supply: bool
    supplier_does_not_use_procured_supply: bool
    recovers_actual_amount_without_markup: bool

    def qualifies(self) -> bool:
        return all(
            value is True
            for value in (
                self.recipient_authorized_payment,
                self.agreement_identifies_pure_agent,
                self.recipient_is_liable_for_third_party_payment,
                self.payment_is_on_recipient_behalf,
                self.separately_indicated_on_invoice,
                self.procured_in_addition_to_own_service,
                self.no_title_to_procured_supply,
                self.supplier_does_not_use_procured_supply,
                self.recovers_actual_amount_without_markup,
            )
        )


@dataclass(frozen=True)
class GstValuationLine:
    name: str
    amount: Decimal | str | int
    # "SERVICE" is the supplier's own taxable service/fee.
    # "THIRD_PARTY_RECOVERY" is still included by default under section 15;
    # exclusion requires the complete Rule 33 evidence object below.
    kind: str = "SERVICE"
    pure_agent_evidence: PureAgentEvidence | None = None


@dataclass(frozen=True)
class StatutoryGstResult:
    taxable_base: Decimal
    gst_rate_percent: Decimal
    total_gst: Decimal
    tax_type: str
    igst: Decimal
    cgst: Decimal
    sgst: Decimal
    supplier_state_code: str
    place_of_supply_state_code: str
    place_of_supply_basis: str
    included_components: tuple[str, ...]
    excluded_pure_agent_components: tuple[str, ...]
    valuation_basis: str = "CGST_ACT_SECTION_15_AND_RULE_33"


def _amount(value: Decimal | str | int, *, label: str) -> Decimal:
    try:
        parsed = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a finite nonnegative amount.") from exc
    if not parsed.is_finite() or parsed < 0:
        raise ValueError(f"{label} must be a finite nonnegative amount.")
    return parsed.quantize(PAISE, rounding=ROUND_HALF_UP)


def _state_code(value: str, *, label: str) -> str:
    if not isinstance(value, str) or len(value) != 2 or not value.isdigit() or value == "00":
        raise ValueError(f"{label} must be an explicit two-digit GST state/UT code.")
    return value


def calculate_statutory_stock_broking_gst(
    lines: Iterable[GstValuationLine],
    *,
    supplier_state_code: str,
    recipient_state_code_in_supplier_records: str | None,
) -> StatutoryGstResult:
    """Calculate a statutory GST estimate from explicit valuation lines.

    Place of supply follows IGST Act section 12(12): recipient location in the
    supplier's records, falling back to supplier location only when not recorded.
    Equal supplier/place-of-supply state codes yield CGST+SGST; unequal codes
    yield IGST. This is a calculation primitive, not tax/legal advice or actual
    invoice verification. Caller must supply the actual supplier state and
    recipient state recorded for this supply.
    """
    supplier_state = _state_code(supplier_state_code, label="supplier_state_code")
    if recipient_state_code_in_supplier_records is None:
        place_state = supplier_state
        place_basis = "SUPPLIER_STATE_FALLBACK_RECIPIENT_STATE_NOT_RECORDED"
    else:
        place_state = _state_code(
            recipient_state_code_in_supplier_records,
            label="recipient_state_code_in_supplier_records",
        )
        place_basis = "RECIPIENT_LOCATION_IN_SUPPLIER_RECORDS"

    included: list[str] = []
    excluded: list[str] = []
    seen: set[str] = set()
    total = Decimal("0.00")
    for line in lines:
        if not isinstance(line, GstValuationLine):
            raise ValueError("Every valuation line must be a GstValuationLine.")
        if not isinstance(line.name, str) or not line.name.strip():
            raise ValueError("Every valuation line requires a name.")
        if line.name in seen:
            raise ValueError("Valuation line names must be unique.")
        seen.add(line.name)
        if line.kind not in {"SERVICE", "THIRD_PARTY_RECOVERY"}:
            raise ValueError(f"Unsupported valuation line kind: {line.kind}")
        amount = _amount(line.amount, label=f"Line {line.name}")
        pure_agent_qualifies = (
            line.kind == "THIRD_PARTY_RECOVERY"
            and line.pure_agent_evidence is not None
            and line.pure_agent_evidence.qualifies()
        )
        if pure_agent_qualifies:
            excluded.append(line.name)
        else:
            # Section 15 default: include separate taxes/fees/charges unless a
            # documented, complete Rule 33 pure-agent exclusion is established.
            included.append(line.name)
            total += amount

    taxable_base = total.quantize(PAISE, rounding=ROUND_HALF_UP)
    total_gst = (taxable_base * GST_RATE_PERCENT / Decimal("100")).quantize(
        PAISE, rounding=ROUND_HALF_UP
    )
    if supplier_state == place_state:
        cgst = (taxable_base * HALF_RATE_PERCENT / Decimal("100")).quantize(
            PAISE, rounding=ROUND_HALF_UP
        )
        sgst = (taxable_base * HALF_RATE_PERCENT / Decimal("100")).quantize(
            PAISE, rounding=ROUND_HALF_UP
        )
        # Each tax head is rounded independently to paise. At half-paise
        # boundaries, CGST+SGST may differ by ₹0.01 from rounding the combined
        # 18% rate once; preserve the component-wise invoice arithmetic.
        total_gst = cgst + sgst
        return StatutoryGstResult(
            taxable_base, GST_RATE_PERCENT, total_gst, "CGST_SGST",
            Decimal("0.00"), cgst, sgst, supplier_state, place_state,
            place_basis, tuple(included), tuple(excluded),
        )
    return StatutoryGstResult(
        taxable_base, GST_RATE_PERCENT, total_gst, "IGST",
        total_gst, Decimal("0.00"), Decimal("0.00"), supplier_state,
        place_state, place_basis, tuple(included), tuple(excluded),
    )
