from dataclasses import replace
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


@pytest.mark.parametrize(
    ("semantic", "intended_use"),
    [
        ("AGGREGATE_ACTUAL_SUMMARY", "ESTIMATE"),
        ("PER_FILL_ACTUAL", "ESTIMATE"),
        ("PER_FILL_ACTUAL", "AGGREGATE_SUMMARY"),
        ("IPFT_ONLY", "AGGREGATE_SUMMARY"),
        ("COMBINED_TRANSACTION_AND_IPFT", "AGGREGATE_SUMMARY"),
        ("BROKERAGE_ESTIMATE", "AGGREGATE_SUMMARY"),
        ("STATUTORY_CHARGE_ESTIMATE", "AGGREGATE_SUMMARY"),
    ],
)
def test_mapping_semantics_cannot_be_relabelled_for_another_intended_use(semantic, intended_use):
    with pytest.raises(ValueError, match="do not permit"):
        resolve(
            {"ipft": "0.01"},
            mapping(semantic=semantic),
            intended_use=intended_use,
        )


@pytest.mark.parametrize(
    ("semantic", "intended_use"),
    [
        ("AGGREGATE_ACTUAL_SUMMARY", "AGGREGATE_SUMMARY"),
        ("BROKERAGE_ESTIMATE", "ESTIMATE"),
        ("STATUTORY_CHARGE_ESTIMATE", "ESTIMATE"),
    ],
)
def test_supported_non_per_fill_use_requires_matching_mapping_semantics(semantic, intended_use):
    result = resolve(
        {"ipft": "0.01"},
        mapping(semantic=semantic),
        intended_use=intended_use,
    )
    assert result["usable"] is True
    assert result["semantic"] == semantic


def test_unknown_intended_use_is_rejected():
    with pytest.raises(ValueError, match="Unsupported intended use"):
        resolve({"ipft": "0.01"}, mapping(), intended_use="POSITION_COST")


@pytest.mark.parametrize(
    ("mapping_change", "argument_change"),
    [
        ({"broker": "OtherBroker"}, {}),
        ({"endpoint": "/different/endpoint"}, {}),
        ({"schema_version": "fixture-v2"}, {}),
        ({"field_path": "charges.other"}, {}),
        ({}, {"broker": "OtherBroker"}),
        ({}, {"schema_version": "fixture-v2"}),
        ({}, {"field_path": "charges.other"}),
        ({}, {"scope": "aggregate-segment-fy"}),
    ],
)
def test_exact_mapping_identity_must_match_every_dimension(mapping_change, argument_change):
    selected = replace(mapping(), **mapping_change)
    with pytest.raises(ValueError, match="No approved API field mapping"):
        resolve({"ipft": "0.01"}, selected, **argument_change)


@pytest.mark.parametrize("value", ["Infinity", "-Infinity", float("inf"), float("-inf")])
def test_non_finite_charge_values_are_rejected(value):
    result = resolve({"ipft": value}, mapping())
    assert result["state"] == "INVALID"
    assert result["usable"] is False
    assert_mapping_provenance(result)


def test_payload_field_must_match_approved_mapping_field_path():
    with pytest.raises(ValueError, match="does not match the approved mapping field path"):
        resolve_charge_api_value(
            {"brokerage": "20.00"},
            "brokerage",
            [mapping()],
            broker="Upstox",
            endpoint="/contract-note/charges",
            schema_version="fixture-v1",
            field_path="charges.ipft",
            scope="contract-note-fill",
            trade_date=date(2026, 10, 24),
            intended_use="PER_FILL_ACTUAL",
        )


def test_official_upstox_aggregate_charges_endpoint_cannot_be_promoted_to_per_fill():
    aggregate_mapping = replace(
        mapping(),
        endpoint="/v2/trade/profit-loss/charges",
        scope="contract-note-fill",
        field_path="charges.ipft",
    )
    with pytest.raises(ValueError, match="Aggregate-only broker endpoint"):
        resolve(
            {"ipft": "0.01"},
            aggregate_mapping,
            endpoint="/v2/trade/profit-loss/charges",
        )


def test_official_upstox_brokerage_calculator_cannot_be_promoted_to_per_fill_actual():
    estimate_mapping = replace(
        mapping(),
        endpoint="/v2/charges/brokerage",
        semantic="PER_FILL_ACTUAL",
        scope="contract-note-fill",
    )
    with pytest.raises(ValueError, match="Estimate-only broker endpoint"):
        resolve(
            {"ipft": "0.17"},
            estimate_mapping,
            endpoint="/v2/charges/brokerage",
        )


def test_official_upstox_brokerage_calculator_cannot_be_used_as_actual_aggregate():
    estimate_mapping = replace(
        mapping(),
        endpoint="/v2/charges/brokerage",
        semantic="AGGREGATE_ACTUAL_SUMMARY",
        scope="contract-note-fill",
    )
    with pytest.raises(ValueError, match="Estimate-only broker endpoint"):
        resolve(
            {"ipft": "0.17"},
            estimate_mapping,
            endpoint="/v2/charges/brokerage",
            intended_use="AGGREGATE_SUMMARY",
        )


def test_official_upstox_aggregate_charges_endpoint_cannot_be_used_as_an_estimate():
    aggregate_mapping = replace(
        mapping(),
        endpoint="/v2/trade/profit-loss/charges",
        semantic="STATUTORY_CHARGE_ESTIMATE",
        scope="aggregate-segment-fy",
    )
    with pytest.raises(ValueError, match="Aggregate-only broker endpoint cannot provide estimate"):
        resolve(
            {"ipft": "0.01"},
            aggregate_mapping,
            endpoint="/v2/trade/profit-loss/charges",
            scope="aggregate-segment-fy",
            intended_use="ESTIMATE",
        )



@pytest.mark.parametrize(
    ("broker", "endpoint"),
    [
        ("Upstox", "/v2/trade/profit-loss/charges/"),
        ("upstox", "/v2/trade/profit-loss/charges"),
        ("UPSTOX", "/v2/trade/profit-loss/charges?segment=FO"),
        ("Upstox", "https://api.upstox.com/v2/trade/profit-loss/charges?segment=FO"),
    ],
)
def test_aggregate_only_endpoint_guard_cannot_be_bypassed_by_url_spelling(broker, endpoint):
    selected = replace(
        mapping(),
        broker=broker,
        endpoint=endpoint,
        scope="aggregate-segment-fy",
    )
    with pytest.raises(ValueError, match="Aggregate-only broker endpoint"):
        resolve(
            {"ipft": "0.01"},
            selected,
            broker=broker,
            endpoint=endpoint,
            scope="aggregate-segment-fy",
        )


@pytest.mark.parametrize(
    ("broker", "endpoint"),
    [
        ("Upstox", "/v2/charges/brokerage/"),
        ("upstox", "/v2/charges/brokerage"),
        ("UPSTOX", "/v2/charges/brokerage?instrument_token=NSE_EQ|INE"),
        ("Upstox", "https://api.upstox.com/v2/charges/brokerage?instrument_token=fixture"),
    ],
)
def test_estimate_only_endpoint_guard_cannot_be_bypassed_by_url_spelling(broker, endpoint):
    selected = replace(
        mapping(),
        broker=broker,
        endpoint=endpoint,
        semantic="PER_FILL_ACTUAL",
    )
    with pytest.raises(ValueError, match="Estimate-only broker endpoint"):
        resolve(
            {"ipft": "0.17"},
            selected,
            broker=broker,
            endpoint=endpoint,
        )
