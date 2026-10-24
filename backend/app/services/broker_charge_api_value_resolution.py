"""Resolve normalized broker charge values only through approved exact mappings."""
from __future__ import annotations

from datetime import date
from typing import Any, Iterable

from app.services.broker_charge_api_mapping import (
    ChargeApiFieldMapping,
    select_charge_api_field_mapping,
)
from app.services.broker_charge_api_normalization import normalize_charge_api_field


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
    charges. This function does not itself promote an accounting allocation.
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
    if intended_use not in {"ESTIMATE", "AGGREGATE_SUMMARY", "PER_FILL_ACTUAL"}:
        raise ValueError("Unsupported intended use.")
    if intended_use == "PER_FILL_ACTUAL" and mapping.semantic != "PER_FILL_ACTUAL":
        raise ValueError("Mapping semantics do not permit per-fill actual accounting.")
    if intended_use == "AGGREGATE_SUMMARY" and mapping.semantic not in {
        "AGGREGATE_ACTUAL_SUMMARY", "STATUTORY_CHARGE_ESTIMATE", "BROKERAGE_ESTIMATE"
    }:
        raise ValueError("Mapping semantics do not permit aggregate summary use.")
    if intended_use == "ESTIMATE" and mapping.semantic not in {
        "BROKERAGE_ESTIMATE", "STATUTORY_CHARGE_ESTIMATE"
    }:
        raise ValueError("Mapping semantics do not permit estimate use.")
    if normalized["state"] in {"MISSING", "NULL", "INVALID"}:
        return {**normalized, "semantic": mapping.semantic, "usable": False}
    return {
        **normalized,
        "semantic": mapping.semantic,
        "usable": True,
        "mapping_source_url": mapping.source_url,
        "mapping_source_sha256": mapping.source_sha256,
    }
