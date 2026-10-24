from datetime import date
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

import pytest

from app.services.broker_tariff_rules import select_tariff_rule
from app.services.upstox_tariff_candidates import (
    SOURCE_SNAPSHOT_SHA256,
    upstox_tariff_candidate_rules,
)


def test_dated_source_excerpt_payload_hash_matches_registry_fingerprint():
    repository_root = Path(__file__).resolve().parents[2]
    source_text = (repository_root / "docs/source_snapshots/UPSTOX_CHARGES_2026-10-24.md").read_text(encoding="utf-8")
    match = re.search(r"```json\n(.*?)\n```", source_text, flags=re.DOTALL)
    assert match is not None
    payload = json.loads(match.group(1))
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == SOURCE_SNAPSHOT_SHA256


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


def test_candidate_rows_have_no_overlapping_effective_windows_for_same_dimensions():
    rules = upstox_tariff_candidate_rules()
    identity_fields = (
        "component", "broker", "exchange", "segment", "product",
        "transaction_side", "calculation_basis",
    )
    grouped = {}
    for rule in rules:
        key = tuple(getattr(rule, field) for field in identity_fields)
        grouped.setdefault(key, []).append(rule)

    for key, scoped_rules in grouped.items():
        ordered = sorted(scoped_rules, key=lambda rule: rule.effective_from)
        for previous, current in zip(ordered, ordered[1:]):
            assert previous.effective_to is not None, (
                f"Open-ended candidate overlaps a later row for {key}"
            )
            assert previous.effective_to < current.effective_from, (
                f"Candidate effective windows overlap for {key}"
            )


def test_exchange_charge_candidates_remain_narrowly_scoped_and_draft():
    rules = [
        rule for rule in upstox_tariff_candidate_rules()
        if rule.component == "exchange_charges"
    ]
    assert len(rules) == 10
    assert all(rule.review_status == "DRAFT" for rule in rules)
    assert all(rule.effective_from == date(2026, 3, 1) for rule in rules)
    assert all(
        (rule.exchange, rule.segment, rule.product, rule.calculation_basis)
        in {
            ("NSE", "EQ", "DELIVERY", "TURNOVER"),
            ("NSE", "EQ", "INTRADAY", "TURNOVER"),
            ("NSE", "FO", "FUTURES", "TURNOVER"),
            ("NSE", "FO", "OPTIONS", "PREMIUM"),
            ("BSE", "FO", "OPTIONS", "PREMIUM"),
        }
        for rule in rules
    )
    # Do not silently imply these rows include or exclude IPFT. Composition
    # remains an approval gate; the registry intentionally contains no IPFT row.
    assert not any(rule.component == "ipft" for rule in upstox_tariff_candidate_rules())


def test_unresolved_charge_components_are_not_added_as_tariff_candidates():
    rules = upstox_tariff_candidate_rules()
    # Only the currently reviewed-for-research STT and exchange-charge
    # categories are inventoried. Inventory does not imply approval.
    assert {rule.component for rule in rules} == {"stt", "exchange_charges"}
    assert all(rule.review_status == "DRAFT" for rule in rules)
    # Do not introduce a generic GST base, IPFT, stamp-duty, brokerage, SEBI,
    # or DP tariff until its scope/source and calculation basis are reviewed.
    assert not any(
        rule.component in {
            "gst", "ipft", "stamp_duty", "brokerage",
            "sebi_turnover", "dp", "demat_transaction",
        }
        for rule in rules
    )
