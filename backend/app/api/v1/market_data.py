from copy import deepcopy
from datetime import date
from math import isfinite

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.instrument import Instrument
from app.models.market_data_subscription import MarketDataSubscription
from app.models.user import User
from app.schemas.market_data import MarketDataStreamChangeMode, MarketDataStreamKeys, MarketDataStreamStart
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.market_data_stream_manager import market_data_stream_manager
from app.services.market_data_subscription_service import MarketDataSubscriptionService
from app.brokers.registry import get_broker_adapter

router = APIRouter(prefix="/market-data", tags=["market-data"])

_INDEX_PRESET_DEFINITIONS = (
    {
        "preset": "nifty_50",
        "display_name": "Nifty 50",
        "name_aliases": {"NIFTY50"},
        "symbol_aliases": {"NIFTY"},
    },
    {
        "preset": "nifty_bank",
        "display_name": "Nifty Bank",
        "name_aliases": {"NIFTYBANK", "BANKNIFTY"},
        "symbol_aliases": {"BANKNIFTY", "NIFTYBANK"},
    },
    {
        "preset": "india_vix",
        "display_name": "India VIX",
        "name_aliases": {"INDIAVIX"},
        "symbol_aliases": {"INDIAVIX"},
    },
)


def _normalize_index_label(value: str | None) -> str:
    return "".join(character for character in (value or "").upper() if character.isalnum())


