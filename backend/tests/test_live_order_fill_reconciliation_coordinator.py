from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.broker_connection import BrokerConnection
from app.models.broker_order import BrokerOrder
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.execution import Execution
from app.models.instrument import Instrument
from app.models.live_position import LivePosition
from app.models.order import Order
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.instrument_service import InstrumentService
from app.services.live_execution_service import LiveExecutionBlocked
from app.services.live_order_fill_reconciliation_coordinator import (
    LiveOrderFillReconciliationCoordinator,
)


class FakeChildReconciler:
    def __init__(self, db, fail_ids=()):
        self.db = db
        self.fail_ids = set(fail_ids)
        self.calls = []

    async def reconcile(self, user_id, order_id, child_id):
        self.calls.append(child_id)
        if child_id in self.fail_ids:
            raise ValueError("mock broker status/trade reconciliation failed")
        child = self.db.get(BrokerOrder, child_id)
        return SimpleNamespace(
            broker_order_ref_id=child.id,
            broker_order_id=child.broker_order_id,
            status=child.status,
            filled_quantity=child.filled_quantity,
        )


class FakePromotionService:
    def __init__(self, fail_trade_id=None):
        self.calls = []
        self.fail_trade_id = fail_trade_id

    async def promote_trade(self, user_id, trade_record_id):
        self.calls.append(trade_record_id)
        if trade_record_id == self.fail_trade_id:
            raise LiveExecutionBlocked("mock charge estimate failed")
        return SimpleNamespace(duplicate=False)


@pytest.fixture()
def order_context(db_session, make_user):
    user = make_user()
    portfolio = PortfolioRepository(db_session).create(
        user_id=user.id, name="Reconcile and promote", virtual_capital=Decimal("100000")
    )
    InstrumentService(db_session).seed_defaults()
    instrument = InstrumentRepository(db_session).search("RELIANCE")[0]
    connection = BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="test-key",
        api_secret_encrypted="test-secret",
        redirect_uri="https://example.invalid/callback",
        is_connected=True,
    )
    now = datetime(2026, 10, 19, 5, 0, tzinfo=timezone.utc)
    order = Order(
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        side="BUY",
        order_type="MARKET",
        segment="EQUITY_DELIVERY",
        quantity=2,
        status="PENDING",
        trading_mode="LIVE",
        execution_reason="MANUAL",
        broker_order_id="conceptual-parent",
        placed_at=now,
    )
    db_session.add_all([connection, order])
    db_session.flush()

    children = []
    records = []
    for index in range(2):
        child = BrokerOrder(
            order_id=order.id,
            broker_connection_id=connection.id,
            broker_name="upstox",
            broker_order_id=f"child-{index + 1}",
            requested_quantity=1,
            filled_quantity=1,
            status="FILLED",
            status_checked_at=now,
        )
        db_session.add(child)
        db_session.flush()
        record = BrokerTradeRecord(
            broker_connection_id=connection.id,
            broker_order_ref_id=child.id,
            broker_trade_id=f"trade-{index + 1}",
            quantity=1,
            price=Decimal("100") + index,
            side="BUY",
            instrument_token=instrument.instrument_key,
            exchange_timestamp=(now + timedelta(seconds=index)).isoformat(),
        )
        db_session.add(record)
        children.append(child)
        records.append(record)
    db_session.commit()
    return db_session, user, portfolio, instrument, order, children, records, now


@pytest.mark.asyncio
async def test_coordinator_reconciles_all_children_then_promotes_in_exchange_time_order(
    order_context,
):
    db, user, portfolio, instrument, order, children, records, now = order_context
    reconciler = FakeChildReconciler(db)
    promoter = FakePromotionService()
    coordinator = LiveOrderFillReconciliationCoordinator(
        db, child_reconciler=reconciler, promotion_service=promoter
    )

    result = await coordinator.reconcile_and_promote(user.id, order.id)

    assert result.reconciliation_complete
    assert result.promotion_complete
    assert result.total_staged_trades == 2
    assert result.total_promoted_trades == 2
    assert result.total_duplicate_trades == 0
    assert promoter.calls == [records[0].id, records[1].id]
    assert reconciler.calls == [child.id for child in children]
    db.refresh(order)
    assert order.status == "PENDING"  # coordinator never changes parent order state
    assert db.query(Execution).count() == 0  # injected promoter is a mock
    assert db.query(LivePosition).count() == 0


