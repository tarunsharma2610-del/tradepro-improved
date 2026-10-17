"""
Instrument catalog service.

`seed_defaults()` inserts a small set of real NSE equities for bootstrap and
tests. `sync_from_upstox()` downloads Upstox's documented BOD JSON instrument
file (gzip-compressed), currently imports only NSE_EQ records, and upserts
them into the local catalog. This is not yet a full NSE/BSE/MCX/F&O sync;
the supported file URL and JSON field names are documented at
https://upstox.com/developer/api-documentation/instruments/.
"""

import gzip
import json
from decimal import Decimal

import httpx
from sqlalchemy.orm import Session

from app.repositories.instrument_repository import InstrumentRepository

# Real, stable ISINs for well-known NSE large-caps — not test/fake data.
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


class InstrumentService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = InstrumentRepository(db)

    def seed_defaults(self) -> int:
        count = 0
        for symbol, name, isin in _SEED_EQUITIES:
            self.repo.upsert(
                instrument_key=f"NSE_EQ|{isin}",
                exchange="NSE",
                segment="NSE_EQ",
                instrument_type="EQUITY",
                trading_symbol=symbol,
                name=name,
                lot_size=1,
                tick_size=Decimal("0.05"),
                expiry=None,
                strike_price=None,
                option_type=None,
                is_active=True,
            )
            count += 1
        return count

    async def sync_from_upstox(self) -> tuple[bool, str]:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(_INSTRUMENT_MASTER_URL, follow_redirects=True)
        except httpx.HTTPError as exc:
            return False, f"Network error fetching instrument master: {exc}"

        if resp.status_code != 200:
            return False, (
                f"Instrument master fetch failed ({resp.status_code}). This endpoint's exact URL/format "
                "wasn't independently confirmed — check the current one at "
                "upstox.com/developer/api-documentation/instruments/ and update _INSTRUMENT_MASTER_URL."
            )

        try:
            raw = gzip.decompress(resp.content)
            records = json.loads(raw)
        except (OSError, json.JSONDecodeError) as exc:
            return False, f"Could not parse the instrument master response: {exc}"

        if not isinstance(records, list):
            return False, "Unexpected instrument master format (expected a JSON array)."

        count = 0
        for rec in records:
            segment = rec.get("segment", "")
            if segment != "NSE_EQ":
                continue  # Phase 2 scope: NSE equity only — see README known limitations
            key = rec.get("instrument_key")
            symbol = rec.get("trading_symbol")
            if not key or not symbol:
                continue
            self.repo.upsert(
                instrument_key=key,
                exchange="NSE",
                segment=segment,
                instrument_type="EQUITY",
                trading_symbol=symbol,
                name=rec.get("name", symbol),
                lot_size=rec.get("lot_size", 1),
                tick_size=Decimal(str(rec.get("tick_size", 0.05))),
                expiry=None,
                strike_price=None,
                option_type=None,
                is_active=True,
            )
            count += 1

        return True, f"Synced {count} NSE equity instruments."
