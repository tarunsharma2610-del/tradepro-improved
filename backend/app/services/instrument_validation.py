"""Fail-closed instrument/segment validation shared by execution paths.

The current importer only guarantees equity instruments. Futures/options must
not be simulated as if they were equities until derivative contracts, lot
sizes, tick-size units, and margin/risk treatment are verified end-to-end.
"""
from typing import Any


_EQUITY_MARKET_SEGMENTS = {"NSE_EQ", "BSE_EQ"}
_EQUITY_INSTRUMENT_TYPES = {"EQUITY", "EQ", "BE", "A", "B"}
_EQUITY_ORDER_SEGMENTS = {"EQUITY_DELIVERY", "EQUITY_INTRADAY"}


def validate_instrument_segment(instrument: Any, requested_segment: Any) -> None:
    segment = getattr(requested_segment, "value", requested_segment)
    segment = str(segment).upper()

    if segment not in _EQUITY_ORDER_SEGMENTS:
        raise ValueError(
            "Futures and options are not enabled until the derivative instrument master, "
            "lot/tick-size handling, and contract risk controls are verified."
        )

    instrument_segment = str(getattr(instrument, "segment", "")).upper()
    instrument_type = str(getattr(instrument, "instrument_type", "")).upper()
    if instrument_segment not in _EQUITY_MARKET_SEGMENTS or instrument_type not in _EQUITY_INSTRUMENT_TYPES:
        raise ValueError(
            "This order segment requires an equity instrument from the verified equity instrument master."
        )
