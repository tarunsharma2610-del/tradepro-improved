from datetime import date

import pytest

from app.services.broker_charge_api_mapping import ChargeApiFieldMapping
from app.services.broker_charge_api_value_resolution import resolve_charge_api_value


SOURCE_URL = "https://example.invalid/synthetic-fixture"
SOURCE_SHA256 = "c" * 64


def mapping(semantic="PER_FILL_ACTUAL", scope="contract-note-fill"):
    return ChargeApiFieldMapping(
        broker="Upstox",
        endpoint="/contract-note/charges",
        schema_version="fixture-v1",
        field_path="charges.ipft",
        semantic=semantic,
        unit="INR",
        currency="INR",
        scope=scope,
        effective_from=date(2026, 1, 1),
        effective_to=date(2026, 12, 31),
        source_url=SOURCE_URL,
        source_sha256=SOURCE_SHA256,
        review_state="APPROVED",
    )


def resolve(payload, selected_mapping, **changes):
    values = {
        "broker": "Upstox",
        "endpoint": "/contract-note/charges",
        "schema_version": "fixture-v1",
        "field_path": "charges.ipft",
        "scope": "contract-note-fill",
        "trade_date": date(2026, 10, 24),
        "intended_use": "PER_FILL_ACTUAL",
    }
    values.update(changes)
    return resolve_charge_api_value(payload, "ipft", [selected_mapping], **values)


def assert_mapping_provenance(result):
    assert result["mapping_source_url"] == SOURCE_URL
    assert result["mapping_source_sha256"] == SOURCE_SHA256
    assert result["semantic"] == "PER_FILL_ACTUAL"


def test_per_fill_actual_requires_explicit_per_fill_semantics():
    result = resolve({"ipft": "0.01"}, mapping())
    assert result["usable"] is True
    assert result["semantic"] == "PER_FILL_ACTUAL"
    assert_mapping_provenance(result)


@pytest.mark.parametrize("semantic", [
    "AGGREGATE_ACTUAL_SUMMARY", "BROKERAGE_ESTIMATE",
    "STATUTORY_CHARGE_ESTIMATE", "IPFT_ONLY",
    "COMBINED_TRANSACTION_AND_IPFT", "TRANSACTION_EXCLUDING_IPFT",
])
def test_aggregate_estimate_or_component_mapping_cannot_be_used_as_per_fill_actual(semantic):
    with pytest.raises(ValueError, match="do not permit per-fill actual"):
        resolve({"ipft": "0.01"}, mapping(semantic=semantic))


@pytest.mark.parametrize(
    ("payload", "expected_state"),
    [
        ({}, "MISSING"),
        ({"ipft": None}, "NULL"),
        ({"ipft": "NaN"}, "INVALID"),
        ({"ipft": -1}, "INVALID"),
        ({"ipft": True}, "INVALID"),
        ({"ipft": {"amount": "0.01"}}, "INVALID"),
    ],
)
def test_unusable_values_keep_mapping_provenance_without_becoming_usable(payload, expected_state):
    result = resolve(payload, mapping())
    assert result["state"] == expected_state
    assert result["usable"] is False
    assert_mapping_provenance(result)


def test_zero_is_preserved_as_present_numeric_value():
    result = resolve({"ipft": 0}, mapping())
    assert result["state"] == "ZERO"
    assert result["usable"] is True
    assert result["decimal_value"] == "0"
    assert_mapping_provenance(result)


def test_mapping_scope_and_endpoint_still_require_exact_match():
    with pytest.raises(ValueError, match="No approved API field mapping"):
        resolve({"ipft": "0.01"}, mapping(scope="aggregate-segment-fy"))
    with pytest.raises(ValueError, match="No approved API field mapping"):
        resolve({"ipft": "0.01"}, mapping(), endpoint="/v2/trade/profit-loss/charges")


@pytest.mark.parametrize("trade_date", [date(2025, 12, 31), date(2027, 1, 1)])
def test_mapping_effective_date_is_enforced(trade_date):
    with pytest.raises(ValueError, match="No approved API field mapping"):
        resolve({"ipft": "0.01"}, mapping(), trade_date=trade_date)


def test_estimate_mapping_cannot_be_used_as_per_fill_actual():
    estimate = mapping(semantic="BROKERAGE_ESTIMATE")
    with pytest.raises(ValueError, match="do not permit per-fill actual"):
        resolve({"ipft": "0.01"}, estimate)
