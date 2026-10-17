from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.portfolio import Portfolio


class PortfolioRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_user(self, user_id: UUID) -> list[Portfolio]:
        return (
            self.db.query(Portfolio)
            .filter(Portfolio.user_id == user_id, Portfolio.is_active.is_(True))
            .order_by(Portfolio.created_at)
            .all()
        )

    def get_for_user(self, user_id: UUID, portfolio_id: UUID) -> Portfolio | None:
        """The ownership check lives HERE, in the query itself — not as an
        afterthought comparison once the row is already loaded."""
        return (
            self.db.query(Portfolio)
            .filter(Portfolio.id == portfolio_id, Portfolio.user_id == user_id)
            .first()
        )

    def get_by_id(self, portfolio_id: UUID) -> Portfolio | None:
        """No ownership check — for internal/system callers only (the
        strategy worker), which already reached this portfolio_id through
        a legitimate path: the Strategy row's own FK, itself only ever set
        by an already-ownership-checked API call. Never call this from
        anything handling a live user request."""
        return self.db.get(Portfolio, portfolio_id)

    def create(self, *, user_id: UUID, name: str, virtual_capital: Decimal) -> Portfolio:
        portfolio = Portfolio(user_id=user_id, name=name, virtual_capital=virtual_capital, cash_balance=virtual_capital)
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    def save(self, portfolio: Portfolio) -> Portfolio:
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio
