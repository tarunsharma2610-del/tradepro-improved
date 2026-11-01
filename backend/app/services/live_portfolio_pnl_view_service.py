"""Join LIVE broker-position snapshots to fresh market quotes for P&L display.

This is a read-only projection: it never mutates positions, executions, cash or
the realized ledger. Missing/stale quotes make the portfolio total unavailable
rather than presenting a partial sum as complete.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.services.live_unrealized_pnl_service import calculate_live_unrealized_pnl


def build_live_unrealized_pnl_view(
    *,
    broker_positions: list[dict[str, Any]],
    quotes_by_instrument: dict[str, dict[str, Any]],
    now: datetime,
    max_quote_age_seconds: int = 15,
) -> dict[str, Any]:
    rows = []
    total = Decimal("0.00")
    unavailable_count = 0

    for index, position in enumerate(broker_positions):
        if not isinstance(position, dict):
            rows.append({"row_index": index, "status": "INVALID_BROKER_POSITION", "unrealized_pnl": None})
            unavailable_count += 1
            continue
        key = position.get("instrument_key")
        quantity = position.get("quantity")
        average_raw = position.get("average_price")
        if not isinstance(key, str) or not key.strip():
            rows.append({"row_index": index, "status": "MISSING_INSTRUMENT_KEY", "unrealized_pnl": None})
            unavailable_count += 1
            continue
        if isinstance(quantity, bool) or not isinstance(quantity, int):
            rows.append({"row_index": index, "instrument_key": key, "status": "INVALID_QUANTITY", "unrealized_pnl": None})
            unavailable_count += 1
            continue
        if quantity == 0:
            rows.append({
                "row_index": index, "instrument_key": key,
                "status": "FLAT", "quantity": 0, "unrealized_pnl": "0.00",
                "quote_age_seconds": None,
            })
            continue
        quote = quotes_by_instrument.get(key)
        if not isinstance(quote, dict):
            rows.append({"row_index": index, "instrument_key": key, "status": "QUOTE_UNAVAILABLE", "unrealized_pnl": None})
            unavailable_count += 1
            continue
        try:
            average = Decimal(str(average_raw))
            last = Decimal(str(quote["ltp"]))
            received_at = datetime.fromisoformat(quote["received_at"])
            result = calculate_live_unrealized_pnl(
                quantity=quantity,
                average_price=average,
                last_price=last,
                quote_received_at=received_at,
                now=now,
                max_quote_age_seconds=max_quote_age_seconds,
            )
        except (KeyError, TypeError, ValueError, ArithmeticError):
            rows.append({"row_index": index, "instrument_key": key, "status": "QUOTE_OR_PRICE_INVALID_OR_STALE", "unrealized_pnl": None})
            unavailable_count += 1
            continue
        total += result.unrealized_pnl
        rows.append({
            "row_index": index, "instrument_key": key, "status": "AVAILABLE",
            "quantity": quantity, "average_price": format(result.average_price, "f"),
            "last_price": format(result.last_price, "f"),
            "unrealized_pnl": format(result.unrealized_pnl, "f"),
            "quote_age_seconds": format(result.quote_age_seconds, "f"),
        })
    complete = unavailable_count == 0
    return {
        "source": "broker_positions_plus_fresh_market_quotes",
        "complete": complete,
        "unavailable_position_count": unavailable_count,
        "total_unrealized_pnl": format(total, "f") if complete else None,
        "rows": rows,
    }
