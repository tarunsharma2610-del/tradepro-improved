from datetime import date
from decimal import Decimal

import pytest

from app.services.broker_tariff_rules import TariffRule, select_tariff_rule


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


def select(rules, **overrides):
    args = {
        "component": "brokerage",
        "broker": "Upstox",
        "exchange": "NSE",
        "segment": "FO",
        "product": "FUTURES",
        "transaction_side": "SELL",
        "calculation_basis": "ORDER_NOTIONAL",
        "trade_date": date(2026, 10, 23),
    }
    args.update(overrides)
    return select_tariff_rule(rules, **args)


def test_selects_single_approved_rule_for_exact_scope_and_effective_date():
    rule = make_rule()
    assert select([rule]) is rule


def test_does_not_select_unreviewed_or_rejected_rule():
    for status in ("DRAFT", "REVIEWED", "REJECTED"):
        with pytest.raises(ValueError, match="No approved tariff rule"):
            select([make_rule(review_status=status)])


@pytest.mark.parametrize(
    "field,value",
    [
        ("exchange", "BSE"),
        ("segment", "EQ"),
        ("product", "OPTIONS"),
        ("transaction_side", "BUY"),
        ("calculation_basis", "PREMIUM"),
        ("component", "stt"),
    ],
)
def test_scope_mismatch_fails_closed(field, value):
    with pytest.raises(ValueError, match="No approved tariff rule"):
        select([make_rule()], **{field: value})


def test_effective_date_boundaries_are_inclusive_and_old_rule_expires():
    old = make_rule(effective_from=date(2025, 1, 1), effective_to=date(2026, 3, 31))
    new = make_rule(effective_from=date(2026, 4, 1), rate=Decimal("0.15"))
    assert select([old], trade_date=date(2026, 3, 31)) is old
    assert select([new], trade_date=date(2026, 4, 1)) is new
    with pytest.raises(ValueError, match="No approved tariff rule"):
        select([old], trade_date=date(2026, 4, 1))


def test_overlapping_approved_rules_fail_closed():
    with pytest.raises(ValueError, match="Multiple approved tariff rules overlap"):
        select([make_rule(), make_rule(rate=Decimal("0.06"))])


@pytest.mark.parametrize(
    "changes",
    [
        {"rate": Decimal("-0.01")},
        {"rate": Decimal("NaN")},
        {"rate_unit": "UNKNOWN"},
        {"effective_from": date(2026, 4, 1), "effective_to": date(2026, 3, 31)},
        {"source_sha256": "not-a-hash"},
        {"source_url": ""},
    ],
)
def test_invalid_rule_provenance_or_rate_is_rejected(changes):
    with pytest.raises(ValueError):
        make_rule(**changes)


def test_future_effective_rule_requires_explicit_approval():
    with pytest.raises(ValueError, match="requires explicit APPROVED"):
        make_rule(
            effective_from=date(2026, 12, 1),
            source_retrieved_on=date(2026, 10, 23),
            review_status="REVIEWED",
        )


@pytest.mark.parametrize(
    ("component", "basis", "unit", "rate", "base", "expected"),
    [
        ("brokerage", "ORDER_NOTIONAL", "PERCENT", "0.003", "100000.00", "3.00"),
        ("sebi_turnover", "TURNOVER", "INR_PER_CRORE", "10", "100000.00", "0.10"),
        ("other_fee", "NOTIONAL", "INR_FIXED", "15.50", "0", "15.50"),
        ("brokerage", "ORDER_NOTIONAL", "PERCENT", "0", "100000.00", "0.00"),
    ],
)
def test_calculate_tariff_amount_respects_declared_rate_unit(
    component, basis, unit, rate, base, expected
):
    from app.services.broker_tariff_rules import calculate_tariff_amount

    rule = make_rule(
        component=component,
        calculation_basis=basis,
        rate=Decimal(rate),
        rate_unit=unit,
    )
    assert calculate_tariff_amount(rule, calculation_base=base) == Decimal(expected)


@pytest.mark.parametrize("base", ["-0.01", "NaN", "Infinity", "not-a-number"])
def test_calculate_tariff_amount_rejects_invalid_bases(base):
    from app.services.broker_tariff_rules import calculate_tariff_amount

    with pytest.raises(ValueError, match="Calculation base"):
        calculate_tariff_amount(make_rule(), calculation_base=base)


def test_calculate_tariff_amount_rounds_half_up_to_paise():
    from app.services.broker_tariff_rules import calculate_tariff_amount

    rule = make_rule(rate=Decimal("0.5"), rate_unit="PERCENT")
    assert calculate_tariff_amount(rule, calculation_base="1.00") == Decimal("0.01")


@pytest.mark.parametrize("status", ["DRAFT", "REVIEWED", "REJECTED"])
def test_calculate_tariff_amount_rejects_non_approved_rule(status):
    from app.services.broker_tariff_rules import calculate_tariff_amount

    rule = make_rule(review_status=status)
    with pytest.raises(ValueError, match="Only an approved tariff rule"):
        calculate_tariff_amount(rule, calculation_base="100000")


