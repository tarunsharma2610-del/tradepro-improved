import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import health
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import SessionLocal
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
            .filter(MarketDataSubscription.is_active.is_(True))
            .all()
        )
        grouped: dict[tuple, list[str]] = {}
        modes: dict[object, set[str]] = {}
        for row in rows:
            modes.setdefault(row.user_id, set()).add(row.feed_mode)
            grouped.setdefault((row.user_id, row.feed_mode), []).append(
                row.instrument.instrument_key
            )
    finally:
        db.close()

    for (user_id, mode), instrument_keys in grouped.items():
        if len(modes.get(user_id, set())) != 1:
            logger.error(
                "Skipping market stream restore for user=%s: conflicting active feed modes=%s",
                user_id, sorted(modes[user_id]),
            )
            continue
        try:
            streamer = await market_data_stream_manager.start(
                user_id, list(dict.fromkeys(instrument_keys)), mode=mode
            )
            logger.info(
                "Restored desired market stream user=%s mode=%s instruments=%s connected=%s",
                user_id, mode, len(streamer.instrument_keys), streamer.connected,
            )
        except Exception:
            logger.exception("Could not restore desired market stream for user=%s", user_id)


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
