from datetime import date
from decimal import Decimal

import pytest

from app.services.broker_gst_component_policy import GstComponentPolicy
from app.services.broker_gst_public_estimate import (
    PUBLIC_SCHEDULE_ESTIMATE_ONLY,
    calculate_public_schedule_gst_estimate,
)

SOURCE = "a" * 64


def policy(*, broker, components, ipft_mode="COMBINED", status="DRAFT"):
    return GstComponentPolicy(
        broker=broker,
        exchange="NSE",
        segment="FO",
        product="OPTIONS",
        effective_from=date(2026, 3, 1),
        effective_to=None,
        taxable_components=tuple(components),
        ipft_mode=ipft_mode,
        source_url=f"https://{broker.lower()}.example/charges",
        source_retrieved_on=date(2026, 10, 26),
        source_sha256=SOURCE,
        review_status=status,
    )


def test_draft_policy_can_only_produce_explicitly_labelled_estimate():
    candidate = policy(broker="Upstox", components=("brokerage", "exchange_charges"))
    estimate = calculate_public_schedule_gst_estimate(
        candidate,
        trade_date=date(2026, 10, 26),
        components={"brokerage": "20.00", "exchange_charges": "5.85"},
    )
    assert estimate.source_kind == PUBLIC_SCHEDULE_ESTIMATE_ONLY
    assert estimate.taxable_base == Decimal("25.85")
    assert estimate.gst_amount == Decimal("4.65")
    assert candidate.review_status == "DRAFT"
    assert not hasattr(estimate, "review_status")


def test_broker_specific_component_sets_are_not_interchangeable():
    # Test fixtures encode the differing public descriptions; they are not a
    # production-approved registry and must not be used as live accounting policy.
    zerodha = policy(
        broker="Zerodha",
        components=("brokerage", "exchange_charges", "sebi_charges"),
    )
    dhan = policy(
        broker="Dhan",
        components=("brokerage", "transaction_charges", "sebi_charges", "ipft"),
        ipft_mode="SEPARATE",
    )
    a = calculate_public_schedule_gst_estimate(
        zerodha,
        trade_date=date(2026, 10, 26),
        components={"brokerage": "20.00", "exchange_charges": "3.07", "sebi_charges": "0.10"},
    )
    b = calculate_public_schedule_gst_estimate(
        dhan,
        trade_date=date(2026, 10, 26),
        components={
            "brokerage": "20.00",
            "transaction_charges": "3.0699",
            "sebi_charges": "0.10",
            "ipft": "0.0001",
        },
    )
    assert a.taxable_base == Decimal("23.17")
    assert b.taxable_base == Decimal("23.17")
    assert a.taxable_components != b.taxable_components
    assert a.source_kind == b.source_kind == PUBLIC_SCHEDULE_ESTIMATE_ONLY


def test_public_estimate_rejects_missing_duplicate_and_unreviewed_components():
    candidate = policy(broker="Upstox", components=("brokerage", "exchange_charges"))
    with pytest.raises(ValueError, match="exactly match"):
        calculate_public_schedule_gst_estimate(
            candidate, trade_date=date(2026, 10, 26),
            components={"brokerage": "20.00"},
        )
    with pytest.raises(ValueError, match="exactly match"):
        calculate_public_schedule_gst_estimate(
            candidate, trade_date=date(2026, 10, 26),
            components={"brokerage": "20.00", "exchange_charges": "3.07", "ipft": "0.01"},
        )


def test_public_estimate_rejects_out_of_date_and_rejected_policy():
    candidate = policy(broker="Upstox", components=("brokerage", "exchange_charges"))
    with pytest.raises(ValueError, match="effective window"):
        calculate_public_schedule_gst_estimate(
            candidate, trade_date=date(2026, 2, 28),
            components={"brokerage": "20.00", "exchange_charges": "3.07"},
        )
    rejected = policy(
        broker="Upstox", components=("brokerage", "exchange_charges"), status="REJECTED"
    )
    with pytest.raises(ValueError, match="Rejected"):
        calculate_public_schedule_gst_estimate(
            rejected, trade_date=date(2026, 10, 26),
            components={"brokerage": "20.00", "exchange_charges": "3.07"},
        )


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-0.01", "not-a-number"])
def test_public_estimate_rejects_invalid_amounts(value):
    candidate = policy(broker="Upstox", components=("brokerage", "exchange_charges"))
    with pytest.raises(ValueError, match="finite nonnegative"):
        calculate_public_schedule_gst_estimate(
            candidate, trade_date=date(2026, 10, 26),
            components={"brokerage": value, "exchange_charges": "3.07"},
        )