@pytest.mark.parametrize(
    ("basis", "unit"),
    [
        ("ORDER_FIXED", "PERCENT"),
        ("ORDER_NOTIONAL", "INR_FIXED"),
    ],
)
def test_brokerage_rule_rejects_incompatible_order_basis_and_rate_unit(basis, unit):
    with pytest.raises(ValueError, match="brokerage requires"):
        make_rule(calculation_basis=basis, rate_unit=unit)


def test_trade_charge_entrypoint_selects_then_calculates_exact_rule():
    from app.services.broker_tariff_rules import calculate_charge_for_trade

    rule, amount = calculate_charge_for_trade(
        [make_rule()],
        component="brokerage",
        broker="Upstox",
        exchange="NSE",
        segment="FO",
        product="FUTURES",
        transaction_side="SELL",
        calculation_basis="ORDER_NOTIONAL",
        trade_date=date(2026, 10, 23),
        calculation_base="100000",
    )
    assert rule is not None
    assert amount == Decimal("50.00")


def test_trade_charge_entrypoint_supports_flat_fixed_order_brokerage():
    from app.services.broker_tariff_rules import calculate_charge_for_trade

    rule = make_rule(
        product="OPTIONS",
        transaction_side="BUY",
        calculation_basis="ORDER_FIXED",
        rate=Decimal("20.00"),
        rate_unit="INR_FIXED",
    )
    selected, amount = calculate_charge_for_trade(
        [rule],
        component="brokerage",
        broker="Upstox",
        exchange="NSE",
        segment="FO",
        product="OPTIONS",
        transaction_side="BUY",
        calculation_basis="ORDER_FIXED",
        trade_date=date(2026, 10, 23),
        calculation_base="100000",
    )
    assert selected is rule
    assert amount == Decimal("20.00")


def test_trade_charge_entrypoint_fails_closed_without_approved_match():
    from app.services.broker_tariff_rules import calculate_charge_for_trade

    with pytest.raises(ValueError, match="No approved tariff rule"):
        calculate_charge_for_trade(
            [make_rule(review_status="REVIEWED")],
            component="brokerage",
            broker="Upstox",
            exchange="NSE",
            segment="FO",
            product="FUTURES",
            transaction_side="SELL",
            calculation_basis="ORDER_NOTIONAL",
            trade_date=date(2026, 10, 23),
            calculation_base="100000",
        )

@pytest.mark.parametrize(
    ("order_notional", "rule_changes", "expected"),
    [
        ("100000", {}, "50.00"),
        ("100", {"minimum_inr": Decimal("20.00")}, "20.00"),
        ("1000000", {"maximum_inr": Decimal("100.00")}, "100.00"),
        ("100000", {"minimum_inr": Decimal("10.00"), "maximum_inr": Decimal("100.00")}, "50.00"),
    ],
)
def test_order_brokerage_applies_caps_bound_to_approved_rule(order_notional, rule_changes, expected):
    from app.services.broker_tariff_rules import calculate_order_brokerage

    rule = make_rule(calculation_basis="ORDER_NOTIONAL", **rule_changes)
    assert calculate_order_brokerage(rule, order_notional=order_notional) == Decimal(expected)


@pytest.mark.parametrize(
    "changes",
    [
        {"minimum_inr": "-1"},
        {"maximum_inr": "NaN"},
        {"minimum_inr": "10.005"},
        {"maximum_inr": "20.005"},
        {"minimum_inr": "20", "maximum_inr": "10"},
        {"minimum_inr": "10", "calculation_basis": "PREMIUM"},
    ],
)
def test_tariff_rule_rejects_invalid_or_inapplicable_brokerage_caps(changes):
    with pytest.raises(ValueError):
        make_rule(**changes)


def test_order_brokerage_supports_flat_fixed_fee_per_executed_order():
    from app.services.broker_tariff_rules import calculate_order_brokerage

    rule = make_rule(
        calculation_basis="ORDER_FIXED",
        rate=Decimal("20.00"),
        rate_unit="INR_FIXED",
        minimum_inr=None,
        maximum_inr=None,
    )
    assert calculate_order_brokerage(rule, order_notional="100000") == Decimal("20.00")
    assert calculate_order_brokerage(rule, order_notional="1") == Decimal("20.00")


def test_order_brokerage_requires_order_scope_and_percent_rule():
    from app.services.broker_tariff_rules import calculate_order_brokerage

    with pytest.raises(ValueError, match="ORDER_NOTIONAL"):
        calculate_order_brokerage(
            make_rule(calculation_basis="PREMIUM"),
            order_notional="1000",
        )


def test_gst_uses_only_exact_explicitly_approved_taxable_component_set():
    from app.services.broker_tariff_rules import calculate_gst_on_explicit_components

    rule = make_rule(
        component="gst",
        calculation_basis="GST_TAXABLE_COMPONENT_SUM",
        rate=Decimal("18"),
        rate_unit="PERCENT",
    )
    base, amount = calculate_gst_on_explicit_components(
        rule,
        taxable_components={"brokerage": "100.00", "exchange_charges": "20.00"},
        approved_taxable_component_names=("brokerage", "exchange_charges"),
    )
    assert base == Decimal("120.00")
    assert amount == Decimal("21.60")


