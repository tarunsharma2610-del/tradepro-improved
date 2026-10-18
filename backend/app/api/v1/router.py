from fastapi import APIRouter

from app.api.v1 import admin, auth, backtests, instruments, news, portfolios, safety, settings, strategies, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(settings.router)
api_router.include_router(instruments.router)
api_router.include_router(portfolios.router)
api_router.include_router(strategies.router)
api_router.include_router(backtests.router)
api_router.include_router(news.router)
api_router.include_router(admin.router)
api_router.include_router(safety.router)
