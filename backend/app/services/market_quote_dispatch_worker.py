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

    async def run(self) -> None:
        """Run until cancelled; retain key ownership while retrying with capped backoff."""
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
                        logger.exception(
                            "Market quote handler failed user=%s instrument=%s attempt=%s error=%s",
                            item.user_id, item.instrument_key, failures, type(exc).__name__,
                        )
                        # Keep single-flight ownership during backoff. Newer
                        # quotes coalesce behind this item; another worker
                        # cannot race a retry of the same user/instrument key.
                        delay = min(
                            self.min_backoff_seconds * (2 ** min(failures - 1, 20)),
                            self.max_backoff_seconds,
                        )
                        if delay:
                            await asyncio.sleep(delay)
                    else:
                        self.dispatcher.task_done()
                        self.processed_count += 1
                        break
            except asyncio.CancelledError:
                # The current observation (or its newest coalesced successor)
                # remains eligible after graceful worker shutdown.
                self.dispatcher.release()
                raise
