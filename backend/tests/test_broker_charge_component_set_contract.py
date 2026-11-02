import pytest

from app.services.broker_charge_component_set_contract import (
    LIVE_FILL_ACCOUNTING_COMPONENTS,
    LIVE_FILL_COMPONENT_SET_VERSION,
    validate_live_fill_component_set,
)


def valid_rows():
    return {
        "component_names": list(LIVE_FILL_ACCOUNTING_COMPONENTS),
        "component_set_versions": [LIVE_FILL_COMPONENT_SET_VERSION] * len(LIVE_FILL_ACCOUNTING_COMPONENTS),
        "component_statuses": ["VERIFIED"] * len(LIVE_FILL_ACCOUNTING_COMPONENTS),
    }


def test_canonical_component_set_requires_exact_supported_version_and_review():
    result = validate_live_fill_component_set(**valid_rows())
    assert result == {
        "component_set_version": LIVE_FILL_COMPONENT_SET_VERSION,
        "components": list(LIVE_FILL_ACCOUNTING_COMPONENTS),
        "verified": True,
    }


def test_component_set_rejects_missing_component():
    rows = valid_rows()
    rows["component_names"].remove("gst")
    rows["component_set_versions"].pop()
    rows["component_statuses"].pop()
    with pytest.raises(ValueError, match="exactly the supported canonical six-component set"):
        validate_live_fill_component_set(**rows)


def test_component_set_rejects_additional_evidence_only_component():
    rows = valid_rows()
    rows["component_names"].append("ipft")
    rows["component_set_versions"].append(None)
    rows["component_statuses"].append("PENDING_REVIEW")
    with pytest.raises(ValueError, match="additional source components must be mapped explicitly"):
        validate_live_fill_component_set(**rows)


def test_component_set_rejects_duplicate_component():
    rows = valid_rows()
    rows["component_names"].append("gst")
    rows["component_set_versions"].append(LIVE_FILL_COMPONENT_SET_VERSION)
    rows["component_statuses"].append("VERIFIED")
    with pytest.raises(ValueError, match="duplicate source components"):
        validate_live_fill_component_set(**rows)


def test_component_set_rejects_legacy_null_or_unsupported_version():
    rows = valid_rows()
    rows["component_set_versions"][0] = None
    with pytest.raises(ValueError, match="missing the supported version"):
        validate_live_fill_component_set(**rows)


def test_component_set_rejects_unreviewed_rows():
    rows = valid_rows()
    rows["component_statuses"][0] = "PENDING_REVIEW"
    with pytest.raises(ValueError, match="independently verified"):
        validate_live_fill_component_set(**rows)
