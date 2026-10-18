from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from app.brokers.base import BrokerCallResult
from app.core.config import settings
from app.models.broker_connection import BrokerConnection
from app.models.broker_order import BrokerOrder
from app.models.order import Order
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.instrument_service import InstrumentService
from app.services.live_execution_service import (
    LiveExecutionBlocked,
    LiveExecutionService,
    LiveOrderIntent,
    LiveOrderPreflight,
    LiveRiskDecision,
)
from app.services.live_order_recovery_service import (
    LiveOrderRecoveryService,
    make_broker_tag,
)


@pytest.fixture()
def recovery_context(db_session, make_user):
    user = make_user()
    portfolio = PortfolioRepository(db_session).create(
        user_id=user.id, name="Recovery test", virtual_capital=Decimal("100000")
    )
    InstrumentService(db_session).seed_defaults()
    instrument = InstrumentRepository(db_session).search("RELIANCE")[0]
    connection = BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="encrypted-key",
        api_secret_encrypted="encrypted-secret",
        redirect_uri="https://example.invalid/callback",
        access_token_encrypted="encrypted-token",
        access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        is_connected=True,
    )
    db_session.add(connection)
    db_session.commit()
    return user, portfolio, instrument, connection


def _enable_preflight(monkeypatch):
    monkeypatch.setattr(settings, "TRADING_MODE", "LIVE")
    monkeypatch.setattr(settings, "LIVE_ORDER_SUBMISSION_ENABLED", True)
    monkeypatch.setattr(settings, "AUTOMATED_ENTRIES_ENABLED", True)
    monkeypatch.setattr(
        BrokerCredentialsService,
        "get_access_token",
        lambda self, user_id, broker: "test-access-token",
    )


def _intent(portfolio, instrument, **overrides):
    values = {
        "portfolio_id": portfolio.id,
        "instrument_id": instrument.id,
        "side": "BUY",
        "order_type": "MARKET",
        "segment": "EQUITY_DELIVERY",
        "quantity": 2,
    }
    values.update(overrides)
    return LiveOrderIntent(**values)


def _service(db_session):
    preflight = LiveExecutionService(
        db_session,
        risk_gate=lambda *_args: LiveRiskDecision(allowed=True),
    )
    return LiveOrderRecoveryService(db_session, preflight_service=preflight)


def _history_row(order_id, tag, instrument_key, *, quantity=2, side="BUY", status="open"):
    return {
        "order_id": order_id,
        "status": status,
        "quantity": quantity,
        "filled_quantity": 0,
        "average_price": 0,
        "tag": tag,
        "instrument_token": instrument_key,
        "transaction_type": side,
    }


def _prepared(db_session, recovery_context, monkeypatch, *, key="client-request-001", quantity=2):
    user, portfolio, instrument, _connection = recovery_context
    _enable_preflight(monkeypatch)
    service = _service(db_session)
    order = service.prepare_intent(
        user.id,
        _intent(portfolio, instrument, quantity=quantity),
        idempotency_key=key,
        user_confirmed=True,
    )
    return service, user, portfolio, instrument, order


def test_broker_tag_is_stable_opaque_and_within_upstox_limit(recovery_context):
    _user, portfolio, _instrument, _connection = recovery_context
    first = make_broker_tag(portfolio.id, "same-request")
    assert first == make_broker_tag(portfolio.id, "same-request")
    assert first != make_broker_tag(portfolio.id, "different-request")
    assert first.startswith("tp")
    assert len(first) == 40
    assert "same-request" not in first


def test_prepare_intent_persists_once_and_reuses_same_idempotency_key(
    db_session, recovery_context, monkeypatch
):
    service, user, portfolio, instrument, order = _prepared(
        db_session, recovery_context, monkeypatch
    )
    duplicate = service.prepare_intent(
        user.id,
        _intent(portfolio, instrument),
        idempotency_key="client-request-001",
        user_confirmed=False,
    )

    assert duplicate.id == order.id
    assert duplicate.broker_tag == order.broker_tag
    assert duplicate.status == "PENDING_SUBMISSION"
    assert db_session.query(Order).filter(Order.portfolio_id == portfolio.id).count() == 1
    assert db_session.query(BrokerOrder).count() == 0


