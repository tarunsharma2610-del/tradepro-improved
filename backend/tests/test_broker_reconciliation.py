from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from app.brokers.base import BrokerCallResult
from app.models.order import Order
from app.services.broker_reconciliation_service import BrokerReconciliationService


def _live_order(db_session, portfolio, instrument, *, trading_mode="LIVE", broker_order_id="upstox-123"):
    _user, p = portfolio
    order = Order(
        portfolio_id=p.id,
        instrument_id=instrument.id,
        side="BUY",
        order_type="MARKET",
        segment="EQUITY_DELIVERY",
        quantity=1,
        status="PENDING",
        trading_mode=trading_mode,
        execution_reason="MANUAL",
        broker_order_id=broker_order_id,
        placed_at=datetime.now(timezone.utc),
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


@pytest.mark.asyncio
async def test_broker_status_check_records_status_without_changing_local_order_accounting(
    db_session, portfolio, instrument, monkeypatch
):
    user, _p = portfolio
    order = _live_order(db_session, portfolio, instrument)
    adapter = SimpleNamespace(
        get_order_status=AsyncMock(return_value=BrokerCallResult(
            ok=True, data={"data": {"order_id": "upstox-123", "status": "open"}}
        ))
    )
    monkeypatch.setattr("app.services.broker_reconciliation_service.get_broker_adapter", lambda _name: adapter)
    monkeypatch.setattr(
        "app.services.broker_reconciliation_service.BrokerCredentialsService.get_access_token",
        lambda _self, _user_id, _broker: "fake-token",
    )

    result = await BrokerReconciliationService(db_session).check_order_status(user.id, order.id)

    db_session.refresh(order)
    assert result.ok is True
    assert order.broker_status == "open"
    assert order.broker_status_checked_at is not None
    assert order.broker_status_error is None
    assert order.status == "PENDING"  # no local fill/cancel inference
    adapter.get_order_status.assert_awaited_once_with("fake-token", "upstox-123")


@pytest.mark.asyncio
async def test_broker_status_check_rejects_paper_order_without_broker_call(
    db_session, portfolio, instrument, monkeypatch
):
    user, _p = portfolio
    order = _live_order(db_session, portfolio, instrument, trading_mode="PAPER")
    adapter = SimpleNamespace(get_order_status=AsyncMock())
    monkeypatch.setattr("app.services.broker_reconciliation_service.get_broker_adapter", lambda _name: adapter)

    with pytest.raises(ValueError, match="only allowed for LIVE"):
        await BrokerReconciliationService(db_session).check_order_status(user.id, order.id)
    adapter.get_order_status.assert_not_awaited()


@pytest.mark.asyncio
async def test_broker_status_check_rejects_mismatched_broker_order_id(
    db_session, portfolio, instrument, monkeypatch
):
    user, _p = portfolio
    order = _live_order(db_session, portfolio, instrument)
    adapter = SimpleNamespace(
        get_order_status=AsyncMock(return_value=BrokerCallResult(
            ok=True, data={"data": {"order_id": "some-other-order", "status": "complete"}}
        ))
    )
    monkeypatch.setattr("app.services.broker_reconciliation_service.get_broker_adapter", lambda _name: adapter)
    monkeypatch.setattr(
        "app.services.broker_reconciliation_service.BrokerCredentialsService.get_access_token",
        lambda _self, _user_id, _broker: "fake-token",
    )

    result = await BrokerReconciliationService(db_session).check_order_status(user.id, order.id)

    db_session.refresh(order)
    assert result.ok is False
    assert order.broker_status is None
    assert "did not match" in order.broker_status_error
    assert order.status == "PENDING"
