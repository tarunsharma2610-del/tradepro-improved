from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.brokers.base import BrokerCallResult
from app.models.execution import Execution
from app.models.order import Order
from app.core.encryption import encrypt_value
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.execution_service import ExecutionService, OrderValidationError, _extract_fresh_market_depth_price, _extract_ltp
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
        analytics_token_encrypted=encrypt_value("fake-analytics-token"),
        analytics_token_expires_at=datetime.now(timezone.utc) + timedelta(days=365),
        is_connected=True,
    )
    db_session.add(conn)
    db_session.commit()


def _mock_quote(price: str):
    """The only thing mocked is the actual HTTP call to Upstox — real
    account credentials aren't available in a test environment. Everything
    downstream (cost calc, position update, cash accounting) is real."""
    now = datetime.now(timezone.utc).isoformat()
    level = {"price": price, "quantity": 100000, "orders": 10}
    quote = {
        "instrument_token": "NSE_EQ|INE002A01018",
        "last_price": price,
        "last_trade_time": "1600000000000",
        "timestamp": now,
        "depth": {"buy": [level], "sell": [level]},
    }
    return patch(
        "app.services.execution_service.get_broker_adapter",
        return_value=type(
            "FakeAdapter",
            (),
            {"get_full_quote": AsyncMock(return_value=BrokerCallResult(ok=True, data={"data": {"NSE_EQ:TEST": quote}}))},
        )(),
    )


@pytest.mark.asyncio
async def test_market_buy_fills_updates_position_and_cash(db_session, portfolio, instrument):
    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    service = ExecutionService(db_session)

    with patch("app.services.execution_service.settings.UPSTOX_CHARGE_ESTIMATES_ENABLED", False), _mock_quote("2500.00"):
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
    assert execution.charge_source == "PAPER_HARDCODED_FALLBACK"


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
async def test_portfolio_daily_realized_loss_limit_blocks_new_entry(db_session, portfolio, instrument):
    user, p = portfolio
    p.risk_controls_enabled = True
    p.max_daily_loss = Decimal("500")
    now = datetime.now(timezone.utc)
    filled_order = Order(
        portfolio_id=p.id, instrument_id=instrument.id, side="SELL",
        order_type="MARKET", segment="EQUITY_INTRADAY", quantity=1,
        limit_price=None, status="FILLED", trading_mode="PAPER",
        execution_reason="MANUAL", strategy_id=None, placed_at=now, filled_at=now,
    )
    db_session.add(filled_order)
    db_session.flush()
    db_session.add(Execution(
        order_id=filled_order.id, portfolio_id=p.id, instrument_id=instrument.id,
        side="SELL", quantity=1, price=Decimal("100"), gross_value=Decimal("100"),
        brokerage=Decimal("0"), stt=Decimal("0"), exchange_charges=Decimal("0"),
        sebi_charges=Decimal("0"), stamp_duty=Decimal("0"), gst=Decimal("0"),
        total_charges=Decimal("0"), realized_pnl=Decimal("-500"), executed_at=now,
    ))
    db_session.commit()
    _connect_fake_broker(db_session, user.id)

    with _mock_quote("2500"):
        order = await ExecutionService(db_session).place_order(
            user.id,
            ServicePlaceOrderRequest(
                portfolio_id=p.id, instrument_id=instrument.id, side=Side.BUY,
                order_type="MARKET", segment=Segment.EQUITY_DELIVERY, quantity=1,
            ),
        )

    assert order.status == "REJECTED"
    assert "daily realized loss" in order.rejection_reason.lower()


@pytest.mark.asyncio
async def test_portfolio_daily_loss_resets_at_india_midnight(db_session, portfolio, instrument):
    from datetime import time, timedelta
    from zoneinfo import ZoneInfo

    user, p = portfolio
    p.risk_controls_enabled = True
    p.max_daily_loss = Decimal("500")
    today_ist = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    session_start = datetime.combine(today_ist, time.min, tzinfo=ZoneInfo("Asia/Kolkata")).astimezone(timezone.utc)
    prior_session_time = session_start - timedelta(seconds=1)
    prior_order = Order(
        portfolio_id=p.id, instrument_id=instrument.id, side="SELL",
        order_type="MARKET", segment="EQUITY_INTRADAY", quantity=1,
        limit_price=None, status="FILLED", trading_mode="PAPER",
        execution_reason="MANUAL", strategy_id=None,
        placed_at=prior_session_time, filled_at=prior_session_time,
    )
    db_session.add(prior_order)
    db_session.flush()
    db_session.add(Execution(
        order_id=prior_order.id, portfolio_id=p.id, instrument_id=instrument.id,
        side="SELL", quantity=1, price=Decimal("100"), gross_value=Decimal("100"),
        brokerage=Decimal("0"), stt=Decimal("0"), exchange_charges=Decimal("0"),
        sebi_charges=Decimal("0"), stamp_duty=Decimal("0"), gst=Decimal("0"),
        total_charges=Decimal("0"), realized_pnl=Decimal("-500"), executed_at=prior_session_time,
    ))
    db_session.commit()
    _connect_fake_broker(db_session, user.id)

    with _mock_quote("2500"):
        order = await ExecutionService(db_session).place_order(
            user.id,
            ServicePlaceOrderRequest(
                portfolio_id=p.id, instrument_id=instrument.id, side=Side.BUY,
                order_type="MARKET", segment=Segment.EQUITY_DELIVERY, quantity=1,
            ),
        )

    assert order.status == "FILLED"


