"""Idempotent intake of broker-confirmed trade rows.

This service intentionally stages normalized broker trades separately from
accounted Executions. It never updates paper balances, positions, order status,
or live accounting. A later reconciliation stage must explicitly promote these
records only after charge handling and live accounting rules are verified.
"""
from dataclasses import dataclass
import hmac
from decimal import Decimal, InvalidOperation
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.brokers.base import BrokerAdapter, BrokerCallResult
from app.brokers.registry import get_broker_adapter
from app.brokers.upstox.response_parsing import BrokerTrade, parse_order_trades
from app.models.broker_connection import BrokerConnection
from app.models.broker_order import BrokerOrder
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.repositories.broker_connection_repository import BrokerConnectionRepository
from app.services.broker_credentials_service import BrokerCredentialsService


@dataclass(frozen=True)
class BrokerTradeIngestionResult:
    order_id: str
    broker_order_id: str
    inserted_count: int
    duplicate_count: int


class BrokerTradeIngestionService:
    """Validate ownership/order mapping, then persist each broker trade once."""

    def __init__(self, db: Session, adapter: BrokerAdapter | Any | None = None):
        self.db = db
        self.adapter = adapter
        self.connections = BrokerConnectionRepository(db)
        self.credentials = BrokerCredentialsService(db)

    async def fetch_and_ingest(
        self,
        user_id: UUID,
        local_order_id: UUID,
        broker_order_id: str,
    ) -> BrokerTradeIngestionResult:
        """Read trades from Upstox, validate identity, then stage them idempotently.

        This method never calls a broker order-write endpoint and never changes
        local order state or accounting. Credentials and connection identity are
        checked again after the async broker request to reject rotation races.
        """
        if not isinstance(broker_order_id, str) or not broker_order_id.strip():
            raise ValueError("A broker order ID is required.")
        broker_order_id = broker_order_id.strip()

        row = (
            self.db.query(Order, Portfolio.user_id)
            .join(Portfolio, Portfolio.id == Order.portfolio_id)
            .filter(Order.id == local_order_id, Portfolio.user_id == user_id)
            .first()
        )
        if row is None:
            raise ValueError("Order not found.")
        order, _owner_id = row
        if order.trading_mode != "LIVE":
            raise ValueError("Broker trades can only be fetched for LIVE orders.")

        child = (
            self.db.query(BrokerOrder)
            .filter(
                BrokerOrder.order_id == order.id,
                BrokerOrder.broker_order_id == broker_order_id,
            )
            .first()
        )
        if child is None:
            raise ValueError("Broker order ID is not mapped to this local order.")
        if child.broker_connection_id is None:
            raise ValueError("Broker child order is not bound to a broker connection.")

        connection = self.connections.get_for_user(user_id, child.broker_name)
        if (
            connection is None
            or not connection.is_connected
            or connection.id != child.broker_connection_id
        ):
            raise ValueError("Broker child order is not bound to this user's verified broker connection.")
        try:
            token = self.credentials.get_access_token(user_id, child.broker_name)
        except Exception as exc:
            raise ValueError("Broker access token could not be validated.") from exc
        if not isinstance(token, str) or not token.strip():
            raise ValueError("No usable broker access token; trade fetch blocked.")

        adapter = self.adapter or get_broker_adapter(child.broker_name)
        try:
            response = await adapter.get_order_trades(token, broker_order_id)
        except Exception as exc:
            raise ValueError("Broker trade lookup failed; no trades were ingested.") from exc
        if not isinstance(response, BrokerCallResult) or not response.ok:
            detail = response.error if isinstance(response, BrokerCallResult) else "invalid adapter result"
            raise ValueError(f"Broker trade lookup failed; no trades were ingested: {detail or 'unknown error'}.")

        try:
            trades = parse_order_trades(response.data, broker_order_id)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Broker trade response failed validation: {exc}") from exc

        # Async network I/O creates a race window: reload connection/token and
        # refuse to persist data fetched under credentials that have changed.
        try:
            self.db.refresh(connection)
            current_token = self.credentials.get_access_token(user_id, child.broker_name)
        except Exception as exc:
            raise ValueError("Broker connection could not be revalidated after trade lookup.") from exc
        if (
            not connection.is_connected
            or connection.id != child.broker_connection_id
            or not isinstance(current_token, str)
            or not hmac.compare_digest(current_token, token)
        ):
            raise ValueError("Broker connection or token changed during trade lookup; ingestion blocked.")

        return self.ingest_trades(user_id, local_order_id, broker_order_id, trades)

    def ingest_trades(
        self,
        user_id: UUID,
        local_order_id: UUID,
        broker_order_id: str,
        trades: Sequence[BrokerTrade],
    ) -> BrokerTradeIngestionResult:
        if not isinstance(broker_order_id, str) or not broker_order_id.strip():
            raise ValueError("A broker order ID is required.")
        broker_order_id = broker_order_id.strip()

        try:
            row = (
                self.db.query(Order, Portfolio.user_id)
                .join(Portfolio, Portfolio.id == Order.portfolio_id)
                .filter(Order.id == local_order_id, Portfolio.user_id == user_id)
                .with_for_update()
                .first()
            )
            if row is None:
                raise ValueError("Order not found.")
            order, owner_id = row
            if owner_id != user_id:
                raise ValueError("Order not found.")
            if order.trading_mode != "LIVE":
                raise ValueError("Broker trades can only be ingested for LIVE orders.")

            broker_order = (
                self.db.query(BrokerOrder)
                .filter(
                    BrokerOrder.order_id == order.id,
                    BrokerOrder.broker_order_id == broker_order_id,
                )
                .with_for_update()
                .first()
            )
            if broker_order is None:
                raise ValueError("Broker order ID is not mapped to this local order.")

            if broker_order.broker_connection_id is None:
                raise ValueError("Broker child order is not bound to a broker connection.")
            connection = (
                self.db.query(BrokerConnection)
                .filter(
                    BrokerConnection.id == broker_order.broker_connection_id,
                    BrokerConnection.user_id == user_id,
                    BrokerConnection.broker == broker_order.broker_name,
                )
                .first()
            )
            if connection is None:
                raise ValueError("Broker child order is not bound to this user’s broker connection.")

            instrument = self.db.get(Instrument, order.instrument_id)
            if instrument is None:
                raise ValueError("The order's instrument no longer exists.")

            normalized: list[tuple[BrokerTrade, str, Decimal]] = []
            seen: set[str] = set()
            for trade in trades:
                if not isinstance(trade, BrokerTrade):
                    raise ValueError("Every trade must be a validated BrokerTrade value.")
                if trade.order_id != broker_order_id:
                    raise ValueError("Trade order_id does not match the mapped broker order.")
                if not isinstance(trade.trade_id, str) or not trade.trade_id.strip():
                    raise ValueError("Trade ID must be a non-empty string.")
                trade_id = trade.trade_id.strip()
                if trade_id in seen:
                    raise ValueError("Input contains duplicate trade IDs.")
                seen.add(trade_id)

                if type(trade.quantity) is not int or trade.quantity <= 0:
                    raise ValueError("Trade quantity must be a positive integer.")
                try:
                    price = Decimal(str(trade.price))
                except (InvalidOperation, TypeError, ValueError):
                    raise ValueError("Trade price must be a valid positive amount.") from None
                if not price.is_finite() or price <= 0:
                    raise ValueError("Trade price must be a valid positive amount.")

                if not isinstance(trade.side, str) or not trade.side.strip():
                    raise ValueError("Trade side must be BUY or SELL.")
                side = trade.side.strip().upper()
                if side not in {"BUY", "SELL"} or side != order.side:
                    raise ValueError("Trade side does not match the local order side.")
                token = trade.instrument_token
                if not isinstance(token, str) or not token.strip():
                    raise ValueError("Trade instrument token is required for safe live reconciliation.")
                if token.strip() != instrument.instrument_key:
                    raise ValueError("Trade instrument token does not match the local order instrument.")
                if trade.exchange_timestamp is not None and (
                    not isinstance(trade.exchange_timestamp, str) or not trade.exchange_timestamp.strip()
                ):
                    raise ValueError("Trade exchange timestamp must be non-empty text when supplied.")
                normalized.append((trade, trade_id, price))

            if not normalized:
                return BrokerTradeIngestionResult(str(order.id), broker_order_id, 0, 0)

            existing_rows = (
                self.db.query(BrokerTradeRecord)
                .filter(
                    BrokerTradeRecord.broker_connection_id == connection.id,
                    BrokerTradeRecord.broker_trade_id.in_([trade_id for _, trade_id, _ in normalized]),
                )
                .all()
            )
            existing_by_id = {record.broker_trade_id: record for record in existing_rows}

            already_ingested_quantity = (
                self.db.query(BrokerTradeRecord.quantity)
                .join(BrokerOrder, BrokerOrder.id == BrokerTradeRecord.broker_order_ref_id)
                .filter(
                    BrokerOrder.order_id == order.id,
                    BrokerTradeRecord.broker_connection_id == connection.id,
                )
                .all()
            )
            cumulative_quantity = sum(int(quantity) for (quantity,) in already_ingested_quantity)
            inserted_count = 0
            duplicate_count = 0

            for trade, trade_id, price in normalized:
                existing = existing_by_id.get(trade_id)
                if existing is not None:
                    if not self._same_trade(existing, broker_order, trade, price):
                        raise ValueError(
                            "Trade ID already exists for this broker connection with conflicting order or trade data."
                        )
                    duplicate_count += 1
                    continue

                if cumulative_quantity + trade.quantity > order.quantity:
                    raise ValueError("Ingested trade quantity would exceed the local order quantity.")

                record = BrokerTradeRecord(
                    broker_connection_id=connection.id,
                    broker_order_ref_id=broker_order.id,
                    broker_trade_id=trade_id,
                    quantity=trade.quantity,
                    price=price,
                    side=trade.side.strip().upper(),
                    instrument_token=trade.instrument_token,
                    exchange_timestamp=trade.exchange_timestamp,
                )
                try:
                    # Savepoint lets a concurrent replay race safely against
                    # the unique constraint without aborting the outer batch.
                    with self.db.begin_nested():
                        self.db.add(record)
                        self.db.flush()
                    inserted_count += 1
                    cumulative_quantity += trade.quantity
                    existing_by_id[trade_id] = record
                except IntegrityError:
                    concurrent = (
                        self.db.query(BrokerTradeRecord)
                        .filter(
                            BrokerTradeRecord.broker_connection_id == connection.id,
                            BrokerTradeRecord.broker_trade_id == trade_id,
                        )
                        .first()
                    )
                    if concurrent is None or not self._same_trade(concurrent, broker_order, trade, price):
                        raise ValueError(
                            "Trade identity conflicted with an existing record during concurrent ingestion."
                        ) from None
                    duplicate_count += 1

            self.db.commit()
            return BrokerTradeIngestionResult(
                str(order.id), broker_order_id, inserted_count, duplicate_count
            )
        except Exception:
            self.db.rollback()
            raise

    @staticmethod
    def _same_trade(
        existing: BrokerTradeRecord,
        broker_order: BrokerOrder,
        trade: BrokerTrade,
        price: Decimal,
    ) -> bool:
        return (
            existing.broker_order_ref_id == broker_order.id
            and existing.quantity == trade.quantity
            and Decimal(str(existing.price)) == price
            and existing.side == trade.side.strip().upper()
            and existing.instrument_token == trade.instrument_token
            and existing.exchange_timestamp == trade.exchange_timestamp
        )
