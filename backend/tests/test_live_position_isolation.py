from decimal import Decimal

from app.models.broker_connection import BrokerConnection
from app.models.live_position import LivePosition
from app.models.position import Position
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.portfolio_repository import PortfolioRepository
from app.services.instrument_service import InstrumentService


def test_live_positions_are_isolated_from_paper_position_rows(db_session, make_user):
    user = make_user()
    portfolio = PortfolioRepository(db_session).create(
        user_id=user.id, name="Position isolation", virtual_capital=Decimal("100000")
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
    db_session.add(connection)
    db_session.flush()

    paper_position = Position(
        portfolio_id=portfolio.id,
        instrument_id=instrument.id,
        quantity=3,
        avg_price=Decimal("90"),
        realized_pnl=Decimal("0"),
    )
    live_position = LivePosition(
        broker_connection_id=connection.id,
        instrument_id=instrument.id,
        quantity=2,
        avg_price=Decimal("100"),
        realized_pnl=Decimal("0"),
    )
    db_session.add_all([paper_position, live_position])
    db_session.commit()

    stored_paper = db_session.query(Position).filter(
        Position.portfolio_id == portfolio.id, Position.instrument_id == instrument.id
    ).one()
    stored_live = db_session.query(LivePosition).filter(
        LivePosition.broker_connection_id == connection.id,
        LivePosition.instrument_id == instrument.id,
    ).one()

    assert stored_paper.quantity == 3
    assert stored_paper.avg_price == Decimal("90.0000")
    assert stored_live.quantity == 2
    assert stored_live.avg_price == Decimal("100.0000")
    assert db_session.query(Position).count() == 1
    assert db_session.query(LivePosition).count() == 1


def test_same_instrument_can_have_distinct_live_positions_per_broker_connection(db_session, make_user):
    first_user = make_user()
    second_user = make_user(email="second-live-account@example.com")
    InstrumentService(db_session).seed_defaults()
    instrument = InstrumentRepository(db_session).search("RELIANCE")[0]
    connections = [
        BrokerConnection(
            user_id=owner.id,
            broker="upstox",
            api_key_encrypted=f"key-{index}",
            api_secret_encrypted=f"secret-{index}",
            redirect_uri="https://example.invalid/callback",
            is_connected=True,
        )
        for index, owner in enumerate((first_user, second_user), start=1)
    ]
    db_session.add_all(connections)
    db_session.flush()
    db_session.add_all([
        LivePosition(
            broker_connection_id=connections[0].id,
            instrument_id=instrument.id,
            quantity=1,
            avg_price=Decimal("100"),
            realized_pnl=Decimal("0"),
        ),
        LivePosition(
            broker_connection_id=connections[1].id,
            instrument_id=instrument.id,
            quantity=-2,
            avg_price=Decimal("110"),
            realized_pnl=Decimal("0"),
        ),
    ])
    db_session.commit()

    assert db_session.query(LivePosition).count() == 2