@pytest.mark.parametrize(
    ("components", "approved"),
    [
        ({"brokerage": "100"}, ("brokerage", "exchange_charges")),
        ({"brokerage": "100", "stt": "5"}, ("brokerage",)),
        ({"brokerage": "100"}, ("brokerage", "brokerage")),
    ],
)
def test_gst_rejects_missing_extra_or_duplicate_taxable_component_names(components, approved):
    from app.services.broker_tariff_rules import calculate_gst_on_explicit_components

    rule = make_rule(
        component="gst",
        calculation_basis="GST_TAXABLE_COMPONENT_SUM",
        rate=Decimal("18"),
        rate_unit="PERCENT",
    )
    with pytest.raises(ValueError):
        calculate_gst_on_explicit_components(
            rule,
            taxable_components=components,
            approved_taxable_component_names=approved,
        )


def test_gst_rejects_nonapproved_rule_and_invalid_component_amount():
    from app.services.broker_tariff_rules import calculate_gst_on_explicit_components

    rule = make_rule(
        component="gst",
        calculation_basis="GST_TAXABLE_COMPONENT_SUM",
        rate=Decimal("18"),
        rate_unit="PERCENT",
    )
    with pytest.raises(ValueError, match="finite nonnegative"):
        calculate_gst_on_explicit_components(
            rule,
            taxable_components={"brokerage": "NaN"},
            approved_taxable_component_names=("brokerage",),
        )
    with pytest.raises(ValueError, match="Only an approved"):
        calculate_gst_on_explicit_components(
            make_rule(
                component="gst",
                calculation_basis="GST_TAXABLE_COMPONENT_SUM",
                rate=Decimal("18"),
                rate_unit="PERCENT",
                review_status="REVIEWED",
            ),
            taxable_components={"brokerage": "100"},
            approved_taxable_component_names=("brokerage",),
        )

@pytest.mark.parametrize(
    ("product", "basis", "base", "expected"),
    [
        ("OPTIONS", "OPTION_PREMIUM", "100000", "1.00"),
        ("FUTURES", "FUTURES_TURNOVER", "100000", "1.00"),
    ],
)
def test_stamp_duty_requires_explicit_buy_side_and_product_base(product, basis, base, expected):
    from app.services.broker_tariff_rules import calculate_stamp_duty_for_trade

    rule = make_rule(
        component="stamp_duty",
        product=product,
        transaction_side="BUY",
        calculation_basis=basis,
        rate=Decimal("0.001"),
        rate_unit="PERCENT",
    )
    assert calculate_stamp_duty_for_trade(
        rule,
        transaction_side="BUY",
        product=product,
        calculation_base=base,
    ) == Decimal(expected)


@pytest.mark.parametrize(
    ("rule_changes", "side", "product", "base", "message"),
    [
        ({"component": "stamp_duty", "transaction_side": "SELL"}, "SELL", "OPTIONS", "1000", "BUY side"),
        ({"component": "stamp_duty", "product": "OPTIONS", "transaction_side": "BUY", "calculation_basis": "FUTURES_TURNOVER"}, "BUY", "OPTIONS", "1000", "requires OPTIONS"),
        ({"component": "stamp_duty", "product": "OPTIONS", "transaction_side": "BUY", "calculation_basis": "ORDER_NOTIONAL"}, "BUY", "OPTIONS", "1000", "requires OPTIONS"),
        ({"component": "brokerage"}, "BUY", "OPTIONS", "1000", "stamp_duty"),
    ],
)
def test_stamp_duty_rejects_wrong_side_product_basis_or_component(rule_changes, side, product, base, message):
    from app.services.broker_tariff_rules import calculate_stamp_duty_for_trade

    rule = make_rule(**rule_changes)
    with pytest.raises(ValueError, match=message):
        calculate_stamp_duty_for_trade(
            rule,
            transaction_side=side,
            product=product,
            calculation_base=base,
        )

def test_trade_charge_entrypoint_applies_caps_from_selected_brokerage_rule():
    from app.services.broker_tariff_rules import calculate_charge_for_trade

    rule = make_rule(
        calculation_basis="ORDER_NOTIONAL",
        maximum_inr=Decimal("25.00"),
    )
    selected, amount = calculate_charge_for_trade(
        [rule],
        component="brokerage",
        broker="Upstox",
        exchange="NSE",
        segment="FO",
        product="FUTURES",
        transaction_side="SELL",
        calculation_basis="ORDER_NOTIONAL",
        trade_date=date(2026, 10, 23),
        calculation_base="100000",
    )
    assert selected.maximum_inr == Decimal("25.00")
    assert amount == Decimal("25.00")



@pytest.mark.parametrize(
    ("notional", "minimum", "maximum", "expected"),
    [
        ("10000", None, Decimal("20.00"), "10.00"),
        ("100000", None, Decimal("20.00"), "20.00"),
        ("1000", Decimal("5.00"), Decimal("20.00"), "5.00"),
        ("100000", Decimal("5.00"), Decimal("20.00"), "20.00"),
    ],
)
def test_order_brokerage_applies_percentage_then_minimum_and_maximum_caps(
    notional, minimum, maximum, expected
):
    from app.services.broker_tariff_rules import calculate_order_brokerage

    rule = make_rule(
        calculation_basis="ORDER_NOTIONAL",
        rate=Decimal("0.1"),
        minimum_inr=minimum,
        maximum_inr=maximum,
    )
    assert calculate_order_brokerage(rule, order_notional=notional) == Decimal(expected)


def test_fixed_order_brokerage_is_flat_and_rejects_caps():
    from app.services.broker_tariff_rules import calculate_order_brokerage

    rule = make_rule(
        calculation_basis="ORDER_FIXED",
        rate_unit="INR_FIXED",
        rate=Decimal("20.00"),
    )
    assert calculate_order_brokerage(rule, order_notional="1000000") == Decimal("20.00")

    # Rule validation must reject caps on fixed-fee rules before calculation.
    with pytest.raises(
        ValueError,
        match="caps are supported only for order-notional percentage brokerage rules",
    ):
        make_rule(
            calculation_basis="ORDER_FIXED",
            rate_unit="INR_FIXED",
            rate=Decimal("20.00"),
            maximum_inr=Decimal("15.00"),
        )


def test_generic_calculator_rejects_special_or_unknown_calculation_shapes():
    from app.services.broker_tariff_rules import calculate_tariff_amount

    special_rules = [
        make_rule(component="gst", calculation_basis="GST_TAXABLE_COMPONENT_SUM"),
        make_rule(component="stamp_duty", transaction_side="BUY", product="OPTIONS",
                  calculation_basis="OPTION_PREMIUM"),
        make_rule(calculation_basis="LESSER_OF_PREMIUM_OR_NOTIONAL"),
    ]
    for rule in special_rules:
        with pytest.raises(ValueError, match="Unsupported tariff calculation shape"):
            calculate_tariff_amount(rule, calculation_base="100000")


def test_trade_entrypoint_routes_stamp_duty_through_side_and_product_guards():
    from app.services.broker_tariff_rules import calculate_charge_for_trade

    rule = make_rule(
        component="stamp_duty",
        transaction_side="BUY",
        product="OPTIONS",
        calculation_basis="OPTION_PREMIUM",
        rate=Decimal("0.001"),
    )
    common = dict(
        rules=[rule],
        component="stamp_duty",
        broker="Upstox",
        exchange="NSE",
        segment="FO",
        product="OPTIONS",
        calculation_basis="OPTION_PREMIUM",
        trade_date=date(2026, 10, 23),
        calculation_base="100000",
    )
    selected, amount = calculate_charge_for_trade(transaction_side="BUY", **common)
    assert selected is rule
    assert amount == Decimal("1.00")

    with pytest.raises(ValueError, match="BUY side"):
        calculate_charge_for_trade(transaction_side="SELL", **common)


def test_trade_entrypoint_rejects_gst_without_explicit_taxable_component_set():
    from app.services.broker_tariff_rules import calculate_charge_for_trade

    rule = make_rule(
        component="gst",
        calculation_basis="GST_TAXABLE_COMPONENT_SUM",
        rate=Decimal("18"),
        rate_unit="PERCENT",
    )
    with pytest.raises(ValueError, match="explicit component set"):
        calculate_charge_for_trade(
            [rule],
            component="gst",
            broker="Upstox",
            exchange="NSE",
            segment="FO",
            product="FUTURES",
            transaction_side="SELL",
            calculation_basis="GST_TAXABLE_COMPONENT_SUM",
            trade_date=date(2026, 10, 23),
            calculation_base="100000",
        )


@pytest.mark.parametrize("rate_unit", ["INR_FIXED", "INR_PER_CRORE"])
def test_brokerage_caps_reject_nonpercentage_rate_units(rate_unit):
    with pytest.raises(ValueError, match="order-notional percentage brokerage"):
        make_rule(
            component="brokerage",
            calculation_basis="ORDER_NOTIONAL",
            rate_unit=rate_unit,
            minimum_inr=Decimal("1.00"),
        )


@pytest.mark.parametrize("rate_unit", ["INR_FIXED", "INR_PER_CRORE"])
def test_stamp_duty_rejects_nonpercentage_rate_units(rate_unit):
    from app.services.broker_tariff_rules import calculate_stamp_duty_for_trade

    rule = make_rule(
        component="stamp_duty",
        transaction_side="BUY",
        product="OPTIONS",
        calculation_basis="OPTION_PREMIUM",
        rate_unit=rate_unit,
    )
    with pytest.raises(ValueError, match="percentage-based"):
        calculate_stamp_duty_for_trade(
            rule,
            transaction_side="BUY",
            product="OPTIONS",
            calculation_base="100000",
        )


