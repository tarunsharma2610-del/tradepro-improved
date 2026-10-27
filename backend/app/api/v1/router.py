from fastapi import APIRouter

from app.api.v1 import admin, auth, backtests, broker_charge_evidence, instruments, market_data, news, portfolios, reconciliation, settings, strategies, upstox_charges, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(broker_charge_evidence.router)
api_router.include_router(users.router)
api_router.include_router(settings.router)
api_router.include_router(instruments.router)
api_router.include_router(market_data.router)
api_router.include_router(portfolios.router)
api_router.include_router(reconciliation.router)
api_router.include_router(upstox_charges.router)
api_router.include_router(strategies.router)
api_router.include_router(backtests.router)
api_router.include_router(news.router)
api_router.include_router(admin.router)
