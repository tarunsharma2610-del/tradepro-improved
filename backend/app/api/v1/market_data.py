from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.instrument import Instrument
from app.models.user import User
from app.schemas.market_data import MarketDataStreamStart
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.market_data_stream_manager import market_data_stream_manager

router = APIRouter(prefix="/market-data", tags=["market-data"])


@router.post("/stream", status_code=status.HTTP_202_ACCEPTED)
async def start_market_data_stream(
    payload: MarketDataStreamStart,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if BrokerCredentialsService(db).get_access_token(user.id, "upstox") is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Connect Upstox and complete OAuth before starting a market stream.")

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

    streamer = await market_data_stream_manager.start(user.id, payload.instrument_keys)
    return {
        "started": True,
        "connected": streamer.connected,
        "instrument_count": len(streamer.instrument_keys),
        "mode": "ltpc",
        "message": "Stream task started. Check GET /market-data/stream for connection and fresh-quote status.",
    }


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
        "mode": "ltpc",
        "instrument_count": len(streamer.instrument_keys),
        "quotes": quotes,
    }


@router.delete("/stream")
async def stop_market_data_stream(user: User = Depends(get_current_user)):
    stopped = await market_data_stream_manager.stop(user.id)
    return {"stopped": stopped}
