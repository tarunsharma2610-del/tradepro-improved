"""Public Upstox schedule rules approved for estimates only.

The underlying candidate registry remains DRAFT. This module is a narrow,
reviewed allowlist for the dated official public schedule snapshot; it must not
be used as evidence of actual booked charges. Actual per-fill accounting still
requires reviewed contract-note evidence and canonical reconciled allocations.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
from typing import Sequence
from uuid import UUID

from app.services.broker_tariff_rules import TariffRule, select_tariff_rule
from app.services.tariff_estimate_snapshot import (
    TariffEstimateSnapshot,
    build_tariff_estimate_snapshot,
)
from app.services.upstox_tariff_candidates import (
    NSE_STT_URL,
    RETRIEVED_ON,
    SOURCE_SNAPSHOT_SHA256,
    UPSTOX_CHARGES_URL,
    upstox_tariff_candidate_rules,
)

PUBLIC_ESTIMATE_SOURCE_KIND = "PUBLIC_SCHEDULE_ESTIMATE_ONLY"

# This explicit allowlist is intentionally limited to the 18 dated STT and
# exchange-charge identities reviewed against the official snapshot. New rows,
# changed rates, dates, or source URLs fail closed until this list is reviewed.
_EXPECTED_IDENTITIES = frozenset({
    ("stt", "NSE", "EQ", "DELIVERY", "BUY", "TURNOVER", "0.1", "PERCENT", "2023-04-01", None, UPSTOX_CHARGES_URL),
    ("stt", "NSE", "EQ", "DELIVERY", "SELL", "TURNOVER", "0.1", "PERCENT", "2023-04-01", None, UPSTOX_CHARGES_URL),
    ("stt", "NSE", "EQ", "INTRADAY", "SELL", "TURNOVER", "0.025", "PERCENT", "2023-04-01", None, UPSTOX_CHARGES_URL),
    ("stt", "NSE", "FO", "FUTURES", "SELL", "TURNOVER", "0.05", "PERCENT", "2026-04-01", None, NSE_STT_URL),
    ("stt", "NSE", "FO", "FUTURES", "SELL", "TURNOVER", "0.02", "PERCENT", "2024-10-01", "2026-03-31", UPSTOX_CHARGES_URL),
    ("stt", "NSE", "FO", "OPTIONS", "SELL", "PREMIUM", "0.15", "PERCENT", "2026-04-01", None, NSE_STT_URL),
    ("stt", "NSE", "FO", "OPTIONS", "SELL", "PREMIUM", "0.1", "PERCENT", "2024-10-01", "2026-03-31", UPSTOX_CHARGES_URL),
    ("stt", "NSE", "FO", "OPTIONS_EXERCISED", "BUY", "INTRINSIC_VALUE", "0.15", "PERCENT", "2026-04-01", None, NSE_STT_URL),
    ("exchange_charges", "NSE", "EQ", "DELIVERY", "BUY", "TURNOVER", "0.00307", "PERCENT", "2026-03-01", None, UPSTOX_CHARGES_URL),
    ("exchange_charges", "NSE", "EQ", "DELIVERY", "SELL", "TURNOVER", "0.00307", "PERCENT", "2026-03-01", None, UPSTOX_CHARGES_URL),
    ("exchange_charges", "NSE", "EQ", "INTRADAY", "BUY", "TURNOVER", "0.00307", "PERCENT", "2026-03-01", None, UPSTOX_CHARGES_URL),
    ("exchange_charges", "NSE", "EQ", "INTRADAY", "SELL", "TURNOVER", "0.00307", "PERCENT", "2026-03-01", None, UPSTOX_CHARGES_URL),
    ("exchange_charges", "NSE", "FO", "FUTURES", "BUY", "TURNOVER", "0.00183", "PERCENT", "2026-03-01", None, UPSTOX_CHARGES_URL),
    ("exchange_charges", "NSE", "FO", "FUTURES", "SELL", "TURNOVER", "0.00183", "PERCENT", "2026-03-01", None, UPSTOX_CHARGES_URL),
    ("exchange_charges", "NSE", "FO", "OPTIONS", "BUY", "PREMIUM", "0.03553", "PERCENT", "2026-03-01", None, UPSTOX_CHARGES_URL),
    ("exchange_charges", "NSE", "FO", "OPTIONS", "SELL", "PREMIUM", "0.03553", "PERCENT", "2026-03-01", None, UPSTOX_CHARGES_URL),
    ("exchange_charges", "BSE", "FO", "OPTIONS", "BUY", "PREMIUM", "0.0325", "PERCENT", "2026-03-01", None, UPSTOX_CHARGES_URL),
    ("exchange_charges", "BSE", "FO", "OPTIONS", "SELL", "PREMIUM", "0.0325", "PERCENT", "2026-03-01", None, UPSTOX_CHARGES_URL),
})


def _identity(rule: TariffRule) -> tuple[str | None, ...]:
    return (
        rule.component,
        rule.exchange,
        rule.segment,
        rule.product,
        rule.transaction_side,
        rule.calculation_basis,
        format(rule.rate, "f"),
        rule.rate_unit,
        rule.effective_from.isoformat(),
        rule.effective_to.isoformat() if rule.effective_to else None,
        rule.source_url,
    )


def upstox_public_schedule_estimate_rules() -> tuple[TariffRule, ...]:
    """Return only the exact allowlisted public-schedule estimate rules.

    The returned APPROVED status is scoped to estimate generation. It does not
    authorize actual-charge promotion, per-fill allocation, or a user's
    account-specific tariff assumptions.
    """
    candidates = upstox_tariff_candidate_rules()
    if len(candidates) != len(_EXPECTED_IDENTITIES):
        raise ValueError("Upstox candidate registry changed; public estimate review must be repeated.")
    if any(rule.review_status != "DRAFT" for rule in candidates):
        raise ValueError("Upstox candidate registry must remain DRAFT; use the reviewed estimate allowlist.")
    if any(
        rule.broker != "Upstox"
        or rule.source_sha256 != SOURCE_SNAPSHOT_SHA256
        or rule.source_retrieved_on != RETRIEVED_ON
        or rule.source_url not in {UPSTOX_CHARGES_URL, NSE_STT_URL}
        or rule.rate_unit != "PERCENT"
        for rule in candidates
    ):
        raise ValueError("Upstox public estimate candidate provenance changed; review is required.")
    by_identity = {_identity(rule): rule for rule in candidates}
    if len(by_identity) != len(candidates) or set(by_identity) != _EXPECTED_IDENTITIES:
        raise ValueError("Upstox public estimate rule identities differ from the reviewed allowlist.")
    return tuple(replace(rule, review_status="APPROVED") for rule in candidates)


def build_upstox_public_schedule_estimate_snapshot(
    *,
    component: str,
    exchange: str,
    segment: str,
    product: str,
    transaction_side: str,
    calculation_basis: str,
    trade_date: date,
    calculation_base: Decimal | str | int | float,
    source_identity: str,
    source_trade_record_id: UUID | str | None = None,
    comparison_scope: str = "TRADE_FILL",
    source_fill_record_ids: Sequence[UUID | str] | None = None,
) -> TariffEstimateSnapshot:
    """Build a public-schedule estimate snapshot; never a broker actual."""
    rule = select_tariff_rule(
        upstox_public_schedule_estimate_rules(),
        component=component,
        broker="Upstox",
        exchange=exchange,
        segment=segment,
        product=product,
        transaction_side=transaction_side,
        calculation_basis=calculation_basis,
        trade_date=trade_date,
    )
    return build_tariff_estimate_snapshot(
        rule,
        trade_date=trade_date,
        calculation_base=calculation_base,
        source_identity=source_identity,
        source_kind=PUBLIC_ESTIMATE_SOURCE_KIND,
        source_trade_record_id=source_trade_record_id,
        comparison_scope=comparison_scope,
        source_fill_record_ids=source_fill_record_ids,
    )
