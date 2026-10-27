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
    with pytest.raises(ValueError, match="SEPARATE IPFT mode"):
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



def test_scoped_estimate_normalizes_combined_transaction_ipft_exactly_once():
    from app.services.broker_gst_component_policy import calculate_scoped_gst_estimate

    rule = policy()
    selected, base, gst = calculate_scoped_gst_estimate(
        [rule],
        broker="ExampleBroker",
        exchange="NSE",
        segment="FO",
        product="OPTIONS",
        trade_date=date(2026, 10, 26),
        components={"brokerage": "20.00", "transaction_charges": "307.00"},
    )
    assert selected is rule
    assert base == Decimal("327.00")
    assert gst == Decimal("58.86")


def test_combined_policy_rejects_separate_ipft_and_duplicate_exchange_representation():
    from app.services.broker_gst_component_policy import resolve_gst_policy_components

    rule = policy()
    with pytest.raises(ValueError, match="must not include a separate IPFT"):
        resolve_gst_policy_components(
            rule,
            components={"brokerage": "20.00", "transaction_charges": "307.00", "ipft": "0.01"},
        )
    with pytest.raises(ValueError, match="cannot both be supplied"):
        resolve_gst_policy_components(
            rule,
            components={"brokerage": "20.00", "exchange_charges": "307.00", "transaction_charges": "307.00"},
        )


def test_separate_policy_requires_transaction_and_ipft_without_combined_total():
    from app.services.broker_gst_component_policy import resolve_gst_policy_components

    rule = policy(
        ipft_mode="SEPARATE",
        taxable_components=("brokerage", "transaction_charges", "ipft"),
    )
    resolved = resolve_gst_policy_components(
        rule,
        components={"brokerage": "20.00", "transaction_charges": "306.99", "ipft": "0.01"},
    )
    assert resolved == {"brokerage": "20.00", "transaction_charges": "306.99", "ipft": "0.01"}
    with pytest.raises(ValueError, match="cannot include combined"):
        resolve_gst_policy_components(
            rule,
            components={"brokerage": "20.00", "exchange_charges": "307.00"},
        )


def test_not_applicable_policy_normalizes_transaction_row_but_rejects_ipft():
    from app.services.broker_gst_component_policy import resolve_gst_policy_components

    rule = policy(
        exchange="BSE",
        ipft_mode="NOT_APPLICABLE",
        taxable_components=("brokerage", "exchange_charges"),
    )
    assert resolve_gst_policy_components(
        rule,
        components={"brokerage": "20.00", "transaction_charges": "2.00"},
    ) == {"brokerage": "20.00", "exchange_charges": "2.00"}
    with pytest.raises(ValueError, match="must not include an IPFT"):
        resolve_gst_policy_components(
            rule,
            components={"brokerage": "20.00", "transaction_charges": "2.00", "ipft": "0.01"},
        )


def test_scoped_estimate_does_not_reuse_policy_for_wrong_exchange_or_date():
    from app.services.broker_gst_component_policy import calculate_scoped_gst_estimate

    rule = policy()
    with pytest.raises(ValueError, match="No approved"):
        calculate_scoped_gst_estimate(
            [rule],
            broker="ExampleBroker",
            exchange="BSE",
            segment="FO",
            product="OPTIONS",
            trade_date=date(2026, 10, 26),
            components={"brokerage": "20.00", "transaction_charges": "2.00"},
        )
    with pytest.raises(ValueError, match="No approved"):
        calculate_scoped_gst_estimate(
            [rule],
            broker="ExampleBroker",
            exchange="NSE",
            segment="FO",
            product="OPTIONS",
            trade_date=date(2026, 2, 28),
            components={"brokerage": "20.00", "transaction_charges": "2.00"},
        )


def test_conflicting_source_policy_blocks_approved_candidate_until_reviewed():
    approved = policy()
    conflict = policy(review_status="CONFLICT")
    with pytest.raises(ValueError, match="Conflicting GST source policy"):
        select_gst_component_policy(
            [approved, conflict],
            broker="ExampleBroker",
            exchange="NSE",
            segment="FO",
            product="OPTIONS",
            trade_date=date(2026, 10, 26),
        )


def test_sub_paise_component_amount_is_rejected_instead_of_silently_rounded():
    with pytest.raises(ValueError, match="paise precision"):
        calculate_gst_estimate(
            policy(),
            components={"brokerage": "20.001", "exchange_charges": "1.00"},
        )


def test_zero_component_is_distinct_from_missing_component():
    rule = policy()
    base, gst = calculate_gst_estimate(
        rule,
        components={"brokerage": "20.00", "exchange_charges": "0.00"},
    )
    assert base == Decimal("20.00")
    assert gst == Decimal("3.60")
    with pytest.raises(ValueError, match="exactly"):
        calculate_gst_estimate(rule, components={"brokerage": "20.00"})


def test_unknown_component_and_nonfinite_amount_fail_closed():
    rule = policy()
    with pytest.raises(ValueError, match="exactly"):
        calculate_gst_estimate(
            rule,
            components={"brokerage": "20.00", "exchange_charges": "1.00", "ipft": "0.01"},
        )
    for invalid in ("NaN", "Infinity", "-0.01", "not-money"):
        with pytest.raises(ValueError):
            calculate_gst_estimate(
                rule,
                components={"brokerage": invalid, "exchange_charges": "1.00"},
            )


def test_effective_end_date_is_inclusive_and_expired_rule_is_not_selected():
    rule = policy(effective_to=date(2026, 10, 26))
    selected = select_gst_component_policy(
        [rule],
        broker="ExampleBroker",
        exchange="NSE",
        segment="FO",
        product="OPTIONS",
        trade_date=date(2026, 10, 26),
    )
    assert selected is rule
    with pytest.raises(ValueError, match="No approved"):
        select_gst_component_policy(
            [rule],
            broker="ExampleBroker",
            exchange="NSE",
            segment="FO",
            product="OPTIONS",
            trade_date=date(2026, 10, 27),
        )


def test_gst_rounds_once_to_paise_with_half_up_rule():
    rule = policy()
    base, gst = calculate_gst_estimate(
        rule,
        components={"brokerage": "0.03", "exchange_charges": "0.00"},
    )
    assert base == Decimal("0.03")
    # 18% of ₹0.03 is ₹0.0054; paise rounding yields ₹0.01.
    assert gst == Decimal("0.01")


def test_gst_policy_selection_does_not_fall_back_to_wrong_scope():
    approved = policy()
    for scope in (
        {"broker": "OtherBroker"},
        {"exchange": "BSE"},
        {"segment": "CM"},
        {"product": "FUTURES_INTRADAY"},
    ):
        query = {
            "broker": "ExampleBroker",
            "exchange": "NSE",
            "segment": "FO",
            "product": "OPTIONS",
            "trade_date": date(2026, 10, 27),
        }
        query.update(scope)
        with pytest.raises(ValueError, match="No approved"):
            select_gst_component_policy([approved], **query)
