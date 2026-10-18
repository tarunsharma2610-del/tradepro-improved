from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.brokers.upstox.response_parsing import BrokerTrade
from app.models.broker_connection import BrokerConnection
from app.models.broker_order import BrokerOrder
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.execution import Execution
from app.models.order import Order
from app.models.position import Position
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.broker_trade_ingestion_service import BrokerTradeIngestionService
from app.services.instrument_service import InstrumentService


@pytest.fixture()
def trade_context(db_session, make_user):
    user = make_user()
    portfolio = PortfolioRepository(db_session).create(
        user_id=user.id, name="Live intake test", virtual_capital=Decimal("100000")
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
    broker_order = BrokerOrder(
        order_id=order.id,
        broker_name="upstox",
        broker_order_id="broker-child-1",
        requested_quantity=5,
        filled_quantity=0,
    )
    db_session.add(broker_order)
    db_session.commit()
    return user, portfolio, instrument, connection, order, broker_order


def _trade(order_id="broker-child-1", trade_id="trade-001", quantity=2, price="100.25", **kwargs):
    return BrokerTrade(
        order_id=order_id,
        trade_id=trade_id,
        quantity=quantity,
        price=Decimal(price),
        side=kwargs.get("side", "BUY"),
        instrument_token=kwargs.get("instrument_token", "NSE_EQ|INE002A01018"),
        exchange_timestamp=kwargs.get("exchange_timestamp", "2026-10-18T09:20:00+05:30"),
    )


def test_ingestion_is_idempotent_and_does_not_mutate_accounting(db_session, trade_context):
    user, portfolio, instrument, _connection, order, broker_order = trade_context
    before_cash = Decimal(str(portfolio.cash_balance))
    service = BrokerTradeIngestionService(db_session)

    first = service.ingest_trades(user.id, order.id, "broker-child-1", [_trade()])
    second = service.ingest_trades(user.id, order.id, "broker-child-1", [_trade()])

    assert first.inserted_count == 1
    assert first.duplicate_count == 0
    assert second.inserted_count == 0
    assert second.duplicate_count == 1
    assert db_session.query(BrokerTradeRecord).count() == 1
    assert db_session.query(Execution).count() == 0
    assert db_session.query(Position).count() == 0
    db_session.refresh(portfolio)
    db_session.refresh(order)
    db_session.refresh(broker_order)
    assert Decimal(str(portfolio.cash_balance)) == before_cash
    assert order.status == "PENDING"
    assert broker_order.filled_quantity == 0


def test_ingestion_rejects_paper_order_and_wrong_broker_child(db_session, trade_context):
    user, _portfolio, _instrument, _connection, order, _broker_order = trade_context
    service = BrokerTradeIngestionService(db_session)

    order.trading_mode = "PAPER"
    db_session.commit()
    with pytest.raises(ValueError, match="LIVE"):
        service.ingest_trades(user.id, order.id, "broker-child-1", [_trade()])
    order.trading_mode = "LIVE"
    db_session.commit()

    with pytest.raises(ValueError, match="not mapped"):
        service.ingest_trades(user.id, order.id, "other-child", [_trade(order_id="other-child")])
    assert db_session.query(BrokerTradeRecord).count() == 0


@pytest.mark.parametrize(
    ("trade", "message"),
    [
        (_trade(order_id="other-child"), "does not match"),
        (_trade(side="SELL"), "side does not match"),
        (_trade(instrument_token="NSE_EQ|WRONG"), "instrument token"),
        (_trade(quantity=6), "exceed the local order quantity"),
        (_trade(quantity=0), "positive integer"),
        (_trade(price="NaN"), "positive amount"),
    ],
)
def test_ingestion_rejects_invalid_or_overfilled_trade(db_session, trade_context, trade, message):
    user, _portfolio, _instrument, _connection, order, _broker_order = trade_context
    with pytest.raises(ValueError, match=message):
        BrokerTradeIngestionService(db_session).ingest_trades(
            user.id, order.id, "broker-child-1", [trade]
        )
    assert db_session.query(BrokerTradeRecord).count() == 0


def test_conflicting_replay_is_rejected_and_original_record_preserved(db_session, trade_context):
    user, _portfolio, _instrument, _connection, order, _broker_order = trade_context
    service = BrokerTradeIngestionService(db_session)
    service.ingest_trades(user.id, order.id, "broker-child-1", [_trade()])

    with pytest.raises(ValueError, match="conflicting"):
        service.ingest_trades(
            user.id, order.id, "broker-child-1", [_trade(price="101.00")]
        )

    records = db_session.query(BrokerTradeRecord).all()
    assert len(records) == 1
    assert records[0].price == Decimal("100.2500")


def test_invalid_later_trade_rolls_back_entire_batch(db_session, trade_context):
    user, _portfolio, _instrument, _connection, order, _broker_order = trade_context
    with pytest.raises(ValueError, match="side does not match"):
        BrokerTradeIngestionService(db_session).ingest_trades(
            user.id, order.id, "broker-child-1", [_trade(), _trade(trade_id="trade-002", side="SELL")]
        )
    assert db_session.query(BrokerTradeRecord).count() == 0


def test_ingestion_enforces_order_ownership(db_session, trade_context, make_user):
    _owner, _portfolio, _instrument, _connection, order, _broker_order = trade_context
    stranger = make_user(email="stranger@example.com")
    with pytest.raises(ValueError, match="Order not found"):
        BrokerTradeIngestionService(db_session).ingest_trades(
            stranger.id, order.id, "broker-child-1", [_trade()]
        )
    assert db_session.query(BrokerTradeRecord).count() == 0
