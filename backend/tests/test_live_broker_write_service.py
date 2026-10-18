"""Regression tests for the deny-all central live broker-write boundary."""
import asyncio

import pytest

from app.services.live_broker_write_service import LiveBrokerWriteService
from app.services.live_execution_service import LiveExecutionBlocked


@pytest.mark.parametrize("method,args", [
    ("place_order", ("test-token", {"instrument_token": "NSE_EQ|INE000000000", "quantity": 1})),
    ("modify_order", ("test-token", {"order_id": "broker-order-1", "quantity": 1})),
    ("cancel_order", ("test-token", "broker-order-1")),
])
def test_all_broker_write_verbs_are_unconditionally_blocked(method, args):
    service = LiveBrokerWriteService()
    with pytest.raises(LiveExecutionBlocked, match="not approved") as exc:
        asyncio.run(getattr(service, method)(*args))
    assert "no broker request was sent" in str(exc.value)


from uuid import uuid4
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from app.services.live_execution_service import LiveOrderIntent, LiveOrderPreflight


@pytest.mark.asyncio
async def test_prepare_order_intent_runs_safety_preflight_before_persisting():
    user_id, portfolio_id, instrument_id, connection_id = (uuid4() for _ in range(4))
    intent = LiveOrderIntent(
        portfolio_id=portfolio_id,
        instrument_id=instrument_id,
        side="BUY",
        order_type="LIMIT",
        segment="EQUITY_DELIVERY",
        quantity=2,
        limit_price=Decimal("100.00"),
    )
    plan = LiveOrderPreflight(
        user_id=user_id,
        portfolio_id=portfolio_id,
        instrument_id=instrument_id,
        broker_name="upstox",
        broker_connection_id=connection_id,
        instrument_key="NSE_EQ|INE000000000",
        side="BUY",
        order_type="LIMIT",
        segment="EQUITY_DELIVERY",
        quantity=2,
        limit_price=Decimal("100.00"),
    )
    preflight = SimpleNamespace(preflight=AsyncMock(return_value=plan))
    persisted = object()
    recovery = SimpleNamespace(persist_preflighted_intent=Mock(return_value=persisted))
    service = LiveBrokerWriteService(
        preflight_coordinator=preflight,
        recovery_service=recovery,
    )

    result = await service.prepare_order_intent(
        user_id,
        intent,
        idempotency_key="client-request-001",
        user_confirmed=True,
    )

    assert result is persisted
    preflight.preflight.assert_awaited_once_with(user_id, intent, user_confirmed=True)
    recovery.persist_preflighted_intent.assert_called_once_with(
        user_id, intent, plan, idempotency_key="client-request-001"
    )


@pytest.mark.asyncio
async def test_prepare_order_intent_does_not_persist_when_safety_preflight_denies():
    user_id, portfolio_id, instrument_id = (uuid4() for _ in range(3))
    intent = LiveOrderIntent(
        portfolio_id=portfolio_id,
        instrument_id=instrument_id,
        side="BUY",
        order_type="MARKET",
        segment="EQUITY_DELIVERY",
        quantity=1,
    )
    preflight = SimpleNamespace(
        preflight=AsyncMock(side_effect=LiveExecutionBlocked("safety latch is tripped"))
    )
    recovery = SimpleNamespace(persist_preflighted_intent=Mock())
    service = LiveBrokerWriteService(
        preflight_coordinator=preflight,
        recovery_service=recovery,
    )

    with pytest.raises(LiveExecutionBlocked, match="safety latch is tripped"):
        await service.prepare_order_intent(
            user_id,
            intent,
            idempotency_key="client-request-002",
            user_confirmed=True,
        )

    recovery.persist_preflighted_intent.assert_not_called()