@pytest.mark.asyncio
async def test_manual_portfolio_order_value_limit_rejects_market_order(db_session, portfolio, instrument):
    user, p = portfolio
    p.risk_controls_enabled = True
    p.max_order_value = Decimal("1000")
    db_session.commit()
    _connect_fake_broker(db_session, user.id)

    with _mock_quote("2500"):
        order = await ExecutionService(db_session).place_order(
            user.id,
            ServicePlaceOrderRequest(
                portfolio_id=p.id, instrument_id=instrument.id, side=Side.BUY,
                order_type="MARKET", segment=Segment.EQUITY_DELIVERY, quantity=1,
            ),
        )

    assert order.status == "REJECTED"
    assert "order value" in order.rejection_reason.lower()
    db_session.refresh(p)
    assert p.cash_balance == Decimal("100000")


@pytest.mark.asyncio
async def test_manual_portfolio_order_value_limit_rejects_limit_order(db_session, portfolio, instrument):
    user, p = portfolio
    p.risk_controls_enabled = True
    p.max_order_value = Decimal("1000")
    db_session.commit()

    order = await ExecutionService(db_session).place_order(
        user.id,
        ServicePlaceOrderRequest(
            portfolio_id=p.id, instrument_id=instrument.id, side=Side.BUY,
            order_type="LIMIT", segment=Segment.EQUITY_DELIVERY, quantity=1,
            limit_price=Decimal("2500"),
        ),
    )

    assert order.status == "REJECTED"
    assert "order value" in order.rejection_reason.lower()


@pytest.mark.asyncio
async def test_pending_limit_orders_count_toward_estimated_portfolio_exposure(db_session, portfolio, instrument):
    user, p = portfolio
    p.risk_controls_enabled = True
    p.max_open_exposure = Decimal("3000")
    from app.repositories.instrument_repository import InstrumentRepository

    InstrumentService(db_session).seed_defaults()
    second_instrument = next(
        item for item in InstrumentRepository(db_session).search("TCS")
        if item.id != instrument.id
    )
    db_session.add(Order(
        portfolio_id=p.id,
        instrument_id=instrument.id,
        side="BUY",
        order_type="LIMIT",
        segment="EQUITY_DELIVERY",
        quantity=1,
        limit_price=Decimal("2000"),
        status="PENDING",
        trading_mode="PAPER",
        execution_reason="MANUAL",
        strategy_id=None,
        placed_at=datetime.now(timezone.utc),
    ))
    db_session.commit()

    order = await ExecutionService(db_session).place_order(
        user.id,
        ServicePlaceOrderRequest(
            portfolio_id=p.id, instrument_id=second_instrument.id, side=Side.BUY,
            order_type="LIMIT", segment=Segment.EQUITY_DELIVERY, quantity=1,
            limit_price=Decimal("1500"),
        ),
    )

    assert order.status == "REJECTED"
    assert "including pending limit orders" in order.rejection_reason.lower()


@pytest.mark.asyncio
async def test_portfolio_open_position_cap_rejects_new_instrument(db_session, portfolio, instrument):
    from app.models.position import Position
    from app.repositories.instrument_repository import InstrumentRepository

    user, p = portfolio
    p.risk_controls_enabled = True
    p.max_open_positions = 1
    db_session.add(Position(
        portfolio_id=p.id, instrument_id=instrument.id,
        quantity=2, avg_price=Decimal("100"), realized_pnl=Decimal("0"),
    ))
    db_session.commit()

    InstrumentService(db_session).seed_defaults()
    second_instrument = InstrumentRepository(db_session).search("TCS")[0]

    order = await ExecutionService(db_session).place_order(
        user.id,
        ServicePlaceOrderRequest(
            portfolio_id=p.id, instrument_id=second_instrument.id, side=Side.BUY,
            order_type="LIMIT", segment=Segment.EQUITY_DELIVERY, quantity=1,
            limit_price=Decimal("100"),
        ),
    )

    assert order.status == "REJECTED"
    assert "open or pending positions" in order.rejection_reason.lower()