@pytest.mark.parametrize(
    "component",
    [
        "stt",
        "ctt",
        "dp",
        "dp_charge",
        "dp_charges",
        "demat_transaction_charge",
        "depository_participant_charge",
    ],
)
def test_generic_calculator_rejects_conditional_tax_and_depository_components(component):
    from app.services.broker_tariff_rules import calculate_tariff_amount

    rule = make_rule(
        component=component,
        calculation_basis="NOTIONAL",
        rate=Decimal("0.1"),
        rate_unit="PERCENT",
    )
    with pytest.raises(ValueError, match="Unsupported tariff calculation shape"):
        calculate_tariff_amount(rule, calculation_base="100000")


def test_upstox_nse_exchange_candidates_are_combined_rates_and_remain_draft():
    from app.services.upstox_tariff_candidates import upstox_tariff_candidate_rules

    rules = [
        rule for rule in upstox_tariff_candidate_rules()
        if rule.component == "exchange_charges"
        and rule.exchange == "NSE"
        and rule.effective_from == date(2026, 3, 1)
    ]
    keyed = {
        (rule.segment, rule.product, rule.calculation_basis): rule
        for rule in rules
    }

    assert keyed[("EQ", "DELIVERY", "TURNOVER")].rate == Decimal("0.00307")
    assert keyed[("FO", "FUTURES", "TURNOVER")].rate == Decimal("0.00183")
    assert keyed[("FO", "OPTIONS", "PREMIUM")].rate == Decimal("0.03553")
    assert all(rule.review_status == "DRAFT" for rule in rules)
    # Rates are the published combined totals; do not model a second IPFT rule
    # on top of these same turnover/premium bases.
    assert not any(rule.component.lower() == "ipft" for rule in rules)


def test_upstox_nse_combined_and_split_ipft_representations_reconcile_before_gst():
    # NSE's circular defines these as equivalent combined member outflows:
    # ₹307/crore = ₹306.99/crore transaction charge + ₹0.01/crore IPFT.
    # This is representation arithmetic only. It does NOT approve either
    # representation for GST taxable-base inclusion; that requires reviewed
    # tax/invoice evidence under the component acceptance matrix.
    combined_exchange_outflow = Decimal("307.00")
    split_exchange_outflow = Decimal("306.99") + Decimal("0.01")

    assert combined_exchange_outflow == split_exchange_outflow

def test_gst_arithmetic_is_invariant_for_combined_vs_split_ipft_representation():
    from app.services.broker_tariff_rules import calculate_gst_on_explicit_components

    # Synthetic arithmetic only: equivalent ₹307.00 exchange outflow should
    # yield the same 18% GST amount whether represented as combined or split.
    # This does not approve either component set for actual taxable-base use.
    rule = make_rule(
        component="gst",
        calculation_basis="GST_TAXABLE_COMPONENT_SUM",
        rate=Decimal("18"),
        rate_unit="PERCENT",
        review_status="APPROVED",
    )
    combined_base, combined_gst = calculate_gst_on_explicit_components(
        rule,
        taxable_components={"exchange_charges": "307.00"},
        approved_taxable_component_names=("exchange_charges",),
    )
    split_base, split_gst = calculate_gst_on_explicit_components(
        rule,
        taxable_components={"transaction_charges": "306.99", "ipft": "0.01"},
        approved_taxable_component_names=("transaction_charges", "ipft"),
    )

    assert combined_base == split_base == Decimal("307.00")
    assert combined_gst == split_gst == Decimal("55.26")




def test_upstox_gst_component_sets_are_source_backed_and_remain_draft():
    from app.services.upstox_tariff_candidates import upstox_gst_component_set_candidates

    candidates = upstox_gst_component_set_candidates()
    assert {(item.segment, item.product) for item in candidates} == {
        ("EQ", "DELIVERY"),
        ("EQ", "INTRADAY"),
        ("FO", "FUTURES"),
        ("FO", "OPTIONS"),
    }
    assert all(item.review_status == "DRAFT" for item in candidates)
    assert all(item.rate_percent == "18" for item in candidates)
    assert all(item.source_url == "https://upstox.com/brokerage-charges/" for item in candidates)
    assert all(item.source_snapshot_sha256 for item in candidates)
    by_product = {(item.segment, item.product): item for item in candidates}
    assert by_product[("EQ", "DELIVERY")].taxable_components == (
        "brokerage", "exchange_charges", "demat_charges"
    )
    for key in (("EQ", "INTRADAY"), ("FO", "FUTURES"), ("FO", "OPTIONS")):
        assert by_product[key].taxable_components == ("brokerage", "exchange_charges")
    # IPFT is already part of the canonical combined exchange-charge component.
    assert all("ipft" not in item.taxable_components for item in candidates)
    assert all(
        excluded not in item.taxable_components
        for item in candidates
        for excluded in ("stt", "stamp_duty", "sebi_charges")
    )



