"""Normalized source-row membership for canonical broker-charge snapshots."""
import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class BrokerChargeCanonicalSourceLink(BaseModel):
    """One explicit edge from a canonical total to one verified source row."""

    __tablename__ = "broker_charge_canonical_source_links"
    __table_args__ = (
        UniqueConstraint(
            "canonical_component_id", "source_component_id",
            name="uq_charge_canonical_source_link_pair",
        ),
        UniqueConstraint(
            "canonical_component_id", "source_ordinal",
            name="uq_charge_canonical_source_link_ordinal",
        ),
        UniqueConstraint("source_component_id", name="uq_charge_canonical_source_link_source"),
        CheckConstraint("source_ordinal >= 0", name="ck_charge_canonical_source_link_ordinal_nonnegative"),
    )

    canonical_component_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("broker_charge_canonical_components.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_component_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("broker_charge_source_components.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    source_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
