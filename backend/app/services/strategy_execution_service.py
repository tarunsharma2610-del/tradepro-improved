"""
One call = one strategy evaluated once. The worker loop (app/worker.py)
calls this for every active strategy on each tick; the API also exposes
it as a manual "evaluate now" endpoint for testing without waiting for
the scheduler.

Deliberately does NOT duplicate ExecutionService's fill logic — entries
and exits both go through ExecutionService.place_order with
execution_reason="STRATEGY", so a strategy's trades get the exact same
cost engine, position accounting, and cash accounting a manual trade
would. See ARCHITECTURE.md, "The shared order/position/execution model."
"""

import asyncio
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.brokers.registry import get_broker_adapter
from app.core.config import settings
from app.models.strategy import Strategy
from app.repositories.portfolio_repository import PortfolioRepository
from app.repositories.position_repository import PositionRepository
from app.services import risk_engine
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.candle_parsing import parse_candles
from app.services.execution_service import ExecutionService
from app.services.execution_service import PlaceOrderRequest as ServicePlaceOrderRequest
from app.services.indicators import Candle
from app.services.notification_service import NotificationService
from app.services.position_math import check_trailing_stop
from app.services.strategy_engine import IndicatorWeights, Signal, compute_score, decide
from app.services.transaction_costs import Segment, Side

_CANDLE_UNIT = "minutes"
_CANDLE_INTERVAL = "5"
_CANDLE_LOOKBACK_DAYS = 10  # calendar days — comfortably covers the ~35-period longest indicator lookback
_MAX_CANDLE_AGE = timedelta(minutes=15)  # fail closed when the newest 5-minute candle is stale


@dataclass
class EvaluationResult:
    strategy_id: str
    signal: str
    reason: str
    order_id: str | None = None