def test_upstox_nse_exchange_candidates_do_not_leak_into_bse_or_mcx():
    from app.services.upstox_tariff_candidates import upstox_tariff_candidate_rules

    rules = [
        rule for rule in upstox_tariff_candidate_rules()
        if rule.component == "exchange_charges"
        and rule.effective_from == date(2026, 3, 1)
    ]
    nse_equity_scope = {
        (rule.exchange, rule.segment, rule.product)
        for rule in rules
        if rule.exchange == "NSE"
    }
    assert nse_equity_scope == {
        ("NSE", "EQ", "DELIVERY"),
        ("NSE", "EQ", "INTRADAY"),
        ("NSE", "FO", "FUTURES"),
        ("NSE", "FO", "OPTIONS"),
    }
    assert not any(rule.exchange == "MCX" for rule in rules)
    assert all(rule.review_status == "DRAFT" for rule in rules)


@pytest.mark.parametrize(
    ("product", "side", "basis", "segment", "rate", "base", "expected"),
    [
        ("FUTURES", "SELL", "TURNOVER", "FO", "0.05", "1000000", "500.00"),
        ("OPTIONS", "SELL", "PREMIUM", "FO", "0.15", "100000", "150.00"),
        ("OPTIONS_EXERCISED", "BUY", "INTRINSIC_VALUE", "FO", "0.15", "100000", "150.00"),
        ("DELIVERY", "BUY", "TURNOVER", "EQ", "0.1", "100000", "100.00"),
    ],
)
def test_stt_specialized_calculator_requires_and_applies_exact_rule_shape(
    product, side, basis, segment, rate, base, expected
):
    from app.services.broker_tariff_rules import calculate_stt_for_trade

    rule = make_rule(
        component="stt",
        product=product,
        transaction_side=side,
        calculation_basis=basis,
        segment=segment,
        rate=Decimal(rate),
        rate_unit="PERCENT",
    )
    assert calculate_stt_for_trade(
        rule, product=product, transaction_side=side, calculation_base=base
    ) == Decimal(expected)


def test_stt_specialized_calculator_rejects_wrong_side_product_or_unreviewed_rule():
    from app.services.broker_tariff_rules import calculate_stt_for_trade

    rule = make_rule(
        component="stt", product="FUTURES", transaction_side="SELL",
        calculation_basis="TURNOVER", segment="FO",
    )
    with pytest.raises(ValueError, match="product and transaction side"):
        calculate_stt_for_trade(
            rule, product="FUTURES", transaction_side="BUY", calculation_base="100000"
        )
    with pytest.raises(ValueError, match="approved tariff rule"):
        calculate_stt_for_trade(
            make_rule(
                component="stt", product="FUTURES", transaction_side="SELL",
                calculation_basis="TURNOVER", segment="FO", review_status="DRAFT",
            ),
            product="FUTURES", transaction_side="SELL", calculation_base="100000",
        )


@pytest.mark.parametrize(
    ("notional", "cap", "weights", "expected"),
    [
        (
            "1000000", "20.00", {"fill-a": "1", "fill-b": "1"},
            {"fill-a": Decimal("10.00"), "fill-b": Decimal("10.00")},
        ),
        (
            "100000", "25.00", {"fill-a": "1", "fill-b": "3"},
            {"fill-a": Decimal("6.25"), "fill-b": Decimal("18.75")},
        ),
    ],
)
def test_multi_fill_brokerage_cap_is_applied_once_before_reviewed_allocation(
    notional, cap, weights, expected
):
    from app.services.broker_tariff_rules import calculate_order_brokerage_allocation

    rule = make_rule(rate=Decimal("0.1"), maximum_inr=Decimal(cap))
    allocations = calculate_order_brokerage_allocation(
        rule, order_notional=notional, reviewed_fill_weights=weights
    )
    assert allocations == expected
    assert sum(allocations.values(), Decimal("0")) == Decimal(cap)


def test_multi_fill_brokerage_allocation_is_paise_exact_and_stable_for_ties():
    from app.services.broker_tariff_rules import calculate_order_brokerage_allocation

    rule = make_rule(calculation_basis="ORDER_FIXED", rate=Decimal("0.05"), rate_unit="INR_FIXED")
    weights = {"fill-b": "1", "fill-a": "1", "fill-c": "1"}
    first = calculate_order_brokerage_allocation(
        rule, order_notional="100000", reviewed_fill_weights=weights
    )
    second = calculate_order_brokerage_allocation(
        rule, order_notional="100000", reviewed_fill_weights=dict(reversed(list(weights.items())))
    )
    assert first == second
    assert first == {"fill-a": Decimal("0.02"), "fill-b": Decimal("0.02"), "fill-c": Decimal("0.01")}
    assert sum(first.values(), Decimal("0")) == Decimal("0.05")


@pytest.mark.parametrize("weights", [{}, {"fill-a": "0", "fill-b": "0"}, {"fill-a": "-1"}])
def test_multi_fill_brokerage_allocation_rejects_empty_or_invalid_weights(weights):
    from app.services.broker_tariff_rules import calculate_order_brokerage_allocation

    with pytest.raises(ValueError):
        calculate_order_brokerage_allocation(
            make_rule(), order_notional="100000", reviewed_fill_weights=weights
        )


