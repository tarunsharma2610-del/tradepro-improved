"""Versioned canonical component set required for live-fill accounting promotion.

Evidence intake intentionally accepts a wider vocabulary. That does not make every
source line eligible for canonical accounting; unsupported or additional rows must
remain visible and block promotion until an explicit mapping is reviewed.
"""
from __future__ import annotations

from collections.abc import Sequence

LIVE_FILL_COMPONENT_SET_VERSION = "live-fill-accounting-component-set-v1"
LIVE_FILL_ACCOUNTING_COMPONENTS = (
    "brokerage",
    "stt",
    "exchange_charges",
    "sebi_charges",
    "stamp_duty",
    "gst",
)


def validate_live_fill_component_set(
    *,
    component_names: Sequence[str],
    component_set_versions: Sequence[str | None],
    component_statuses: Sequence[str],
) -> dict[str, object]:
    """Require exactly one reviewed row per canonical component and this set version."""
    if len(component_names) != len(set(component_names)):
        raise ValueError("Live accounting component set contains duplicate source components.")
    if set(component_names) != set(LIVE_FILL_ACCOUNTING_COMPONENTS):
        raise ValueError(
            "Live accounting requires exactly the supported canonical six-component set; "
            "missing or additional source components must be mapped explicitly before promotion."
        )
    if len(component_set_versions) != len(component_names) or any(
        version != LIVE_FILL_COMPONENT_SET_VERSION for version in component_set_versions
    ):
        raise ValueError("Live accounting component set is missing the supported version.")
    if len(component_statuses) != len(component_names) or any(
        status != "VERIFIED" for status in component_statuses
    ):
        raise ValueError("Every live-accounting component must be independently verified.")
    return {
        "component_set_version": LIVE_FILL_COMPONENT_SET_VERSION,
        "components": list(LIVE_FILL_ACCOUNTING_COMPONENTS),
        "verified": True,
    }
