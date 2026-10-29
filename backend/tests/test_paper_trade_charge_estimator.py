from datetime import date
from decimal import Decimal

import pytest

from app.brokers.upstox.reconciliation_client import ReadOnlyBrokerResult
from app.services.paper_trade_charge_estimator import estimate_paper_trade_costs
from app.services.transaction_costs import Segment, Side, calculate_costs


class FakeChargeClient:
    def __init__(self, result):
        self.result = result
        self.calls = []

    async def get_brokerage_estimate(self, access_token, **kwargs):
        self.calls.append((access_token, kwargs))
        return self.result


def api_payload(*, ipft="0.17", total=Decimal("6.19")):
    # Components sum to 6.19: brokerage 1.00 + GST .90 + STT 1.00 +
    # stamp .50 + transaction 2.00 + clearing .00 + IPFT .17 + SEBI .62.
    return {
        "status": "success",
        "data": {
            "charges": {
                "total": str(total),
                "brokerage": "1.00",
                "taxes": {"gst": "0.90", "stt": "1.00", "stamp_duty": "0.50"},
                "other_charges": {
                    "transaction": "2.00",
                    "clearing": "0.00",
                    "ipft": ipft,
                    "sebi_turnover": "0.62",
                },
            }
        },
    }


@pytest.mark.asyncio
async def test_complete_upstox_estimate_is_used_and_ipft_counted_once():
    client = FakeChargeClient(ReadOnlyBrokerResult(ok=True, data=api_payload(), status_code=200))
    result = await estimate_paper_trade_costs(
        "test-token",
        instrument_token="NSE_FO|12345",
        quantity=10,
        segment=Segment.OPTIONS,
        side=Side.BUY,
        price=Decimal("100.00"),
        trade_date=date(2026, 10, 29),
        client=client,
    )

    assert result.source == "UPSTOX_API_ESTIMATE"
    assert result.costs.total_charges == Decimal("6.19")
    assert result.costs.exchange_charges == Decimal("2.17")
    assert result.costs.gst == Decimal("0.90")
    assert client.calls[0][1]["product"] == "I"
    assert client.calls[0][1]["transaction_type"] == "BUY"


@pytest.mark.asyncio
async def test_delivery_uses_delivery_product_code():
    client = FakeChargeClient(ReadOnlyBrokerResult(ok=True, data=api_payload(), status_code=200))
    await estimate_paper_trade_costs(
        "test-token",
        instrument_token="NSE_EQ|INE123A01016",
        quantity=10,
        segment=Segment.EQUITY_DELIVERY,
        side=Side.SELL,
        price=Decimal("100.00"),
        trade_date=date(2026, 10, 29),
        client=client,
    )
    assert client.calls[0][1]["product"] == "D"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload",
    [
        {"status": "success", "data": {}},
        {"status": "error", "data": api_payload()["data"]},
        api_payload(ipft=None),
        api_payload(total=Decimal("9.99")),
        {"status": "success", "data": {"charges": {
            "total": "6.19", "brokerage": "1.00",
            "taxes": {"gst": "NaN", "stt": "1.00", "stamp_duty": "0.50"},
            "other_charges": {"transaction": "2.00", "clearing": "0.00", "ipft": "0.17", "sebi_turnover": "0.62"},
        }}},
    ],
)
async def test_incomplete_invalid_or_inconsistent_api_uses_hardcoded_fallback(payload):
    client = FakeChargeClient(ReadOnlyBrokerResult(ok=True, data=payload, status_code=200))
    result = await estimate_paper_trade_costs(
        "test-token",
        instrument_token="NSE_EQ|INE123A01016",
        quantity=10,
        segment=Segment.EQUITY_DELIVERY,
        side=Side.BUY,
        price=Decimal("100.00"),
        trade_date=date(2026, 10, 29),
        client=client,
    )
    assert result.source == "HARDCODED_FALLBACK"
    assert result.costs == calculate_costs(
        Segment.EQUITY_DELIVERY, Side.BUY, 10, Decimal("100.00")
    )
    assert result.fallback_reason


@pytest.mark.asyncio
async def test_api_failure_uses_hardcoded_fallback_without_blocking_paper_trade():
    client = FakeChargeClient(ReadOnlyBrokerResult(ok=False, status_code=401, error_code="TOKEN_EXPIRED_OR_UNAUTHORIZED"))
    result = await estimate_paper_trade_costs(
        "expired",
        instrument_token="NSE_EQ|INE123A01016",
        quantity=10,
        segment=Segment.EQUITY_DELIVERY,
        side=Side.BUY,
        price=Decimal("100.00"),
        trade_date=date(2026, 10, 29),
        client=client,
    )
    assert result.source == "HARDCODED_FALLBACK"
    assert result.fallback_reason == "TOKEN_EXPIRED_OR_UNAUTHORIZED"


@pytest.mark.asyncio
async def test_missing_token_uses_hardcoded_fallback():
    result = await estimate_paper_trade_costs(
        None,
        instrument_token="NSE_EQ|INE123A01016",
        quantity=10,
        segment=Segment.EQUITY_DELIVERY,
        side=Side.BUY,
        price=Decimal("100.00"),
        trade_date=date(2026, 10, 29),
    )
    assert result.source == "HARDCODED_FALLBACK"
    assert result.fallback_reason == "missing_access_token"
