from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.brokers.base import BrokerCallResult
from app.models.broker_connection import BrokerConnection
from app.models.broker_order import BrokerOrder
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.execution import Execution
from app.models.order import Order
from app.models.position import Position
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.broker_child_order_reconciliation_service import (
    BrokerChildOrderReconciliationService,
)
from app.services.instrument_service import InstrumentService


class FakeChildOrderAdapter:
    def __init__(self, *, trade_quantity=2, status="open", filled_quantity=2, order_quantity=5,
                 average_price="100.25", fail_status=False):
        self.trade_quantity = trade_quantity
        self.status = status
        self.filled_quantity = filled_quantity
        self.order_quantity = order_quantity
        self.average_price = average_price
        self.fail_status = fail_status
        self.calls = []

    async def get_order_trades(self, access_token, order_id):
        self.calls.append(("trades", access_token, order_id))
        return BrokerCallResult(ok=True, data={"status": "success", "data": [{
            "order_id": order_id,
            "trade_id": "trade-child-001",
            "quantity": self.trade_quantity,
            "average_price": self.average_price,
            "transaction_type": "BUY",
            "instrument_token": "NSE_EQ|INE002A01018",
            "exchange_timestamp": "2026-10-18T09:20:00+05:30",
        }]})

    async def get_order_status(self, access_token, order_id):
        self.calls.append(("status", access_token, order_id))
        if self.fail_status:
            return BrokerCallResult(ok=False, error="status endpoint unavailable")
        return BrokerCallResult(ok=True, data={"status": "success", "data": {
            "order_id": order_id,
            "status": self.status,
            "quantity": self.order_quantity,
            "filled_quantity": self.filled_quantity,
            "average_price": self.average_price if self.filled_quantity else 0,
            "instrument_token": "NSE_EQ|INE002A01018",
            "transaction_type": "BUY",
        }})


@pytest.fixture()
def child_context(db_session, make_user, monkeypatch):
    user = make_user()
    portfolio = PortfolioRepository(db_session).create(
        user_id=user.id, name="Child reconcile", virtual_capital=Decimal("100000")
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
        access_token_expires_at=datetime(2026, 10, 19, 18, 0, tzinfo=timezone.utc),
        is_connected=True,
    )
    order = Order(
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        side="BUY",
        order_type="MARKET",
        segment="EQUITY_DELIVERY",
        quantity=5,
        status="PENDING",
        trading_mode="LIVE",
        execution_reason="MANUAL",
        broker_order_id="broker-child-1",
        placed_at=datetime.now(timezone.utc),
    )
    db_session.add_all([connection, order])
    db_session.flush()
    child = BrokerOrder(
        broker_connection_id=connection.id,
        order_id=order.id,
        broker_name="upstox",
        broker_order_id="broker-child-1",
        requested_quantity=5,
        filled_quantity=0,
        status="UNKNOWN",
    )
    db_session.add(child)
    db_session.commit()
    monkeypatch.setattr(
        BrokerCredentialsService, "get_access_token", lambda *_: "same-test-token"
    )
    return db_session, user, portfolio, instrument, connection, order, child


@pytest.mark.asyncio
async def test_reconciles_partial_fill_from_broker_trades_without_accounting_side_effects(
    child_context,
):
    db, user, portfolio, instrument, connection, order, child = child_context
    initial_cash = Decimal(str(portfolio.cash_balance))
    adapter = FakeChildOrderAdapter()
    service = BrokerChildOrderReconciliationService(db, adapter=adapter)

    result = await service.reconcile(user.id, order.id, child.id)

    db.refresh(child)
    db.refresh(order)
    db.refresh(portfolio)
    assert result.status == "PARTIALLY_FILLED"
    assert result.filled_quantity == 2
    assert result.average_fill_price == Decimal("100.25")
    assert result.trades_inserted == 1
    assert child.status == "PARTIALLY_FILLED"
    assert child.filled_quantity == 2
    assert order.status == "PENDING"
    assert Decimal(str(portfolio.cash_balance)) == initial_cash
    assert db.query(Execution).count() == 0
    assert db.query(Position).count() == 0
    assert db.query(BrokerTradeRecord).count() == 1
    assert [call[0] for call in adapter.calls] == ["trades", "status"]


@pytest.mark.asyncio
async def test_replay_is_idempotent_and_terminal_cancel_preserves_partial_fill(child_context):
    db, user, portfolio, instrument, connection, order, child = child_context
    adapter = FakeChildOrderAdapter(status="cancelled", filled_quantity=2)
    service = BrokerChildOrderReconciliationService(db, adapter=adapter)

    first = await service.reconcile(user.id, order.id, child.id)
    second = await service.reconcile(user.id, order.id, child.id)

    assert first.status == "CANCELLED_PARTIALLY_FILLED"
    assert second.status == "CANCELLED_PARTIALLY_FILLED"
    assert first.trades_inserted == 1
    assert second.trades_inserted == 0
    assert second.duplicate_trades == 1
    assert db.query(BrokerTradeRecord).count() == 1
    db.refresh(order)
    assert order.status == "PENDING"


@pytest.mark.asyncio
async def test_fully_filled_status_requires_matching_complete_trade_quantity(child_context):
    db, user, portfolio, instrument, connection, order, child = child_context
    adapter = FakeChildOrderAdapter(
        trade_quantity=5, status="complete", filled_quantity=5, order_quantity=5
    )
    service = BrokerChildOrderReconciliationService(db, adapter=adapter)

    result = await service.reconcile(user.id, order.id, child.id)

    assert result.status == "FILLED"
    assert result.filled_quantity == 5
    assert result.average_fill_price == Decimal("100.25")


@pytest.mark.asyncio
async def test_status_fill_quantity_mismatch_does_not_update_child_status(child_context):
    db, user, portfolio, instrument, connection, order, child = child_context
    adapter = FakeChildOrderAdapter(filled_quantity=1)
    service = BrokerChildOrderReconciliationService(db, adapter=adapter)

    with pytest.raises(ValueError, match="does not match the durable broker trade records"):
        await service.reconcile(user.id, order.id, child.id)

    db.refresh(child)
    assert child.status == "UNKNOWN"
    assert child.filled_quantity == 0
    # Broker-confirmed trade intake remains durable and can be reconciled again.
    assert db.query(BrokerTradeRecord).count() == 1
    db.refresh(order)
    assert order.status == "PENDING"


@pytest.mark.asyncio
async def test_unknown_status_fails_closed_without_child_state_update(child_context):
    db, user, portfolio, instrument, connection, order, child = child_context
    adapter = FakeChildOrderAdapter(status="some new status")
    service = BrokerChildOrderReconciliationService(db, adapter=adapter)

    with pytest.raises(ValueError, match="Unrecognized broker order status"):
        await service.reconcile(user.id, order.id, child.id)

    db.refresh(child)
    assert child.status == "UNKNOWN"
    assert child.filled_quantity == 0


@pytest.mark.asyncio
async def test_cancelled_partial_child_cannot_regress_to_open(child_context):
    db, user, portfolio, instrument, connection, order, child = child_context
    service = BrokerChildOrderReconciliationService(
        db, adapter=FakeChildOrderAdapter(status="cancelled", filled_quantity=2)
    )
    await service.reconcile(user.id, order.id, child.id)

    service.adapter = FakeChildOrderAdapter(status="open", filled_quantity=2)
    service.ingestion.adapter = service.adapter
    with pytest.raises(ValueError, match="terminal state conflict"):
        await service.reconcile(user.id, order.id, child.id)

    db.refresh(child)
    assert child.status == "CANCELLED_PARTIALLY_FILLED"
