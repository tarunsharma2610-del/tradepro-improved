"""
This is the "backtesting reuses the same execution/cost model" rule made
concrete: every calculation in the loop below is the same function
strategy_execution_service.py calls for live trading — compute_score,
decide, check_trailing_stop, calculate_costs, apply_fill. The only things
genuinely new here are the bar-by-bar walk-forward loop itself and
slippage, which live trading doesn't need (a live fill already reflects
real market friction; a backtest has to simulate it — see
_apply_slippage).

Deliberately pure: no DB, no network, no broker. backtest_service.py is
the thin layer that fetches real candles and persists what this returns.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.services.indicators import Candle
from app.services.position_math import apply_fill, check_trailing_stop
from app.services.strategy_engine import IndicatorWeights, Signal, compute_score, decide
from app.services.transaction_costs import CostBreakdown, Segment, Side, calculate_costs

MIN_LOOKBACK_CANDLES = 36  # MACD (slow=26 + signal=9) is the longest-lookback indicator, +1 buffer


@dataclass
class BacktestConfig:
    initial_capital: Decimal
    quantity: int
    segment: Segment
    weights: IndicatorWeights
    entry_threshold: Decimal
    exit_threshold: Decimal
    trailing_stop_pct: Decimal
    slippage_bps: Decimal = Decimal("5")  # 0.05% default — a modest, configurable friction assumption


@dataclass
class SimulatedTrade:
    side: Side
    quantity: int
    price: Decimal  # after slippage — what actually "filled"
    costs: CostBreakdown
    realized_pnl: Decimal
    timestamp: datetime | None
    candle_index: int


@dataclass
class BacktestResult:
    initial_capital: Decimal
    final_capital: Decimal
    trades: list[SimulatedTrade] = field(default_factory=list)
    max_drawdown_pct: Decimal = Decimal("0")
    candles_evaluated: int = 0
    error: str | None = None

    @property
    def net_pnl(self) -> Decimal:
        """Final minus initial capital — the one number that's correct by
        construction, since every cost is already reflected in cash
        through the same net_cash_impact live trading uses. Don't
        reconcile this against summed realized_pnl elsewhere; they answer
        different questions (this includes costs, realized_pnl doesn't)."""
        return self.final_capital - self.initial_capital

    @property
    def closing_trades(self) -> list[SimulatedTrade]:
        """Trades that closed some or all of a position — i.e. ones that
        can meaningfully be called a win or a loss. Entries always carry
        realized_pnl=0 and aren't 'trades' in the win/loss sense."""
        return [t for t in self.trades if t.realized_pnl != 0]

    @property
    def win_count(self) -> int:
        return sum(1 for t in self.closing_trades if t.realized_pnl > 0)

    @property
    def loss_count(self) -> int:
        return sum(1 for t in self.closing_trades if t.realized_pnl < 0)


def _apply_slippage(price: Decimal, side: Side, slippage_bps: Decimal) -> Decimal:
    """A market order in real trading rarely fills at exactly the last
    printed price — this simulates that friction. Buys fill slightly
    worse (higher), sells fill slightly worse (lower); real market impact
    always works against the trader, never for them, which is the
    conservative (non-optimistic) assumption a backtest should make."""
    fraction = slippage_bps / Decimal("10000")
    return price * (1 + fraction) if side == Side.BUY else price * (1 - fraction)


def run_backtest(candles: list[Candle], config: BacktestConfig) -> BacktestResult:
    if len(candles) < MIN_LOOKBACK_CANDLES + 1:
        return BacktestResult(
            initial_capital=config.initial_capital,
            final_capital=config.initial_capital,
            error=f"Need at least {MIN_LOOKBACK_CANDLES + 1} candles, got {len(candles)}.",
        )

    cash = config.initial_capital
    position_quantity = 0
    position_avg_price = Decimal("0")
    watermark: Decimal | None = None
    trades: list[SimulatedTrade] = []
    equity_curve: list[Decimal] = []

    for i in range(MIN_LOOKBACK_CANDLES, len(candles)):
        window = candles[: i + 1]
        candle = candles[i]
        current_price = candle.close
        in_position = position_quantity != 0

        score = compute_score(window, config.weights)
        signal = decide(
            score, in_position=in_position, entry_threshold=config.entry_threshold, exit_threshold=config.exit_threshold
        )

        if in_position and signal == Signal.HOLD:
            watermark, stop_hit = check_trailing_stop(
                watermark=watermark, position_quantity=position_quantity,
                current_price=current_price, stop_pct=config.trailing_stop_pct,
            )
            if stop_hit:
                signal = Signal.EXIT

        if signal == Signal.ENTER_LONG and not in_position:
            fill_price = _apply_slippage(current_price, Side.BUY, config.slippage_bps)
            costs = calculate_costs(config.segment, Side.BUY, config.quantity, fill_price)
            if cash + costs.net_cash_impact >= 0:
                update = apply_fill(
                    position_quantity=0, position_avg_price=Decimal("0"),
                    side=Side.BUY, fill_quantity=config.quantity, fill_price=fill_price,
                )
                position_quantity, position_avg_price = update.new_quantity, update.new_avg_price
                cash += costs.net_cash_impact
                watermark = fill_price
                trades.append(SimulatedTrade(Side.BUY, config.quantity, fill_price, costs, update.realized_pnl, candle.timestamp, i))
            # else: would-be entry skipped, insufficient simulated capital — not an error, just no trade this bar

        elif signal == Signal.EXIT and in_position:
            exit_side = Side.SELL if position_quantity > 0 else Side.BUY
            exit_qty = abs(position_quantity)
            fill_price = _apply_slippage(current_price, exit_side, config.slippage_bps)
            costs = calculate_costs(config.segment, exit_side, exit_qty, fill_price)
            update = apply_fill(
                position_quantity=position_quantity, position_avg_price=position_avg_price,
                side=exit_side, fill_quantity=exit_qty, fill_price=fill_price,
            )
            position_quantity, position_avg_price = update.new_quantity, update.new_avg_price
            cash += costs.net_cash_impact
            watermark = None
            trades.append(SimulatedTrade(exit_side, exit_qty, fill_price, costs, update.realized_pnl, candle.timestamp, i))

        equity_curve.append(cash + Decimal(position_quantity) * current_price)

    final_price = candles[-1].close
    final_capital = cash + Decimal(position_quantity) * final_price

    return BacktestResult(
        initial_capital=config.initial_capital,
        final_capital=final_capital,
        trades=trades,
        max_drawdown_pct=_max_drawdown_pct(equity_curve),
        candles_evaluated=len(candles) - MIN_LOOKBACK_CANDLES,
    )


def _max_drawdown_pct(equity_curve: list[Decimal]) -> Decimal:
    if not equity_curve:
        return Decimal("0")

    peak = equity_curve[0]
    max_dd = Decimal("0")
    for value in equity_curve:
        peak = max(peak, value)
        if peak > 0:
            drawdown = (peak - value) / peak * Decimal("100")
            max_dd = max(max_dd, drawdown)
    return max_dd
