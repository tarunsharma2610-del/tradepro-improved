from copy import deepcopy
from datetime import date
from math import isfinite

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.instrument import Instrument
from app.models.user import User
from app.schemas.market_data import MarketDataStreamStart
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.market_data_stream_manager import market_data_stream_manager
from app.brokers.registry import get_broker_adapter

router = APIRouter(prefix="/market-data", tags=["market-data"])


@router.post("/stream", status_code=status.HTTP_202_ACCEPTED)
async def start_market_data_stream(
    payload: MarketDataStreamStart,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if BrokerCredentialsService(db).get_analytics_token(user.id, "upstox") is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Configure a valid Upstox Analytics Token in Settings before starting a market stream.")

    found = {
        row.instrument_key
        for row in db.query(Instrument.instrument_key)
        .filter(Instrument.is_active.is_(True), Instrument.instrument_key.in_(payload.instrument_keys))
        .all()
    }
    missing = sorted(set(payload.instrument_keys) - found)
    if missing:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Unknown or inactive instrument_key(s): {', '.join(missing[:10])}",
        )

    streamer = await market_data_stream_manager.start(user.id, payload.instrument_keys, mode=payload.mode)
    return {
        "started": True,
        "connected": streamer.connected,
        "instrument_count": len(streamer.instrument_keys),
        "mode": streamer.mode,
        "message": "Stream task started. Check GET /market-data/stream for connection and fresh-quote status.",
    }


@router.get("/option-chain")
async def get_option_chain(
    instrument_key: str = Query(min_length=3, max_length=100),
    expiry_date: str = Query(min_length=7, max_length=20),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return Upstox's authoritative option-chain snapshot for one expiry."""
    if instrument_key.startswith("MCX_"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Upstox Option Chain API does not currently support MCX.")
    if expiry_date not in {"current_week", "next_week", "far_week", "current_month", "next_month", "far_month"}:
        try:
            parsed_expiry = date.fromisoformat(expiry_date)
            if parsed_expiry.isoformat() != expiry_date:
                raise ValueError("expiry_date must use YYYY-MM-DD.")
        except ValueError:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "expiry_date must be YYYY-MM-DD or a supported Upstox relative expiry keyword.")
    token = BrokerCredentialsService(db).get_analytics_token(user.id, "upstox")
    if token is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Configure a valid Upstox Analytics Token in Settings before requesting option-chain data.")
    result = await get_broker_adapter("upstox").get_option_chain(token, instrument_key, expiry_date)
    if not result.ok:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, result.error or "Upstox option-chain request failed.")

    payload = deepcopy(result.data)
    # Upstox supplies current OI and previous OI per contract. Expose their
    # difference as a derived field only when both source values are present
    # and finite; never turn a missing/null value into zero.
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        for strike in payload["data"]:
            if not isinstance(strike, dict):
                continue
            for side in ("call_options", "put_options"):
                option = strike.get(side)
                market = option.get("market_data") if isinstance(option, dict) else None
                if not isinstance(market, dict):
                    continue
                oi, previous_oi = market.get("oi"), market.get("prev_oi")
                valid = (
                    isinstance(oi, (int, float)) and not isinstance(oi, bool)
                    and isinstance(previous_oi, (int, float)) and not isinstance(previous_oi, bool)
                    and isfinite(oi) and isfinite(previous_oi)
                )
                market["change_oi"] = oi - previous_oi if valid else None
    return payload


@router.get("/stream")
def market_data_stream_status(user: User = Depends(get_current_user)):
    streamer = market_data_stream_manager.get(user.id)
    if streamer is None:
        return {"running": False, "connected": False, "quotes": {}}

    quotes = {}
    for key in streamer.instrument_keys:
        tick = streamer.latest_tick(key)
        quotes[key] = None if tick is None else {
            "ltp": tick.ltp,
            "exchange_timestamp_ms": tick.exchange_timestamp_ms,
            "received_at": tick.received_at.isoformat(),
            "stale": False,
        }
    return {
        "running": streamer.running,
        "connected": streamer.connected,
        "mode": streamer.mode,
        "instrument_count": len(streamer.instrument_keys),
        "quotes": quotes,
    }


@router.delete("/stream")
async def stop_market_data_stream(user: User = Depends(get_current_user)):
    stopped = await market_data_stream_manager.stop(user.id)
    return {"stopped": stopped}
