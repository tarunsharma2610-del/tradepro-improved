from datetime import date
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class MarketUniverseSnapshot(BaseModel):
    """Auditable, immutable membership snapshot for a market index universe."""

    __tablename__ = "market_universe_snapshots"
    __table_args__ = (
        UniqueConstraint("universe_key", "as_of_date", name="uq_market_universe_snapshot_date"),
        Index("ix_market_universe_active", "universe_key", "is_active"),
        Index("uq_market_universe_one_active", "universe_key", unique=True, postgresql_where=text("is_active = true"), sqlite_where=text("is_active = 1")),
    )

    universe_key: Mapped[str] = mapped_column(String(50), nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    member_count: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class MarketUniverseMembership(BaseModel):
    """Exact instrument membership belonging to one immutable snapshot."""

    __tablename__ = "market_universe_memberships"
    __table_args__ = (
        UniqueConstraint("snapshot_id", "instrument_id", name="uq_market_universe_member_instrument"),
        UniqueConstraint("snapshot_id", "trading_symbol", name="uq_market_universe_member_symbol"),
        Index("ix_market_universe_membership_snapshot", "snapshot_id"),
    )

    snapshot_id: Mapped[UUID] = mapped_column(
        ForeignKey("market_universe_snapshots.id", ondelete="CASCADE"), nullable=False
    )
    instrument_id: Mapped[UUID] = mapped_column(
        ForeignKey("instruments.id", ondelete="RESTRICT"), nullable=False
    )
    trading_symbol: Mapped[str] = mapped_column(String(50), nullable=False)
