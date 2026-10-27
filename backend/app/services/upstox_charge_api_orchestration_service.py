"""Safe orchestration boundary for Upstox charge APIs.

This service intentionally separates pre-trade estimates from post-trade aggregate
reconciliation evidence. Neither response is per-fill actual charge evidence, and
neither can be passed directly to live-fill accounting as a canonical allocation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from app.brokers.upstox.reconciliation_client import (
    ReadOnlyBrokerResult,
    UpstoxReadOnlyReconciliationClient,
)


BROKERAGE_ESTIMATE_ENDPOINT = "/v2/charges/brokerage"
AGGREGATE_CHARGES_ENDPOINT = "/v2/trade/profit-loss/charges"


@dataclass(frozen=True)
class ChargeApiEnvelope:
    broker: str
    endpoint: str
    evidence_kind: str
    usable: bool
    per_fill_actual: bool
    trade_date: date | None
    scope: dict[str, str]
    payload: Any = None
    status_code: int | None = None
    error_code: str | None = None


class UpstoxChargeApiOrchestrationService:
    """Call read-only charge APIs and preserve their permitted evidence scope."""

    def __init__(self, client: UpstoxReadOnlyReconciliationClient | None = None):
        self.client = client or UpstoxReadOnlyReconciliationClient()

    @staticmethod
    def _envelope(
        result: ReadOnlyBrokerResult,
        *,
        endpoint: str,
        evidence_kind: str,
        trade_date: date | None,
        scope: dict[str, str],
    ) -> ChargeApiEnvelope:
        return ChargeApiEnvelope(
            broker="upstox",
            endpoint=endpoint,
            evidence_kind=evidence_kind,
            usable=bool(result.ok and result.data is not None),
            # This orchestration service only calls the two documented APIs below;
            # neither endpoint is accepted as per-fill actual evidence.
            per_fill_actual=False,
            trade_date=trade_date,
            scope=dict(scope),
            payload=result.data if result.ok else None,
            status_code=result.status_code,
            error_code=result.error_code,
        )

    async def get_brokerage_estimate(
        self,
        access_token: str,
        *,
        instrument_token: str,
        quantity: int,
        product: str,
        transaction_type: str,
        price: Decimal | str | int | float,
        trade_date: date,
        exchange: str,
        segment: str,
    ) -> ChargeApiEnvelope:
        if not isinstance(trade_date, date):
            raise ValueError("trade_date must be an explicit date.")
        result = await self.client.get_brokerage_estimate(
            access_token,
            instrument_token=instrument_token,
            quantity=quantity,
            product=product,
            transaction_type=transaction_type,
            price=price,
        )
        return self._envelope(
            result,
            endpoint=BROKERAGE_ESTIMATE_ENDPOINT,
            evidence_kind="ESTIMATE_ONLY",
            trade_date=trade_date,
            scope={
                "exchange": exchange.upper(),
                "segment": segment.upper(),
                "product": product.upper(),
                "transaction_type": transaction_type.upper(),
            },
        )

    async def get_aggregate_trade_charges(
        self,
        access_token: str,
        *,
        segment: str,
        financial_year: str,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> ChargeApiEnvelope:
        result = await self.client.get_trade_charges(
            access_token,
            segment=segment,
            financial_year=financial_year,
            from_date=from_date,
            to_date=to_date,
        )
        return self._envelope(
            result,
            endpoint=AGGREGATE_CHARGES_ENDPOINT,
            evidence_kind="AGGREGATE_RECONCILIATION_ONLY",
            trade_date=None,
            scope={
                "segment": segment.upper(),
                "financial_year": financial_year,
                **({"from_date": from_date} if from_date else {}),
                **({"to_date": to_date} if to_date else {}),
            },
        )