@pytest.mark.asyncio
async def test_any_child_reconciliation_failure_blocks_all_parent_fill_promotion(
    order_context,
):
    db, user, _portfolio, _instrument, order, children, records, now = order_context
    children[1].status = "UNKNOWN"
    children[1].status_checked_at = None
    db.commit()
    reconciler = FakeChildReconciler(db, fail_ids={children[1].id})
    promoter = FakePromotionService()
    coordinator = LiveOrderFillReconciliationCoordinator(
        db, child_reconciler=reconciler, promotion_service=promoter
    )

    result = await coordinator.reconcile_and_promote(user.id, order.id)

    assert not result.reconciliation_complete
    assert not result.promotion_complete
    assert result.total_staged_trades == 2
    assert result.total_promoted_trades == 0
    assert promoter.calls == []
    assert result.blocked_reason and "No fills were promoted" in result.blocked_reason
    assert any(child.error for child in result.child_results)


@pytest.mark.asyncio
async def test_multiple_fills_with_ambiguous_exchange_timestamps_are_not_promoted(
    order_context,
):
    db, user, _portfolio, _instrument, order, children, records, now = order_context
    records[1].exchange_timestamp = records[0].exchange_timestamp
    db.commit()
    promoter = FakePromotionService()
    coordinator = LiveOrderFillReconciliationCoordinator(
        db,
        child_reconciler=FakeChildReconciler(db),
        promotion_service=promoter,
    )

    result = await coordinator.reconcile_and_promote(user.id, order.id)

    assert result.reconciliation_complete
    assert not result.promotion_complete
    assert result.total_promoted_trades == 0
    assert promoter.calls == []
    assert "share an exchange timestamp" in result.blocked_reason


@pytest.mark.asyncio
async def test_missing_exchange_timestamp_on_multi_fill_parent_fails_closed(order_context):
    db, user, _portfolio, _instrument, order, children, records, now = order_context
    records[1].exchange_timestamp = None
    db.commit()
    promoter = FakePromotionService()
    coordinator = LiveOrderFillReconciliationCoordinator(
        db,
        child_reconciler=FakeChildReconciler(db),
        promotion_service=promoter,
    )

    result = await coordinator.reconcile_and_promote(user.id, order.id)

    assert result.reconciliation_complete
    assert not result.promotion_complete
    assert result.total_promoted_trades == 0
    assert promoter.calls == []
    assert "require distinct timezone-aware exchange timestamps" in result.blocked_reason


@pytest.mark.asyncio
async def test_promotion_failure_stops_later_fills_and_is_reported_for_retry(order_context):
    db, user, _portfolio, _instrument, order, children, records, now = order_context
    promoter = FakePromotionService(fail_trade_id=records[0].id)
    coordinator = LiveOrderFillReconciliationCoordinator(
        db,
        child_reconciler=FakeChildReconciler(db),
        promotion_service=promoter,
    )

    result = await coordinator.reconcile_and_promote(user.id, order.id)

    assert result.reconciliation_complete
    assert not result.promotion_complete
    assert result.total_promoted_trades == 0
    assert promoter.calls == [records[0].id]
    assert "Promotion stopped" in result.blocked_reason


# Service-level integration coverage: real reconciliation, intake, promotion and
# accounting services with only broker I/O and charge estimation mocked.
from app.brokers.base import BrokerCallResult
from app.models.position import Position
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.broker_child_order_reconciliation_service import BrokerChildOrderReconciliationService
from app.services.live_fill_accounting_service import LiveChargeBreakdown, LiveFillAccountingService
from app.services.live_fill_promotion_service import LiveFillPromotionService


class ReadOnlyUpstoxIntegrationAdapter:
    def __init__(self, instrument_token, *, failing_status_order_id=None):
        self.instrument_token = instrument_token
        self.failing_status_order_id = failing_status_order_id
        self.trade_calls = []
        self.status_calls = []
        self.write_calls = 0

    async def get_order_trades(self, access_token, broker_order_id):
        self.trade_calls.append(broker_order_id)
        index = 1 if broker_order_id == "child-1" else 2
        return BrokerCallResult(ok=True, data={"status": "success", "data": [{
            "order_id": broker_order_id,
            "trade_id": f"trade-{index}",
            "quantity": 1,
            "average_price": str(99 + index),
            "transaction_type": "BUY",
            "instrument_token": self.instrument_token,
            "exchange_timestamp": f"2026-10-19T05:00:0{index - 1}+00:00",
        }]})

    async def get_order_status(self, access_token, broker_order_id):
        self.status_calls.append(broker_order_id)
        if broker_order_id == self.failing_status_order_id:
            return BrokerCallResult(ok=False, error="mock status endpoint unavailable")
        index = 1 if broker_order_id == "child-1" else 2
        return BrokerCallResult(ok=True, data={"status": "success", "data": {
            "order_id": broker_order_id,
            "status": "complete",
            "quantity": 1,
            "filled_quantity": 1,
            "average_price": str(99 + index),
            "instrument_token": self.instrument_token,
            "transaction_type": "BUY",
        }})


