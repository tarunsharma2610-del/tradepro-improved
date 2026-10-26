from datetime import date
from decimal import Decimal

import pytest

from app.services.broker_gst_component_policy import (
    GstComponentPolicy,
    calculate_gst_estimate,
    select_gst_component_policy,
)

SOURCE = "a" * 64


def policy(**overrides):
    values = {
        "broker": "ExampleBroker",
        "exchange": "NSE",
        "segment": "FO",
        "product": "OPTIONS",
        "effective_from": date(2026, 3, 1),
        "effective_to": None,
        "taxable_components": ("brokerage", "exchange_charges"),
        "ipft_mode": "COMBINED",
        "source_url": "https://example.invalid/tariff",
        "source_retrieved_on": date(2026, 10, 26),
        "source_sha256": SOURCE,
        "review_status": "APPROVED",
    }
    values.update(overrides)
    return GstComponentPolicy(**values)


def test_combined_ipft_policy_calculates_exchange_component_once():
    rule = policy()
    base, gst = calculate_gst_estimate(
        rule,
        components={"brokerage": Decimal("20.00"), "exchange_charges": Decimal("5.85")},
    )
    assert base == Decimal("25.85")
    assert gst == Decimal("4.65")


def test_combined_ipft_rejects_duplicate_ipft_representation():
    with pytest.raises(ValueError, match="COMBINED mode"):
        policy(taxable_components=("brokerage", "exchange_charges", "ipft"))


def test_separate_ipft_policy_requires_both_rows_and_disallows_combined_total():
    separate = policy(
        ipft_mode="SEPARATE",
        taxable_components=("brokerage", "transaction_charges", "ipft"),
    )
    base, gst = calculate_gst_estimate(
        separate,
        components={
            "brokerage": "20.00",
            "transaction_charges": "5.68",
            "ipft": "0.17",
        },
    )
    assert base == Decimal("25.85")
    assert gst == Decimal("4.65")
    with pytest.raises(ValueError, match="SEPARATE mode"):
        policy(
            ipft_mode="SEPARATE",
            taxable_components=("brokerage", "exchange_charges", "ipft"),
        )


def test_not_applicable_ipft_policy_does_not_accept_ipft_component():
    with pytest.raises(ValueError, match="NOT_APPLICABLE"):
        policy(ipft_mode="NOT_APPLICABLE", taxable_components=("brokerage", "ipft"))


def test_unapproved_policy_never_calculates_or_selects():
    draft = policy(review_status="DRAFT")
    with pytest.raises(ValueError, match="Only an approved"):
        calculate_gst_estimate(draft, components={"brokerage": "20", "exchange_charges": "1"})
    with pytest.raises(ValueError, match="No approved"):
        select_gst_component_policy(
            [draft], broker="ExampleBroker", exchange="NSE", segment="FO",
            product="OPTIONS", trade_date=date(2026, 10, 26),
        )


def test_policy_selection_requires_exact_scope_and_effective_date():
    old = policy(effective_to=date(2026, 9, 30))
    new = policy(effective_from=date(2026, 10, 1))
    assert select_gst_component_policy(
        [old, new], broker="ExampleBroker", exchange="NSE", segment="FO",
        product="OPTIONS", trade_date=date(2026, 10, 26),
    ) is new
    with pytest.raises(ValueError, match="No approved"):
        select_gst_component_policy(
            [old], broker="ExampleBroker", exchange="NSE", segment="FO",
            product="OPTIONS", trade_date=date(2026, 10, 1),
        )


def test_overlapping_approved_policies_fail_closed():
    with pytest.raises(ValueError, match="Multiple approved"):
        select_gst_component_policy(
            [policy(), policy()], broker="ExampleBroker", exchange="NSE",
            segment="FO", product="OPTIONS", trade_date=date(2026, 10, 26),
        )


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-0.01", "not-a-number"])
def test_invalid_component_amounts_are_rejected(value):
    with pytest.raises(ValueError, match="finite nonnegative"):
        calculate_gst_estimate(
            policy(), components={"brokerage": value, "exchange_charges": "1.00"}
        )


def test_taxable_component_set_must_match_exactly():
    with pytest.raises(ValueError, match="exactly match"):
        calculate_gst_estimate(
            policy(), components={"brokerage": "20.00", "exchange_charges": "1.00", "ipft": "0.01"}
        )
