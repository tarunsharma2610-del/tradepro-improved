from datetime import date
from decimal import Decimal

import pytest

from app.brokers.upstox.reconciliation_client import ReadOnlyBrokerResult
from app.services.upstox_charge_api_orchestration_service import (
    AGGREGATE_CHARGES_ENDPOINT,
    BROKERAGE_ESTIMATE_ENDPOINT,
    UpstoxChargeApiOrchestrationService,
)


class FakeReadOnlyClient:
    def __init__(self, result):
        self.result = result
        self.calls = []

    async def get_brokerage_estimate(self, access_token, **kwargs):
        self.calls.append(("estimate", access_token, kwargs))
        return self.result

    async def get_trade_charges(self, access_token, **kwargs):
        self.calls.append(("aggregate", access_token, kwargs))
        return self.result


@pytest.mark.asyncio
async def test_brokerage_api_is_exposed_as_estimate_only_with_scope():
    payload = {"status": "success", "data": {"charges": {"gst": 3.60, "ipft": None}}}
    client = FakeReadOnlyClient(ReadOnlyBrokerResult(ok=True, data=payload, status_code=200))
    service = UpstoxChargeApiOrchestrationService(client)

    result = await service.get_brokerage_estimate(
        "secret-token",
        instrument_token="NSE_EQ|INE123A01016",
        quantity=10,
        product="I",
        transaction_type="BUY",
        price=Decimal("100.00"),
        trade_date=date(2026, 10, 27),
        exchange="nse",
        segment="eq",
    )

    assert result.endpoint == BROKERAGE_ESTIMATE_ENDPOINT
    assert result.evidence_kind == "ESTIMATE_ONLY"
    assert result.usable is True
    assert result.per_fill_actual is False
    assert result.payload == payload
    assert result.scope == {
        "exchange": "NSE",
        "segment": "EQ",
        "product": "I",
        "transaction_type": "BUY",
    }
    assert client.calls[0][1] == "secret-token"
    # Null IPFT is preserved in source payload; this service never converts it to zero.
    assert result.payload["data"]["charges"]["ipft"] is None


@pytest.mark.asyncio
async def test_post_trade_charges_api_is_aggregate_only_never_per_fill_actual():
    payload = {"status": "success", "data": {"charges_breakdown": {"total": 20.15, "taxes": {"gst": 3.60}, "charges": {"ipft": None}}}}
    client = FakeReadOnlyClient(ReadOnlyBrokerResult(ok=True, data=payload, status_code=200))
    service = UpstoxChargeApiOrchestrationService(client)

    result = await service.get_aggregate_trade_charges(
        "secret-token",
        segment="FO",
        financial_year="2627",
        from_date="01-10-2026",
        to_date="27-10-2026",
    )

    assert result.endpoint == AGGREGATE_CHARGES_ENDPOINT
    assert result.evidence_kind == "AGGREGATE_RECONCILIATION_ONLY"
    assert result.usable is True
    assert result.per_fill_actual is False
    assert result.trade_date is None
    assert result.scope["segment"] == "FO"
    assert result.scope["financial_year"] == "2627"
    assert result.payload == payload


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("endpoint_kind", "payload"),
    [
        ("estimate", {"status": "error", "data": {"charges": {"total": 10}}}),
        ("estimate", {"status": "success", "data": {"charges_breakdown": {"total": 10}}}),
        ("aggregate", {"status": "success", "data": {"total_charges": 20.15}}),
        ("aggregate", {"status": "success", "data": {"charges": {"total": 20.15}}}),
        ("aggregate", {"data": {"charges_breakdown": {"total": 20.15}}}),
    ],
)
async def test_successful_http_with_wrong_documented_payload_schema_is_unusable(endpoint_kind, payload):
    client = FakeReadOnlyClient(ReadOnlyBrokerResult(ok=True, data=payload, status_code=200))
    service = UpstoxChargeApiOrchestrationService(client)
    if endpoint_kind == "estimate":
        result = await service.get_brokerage_estimate(
            "token", instrument_token="NSE_EQ|TEST", quantity=1, product="I",
            transaction_type="BUY", price="100", trade_date=date(2026, 10, 27),
            exchange="NSE", segment="EQ",
        )
    else:
        result = await service.get_aggregate_trade_charges(
            "token", segment="FO", financial_year="2627"
        )
    assert result.usable is False
    assert result.payload is None
    assert result.per_fill_actual is False
    assert result.error_code == "INVALID_RESPONSE_SCHEMA"


@pytest.mark.asyncio
async def test_failed_api_call_is_not_exposed_as_usable_evidence():
    client = FakeReadOnlyClient(
        ReadOnlyBrokerResult(ok=False, status_code=401, error_code="TOKEN_EXPIRED_OR_UNAUTHORIZED")
    )
    service = UpstoxChargeApiOrchestrationService(client)

    result = await service.get_aggregate_trade_charges(
        "expired-token", segment="EQ", financial_year="2627"
    )

    assert result.usable is False
    assert result.payload is None
    assert result.per_fill_actual is False
    assert result.error_code == "TOKEN_EXPIRED_OR_UNAUTHORIZED"


@pytest.mark.asyncio
async def test_brokerage_estimate_requires_explicit_trade_date():
    client = FakeReadOnlyClient(ReadOnlyBrokerResult(ok=True, data={"data": {}}, status_code=200))
    service = UpstoxChargeApiOrchestrationService(client)

    with pytest.raises(ValueError, match="explicit date"):
        await service.get_brokerage_estimate(
            "secret-token",
            instrument_token="NSE_EQ|INE123A01016",
            quantity=1,
            product="D",
            transaction_type="SELL",
            price="100",
            trade_date="2026-10-27",
            exchange="NSE",
            segment="EQ",
        )
