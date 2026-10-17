from uuid import UUID

from sqlalchemy.orm import Session

from app.models.strategy import Strategy


class StrategyRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_portfolio(self, portfolio_id: UUID) -> list[Strategy]:
        return self.db.query(Strategy).filter(Strategy.portfolio_id == portfolio_id).all()

    def get_for_portfolio(self, portfolio_id: UUID, strategy_id: UUID) -> Strategy | None:
        return self.db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.portfolio_id == portfolio_id).first()

    def list_all_active(self) -> list[Strategy]:
        """Used by the worker loop — deliberately not tenant-scoped, since
        the worker evaluates every active strategy across every user."""
        return self.db.query(Strategy).filter(Strategy.is_active.is_(True)).all()

    def create(self, strategy: Strategy) -> Strategy:
        self.db.add(strategy)
        self.db.commit()
        self.db.refresh(strategy)
        return strategy

    def save(self, strategy: Strategy) -> Strategy:
        self.db.add(strategy)
        self.db.commit()
        self.db.refresh(strategy)
        return strategy

    def delete(self, strategy: Strategy) -> None:
        self.db.delete(strategy)
        self.db.commit()
