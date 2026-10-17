from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.brokers.base import BrokerCallResult
from app.core.encryption import encrypt_value
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.execution_service import ExecutionService, OrderValidationError
from app.services.execution_service import PlaceOrderRequest as ServicePlaceOrderRequest
from app.services.instrument_service import InstrumentService
from app.services.transaction_costs import Segment, Side


@pytest.fixture()
def instrument(db_session):
    InstrumentService(db_session).seed_defaults()
    from app.repositories.instrument_repository import InstrumentRepository

    return InstrumentRepository(db_session).search("RELIANCE")[0]


@pytest.fixture()
def portfolio(db_session, make_user):
    user = make_user()
    p = PortfolioRepository(db_session).create(user_id=user.id, name="Main", virtual_capital=Decimal("100000"))
    return user, p


def _connect_fake_broker(db_session, user_id):
    """Gives the user a 'connected' Upstox session without any real
    network call — mirrors what complete_oauth() would have set, so the
    execution service's access-token lookup exercises the real code path."""
    from datetime import datetime, timedelta, timezone

    from app.models.broker_connection import BrokerConnection

    conn = BrokerConnection(
        user_id=user_id,
        broker="upstox",
        api_key_encrypted=encrypt_value("fake-key"),
        api_secret_encrypted=encrypt_value("fake-secret"),
        redirect_uri="https://example.com/cb",
        access_token_encrypted=encrypt_value("fake-access-token"),
        access_token_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        is_connected=True,
    )
    db_session.add(conn)
    db_session.commit()


def _mock_quote(price: str):
    """The only thing mocked is the actual HTTP call to Upstox — real
    account credentials aren't available in a test environment. Everything
    downstream (cost calc, position update, cash accounting) is real."""
    return patch(
        "app.services.execution_service.get_broker_adapter",
        return_value=type(
            "FakeAdapter", (), {"get_quote": AsyncMock(return_value=BrokerCallResult(ok=True, data={"data": {"NSE_EQ|INE002A01018": {"last_price": price}}}))}
        )(),
    )


@pytest.mark.asyncio
async def test_market_buy_fills_updates_position_and_cash(db_session, portfolio, instrument):
    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    service = ExecutionService(db_session)

    with _mock_quote("2500.00"):
        order = await service.place_order(
            user.id,
            ServicePlaceOrderRequest(
                portfolio_id=p.id, instrument_id=instrument.id, side=Side.BUY,
                order_type="MARKET", segment=Segment.EQUITY_DELIVERY, quantity=10,
            ),
        )

    assert order.status == "FILLED"

    db_session.refresh(p)
    # Cash should have dropped by more than the raw 10*2500=25000 (charges add on top).
    assert p.cash_balance < Decimal("100000") - Decimal("25000")

    from app.repositories.position_repository import PositionRepository

    position = PositionRepository(db_session).get_or_create(p.id, instrument.id)
    assert position.quantity == 10
    assert position.avg_price == Decimal("2500.0000")

    from app.models.execution import Execution

    execution = db_session.query(Execution).filter(Execution.order_id == order.id).first()
    assert execution is not None
    assert execution.total_charges > 0


@pytest.mark.asyncio
async def test_order_rejected_without_a_connected_broker_never_fakes_a_price(db_session, portfolio, instrument):
    """No broker connection at all — this must REJECT, not silently fill
    at some invented price."""
    user, p = portfolio
    service = ExecutionService(db_session)

    order = await service.place_order(
        user.id,
        ServicePlaceOrderRequest(
            portfolio_id=p.id, instrument_id=instrument.id, side=Side.BUY,
            order_type="MARKET", segment=Segment.EQUITY_DELIVERY, quantity=10,
        ),
    )

    assert order.status == "REJECTED"
    assert "broker" in order.rejection_reason.lower()

    db_session.refresh(p)
    assert p.cash_balance == Decimal("100000")  # untouched


