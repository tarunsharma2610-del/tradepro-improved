from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from app.services.broker_tariff_rules import TariffRule
from app.brokers.upstox.reconciliation_client import ReadOnlyBrokerResult
from app.services.tariff_estimate_snapshot import (
    build_tariff_estimate_snapshot,
    build_upstox_brokerage_api_snapshots,
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


def test_flat_order_brokerage_snapshot_records_fixed_per_order_fee():
    fixed_rule = make_rule(
        calculation_basis="ORDER_FIXED",
        rate=Decimal("20.00"),
        rate_unit="INR_FIXED",
        minimum_inr=None,
        maximum_inr=None,
    )
    snapshot = build(fixed_rule, calculation_base="100000")
    assert snapshot.calculated_amount == "20.00"
    assert snapshot.calculation_basis == "ORDER_FIXED"
    assert snapshot.rate_unit == "INR_FIXED"


def test_order_brokerage_snapshot_applies_rule_bound_minimum():
    snapshot = build(
        make_rule(minimum_inr=Decimal("20.00")),
        calculation_base="100",
    )
    assert snapshot.calculated_amount == "20.00"
    assert snapshot.minimum_inr == "20.00"

def make_upstox_result(*, stt=175.0):
    return ReadOnlyBrokerResult(
        ok=True,
        data={
            "status": "success",
            "data": {
                "charges": {
                    "total": 208.27,
                    "brokerage": 0.0,
                    "taxes": {"gst": 1.02, "stt": stt, "stamp_duty": 26.23},
                    "other_charges": {
                        "transaction": 5.68,
                        "clearing": 0.0,
                        "ipft": 0.17,
                        "sebi_turnover": 0.17,
                    },
                    "dp_plan": {"name": "DP3A", "min_expense": 18.5},
                },
            },
        },
        status_code=200,
    )


def build_api_snapshots(result=None, **overrides):
    args = {
        "request_parameters": {
            "instrument_token": "NSE_FO|35271",
            "quantity": 10,
            "product": "I",
            "transaction_type": "BUY",
            "price": "1400",
        },
        "trade_date": date(2026, 10, 24),
        "source_identity": "broker-order:order-123:upstox-estimate",
        "exchange": "NSE",
        "segment": "FO",
        "product": "FUTURES_INTRADAY",
        "retrieved_at": datetime(2026, 10, 24, 10, 15, tzinfo=timezone.utc),
    }
    args.update(overrides)
    return build_upstox_brokerage_api_snapshots(result or make_upstox_result(), **args)


def test_upstox_api_estimate_normalizes_each_supported_component_with_provenance():
    snapshots = build_api_snapshots()
    by_component = {snapshot.component: snapshot for snapshot in snapshots}

    assert set(by_component) == {
        "brokerage", "stt", "stamp_duty", "gst", "exchange_charges", "sebi_charges"
    }
    assert by_component["brokerage"].calculated_amount == "0.00"
    assert by_component["stt"].calculated_amount == "175.00"
    assert by_component["stamp_duty"].calculated_amount == "26.23"
    assert by_component["gst"].calculated_amount == "1.02"
    assert by_component["exchange_charges"].calculated_amount == "5.85"
    assert by_component["sebi_charges"].calculated_amount == "0.17"
    for snapshot in snapshots:
        assert snapshot.source_kind == "UPSTOX_BROKERAGE_API_ESTIMATE"
        assert snapshot.review_status == "ESTIMATE_ONLY"
        assert snapshot.api_version == "2.0"
        assert snapshot.api_endpoint == "/v2/charges/brokerage"
        assert snapshot.api_retrieved_at == "2026-10-24T10:15:00Z"
        assert snapshot.api_response_sha256 == snapshot.source_sha256
        assert snapshot.dp_plan_name == "DP3A"
        assert snapshot.dp_plan_min_expense == "18.50"
        assert snapshot.api_total_amount == "208.27"
        assert snapshot.api_response_json is not None
        assert len(snapshot.api_response_sha256) == 64
        assert "access_token" not in (snapshot.api_request_json or "")
        assert snapshot.idempotency_key and len(snapshot.idempotency_key) == 64


def test_upstox_api_estimate_is_stable_for_exact_replay_but_response_changes_conflict():
    first = build_api_snapshots()
    replay = build_api_snapshots()
    assert [item.canonical_json() for item in first] == [item.canonical_json() for item in replay]
    assert [item.snapshot_sha256 for item in first] == [item.snapshot_sha256 for item in replay]

    changed = build_api_snapshots(make_upstox_result(stt=176.0))
    first_by_component = {item.component: item for item in first}
    changed_by_component = {item.component: item for item in changed}
    assert first_by_component["stt"].idempotency_key == changed_by_component["stt"].idempotency_key
    with pytest.raises(ValueError, match="Conflicting tariff estimate replay"):
        compare_estimate_replay(first_by_component["stt"], changed_by_component["stt"])


def test_upstox_api_estimate_rejects_failed_or_malformed_responses():
    failed = ReadOnlyBrokerResult(ok=False, error_code="UPSTREAM_SERVER_ERROR")
    with pytest.raises(ValueError, match="successful Upstox"):
        build_api_snapshots(failed)

    malformed = ReadOnlyBrokerResult(ok=True, data={"status": "success", "data": {"charges": {}}})
    with pytest.raises(ValueError, match="missing documented charge breakdown"):
        build_api_snapshots(malformed)


def test_upstox_api_estimate_rejects_invalid_order_request_parameters():
    with pytest.raises(ValueError, match="quantity, price, product, or side is invalid"):
        build_api_snapshots(request_parameters={
            "instrument_token": "NSE_FO|35271", "quantity": "0", "product": "I",
            "transaction_type": "BUY", "price": "1400",
        })
    with pytest.raises(ValueError, match="quantity, price, product, or side is invalid"):
        build_api_snapshots(request_parameters={
            "instrument_token": "NSE_FO|35271", "quantity": "10", "product": "I",
            "transaction_type": "BUY", "price": "NaN",
        })


def test_upstox_api_estimate_rejects_missing_provenance_or_naive_timestamp():
    with pytest.raises(ValueError, match="exactly the documented"):
        build_api_snapshots(request_parameters={"instrument_token": "NSE_FO|35271"})
    with pytest.raises(ValueError, match="timezone-aware"):
        build_api_snapshots(retrieved_at=datetime(2026, 10, 24, 10, 15))


def test_upstox_api_estimate_rejects_nonfinite_component_values():
    bad = make_upstox_result()
    bad.data["data"]["charges"]["taxes"]["stt"] = float("nan")
    with pytest.raises(ValueError, match="finite nonnegative"):
        build_api_snapshots(bad)
