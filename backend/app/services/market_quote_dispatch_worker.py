"""Supervised async worker for bounded PAPER market-quote dispatch.

This worker deliberately does not submit broker orders. Its handler must be a
PAPER-only observation/evaluation callback; scanner-to-execution wiring stays
behind the separate safety gate.
"""
import asyncio
import logging
from collections.abc import Awaitable, Callable

from app.services.market_quote_dispatcher import (
    DispatchedMarketObservation,
    MarketQuoteDispatcher,
)

logger = logging.getLogger(__name__)


class MarketQuoteDispatchWorker:
    """Consume dispatcher items with cancellation-safe release and bounded retry."""

    def __init__(
        self,
        dispatcher: MarketQuoteDispatcher,
        handler: Callable[[DispatchedMarketObservation], Awaitable[None]],
        *,
        min_backoff_seconds: float = 0.25,
        max_backoff_seconds: float = 5.0,
    ) -> None:
        if min_backoff_seconds < 0 or max_backoff_seconds < min_backoff_seconds:
            raise ValueError("Invalid dispatch retry backoff bounds.")
        self.dispatcher = dispatcher
        self.handler = handler
        self.min_backoff_seconds = min_backoff_seconds
        self.max_backoff_seconds = max_backoff_seconds
        self.processed_count = 0
        self.failure_count = 0
        self._failures_by_key: dict[tuple[str, str], int] = {}

    async def run(self) -> None:
        """Run until cancelled; failed items are released and retried with backoff."""
        while True:
            item = await self.dispatcher.get()
            key = (item.user_id, item.instrument_key)
            try:
                await self.handler(item)
            except asyncio.CancelledError:
                # The current observation (or its newest coalesced successor)
                # must remain eligible after graceful worker shutdown.
                self.dispatcher.release()
                raise
            except Exception as exc:
                self.failure_count += 1
                failures = self._failures_by_key.get(key, 0) + 1
                self._failures_by_key[key] = failures
                logger.exception(
                    "Market quote handler failed user=%s instrument=%s attempt=%s error=%s",
                    item.user_id, item.instrument_key, failures, type(exc).__name__,
                )
                self.dispatcher.release()
                delay = min(
                    self.min_backoff_seconds * (2 ** min(failures - 1, 20)),
                    self.max_backoff_seconds,
                )
                if delay:
                    await asyncio.sleep(delay)
            else:
                self.dispatcher.task_done()
                self._failures_by_key.pop(key, None)
                self.processed_count += 1
