"""
Deliberately aggregate-only. An admin gets counts (how many users, how
many active strategies) to gauge platform health, not a way to browse any
specific user's portfolio or trades -- that would cut against the same
multi-tenancy principle the rest of this app enforces ("never trust an id
without checking ownership") in spirit, even though an admin technically
has the database access to bypass it. Nothing here queries by another
user's identity.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from redis.asyncio import from_url

from app.core.config import settings
from app.core.deps import get_db, require_admin
from app.models.backtest import BacktestRun
from app.models.news_item import NewsItem
from app.models.portfolio import Portfolio
from app.models.strategy import Strategy
from app.models.user import User
from app.schemas.admin import PlatformStatsOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=PlatformStatsOut)
def platform_stats(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return PlatformStatsOut(
        total_users=db.query(func.count(User.id)).scalar(),
        total_portfolios=db.query(func.count(Portfolio.id)).scalar(),
        total_active_strategies=db.query(func.count(Strategy.id)).filter(Strategy.is_active.is_(True)).scalar(),
        total_strategies=db.query(func.count(Strategy.id)).scalar(),
        total_news_items=db.query(func.count(NewsItem.id)).scalar(),
        total_backtest_runs=db.query(func.count(BacktestRun.id)).scalar(),
    )


@router.get("/market-data-metrics")
async def market_data_metrics(_admin: User = Depends(require_admin)):
    """Expose shared Redis-aggregated PAPER dispatch counters to admins only."""
    from app.services.market_data_metrics import fleet_snapshot

    redis_client = None
    try:
        redis_client = from_url(settings.REDIS_URL, decode_responses=True)
        return await fleet_snapshot(redis_client)
    except Exception as exc:
        # Never return process-local zeros as if they represented the worker
        # fleet. A missing shared metrics source is an explicit unavailable
        # state, not a healthy-looking empty dashboard.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Shared market-data metrics are temporarily unavailable.",
        ) from exc
    finally:
        if redis_client is not None:
            await redis_client.aclose()
