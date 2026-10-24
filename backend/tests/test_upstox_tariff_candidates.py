from datetime import date
from decimal import Decimal

import pytest

from app.services.broker_tariff_rules import select_tariff_rule
from app.services.upstox_tariff_candidates import (
    SOURCE_SNAPSHOT_SHA256,
    upstox_tariff_candidate_rules,
)


def test_candidate_registry_is_source_fingerprinted_and_all_draft():
    rules = upstox_tariff_candidate_rules()
    assert len(rules) == 18
    assert all(rule.review_status == "DRAFT" for rule in rules)
    assert all(rule.source_sha256 == SOURCE_SNAPSHOT_SHA256 for rule in rules)


def test_stt_effective_date_transition_has_no_gap_or_overlap_in_candidate_rows():
    rules = [
        rule for rule in upstox_tariff_candidate_rules()
        if rule.component == "stt"
        and rule.segment == "FO"
        and rule.product == "FUTURES"
        and rule.transaction_side == "SELL"
    ]
    old = [
        rule for rule in rules
        if rule.effective_to is not None
        and rule.effective_from <= date(2026, 3, 31) <= rule.effective_to
    ]
    new = [
        rule for rule in rules
        if rule.effective_from <= date(2026, 4, 1)
        and (rule.effective_to is None or date(2026, 4, 1) <= rule.effective_to)
    ]
    assert len(old) == 1 and old[0].rate == Decimal("0.02")
    assert len(new) == 1 and new[0].rate == Decimal("0.05")


def test_draft_candidates_are_never_selectable_for_calculation():
    with pytest.raises(ValueError, match="No approved tariff rule"):
        select_tariff_rule(
            upstox_tariff_candidate_rules(),
            component="stt",
            broker="Upstox",
            exchange="NSE",
            segment="FO",
            product="FUTURES",
            transaction_side="SELL",
            calculation_basis="TURNOVER",
            trade_date=date(2026, 4, 1),
        )


def test_exercised_option_stt_has_separate_intrinsic_value_and_buyer_scope():
    matches = [
        rule for rule in upstox_tariff_candidate_rules()
        if rule.component == "stt" and rule.product == "OPTIONS_EXERCISED"
    ]
    assert len(matches) == 1
    rule = matches[0]
    assert rule.transaction_side == "BUY"
    assert rule.calculation_basis == "INTRINSIC_VALUE"
    assert rule.rate == Decimal("0.15")
    assert rule.review_status == "DRAFT"
