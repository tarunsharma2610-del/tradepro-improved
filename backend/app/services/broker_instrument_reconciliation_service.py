"""Deterministic reconciliation of broker snapshot instruments to the master.

Only exact broker instrument keys are authoritative. Symbols are validation
attributes, never fallback identifiers; ambiguous or unknown rows are surfaced
for review and are not silently mapped.
"""
from collections import Counter
from typing import Any, Iterable


def reconcile_broker_instruments(
    rows: Iterable[dict[str, Any]],
    instruments: Iterable[Any],
) -> list[dict[str, Any]]:
    master = {}
    for instrument in instruments:
        key = getattr(instrument, "instrument_key", None)
        if not isinstance(key, str) or not key.strip():
            continue
        master.setdefault(key.strip(), []).append(instrument)

    source_rows = list(rows)
    keys = [row.get("instrument_key") for row in source_rows if isinstance(row, dict)]
    counts = Counter(key for key in keys if isinstance(key, str))

    results = []
    for index, row in enumerate(source_rows):
        if not isinstance(row, dict):
            results.append({"row_index": index, "status": "INVALID_SOURCE_ROW", "instrument_id": None})
            continue
        key = row.get("instrument_key")
        if not isinstance(key, str) or not key.strip():
            results.append({"row_index": index, "status": "MISSING_BROKER_KEY", "instrument_id": None})
            continue
        key = key.strip()
        candidates = master.get(key, [])
        if counts[key] > 1 or len(candidates) > 1:
            results.append({"row_index": index, "instrument_key": key, "status": "AMBIGUOUS", "instrument_id": None})
            continue
        if not candidates:
            results.append({"row_index": index, "instrument_key": key, "status": "UNMAPPED", "instrument_id": None})
            continue
        instrument = candidates[0]
        source_exchange = row.get("exchange")
        source_symbol = row.get("trading_symbol")
        if (
            (source_exchange and source_exchange != instrument.exchange)
            or (source_symbol and source_symbol != instrument.trading_symbol)
        ):
            results.append({
                "row_index": index,
                "instrument_key": key,
                "status": "IDENTITY_CONFLICT",
                "instrument_id": None,
            })
            continue
        results.append({
            "row_index": index,
            "instrument_key": key,
            "status": "MATCHED",
            "instrument_id": str(instrument.id),
        })
    return results
