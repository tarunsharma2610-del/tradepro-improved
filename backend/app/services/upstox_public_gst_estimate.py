"""Upstox public-schedule GST estimate only; never actual-charge evidence.

Scope is limited to documented exchange/product combinations from 2026-03-01.
The exchange_charges input is the source-backed exchange charge total. For NSE
from 2026-03-01 this is the combined transaction/IPFT amount exactly once; for
BSE options use the applicable BSE schedule and do not assume NSE IPFT applies.
This function intentionally rejects a separate ipft component.
The official API example currently conflicts with the published tariff wording;
results must remain labelled estimates and must not be promoted to actuals.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Mapping

from app.services.broker_tariff_rules import TariffRule, calculate_gst_on_explicit_components
from app.services.upstox_tariff_candidates import (
    RETRIEVED_ON,
    SOURCE_SNAPSHOT_SHA256,
    UPSTOX_CHARGES_URL,
)

PUBLIC_SCHEDULE_ESTIMATE_ONLY = "PUBLIC_SCHEDULE_ESTIMATE_ONLY"
GST_EFFECTIVE_FROM = date(2026, 3, 1)
GST_RATE_PERCENT = Decimal("18")

_SUPPORTED_SCOPES = {
    ("NSE", "EQ", "DELIVERY"),
    ("NSE", "EQ", "INTRADAY"),
    ("NSE", "FO", "FUTURES"),
    ("NSE", "FO", "OPTIONS"),
    ("BSE", "FO", "OPTIONS"),
}


@dataclass(frozen=True)
class UpstoxPublicGstEstimate:
    source_kind: str
    trade_date: date
    exchange: str
    segment: str
    product: str
    rate_percent: Decimal
    taxable_components: tuple[str, ...]
    taxable_base: Decimal
    gst_amount: Decimal
    source_url: str
    source_sha256: str


def calculate_upstox_public_gst_estimate(
    *,
    trade_date: date,
    exchange: str,
    segment: str,
    product: str,
    taxable_components: Mapping[str, Decimal | str | int | float],
) -> UpstoxPublicGstEstimate:
    """Calculate an 18% estimate from explicit schedule-listed components.

    For equity delivery, callers must explicitly provide demat_charges (use
    0.00 only when it is known not to apply). Other supported products accept
    only brokerage and exchange_charges. exchange_charges means the combined
    transaction/IPFT amount; a separate ipft key is rejected to prevent double
    counting. SEBI, STT, stamp duty and trade notional are not GST-base inputs
    in this estimate function. The official API sample discrepancy remains
    unresolved; this estimate is not an actual invoice calculation.
    """
    if not isinstance(trade_date, date):
        raise ValueError("trade_date must be an explicit date.")
    if trade_date < GST_EFFECTIVE_FROM:
        raise ValueError("Public GST estimate helper supports dates from 2026-03-01 only.")
    normalized_scope = (str(exchange).upper(), str(segment).upper(), str(product).upper())
    if normalized_scope not in _SUPPORTED_SCOPES:
        raise ValueError("Exchange/segment/product is outside the reviewed Upstox estimate scope.")
    expected = (
        {"brokerage", "exchange_charges", "demat_charges"}
        if normalized_scope[2] == "DELIVERY"
        else {"brokerage", "exchange_charges"}
    )
    if not isinstance(taxable_components, dict) or set(taxable_components) != expected:
        raise ValueError(
            "GST estimate components must exactly match the reviewed product set; "
            "exchange_charges already includes transaction/IPFT once."
        )

    rule = TariffRule(
        component="gst",
        broker="Upstox",
        exchange=normalized_scope[0],
        segment=normalized_scope[1],
        product=normalized_scope[2],
        transaction_side="BOTH",
        calculation_basis="GST_TAXABLE_COMPONENT_SUM",
        rate=GST_RATE_PERCENT,
        rate_unit="PERCENT",
        effective_from=GST_EFFECTIVE_FROM,
        effective_to=None,
        source_url=UPSTOX_CHARGES_URL,
        source_retrieved_on=RETRIEVED_ON,
        source_sha256=SOURCE_SNAPSHOT_SHA256,
        review_status="APPROVED",
    )
    base, amount = calculate_gst_on_explicit_components(
        rule,
        taxable_components=dict(taxable_components),
        approved_taxable_component_names=tuple(sorted(expected)),
    )
    return UpstoxPublicGstEstimate(
        source_kind=PUBLIC_SCHEDULE_ESTIMATE_ONLY,
        trade_date=trade_date,
        exchange=normalized_scope[0],
        segment=normalized_scope[1],
        product=normalized_scope[2],
        rate_percent=GST_RATE_PERCENT,
        taxable_components=tuple(sorted(expected)),
        taxable_base=base,
        gst_amount=amount,
        source_url=UPSTOX_CHARGES_URL,
        source_sha256=SOURCE_SNAPSHOT_SHA256,
    )
