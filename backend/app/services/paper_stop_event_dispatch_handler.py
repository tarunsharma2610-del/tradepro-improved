"""Database-backed handler for dispatched scanner observations.

The handler commits stop-event claims before executing them. The execution
service then commits the PAPER order, accounting mutations and terminal event
state atomically. This module never calls a broker order-write endpoint.
"""
from datetime import datetime, timezone
from uuid import UUID

from app.core.database import SessionLocal
from app.models.instrument import Instrument
from app.models.paper_stop_event import PaperStopEvent
from app.services.market_quote_dispatcher import DispatchedMarketObservation
from app.services.paper_stop_event_execution_service import PaperStopEventExecutionService
from app.services.paper_stop_event_intake_service import (
    PaperStopEventIntakeService,
    PaperStopObservationRejected,
)
from app.services.paper_stop_event_lifecycle import PaperStopEventLifecycle


_ACTIVE_EVENT_STATES = ("CLAIMED", "EXECUTING", "RETRYABLE")


async def _execute_event(event_id: UUID, user_id: UUID) -> None:
    """Recover an expired claim if needed, then execute its current token."""
    session = SessionLocal()
    try:
        event = (
            session.query(PaperStopEvent)
            .filter(PaperStopEvent.id == event_id)
            .with_for_update()
            .first()
        )
        if event is None or event.state not in _ACTIVE_EVENT_STATES:
            session.rollback()
            return

        now = datetime.now(timezone.utc)
        claimed_until = event.claimed_until
        if claimed_until is not None and claimed_until.tzinfo is None:
            claimed_until = claimed_until.replace(tzinfo=timezone.utc)
        if claimed_until is None or claimed_until <= now:
            event = PaperStopEventLifecycle(session).reclaim_expired(
                event_id=event_id, now=now,
            )
            if event is None:
                session.commit()
                return

        if event.state != "CLAIMED" or event.claim_token is None:
            session.commit()
            return
        claim_token = event.claim_token
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    execution_session = SessionLocal()
    try:
        await PaperStopEventExecutionService(execution_session).execute_claimed(
            user_id=user_id,
            event_id=event_id,
            claim_token=claim_token,
        )
    finally:
        execution_session.close()


async def handle_paper_market_observation(
    item: DispatchedMarketObservation,
) -> None:
    """Persist a triggered stop and execute/recover its durable PAPER event.

    An exact quote identity is looked up before intake so a redelivered Redis
    snapshot can resume a claim committed by a previous worker process even
    when the quote has since become too old for *new* stop evaluation.
    """
    try:
        user_id = UUID(item.user_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("Dispatched observation has an invalid user UUID.") from exc

    session = SessionLocal()
    try:
        instrument = (
            session.query(Instrument)
            .filter(Instrument.instrument_key == item.instrument_key)
            .first()
        )
        if instrument is None:
            session.rollback()
            return

        matching = (
            session.query(PaperStopEvent.id)
            .filter(
                PaperStopEvent.user_id == user_id,
                PaperStopEvent.instrument_id == instrument.id,
                PaperStopEvent.quote_epoch == item.epoch,
                PaperStopEvent.quote_version == item.version,
                PaperStopEvent.state.in_(_ACTIVE_EVENT_STATES),
            )
            .all()
        )
        event_ids = [row[0] for row in matching]
        session.rollback()
    finally:
        session.close()

    if not event_ids:
        intake_session = SessionLocal()
        try:
            try:
                PaperStopEventIntakeService(intake_session).evaluate_and_claim(
                    item.observation
                )
                intake_session.commit()
            except PaperStopObservationRejected:
                # A quote that waited in a bounded queue may become stale.
                # It cannot create a new event, but any previously committed
                # event for this exact identity was handled by the lookup above.
                intake_session.rollback()
            except Exception:
                intake_session.rollback()
                raise
        finally:
            intake_session.close()

        lookup_session = SessionLocal()
        try:
            instrument = (
                lookup_session.query(Instrument)
                .filter(Instrument.instrument_key == item.instrument_key)
                .first()
            )
            if instrument is None:
                lookup_session.rollback()
                return
            matching = (
                lookup_session.query(PaperStopEvent.id)
                .filter(
                    PaperStopEvent.user_id == user_id,
                    PaperStopEvent.instrument_id == instrument.id,
                    PaperStopEvent.quote_epoch == item.epoch,
                    PaperStopEvent.quote_version == item.version,
                    PaperStopEvent.state.in_(_ACTIVE_EVENT_STATES),
                )
                .all()
            )
            event_ids = [row[0] for row in matching]
            lookup_session.rollback()
        finally:
            lookup_session.close()

    for event_id in event_ids:
        await _execute_event(event_id, user_id)