def test_reusing_idempotency_key_for_changed_intent_is_rejected(
    db_session, recovery_context, monkeypatch
):
    service, user, portfolio, instrument, _order = _prepared(
        db_session, recovery_context, monkeypatch
    )
    with pytest.raises(LiveExecutionBlocked, match="different intent"):
        service.prepare_intent(
            user.id,
            _intent(portfolio, instrument, side="SELL"),
            idempotency_key="client-request-001",
            user_confirmed=True,
        )
    assert db_session.query(Order).count() == 1


def test_prepare_intent_requires_all_preflight_gates_for_new_key(
    db_session, recovery_context, monkeypatch
):
    user, portfolio, instrument, _connection = recovery_context
    monkeypatch.setattr(settings, "TRADING_MODE", "LIVE")
    monkeypatch.setattr(settings, "LIVE_ORDER_SUBMISSION_ENABLED", False)
    service = _service(db_session)

    with pytest.raises(LiveExecutionBlocked, match="LIVE_ORDER_SUBMISSION_ENABLED is off"):
        service.prepare_intent(
            user.id,
            _intent(portfolio, instrument),
            idempotency_key="must-not-persist",
            user_confirmed=True,
        )
    assert db_session.query(Order).count() == 0


@pytest.mark.asyncio
async def test_tag_recovery_persists_only_broker_identity_and_is_idempotent(
    db_session, recovery_context, monkeypatch
):
    service, user, _portfolio, instrument, order = _prepared(
        db_session, recovery_context, monkeypatch
    )
    service.mark_submission_unknown(user.id, order.id)
    adapter = SimpleNamespace(
        get_order_history=AsyncMock(return_value=BrokerCallResult(
            ok=True,
            data={"status": "success", "data": [
                _history_row("broker-child-1", order.broker_tag, instrument.instrument_key)
            ]},
        )),
        place_order=AsyncMock(),
    )

    first = await service.recover_by_tag(user.id, order.id, adapter=adapter)
    second = await service.recover_by_tag(user.id, order.id, adapter=adapter)

    assert first.state == "RECOVERED"
    assert first.broker_order_ids == ("broker-child-1",)
    assert second.state == "RECOVERED"
    assert second.broker_order_ids == ("broker-child-1",)
    adapter.get_order_history.assert_awaited_once_with("test-access-token", tag=order.broker_tag)
    adapter.place_order.assert_not_awaited()
    assert db_session.query(BrokerOrder).filter(BrokerOrder.order_id == order.id).count() == 1
    db_session.refresh(order)
    assert order.status == "SUBMISSION_UNKNOWN"
    assert order.broker_order_id == "broker-child-1"
    assert db_session.query(Order).count() == 1


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("response", "expected_state"),
    [
        (BrokerCallResult(ok=False, error="timeout"), "UNKNOWN_REQUIRES_REVIEW"),
        (BrokerCallResult(ok=True, data={"status": "success", "data": []}), "NO_MATCH_REQUIRES_REVIEW"),
    ],
)
async def test_ambiguous_timeout_or_no_match_never_triggers_resubmission(
    db_session, recovery_context, monkeypatch, response, expected_state
):
    service, user, _portfolio, _instrument, order = _prepared(
        db_session, recovery_context, monkeypatch
    )
    service.mark_submission_unknown(user.id, order.id)
    adapter = SimpleNamespace(
        get_order_history=AsyncMock(return_value=response),
        place_order=AsyncMock(),
    )

    result = await service.recover_by_tag(user.id, order.id, adapter=adapter)

    assert result.state == expected_state
    assert "do not resubmit" in (result.detail or "").lower()
    adapter.get_order_history.assert_awaited_once_with("test-access-token", tag=order.broker_tag)
    adapter.place_order.assert_not_awaited()
    assert db_session.query(BrokerOrder).count() == 0
    db_session.refresh(order)
    assert order.status == "SUBMISSION_UNKNOWN"