class FixedIntegrationChargeEstimator:
    def __init__(self, db):
        self.db = db

    async def estimate_for_trade(self, user_id, broker_trade_record_id):
        record = self.db.get(BrokerTradeRecord, broker_trade_record_id)
        return SimpleNamespace(
            broker_trade_id=record.broker_trade_id,
            broker_connection_id=record.broker_connection_id,
            instrument_token=record.instrument_token,
            quantity=record.quantity,
            price=Decimal(str(record.price)),
            breakdown=LiveChargeBreakdown(
                brokerage=Decimal("1.00"), stt=Decimal("0.10"),
                exchange_charges=Decimal("0.05"), sebi_charges=Decimal("0.01"),
                stamp_duty=Decimal("0.02"), gst=Decimal("0.19"),
                source="APPROVED_ESTIMATE", reference="test-estimator-v1",
            ),
            estimated_total=Decimal("1.37"),
            dp_charges=Decimal("0.00"),
        )


@pytest.mark.asyncio
async def test_real_services_reconcile_ingest_promote_and_replay_idempotently(order_context, monkeypatch):
    db, user, portfolio, instrument, order, children, records, now = order_context
    adapter = ReadOnlyUpstoxIntegrationAdapter(instrument.instrument_key)
    monkeypatch.setattr(BrokerCredentialsService, "get_access_token", lambda *_args: "test-access-token")
    promotion = LiveFillPromotionService(
        db,
        charge_estimator=FixedIntegrationChargeEstimator(db),
        accounting=LiveFillAccountingService(db),
    )
    coordinator = LiveOrderFillReconciliationCoordinator(
        db,
        child_reconciler=BrokerChildOrderReconciliationService(db, adapter=adapter),
        promotion_service=promotion,
    )
    cash_before = Decimal(str(portfolio.cash_balance))

    first = await coordinator.reconcile_and_promote(user.id, order.id)
    second = await coordinator.reconcile_and_promote(user.id, order.id)

    assert first.reconciliation_complete and first.promotion_complete
    assert first.total_staged_trades == 2
    assert first.total_promoted_trades == 2
    assert second.reconciliation_complete and second.promotion_complete
    assert second.total_promoted_trades == 0
    assert second.total_duplicate_trades == 2
    assert db.query(BrokerTradeRecord).count() == 2
    assert db.query(Execution).count() == 2
    assert db.query(LivePosition).one().quantity == 2
    assert db.query(Position).count() == 0
    db.refresh(portfolio)
    db.refresh(order)
    assert Decimal(str(portfolio.cash_balance)) == cash_before
    assert order.status == "PENDING"
    assert adapter.trade_calls == ["child-1", "child-2", "child-1", "child-2"]
    assert adapter.status_calls == ["child-1", "child-2", "child-1", "child-2"]
    assert adapter.write_calls == 0


@pytest.mark.asyncio
async def test_real_services_block_all_promotion_if_any_sibling_status_fails(order_context, monkeypatch):
    db, user, portfolio, _instrument, order, children, records, now = order_context
    adapter = ReadOnlyUpstoxIntegrationAdapter(
        records[0].instrument_token, failing_status_order_id="child-2"
    )
    monkeypatch.setattr(BrokerCredentialsService, "get_access_token", lambda *_args: "test-access-token")
    promotion = LiveFillPromotionService(
        db,
        charge_estimator=FixedIntegrationChargeEstimator(db),
        accounting=LiveFillAccountingService(db),
    )
    coordinator = LiveOrderFillReconciliationCoordinator(
        db,
        child_reconciler=BrokerChildOrderReconciliationService(db, adapter=adapter),
        promotion_service=promotion,
    )
    cash_before = Decimal(str(portfolio.cash_balance))

    result = await coordinator.reconcile_and_promote(user.id, order.id)

    assert not result.reconciliation_complete
    assert not result.promotion_complete
    assert result.total_promoted_trades == 0
    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0
    assert db.query(BrokerTradeRecord).count() == 2  # staged data is not accounting
    db.refresh(portfolio)
    db.refresh(order)
    assert Decimal(str(portfolio.cash_balance)) == cash_before
    assert order.status == "PENDING"
    assert adapter.write_calls == 0
