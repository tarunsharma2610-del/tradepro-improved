"""Fail-closed live-order preflight; deliberately not wired to submission.

This module is a safety boundary only. It does not create Order rows, call
BrokerAdapter.place_order, persist broker IDs, or mutate any accounting.
Until a reviewed account-wide risk gate is supplied and the independent
environment interlocks are enabled, preflight is rejected.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.broker_connection import BrokerConnection
from app.models.instrument import Instrument
from app.models.portfolio import Portfolio
from app.repositories.broker_connection_repository import BrokerConnectionRepository
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.instrument_validation import validate_instrument_segment


class LiveExecutionBlocked(ValueError):
    """A required live-trading safety gate failed."""


@dataclass(frozen=True)
class LiveOrderIntent:
    portfolio_id: UUID
    instrument_id: UUID
    side: str
    order_type: str
    segment: str
    quantity: int
    limit_price: Decimal | None = None
    execution_reason: str = "MANUAL"
    strategy_id: UUID | None = None


@dataclass(frozen=True)
class LiveRiskDecision:
    allowed: bool
    reason: str | None = None


@dataclass(frozen=True)
class LiveOrderPreflight:
    """Validated, non-secret plan; this is not a submitted or persisted order."""

    user_id: UUID
    portfolio_id: UUID
    instrument_id: UUID
    broker_name: str
    broker_connection_id: UUID
    instrument_key: str
    side: str
    order_type: str
    segment: str
    quantity: int
    limit_price: Decimal | None


LiveRiskGate = Callable[[UUID, Portfolio, Instrument, LiveOrderIntent], LiveRiskDecision]


class LiveExecutionService:
    """Validate a future live intent without performing broker/network writes.

    A concrete account-wide risk gate is mandatory. The existing strategy risk
    engine is not a substitute: it does not cover all manual/live exposures,
    margin, order frequency, market session, or stale-quote controls.
    """

    BROKER_NAME = "upstox"

    def __init__(self, db: Session, risk_gate: LiveRiskGate | None = None):
        self.db = db
        self.connections = BrokerConnectionRepository(db)
        self.credentials = BrokerCredentialsService(db)
        self.risk_gate = risk_gate

    def preflight(
        self,
        user_id: UUID,
        intent: LiveOrderIntent,
        *,
        user_confirmed: bool = False,
    ) -> LiveOrderPreflight:
        # These interlocks run before any database lookup or credential access.
        if settings.TRADING_MODE.strip().upper() != "LIVE":
            raise LiveExecutionBlocked("TRADING_MODE must be LIVE; no order was submitted.")
        if not settings.LIVE_ORDER_SUBMISSION_ENABLED:
            raise LiveExecutionBlocked(
                "LIVE_ORDER_SUBMISSION_ENABLED is off; live execution remains disabled."
            )
        if user_confirmed is not True:
            raise LiveExecutionBlocked("Explicit user confirmation is required for a live order.")
        if self.risk_gate is None:
            raise LiveExecutionBlocked("No reviewed account-wide live risk gate is configured.")

        normalized_limit_price = self._validate_intent(intent)

        portfolio = (
            self.db.query(Portfolio)
            .filter(
                Portfolio.id == intent.portfolio_id,
                Portfolio.user_id == user_id,
            )
            .with_for_update()
            .first()
        )
        if portfolio is None:
            raise LiveExecutionBlocked("Portfolio not found.")
        if not portfolio.is_active:
            raise LiveExecutionBlocked("Portfolio is inactive.")

        instrument = self.db.get(Instrument, intent.instrument_id)
        if instrument is None or not instrument.is_active:
            raise LiveExecutionBlocked("Instrument not found or inactive.")
        try:
            validate_instrument_segment(instrument, intent.segment)
        except ValueError as exc:
            raise LiveExecutionBlocked(str(exc)) from exc

        if intent.execution_reason == "STRATEGY":
            if intent.strategy_id is None:
                raise LiveExecutionBlocked("Strategy orders require a strategy_id.")
            if not settings.AUTOMATED_ENTRIES_ENABLED:
                raise LiveExecutionBlocked("Automated entries are disabled.")

        connection: BrokerConnection | None = self.connections.get_for_user(
            user_id, self.BROKER_NAME
        )
        if connection is None or not connection.is_connected:
            raise LiveExecutionBlocked("No verified Upstox connection is available.")
        try:
            access_token = self.credentials.get_access_token(user_id, self.BROKER_NAME)
        except Exception as exc:
            raise LiveExecutionBlocked("Upstox access token could not be validated.") from exc
        if not isinstance(access_token, str) or not access_token.strip():
            raise LiveExecutionBlocked("Upstox access token is missing, expired, or unusable.")

        try:
            decision = self.risk_gate(user_id, portfolio, instrument, intent)
        except Exception as exc:
            raise LiveExecutionBlocked("Live risk gate failed; order is blocked.") from exc
        if not isinstance(decision, LiveRiskDecision):
            raise LiveExecutionBlocked("Live risk gate returned an invalid decision; order is blocked.")
        if not decision.allowed:
            raise LiveExecutionBlocked(
                decision.reason or "Live risk gate rejected the order."
            )

        # Deliberately do not return the access token or an adapter. The next
        # reviewed step must implement durable intent/tag recovery before any
        # broker submission can be considered.
        return LiveOrderPreflight(
            user_id=user_id,
            portfolio_id=portfolio.id,
            instrument_id=instrument.id,
            broker_name=self.BROKER_NAME,
            broker_connection_id=connection.id,
            instrument_key=instrument.instrument_key,
            side=intent.side,
            order_type=intent.order_type,
            segment=intent.segment,
            quantity=intent.quantity,
            limit_price=normalized_limit_price,
        )

    @staticmethod
    def _validate_intent(intent: LiveOrderIntent) -> Decimal | None:
        if not isinstance(intent.side, str) or intent.side not in {"BUY", "SELL"}:
            raise LiveExecutionBlocked("Side must be BUY or SELL.")
        if not isinstance(intent.order_type, str) or intent.order_type not in {"MARKET", "LIMIT"}:
            raise LiveExecutionBlocked("Order type must be MARKET or LIMIT.")
        if type(intent.quantity) is not int or intent.quantity <= 0:
            raise LiveExecutionBlocked("Quantity must be a positive integer.")
        if not isinstance(intent.segment, str) or intent.segment not in {"EQUITY_DELIVERY", "EQUITY_INTRADAY"}:
            raise LiveExecutionBlocked("Only verified equity delivery/intraday segments are supported.")
        if intent.order_type == "LIMIT":
            if intent.limit_price is None:
                raise LiveExecutionBlocked("LIMIT orders require a positive limit price.")
            try:
                limit_price = Decimal(str(intent.limit_price))
            except (InvalidOperation, TypeError, ValueError):
                raise LiveExecutionBlocked("LIMIT price must be a valid positive amount.") from None
            if not limit_price.is_finite() or limit_price <= 0:
                raise LiveExecutionBlocked("LIMIT price must be a valid positive amount.")
        elif intent.limit_price is not None:
            raise LiveExecutionBlocked("MARKET orders must not include a limit price.")
        if not isinstance(intent.execution_reason, str) or intent.execution_reason not in {"MANUAL", "STRATEGY"}:
            raise LiveExecutionBlocked("Unsupported execution reason.")
        return limit_price if intent.order_type == "LIMIT" else None