def test_multi_fill_brokerage_allocation_rejects_unapproved_tariff():
    from app.services.broker_tariff_rules import calculate_order_brokerage_allocation

    with pytest.raises(ValueError, match="Only an approved tariff rule"):
        calculate_order_brokerage_allocation(
            make_rule(review_status="DRAFT"),
            order_notional="100000",
            reviewed_fill_weights={"fill-a": "1", "fill-b": "1"},
        )


@pytest.mark.parametrize("amount", ["100.001", "0.009", "-0.01", "NaN", "Infinity"])
def test_gst_rejects_component_amounts_not_valid_inr_paise(amount):
    from app.services.broker_tariff_rules import calculate_gst_on_explicit_components

    rule = make_rule(
        component="gst", calculation_basis="GST_TAXABLE_COMPONENT_SUM",
        rate=Decimal("18"), rate_unit="PERCENT",
    )
    with pytest.raises(ValueError):
        calculate_gst_on_explicit_components(
            rule, taxable_components={"brokerage": amount},
            approved_taxable_component_names=("brokerage",),
        )


@pytest.mark.parametrize("rate", ["0", "5", "100", "100.01"])
def test_gst_rejects_rates_other_than_supported_18_percent(rate):
    from app.services.broker_tariff_rules import calculate_gst_on_explicit_components

    rule = make_rule(
        component="gst", calculation_basis="GST_TAXABLE_COMPONENT_SUM",
        rate=Decimal(rate), rate_unit="PERCENT",
    )
    with pytest.raises(ValueError, match="require an 18 percent rate"):
        calculate_gst_on_explicit_components(
            rule, taxable_components={"brokerage": "100.00"},
            approved_taxable_component_names=("brokerage",),
        )


@pytest.mark.parametrize("base", ["100.001", "0.009", "-0.01", "NaN", "Infinity"])
def test_stamp_duty_rejects_invalid_or_subpaise_base(base):
    from app.services.broker_tariff_rules import calculate_stamp_duty_for_trade

    rule = make_rule(
        component="stamp_duty", product="OPTIONS", transaction_side="BUY",
        calculation_basis="OPTION_PREMIUM", rate=Decimal("0.001"), rate_unit="PERCENT",
    )
    with pytest.raises(ValueError):
        calculate_stamp_duty_for_trade(
            rule, transaction_side="BUY", product="OPTIONS", calculation_base=base,
        )


@pytest.mark.parametrize("rate", ["100.01"])
def test_stamp_duty_rejects_out_of_range_percentage(rate):
    from app.services.broker_tariff_rules import calculate_stamp_duty_for_trade

    rule = make_rule(
        component="stamp_duty", product="OPTIONS", transaction_side="BUY",
        calculation_basis="OPTION_PREMIUM", rate=Decimal(rate), rate_unit="PERCENT",
    )
    with pytest.raises(ValueError, match="Stamp duty rate percent"):
        calculate_stamp_duty_for_trade(
            rule, transaction_side="BUY", product="OPTIONS", calculation_base="100.00",
        )

@pytest.mark.parametrize(
    ("kwargs", "expected_mode", "expected_total"),
    [
        ({"igst": "18.00"}, "IGST", Decimal("18.00")),
        ({"cgst": "9.00", "sgst": "9.00"}, "CGST_SGST", Decimal("18.00")),
        ({"cgst": "9.01", "sgst": "8.99"}, "CGST_SGST", Decimal("18.00")),
    ],
)
def test_aggregate_gst_invoice_components_accepts_one_valid_tax_mode(
    kwargs, expected_mode, expected_total
):
    from app.services.broker_tariff_rules import aggregate_gst_invoice_components

    assert aggregate_gst_invoice_components(**kwargs) == (expected_mode, expected_total)


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"cgst": "9.00"},
        {"sgst": "9.00"},
        {"igst": "18.00", "cgst": "9.00", "sgst": "9.00"},
        {"igst": "18.00", "cgst": "0.00"},
        {"igst": "-0.01"},
        {"igst": "NaN"},
        {"cgst": "1.001", "sgst": "1.00"},
    ],
)
def test_aggregate_gst_invoice_components_rejects_ambiguous_or_invalid_lines(kwargs):
    from app.services.broker_tariff_rules import aggregate_gst_invoice_components

    with pytest.raises(ValueError):
        aggregate_gst_invoice_components(**kwargs)

def make_ipft_rule(*, effective_from, effective_to, rate, source_url):
    return make_rule(
        component="ipft",
        exchange="NSE",
        segment="FO",
        product="OPTIONS",
        transaction_side="BUY",
        calculation_basis="PREMIUM",
        rate=Decimal(rate),
        rate_unit="INR_PER_CRORE",
        effective_from=effective_from,
        effective_to=effective_to,
        source_url=source_url,
        source_retrieved_on=date(2026, 10, 27),
    )


