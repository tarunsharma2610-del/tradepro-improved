"""
Run with: python -m app.worker

Deliberately the same image/dependencies as the API (see backend/Dockerfile
and docker-compose.yml's `worker` service) -- this file is a different
entrypoint into the same codebase, not a second implementation of
anything.

Three independent cadences share one process rather than three separate
containers, since none of them is expensive enough alone to justify its
own container + healthcheck + restart policy:
- run_once(): strategy evaluation, every 5 min, market hours only.
- run_telegram_poll(): Telegram getUpdates, every 30s, always -- a user
  linking their account shouldn't feel like it takes minutes to register.
- run_news_ingest(): RSS ingestion, every 30 min, always -- news doesn't
  stop outside market hours and doesn't need to be as fresh as prices.
Each is independently testable and independently error-isolated from the
other two; a failure in one never blocks or crashes the others.
"""

import asyncio
import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.database import SessionLocal
from app.models.strategy import Strategy
from app.repositories.strategy_repository import StrategyRepository
from app.services.execution_service import ExecutionService
from app.services.news_service import NewsService
from app.services.redis_market_quote_worker import RedisMarketQuoteWorker
from app.services.strategy_execution_service import StrategyExecutionService
from app.services.telegram_service import TelegramService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trading_platform.worker")

STRATEGY_EVAL_INTERVAL_SECONDS = 300  # 5 minutes -- matches the 5-minute candles the strategy engine reads
TELEGRAM_POLL_INTERVAL_SECONDS = 30
NEWS_INGEST_INTERVAL_SECONDS = 1800  # 30 minutes
IST = ZoneInfo("Asia/Kolkata")


def _is_market_hours(now: datetime | None = None) -> bool:
    """NSE regular session: 9:15-15:30 IST, Monday-Friday. Deliberately
    does not account for exchange holidays -- see README known
    limitations; a strategy just won't find fresh candles to act on
    outside real trading anyway, so this is a courtesy to avoid hammering
    Upstox with pointless calls, not a correctness-critical check."""
    now = (now or datetime.now(IST)).astimezone(IST)
    if now.weekday() >= 5:  # 5=Saturday, 6=Sunday
        return False
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open <= now <= market_close


async def run_once() -> int:
    """Match pending paper limits, then evaluate every active strategy.

    Returns the number of strategies evaluated. Matcher failure is isolated
    from strategy evaluation; a single strategy failure never blocks others.
    """
    db = SessionLocal()
    try:
        try:
            matched = await ExecutionService(db).match_pending_limit_orders()
            if matched:
                logger.info("Matched %s paper LIMIT order(s).", matched)
        except Exception:
            logger.exception("Paper limit-order matching failed this pass -- continuing with strategies")
            db.rollback()
        strategy_ids = [s.id for s in StrategyRepository(db).list_all_active()]
    finally:
        db.close()

    count = 0
    for strategy_id in strategy_ids:
        session = SessionLocal()
        try:
            strategy = session.get(Strategy, strategy_id)
            if strategy is None or not strategy.is_active:
                continue  # deleted or deactivated between the list and now
            result = await StrategyExecutionService(session).evaluate(strategy)
            logger.info("strategy=%s signal=%s reason=%s", strategy_id, result.signal, result.reason)
            count += 1
        except Exception:
            logger.exception("Evaluation failed for strategy=%s -- continuing with the rest", strategy_id)
            session.rollback()
        finally:
            session.close()

    return count


async def run_telegram_poll() -> int:
    session = SessionLocal()
    try:
        return await TelegramService(session).process_updates()
    except Exception:
        logger.exception("Telegram polling failed this tick -- will retry next one")
        return 0
    finally:
        session.close()


async def run_news_ingest() -> dict[str, int]:
    session = SessionLocal()
    try:
        return await NewsService(session).ingest_all_active()
    except Exception:
        logger.exception("News ingestion failed this tick -- will retry next one")
        return {}
    finally:
        session.close()


async def main() -> None:
    logger.info(
        "Worker started. Strategies every %ss (market hours), Telegram every %ss, news every %ss.",
        STRATEGY_EVAL_INTERVAL_SECONDS, TELEGRAM_POLL_INTERVAL_SECONDS, NEWS_INGEST_INTERVAL_SECONDS,
    )
    last_strategy_eval = 0.0
    last_news_ingest = 0.0
    quote_worker = RedisMarketQuoteWorker()
    quote_worker_task = asyncio.create_task(
        quote_worker.run_forever(), name="redis-market-quote-worker"
    )

    try:
        while True:
            now = time.monotonic()

            completed_links = await run_telegram_poll()
            if completed_links:
                logger.info("Completed %s Telegram link(s) this tick.", completed_links)

            if now - last_strategy_eval >= STRATEGY_EVAL_INTERVAL_SECONDS:
                if _is_market_hours():
                    evaluated = await run_once()
                    if evaluated:
                        logger.info("Evaluated %s active strateg(ies) this pass.", evaluated)
                else:
                    logger.debug("Outside market hours -- skipping strategy evaluation this pass.")
                last_strategy_eval = now

            if now - last_news_ingest >= NEWS_INGEST_INTERVAL_SECONDS:
                results = await run_news_ingest()
                if results:
                    logger.info("News ingestion: %s", results)
                last_news_ingest = now

            await asyncio.sleep(TELEGRAM_POLL_INTERVAL_SECONDS)
    finally:
        quote_worker_task.cancel()
        await asyncio.gather(quote_worker_task, return_exceptions=True)
        await quote_worker.close()


if __name__ == "__main__":
    asyncio.run(main())
