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