@pytest.mark.asyncio
async def test_buy_rejected_when_it_would_exceed_available_cash(db_session, portfolio, instrument):
    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    service = ExecutionService(db_session)

    with _mock_quote("2500.00"):
        order = await service.place_order(
            user.id,
            ServicePlaceOrderRequest(
                portfolio_id=p.id, instrument_id=instrument.id, side=Side.BUY,
                order_type="MARKET", segment=Segment.EQUITY_DELIVERY, quantity=1000,  # 25,00,000 >> 1,00,000 capital
            ),
        )

    assert order.status == "REJECTED"
    assert "insufficient" in order.rejection_reason.lower()


@pytest.mark.asyncio
async def test_delivery_sell_rejected_without_holding_the_shares(db_session, portfolio, instrument):
    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    service = ExecutionService(db_session)

    with _mock_quote("2500.00"):
        order = await service.place_order(
            user.id,
            ServicePlaceOrderRequest(
                portfolio_id=p.id, instrument_id=instrument.id, side=Side.SELL,
                order_type="MARKET", segment=Segment.EQUITY_DELIVERY, quantity=5,
            ),
        )

    assert order.status == "REJECTED"
    assert "holdings" in order.rejection_reason.lower()


@pytest.mark.asyncio
async def test_intraday_sell_allowed_without_holding_shares_short_selling(db_session, portfolio, instrument):
    """Same setup as the delivery test above, but EQUITY_INTRADAY permits
    going short — this is a real, intentional difference, not an
    oversight, so it's tested explicitly rather than just implied by the
    delivery test passing."""
    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    service = ExecutionService(db_session)

    with _mock_quote("2500.00"):
        order = await service.place_order(
            user.id,
            ServicePlaceOrderRequest(
                portfolio_id=p.id, instrument_id=instrument.id, side=Side.SELL,
                order_type="MARKET", segment=Segment.EQUITY_INTRADAY, quantity=5,
            ),
        )

    assert order.status == "FILLED"

    from app.repositories.position_repository import PositionRepository

    position = PositionRepository(db_session).get_or_create(p.id, instrument.id)
    assert position.quantity == -5


@pytest.mark.asyncio
async def test_limit_order_accepted_but_not_filled_in_phase_2(db_session, portfolio, instrument):
    user, p = portfolio
    service = ExecutionService(db_session)

    order = await service.place_order(
        user.id,
        ServicePlaceOrderRequest(
            portfolio_id=p.id, instrument_id=instrument.id, side=Side.BUY,
            order_type="LIMIT", segment=Segment.EQUITY_DELIVERY, quantity=5, limit_price=Decimal("2400"),
        ),
    )

    assert order.status == "PENDING"


