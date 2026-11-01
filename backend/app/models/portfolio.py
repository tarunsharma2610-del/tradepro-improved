import uuid

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Portfolio(BaseModel):
    __tablename__ = "portfolios"
    __table_args__ = (
        CheckConstraint("trading_mode IN ('PAPER', 'LIVE')", name="ck_portfolios_trading_mode"),
        CheckConstraint("balance_source IN ('SIMULATED', 'UNAVAILABLE', 'BROKER')", name="ck_portfolios_balance_source"),
        CheckConstraint(
            "(trading_mode = 'PAPER' AND balance_source = 'SIMULATED') OR "
            "(trading_mode = 'LIVE' AND balance_source IN ('UNAVAILABLE', 'BROKER'))",
            name="ck_portfolios_balance_source_mode",
        ),
        UniqueConstraint("id", "trading_mode", name="uq_portfolios_id_trading_mode"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Existing portfolios are backfilled PAPER; LIVE remains unavailable until isolation gates pass.
    trading_mode: Mapped[str] = mapped_column(String(5), nullable=False, default="PAPER", server_default="PAPER")

    # Set once at creation, never changed by trading activity — the
    # starting line for measuring overall portfolio performance.
    virtual_capital: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    # Moves with every fill (buys reduce it, sells increase it, all
    # transaction costs come out of it) — this IS the tenant/portfolio
    # accounting model referenced in the architecture rules, not a
    # separate implementation from what Phase 3+ strategies will use.
    cash_balance: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    # LIVE funds are unavailable until a verified broker balance sync completes.
    # PAPER balances are simulated and must never be presented as broker funds.
    balance_source: Mapped[str] = mapped_column(
        String(16), nullable=False, default="SIMULATED", server_default="SIMULATED"
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Optional user-configurable portfolio risk controls.
    risk_controls_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_daily_loss: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    max_open_exposure: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    max_order_value: Mapped[float | None] = mapped_column(Numeric(18, 2), nullable=True)
    max_open_positions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_orders_per_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
