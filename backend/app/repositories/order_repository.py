from uuid import UUID

from sqlalchemy.orm import Session

from app.models.order import Order


class OrderRepository:
    """Scoped by portfolio_id, not user_id directly — callers must resolve
    the portfolio via PortfolioRepository.get_for_user(user_id, portfolio_id)
    FIRST and only call these methods once that ownership check has
    already passed. See services/execution_service.py, which is the only
    place that's supposed to call these."""

    def __init__(self, db: Session):
        self.db = db

    def list_for_portfolio(self, portfolio_id: UUID, limit: int = 100) -> list[Order]:
        return (
            self.db.query(Order)
            .filter(Order.portfolio_id == portfolio_id)
            .order_by(Order.placed_at.desc())
            .limit(limit)
            .all()
        )

    def get_for_portfolio(self, portfolio_id: UUID, order_id: UUID) -> Order | None:
        return self.db.query(Order).filter(Order.id == order_id, Order.portfolio_id == portfolio_id).first()

    def get_for_paper_stop_event(self, event_id: UUID) -> Order | None:
        """Return the single durable order result associated with a stop event."""
        return self.db.query(Order).filter(Order.paper_stop_event_id == event_id).first()

    def create(self, order: Order, *, commit: bool = True) -> Order:
        """Persist an order; callers may retain transaction ownership."""
        self.db.add(order)
        if commit:
            self.db.commit()
            self.db.refresh(order)
        else:
            self.db.flush()
        return order

    def save(self, order: Order, *, commit: bool = True) -> Order:
        """Persist an order; callers may retain transaction ownership."""
        self.db.add(order)
        if commit:
            self.db.commit()
            self.db.refresh(order)
        else:
            self.db.flush()
        return order
