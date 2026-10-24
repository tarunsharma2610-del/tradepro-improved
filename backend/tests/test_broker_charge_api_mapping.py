from datetime import date

import pytest

from app.services.broker_charge_api_mapping import (
    ChargeApiFieldMapping,
    select_charge_api_field_mapping,
)


def make_mapping(**changes):
    values = {
        "broker": "Upstox",
        "endpoint": "/v2/charges/brokerage",
        "schema_version": "documented-v2",
        "field_path": "data.charges.ipft",
        "semantic": "IPFT_ONLY",
        "unit": "INR",
        "currency": "INR",
        "scope": "single-order-estimate",
        "effective_from": date(2026, 1, 1),
        "effective_to": None,
        "source_url": "https://upstox.com/developer/api-documentation/get-brokerage/",
        "source_sha256": "a" * 64,
        "review_state": "APPROVED",
    }
    values.update(changes)
    return ChargeApiFieldMapping(**values)


def select(mappings, **changes):
    values = {
        "broker": "Upstox",
        "endpoint": "/v2/charges/brokerage",
        "schema_version": "documented-v2",
        "field_path": "data.charges.ipft",
        "scope": "single-order-estimate",
        "trade_date": date(2026, 10, 24),
    }
    values.update(changes)
    return select_charge_api_field_mapping(mappings, **values)


def test_selects_exact_approved_mapping():
    mapping = make_mapping()
    assert select([mapping]) is mapping


@pytest.mark.parametrize("state", ["DRAFT", "REVIEWED", "REJECTED"])
def test_unapproved_mapping_is_never_selected(state):
    with pytest.raises(ValueError, match="No approved API field mapping"):
        select([make_mapping(review_state=state)])


@pytest.mark.parametrize(
    "change",
    [
        {"endpoint": "/v2/trade/profit-loss/charges"},
        {"schema_version": "different-schema"},
        {"field_path": "data.charges.transaction"},
        {"scope": "aggregate-segment-fy"},
    ],
)
def test_mapping_requires_exact_endpoint_schema_field_and_scope(change):
    with pytest.raises(ValueError, match="No approved API field mapping"):
        select([make_mapping()], **change)


def test_unknown_semantics_cannot_be_used_for_accounting():
    with pytest.raises(ValueError, match="Unknown API field semantics"):
        select([make_mapping(semantic="UNKNOWN")])


def test_overlapping_approved_mappings_fail_closed():
    with pytest.raises(ValueError, match="Overlapping approved"):
        select([make_mapping(), make_mapping(source_sha256="b" * 64)])


def test_mapping_effective_date_boundary_is_inclusive():
    mapping = make_mapping(effective_from=date(2026, 10, 1), effective_to=date(2026, 10, 31))
    assert select([mapping], trade_date=date(2026, 10, 31)) is mapping
    with pytest.raises(ValueError, match="No approved API field mapping"):
        select([mapping], trade_date=date(2026, 11, 1))


@pytest.mark.parametrize(
    "changes",
    [
        {"source_sha256": "bad"},
        {"field_path": ""},
        {"effective_from": date(2026, 11, 1), "effective_to": date(2026, 10, 1)},
        {"semantic": "GUESS"},
    ],
)
def test_invalid_mapping_metadata_is_rejected(changes):
    with pytest.raises(ValueError):
        make_mapping(**changes)
