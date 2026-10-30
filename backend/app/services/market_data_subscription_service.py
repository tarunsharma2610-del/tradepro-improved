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
        # Replacing one feed mode must not deactivate instruments assigned to
        # another mode; mixed-mode streams maintain independent desired sets.
        for row in existing:
            if row.feed_mode == feed_mode:
                row.is_active = False

        existing_by_identity = {
            (row.instrument_id, row.feed_mode): row for row in existing
        }
        for instrument_id in desired_ids:
            row = existing_by_identity.get((instrument_id, feed_mode))
            if row is None:
                self.db.add(MarketDataSubscription(
                    user_id=user_id,
                    broker_connection_id=connection.id,
                    instrument_id=instrument_id,
                    feed_mode=feed_mode,
                    is_active=True,
                ))
            else:
                row.is_active = True

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

    def replace_modes_for_user(
        self,
        *,
        user_id: UUID,
        broker: str,
        subscriptions_by_mode: dict[str, list[str]],
    ) -> dict[str, list[MarketDataSubscription]]:
        """Atomically persist the complete desired instrument set for each mode."""
        allowed = {"ltpc", "option_greeks", "full"}
        if set(subscriptions_by_mode) - allowed:
            raise ValueError("Unsupported market-data feed mode.")
        connection = (
            self.db.query(BrokerConnection)
            .filter(BrokerConnection.user_id == user_id, BrokerConnection.broker == broker)
            .one_or_none()
        )
        if connection is None:
            raise ValueError("Broker connection is not configured for this user.")

        all_keys = {key for keys in subscriptions_by_mode.values() for key in keys}
        instruments = (
            self.db.query(Instrument)
            .filter(Instrument.is_active.is_(True), Instrument.instrument_key.in_(all_keys))
            .all()
        ) if all_keys else []
        by_key = {item.instrument_key: item for item in instruments}
        missing = sorted(all_keys - set(by_key))
        if missing:
            raise ValueError(f"Unknown or inactive instrument keys: {', '.join(missing[:10])}")
        identities = {
            (mode, by_key[key].id)
            for mode, keys in subscriptions_by_mode.items()
            for key in keys
        }
        existing = (
            self.db.query(MarketDataSubscription)
            .filter(
                MarketDataSubscription.user_id == user_id,
                MarketDataSubscription.broker_connection_id == connection.id,
            )
            .all()
        )
        existing_by_identity = {(row.feed_mode, row.instrument_id): row for row in existing}
        try:
            for row in existing:
                if row.feed_mode in allowed:
                    row.is_active = (row.feed_mode, row.instrument_id) in identities
            for mode, instrument_id in identities:
                row = existing_by_identity.get((mode, instrument_id))
                if row is None:
                    self.db.add(MarketDataSubscription(
                        user_id=user_id,
                        broker_connection_id=connection.id,
                        instrument_id=instrument_id,
                        feed_mode=mode,
                        is_active=True,
                    ))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return {
            mode: self.list_active_for_mode(user_id=user_id, broker=broker, feed_mode=mode)
            for mode in allowed
        }

    def list_active_for_mode(
        self, *, user_id: UUID, broker: str, feed_mode: str
    ) -> list[MarketDataSubscription]:
        connection = (
            self.db.query(BrokerConnection)
            .filter(BrokerConnection.user_id == user_id, BrokerConnection.broker == broker)
            .one_or_none()
        )
        if connection is None:
            return []
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

    def deactivate_mode_for_user(
        self, *, user_id: UUID, broker: str, feed_mode: str
    ) -> int:
        """Deactivate only one feed mode; preserve other desired mode sets."""
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
            return 0
        try:
            count = (
                self.db.query(MarketDataSubscription)
                .filter(
                    MarketDataSubscription.user_id == user_id,
                    MarketDataSubscription.broker_connection_id == connection.id,
                    MarketDataSubscription.feed_mode == feed_mode,
                    MarketDataSubscription.is_active.is_(True),
                )
                .update(
                    {MarketDataSubscription.is_active: False},
                    synchronize_session=False,
                )
            )
            self.db.commit()
            return count
        except Exception:
            self.db.rollback()
            raise

    def list_active(self, *, user_id: UUID) -> list[MarketDataSubscription]:
        return (
            self.db.query(MarketDataSubscription)
            .filter(
                MarketDataSubscription.user_id == user_id,
                MarketDataSubscription.is_active.is_(True),
            )
            .all()
        )
