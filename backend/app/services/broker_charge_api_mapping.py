"""Reviewed semantics registry for broker charge API fields.

Field presence/value normalization is intentionally separate from business
semantics. Only an exact, reviewed mapping for the endpoint/schema/scope/date
may interpret a normalized amount.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable


ALLOWED_SEMANTICS = frozenset({
    "BROKERAGE_ESTIMATE",
    "STATUTORY_CHARGE_ESTIMATE",
    "AGGREGATE_ACTUAL_SUMMARY",
    "PER_FILL_ACTUAL",
    "COMBINED_TRANSACTION_AND_IPFT",
    "TRANSACTION_EXCLUDING_IPFT",
    "IPFT_ONLY",
    "UNKNOWN",
})
ALLOWED_STATES = frozenset({"DRAFT", "REVIEWED", "APPROVED", "REJECTED"})


@dataclass(frozen=True)
class ChargeApiFieldMapping:
    broker: str
    endpoint: str
    schema_version: str
    field_path: str
    semantic: str
    unit: str
    currency: str
    scope: str
    effective_from: date
    effective_to: date | None
    source_url: str
    source_sha256: str
    review_state: str = "DRAFT"

    def __post_init__(self) -> None:
        for name in (
            "broker", "endpoint", "schema_version", "field_path", "unit",
            "currency", "scope", "source_url", "source_sha256",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required for charge API field mapping.")
        if self.semantic not in ALLOWED_SEMANTICS:
            raise ValueError("Unsupported charge API field semantic.")
        if self.review_state not in ALLOWED_STATES:
            raise ValueError("Unsupported charge API mapping review state.")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("Mapping effective_to cannot precede effective_from.")
        if len(self.source_sha256) != 64 or any(
            c not in "0123456789abcdefABCDEF" for c in self.source_sha256
        ):
            raise ValueError("Mapping source_sha256 must be a 64-character hexadecimal SHA-256.")


def select_charge_api_field_mapping(
    mappings: Iterable[ChargeApiFieldMapping],
    *,
    broker: str,
    endpoint: str,
    schema_version: str,
    field_path: str,
    scope: str,
    trade_date: date,
) -> ChargeApiFieldMapping:
    """Select one exact approved mapping; never fall back by field name."""
    key = (broker, endpoint, schema_version, field_path, scope)
    matches = [
        mapping for mapping in mappings
        if (
            mapping.broker, mapping.endpoint, mapping.schema_version,
            mapping.field_path, mapping.scope,
        ) == key
        and mapping.review_state == "APPROVED"
        and mapping.effective_from <= trade_date
        and (mapping.effective_to is None or trade_date <= mapping.effective_to)
    ]
    if not matches:
        raise ValueError("No approved API field mapping matches exact endpoint, schema, scope and date.")
    if len(matches) > 1:
        raise ValueError("Overlapping approved API field mappings are ambiguous.")
    mapping = matches[0]
    if mapping.semantic == "UNKNOWN":
        raise ValueError("Unknown API field semantics cannot be used for charge accounting.")
    return mapping
