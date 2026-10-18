from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.models.broker_trade_record import BrokerTradeRecord
from app.models.execution import Execution
from app.models.live_position import LivePosition
from app.models.order import Order
from app.models.position import Position
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.broker_trade_ingestion_service import BrokerTradeIngestionService
from app.services.instrument_service import InstrumentService
from app.services.live_fill_accounting_service import (
    LiveChargeBreakdown,
    LiveFillAccountingService,
)
from app.services.live_execution_service import LiveExecutionBlocked
from app.brokers.upstox.response_parsing import BrokerTrade
from app.models.broker_connection import BrokerConnection
from app.models.broker_order import BrokerOrder


def _charges(**overrides):
    values = dict(
        brokerage=Decimal("2.00"),
        stt=Decimal("0.20"),
        exchange_charges=Decimal("0.03"),
        sebi_charges=Decimal("0.01"),
        stamp_duty=Decimal("0.02"),
        gst=Decimal("0.37"),
        source="BROKER_REPORTED",
        reference="mock-contract-note:trade-001",
    )
    values.update(overrides)
    return LiveChargeBreakdown(**values)


@pytest.fixture()
def accounting_context(db_session, make_user):
    user = make_user()
    portfolio = PortfolioRepository(db_session).create(
        user_id=user.id, name="Live accounting", virtual_capital=Decimal("100000")
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
        order_id=order.id,
        broker_connection_id=connection.id,
        broker_name="upstox",
        broker_order_id="broker-child-1",
        requested_quantity=5,
        filled_quantity=2,
    )
    db_session.add(child)
    db_session.flush()
    record = BrokerTradeRecord(
        broker_connection_id=connection.id,
        broker_order_ref_id=child.id,
        broker_trade_id="trade-001",
        quantity=2,
        price=Decimal("100.25"),
        side="BUY",
        instrument_token=instrument.instrument_key,
        exchange_timestamp="2026-10-18T09:20:00+05:30",
    )
    db_session.add(record)
    db_session.commit()
    return db_session, user, portfolio, instrument, connection, order, child, record


def test_atomic_accounting_updates_live_position_and_execution_only(accounting_context):
    db, user, portfolio, instrument, connection, order, child, record = accounting_context
    before_cash = Decimal(str(portfolio.cash_balance))
    result = LiveFillAccountingService(db).account_trade(user.id, record.id, _charges())

    assert result.duplicate is False
    assert result.broker_trade_id == "trade-001"
    assert result.live_position_quantity == 2
    assert result.live_position_avg_price == Decimal("100.2500")
    execution = db.query(Execution).one()
    position = db.query(LivePosition).one()
    assert execution.order_id == order.id
    assert execution.broker_order_ref_id == child.id
    assert execution.broker_connection_id == connection.id
    assert execution.broker_trade_id == record.broker_trade_id
    assert execution.charge_source == "BROKER_REPORTED"
    assert execution.charge_reference == "mock-contract-note:trade-001"
    assert execution.total_charges == Decimal("2.63")
    assert position.quantity == 2
    assert position.avg_price == Decimal("100.2500")
    assert position.realized_pnl == Decimal("0.00")
    assert db.query(Position).count() == 0
    db.refresh(portfolio)
    assert Decimal(str(portfolio.cash_balance)) == before_cash
    db.refresh(order)
    assert order.status == "PENDING"


def test_replay_is_idempotent_and_does_not_double_position(accounting_context):
    db, user, _portfolio, _instrument, _connection, _order, _child, record = accounting_context
    service = LiveFillAccountingService(db)
    first = service.account_trade(user.id, record.id, _charges())
    second = service.account_trade(user.id, record.id, _charges())

    assert not first.duplicate
    assert second.duplicate
    assert first.execution_id == second.execution_id
    assert db.query(Execution).count() == 1
    assert db.query(LivePosition).one().quantity == 2


def test_missing_or_invalid_charge_provenance_fails_closed(accounting_context):
    db, user, _portfolio, _instrument, _connection, _order, _child, record = accounting_context
    service = LiveFillAccountingService(db)

    with pytest.raises(LiveExecutionBlocked, match="explicit validated live charge"):
        service.account_trade(user.id, record.id, None)
    with pytest.raises(LiveExecutionBlocked, match="provenance reference"):
        service.account_trade(user.id, record.id, _charges(reference=" "))
    with pytest.raises(LiveExecutionBlocked, match="Charge source"):
        service.account_trade(user.id, record.id, _charges(source="PAPER_ESTIMATE"))

    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0


def test_invalid_negative_or_nonfinite_charge_rolls_back(accounting_context):
    db, user, _portfolio, _instrument, _connection, _order, _child, record = accounting_context
    with pytest.raises(LiveExecutionBlocked, match="finite and non-negative"):
        LiveFillAccountingService(db).account_trade(
            user.id, record.id, _charges(gst=Decimal("NaN"))
        )
    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0


def test_foreign_user_cannot_account_another_connections_trade(accounting_context, make_user):
    db, _user, _portfolio, _instrument, _connection, _order, _child, record = accounting_context
    stranger = make_user(email="other-account@example.com")

    with pytest.raises(LiveExecutionBlocked, match="not owned"):
        LiveFillAccountingService(db).account_trade(stranger.id, record.id, _charges())

    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0


def test_transaction_rolls_back_position_when_execution_insert_fails(accounting_context, monkeypatch):
    db, user, _portfolio, _instrument, _connection, _order, _child, record = accounting_context
    service = LiveFillAccountingService(db)

    def fail_timestamp(_value):
        raise RuntimeError("forced failure before execution insert")

    monkeypatch.setattr(service, "_trade_timestamp", fail_timestamp)
    with pytest.raises(RuntimeError, match="forced failure"):
        service.account_trade(user.id, record.id, _charges())

    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0


def test_explicit_estimate_is_stored_as_estimate_not_actual(accounting_context):
    db, user, _portfolio, _instrument, _connection, _order, _child, record = accounting_context
    charges = _charges(source="APPROVED_ESTIMATE", reference="upstox-estimator-v1")
    result = LiveFillAccountingService(db).account_trade(user.id, record.id, charges)

    execution = db.query(Execution).one()
    assert not result.duplicate
    assert execution.charge_source == "APPROVED_ESTIMATE"
    assert execution.charge_reference == "upstox-estimator-v1"
