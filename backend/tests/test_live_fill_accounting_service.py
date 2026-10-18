from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.models.broker_connection import BrokerConnection
from app.models.broker_order import BrokerOrder
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.execution import Execution
from app.models.live_position import LivePosition
from app.models.order import Order
from app.models.position import Position
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.instrument_service import InstrumentService
from app.services.live_fill_accounting_service import (
    LiveFillAccountingService,
    LiveFillChargeBreakdown,
)


def _charges(**overrides):
    values = dict(
        brokerage=Decimal("20.00"),
        stt=Decimal("0.20"),
        exchange_charges=Decimal("0.01"),
        sebi_charges=Decimal("0.01"),
        stamp_duty=Decimal("0.03"),
        gst=Decimal("3.61"),
        total_charges=Decimal("23.86"),
        source="BROKER_REPORTED",
        reference="contract-note-2026-10-18-001",
    )
    values.update(overrides)
    return LiveFillChargeBreakdown(**values)


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
        api_key_encrypted="encrypted-key",
        api_secret_encrypted="encrypted-secret",
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
        broker_connection_id=connection.id,
        order_id=order.id,
        broker_name="upstox",
        broker_order_id="broker-child-1",
        requested_quantity=5,
        filled_quantity=2,
        status="PARTIALLY_FILLED",
    )
    record = BrokerTradeRecord(
        broker_connection_id=connection.id,
        broker_order_ref_id=child.id,
        broker_trade_id="trade-live-001",
        quantity=2,
        price=Decimal("100.25"),
        side="BUY",
        instrument_token=instrument.instrument_key,
        exchange_timestamp="2026-10-18T09:20:00+05:30",
    )
    paper_position = Position(
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        quantity=7,
        avg_price=Decimal("80"),
        realized_pnl=Decimal("12.00"),
    )
    db_session.add_all([child, record, paper_position])
    db_session.commit()
    return db_session, user, portfolio, instrument, connection, order, child, record, paper_position


def test_promote_live_trade_atomically_updates_live_position_and_execution_only(accounting_context):
    db, user, portfolio, instrument, connection, order, child, record, paper_position = accounting_context
    cash_before = Decimal(str(portfolio.cash_balance))
    service = LiveFillAccountingService(db)

    result = service.promote_trade(user.id, record.id, _charges())

    db.refresh(portfolio)
    db.refresh(paper_position)
    live_position = db.query(LivePosition).filter(
        LivePosition.broker_connection_id == connection.id,
        LivePosition.instrument_id == instrument.id,
    ).one()
    execution = db.query(Execution).filter(
        Execution.broker_connection_id == connection.id,
        Execution.broker_trade_id == record.broker_trade_id,
    ).one()
    assert result.inserted is True
    assert result.live_position_quantity == 2
    assert result.live_position_average_price == Decimal("100.2500")
    assert execution.charge_source == "BROKER_REPORTED"
    assert execution.charge_reference == "contract-note-2026-10-18-001"
    assert execution.price == Decimal("100.2500")
    assert execution.gross_value == Decimal("200.50")
    assert live_position.quantity == 2
    assert paper_position.quantity == 7
    assert paper_position.avg_price == Decimal("80.0000")
    assert Decimal(str(portfolio.cash_balance)) == cash_before
    assert order.status == "PENDING"
    assert db.query(Execution).count() == 1


def test_replaying_same_broker_trade_does_not_double_count_position(accounting_context):
    db, user, portfolio, instrument, connection, order, child, record, paper_position = accounting_context
    service = LiveFillAccountingService(db)

    first = service.promote_trade(user.id, record.id, _charges())
    second = service.promote_trade(user.id, record.id, _charges())

    assert first.inserted is True
    assert second.inserted is False
    assert first.execution_id == second.execution_id
    live_position = db.query(LivePosition).filter(
        LivePosition.broker_connection_id == connection.id,
        LivePosition.instrument_id == instrument.id,
    ).one()
    assert live_position.quantity == 2
    assert db.query(Execution).count() == 1


@pytest.mark.parametrize(
    ("charges", "message"),
    [
        (_charges(source="ESTIMATED"), "broker-reported charges"),
        (_charges(reference=" "), "audit reference"),
        (_charges(total_charges=Decimal("99.00")), "sum of its six components"),
        (_charges(brokerage=Decimal("-1.00"), total_charges=Decimal("2.86")), "non-negative"),
        (_charges(stt=Decimal("0.201"), total_charges=Decimal("23.861")), "paise precision"),
    ],
)
def test_invalid_or_estimated_charges_block_live_promotion(accounting_context, charges, message):
    db, user, portfolio, instrument, connection, order, child, record, paper_position = accounting_context

    with pytest.raises(ValueError, match=message):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, charges)

    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0
    db.refresh(paper_position)
    assert paper_position.quantity == 7


def test_naive_exchange_timestamp_blocks_live_promotion(accounting_context):
    db, user, portfolio, instrument, connection, order, child, record, paper_position = accounting_context
    record.exchange_timestamp = "2026-10-18T09:20:00"
    db.commit()

    with pytest.raises(ValueError, match="timezone offset"):
        LiveFillAccountingService(db).promote_trade(user.id, record.id, _charges())

    assert db.query(Execution).count() == 0
    assert db.query(LivePosition).count() == 0


def test_sell_fill_realizes_pnl_on_live_position_without_changing_paper_position(accounting_context):
    db, user, portfolio, instrument, connection, order, child, record, paper_position = accounting_context
    order.side = "SELL"
    child.requested_quantity = 1
    record.quantity = 1
    record.side = "SELL"
    record.price = Decimal("100.25")
    db.add(LivePosition(
        broker_connection_id=connection.id,
        instrument_id=instrument.id,
        quantity=3,
        avg_price=Decimal("90"),
        realized_pnl=Decimal("0"),
    ))
    db.commit()

    result = LiveFillAccountingService(db).promote_trade(user.id, record.id, _charges())

    live_position = db.query(LivePosition).filter(
        LivePosition.broker_connection_id == connection.id,
        LivePosition.instrument_id == instrument.id,
    ).one()
    db.refresh(paper_position)
    assert result.realized_pnl == Decimal("10.25")
    assert live_position.quantity == 2
    assert live_position.avg_price == Decimal("90.0000")
    assert live_position.realized_pnl == Decimal("10.25")
    assert paper_position.quantity == 7
