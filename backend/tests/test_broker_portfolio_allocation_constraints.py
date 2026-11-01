import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import Base
import app.models  # noqa: F401
from app.models.broker_connection import BrokerConnection
from app.models.broker_portfolio_allocation import BrokerPortfolioAllocation
from app.models.portfolio import Portfolio
from app.models.user import User


@pytest.fixture()
def allocation_db():
    engine = create_engine("sqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def _user(db: Session, email: str) -> User:
    user = User(
        email=email,
        password_hash="test-only",
        full_name="Allocation Test",
    )
    db.add(user)
    db.flush()
    return user


def _live_portfolio(db: Session, user: User, name: str = "LIVE") -> Portfolio:
    portfolio = Portfolio(
        user_id=user.id,
        name=name,
        trading_mode="LIVE",
        virtual_capital=0,
        cash_balance=0,
        balance_source="UNAVAILABLE",
    )
    db.add(portfolio)
    db.flush()
    return portfolio


def _broker_connection(db: Session, user: User) -> BrokerConnection:
    connection = BrokerConnection(
        user_id=user.id,
        broker="upstox",
        api_key_encrypted="encrypted-test-key",
        api_secret_encrypted="encrypted-test-secret",
        redirect_uri="https://example.invalid/callback",
    )
    db.add(connection)
    db.flush()
    return connection


def test_allocation_accepts_same_users_live_portfolio_and_broker(allocation_db):
    user = _user(allocation_db, "owner@example.com")
    portfolio = _live_portfolio(allocation_db, user)
    connection = _broker_connection(allocation_db, user)
    allocation = BrokerPortfolioAllocation(
        user_id=user.id,
        portfolio_id=portfolio.id,
        broker_connection_id=connection.id,
        trading_mode="LIVE",
    )
    allocation_db.add(allocation)
    allocation_db.commit()

    saved = allocation_db.query(BrokerPortfolioAllocation).one()
    assert saved.user_id == user.id
    assert saved.portfolio_id == portfolio.id
    assert saved.broker_connection_id == connection.id


def test_allocation_rejects_cross_user_broker_connection(allocation_db):
    owner = _user(allocation_db, "portfolio-owner@example.com")
    other = _user(allocation_db, "broker-owner@example.com")
    portfolio = _live_portfolio(allocation_db, owner)
    connection = _broker_connection(allocation_db, other)
    allocation_db.add(BrokerPortfolioAllocation(
        user_id=owner.id,
        portfolio_id=portfolio.id,
        broker_connection_id=connection.id,
        trading_mode="LIVE",
    ))
    with pytest.raises(IntegrityError):
        allocation_db.commit()


def test_allocation_rejects_paper_portfolio(allocation_db):
    user = _user(allocation_db, "paper-owner@example.com")
    paper = Portfolio(
        user_id=user.id,
        name="PAPER",
        trading_mode="PAPER",
        virtual_capital=10000,
        cash_balance=10000,
        balance_source="SIMULATED",
    )
    connection = _broker_connection(allocation_db, user)
    allocation_db.add(paper)
    allocation_db.flush()
    allocation_db.add(BrokerPortfolioAllocation(
        user_id=user.id,
        portfolio_id=paper.id,
        broker_connection_id=connection.id,
        trading_mode="LIVE",
    ))
    with pytest.raises(IntegrityError):
        allocation_db.commit()


def test_broker_connection_cannot_be_allocated_to_two_portfolios(allocation_db):
    user = _user(allocation_db, "single-account@example.com")
    first = _live_portfolio(allocation_db, user, "LIVE one")
    second = _live_portfolio(allocation_db, user, "LIVE two")
    connection = _broker_connection(allocation_db, user)
    allocation_db.add(BrokerPortfolioAllocation(
        user_id=user.id, portfolio_id=first.id,
        broker_connection_id=connection.id, trading_mode="LIVE",
    ))
    allocation_db.commit()

    allocation_db.add(BrokerPortfolioAllocation(
        user_id=user.id, portfolio_id=second.id,
        broker_connection_id=connection.id, trading_mode="LIVE",
    ))
    with pytest.raises(IntegrityError):
        allocation_db.commit()


def test_live_portfolio_cannot_be_allocated_to_two_broker_connections(allocation_db):
    user = _user(allocation_db, "single-portfolio@example.com")
    portfolio = _live_portfolio(allocation_db, user)
    first = _broker_connection(allocation_db, user)
    second = BrokerConnection(
        user_id=user.id,
        broker="zerodha",
        api_key_encrypted="encrypted-test-key-2",
        api_secret_encrypted="encrypted-test-secret-2",
        redirect_uri="https://example.invalid/callback-2",
    )
    allocation_db.add(second)
    allocation_db.flush()
    allocation_db.add(BrokerPortfolioAllocation(
        user_id=user.id, portfolio_id=portfolio.id,
        broker_connection_id=first.id, trading_mode="LIVE",
    ))
    allocation_db.commit()

    allocation_db.add(BrokerPortfolioAllocation(
        user_id=user.id, portfolio_id=portfolio.id,
        broker_connection_id=second.id, trading_mode="LIVE",
    ))
    with pytest.raises(IntegrityError):
        allocation_db.commit()


def test_funds_snapshot_is_owner_scoped_and_live_only(allocation_db):
    from decimal import Decimal
    from app.models.broker_funds_snapshot import BrokerFundsSnapshot

    owner = _user(allocation_db, "funds-owner@example.com")
    other = _user(allocation_db, "funds-other@example.com")
    portfolio = _live_portfolio(allocation_db, owner)
    connection = _broker_connection(allocation_db, owner)
    snapshot = BrokerFundsSnapshot(
        broker_connection_id=connection.id,
        portfolio_id=portfolio.id,
        user_id=owner.id,
        trading_mode="LIVE",
        total_available_to_trade=Decimal("500.00"),
        cash_available_to_trade=Decimal("450.00"),
        pledge_available_to_trade=Decimal("50.00"),
        unsettled_profit_today=Decimal("0.00"),
        unsettled_profit_previous_days=Decimal("0.00"),
        raw_response={"status": "success", "data": {}},
    )
    allocation_db.add(snapshot)
    allocation_db.commit()
    assert allocation_db.query(BrokerFundsSnapshot).count() == 1

    allocation_db.add(BrokerFundsSnapshot(
        broker_connection_id=connection.id,
        portfolio_id=portfolio.id,
        user_id=other.id,
        trading_mode="LIVE",
        total_available_to_trade=Decimal("500.00"),
        cash_available_to_trade=Decimal("450.00"),
        pledge_available_to_trade=Decimal("50.00"),
        unsettled_profit_today=Decimal("0.00"),
        unsettled_profit_previous_days=Decimal("0.00"),
        raw_response={"status": "success", "data": {}},
    ))
    with pytest.raises(IntegrityError):
        allocation_db.commit()
