"""Lossless normalization of broker charge API fields.

This module records field presence and numeric interpretation without inferring
whether a broker field is combined, per-order, aggregate, or an actual per-fill
charge. That semantic decision requires a versioned, reviewed source mapping.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


def normalize_charge_api_field(payload: dict[str, Any], field: str) -> dict[str, Any]:
    """Return a lossless field-state envelope for a JSON API payload.

    States are MISSING, NULL, ZERO, VALUE, or INVALID. The original raw value
    is retained; callers must not collapse missing/null/zero or infer tariff
    semantics from a field name.
    """
    if not isinstance(payload, dict):
        raise ValueError("Charge API payload must be a JSON object.")
    if not isinstance(field, str) or not field.strip():
        raise ValueError("Charge API field name is required.")
    if field not in payload:
        return {"field": field, "state": "MISSING", "raw_value": None, "decimal_value": None}
    raw = payload[field]
    if raw is None:
        return {"field": field, "state": "NULL", "raw_value": None, "decimal_value": None}
    if isinstance(raw, bool) or isinstance(raw, (dict, list)):
        return {"field": field, "state": "INVALID", "raw_value": raw, "decimal_value": None}
    try:
        value = Decimal(str(raw))
    except (InvalidOperation, TypeError, ValueError):
        return {"field": field, "state": "INVALID", "raw_value": raw, "decimal_value": None}
    if not value.is_finite() or value < 0:
        return {"field": field, "state": "INVALID", "raw_value": raw, "decimal_value": None}
    return {
        "field": field,
        "state": "ZERO" if value == 0 else "VALUE",
        "raw_value": raw,
        "decimal_value": str(value),
    }
