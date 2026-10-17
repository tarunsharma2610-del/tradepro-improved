import uuid

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Portfolio(BaseModel):
    __tablename__ = "portfolios"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Set once at creation, never changed by trading activity — the
    # starting line for measuring overall portfolio performance.
    virtual_capital: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    # Moves with every fill (buys reduce it, sells increase it, all
    # transaction costs come out of it) — this IS the tenant/portfolio
    # accounting model referenced in the architecture rules, not a
    # separate implementation from what Phase 3+ strategies will use.
    cash_balance: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
