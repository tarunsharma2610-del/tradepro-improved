"""Read-only, explicitly estimated charge breakdown for one staged live trade.

Upstox's brokerage endpoint calculates estimated charges from order inputs. It
does not prove final fees levied on an executed trade. This service returns an
APPROVED_ESTIMATE provenance label and never writes accounting rows.
"""
from dataclasses import dataclass
import hmac
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.brokers.base import BrokerAdapter, BrokerCallResult
from app.brokers.registry import get_broker_adapter
from app.brokers.upstox.response_parsing import parse_brokerage_details
from app.models.broker_connection import BrokerConnection
from app.models.broker_order import BrokerOrder
from app.models.broker_trade_record import BrokerTradeRecord
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.repositories.broker_connection_repository import BrokerConnectionRepository
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.live_execution_service import LiveExecutionBlocked
from app.services.live_fill_accounting_service import LiveChargeBreakdown


@dataclass(frozen=True)
class LiveChargeEstimateResult:
    broker_trade_id: str
    broker_connection_id: UUID
    instrument_token: str
    quantity: int
    price: Decimal
    breakdown: LiveChargeBreakdown
    estimated_total: Decimal
    dp_charges: Decimal


class LiveChargeEstimateService:
    """Resolve a staged trade's charge estimate using the verified user's token."""

    BROKER_NAME = "upstox"

    def __init__(self, db: Session, adapter: BrokerAdapter | None = None):
        self.db = db
        self.adapter = adapter or get_broker_adapter(self.BROKER_NAME)
        self.connections = BrokerConnectionRepository(db)
        self.credentials = BrokerCredentialsService(db)

    async def estimate_for_trade(
        self, user_id: UUID, broker_trade_record_id: UUID
    ) -> LiveChargeEstimateResult:
        record = self.db.get(BrokerTradeRecord, broker_trade_record_id)
        if record is None:
            raise LiveExecutionBlocked("Staged broker trade record was not found.")
        child = self.db.get(BrokerOrder, record.broker_order_ref_id)
        if child is None or child.broker_connection_id != record.broker_connection_id:
            raise LiveExecutionBlocked("Staged trade has an invalid broker-order mapping.")
        connection = self.connections.get_for_user(user_id, child.broker_name)
        if (
            connection is None
            or not connection.is_connected
            or connection.id != record.broker_connection_id
        ):
            raise LiveExecutionBlocked("Staged trade is not bound to this user's verified broker connection.")
        order = self.db.get(Order, child.order_id)
        if order is None or order.trading_mode != "LIVE":
            raise LiveExecutionBlocked("Charge estimates are available only for mapped LIVE orders.")
        owner_id = self.db.query(Portfolio.user_id).filter(Portfolio.id == order.portfolio_id).scalar()
        if owner_id != user_id:
            raise LiveExecutionBlocked("Live order is not owned by this user.")
        if record.side not in {"BUY", "SELL"} or record.side != order.side:
            raise LiveExecutionBlocked("Staged trade side conflicts with its parent order.")
        instrument = self.db.get(Instrument, order.instrument_id)
        if (
            instrument is None
            or record.instrument_token != instrument.instrument_key
            or record.quantity <= 0
            or Decimal(str(record.price)) <= 0
        ):
            raise LiveExecutionBlocked("Staged trade lacks valid instrument identity, quantity, or price data.")
        if order.segment not in {"EQUITY_DELIVERY", "EQUITY_INTRADAY"}:
            raise LiveExecutionBlocked("Charge estimates currently support verified equity segments only.")

        try:
            token = self.credentials.get_access_token(user_id, child.broker_name)
        except Exception as exc:
            raise LiveExecutionBlocked("Broker access token could not be validated.") from exc
        if not isinstance(token, str) or not token.strip():
            raise LiveExecutionBlocked("No usable broker access token; charge estimate blocked.")

        product = "I" if order.segment == "EQUITY_INTRADAY" else "D"
        try:
            response = await self.adapter.get_brokerage_details(
                token,
                instrument_token=record.instrument_token,
                quantity=record.quantity,
                product=product,
                transaction_type=record.side,
                price=float(record.price),
            )
        except Exception as exc:
            raise LiveExecutionBlocked("Upstox charge estimate request failed; no accounting was written.") from exc
        if not isinstance(response, BrokerCallResult) or not response.ok:
            detail = response.error if isinstance(response, BrokerCallResult) else "invalid adapter result"
            raise LiveExecutionBlocked(
                f"Upstox charge estimate failed; no accounting was written: {detail or 'unknown error'}."
            )
        try:
            parsed = parse_brokerage_details(response.data)
        except (TypeError, ValueError) as exc:
            raise LiveExecutionBlocked(
                f"Upstox charge estimate response failed validation: {exc}"
            ) from exc

        # Recheck connection and token after async I/O to prevent using a stale
        # credential/session after disconnect or credential rotation.
        try:
            self.db.refresh(connection)
            current_token = self.credentials.get_access_token(user_id, child.broker_name)
        except Exception as exc:
            raise LiveExecutionBlocked("Broker connection could not be revalidated after charge estimate.") from exc
        if (
            not connection.is_connected
            or connection.id != record.broker_connection_id
            or not isinstance(current_token, str)
            or not hmac.compare_digest(current_token, token)
        ):
            raise LiveExecutionBlocked("Broker connection or token changed during charge estimate; blocked.")

        if parsed.dp_charges > 0:
            raise LiveExecutionBlocked(
                "Upstox reports a daily per-scrip DP minimum separately from the trade estimate; "
                "it cannot safely be allocated to one fill. Use reviewed contract-note allocation."
            )

        reference = (
            f"upstox:/v2/charges/brokerage;trade={record.broker_trade_id};"
            f"product={product};qty={record.quantity};price={record.price}"
        )
        breakdown = LiveChargeBreakdown(
            brokerage=parsed.brokerage,
            stt=parsed.stt,
            exchange_charges=parsed.exchange_charges,
            sebi_charges=parsed.sebi_turnover_charges,
            stamp_duty=parsed.stamp_duty,
            gst=parsed.gst,
            dp_charges=parsed.dp_charges,
            source="APPROVED_ESTIMATE",
            reference=reference,
        )
        return LiveChargeEstimateResult(
            broker_trade_id=record.broker_trade_id,
            broker_connection_id=record.broker_connection_id,
            instrument_token=record.instrument_token,
            quantity=record.quantity,
            price=Decimal(str(record.price)),
            breakdown=breakdown,
            estimated_total=parsed.reported_estimate_total,
            dp_charges=parsed.dp_charges,
        )
