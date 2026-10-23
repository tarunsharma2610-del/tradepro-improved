from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from app.services.broker_tariff_rules import TariffRule
from app.services.tariff_estimate_snapshot import (
    build_tariff_estimate_snapshot,
    compare_estimate_replay,
)


def make_rule(**overrides):
    values = {
        "component": "brokerage",
        "broker": "Upstox",
        "exchange": "NSE",
        "segment": "FO",
        "product": "FUTURES",
        "transaction_side": "SELL",
        "calculation_basis": "ORDER_NOTIONAL",
        "rate": Decimal("0.05"),
        "rate_unit": "PERCENT",
        "effective_from": date(2026, 4, 1),
        "effective_to": None,
        "source_url": "https://upstox.com/brokerage-charges/",
        "source_retrieved_on": date(2026, 10, 23),
        "source_sha256": "a" * 64,
        "review_status": "APPROVED",
    }
    values.update(overrides)
    return TariffRule(**values)


def build(rule=None, **overrides):
    args = {
        "trade_date": date(2026, 10, 23),
        "calculation_base": "100000.00",
        "source_identity": "broker-trade:trade-123:brokerage",
    }
    args.update(overrides)
    return build_tariff_estimate_snapshot(rule or make_rule(), **args)


def test_snapshot_is_canonical_and_stable_for_exact_replay():
    first = build()
    second = build()
    assert first.canonical_json() == second.canonical_json()
    assert first.snapshot_sha256 == second.snapshot_sha256
    assert compare_estimate_replay(first, second) == "EXACT_REPLAY"
    assert first.calculated_amount == "50.00"
    assert first.currency == "INR"
    assert first.review_status == "APPROVED"


def test_same_identity_and_rule_but_changed_base_conflicts():
    first = build()
    second = build(calculation_base="200000.00")
    assert first.idempotency_key == second.idempotency_key
    with pytest.raises(ValueError, match="Conflicting tariff estimate replay"):
        compare_estimate_replay(first, second)


def test_changed_rule_for_same_event_is_a_conflicting_replay():
    first = build()
    second = build(make_rule(rate=Decimal("0.06")))
    assert first.idempotency_key == second.idempotency_key
    with pytest.raises(ValueError, match="Conflicting tariff estimate replay"):
        compare_estimate_replay(first, second)


@pytest.mark.parametrize("status", ["DRAFT", "REVIEWED", "REJECTED"])
def test_snapshot_rejects_unapproved_rule(status):
    with pytest.raises(ValueError, match="Only an approved tariff rule"):
        build(make_rule(review_status=status))


def test_snapshot_rejects_missing_identity():
    with pytest.raises(ValueError, match="source_identity"):
        build(source_identity=" ")


def test_snapshot_rejects_trade_date_outside_rule_validity():
    with pytest.raises(ValueError, match="not effective"):
        build(trade_date=date(2025, 12, 31))


@pytest.mark.parametrize("base", ["-1", "NaN", "Infinity", "nope"])
def test_snapshot_rejects_invalid_calculation_base(base):
    with pytest.raises(ValueError, match="Calculation base"):
        build(calculation_base=base)


def test_replay_comparison_rejects_different_idempotency_key():
    with pytest.raises(ValueError, match="keys do not match"):
        compare_estimate_replay(build(), build(source_identity="different-trade"))


def test_order_fill_set_snapshot_canonicalizes_exact_fill_identity():
    from uuid import uuid4
    fill_a, fill_b = uuid4(), uuid4()
    first = build(
        source_identity="broker-order:order-123:brokerage",
        source_trade_record_id=None,
        comparison_scope="ORDER_FILL_SET",
        source_fill_record_ids=[fill_b, fill_a],
    )
    second = build(
        source_identity="broker-order:order-123:brokerage",
        source_trade_record_id=None,
        comparison_scope="ORDER_FILL_SET",
        source_fill_record_ids=[fill_a, fill_b],
    )
    assert first.source_trade_record_id is None
    assert first.comparison_scope == "ORDER_FILL_SET"
    assert first.source_fill_ids_json == second.source_fill_ids_json
    assert first.source_fill_set_sha256 == second.source_fill_set_sha256
    assert first.canonical_json() == second.canonical_json()


def test_order_fill_set_snapshot_rejects_duplicate_fill_ids():
    from uuid import uuid4
    fill_id = uuid4()
    with pytest.raises(ValueError, match="must not contain duplicate"):
        build(
            source_identity="broker-order:duplicate:brokerage",
            source_trade_record_id=None,
            comparison_scope="ORDER_FILL_SET",
            source_fill_record_ids=[fill_id, fill_id],
        )


def test_order_fill_set_snapshot_requires_exact_fill_set():
    with pytest.raises(ValueError, match="requires a nonempty exact fill set"):
        build(
            source_identity="broker-order:missing:brokerage",
            source_trade_record_id=None,
            comparison_scope="ORDER_FILL_SET",
            source_fill_record_ids=[],
        )

def test_order_brokerage_snapshot_applies_rule_bound_cap_and_fingerprints_it():
    capped_rule = make_rule(maximum_inr=Decimal("25.00"))
    snapshot = build(capped_rule)

    assert snapshot.calculated_amount == "25.00"
    assert snapshot.maximum_inr == "25.00"
    assert snapshot.minimum_inr is None
    assert snapshot.schema_version == "tariff-estimate-snapshot-v4"

    changed_cap = build(make_rule(maximum_inr=Decimal("30.00")))
    assert snapshot.idempotency_key == changed_cap.idempotency_key
    with pytest.raises(ValueError, match="Conflicting tariff estimate replay"):
        compare_estimate_replay(snapshot, changed_cap)


def test_order_brokerage_snapshot_applies_rule_bound_minimum():
    snapshot = build(
        make_rule(minimum_inr=Decimal("20.00")),
        calculation_base="100",
    )
    assert snapshot.calculated_amount == "20.00"
    assert snapshot.minimum_inr == "20.00"

