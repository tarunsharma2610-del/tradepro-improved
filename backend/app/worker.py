"""
Run with: python -m app.worker

Deliberately the same image/dependencies as the API (see backend/Dockerfile
and docker-compose.yml's `worker` service) -- this file is a different
entrypoint into the same codebase, not a second implementation of
anything.

Independent cadences and event-driven consumers share one worker container
rather than multiplying services that do not need separate deployment units:
- run_once(): indicator strategy evaluation and PAPER limit matching, every
  5 min during market hours.
- run_telegram_poll(): Telegram getUpdates, every 30s.
- run_news_ingest(): RSS ingestion, every 30 min.
- Redis quote ingress feeds a bounded scanner/dispatcher worker pool.
- Durable PAPER stop-event recovery scans expired claims every 5s.
The event-driven consumers run independently of the periodic strategy loop;
failures are logged and retried without blocking Telegram/news scheduling.
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
from app.services.market_scanner import MarketScanner
from app.services.market_data_metrics import RedisDispatchMetricsExporter
from app.services.market_quote_dispatcher import MarketQuoteDispatcher
from app.services.market_quote_dispatch_worker import MarketQuoteDispatchWorker
from app.services.market_scan_dispatch_pipeline import MarketScanDispatchPipeline
from app.services.paper_stop_event_dispatch_handler import (
    handle_paper_market_observation,
    recover_expired_paper_stop_events_once,
)
from app.services.redis_market_quote_worker import RedisMarketQuoteWorker
from app.services.strategy_execution_service import StrategyExecutionService
from app.services.telegram_service import TelegramService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("trading_platform.worker")

STRATEGY_EVAL_INTERVAL_SECONDS = 300  # 5 minutes -- matches the 5-minute candles the strategy engine reads
TELEGRAM_POLL_INTERVAL_SECONDS = 30
NEWS_INGEST_INTERVAL_SECONDS = 1800  # 30 minutes
PAPER_STOP_RECOVERY_INTERVAL_SECONDS = 5
MARKET_DISPATCH_WORKER_COUNT = 4
MARKET_DISPATCH_QUEUE_CAPACITY = 8192
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


async def run_once(*, scanner: MarketScanner | None = None) -> int:
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
            result = await StrategyExecutionService(session, scanner=scanner).evaluate(strategy)
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


async def run_paper_stop_event_recovery() -> None:
    """Resume expired durable PAPER stop claims independently of Redis."""
    while True:
        try:
            recovered = await recover_expired_paper_stop_events_once()
            if recovered:
                logger.info("Recovered %s expired PAPER stop event(s).", recovered)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("PAPER stop-event recovery failed this pass -- will retry.")
        await asyncio.sleep(PAPER_STOP_RECOVERY_INTERVAL_SECONDS)


async def main() -> None:
    logger.info(
        "Worker started. Strategies every %ss (market hours), Telegram every %ss, news every %ss; "
        "PAPER quote workers=%s queue_capacity=%s recovery every %ss.",
        STRATEGY_EVAL_INTERVAL_SECONDS, TELEGRAM_POLL_INTERVAL_SECONDS,
        NEWS_INGEST_INTERVAL_SECONDS, MARKET_DISPATCH_WORKER_COUNT,
        MARKET_DISPATCH_QUEUE_CAPACITY, PAPER_STOP_RECOVERY_INTERVAL_SECONDS,
    )
    last_strategy_eval = 0.0
    last_news_ingest = 0.0
    scanner = MarketScanner()
    dispatcher = MarketQuoteDispatcher(max_pending_keys=MARKET_DISPATCH_QUEUE_CAPACITY)
    pipeline = MarketScanDispatchPipeline(scanner=scanner, dispatcher=dispatcher)
    quote_worker = RedisMarketQuoteWorker(on_quote=pipeline.on_quote)
    metrics_exporter = RedisDispatchMetricsExporter()

    async def export_dispatch_metrics() -> None:
        while True:
            try:
                await metrics_exporter.flush_once(quote_worker.redis)
            except asyncio.CancelledError:
                raise
            except Exception:
                # Metrics must never stop quote ingress or PAPER evaluation.
                logger.exception("Could not export PAPER dispatch metrics to Redis")
            await asyncio.sleep(5)

    metrics_export_task = asyncio.create_task(
        export_dispatch_metrics(), name="paper-dispatch-metrics-export"
    )
    quote_worker_task = asyncio.create_task(
        quote_worker.run_forever(), name="redis-market-quote-worker"
    )
    # Independent instrument keys can be processed concurrently. The
    # dispatcher still enforces single-flight ownership per user/instrument.
    dispatch_worker_tasks = [
        asyncio.create_task(
            MarketQuoteDispatchWorker(
                dispatcher,
                handle_paper_market_observation,
                max_attempts=5,
                on_exhausted=lambda item: scanner.clear_instrument(
                    item.user_id, item.instrument_key
                ),
            ).run(),
            name=f"paper-market-quote-dispatch-worker-{index + 1}",
        )
        for index in range(MARKET_DISPATCH_WORKER_COUNT)
    ]
    stop_recovery_task = asyncio.create_task(
        run_paper_stop_event_recovery(), name="paper-stop-event-recovery"
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
                        logger.info("Evaluated %s active strategies this pass.", evaluated)
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
        # Stop ingress first, then release any in-flight dispatch item. A
        # process restart can recover committed claims from PostgreSQL even
        # when the in-memory Redis/dispatcher queue is lost.
        quote_worker_task.cancel()
        await asyncio.gather(quote_worker_task, return_exceptions=True)
        for task in dispatch_worker_tasks:
            task.cancel()
        stop_recovery_task.cancel()
        await asyncio.gather(
            *dispatch_worker_tasks, stop_recovery_task, return_exceptions=True
        )
        metrics_export_task.cancel()
        await asyncio.gather(metrics_export_task, return_exceptions=True)
        # Final flush after dispatch consumers stop; a repeated sequence is
        # safe if a previous Redis response was lost after its Lua commit.
        try:
            await metrics_exporter.flush_once(quote_worker.redis)
        except Exception:
            logger.exception("Final PAPER dispatch metrics flush failed")
        await quote_worker.close()


if __name__ == "__main__":
    asyncio.run(main())
