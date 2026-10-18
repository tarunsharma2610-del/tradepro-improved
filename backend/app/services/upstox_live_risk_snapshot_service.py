"""Read-only Upstox snapshot collector for the live risk-gate foundation.

This service only calls quote, positions, funds, margin-estimate and market
calendar endpoints. It has no order-placement method and never submits orders.
The resulting synchronous provider bundle is intended for the preflight gate;
callers must still keep submission routes/workers unwired until separately
reviewed.
"""
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.brokers.base import BrokerAdapter, BrokerCallResult
from app.brokers.upstox.risk_snapshot_parsing import (
    ExchangeTiming,
    FullMarketQuote,
    MarketHoliday,
    OpenBrokerPosition,
    parse_full_market_quote,
    parse_market_holidays,
    parse_market_timings,
    parse_open_positions,
)
from app.models.instrument import Instrument
from app.models.order import Order
from app.models.portfolio import Portfolio
from app.services.live_execution_service import LiveOrderIntent
from app.services.live_pre_trade_risk_gate import (
    BrokerFundsSnapshot,
    BrokerMarginSnapshot,
    BrokerPositionSnapshot,
    LiveQuoteSnapshot,
    MarketSessionSnapshot,
)
from app.brokers.upstox.response_parsing import parse_funds_and_margin_v3, parse_margin_details

IST = ZoneInfo("Asia/Kolkata")


@dataclass(frozen=True)
class UpstoxLiveRiskSnapshots:
    quote_snapshots: dict[str, LiveQuoteSnapshot]
    positions: tuple[BrokerPositionSnapshot, ...]
    funds: BrokerFundsSnapshot
    margin: BrokerMarginSnapshot
    session: MarketSessionSnapshot

    def quote_provider(self, _user_id: UUID, instrument: Instrument) -> LiveQuoteSnapshot:
        try:
            return self.quote_snapshots[instrument.instrument_key]
        except KeyError:
            raise ValueError("No fresh Upstox quote was collected for this instrument.") from None

    def positions_provider(self, _user_id: UUID) -> tuple[BrokerPositionSnapshot, ...]:
        return self.positions

    def funds_provider(self, _user_id: UUID) -> BrokerFundsSnapshot:
        return self.funds

    def margin_provider(
        self, _user_id: UUID, _instrument: Instrument, _intent: LiveOrderIntent, _value: Decimal
    ) -> BrokerMarginSnapshot:
        return self.margin

    def session_provider(self, _now: datetime) -> MarketSessionSnapshot:
        return self.session


