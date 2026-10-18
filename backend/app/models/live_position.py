import uuid

from sqlalchemy import ForeignKey, Integer, Numeric, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class LivePosition(BaseModel):
    """App-attributed live fills, isolated from virtual paper positions.

    Live positions are keyed to a broker connection because one real broker
    account may span several logical app portfolios. Broker position snapshots
    remain the source of truth for account-wide exposure; this table tracks
    only fills ingested/accounted by this application.
    """

    __tablename__ = "live_positions"
    __table_args__ = (
        UniqueConstraint(
            "broker_connection_id",
            "instrument_id",
            name="uq_live_position_connection_instrument",
        ),
    )

    broker_connection_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("broker_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("instruments.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    instrument: Mapped["Instrument"] = relationship(lazy="joined")
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_price: Mapped[float] = mapped_column(Numeric(18, 4), default=0, nullable=False)
    realized_pnl: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)
