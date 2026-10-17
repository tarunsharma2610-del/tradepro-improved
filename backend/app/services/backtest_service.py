from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.brokers.registry import get_broker_adapter
from app.models.backtest import BacktestRun
from app.models.backtest_trade import BacktestTrade
from app.models.instrument import Instrument
from app.repositories.backtest_repository import BacktestRepository
from app.services.backtest_engine import BacktestConfig, run_backtest
from app.services.broker_credentials_service import BrokerCredentialsService
from app.services.strategy_engine import IndicatorWeights
from app.services.candle_parsing import parse_candles
from app.services.transaction_costs import Segment


class BacktestService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = BacktestRepository(db)
        self.broker_credentials = BrokerCredentialsService(db)

    async def run(self, user_id: UUID, run: BacktestRun, instrument: Instrument) -> BacktestRun:
        access_token = self.broker_credentials.get_access_token(user_id, "upstox")
        if access_token is None:
            return self._fail(run, "No connected broker with a live session — connect Upstox in Settings first.")

        result = await get_broker_adapter("upstox").get_historical_data(
            access_token, instrument.instrument_key, "minutes", "5", run.from_date, run.to_date
        )
        if not result.ok:
            return self._fail(run, f"Could not fetch historical data: {result.error}")

        candles = parse_candles(result.data)
        if not candles:
            return self._fail(run, "Broker response didn't contain readable candle data for this date range.")

        weights = IndicatorWeights(
            rsi=Decimal(str(run.rsi_weight)), sma_crossover=Decimal(str(run.sma_crossover_weight)),
            macd=Decimal(str(run.macd_weight)), volume_spike=Decimal(str(run.volume_spike_weight)),
            momentum=Decimal(str(run.momentum_weight)),
        )
        config = BacktestConfig(
            initial_capital=Decimal(str(run.initial_capital)), quantity=run.quantity, segment=Segment(run.segment),
            weights=weights, entry_threshold=Decimal(str(run.entry_score_threshold)),
            exit_threshold=Decimal(str(run.exit_score_threshold)), trailing_stop_pct=Decimal(str(run.trailing_stop_pct)),
            slippage_bps=Decimal(str(run.slippage_bps)),
        )

        backtest_result = run_backtest(candles, config)
        if backtest_result.error:
            return self._fail(run, backtest_result.error)

        run.status = "COMPLETED"
        run.final_capital = backtest_result.final_capital
        run.net_pnl = backtest_result.net_pnl
        run.max_drawdown_pct = backtest_result.max_drawdown_pct
        run.total_trades = len(backtest_result.closing_trades)
        run.win_count = backtest_result.win_count
        run.loss_count = backtest_result.loss_count
        run.candles_evaluated = backtest_result.candles_evaluated
        run.completed_at = datetime.now(timezone.utc)
        self.repo.save(run)

        trade_rows = [
            BacktestTrade(
                backtest_run_id=run.id, side=t.side.value, quantity=t.quantity, price=t.price,
                gross_value=t.costs.gross_value, brokerage=t.costs.brokerage, stt=t.costs.stt,
                exchange_charges=t.costs.exchange_charges, sebi_charges=t.costs.sebi_charges,
                stamp_duty=t.costs.stamp_duty, gst=t.costs.gst, total_charges=t.costs.total_charges,
                realized_pnl=t.realized_pnl, candle_index=t.candle_index, executed_at=t.timestamp,
            )
            for t in backtest_result.trades
        ]
        if trade_rows:
            self.repo.add_trades(trade_rows)

        return run

    def _fail(self, run: BacktestRun, message: str) -> BacktestRun:
        run.status = "FAILED"
        run.error_message = message
        return self.repo.save(run)