@pytest.mark.asyncio
async def test_portfolio_daily_order_cap_rejects_additional_order(db_session, portfolio, instrument):
    user, p = portfolio
    p.risk_controls_enabled = True
    p.max_orders_per_day = 1
    now = datetime.now(timezone.utc)
    db_session.add(Order(
        portfolio_id=p.id, instrument_id=instrument.id, side="BUY",
        order_type="LIMIT", segment="EQUITY_DELIVERY", quantity=1,
        limit_price=Decimal("100"), status="CANCELLED", trading_mode="PAPER",
        execution_reason="MANUAL", strategy_id=None, placed_at=now,
    ))
    db_session.commit()

    # A cancelled order must not consume the daily order allowance.
    allowed = await ExecutionService(db_session).place_order(
        user.id,
        ServicePlaceOrderRequest(
            portfolio_id=p.id, instrument_id=instrument.id, side=Side.BUY,
            order_type="LIMIT", segment=Segment.EQUITY_DELIVERY, quantity=1,
            limit_price=Decimal("100"),
        ),
    )
    assert allowed.status == "PENDING"

    # The next request is rejected because the active order now consumes the cap.
    rejected = await ExecutionService(db_session).place_order(
        user.id,
        ServicePlaceOrderRequest(
            portfolio_id=p.id, instrument_id=instrument.id, side=Side.BUY,
            order_type="LIMIT", segment=Segment.EQUITY_DELIVERY, quantity=1,
            limit_price=Decimal("100"),
        ),
    )
    assert rejected.status == "REJECTED"
    assert "daily order cap" in rejected.rejection_reason.lower()


@pytest.mark.asyncio
async def test_portfolio_risk_controls_disabled_by_default(db_session, portfolio, instrument):
    user, p = portfolio
    assert p.risk_controls_enabled is False
    _connect_fake_broker(db_session, user.id)
    with _mock_quote("2500"):
        order = await ExecutionService(db_session).place_order(
            user.id,
            ServicePlaceOrderRequest(
                portfolio_id=p.id, instrument_id=instrument.id, side=Side.BUY,
                order_type="MARKET", segment=Segment.EQUITY_DELIVERY, quantity=1,
            ),
        )
    assert order.status == "FILLED"


@pytest.mark.asyncio
async def test_paper_market_order_never_calls_broker_live_order_endpoint(db_session, portfolio, instrument):
    """A paper fill may read a live quote, but must never submit a real order."""
    user, p = portfolio
    _connect_fake_broker(db_session, user.id)
    service = ExecutionService(db_session)

    with _mock_quote("2500.00") as adapter_factory:
        adapter = adapter_factory.return_value
        adapter.place_order = AsyncMock()

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

        assert order.trading_mode == "PAPER"
        assert order.status == "FILLED"
        adapter.place_order.assert_not_awaited()



def test_quote_parser_uses_only_the_requested_instrument_key():
    requested = "NSE_EQ|INE002A01018"
    other = "NSE_EQ|OTHER_INSTRUMENT"

    assert _extract_ltp({"data": {requested: {"last_price": "123.45"}}}, requested) == Decimal("123.45")
    assert _extract_ltp({"data": {other: {"last_price": "9999.00"}}}, requested) is None



def test_market_depth_price_uses_fresh_snapshot_and_side_appropriate_depth():
    now = datetime(2026, 10, 30, 10, 0, tzinfo=timezone.utc)
    fresh = {
        "data": {
            "NSE_EQ:TEST": {
                "instrument_token": "NSE_EQ|INE002A01018",
                "last_price": "123.45",
                "last_trade_time": "1600000000000",
                "timestamp": now.isoformat(),
                "depth": {
                    "buy": [{"price": "123.40", "quantity": 2}],
                    "sell": [
                        {"price": "123.50", "quantity": 1},
                        {"price": "123.60", "quantity": 2},
                    ],
                },
            }
        }
    }
    assert _extract_fresh_market_depth_price(
        fresh, "NSE_EQ|INE002A01018", side=Side.BUY, quantity=2, now=now
    ) == Decimal("123.55")
    assert _extract_fresh_market_depth_price(
        fresh, "NSE_EQ|INE002A01018", side=Side.SELL, quantity=2, now=now
    ) == Decimal("123.40")
    assert _extract_fresh_market_depth_price(
        fresh, "NSE_EQ|OTHER", side=Side.BUY, quantity=1, now=now
    ) is None


def test_market_depth_rejects_stale_snapshot_and_insufficient_liquidity():
    now = datetime(2026, 10, 30, 10, 0, tzinfo=timezone.utc)
    quote = {
        "instrument_token": "NSE_EQ|INE002A01018",
        "timestamp": (now - timedelta(seconds=20)).isoformat(),
        "depth": {"buy": [{"price": "123.40", "quantity": 1}], "sell": [{"price": "123.50", "quantity": 1}]},
    }
    stale = {"data": {"NSE_EQ:TEST": quote}}
    assert _extract_fresh_market_depth_price(
        stale, "NSE_EQ|INE002A01018", side=Side.BUY, quantity=1, now=now
    ) is None
    quote["timestamp"] = now.isoformat()
    assert _extract_fresh_market_depth_price(
        stale, "NSE_EQ|INE002A01018", side=Side.BUY, quantity=2, now=now
    ) is None
