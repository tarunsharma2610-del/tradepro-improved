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
