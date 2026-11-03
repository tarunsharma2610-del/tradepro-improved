"""Fail-closed live market scanner over validated Redis quote snapshots.

This first scanner slice computes observations only. It does not create trade
signals, persist orders, or call any broker order endpoint. Historical candles
remain the source for technical indicators until the PAPER integration gate.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import isfinite
import time
from uuid import UUID
from app.services.candle_parsing import parse_candles
from app.services.indicators import momentum


def _finite_number(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if isfinite(number) else None


@dataclass(frozen=True)
class MarketScanObservation:
    user_id: str
    instrument_key: str
    epoch: str
    version: int
    ltp: float
    price_change_pct: float | None
    volume_traded_today: float | None
    open_interest: float | None
    buy_sell_imbalance: float | None
    option_greeks: dict | None
    exchange_timestamp_ms: int
    received_at: str
    # Optional defaults preserve compatibility for existing observation
    # producers and tests that construct the pre-depth data shape.
    best_bid_price: float | None = None
    best_ask_price: float | None = None
    spread_bps: float | None = None
    best_bid_quantity: float | None = None
    best_ask_quantity: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class MarketScanner:
    """Build per-user, per-instrument observations from validated snapshots."""

    def __init__(self, *, max_age_seconds: float = 15.0) -> None:
        if max_age_seconds <= 0:
            raise ValueError("Scanner observation TTL must be positive.")
        self.max_age_seconds = max_age_seconds
        self._latest: dict[tuple[str, str], MarketScanObservation] = {}
        self._latest_seen: dict[tuple[str, str], float] = {}

    def process_quote(
        self, user_id: UUID | str, quote: dict, *, now: datetime | None = None
    ) -> MarketScanObservation | None:
        owner = str(user_id)
        if not isinstance(quote, dict) or quote.get("user_id") != owner:
            return None
        instrument_key, epoch = quote.get("instrument_key"), quote.get("epoch")
        version, ltp = quote.get("version"), _finite_number(quote.get("ltp"))
        exchange_timestamp_ms, received_at = quote.get("exchange_timestamp_ms"), quote.get("received_at")
        if (
            not isinstance(instrument_key, str) or "|" not in instrument_key
            or not isinstance(epoch, str) or not epoch
            or isinstance(version, bool) or not isinstance(version, int) or version <= 0
            or ltp is None or ltp <= 0
            or isinstance(exchange_timestamp_ms, bool)
            or not isinstance(exchange_timestamp_ms, int) or exchange_timestamp_ms <= 0
            or not isinstance(received_at, str)
        ):
            return None
        try:
            parsed_received_at = datetime.fromisoformat(received_at)
        except ValueError:
            return None
        if parsed_received_at.tzinfo is None:
            return None

        current = now or datetime.now(parsed_received_at.tzinfo)
        if current.tzinfo is None:
            return None
        current_utc = current.astimezone(timezone.utc)
        received_utc = parsed_received_at.astimezone(timezone.utc)
        received_age = (current_utc - received_utc).total_seconds()
        exchange_age_ms = current_utc.timestamp() * 1000 - exchange_timestamp_ms
        if not 0 <= received_age <= self.max_age_seconds:
            return None
        # Permit up to 60 seconds of exchange/server clock skew, but reject
        # future-dated ticks beyond that and ticks older than the scanner TTL.
        if not -60_000 <= exchange_age_ms <= self.max_age_seconds * 1000:
            return None

        identity = (owner, instrument_key)
        previous = self._latest.get(identity)
        if previous is not None and previous.epoch == epoch and version <= previous.version:
            return None

        price_change_pct = None
        ohlc = quote.get("ohlc")
        if isinstance(ohlc, list):
            daily = next(
                (item for item in ohlc if isinstance(item, dict)
                 and str(item.get("interval", "")).lower() in {"1d", "day", "daily"}),
                None,
            )
            close = _finite_number(daily.get("close")) if daily else None
            if close is not None and close > 0:
                price_change_pct = ((ltp - close) / close) * 100.0

        volume = _finite_number(quote.get("volume_traded_today"))
        open_interest = _finite_number(quote.get("open_interest"))
        buy, sell = _finite_number(quote.get("total_buy_quantity")), _finite_number(quote.get("total_sell_quantity"))
        imbalance = None
        if buy is not None and sell is not None and buy >= 0 and sell >= 0 and buy + sell > 0:
            imbalance = (buy - sell) / (buy + sell)

        # Market-quality measurements use only the first provider depth
        # level. Missing, malformed, crossed, or non-positive books stay None;
        # they must never be interpreted as liquid/zero-spread markets.
        best_bid = best_ask = spread_bps = bid_quantity = ask_quantity = None
        raw_depth = quote.get("depth")
        if isinstance(raw_depth, list) and raw_depth and isinstance(raw_depth[0], dict):
            level = raw_depth[0]
            bid = _finite_number(level.get("bid_price"))
            ask = _finite_number(level.get("ask_price"))
            bid_qty = _finite_number(level.get("bid_quantity"))
            ask_qty = _finite_number(level.get("ask_quantity"))
            if bid is not None and ask is not None and bid > 0 and ask >= bid:
                midpoint = (bid + ask) / 2.0
                if midpoint > 0:
                    best_bid, best_ask = bid, ask
                    spread_bps = ((ask - bid) / midpoint) * 10_000.0
            if bid_qty is not None and bid_qty >= 0:
                bid_quantity = bid_qty
            if ask_qty is not None and ask_qty >= 0:
                ask_quantity = ask_qty

        raw_greeks = quote.get("option_greeks")
        greeks = None
        if isinstance(raw_greeks, dict):
            valid = {key: number for key, raw in raw_greeks.items()
                     if (number := _finite_number(raw)) is not None}
            greeks = valid or None

        observation = MarketScanObservation(
            user_id=owner, instrument_key=instrument_key, epoch=epoch, version=version,
            ltp=ltp, price_change_pct=price_change_pct,
            volume_traded_today=volume if volume is not None and volume >= 0 else None,
            open_interest=open_interest if open_interest is not None and open_interest >= 0 else None,
            buy_sell_imbalance=imbalance,
            best_bid_price=best_bid, best_ask_price=best_ask,
            spread_bps=spread_bps,
            best_bid_quantity=bid_quantity, best_ask_quantity=ask_quantity,
            option_greeks=greeks,
            exchange_timestamp_ms=exchange_timestamp_ms, received_at=received_at,
        )
        self._latest[identity] = observation
        self._latest_seen[identity] = time.monotonic()
        return observation

    @staticmethod
    def historical_momentum_from_response(response_data: dict, *, period: int = 10):
        """Return the shared momentum score from validated Upstox candles.

        Provider errors, malformed rows, or insufficient history yield None.
        This is an advisory scanner feature; it never creates an order signal.
        """
        if isinstance(period, bool) or not isinstance(period, int) or period <= 0:
            return None
        candles = parse_candles(response_data)
        if candles is None or len(candles) < period + 1:
            return None
        return momentum(candles, period=period)

    @staticmethod
    def passes_market_quality(
        observation: MarketScanObservation,
        *,
        max_spread_bps: float,
        min_bid_quantity: float = 0.0,
        min_ask_quantity: float = 0.0,
    ) -> bool:
        """Apply caller-supplied liquidity limits; unknown data fails closed.

        Thresholds are deliberately explicit inputs rather than universal
        constants because acceptable spreads/depth differ by segment and
        instrument. This is a scanner filter only, never an execution rule.
        """
        limits = (max_spread_bps, min_bid_quantity, min_ask_quantity)
        if any(_finite_number(value) is None for value in limits):
            return False
        if max_spread_bps < 0 or min_bid_quantity < 0 or min_ask_quantity < 0:
            return False
        if (
            observation.spread_bps is None
            or observation.best_bid_quantity is None
            or observation.best_ask_quantity is None
        ):
            return False
        return (
            observation.spread_bps <= max_spread_bps
            and observation.best_bid_quantity >= min_bid_quantity
            and observation.best_ask_quantity >= min_ask_quantity
        )

    def latest(self, user_id: UUID | str, instrument_key: str) -> MarketScanObservation | None:
        identity = (str(user_id), instrument_key)
        seen = self._latest_seen.get(identity)
        if seen is None or time.monotonic() - seen > self.max_age_seconds:
            self._latest.pop(identity, None)
            self._latest_seen.pop(identity, None)
            return None
        return self._latest.get(identity)

    def clear_instrument(self, user_id: UUID | str, instrument_key: str) -> None:
        """Allow one capacity-dropped Redis snapshot to be validated again."""
        identity = (str(user_id), instrument_key)
        self._latest.pop(identity, None)
        self._latest_seen.pop(identity, None)

    def clear_user(self, user_id: UUID | str) -> None:
        owner = str(user_id)
        for identity in [key for key in self._latest if key[0] == owner]:
            self._latest.pop(identity, None)
            self._latest_seen.pop(identity, None)
