from uuid import UUID

from sqlalchemy.orm import Session

from app.models.position import Position


class PositionRepository:
    """Same contract as OrderRepository: scoped by portfolio_id, and it's
    the caller's job (services/execution_service.py) to have already
    verified the portfolio belongs to the requesting user."""

    def __init__(self, db: Session):
        self.db = db

    def list_for_portfolio(self, portfolio_id: UUID) -> list[Position]:
        return (
            self.db.query(Position)
            .filter(Position.portfolio_id == portfolio_id, Position.quantity != 0)
            .all()
        )

    def get_or_create(self, portfolio_id: UUID, instrument_id: UUID) -> Position:
        position = (
            self.db.query(Position)
            .filter(Position.portfolio_id == portfolio_id, Position.instrument_id == instrument_id)
            .first()
        )
        if position is None:
            position = Position(portfolio_id=portfolio_id, instrument_id=instrument_id, quantity=0, avg_price=0, realized_pnl=0)
            self.db.add(position)
            self.db.commit()
            self.db.refresh(position)
        return position

    def save(self, position: Position) -> Position:
        self.db.add(position)
        self.db.commit()
        self.db.refresh(position)
        return position
