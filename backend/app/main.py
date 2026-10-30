import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import health
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.broker_connection import BrokerConnection
from app.models.market_data_subscription import MarketDataSubscription
from app.services.market_data_stream_manager import market_data_stream_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trading_platform")


async def _restore_desired_market_streams() -> None:
    """Recreate API-owned Upstox streams after an unclean process restart.

    Only persisted active subscriptions are restored. Explicit user stop
    deactivates rows first, so a deliberate stop is not undone at startup.
    """
    db = SessionLocal()
    try:
        rows = (
            db.query(MarketDataSubscription)
            .join(
                BrokerConnection,
                MarketDataSubscription.broker_connection_id == BrokerConnection.id,
            )
            .filter(
                MarketDataSubscription.is_active.is_(True),
                BrokerConnection.broker == "upstox",
                BrokerConnection.user_id == MarketDataSubscription.user_id,
            )
            .all()
        )
        grouped: dict[object, dict[str, set[str]]] = {}
        for row in rows:
            grouped.setdefault(row.user_id, {}).setdefault(row.feed_mode, set()).add(
                row.instrument.instrument_key
            )
    finally:
        db.close()

    for user_id, subscriptions_by_mode in grouped.items():
        # A single instrument cannot be assigned to multiple modes. Treat
        # conflicting legacy rows as corrupt desired state and restore none.
        assigned_modes: dict[str, str] = {}
        conflicts: set[str] = set()
        for feed_mode, keys in subscriptions_by_mode.items():
            for key in keys:
                previous = assigned_modes.get(key)
                if previous is not None and previous != feed_mode:
                    conflicts.add(key)
                assigned_modes[key] = feed_mode
        if conflicts:
            logger.error(
                "Skipping market stream restore for user=%s: instruments have conflicting feed modes=%s",
                user_id, sorted(conflicts)[:10],
            )
            continue

        for mode, instrument_keys in sorted(subscriptions_by_mode.items()):
            try:
                streamer = await market_data_stream_manager.start(
                    user_id, sorted(instrument_keys), mode=mode
                )
                logger.info(
                    "Restored desired market stream user=%s mode=%s instruments=%s connected=%s",
                    user_id, mode, len(instrument_keys), streamer.connected,
                )
            except Exception:
                # Do not prevent other modes or users from being restored.
                logger.exception(
                    "Could not restore desired market stream user=%s mode=%s",
                    user_id, mode,
                )


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.MASTER_ENCRYPTION_KEY:
        logger.warning(
            "MASTER_ENCRYPTION_KEY is not set. The app will start, but saving any broker "
            "credentials or platform settings will fail until it's configured. Run setup.sh."
        )
    if settings.is_live_trading_enabled:
        logger.warning(
            "TRADING_MODE=LIVE — live order placement is not implemented yet in this phase; "
            "this flag exists for future phases and should stay PAPER until that work is reviewed."
        )
    logger.info(
        "Trading Platform API starting in %s mode (trading mode: %s)", settings.ENVIRONMENT, settings.TRADING_MODE
    )
    try:
        await _restore_desired_market_streams()
        yield
    finally:
        await market_data_stream_manager.shutdown()


app = FastAPI(title=settings.APP_NAME, version="0.1.0-phase1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,  # required for the httpOnly auth cookies to work cross-port in dev
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)  # unversioned: Docker/nginx healthchecks hit this directly
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {"name": settings.APP_NAME, "status": "running", "docs": "/docs"}