@pytest.mark.asyncio
async def test_cannot_place_an_order_on_another_users_portfolio(db_session, portfolio, instrument, make_user):
    _, p = portfolio  # belongs to the first user
    other_user = make_user(email="other@example.com")
    service = ExecutionService(db_session)

    with pytest.raises(OrderValidationError):
        await service.place_order(
            other_user.id,
            ServicePlaceOrderRequest(
                portfolio_id=p.id, instrument_id=instrument.id, side=Side.BUY,
                order_type="MARKET", segment=Segment.EQUITY_DELIVERY, quantity=1,
            ),
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_price", ["NaN", "Infinity", "-1", "0", "not-a-price"])
async def test_invalid_quote_price_is_rejected_without_changing_portfolio(db_session, portfolio, instrument, bad_price):
    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    service = ExecutionService(db_session)

    with _mock_quote(bad_price):
        order = await service.place_order(
            user.id,
            ServicePlaceOrderRequest(
                portfolio_id=p.id,
                instrument_id=instrument.id,
                side=Side.BUY,
                order_type="MARKET",
                segment=Segment.EQUITY_DELIVERY,
                quantity=1,
            ),
        )

    assert order.status == "REJECTED"
    assert "price" in order.rejection_reason.lower() or "last traded" in order.rejection_reason.lower()
    db_session.refresh(p)
    assert p.cash_balance == Decimal("100000")


@pytest.mark.asyncio
async def test_invalid_limit_order_input_is_rejected_before_database_order_creation(db_session, portfolio, instrument):
    user, p = portfolio
    service = ExecutionService(db_session)

    with pytest.raises(OrderValidationError, match="positive limit price"):
        await service.place_order(
            user.id,
            ServicePlaceOrderRequest(
                portfolio_id=p.id,
                instrument_id=instrument.id,
                side=Side.BUY,
                order_type="LIMIT",
                segment=Segment.EQUITY_DELIVERY,
                quantity=1,
                limit_price=Decimal("0"),
            ),
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "order_type,quantity,limit_price,expected_message",
    [
        ("MARKET", 0, None, "Quantity"),
        ("LIMIT", 1, None, "limit price"),
        ("LIMIT", 1, Decimal("0"), "limit price"),
        ("LIMIT", 1, Decimal("-1"), "limit price"),
        ("MARKET", 1, Decimal("2500"), "must not include"),
    ],
)
async def test_malformed_orders_are_rejected_before_broker_or_database_side_effects(
    db_session, portfolio, instrument, order_type, quantity, limit_price, expected_message
):
    user, p = portfolio
    service = ExecutionService(db_session)

    with pytest.raises(OrderValidationError, match=expected_message):
        await service.place_order(
            user.id,
            ServicePlaceOrderRequest(
                portfolio_id=p.id,
                instrument_id=instrument.id,
                side=Side.BUY,
                order_type=order_type,
                segment=Segment.EQUITY_DELIVERY,
                quantity=quantity,
                limit_price=limit_price,
            ),
        )


@pytest.mark.asyncio
async def test_crossed_paper_limit_buy_fills_and_updates_position(db_session, portfolio, instrument):
    user, p = portfolio
    service = ExecutionService(db_session)
    order = await service.place_order(
        user.id,
        ServicePlaceOrderRequest(
            portfolio_id=p.id,
            instrument_id=instrument.id,
            side=Side.BUY,
            order_type="LIMIT",
            segment=Segment.EQUITY_DELIVERY,
            quantity=5,
            limit_price=Decimal("2400"),
        ),
    )
    _connect_fake_broker(db_session, user.id)

    with _mock_quote("2300"):
        filled = await service.match_pending_limit_orders()

    assert filled == 1
    db_session.refresh(order)
    db_session.refresh(p)
    assert order.status == "FILLED"
    assert p.cash_balance < Decimal("100000") - Decimal("11500")

    from app.repositories.position_repository import PositionRepository
    from app.models.execution import Execution

    position = PositionRepository(db_session).get_or_create(p.id, instrument.id)
    execution = db_session.query(Execution).filter(Execution.order_id == order.id).one()
    assert position.quantity == 5
    assert execution.price == Decimal("2300")


@pytest.mark.asyncio
async def test_paper_limit_order_stays_pending_until_price_crosses(db_session, portfolio, instrument):
    user, p = portfolio
    service = ExecutionService(db_session)
    order = await service.place_order(
        user.id,
        ServicePlaceOrderRequest(
            portfolio_id=p.id,
            instrument_id=instrument.id,
            side=Side.BUY,
            order_type="LIMIT",
            segment=Segment.EQUITY_DELIVERY,
            quantity=1,
            limit_price=Decimal("2400"),
        ),
    )
    _connect_fake_broker(db_session, user.id)

    with _mock_quote("2500"):
        filled = await service.match_pending_limit_orders()

    db_session.refresh(order)
    assert filled == 0
    assert order.status == "PENDING"


@pytest.mark.asyncio
async def test_crossed_delivery_limit_sell_without_holdings_is_rejected(db_session, portfolio, instrument):
    user, p = portfolio
    service = ExecutionService(db_session)
    order = await service.place_order(
        user.id,
        ServicePlaceOrderRequest(
            portfolio_id=p.id,
            instrument_id=instrument.id,
            side=Side.SELL,
            order_type="LIMIT",
            segment=Segment.EQUITY_DELIVERY,
            quantity=1,
            limit_price=Decimal("2400"),
        ),
    )
    _connect_fake_broker(db_session, user.id)

    with _mock_quote("2500"):
        filled = await service.match_pending_limit_orders()

    db_session.refresh(order)
    assert filled == 0
    assert order.status == "REJECTED"
    assert "holdings" in order.rejection_reason.lower()


@pytest.mark.asyncio
async def test_pending_paper_limit_order_can_be_cancelled(db_session, portfolio, instrument):
    user, p = portfolio
    service = ExecutionService(db_session)
    order = await service.place_order(
        user.id,
        ServicePlaceOrderRequest(
            portfolio_id=p.id,
            instrument_id=instrument.id,
            side=Side.BUY,
            order_type="LIMIT",
            segment=Segment.EQUITY_DELIVERY,
            quantity=1,
            limit_price=Decimal("2400"),
        ),
    )

    cancelled = service.cancel_order(user.id, p.id, order.id)

    assert cancelled.status == "CANCELLED"


@pytest.mark.asyncio
async def test_cannot_cancel_another_users_order(db_session, portfolio, instrument, make_user):
    user, p = portfolio
    service = ExecutionService(db_session)
    order = await service.place_order(
        user.id,
        ServicePlaceOrderRequest(
            portfolio_id=p.id,
            instrument_id=instrument.id,
            side=Side.BUY,
            order_type="LIMIT",
            segment=Segment.EQUITY_DELIVERY,
            quantity=1,
            limit_price=Decimal("2400"),
        ),
    )
    other_user = make_user(email="order-owner-check@example.com")

    with pytest.raises(OrderValidationError, match="Portfolio not found"):
        service.cancel_order(other_user.id, p.id, order.id)


@pytest.mark.asyncio
async def test_filled_order_cannot_be_cancelled(db_session, portfolio, instrument):
    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    service = ExecutionService(db_session)
    with _mock_quote("2300"):
        order = await service.place_order(
            user.id,
            ServicePlaceOrderRequest(
                portfolio_id=p.id,
                instrument_id=instrument.id,
                side=Side.BUY,
                order_type="MARKET",
                segment=Segment.EQUITY_DELIVERY,
                quantity=1,
            ),
        )

    assert order.status == "FILLED"
    with pytest.raises(OrderValidationError, match="Only pending orders"):
        service.cancel_order(user.id, p.id, order.id)


@pytest.mark.asyncio
async def test_live_mode_fails_closed_before_creating_order(db_session, portfolio, instrument, monkeypatch):
    """LIVE mode must not create a paper order or reach broker execution."""
    from app.core.config import settings
    from app.models.order import Order

    user, p = portfolio
    monkeypatch.setattr(settings, "TRADING_MODE", "LIVE")
    before = db_session.query(Order).count()

    with pytest.raises(OrderValidationError, match="Live trading is not implemented"):
        await ExecutionService(db_session).place_order(
            user.id,
            ServicePlaceOrderRequest(
                portfolio_id=p.id,
                instrument_id=instrument.id,
                side=Side.BUY,
                order_type="MARKET",
                segment=Segment.EQUITY_DELIVERY,
                quantity=1,
            ),
        )

    assert db_session.query(Order).count() == before


@pytest.mark.asyncio
async def test_repeated_idempotency_key_returns_existing_order_without_duplicate(db_session, portfolio, instrument):
    user, p = portfolio
    service = ExecutionService(db_session)
    request = ServicePlaceOrderRequest(
        portfolio_id=p.id,
        instrument_id=instrument.id,
        side=Side.BUY,
        order_type="LIMIT",
        segment=Segment.EQUITY_DELIVERY,
        quantity=2,
        limit_price=Decimal("2400"),
        idempotency_key="client-retry-001",
    )
    first = await service.place_order(user.id, request)
    second = await service.place_order(user.id, request)

    from app.models.order import Order
    assert second.id == first.id
    assert db_session.query(Order).filter(Order.portfolio_id == p.id).count() == 1


@pytest.mark.asyncio
async def test_idempotency_key_cannot_be_reused_for_different_payload(db_session, portfolio, instrument):
    user, p = portfolio
    service = ExecutionService(db_session)
    await service.place_order(user.id, ServicePlaceOrderRequest(
        portfolio_id=p.id, instrument_id=instrument.id, side=Side.BUY,
        order_type="LIMIT", segment=Segment.EQUITY_DELIVERY, quantity=2,
        limit_price=Decimal("2400"), idempotency_key="client-retry-002",
    ))
    with pytest.raises(OrderValidationError, match="different order request"):
        await service.place_order(user.id, ServicePlaceOrderRequest(
            portfolio_id=p.id, instrument_id=instrument.id, side=Side.BUY,
            order_type="LIMIT", segment=Segment.EQUITY_DELIVERY, quantity=3,
            limit_price=Decimal("2400"), idempotency_key="client-retry-002",
        ))


@pytest.mark.asyncio
async def test_limit_order_rejected_above_configured_order_value_cap(db_session, portfolio, instrument, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "MAX_ORDER_VALUE_PCT_OF_VIRTUAL_CAPITAL", Decimal("25.0"))
    user, p = portfolio

    order = await ExecutionService(db_session).place_order(
        user.id,
        ServicePlaceOrderRequest(
            portfolio_id=p.id, instrument_id=instrument.id, side=Side.BUY,
            order_type="LIMIT", segment=Segment.EQUITY_DELIVERY, quantity=11,
            limit_price=Decimal("2400"),
        ),
    )

    assert order.status == "REJECTED"
    assert "maximum order value" in order.rejection_reason.lower()


@pytest.mark.asyncio
async def test_market_order_rejected_above_configured_order_value_cap(db_session, portfolio, instrument, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "MAX_ORDER_VALUE_PCT_OF_VIRTUAL_CAPITAL", Decimal("25.0"))
    user, p = portfolio
    _connect_fake_broker(db_session, user.id)

    with _mock_quote("2500"):
        order = await ExecutionService(db_session).place_order(
            user.id,
            ServicePlaceOrderRequest(
                portfolio_id=p.id, instrument_id=instrument.id, side=Side.BUY,
                order_type="MARKET", segment=Segment.EQUITY_DELIVERY, quantity=11,
            ),
        )

    assert order.status == "REJECTED"
    assert "maximum order value" in order.rejection_reason.lower()
    db_session.refresh(p)
    assert p.cash_balance == Decimal("100000")


@pytest.mark.asyncio
async def test_fill_accounting_rolls_back_atomically_if_execution_persistence_fails(
    db_session, portfolio, instrument
):
    """A failed fill must not leave a FILLED order, changed cash, or a changed
    position without the corresponding execution row."""
    from sqlalchemy import event

    from app.models.execution import Execution
    from app.models.order import Order
    from app.models.position import Position

    user, p = portfolio
    _connect_fake_broker(db_session, user.id)

    def fail_execution_insert(_mapper, _connection, _target):
        raise RuntimeError("simulated execution persistence failure")

    event.listen(Execution, "before_insert", fail_execution_insert)
    try:
        with _mock_quote("2500.00"):
            with pytest.raises(RuntimeError, match="simulated execution persistence failure"):
                await ExecutionService(db_session).place_order(
                    user.id,
                    ServicePlaceOrderRequest(
                        portfolio_id=p.id,
                        instrument_id=instrument.id,
                        side=Side.BUY,
                        order_type="MARKET",
                        segment=Segment.EQUITY_DELIVERY,
                        quantity=1,
                    ),
                )
    finally:
        event.remove(Execution, "before_insert", fail_execution_insert)

    # Roll back any failed SQLAlchemy unit of work before inspecting persisted state.
    db_session.rollback()
    db_session.expire_all()

    assert db_session.query(Order).filter(Order.portfolio_id == p.id).count() == 0
    assert db_session.query(Execution).filter(Execution.portfolio_id == p.id).count() == 0
    assert db_session.query(Position).filter(Position.portfolio_id == p.id).count() == 0
    db_session.refresh(p)
    assert p.cash_balance == Decimal("100000")
