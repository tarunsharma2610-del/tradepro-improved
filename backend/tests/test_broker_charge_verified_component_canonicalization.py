from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import UUID

import pytest

from app.services.broker_charge_verified_component_canonicalization import (
    canonicalize_verified_component_records,
)

EVIDENCE_ID = UUID("11111111-1111-4111-8111-111111111111")
SOURCE_HASH = "a" * 64


def records():
    amounts = {
        "brokerage": "20.00",
        "stt": "0.20",
        "exchange_charges": "307.00",
        "sebi_charges": "0.01",
        "stamp_duty": "0.03",
        "gst": "58.91",
    }
    return [
        SimpleNamespace(
            id=UUID(f"22222222-2222-4222-8222-{index:012d}"),
            evidence_id=EVIDENCE_ID,
            source_sha256=SOURCE_HASH,
            component_name=name,
            source_label=name.replace("_", " ").title(),
            representation_mode=None,
            representation_contract_version=None,
            revision=1,
            source_amount=Decimal(amount),
            currency="INR",
            source_locator=f"page=1,row={index}",
            status="VERIFIED",
            extracted_by_user_id=UUID("44444444-4444-4444-8444-444444444444"),
            reviewed_by_user_id=UUID("33333333-3333-4333-8333-333333333333"),
            reviewed_at=datetime(2026, 10, 25, tzinfo=timezone.utc),
        )
        for index, (name, amount) in enumerate(amounts.items(), start=1)
    ]


def test_verified_rows_are_canonicalized_with_provenance_but_not_approved():
    result = canonicalize_verified_component_records(
        records(), expected_evidence_id=EVIDENCE_ID, expected_source_sha256=SOURCE_HASH
    )
    assert result["canonical_components"]["exchange_charges"] == "307.00"
    assert result["evidence_id"] == str(EVIDENCE_ID)
    assert result["source_sha256"] == SOURCE_HASH
    assert len(result["source_record_provenance"]) == 6
    assert result["accounting_approved"] is False


@pytest.mark.parametrize("field,value,match", [
    ("status", "PENDING_REVIEW", "independently VERIFIED"),
    ("currency", "USD", "Only INR"),
    ("source_sha256", "b" * 64, "hash does not match"),
    ("source_locator", "", "source locator"),
    ("reviewed_by_user_id", None, "reviewer identity"),
    ("reviewed_at", None, "reviewer identity"),
])
def test_unreviewed_or_mismatched_record_fails_closed(field, value, match):
    rows = records()
    setattr(rows[0], field, value)
    with pytest.raises(ValueError, match=match):
        canonicalize_verified_component_records(
            rows, expected_evidence_id=EVIDENCE_ID, expected_source_sha256=SOURCE_HASH
        )


def test_mixed_evidence_records_fail_closed():
    rows = records()
    rows[0].evidence_id = UUID("44444444-4444-4444-8444-444444444444")
    with pytest.raises(ValueError, match="different evidence"):
        canonicalize_verified_component_records(
            rows, expected_evidence_id=EVIDENCE_ID, expected_source_sha256=SOURCE_HASH
        )


def test_empty_or_malformed_source_hash_fails_closed():
    with pytest.raises(ValueError, match="records are required"):
        canonicalize_verified_component_records(
            [], expected_evidence_id=EVIDENCE_ID, expected_source_sha256=SOURCE_HASH
        )
    with pytest.raises(ValueError, match="64-character hexadecimal"):
        canonicalize_verified_component_records(
            records(), expected_evidence_id=EVIDENCE_ID, expected_source_sha256="not-a-hash"
        )


def test_same_user_cannot_extract_and_verify_source_component():
    rows = records()
    rows[0].extracted_by_user_id = rows[0].reviewed_by_user_id
    with pytest.raises(ValueError, match="distinct from the extractor"):
        canonicalize_verified_component_records(
            rows, expected_evidence_id=EVIDENCE_ID, expected_source_sha256=SOURCE_HASH
        )
