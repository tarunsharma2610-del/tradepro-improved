import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

import pytest

from app.services.broker_charge_representation_contract import CONTRACT_VERSION
from app.services.broker_charge_allocation_service import METHOD_VERSION
from app.services.broker_charge_canonical_allocation_plan import (
    build_verified_component_allocation_plan,
)

EVIDENCE = UUID("11111111-1111-4111-8111-111111111111")
EXTRACTOR = UUID("22222222-2222-4222-8222-222222222222")
REVIEWER = UUID("33333333-3333-4333-8333-333333333333")
SOURCE_HASH = "a" * 64
FILL_IDS = sorted([
    "44444444-4444-4444-8444-444444444444",
    "55555555-5555-4555-8555-555555555555",
])
MANIFEST = json.dumps(FILL_IDS, separators=(",", ":"))
MANIFEST_HASH = hashlib.sha256(MANIFEST.encode()).hexdigest()
WEIGHTS = json.dumps([
    {"fill_record_id": FILL_IDS[0], "weight": "1"},
    {"fill_record_id": FILL_IDS[1], "weight": "2"},
], separators=(",", ":"))


def source_rows(*, split_exchange=False):
    values = [
        ("brokerage", "20.00", "Brokerage", None, None),
        ("stt", "0.20", "STT", None, None),
        ("sebi_charges", "0.01", "SEBI Turnover", None, None),
        ("stamp_duty", "0.03", "Stamp Duty", None, None),
        ("gst", "58.91", "GST", None, None),
    ]
    if split_exchange:
        values.extend([
            ("transaction_charges", "306.99", "Transaction Charges", "SPLIT_TRANSACTION_AND_IPFT", CONTRACT_VERSION),
            ("ipft", "0.01", "IPFT", "SPLIT_TRANSACTION_AND_IPFT", CONTRACT_VERSION),
        ])
    else:
        values.append(("exchange_charges", "307.00", "Exchange Charges", None, None))
    return [
        SimpleNamespace(
            id=UUID(f"66666666-6666-4666-8666-{index:012d}"),
            evidence_id=EVIDENCE,
            source_sha256=SOURCE_HASH,
            component_name=name,
            source_label=label,
            representation_mode=mode,
            representation_contract_version=contract_version,
            revision=1,
            source_amount=Decimal(amount),
            currency="INR",
            source_locator=f"page=1,row={index}",
            status="VERIFIED",
            reviewed_by_user_id=REVIEWER,
            reviewed_at=datetime(2026, 10, 25, tzinfo=timezone.utc),
            extracted_by_user_id=EXTRACTOR,
            eligible_fill_ids_json=MANIFEST,
            eligible_fill_weights_json=WEIGHTS,
            eligible_fill_set_sha256=MANIFEST_HASH,
            allocation_basis="EXPLICIT_REVIEWED",
            rounding_policy=METHOD_VERSION,
            component_set_version="canonical-six-v1",
        )
        for index, (name, amount, label, mode, contract_version) in enumerate(values, start=1)
    ]


def test_direct_source_rows_produce_exact_non_persisted_plan():
    rows = source_rows()
    result = build_verified_component_allocation_plan(
        rows, evidence_id=EVIDENCE, source_sha256=SOURCE_HASH,
        canonical_component="brokerage",
    )
    assert result["canonical_source_total"] == "20.00"
    assert result["allocations"] == {
        FILL_IDS[0]: "6.67",
        FILL_IDS[1]: "13.33",
    }
    assert result["eligible_fill_set_sha256"] == MANIFEST_HASH
    assert result["accounting_approved"] is False
    assert result["persisted"] is False


def test_split_transaction_and_ipft_are_combined_once_before_allocation():
    rows = source_rows(split_exchange=True)
    result = build_verified_component_allocation_plan(
        rows, evidence_id=EVIDENCE, source_sha256=SOURCE_HASH,
        canonical_component="exchange_charges",
    )
    assert result["canonical_source_total"] == "307.00"
    assert sum(Decimal(value) for value in result["allocations"].values()) == Decimal("307.00")
    assert {row["component_name"] for row in result["source_record_provenance"]} == {
        "transaction_charges", "ipft"
    }
    assert len(result["source_record_provenance"]) == 2
    assert result["accounting_approved"] is False


def test_contributing_split_rows_must_share_same_fill_manifest():
    rows = source_rows(split_exchange=True)
    ipft = next(row for row in rows if row.component_name == "ipft")
    ipft.eligible_fill_ids_json = json.dumps([FILL_IDS[0]], separators=(",", ":"))
    with pytest.raises(ValueError, match="share one reviewed eligible-fill manifest"):
        build_verified_component_allocation_plan(
            rows, evidence_id=EVIDENCE, source_sha256=SOURCE_HASH,
            canonical_component="exchange_charges",
        )


def test_only_explicit_reviewed_weights_are_supported_for_plan():
    rows = source_rows()
    rows[0].allocation_basis = "QUANTITY"
    with pytest.raises(ValueError, match="EXPLICIT_REVIEWED"):
        build_verified_component_allocation_plan(
            rows, evidence_id=EVIDENCE, source_sha256=SOURCE_HASH,
            canonical_component="brokerage",
        )


def test_plan_rejects_noncanonical_or_unfingerprinted_fill_manifest():
    rows = source_rows()
    rows[0].eligible_fill_set_sha256 = "b" * 64
    with pytest.raises(ValueError, match="fingerprint does not match"):
        build_verified_component_allocation_plan(
            rows, evidence_id=EVIDENCE, source_sha256=SOURCE_HASH,
            canonical_component="brokerage",
        )
