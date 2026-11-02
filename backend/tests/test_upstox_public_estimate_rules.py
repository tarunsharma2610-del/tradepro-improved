from datetime import date
from decimal import Decimal
import json

import pytest

from app.services.broker_tariff_rules import select_tariff_rule
from app.services.tariff_estimate_snapshot import build_tariff_estimate_snapshot
from app.services.upstox_public_estimate_rules import (
    PUBLIC_ESTIMATE_SOURCE_KIND,
    build_upstox_public_schedule_estimate_snapshot,
    upstox_public_schedule_estimate_rules,
)
from app.services.upstox_tariff_candidates import (
    SOURCE_SNAPSHOT_SHA256,
    upstox_tariff_candidate_rules,
)


def test_candidate_rules_remain_draft_but_reviewed_public_estimate_allowlist_is_approved():
    candidates = upstox_tariff_candidate_rules()
    approved = upstox_public_schedule_estimate_rules()

    assert len(candidates) == len(approved) == 18
    assert all(rule.review_status == "DRAFT" for rule in candidates)
    assert all(rule.review_status == "APPROVED" for rule in approved)
    assert all(rule.source_sha256 == SOURCE_SNAPSHOT_SHA256 for rule in approved)
    assert {rule.component for rule in approved} == {"stt", "exchange_charges"}
    assert not {"brokerage", "gst", "stamp_duty", "dp", "sebi_charges"} & {
        rule.component for rule in approved
    }


def test_public_estimate_allowlist_rejects_unreviewed_registry_changes(monkeypatch):
    from app.services import upstox_public_estimate_rules as registry

    original = registry.upstox_tariff_candidate_rules
    monkeypatch.setattr(registry, "upstox_tariff_candidate_rules", lambda: original()[:-1])
    with pytest.raises(ValueError, match="candidate registry changed"):
        registry.upstox_public_schedule_estimate_rules()


def test_effective_date_boundaries_select_exact_public_estimate_rules():
    rules = upstox_public_schedule_estimate_rules()
    old_stt = select_tariff_rule(
        rules,
        component="stt", broker="Upstox", exchange="NSE", segment="FO",
        product="FUTURES", transaction_side="SELL", calculation_basis="TURNOVER",
        trade_date=date(2026, 3, 31),
    )
    new_stt = select_tariff_rule(
        rules,
        component="stt", broker="Upstox", exchange="NSE", segment="FO",
        product="FUTURES", transaction_side="SELL", calculation_basis="TURNOVER",
        trade_date=date(2026, 4, 1),
    )
    assert old_stt.rate == Decimal("0.02")
    assert new_stt.rate == Decimal("0.05")

    with pytest.raises(ValueError, match="No approved tariff rule"):
        select_tariff_rule(
            rules,
            component="exchange_charges", broker="Upstox", exchange="NSE", segment="FO",
            product="FUTURES", transaction_side="SELL", calculation_basis="TURNOVER",
            trade_date=date(2026, 2, 28),
        )
    exchange = select_tariff_rule(
        rules,
        component="exchange_charges", broker="Upstox", exchange="NSE", segment="FO",
        product="FUTURES", transaction_side="SELL", calculation_basis="TURNOVER",
        trade_date=date(2026, 3, 1),
    )
    assert exchange.rate == Decimal("0.00183")


def test_public_schedule_estimate_snapshot_is_explicitly_not_actual_charge_evidence():
    snapshot = build_upstox_public_schedule_estimate_snapshot(
        component="stt",
        exchange="NSE",
        segment="FO",
        product="FUTURES",
        transaction_side="SELL",
        calculation_basis="TURNOVER",
        trade_date=date(2026, 4, 1),
        calculation_base=Decimal("1000000"),
        source_identity="public-schedule-estimate:future-sell:2026-10-26",
    )
    payload = json.loads(snapshot.canonical_json())
    assert snapshot.source_kind == PUBLIC_ESTIMATE_SOURCE_KIND
    assert snapshot.review_status == "APPROVED"
    assert snapshot.source_sha256 == SOURCE_SNAPSHOT_SHA256
    assert snapshot.calculated_amount == "500.00"
    assert payload["source_kind"] == "PUBLIC_SCHEDULE_ESTIMATE_ONLY"
    assert payload["source_kind"] != "UPSTOX_BROKERAGE_API_ESTIMATE"


def test_public_estimate_builder_fails_closed_for_unsupported_scope():
    with pytest.raises(ValueError, match="No approved tariff rule"):
        build_upstox_public_schedule_estimate_snapshot(
            component="exchange_charges",
            exchange="BSE",
            segment="EQ",
            product="DELIVERY",
            transaction_side="BUY",
            calculation_basis="TURNOVER",
            trade_date=date(2026, 10, 26),
            calculation_base=Decimal("100000"),
            source_identity="unsupported-bse-cash",
        )


def test_tariff_estimate_source_kind_is_validated():
    rule = upstox_public_schedule_estimate_rules()[0]
    with pytest.raises(ValueError, match="Unsupported tariff estimate source_kind"):
        build_tariff_estimate_snapshot(
            rule,
            trade_date=date(2026, 10, 26),
            calculation_base=Decimal("100000"),
            source_identity="bad-source-kind",
            source_kind="BROKER_ACTUAL",
        )
