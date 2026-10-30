from uuid import UUID

from sqlalchemy.orm import Session

from app.models.broker_connection import BrokerConnection
from app.models.instrument import Instrument
from app.models.market_data_subscription import MarketDataSubscription


class MarketDataSubscriptionService:
    """Persist and reconcile desired subscriptions without starting broker I/O."""

    def __init__(self, db: Session):
        self.db = db

    def replace_for_user(
        self,
        *,
        user_id: UUID,
        broker: str,
        instrument_keys: list[str],
        feed_mode: str,
    ) -> list[MarketDataSubscription]:
        if feed_mode not in {"ltpc", "option_greeks", "full"}:
            raise ValueError("Unsupported market-data feed mode.")

        connection = (
            self.db.query(BrokerConnection)
            .filter(
                BrokerConnection.user_id == user_id,
                BrokerConnection.broker == broker,
            )
            .one_or_none()
        )
        if connection is None:
            raise ValueError("Broker connection is not configured for this user.")

        instruments = (
            self.db.query(Instrument)
            .filter(
                Instrument.is_active.is_(True),
                Instrument.instrument_key.in_(set(instrument_keys)),
            )
            .all()
        )
        by_key = {item.instrument_key: item for item in instruments}
        missing = sorted(set(instrument_keys) - set(by_key))
        if missing:
            raise ValueError(f"Unknown or inactive instrument keys: {', '.join(missing[:10])}")

        existing = (
            self.db.query(MarketDataSubscription)
            .filter(
                MarketDataSubscription.user_id == user_id,
                MarketDataSubscription.broker_connection_id == connection.id,
            )
            .all()
        )
        desired_ids = {by_key[key].id for key in instrument_keys}
        for row in existing:
            row.is_active = row.instrument_id in desired_ids

        existing_ids = {row.instrument_id for row in existing}
        for instrument_id in desired_ids - existing_ids:
            self.db.add(MarketDataSubscription(
                user_id=user_id,
                broker_connection_id=connection.id,
                instrument_id=instrument_id,
                feed_mode=feed_mode,
                is_active=True,
            ))

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return (
            self.db.query(MarketDataSubscription)
            .filter(
                MarketDataSubscription.user_id == user_id,
                MarketDataSubscription.broker_connection_id == connection.id,
                MarketDataSubscription.feed_mode == feed_mode,
                MarketDataSubscription.is_active.is_(True),
            )
            .all()
        )

    def deactivate_for_user(self, *, user_id: UUID, broker: str) -> int:
        connection = (
            self.db.query(BrokerConnection)
            .filter(
                BrokerConnection.user_id == user_id,
                BrokerConnection.broker == broker,
            )
            .one_or_none()
        )
        if connection is None:
            return 0
        count = (
            self.db.query(MarketDataSubscription)
            .filter(
                MarketDataSubscription.user_id == user_id,
                MarketDataSubscription.broker_connection_id == connection.id,
                MarketDataSubscription.is_active.is_(True),
            )
            .update({MarketDataSubscription.is_active: False}, synchronize_session=False)
        )
        self.db.commit()
        return count

    def list_active(self, *, user_id: UUID) -> list[MarketDataSubscription]:
        return (
            self.db.query(MarketDataSubscription)
            .filter(
                MarketDataSubscription.user_id == user_id,
                MarketDataSubscription.is_active.is_(True),
            )
            .all()
        )