@pytest.mark.asyncio
async def test_tag_recovery_rejects_wrong_tag_or_mismatched_intent_without_binding(
    db_session, recovery_context, monkeypatch
):
    service, user, _portfolio, instrument, order = _prepared(
        db_session, recovery_context, monkeypatch
    )
    service.mark_submission_unknown(user.id, order.id)
    adapter = SimpleNamespace(
        get_order_history=AsyncMock(return_value=BrokerCallResult(
            ok=True,
            data={"status": "success", "data": [
                _history_row("foreign-broker-order", "another-tag", instrument.instrument_key)
            ]},
        )),
        place_order=AsyncMock(),
    )

    result = await service.recover_by_tag(user.id, order.id, adapter=adapter)

    assert result.state == "MISMATCH_REQUIRES_REVIEW"
    assert db_session.query(BrokerOrder).count() == 0
    adapter.place_order.assert_not_awaited()


@pytest.mark.asyncio
async def test_tag_recovery_supports_sliced_children_only_when_quantities_reconcile(
    db_session, recovery_context, monkeypatch
):
    service, user, _portfolio, instrument, order = _prepared(
        db_session, recovery_context, monkeypatch, quantity=5
    )
    service.mark_submission_unknown(user.id, order.id)
    adapter = SimpleNamespace(
        get_order_history=AsyncMock(return_value=BrokerCallResult(
            ok=True,
            data={"status": "success", "data": [
                _history_row("child-a", order.broker_tag, instrument.instrument_key, quantity=2),
                _history_row("child-b", order.broker_tag, instrument.instrument_key, quantity=3),
            ]},
        )),
        place_order=AsyncMock(),
    )

    result = await service.recover_by_tag(user.id, order.id, adapter=adapter)

    assert result.state == "RECOVERED"
    assert result.broker_order_ids == ("child-a", "child-b")
    assert db_session.query(BrokerOrder).filter(BrokerOrder.order_id == order.id).count() == 2
    db_session.refresh(order)
    assert order.broker_order_id is None  # parent has multiple broker child IDs
    adapter.place_order.assert_not_awaited()


@pytest.mark.asyncio
async def test_tag_recovery_does_not_bind_child_quantities_that_do_not_sum_to_intent(
    db_session, recovery_context, monkeypatch
):
    service, user, _portfolio, instrument, order = _prepared(
        db_session, recovery_context, monkeypatch, quantity=5
    )
    service.mark_submission_unknown(user.id, order.id)
    adapter = SimpleNamespace(
        get_order_history=AsyncMock(return_value=BrokerCallResult(
            ok=True,
            data={"status": "success", "data": [
                _history_row("child-a", order.broker_tag, instrument.instrument_key, quantity=2),
                _history_row("child-b", order.broker_tag, instrument.instrument_key, quantity=2),
            ]},
        )),
        place_order=AsyncMock(),
    )

    result = await service.recover_by_tag(user.id, order.id, adapter=adapter)

    assert result.state == "MISMATCH_REQUIRES_REVIEW"
    assert db_session.query(BrokerOrder).count() == 0
    adapter.place_order.assert_not_awaited()


def test_persist_preflighted_intent_revalidates_plan_and_connection(
    db_session, recovery_context, monkeypatch
):
    user, portfolio, instrument, connection = recovery_context
    service = _service(db_session)
    intent = _intent(portfolio, instrument)
    plan = LiveOrderPreflight(
        user_id=user.id,
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        broker_name="upstox",
        broker_connection_id=connection.id,
        instrument_key=instrument.instrument_key,
        side=intent.side,
        order_type=intent.order_type,
        segment=intent.segment,
        quantity=intent.quantity,
        limit_price=intent.limit_price,
    )

    order = service.persist_preflighted_intent(
        user.id, intent, plan, idempotency_key="safe-plan-key-001"
    )
    replay = service.persist_preflighted_intent(
        user.id, intent, plan, idempotency_key="safe-plan-key-001"
    )

    assert order.id == replay.id
    assert order.status == "PENDING_SUBMISSION"
    assert order.trading_mode == "LIVE"
    assert order.broker_tag == make_broker_tag(portfolio.id, "safe-plan-key-001")
    assert db_session.query(Order).filter(Order.portfolio_id == portfolio.id).count() == 1
    assert db_session.query(BrokerOrder).count() == 0


