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


def test_changed_rule_fingerprint_changes_idempotency_key():
    first = build()
    second = build(make_rule(rate=Decimal("0.06")))
    assert first.idempotency_key != second.idempotency_key
    with pytest.raises(ValueError, match="keys do not match"):
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
