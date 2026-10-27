"""Authenticated, read-only endpoints for Upstox charge estimates and aggregate reconciliation."""
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.encryption import decrypt_value
from app.models.broker_connection import BrokerConnection
from app.models.user import User
from app.repositories.broker_connection_repository import BrokerConnectionRepository
from app.services.upstox_charge_api_orchestration_service import (
    UpstoxChargeApiOrchestrationService,
)

router = APIRouter(prefix="/upstox/charges", tags=["Upstox charge APIs"])


class ChargeApiResponse(BaseModel):
    broker: str = "upstox"
    endpoint: str
    evidence_kind: str
    usable: bool
    per_fill_actual: bool
    trade_date: date | None = None
    scope: dict[str, str]
    payload: Any = None
    status_code: int | None = None
    error_code: str | None = None


def _connected_token(db: Session, user_id: UUID) -> str:
    connection = BrokerConnectionRepository(db).get_for_user(user_id, "upstox")
    if connection is None or not connection.is_connected or not connection.access_token_encrypted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Upstox is not connected. Complete OAuth and test the connection first.",
        )
    token = decrypt_value(connection.access_token_encrypted)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Stored Upstox access token cannot be decrypted; reconnect the broker.",
        )
    return token


@router.get("/brokerage-estimate", response_model=ChargeApiResponse)
async def brokerage_estimate(
    instrument_token: str = Query(min_length=1, max_length=128),
    quantity: int = Query(gt=0),
    product: str = Query(min_length=1, max_length=16),
    transaction_type: str = Query(pattern="^(BUY|SELL|buy|sell)$"),
    price: Decimal = Query(gt=0),
    trade_date: date = Query(...),
    exchange: str = Query(min_length=1, max_length=8),
    segment: str = Query(min_length=1, max_length=8),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return an estimate only; never an actual charge or canonical allocation."""
    token = _connected_token(db, user.id)
    try:
        result = await UpstoxChargeApiOrchestrationService().get_brokerage_estimate(
            token,
            instrument_token=instrument_token,
            quantity=quantity,
            product=product,
            transaction_type=transaction_type,
            price=price,
            trade_date=trade_date,
            exchange=exchange,
            segment=segment,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ChargeApiResponse(
        endpoint=result.endpoint,
        evidence_kind=result.evidence_kind,
        usable=result.usable,
        per_fill_actual=False,
        trade_date=result.trade_date,
        scope=result.scope,
        payload=result.payload,
        status_code=result.status_code,
        error_code=result.error_code,
    )


@router.get("/aggregate")
async def aggregate_trade_charges(
    segment: str = Query(min_length=1, max_length=8),
    financial_year: str = Query(min_length=4, max_length=4, pattern="^[0-9]{4}$"),
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Return aggregate evidence for reconciliation; never per-fill actuals."""
    token = _connected_token(db, user.id)
    try:
        result = await UpstoxChargeApiOrchestrationService().get_aggregate_trade_charges(
            token,
            segment=segment,
            financial_year=financial_year,
            from_date=from_date,
            to_date=to_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return ChargeApiResponse(
        endpoint=result.endpoint,
        evidence_kind=result.evidence_kind,
        usable=result.usable,
        per_fill_actual=False,
        trade_date=None,
        scope=result.scope,
        payload=result.payload,
        status_code=result.status_code,
        error_code=result.error_code,
    )