def test_persist_preflighted_intent_rejects_plan_for_other_user_or_changed_intent(
    db_session, recovery_context
):
    user, portfolio, instrument, connection = recovery_context
    service = _service(db_session)
    intent = _intent(portfolio, instrument)
    plan = LiveOrderPreflight(
        user_id=user.id,
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        broker_name="upstox",
        broker_connection_id=connection.id,
        instrument_key=instrument.instrument_key,
        side="SELL",
        order_type=intent.order_type,
        segment=intent.segment,
        quantity=intent.quantity,
        limit_price=intent.limit_price,
    )

    with pytest.raises(LiveExecutionBlocked, match="does not match"):
        service.persist_preflighted_intent(
            user.id, intent, plan, idempotency_key="safe-plan-key-002"
        )

    assert db_session.query(Order).count() == 0


def test_persist_preflighted_intent_rejects_changed_broker_connection(
    db_session, recovery_context
):
    user, portfolio, instrument, connection = recovery_context
    service = _service(db_session)
    intent = _intent(portfolio, instrument)
    plan = LiveOrderPreflight(
        user_id=user.id,
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        broker_name="upstox",
        broker_connection_id=connection.id,
        instrument_key=instrument.instrument_key,
        side=intent.side,
        order_type=intent.order_type,
        segment=intent.segment,
        quantity=intent.quantity,
        limit_price=intent.limit_price,
    )
    connection.is_connected = False
    db_session.commit()

    with pytest.raises(LiveExecutionBlocked, match="connection changed"):
        service.persist_preflighted_intent(
            user.id, intent, plan, idempotency_key="safe-plan-key-003"
        )

    assert db_session.query(Order).count() == 0


def test_persist_preflighted_intent_rejects_instrument_key_change_after_snapshot(
    db_session, recovery_context
):
    user, portfolio, instrument, connection = recovery_context
    service = _service(db_session)
    intent = _intent(portfolio, instrument)
    plan = LiveOrderPreflight(
        user_id=user.id,
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        broker_name="upstox",
        broker_connection_id=connection.id,
        instrument_key=instrument.instrument_key,
        side=intent.side,
        order_type=intent.order_type,
        segment=intent.segment,
        quantity=intent.quantity,
        limit_price=intent.limit_price,
    )
    instrument.instrument_key = "NSE_EQ|CHANGED_AFTER_PREFLIGHT"
    db_session.commit()

    with pytest.raises(LiveExecutionBlocked, match="Instrument changed after preflight"):
        service.persist_preflighted_intent(
            user.id, intent, plan, idempotency_key="safe-plan-key-004"
        )

    assert db_session.query(Order).count() == 0


def test_mark_submission_unknown_is_idempotent_and_refuses_terminal_states(
    db_session, recovery_context, monkeypatch
):
    service, user, _portfolio, _instrument, order = _prepared(
        db_session, recovery_context, monkeypatch
    )

    first = service.mark_submission_unknown(user.id, order.id)
    second = service.mark_submission_unknown(user.id, order.id)

    assert first.status == "SUBMISSION_UNKNOWN"
    assert second.status == "SUBMISSION_UNKNOWN"

    second.status = "FILLED"
    db_session.add(second)
    db_session.commit()

    with pytest.raises(LiveExecutionBlocked, match="eligible state"):
        service.mark_submission_unknown(user.id, order.id)

    db_session.refresh(second)
    assert second.status == "FILLED"
