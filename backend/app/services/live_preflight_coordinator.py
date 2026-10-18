"""Async, preflight-only composition of Upstox snapshots and live risk checks.

This service performs read-only broker calls and returns a validated preflight
plan. It is intentionally not registered in any API route or worker and never
submits, persists, modifies, or cancels an order.
"""
from datetime import datetime, timezone
from typing import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from app.brokers.base import BrokerAdapter
from app.brokers.registry import get_broker_adapter
from app.core.config import settings
from app.models.instrument import Instrument
from app.models.portfolio import Portfolio
from app.repositories.broker_connection_repository import BrokerConnectionRepository
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.live_execution_service import (
    LiveExecutionBlocked,
    LiveExecutionService,
    LiveOrderIntent,
    LiveOrderPreflight,
)
from app.services.live_pre_trade_risk_gate import AccountWideLiveRiskGate
from app.services.upstox_live_risk_snapshot_service import UpstoxLiveRiskSnapshotService


Clock = Callable[[], datetime]


class LivePreflightCoordinator:
    """Gather fresh read-only snapshots, then run the existing risk preflight.

    The existing PAPER-only execution service is not changed. This coordinator
    remains an unregistered foundation: a successful result is only a plan and
    is never permission to send a broker order from this module.
    """

    BROKER_NAME = "upstox"

    def __init__(
        self,
        db: Session,
        *,
        adapter: BrokerAdapter | None = None,
        clock: Clock | None = None,
    ):
        self.db = db
        self.adapter = adapter or get_broker_adapter(self.BROKER_NAME)
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.connections = BrokerConnectionRepository(db)
        self.credentials = BrokerCredentialsService(db)

    async def preflight(
        self,
        user_id: UUID,
        intent: LiveOrderIntent,
        *,
        user_confirmed: bool = False,
    ) -> LiveOrderPreflight:
        # Match the existing service's earliest interlocks before any DB,
        # credential, or broker access. This coordinator cannot bypass them.
        if settings.TRADING_MODE.strip().upper() != "LIVE":
            raise LiveExecutionBlocked("TRADING_MODE must be LIVE; no order was submitted.")
        if not settings.LIVE_ORDER_SUBMISSION_ENABLED:
            raise LiveExecutionBlocked(
                "LIVE_ORDER_SUBMISSION_ENABLED is off; live execution remains disabled."
            )
        if user_confirmed is not True:
            raise LiveExecutionBlocked("Explicit user confirmation is required for a live order.")

        portfolio = (
            self.db.query(Portfolio)
            .filter(Portfolio.id == intent.portfolio_id, Portfolio.user_id == user_id)
            .first()
        )
        if portfolio is None or not portfolio.is_active:
            raise LiveExecutionBlocked("An active portfolio owned by this user is required.")
        instrument = self.db.get(Instrument, intent.instrument_id)
        if instrument is None or not instrument.is_active:
            raise LiveExecutionBlocked("Instrument not found or inactive.")

        connection = self.connections.get_for_user(user_id, self.BROKER_NAME)
        if connection is None or not connection.is_connected:
            raise LiveExecutionBlocked("No verified Upstox connection is available.")
        access_token = self.credentials.get_access_token(user_id, self.BROKER_NAME)
        if not isinstance(access_token, str) or not access_token.strip():
            raise LiveExecutionBlocked("Upstox access token is missing, expired, or unusable.")

        collected_at = self.clock()
        if collected_at.tzinfo is None or collected_at.utcoffset() is None:
            raise LiveExecutionBlocked("Preflight clock must return a timezone-aware timestamp.")
        try:
            snapshots = await UpstoxLiveRiskSnapshotService(
                self.db, self.adapter, access_token
            ).collect(user_id, instrument, intent, now=collected_at)
        except Exception as exc:
            raise LiveExecutionBlocked(
                "Upstox risk snapshots could not be validated; live preflight blocked."
            ) from exc

        gate = AccountWideLiveRiskGate(
            self.db,
            quote_provider=snapshots.quote_provider,
            session_provider=snapshots.session_provider,
            positions_provider=snapshots.positions_provider,
            funds_provider=snapshots.funds_provider,
            margin_provider=snapshots.margin_provider,
            clock=self.clock,
        )
        # preflight revalidates all local intent/connection/interlock rules.
        # No broker order endpoint is called; this returns only a non-secret plan.
        try:
            return LiveExecutionService(self.db, risk_gate=gate).preflight(
                user_id, intent, user_confirmed=user_confirmed
            )
        except LiveExecutionBlocked:
            raise
        except Exception as exc:
            raise LiveExecutionBlocked("Live preflight failed closed; no order was submitted.") from exc