def test_ipft_estimate_selects_historical_rate_for_january_2023_options():
    from app.services.broker_tariff_rules import calculate_ipft_estimate_for_scope

    pre_april_2023 = make_ipft_rule(
        effective_from=date(2022, 1, 1),
        effective_to=date(2023, 3, 31),
        rate="0.01",
        source_url="https://nsearchives.nseindia.com/content/circulars/FA56129.pdf",
    )
    revised_2023 = make_ipft_rule(
        effective_from=date(2023, 4, 1),
        effective_to=date(2026, 2, 28),
        rate="50",
        source_url="https://nsearchives.nseindia.com/content/circulars/FA56129.pdf",
    )
    rollback_2026 = make_ipft_rule(
        effective_from=date(2026, 3, 1),
        effective_to=None,
        rate="0.01",
        source_url="https://nsearchives.nseindia.com/content/circulars/FA73061.pdf",
    )
    selected, amount = calculate_ipft_estimate_for_scope(
        [pre_april_2023, revised_2023, rollback_2026],
        broker="Upstox",
        exchange="NSE",
        segment="FO",
        product="OPTIONS",
        transaction_side="BUY",
        trade_date=date(2023, 1, 23),
        premium_value_base="100000000",
    )
    assert selected is pre_april_2023
    assert amount == Decimal("0.10")


@pytest.mark.parametrize(
    ("trade_date", "expected_rate", "expected_amount"),
    [
        (date(2023, 3, 31), Decimal("0.01"), Decimal("0.10")),
        (date(2023, 4, 1), Decimal("50"), Decimal("500.00")),
        (date(2026, 2, 28), Decimal("50"), Decimal("500.00")),
        (date(2026, 3, 1), Decimal("0.01"), Decimal("0.10")),
    ],
)
def test_ipft_effective_date_boundaries_do_not_apply_current_rate_retroactively(
    trade_date, expected_rate, expected_amount
):
    from app.services.broker_tariff_rules import calculate_ipft_estimate_for_scope

    rules = [
        make_ipft_rule(
            effective_from=date(2022, 1, 1),
            effective_to=date(2023, 3, 31),
            rate="0.01",
            source_url="https://nsearchives.nseindia.com/content/circulars/FA56129.pdf",
        ),
        make_ipft_rule(
            effective_from=date(2023, 4, 1),
            effective_to=date(2026, 2, 28),
            rate="50",
            source_url="https://nsearchives.nseindia.com/content/circulars/FA56129.pdf",
        ),
        make_ipft_rule(
            effective_from=date(2026, 3, 1),
            effective_to=None,
            rate="0.01",
            source_url="https://nsearchives.nseindia.com/content/circulars/FA73061.pdf",
        ),
    ]
    selected, amount = calculate_ipft_estimate_for_scope(
        rules,
        broker="Upstox",
        exchange="NSE",
        segment="FO",
        product="OPTIONS",
        transaction_side="BUY",
        trade_date=trade_date,
        premium_value_base="100000000",
    )
    assert selected.rate == expected_rate
    assert amount == expected_amount


def test_ipft_estimate_fails_closed_for_wrong_product_or_unapproved_rule():
    from app.services.broker_tariff_rules import calculate_ipft_estimate_for_scope

    rule = make_ipft_rule(
        effective_from=date(2022, 1, 1),
        effective_to=None,
        rate="0.01",
        source_url="https://nsearchives.nseindia.com/content/circulars/FA56129.pdf",
    )
    args = {
        "broker": "Upstox",
        "exchange": "NSE",
        "segment": "FO",
        "product": "OPTIONS",
        "transaction_side": "BUY",
        "trade_date": date(2023, 1, 23),
        "premium_value_base": "100000000",
    }
    with pytest.raises(ValueError, match="only NSE equity options"):
        calculate_ipft_estimate_for_scope([rule], **{**args, "product": "FUTURES"})
    with pytest.raises(ValueError, match="No approved tariff rule"):
        calculate_ipft_estimate_for_scope(
            [make_ipft_rule(
                effective_from=date(2022, 1, 1),
                effective_to=None,
                rate="0.01",
                source_url="https://nsearchives.nseindia.com/content/circulars/FA56129.pdf",
            ) if False else make_ipft_rule(
                effective_from=date(2022, 1, 1),
                effective_to=None,
                rate="0.01",
                source_url="https://nsearchives.nseindia.com/content/circulars/FA56129.pdf",
            )],
            **args,
        )


def test_generic_tariff_calculator_cannot_bypass_ipft_guard():
    from app.services.broker_tariff_rules import calculate_tariff_amount

    rule = make_ipft_rule(
        effective_from=date(2022, 1, 1),
        effective_to=None,
        rate="0.01",
        source_url="https://nsearchives.nseindia.com/content/circulars/FA56129.pdf",
    )
    with pytest.raises(ValueError, match="Unsupported tariff calculation shape"):
        calculate_tariff_amount(rule, calculation_base="100000000")