@router.get("/index-presets")
def get_index_feed_presets(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Resolve common index feed presets from the validated Upstox BOD catalog.

    The complete BOD catalog is the authoritative local universe used by the
    scanner. Resolve keys from active NSE_INDEX rows rather than hardcoding
    exchange tokens or depending on an OAuth-only search request at runtime.
    """
    catalog = (
        db.query(Instrument)
        .filter(
            Instrument.is_active.is_(True),
            Instrument.exchange == "NSE",
            Instrument.segment == "NSE_INDEX",
            Instrument.instrument_type == "INDEX",
        )
        .all()
    )
    presets = []
    for definition in _INDEX_PRESET_DEFINITIONS:
        matches = [
            item for item in catalog
            if _normalize_index_label(item.name) in definition["name_aliases"]
            or _normalize_index_label(item.trading_symbol) in definition["symbol_aliases"]
        ]
        if len(matches) == 1:
            item = matches[0]
            presets.append({
                "preset": definition["preset"],
                "display_name": definition["display_name"],
                "available": True,
                "instrument": {
                    "instrument_key": item.instrument_key,
                    "name": item.name,
                    "trading_symbol": item.trading_symbol,
                    "exchange": item.exchange,
                    "segment": item.segment,
                    "instrument_type": item.instrument_type,
                },
            })
        else:
            presets.append({
                "preset": definition["preset"],
                "display_name": definition["display_name"],
                "available": False,
                "reason": "not_found" if not matches else "ambiguous_catalog_match",
                "instrument": None,
            })
    return {
        "source": "upstox_bod_instrument_master",
        "catalog_sync_endpoint": "/api/v1/instruments/sync",
        "presets": presets,
    }

def _validate_active_instruments(db: Session, instrument_keys: list[str]) -> None:
    found = {
        row.instrument_key
        for row in db.query(Instrument.instrument_key)
        .filter(Instrument.is_active.is_(True), Instrument.instrument_key.in_(instrument_keys))
        .all()
    }
    missing = sorted(set(instrument_keys) - found)
    if missing:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Unknown or inactive instrument_key(s): {', '.join(missing[:10])}",
        )


def _require_analytics_token(db: Session, user: User) -> None:
    if BrokerCredentialsService(db).get_analytics_token(user.id, "upstox") is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Configure a valid Upstox Analytics Token in Settings before managing a market stream.",
        )



@router.post("/stream", status_code=status.HTTP_202_ACCEPTED)
async def start_market_data_stream(
    payload: MarketDataStreamStart,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_analytics_token(db, user)
    _validate_active_instruments(db, payload.instrument_keys)

    existing_streamer = market_data_stream_manager.get(user.id)
    try:
        if existing_streamer is not None and existing_streamer.running:
            await existing_streamer.subscribe(payload.instrument_keys, payload.mode)
            streamer = existing_streamer
        else:
            streamer = await market_data_stream_manager.start(user.id, payload.instrument_keys, mode=payload.mode)
        MarketDataSubscriptionService(db).replace_modes_for_user(
            user_id=user.id,
            broker="upstox",
            subscriptions_by_mode=streamer.subscriptions_by_mode,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))
    return {
        "started": True,
        "connected": streamer.connected,
        "instrument_count": len(streamer.instrument_keys),
        "mode": streamer.mode,
        "message": "Stream task started. Check GET /market-data/stream for connection and fresh-quote status.",
    }


@router.post("/stream/subscribe", status_code=status.HTTP_202_ACCEPTED)
async def subscribe_market_data(
    payload: MarketDataStreamKeys,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_analytics_token(db, user)
    streamer = market_data_stream_manager.get(user.id)
    if streamer is None or not streamer.running:
        raise HTTPException(status.HTTP_409_CONFLICT, "Start a market-data stream before adding subscriptions.")
    _validate_active_instruments(db, payload.instrument_keys)
    feed_mode = payload.mode or streamer.mode
    try:
        delivery = await streamer.subscribe(payload.instrument_keys, feed_mode)
        MarketDataSubscriptionService(db).replace_modes_for_user(
            user_id=user.id,
            broker="upstox",
            subscriptions_by_mode=streamer.subscriptions_by_mode,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))
    return {
        "subscribed": True,
        "delivery": delivery,
        "mode": feed_mode,
        "subscriptions_by_mode": streamer.subscriptions_by_mode,
        "instrument_count": len(streamer.instrument_keys),
        "instrument_keys": streamer.instrument_keys,
    }


@router.post("/stream/unsubscribe", status_code=status.HTTP_202_ACCEPTED)
async def unsubscribe_market_data(
    payload: MarketDataStreamKeys,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_analytics_token(db, user)
    streamer = market_data_stream_manager.get(user.id)
    if streamer is None or not streamer.running:
        raise HTTPException(status.HTTP_409_CONFLICT, "No running market-data stream exists.")
    requested = set(payload.instrument_keys) & set(streamer.instrument_keys)
    if payload.mode:
        requested &= set(streamer.subscriptions.get(payload.mode, set()))
    if requested and len(requested) == len(streamer.instrument_keys):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Cannot remove the final instruments; use DELETE /market-data/stream to stop the stream.",
        )
    removals_by_mode = {
        mode: requested & mode_keys
        for mode, mode_keys in streamer.subscriptions.items()
        if requested & mode_keys
    }
    try:
        delivery = await streamer.unsubscribe(list(requested))
        MarketDataSubscriptionService(db).replace_modes_for_user(
            user_id=user.id,
            broker="upstox",
            subscriptions_by_mode=streamer.subscriptions_by_mode,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))
    return {
        "unsubscribed": True,
        "delivery": delivery,
        "subscriptions_by_mode": streamer.subscriptions_by_mode,
        "instrument_count": len(streamer.instrument_keys),
        "instrument_keys": streamer.instrument_keys,
    }


@router.post("/stream/change-mode", status_code=status.HTTP_202_ACCEPTED)
async def change_market_data_stream_mode(
    payload: MarketDataStreamChangeMode,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _require_analytics_token(db, user)
    streamer = market_data_stream_manager.get(user.id)
    if streamer is None or not streamer.running:
        raise HTTPException(status.HTTP_409_CONFLICT, "No running market-data stream exists.")
    try:
        delivery = await streamer.change_mode(payload.instrument_keys, payload.mode)
        MarketDataSubscriptionService(db).replace_modes_for_user(
            user_id=user.id,
            broker="upstox",
            subscriptions_by_mode=streamer.subscriptions_by_mode,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc))
    return {
        "mode_changed": True,
        "delivery": delivery,
        "mode": streamer.mode,
        "subscriptions_by_mode": streamer.subscriptions_by_mode,
        "instrument_count": len(streamer.instrument_keys),
        "instrument_keys": streamer.instrument_keys,
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
        return {"running": False, "connected": False, "quotes": {}, "market_status": None}

    quotes = {}
    for key in streamer.instrument_keys:
        tick = streamer.latest_tick(key)
        quotes[key] = None if tick is None else {
            "instrument_key": tick.instrument_key,
            "ltp": tick.ltp,
            "exchange_timestamp_ms": tick.exchange_timestamp_ms,
            "received_at": tick.received_at.isoformat(),
            "depth": tick.depth,
            "option_greeks": tick.option_greeks,
            "open_interest": tick.open_interest,
            "volume_traded_today": tick.volume_traded_today,
            "average_traded_price": tick.average_traded_price,
            "total_buy_quantity": tick.total_buy_quantity,
            "total_sell_quantity": tick.total_sell_quantity,
            "ohlc": tick.ohlc,
            "indicative_equilibrium_price": tick.indicative_equilibrium_price,
            "reference_price": tick.reference_price,
            "indicative_equilibrium_quantity": tick.indicative_equilibrium_quantity,
            "indicative_interest_quantity_total": tick.indicative_interest_quantity_total,
            "indicative_interest_quantity_market": tick.indicative_interest_quantity_market,
            "cas_eligible": tick.cas_eligible,
            "stale": False,
        }
    return {
        "running": streamer.running,
        "connected": streamer.connected,
        "mode": streamer.mode,
        "subscriptions_by_mode": streamer.subscriptions_by_mode,
        "instrument_count": len(streamer.instrument_keys),
        "instrument_keys": streamer.instrument_keys,
        "quotes": quotes,
        "market_status": streamer.market_info,
    }


@router.delete("/stream")
async def stop_market_data_stream(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    MarketDataSubscriptionService(db).deactivate_for_user(user_id=user.id, broker="upstox")
    stopped = await market_data_stream_manager.stop(user.id)
    return {"stopped": stopped}