class StrategyExecutionService:
    def __init__(self, db: Session, *, scanner=None):
        self.db = db
        # Worker evaluations share the in-process scanner fed by validated Redis snapshots.
        # API/manual evaluations may omit it; candle-based indicator evaluation remains unchanged.
        self.scanner = scanner
        self.portfolios = PortfolioRepository(db)
        self.positions = PositionRepository(db)
        self.broker_credentials = BrokerCredentialsService(db)
        self.execution = ExecutionService(db)
        self.notifications = NotificationService(db)

    async def evaluate(self, strategy: Strategy) -> EvaluationResult:
        # The API exposes an immediate-evaluation endpoint as well as the worker.
        # Enforce activation here so manual calls cannot bypass the worker's active check.
        if not strategy.is_active:
            return EvaluationResult(str(strategy.id), Signal.HOLD.value, "Strategy is inactive; activate it before evaluation.")

        portfolio = self.portfolios.get_by_id(strategy.portfolio_id)
        if portfolio is None:
            return EvaluationResult(str(strategy.id), Signal.HOLD.value, "Portfolio no longer exists.")

        access_token = self.broker_credentials.get_analytics_token(portfolio.user_id, "upstox")
        if access_token is None:
            return EvaluationResult(str(strategy.id), Signal.HOLD.value, "No valid Upstox broker Analytics Token is configured in Settings.")

        candles = await self._fetch_candles(access_token, strategy.instrument.instrument_key)
        if candles is None:
            return EvaluationResult(str(strategy.id), Signal.HOLD.value, "Could not fetch candle data.")
        if not self._latest_candle_is_fresh(candles):
            return EvaluationResult(
                str(strategy.id), Signal.HOLD.value,
                "Latest candle is missing, stale, or has an invalid timestamp; automated evaluation failed closed."
            )

        position = self.positions.get_or_create(portfolio.id, strategy.instrument_id)
        in_position = position.quantity != 0

        weights = IndicatorWeights(
            rsi=Decimal(str(strategy.rsi_weight)),
            sma_crossover=Decimal(str(strategy.sma_crossover_weight)),
            macd=Decimal(str(strategy.macd_weight)),
            volume_spike=Decimal(str(strategy.volume_spike_weight)),
            momentum=Decimal(str(strategy.momentum_weight)),
        )
        score = compute_score(candles, weights)
        signal = decide(
            score,
            in_position=in_position,
            entry_threshold=Decimal(str(strategy.entry_score_threshold)),
            exit_threshold=Decimal(str(strategy.exit_score_threshold)),
        )

        strategy.last_evaluated_at = datetime.now(timezone.utc)

        # Trailing stop overrides a HOLD while in position — it's checked
        # independent of the score, using the latest candle's close as the
        # current price (avoids a second network round-trip for an LTP
        # that a 5-minute-old candle already approximates closely enough
        # for a stop check).
        observation = (
            self.scanner.latest(portfolio.user_id, strategy.instrument.instrument_key)
            if self.scanner is not None else None
        )
        current_price = Decimal(str(observation.ltp)) if observation is not None else candles[-1].close
        if in_position and signal == Signal.HOLD and observation is not None:
            # A worker-managed trailing stop requires a fresh, user/instrument-scoped
            # scanner observation. Never substitute an old candle close when the
            # live observation is unavailable; indicator-driven exits remain intact.
            stop_result = self._check_trailing_stop(strategy, position.quantity, current_price)
            if stop_result is not None:
                signal = Signal.EXIT

        if signal == Signal.ENTER_LONG:
            return await self._enter(strategy, portfolio, current_price, score.composite_score)
        if signal == Signal.EXIT:
            return await self._exit(strategy, portfolio, position.quantity, score.composite_score)

        self.db.add(strategy)
        self.db.commit()
        return EvaluationResult(str(strategy.id), Signal.HOLD.value, f"Score {score.composite_score} did not cross a threshold.")

    async def _enter(self, strategy: Strategy, portfolio, current_price: Decimal, composite_score: Decimal | None) -> EvaluationResult:
        # Kill switch blocks new automated entries only; exits remain available to reduce risk.
        if not settings.AUTOMATED_ENTRIES_ENABLED:
            self.db.add(strategy)
            self.db.commit()
            return EvaluationResult(
                str(strategy.id), Signal.HOLD.value,
                "Automated entries are disabled by the emergency kill switch."
            )

        risk_result = risk_engine.check_can_enter(self.db, strategy)
        if not risk_result.allowed:
            self.db.add(strategy)
            self.db.commit()
            return EvaluationResult(str(strategy.id), Signal.HOLD.value, f"Blocked by risk engine: {risk_result.reason}")

        order = await self.execution.place_order(
            portfolio.user_id,
            ServicePlaceOrderRequest(
                portfolio_id=portfolio.id,
                instrument_id=strategy.instrument_id,
                side=Side.BUY,
                order_type="MARKET",
                segment=Segment(strategy.segment),
                quantity=strategy.quantity,
                execution_reason="STRATEGY",
                strategy_id=strategy.id,
            ),
        )

        if order.status == "FILLED":
            strategy.current_watermark = order.limit_price or current_price  # entry price starts the trailing-stop watermark
        self.db.add(strategy)
        self.db.commit()

        if order.status == "FILLED":
            await self.notifications.notify_user(
                portfolio.user_id,
                f"[{strategy.name}] Entered {strategy.quantity} {strategy.instrument.trading_symbol} "
                f"@ ~₹{current_price} (score {composite_score}).",
            )

        reason = f"Entered: score {composite_score}." if order.status == "FILLED" else f"Entry order {order.status}: {order.rejection_reason}"
        return EvaluationResult(str(strategy.id), Signal.ENTER_LONG.value, reason, order_id=str(order.id))

    async def _exit(self, strategy: Strategy, portfolio, position_quantity: int, composite_score: Decimal | None) -> EvaluationResult:
        order = await self.execution.place_order(
            portfolio.user_id,
            ServicePlaceOrderRequest(
                portfolio_id=portfolio.id,
                instrument_id=strategy.instrument_id,
                side=Side.SELL if position_quantity > 0 else Side.BUY,
                order_type="MARKET",
                segment=Segment(strategy.segment),
                quantity=abs(position_quantity),
                execution_reason="STRATEGY",
                strategy_id=strategy.id,
            ),
        )

        just_paused = False
        if order.status == "FILLED":
            strategy.current_watermark = None
            just_paused = risk_engine.pause_if_daily_loss_exceeded(self.db, strategy)
        self.db.add(strategy)
        self.db.commit()

        if order.status == "FILLED":
            pnl_note = f" Paused for today — daily loss limit reached." if just_paused else ""
            await self.notifications.notify_user(
                portfolio.user_id,
                f"[{strategy.name}] Exited {abs(position_quantity)} {strategy.instrument.trading_symbol} "
                f"(score {composite_score}).{pnl_note}",
            )

        reason = f"Exited: score {composite_score}." if order.status == "FILLED" else f"Exit order {order.status}: {order.rejection_reason}"
        return EvaluationResult(str(strategy.id), Signal.EXIT.value, reason, order_id=str(order.id))

    def _check_trailing_stop(self, strategy: Strategy, position_quantity: int, current_price: Decimal) -> bool | None:
        """Returns True if the stop was hit (caller treats this as EXIT),
        otherwise updates the watermark in place and returns None. Thin
        wrapper over the shared pure check_trailing_stop — see
        position_math.py, reused unchanged by the backtest engine too."""
        watermark = Decimal(str(strategy.current_watermark)) if strategy.current_watermark is not None else None
        stop_pct = Decimal(str(strategy.trailing_stop_pct))

        new_watermark, hit = check_trailing_stop(
            watermark=watermark, position_quantity=position_quantity, current_price=current_price, stop_pct=stop_pct
        )
        strategy.current_watermark = new_watermark
        return True if hit else None

    @staticmethod
    def _latest_candle_is_fresh(candles: list[Candle], *, now: datetime | None = None) -> bool:
        if not candles:
            return False
        timestamp = candles[-1].timestamp
        if timestamp is None:
            return False
        # Upstox normally returns offset-aware exchange timestamps. For a
        # naive timestamp, interpret it as Indian exchange time, never UTC.
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
        current_time = now or datetime.now(timezone.utc)
        age = current_time - timestamp.astimezone(timezone.utc)
        return timedelta(seconds=-60) <= age <= _MAX_CANDLE_AGE

    async def _fetch_candles(self, access_token: str, instrument_key: str) -> list[Candle] | None:
        # Use exchange-local dates. Upstox has a dedicated current-session
        # endpoint; historical data alone is not the source of truth for today's
        # live candles. Fetch both supported endpoints concurrently and merge by
        # timestamp, preferring the intraday response on overlap.
        today_ist = datetime.now(ZoneInfo("Asia/Kolkata")).date()
        from_date = today_ist - timedelta(days=_CANDLE_LOOKBACK_DAYS)
        adapter = get_broker_adapter("upstox")
        historical_result, intraday_result = await asyncio.gather(
            adapter.get_historical_data(
                access_token, instrument_key, _CANDLE_UNIT, _CANDLE_INTERVAL, from_date, today_ist
            ),
            adapter.get_intraday_data(
                access_token, instrument_key, _CANDLE_UNIT, _CANDLE_INTERVAL
            ),
        )
        if not historical_result.ok or not intraday_result.ok:
            return None

        historical = parse_candles(historical_result.data)
        intraday = parse_candles(intraday_result.data)
        if historical is None or intraday is None:
            return None

        merged: dict[datetime, Candle] = {}
        for candle in historical:
            timestamp = candle.timestamp
            if timestamp is None:
                return None
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            merged[timestamp.astimezone(timezone.utc)] = candle
        for candle in intraday:
            timestamp = candle.timestamp
            if timestamp is None:
                return None
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            merged[timestamp.astimezone(timezone.utc)] = candle

        def sort_key(candle: Candle) -> datetime:
            timestamp = candle.timestamp
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            return timestamp.astimezone(timezone.utc)

        return sorted(merged.values(), key=sort_key)
