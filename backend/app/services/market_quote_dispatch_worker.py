"""Supervised async worker for bounded PAPER market-quote dispatch.

This worker deliberately does not submit broker orders. Its handler must be a
PAPER-only observation/evaluation callback. Repeated failures are bounded so
one poison instrument cannot occupy a worker forever; the caller resets scanner
high-water state so Redis snapshot recovery can safely offer the quote again.
"""
import asyncio
import logging
from collections.abc import Awaitable, Callable

from app.services.market_data_metrics import increment
from app.services.market_quote_dispatcher import (
    DispatchedMarketObservation,
    MarketQuoteDispatcher,
)

logger = logging.getLogger(__name__)


class MarketQuoteDispatchWorker:
    """Consume dispatch items with cancellation-safe release and bounded retry."""

    def __init__(
        self,
        dispatcher: MarketQuoteDispatcher,
        handler: Callable[[DispatchedMarketObservation], Awaitable[None]],
        *,
        min_backoff_seconds: float = 0.25,
        max_backoff_seconds: float = 5.0,
        max_attempts: int = 5,
        on_exhausted: Callable[[DispatchedMarketObservation], None] | None = None,
    ) -> None:
        if min_backoff_seconds < 0 or max_backoff_seconds < min_backoff_seconds:
            raise ValueError("Invalid dispatch retry backoff bounds.")
        if isinstance(max_attempts, bool) or not isinstance(max_attempts, int) or max_attempts < 1:
            raise ValueError("Dispatch max_attempts must be a positive integer.")
        self.dispatcher = dispatcher
        self.handler = handler
        self.min_backoff_seconds = min_backoff_seconds
        self.max_backoff_seconds = max_backoff_seconds
        self.max_attempts = max_attempts
        self.on_exhausted = on_exhausted
        self.processed_count = 0
        self.failure_count = 0
        self.exhausted_count = 0

    async def run(self) -> None:
        """Run until cancelled; bounded retries yield capacity to other keys."""
        while True:
            item = await self.dispatcher.get()
            try:
                failures = 0
                while True:
                    try:
                        await self.handler(item)
                    except asyncio.CancelledError:
                        raise
                    except Exception as exc:
                        failures += 1
                        self.failure_count += 1
                        increment("market_quote_dispatch_handler_failures_total")
                        logger.exception(
                            "Market quote handler failed user=%s instrument=%s attempt=%s/%s error=%s",
                            item.user_id, item.instrument_key, failures,
                            self.max_attempts, type(exc).__name__,
                        )
                        if failures >= self.max_attempts:
                            # The current observation may already have committed
                            # a durable stop claim before an uncertain failure.
                            # Clearing scanner high-water lets Redis's
                            # authoritative-snapshot sweep replay the same quote;
                            # the database event/order identity makes replay safe.
                            if self.on_exhausted is not None:
                                try:
                                    self.on_exhausted(item)
                                except Exception:
                                    logger.exception(
                                        "Failed to reset scanner state after dispatch retries "
                                        "user=%s instrument=%s",
                                        item.user_id, item.instrument_key,
                                    )
                                    # Do not acknowledge an item if recovery
                                    # cannot be re-armed; cancellation-safe
                                    # release preserves it for supervision.
                                    self.dispatcher.release()
                                    raise
                            self.dispatcher.task_done()
                            self.exhausted_count += 1
                            increment("market_quote_dispatch_exhausted_total")
                            break

                        delay = min(
                            self.min_backoff_seconds * (2 ** min(failures - 1, 20)),
                            self.max_backoff_seconds,
                        )
                        if delay:
                            await asyncio.sleep(delay)
                    else:
                        self.dispatcher.task_done()
                        self.processed_count += 1
                        increment("market_quote_dispatch_processed_total")
                        break
            except asyncio.CancelledError:
                # The current observation (or its newest coalesced successor)
                # remains eligible after graceful worker shutdown.
                self.dispatcher.release()
                raise
