"""Fail-closed live market scanner over validated Redis quote snapshots.

This first scanner slice computes observations only. It does not create trade
signals, persist orders, or call any broker order endpoint. Historical candles
remain the source for technical indicators until the PAPER integration gate.
"""
from dataclasses import asdict, dataclass
from datetime import datetime
from math import isfinite
from uuid import UUID


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

    def to_dict(self) -> dict:
        return asdict(self)


class MarketScanner:
    """Build per-user, per-instrument observations from validated snapshots."""

    def __init__(self) -> None:
        self._latest: dict[tuple[str, str], MarketScanObservation] = {}

    def process_quote(self, user_id: UUID | str, quote: dict) -> MarketScanObservation | None:
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
            buy_sell_imbalance=imbalance, option_greeks=greeks,
            exchange_timestamp_ms=exchange_timestamp_ms, received_at=received_at,
        )
        self._latest[identity] = observation
        return observation

    def latest(self, user_id: UUID | str, instrument_key: str) -> MarketScanObservation | None:
        return self._latest.get((str(user_id), instrument_key))

    def clear_user(self, user_id: UUID | str) -> None:
        owner = str(user_id)
        for identity in [key for key in self._latest if key[0] == owner]:
            self._latest.pop(identity, None)
