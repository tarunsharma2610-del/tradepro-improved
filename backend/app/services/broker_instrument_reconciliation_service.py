"""Deterministic reconciliation of broker snapshot instruments to the master.

Only exact broker instrument keys are authoritative. Symbols are validation
attributes, never fallback identifiers; ambiguous or unknown rows are surfaced
for review and are not silently mapped.
"""
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
    # Only exact duplicate source identities are ambiguous. A repeated key
    # with a conflicting symbol/exchange must be reported as IDENTITY_CONFLICT,
    # not allowed to poison an otherwise valid row sharing that key.
    source_identity_counts: dict[tuple[str, str, str], int] = {}
    for source in source_rows:
        if not isinstance(source, dict):
            continue
        key = source.get("instrument_key")
        if isinstance(key, str) and key.strip():
            identity = (
                key.strip(),
                str(source.get("exchange") or "").strip(),
                str(source.get("trading_symbol") or "").strip(),
            )
            source_identity_counts[identity] = source_identity_counts.get(identity, 0) + 1

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
        source_identity = (
            key,
            str(row.get("exchange") or "").strip(),
            str(row.get("trading_symbol") or "").strip(),
        )
        if source_identity_counts.get(source_identity, 0) > 1 or len(candidates) > 1:
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
