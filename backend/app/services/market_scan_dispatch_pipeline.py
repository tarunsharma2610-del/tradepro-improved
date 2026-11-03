"""Validated quote-to-dispatch adapter for the PAPER market-data pipeline.

This boundary performs only in-memory validation and bounded dispatch. It does
not access the database, create trading signals, evaluate strategies, or call
broker order endpoints. Runtime worker supervision is configured separately.
"""
from uuid import UUID

from app.services.market_quote_dispatcher import MarketQuoteDispatcher
from app.services.market_scanner import MarketScanner


class MarketScanDispatchPipeline:
    """Convert trusted Redis snapshots into bounded scanner observations."""

    def __init__(
        self,
        *,
        scanner: MarketScanner | None = None,
        dispatcher: MarketQuoteDispatcher | None = None,
    ) -> None:
        self.scanner = scanner or MarketScanner()
        self.dispatcher = dispatcher or MarketQuoteDispatcher()
        self.accepted_observations = 0
        self.rejected_quotes = 0
        self.rejected_dispatches = 0

    def on_quote(self, user_id: UUID | str, quote: dict) -> bool:
        """Redis worker callback; return True only when dispatch accepted it."""
        observation = self.scanner.process_quote(user_id, quote)
        if observation is None:
            self.rejected_quotes += 1
            return False
        if not self.dispatcher.publish(observation):
            self.rejected_dispatches += 1
            # Scanner validation advances its in-memory high-water mark.
            # Clear only this instrument so the Redis consumer's periodic
            # authoritative-snapshot sweep can retry it without re-admitting
            # duplicates for every other instrument owned by this user.
            # Durable per-strategy quote ordering in PostgreSQL remains the
            # final duplicate/regression boundary.
            self.scanner.clear_instrument(user_id, observation.instrument_key)
            return False
        self.accepted_observations += 1
        return True

    def clear_user(self, user_id: UUID | str) -> None:
        """Clear scanner memory when a user's subscriptions are removed."""
        self.scanner.clear_user(user_id)
