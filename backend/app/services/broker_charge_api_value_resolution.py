"""Resolve normalized broker charge values only through approved exact mappings."""
from __future__ import annotations

from datetime import date
from typing import Any, Iterable

from app.services.broker_charge_api_mapping import (
    ChargeApiFieldMapping,
    select_charge_api_field_mapping,
)
from app.services.broker_charge_api_normalization import normalize_charge_api_field


# The official Upstox endpoint is period/segment aggregate evidence, not a
# documented per-fill payload. A bad/stale registry row must not override this
# source-level restriction.
AGGREGATE_ONLY_ENDPOINTS = frozenset({
    ("Upstox", "/v2/trade/profit-loss/charges"),
})


def resolve_charge_api_value(
    payload: dict[str, Any],
    field: str,
    mappings: Iterable[ChargeApiFieldMapping],
    *,
    broker: str,
    endpoint: str,
    schema_version: str,
    field_path: str,
    scope: str,
    trade_date: date,
    intended_use: str,
) -> dict[str, Any]:
    """Return field state plus approved semantics; never infer missing semantics.

    PER_FILL_ACTUAL use accepts only a mapping explicitly marked PER_FILL_ACTUAL.
    Aggregate summaries and estimates cannot be silently reused as actual per-fill
    charges. Mapping provenance is retained for every resolved field state,
    including missing, null, and invalid values. This function does not promote
    an accounting allocation.
    """
    normalized = normalize_charge_api_field(payload, field)
    mapping = select_charge_api_field_mapping(
        mappings,
        broker=broker,
        endpoint=endpoint,
        schema_version=schema_version,
        field_path=field_path,
        scope=scope,
        trade_date=trade_date,
    )
    if field != mapping.field_path.rsplit(".", 1)[-1]:
        raise ValueError("Payload field does not match the approved mapping field path.")
    if intended_use not in {"ESTIMATE", "AGGREGATE_SUMMARY", "PER_FILL_ACTUAL"}:
        raise ValueError("Unsupported intended use.")
    if intended_use == "PER_FILL_ACTUAL" and mapping.semantic != "PER_FILL_ACTUAL":
        raise ValueError("Mapping semantics do not permit per-fill actual accounting.")
    if intended_use == "PER_FILL_ACTUAL" and (broker, endpoint) in AGGREGATE_ONLY_ENDPOINTS:
        raise ValueError("Aggregate-only broker endpoint cannot provide per-fill actual evidence.")
    if intended_use == "AGGREGATE_SUMMARY" and mapping.semantic not in {
        "AGGREGATE_ACTUAL_SUMMARY", "STATUTORY_CHARGE_ESTIMATE", "BROKERAGE_ESTIMATE"
    }:
        raise ValueError("Mapping semantics do not permit aggregate summary use.")
    if intended_use == "ESTIMATE" and mapping.semantic not in {
        "BROKERAGE_ESTIMATE", "STATUTORY_CHARGE_ESTIMATE"
    }:
        raise ValueError("Mapping semantics do not permit estimate use.")

    # Provenance describes the approved interpretation even when the payload
    # value is unusable. Keeping it on all states makes missing/null/invalid
    # results auditable without implying that they are accounting-ready.
    provenance = {
        "semantic": mapping.semantic,
        "mapping_source_url": mapping.source_url,
        "mapping_source_sha256": mapping.source_sha256,
    }
    if normalized["state"] in {"MISSING", "NULL", "INVALID"}:
        return {**normalized, **provenance, "usable": False}
    return {**normalized, **provenance, "usable": True}
