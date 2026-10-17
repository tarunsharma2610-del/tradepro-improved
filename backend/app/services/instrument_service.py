"""
Instrument catalog service.

Downloads Upstox's official gzip-compressed BOD JSON instrument master and
imports supported NSE, BSE and MCX segments. Unknown segments/types are skipped.
A successful download is upserted in one database transaction; failed or
malformed downloads never mutate the catalog. Existing instruments are not
deactivated by this sync because a partial but syntactically valid file must
not accidentally disable tradable instruments.
"""

import gzip
import json
from datetime import date, datetime, timezone
from decimal import Decimal

import httpx
from sqlalchemy.orm import Session

from app.repositories.instrument_repository import InstrumentRepository

_SEED_EQUITIES = [
    ("RELIANCE", "Reliance Industries Ltd", "INE002A01018"),
    ("TCS", "Tata Consultancy Services Ltd", "INE467B01029"),
    ("HDFCBANK", "HDFC Bank Ltd", "INE040A01034"),
    ("INFY", "Infosys Ltd", "INE009A01021"),
    ("ICICIBANK", "ICICI Bank Ltd", "INE090A01021"),
    ("HINDUNILVR", "Hindustan Unilever Ltd", "INE030A01027"),
    ("ITC", "ITC Ltd", "INE154A01025"),
    ("SBIN", "State Bank of India", "INE062A01020"),
    ("BHARTIARTL", "Bharti Airtel Ltd", "INE397D01024"),
    ("KOTAKBANK", "Kotak Mahindra Bank Ltd", "INE237A01028"),
]

_INSTRUMENT_MASTER_URL = "https://assets.upstox.com/market-quote/instruments/exchange/complete.json.gz"

# Segments listed in Upstox's official BOD instrument documentation.
_SUPPORTED_SEGMENTS = {
    "NSE_EQ", "NSE_INDEX", "NSE_FO", "NCD_FO",
    "BSE_EQ", "BSE_INDEX", "BSE_FO", "BCD_FO",
    "MCX_FO", "NSE_COM",
}
_OPTION_TYPES = {"CE", "PE"}
_SEGMENT_EXCHANGE = {
    "NSE_EQ": "NSE", "NSE_INDEX": "NSE", "NSE_FO": "NSE", "NSE_COM": "NSE",
    "NCD_FO": "NSE",
    "BSE_EQ": "BSE", "BSE_INDEX": "BSE", "BSE_FO": "BSE", "BCD_FO": "BSE",
    "MCX_FO": "MCX",
}


def _expiry_date(value) -> date | None:
    """Convert Upstox epoch-milliseconds or ISO date into an expiry date."""
    if value in (None, ""):
        return None
    if isinstance(value, str):
        # Be defensive if a future BOD schema emits YYYY-MM-DD.
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except ValueError:
            try:
                value = int(value)
            except ValueError:
                return None
    if isinstance(value, (int, float)) and value > 0:
        try:
            return datetime.fromtimestamp(value / 1000, tz=timezone.utc).date()
        except (OverflowError, OSError, ValueError):
            return None
    return None


def _normalize_record(rec: dict) -> dict | None:
    """Map a documented BOD record into the application's canonical model."""
    if not isinstance(rec, dict):
        return None
    segment = rec.get("segment")
    if not isinstance(segment, str) or segment not in _SUPPORTED_SEGMENTS:
        return None

    key = rec.get("instrument_key")
    symbol = rec.get("trading_symbol")
    exchange = rec.get("exchange")
    raw_type = rec.get("instrument_type")
    if not all(isinstance(v, str) and v.strip() for v in (key, symbol, exchange, raw_type)):
        return None
    if exchange != _SEGMENT_EXCHANGE[segment]:
        return None
    if not key.startswith(f"{segment}|"):
        return None

    expiry = _expiry_date(rec.get("expiry"))
    strike = rec.get("strike_price")
    option_type = raw_type if raw_type in _OPTION_TYPES else None

    if segment.endswith("_EQ") and raw_type not in {"FUT", "CE", "PE", "INDEX"}:
        # The exchange equity segment is authoritative; exchanges may use
        # additional board/category codes beyond EQ and BE.
        canonical_type = "EQUITY"
        expiry = None
        strike = None
    elif segment.endswith("_INDEX") and raw_type == "INDEX":
        canonical_type = "INDEX"
        expiry = None
        strike = None
    elif raw_type == "FUT":
        canonical_type = "FUTURES"
        strike = None
        option_type = None
    elif raw_type in _OPTION_TYPES:
        canonical_type = "OPTIONS"
    else:
        # Do not guess the meaning of new/unsupported instrument types.
        return None

    try:
        lot_size = int(rec.get("lot_size") or 1)
        tick_size = Decimal(str(rec.get("tick_size", 0.05)))
        strike_price = Decimal(str(strike)) if strike not in (None, "") else None
    except (ValueError, TypeError, ArithmeticError):
        return None
    if lot_size <= 0 or not tick_size.is_finite() or tick_size <= 0:
        return None
    if strike_price is not None and (not strike_price.is_finite() or strike_price < 0):
        return None
    if canonical_type in {"FUTURES", "OPTIONS"} and expiry is None:
        return None
    if canonical_type == "OPTIONS" and (
        strike_price is None or strike_price <= 0 or option_type not in _OPTION_TYPES
    ):
        return None
    name = rec.get("name")
    if not isinstance(name, str) or not name.strip():
        name = symbol

    return {
        "instrument_key": key,
        "exchange": exchange,
        "segment": segment,
        "instrument_type": canonical_type,
        "trading_symbol": symbol,
        "name": name,
        "lot_size": lot_size,
        "tick_size": tick_size,
        "expiry": expiry,
        "strike_price": strike_price,
        "option_type": option_type,
        "is_active": True,
    }


class InstrumentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = InstrumentRepository(db)

    def seed_defaults(self) -> int:
        records = [
            {
                "instrument_key": f"NSE_EQ|{isin}",
                "exchange": "NSE",
                "segment": "NSE_EQ",
                "instrument_type": "EQUITY",
                "trading_symbol": symbol,
                "name": name,
                "lot_size": 1,
                "tick_size": Decimal("0.05"),
                "expiry": None,
                "strike_price": None,
                "option_type": None,
                "is_active": True,
            }
            for symbol, name, isin in _SEED_EQUITIES
        ]
        return self.repo.upsert_many(records)

    async def sync_from_upstox(self) -> tuple[bool, str]:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.get(_INSTRUMENT_MASTER_URL, follow_redirects=True)
        except httpx.HTTPError as exc:
            return False, f"Network error fetching instrument master: {exc}"

        if resp.status_code != 200:
            return False, f"Instrument master fetch failed ({resp.status_code})."

        try:
            raw = gzip.decompress(resp.content)
            records = json.loads(raw)
        except (OSError, EOFError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            return False, f"Could not parse the instrument master response: {exc}"

        if not isinstance(records, list) or not records:
            return False, "Unexpected or empty instrument master (expected a non-empty JSON array)."

        normalized = []
        seen_keys = set()
        for record in records:
            item = _normalize_record(record)
            if item is None or item["instrument_key"] in seen_keys:
                continue
            seen_keys.add(item["instrument_key"])
            normalized.append(item)

        if not normalized:
            return False, "Instrument master contained no supported, valid records; catalog was not changed."

        try:
            count = self.repo.upsert_many(normalized)
        except Exception:
            self.db.rollback()
            raise

        return True, f"Synced {count} instruments across supported NSE, BSE and MCX segments."
