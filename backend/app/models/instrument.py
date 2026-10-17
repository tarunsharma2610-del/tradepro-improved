from datetime import date

from sqlalchemy import Boolean, Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Instrument(BaseModel):
    """One row per tradable instrument. `instrument_key` is Upstox's own
    identifier (e.g. "NSE_EQ|INE002A01018") — kept as the primary lookup
    key everywhere else in the schema so a broker-agnostic instrument_id
    still traces back to exactly what a broker adapter needs, without the
    rest of the app needing to know the broker's key format."""

    __tablename__ = "instruments"

    instrument_key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    exchange: Mapped[str] = mapped_column(String(20), nullable=False)  # NSE, BSE, MCX
    segment: Mapped[str] = mapped_column(String(20), nullable=False)  # NSE_EQ, NSE_FO, MCX_FO, ...
    instrument_type: Mapped[str] = mapped_column(String(20), nullable=False)  # EQUITY, FUTURES, OPTIONS, INDEX
    trading_symbol: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    lot_size: Mapped[int] = mapped_column(default=1, nullable=False)
    tick_size: Mapped[float] = mapped_column(Numeric(10, 4), default=0.05, nullable=False)

    # F&O only — null for equity/index
    expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    strike_price: Mapped[float | None] = mapped_column(Numeric(18, 4), nullable=True)
    option_type: Mapped[str | None] = mapped_column(String(2), nullable=True)  # CE, PE

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Instrument {self.trading_symbol} ({self.instrument_key})>"
