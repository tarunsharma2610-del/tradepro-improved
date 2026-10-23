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
    ("unit", "rate", "base", "expected"),
    [
        ("PERCENT", "0.003", "100000.00", "3.00"),
        ("INR_PER_CRORE", "10", "100000.00", "0.10"),
        ("INR_FIXED", "15.50", "0", "15.50"),
        ("PERCENT", "0", "100000.00", "0.00"),
    ],
)
def test_calculate_tariff_amount_respects_declared_rate_unit(unit, rate, base, expected):
    from app.services.broker_tariff_rules import calculate_tariff_amount

    rule = make_rule(rate=Decimal(rate), rate_unit=unit)
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