class UpstoxLiveRiskSnapshotService:
    """Collect and validate the broker snapshots required by the live risk gate."""

    BROKER_NAME = "upstox"
    MAX_QUOTE_KEYS = 500

    def __init__(self, db: Session, adapter: BrokerAdapter, access_token: str):
        if not isinstance(access_token, str) or not access_token.strip():
            raise ValueError("A usable Upstox access token is required.")
        self.db = db
        self.adapter = adapter
        self.access_token = access_token

    async def collect(
        self,
        user_id: UUID,
        instrument: Instrument,
        intent: LiveOrderIntent,
        *,
        now: datetime | None = None,
    ) -> UpstoxLiveRiskSnapshots:
        collected_at = now or datetime.now(timezone.utc)
        if collected_at.tzinfo is None or collected_at.utcoffset() is None:
            raise ValueError("Snapshot collection time must be timezone-aware.")

        portfolio_ids = [
            row[0] for row in self.db.query(Portfolio.id).filter(Portfolio.user_id == user_id).all()
        ]
        pending_instruments = (
            self.db.query(Instrument)
            .join(Order, Order.instrument_id == Instrument.id)
            .filter(
                Order.portfolio_id.in_(portfolio_ids),
                Order.trading_mode == "LIVE",
                Order.status.in_(
                    ("PENDING_SUBMISSION", "SUBMITTING", "SUBMISSION_UNKNOWN", "PENDING", "PARTIALLY_FILLED")
                ),
            )
            .all()
            if portfolio_ids else []
        )

        holidays_result = await self.adapter.get_market_holidays(self.access_token)
        holidays = parse_market_holidays(self._required_result(holidays_result, "market holidays"))

        market_date = collected_at.astimezone(IST).date()
        session = await self._market_session(market_date, collected_at, holidays)

        positions_result = await self.adapter.get_positions(self.access_token)
        broker_positions = parse_open_positions(self._required_result(positions_result, "positions"))

        quote_keys = {instrument.instrument_key}
        quote_keys.update(item.instrument_key for item in broker_positions)
        quote_keys.update(item.instrument_key for item in pending_instruments)
        if len(quote_keys) > self.MAX_QUOTE_KEYS:
            raise ValueError("Risk snapshot exceeds Upstox's 500-instrument full-quote limit.")

        quote_snapshots: dict[str, LiveQuoteSnapshot] = {}
        for key in sorted(quote_keys):
            result = await self.adapter.get_full_market_quote(self.access_token, [key])
            quote = parse_full_market_quote(self._required_result(result, "full market quote"), key)
            quote_snapshots[key] = LiveQuoteSnapshot(quote.last_price, quote.observed_at)

        position_snapshots: list[BrokerPositionSnapshot] = []
        for row in broker_positions:
            quote = quote_snapshots.get(row.instrument_key)
            if quote is None:
                raise ValueError("An open broker position has no validated market quote.")
            position_snapshots.append(
                BrokerPositionSnapshot(
                    instrument_key=row.instrument_key,
                    quantity=row.quantity,
                    market_price=quote.price,
                    observed_at=quote.observed_at,
                )
            )

        funds_result = await self.adapter.get_funds_and_margin(self.access_token)
        funds_data = parse_funds_and_margin_v3(self._required_result(funds_result, "funds and margin"))
        funds = BrokerFundsSnapshot(
            cash_available=funds_data.cash_available_to_trade_total,
            observed_at=collected_at,
        )

        product = "I" if intent.segment == "EQUITY_INTRADAY" else "D"
        margin_request: dict[str, Any] = {
            "instrument_key": instrument.instrument_key,
            "quantity": intent.quantity,
            "transaction_type": intent.side,
            "product": product,
        }
        if intent.limit_price is not None:
            margin_request["price"] = float(intent.limit_price)
        margin_result = await self.adapter.get_margin_details(self.access_token, [margin_request])
        margin_data = parse_margin_details(self._required_result(margin_result, "margin estimate"))
        margin = BrokerMarginSnapshot(
            required_margin=margin_data.required_margin,
            observed_at=collected_at,
        )

        return UpstoxLiveRiskSnapshots(
            quote_snapshots=quote_snapshots,
            positions=tuple(position_snapshots),
            funds=funds,
            margin=margin,
            session=session,
        )

    async def _market_session(
        self, market_date: date, now: datetime, holidays: tuple[MarketHoliday, ...]
    ) -> MarketSessionSnapshot:
        day = next((item for item in holidays if item.market_date == market_date), None)
        now_utc = now.astimezone(timezone.utc)
        if day is not None:
            special = next((item for item in day.open_exchanges if item[0] == "NSE"), None)
            if special is not None:
                is_open = special[1] <= now_utc < special[2]
                return MarketSessionSnapshot(
                    is_open=is_open,
                    observed_at=now,
                    reason=None if is_open else "Official calendar special NSE session is currently closed.",
                )
            if "NSE" in day.closed_exchanges or day.holiday_type == "TRADING_HOLIDAY":
                return MarketSessionSnapshot(
                    is_open=False,
                    observed_at=now,
                    reason=f"Official Upstox calendar marks {market_date} as an NSE trading holiday.",
                )

        timings_result = await self.adapter.get_market_timings(self.access_token, market_date)
        timings = parse_market_timings(
            self._required_result(timings_result, "market timings"),
            market_date,
            expected_exchange="NSE",
        )
        is_open = timings.opens_at <= now_utc < timings.closes_at
        return MarketSessionSnapshot(
            is_open=is_open,
            observed_at=now,
            reason=None if is_open else "Official NSE market timings report the session is closed.",
        )

    @staticmethod
    def _required_result(result: BrokerCallResult, label: str) -> Any:
        if not isinstance(result, BrokerCallResult) or not result.ok:
            detail = result.error if isinstance(result, BrokerCallResult) else "invalid adapter result"
            raise ValueError(f"Upstox {label} lookup failed: {detail or 'unknown error'}.")
        return result.data
