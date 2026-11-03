from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.deps import get_current_user, get_db
from app.middleware.rate_limit import assistant_rate_limit, order_rate_limit
from app.models.execution import Execution
from app.models.audit_log import AuditLog
from app.models.broker_connection import BrokerConnection
from app.models.broker_portfolio_allocation import BrokerPortfolioAllocation
from app.models.broker_funds_snapshot import BrokerFundsSnapshot
from app.models.broker_position_snapshot import BrokerPositionSnapshot
from app.models.broker_holding_snapshot import BrokerHoldingSnapshot
from app.models.position import Position
from app.models.user import User
from app.repositories.portfolio_repository import PortfolioRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.broker import BrokerPortfolioAllocationCreate, BrokerPortfolioAllocationOut, BrokerFundsSnapshotOut, BrokerPositionSnapshotOut, BrokerHoldingSnapshotOut
from app.schemas.analytics import PortfolioAnalyticsOut, StrategyAnalyticsOut
from app.schemas.assistant import AssistantAskRequest, AssistantAskResponse
from app.schemas.order import ExecutionOut, OrderOut, PlaceOrderRequest, PositionOut
from app.schemas.portfolio import PortfolioCreate, PortfolioOut, PortfolioRiskSettings
from app.services.ai_assistant_service import AIAssistantService, AssistantError
from app.services import analytics_service
from app.services.execution_service import ExecutionService, OrderValidationError
from app.services.execution_service import PlaceOrderRequest as ServicePlaceOrderRequest
from app.services.transaction_costs import Segment, Side
from app.services.broker_credentials_service import BrokerCredentialsService
from app.brokers.registry import get_broker_adapter
from app.services.broker_funds_service import normalize_upstox_funds_v3
from app.services.broker_position_service import normalize_upstox_positions
from redis.asyncio import from_url
from app.core.config import settings
from app.services.redis_market_quote_consumer import RedisMarketQuoteConsumer
from app.services.live_portfolio_pnl_view_service import build_live_unrealized_pnl_view
from app.services.broker_holding_service import normalize_upstox_holdings
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/portfolios", tags=["portfolios"])

# Broker position snapshots are refreshed by an explicit broker sync; never value old positions.
LIVE_POSITION_SNAPSHOT_MAX_AGE_SECONDS = 120


@router.get("", response_model=list[PortfolioOut])
def list_portfolios(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return PortfolioRepository(db).list_for_user(user.id)


@router.post("", response_model=PortfolioOut, status_code=status.HTTP_201_CREATED)
def create_portfolio(payload: PortfolioCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return PortfolioRepository(db).create(
        user_id=user.id, name=payload.name, virtual_capital=payload.virtual_capital,
        trading_mode=payload.trading_mode,
    )


def _get_owned_portfolio(db: Session, user: User, portfolio_id: UUID):
    portfolio = PortfolioRepository(db).get_for_user(user.id, portfolio_id)
    if portfolio is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Portfolio not found.")
    return portfolio


@router.get("/{portfolio_id}", response_model=PortfolioOut)
def get_portfolio(portfolio_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_owned_portfolio(db, user, portfolio_id)


@router.patch("/{portfolio_id}/risk-settings", response_model=PortfolioOut)
def update_portfolio_risk_settings(
    portfolio_id: UUID,
    payload: PortfolioRiskSettings,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfolio = _get_owned_portfolio(db, user, portfolio_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(portfolio, field, value)
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@router.post(
    "/{portfolio_id}/broker-allocation",
    response_model=BrokerPortfolioAllocationOut,
    status_code=status.HTTP_201_CREATED,
)
def allocate_broker_account(
    portfolio_id: UUID,
    payload: BrokerPortfolioAllocationCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfolio = _get_owned_portfolio(db, user, portfolio_id)
    if portfolio.trading_mode != "LIVE":
        raise HTTPException(status.HTTP_409_CONFLICT, "Broker accounts can only be allocated to LIVE portfolios.")

    connection = (
        db.query(BrokerConnection)
        .filter(
            BrokerConnection.id == payload.broker_connection_id,
            BrokerConnection.user_id == user.id,
        )
        .with_for_update()
        .one_or_none()
    )
    if connection is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Broker connection not found.")
    now = datetime.now(timezone.utc)
    expiry = connection.access_token_expires_at
    if expiry is not None and expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if not connection.is_connected or not connection.access_token_encrypted or expiry is None or expiry <= now:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Broker connection must have a verified, currently usable OAuth session before allocation.",
        )

    allocation = BrokerPortfolioAllocation(
        broker_connection_id=connection.id,
        portfolio_id=portfolio.id,
        user_id=user.id,
        trading_mode="LIVE",
    )
    db.add(allocation)
    db.add(AuditLog(
        user_id=user.id,
        action="broker_portfolio_allocation.created",
        resource_type="broker_portfolio_allocation",
        resource_id=str(allocation.id),
        ip_address=request.client.host if request.client else None,
        event_metadata={"portfolio_id": str(portfolio.id), "broker_connection_id": str(connection.id), "broker": connection.broker},
    ))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This broker connection or LIVE portfolio is already allocated, or the ownership constraints were not satisfied.",
        ) from exc
    db.refresh(allocation)
    return {
        "id": allocation.id,
        "portfolio_id": portfolio.id,
        "broker_connection_id": connection.id,
        "broker": connection.broker,
        "trading_mode": "LIVE",
        "created_at": allocation.created_at,
    }


@router.get("/{portfolio_id}/broker-allocation", response_model=BrokerPortfolioAllocationOut)
def get_broker_account_allocation(
    portfolio_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfolio = _get_owned_portfolio(db, user, portfolio_id)
    allocation = (
        db.query(BrokerPortfolioAllocation)
        .filter(
            BrokerPortfolioAllocation.portfolio_id == portfolio.id,
            BrokerPortfolioAllocation.user_id == user.id,
        )
        .one_or_none()
    )
    if allocation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No broker account is allocated to this portfolio.")
    connection = db.query(BrokerConnection).filter(
        BrokerConnection.id == allocation.broker_connection_id,
        BrokerConnection.user_id == user.id,
    ).one_or_none()
    if connection is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Allocated broker connection is no longer available.")
    return {
        "id": allocation.id,
        "portfolio_id": portfolio.id,
        "broker_connection_id": connection.id,
        "broker": connection.broker,
        "trading_mode": allocation.trading_mode,
        "created_at": allocation.created_at,
    }


@router.delete("/{portfolio_id}/broker-allocation", status_code=status.HTTP_204_NO_CONTENT)
def remove_broker_account_allocation(
    portfolio_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfolio = _get_owned_portfolio(db, user, portfolio_id)
    allocation = (
        db.query(BrokerPortfolioAllocation)
        .filter(
            BrokerPortfolioAllocation.portfolio_id == portfolio.id,
            BrokerPortfolioAllocation.user_id == user.id,
        )
        .with_for_update()
        .one_or_none()
    )
    if allocation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No broker account is allocated to this portfolio.")
    db.add(AuditLog(
        user_id=user.id,
        action="broker_portfolio_allocation.deleted",
        resource_type="broker_portfolio_allocation",
        resource_id=str(allocation.id),
        ip_address=request.client.host if request.client else None,
        event_metadata={"portfolio_id": str(portfolio.id), "broker_connection_id": str(allocation.broker_connection_id)},
    ))
    db.delete(allocation)
    db.commit()


@router.post(
    "/{portfolio_id}/broker-funds/sync",
    response_model=BrokerFundsSnapshotOut,
    status_code=status.HTTP_201_CREATED,
)
async def sync_broker_funds(
    portfolio_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfolio = _get_owned_portfolio(db, user, portfolio_id)
    if portfolio.trading_mode != "LIVE":
        raise HTTPException(status.HTTP_409_CONFLICT, "Broker funds can only be synchronized to a LIVE portfolio.")
    allocation = db.query(BrokerPortfolioAllocation).filter(
        BrokerPortfolioAllocation.portfolio_id == portfolio.id,
        BrokerPortfolioAllocation.user_id == user.id,
    ).one_or_none()
    if allocation is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Allocate a verified broker connection before synchronizing funds.")
    connection = db.query(BrokerConnection).filter(
        BrokerConnection.id == allocation.broker_connection_id,
        BrokerConnection.user_id == user.id,
    ).one_or_none()
    if connection is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Allocated broker connection is unavailable.")
    access_token = BrokerCredentialsService(db).get_access_token(user.id, connection.broker)
    if not access_token:
        raise HTTPException(status.HTTP_409_CONFLICT, "Broker OAuth session is unavailable or expired. Reconnect the broker.")
    result = await get_broker_adapter(connection.broker).get_funds_and_margin(access_token)
    if not result.ok:
        code = status.HTTP_503_SERVICE_UNAVAILABLE if "423" in (result.error or "") else status.HTTP_502_BAD_GATEWAY
        raise HTTPException(code, "Broker funds service is temporarily unavailable; the previous snapshot was retained.")
    try:
        normalized = normalize_upstox_funds_v3(result.data)
    except ValueError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Broker returned an invalid funds response; no snapshot was saved.") from exc

    snapshot = BrokerFundsSnapshot(
        broker_connection_id=connection.id,
        portfolio_id=portfolio.id,
        user_id=user.id,
        **normalized,
        raw_response=result.data,
    )
    db.add(snapshot)
    db.add(AuditLog(
        user_id=user.id,
        action="broker_funds_snapshot.created",
        resource_type="broker_funds_snapshot",
        resource_id=str(snapshot.id),
        ip_address=request.client.host if request.client else None,
        event_metadata={"portfolio_id": str(portfolio.id), "broker_connection_id": str(connection.id), "broker": connection.broker},
    ))
    db.commit()
    db.refresh(snapshot)
    # Do not copy available margin into Portfolio.cash_balance or mark it as
    # withdrawable cash/net liquidation value. Those remain unavailable until
    # a separate verified account-equity source and mapping are implemented.
    return snapshot


@router.get("/{portfolio_id}/broker-funds/latest", response_model=BrokerFundsSnapshotOut)
def get_latest_broker_funds(
    portfolio_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfolio = _get_owned_portfolio(db, user, portfolio_id)
    if portfolio.trading_mode != "LIVE":
        raise HTTPException(status.HTTP_409_CONFLICT, "Broker funds are only available for LIVE portfolios.")
    allocation = db.query(BrokerPortfolioAllocation).filter(
        BrokerPortfolioAllocation.portfolio_id == portfolio.id,
        BrokerPortfolioAllocation.user_id == user.id,
    ).one_or_none()
    if allocation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No broker account is currently allocated to this portfolio.")
    snapshot = db.query(BrokerFundsSnapshot).filter(
        BrokerFundsSnapshot.portfolio_id == portfolio.id,
        BrokerFundsSnapshot.user_id == user.id,
        BrokerFundsSnapshot.broker_connection_id == allocation.broker_connection_id,
    ).order_by(desc(BrokerFundsSnapshot.created_at)).first()
    if snapshot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No verified broker funds snapshot is available for the currently allocated account.")
    return snapshot


@router.post(
    "/{portfolio_id}/broker-positions/sync",
    response_model=BrokerPositionSnapshotOut,
    status_code=status.HTTP_201_CREATED,
)
async def sync_broker_positions(
    portfolio_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfolio = _get_owned_portfolio(db, user, portfolio_id)
    if portfolio.trading_mode != "LIVE":
        raise HTTPException(status.HTTP_409_CONFLICT, "Broker positions can only be synchronized to a LIVE portfolio.")
    allocation = db.query(BrokerPortfolioAllocation).filter(
        BrokerPortfolioAllocation.portfolio_id == portfolio.id,
        BrokerPortfolioAllocation.user_id == user.id,
    ).one_or_none()
    if allocation is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Allocate a verified broker connection before synchronizing positions.")
    connection = db.query(BrokerConnection).filter(
        BrokerConnection.id == allocation.broker_connection_id,
        BrokerConnection.user_id == user.id,
    ).one_or_none()
    if connection is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Allocated broker connection is unavailable.")
    access_token = BrokerCredentialsService(db).get_access_token(user.id, connection.broker)
    if not access_token:
        raise HTTPException(status.HTTP_409_CONFLICT, "Broker OAuth session is unavailable or expired. Reconnect the broker.")
    result = await get_broker_adapter(connection.broker).get_positions(access_token)
    if not result.ok:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Broker positions service is unavailable; the previous snapshot was retained.")
    try:
        positions = normalize_upstox_positions(result.data)
    except ValueError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Broker returned an invalid positions response; no snapshot was saved.") from exc

    snapshot = BrokerPositionSnapshot(
        broker_connection_id=connection.id,
        portfolio_id=portfolio.id,
        user_id=user.id,
        positions=positions,
        raw_response=result.data,
    )
    db.add(snapshot)
    db.add(AuditLog(
        user_id=user.id,
        action="broker_position_snapshot.created",
        resource_type="broker_position_snapshot",
        resource_id=str(snapshot.id),
        ip_address=request.client.host if request.client else None,
        event_metadata={"portfolio_id": str(portfolio.id), "broker_connection_id": str(connection.id), "position_count": len(positions)},
    ))
    db.commit()
    db.refresh(snapshot)
    # This is a broker snapshot, not an order/fill ledger. It does not mutate
    # PAPER Position rows, LivePosition, cash balance, or lifetime P&L.
    return snapshot


@router.get("/{portfolio_id}/broker-positions/latest", response_model=BrokerPositionSnapshotOut)
def get_latest_broker_positions(
    portfolio_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfolio = _get_owned_portfolio(db, user, portfolio_id)
    if portfolio.trading_mode != "LIVE":
        raise HTTPException(status.HTTP_409_CONFLICT, "Broker positions are only available for LIVE portfolios.")
    allocation = db.query(BrokerPortfolioAllocation).filter(
        BrokerPortfolioAllocation.portfolio_id == portfolio.id,
        BrokerPortfolioAllocation.user_id == user.id,
    ).one_or_none()
    if allocation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No broker account is currently allocated to this portfolio.")
    snapshot = db.query(BrokerPositionSnapshot).filter(
        BrokerPositionSnapshot.portfolio_id == portfolio.id,
        BrokerPositionSnapshot.user_id == user.id,
        BrokerPositionSnapshot.broker_connection_id == allocation.broker_connection_id,
    ).order_by(desc(BrokerPositionSnapshot.created_at)).first()
    if snapshot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No verified broker positions snapshot is available for the currently allocated account.")
    return snapshot


@router.get("/{portfolio_id}/live-unrealized-pnl")
async def get_live_unrealized_pnl(
    portfolio_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Read-only LIVE P&L projection from the allocated broker snapshot and this user's fresh Redis quotes."""
    portfolio = _get_owned_portfolio(db, user, portfolio_id)
    if portfolio.trading_mode != "LIVE":
        raise HTTPException(status.HTTP_409_CONFLICT, "Unrealized broker P&L is only available for LIVE portfolios.")
    allocation = db.query(BrokerPortfolioAllocation).filter(
        BrokerPortfolioAllocation.portfolio_id == portfolio.id,
        BrokerPortfolioAllocation.user_id == user.id,
    ).one_or_none()
    if allocation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No broker account is currently allocated to this portfolio.")
    connection = db.query(BrokerConnection).filter(
        BrokerConnection.id == allocation.broker_connection_id,
        BrokerConnection.user_id == user.id,
    ).one_or_none()
    if connection is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "The allocated broker connection is unavailable.")
    snapshot = db.query(BrokerPositionSnapshot).filter(
        BrokerPositionSnapshot.portfolio_id == portfolio.id,
        BrokerPositionSnapshot.user_id == user.id,
        BrokerPositionSnapshot.broker_connection_id == connection.id,
    ).order_by(desc(BrokerPositionSnapshot.created_at)).first()
    if snapshot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No broker positions snapshot is available for the allocated account.")
    if not isinstance(snapshot.positions, list):
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "The stored broker positions snapshot is invalid.")
    snapshot_created_at = snapshot.created_at
    if snapshot_created_at is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "The broker positions snapshot has no creation timestamp.")
    if snapshot_created_at.tzinfo is None:
        snapshot_created_at = snapshot_created_at.replace(tzinfo=timezone.utc)
    snapshot_age_seconds = (datetime.now(timezone.utc) - snapshot_created_at).total_seconds()
    if snapshot_age_seconds < 0 or snapshot_age_seconds > LIVE_POSITION_SNAPSHOT_MAX_AGE_SECONDS:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "The broker positions snapshot is stale or has an invalid timestamp; synchronize broker positions before retrying.",
        )

    instrument_keys = list(dict.fromkeys(
        position.get("instrument_key")
        for position in snapshot.positions
        if isinstance(position, dict)
        and position.get("quantity") != 0
        and isinstance(position.get("instrument_key"), str)
        and position.get("instrument_key")
    ))
    quotes_by_instrument = {}
    redis = None
    try:
        redis = from_url(settings.REDIS_URL, decode_responses=True)
        # Distinguish an unavailable Redis service from an ordinary missing/stale
        # quote. The consumer intentionally maps Redis read failures to None.
        await redis.ping()
        consumer = RedisMarketQuoteConsumer(redis, user.id, max_age_seconds=15)
        for instrument_key in instrument_keys:
            quote = await consumer.get_quote(instrument_key)
            if quote is not None:
                quotes_by_instrument[instrument_key] = quote
    except Exception as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Market quote storage is temporarily unavailable; LIVE P&L cannot be calculated.",
        ) from exc
    finally:
        if redis is not None:
            await redis.aclose()

    return build_live_unrealized_pnl_view(
        broker_positions=snapshot.positions,
        quotes_by_instrument=quotes_by_instrument,
        now=datetime.now(timezone.utc),
        max_quote_age_seconds=15,
    )


@router.post(
    "/{portfolio_id}/broker-holdings/sync",
    response_model=BrokerHoldingSnapshotOut,
    status_code=status.HTTP_201_CREATED,
)
async def sync_broker_holdings(
    portfolio_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfolio = _get_owned_portfolio(db, user, portfolio_id)
    if portfolio.trading_mode != "LIVE":
        raise HTTPException(status.HTTP_409_CONFLICT, "Broker holdings can only be synchronized to a LIVE portfolio.")
    allocation = db.query(BrokerPortfolioAllocation).filter(
        BrokerPortfolioAllocation.portfolio_id == portfolio.id,
        BrokerPortfolioAllocation.user_id == user.id,
    ).one_or_none()
    if allocation is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Allocate a verified broker connection before synchronizing holdings.")
    connection = db.query(BrokerConnection).filter(
        BrokerConnection.id == allocation.broker_connection_id,
        BrokerConnection.user_id == user.id,
    ).one_or_none()
    if connection is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Allocated broker connection is unavailable.")
    access_token = BrokerCredentialsService(db).get_access_token(user.id, connection.broker)
    if not access_token:
        raise HTTPException(status.HTTP_409_CONFLICT, "Broker OAuth session is unavailable or expired. Reconnect the broker.")
    result = await get_broker_adapter(connection.broker).get_holdings(access_token)
    if not result.ok:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Broker holdings service is unavailable; the previous snapshot was retained.")
    try:
        holdings = normalize_upstox_holdings(result.data)
    except ValueError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Broker returned an invalid holdings response; no snapshot was saved.") from exc

    snapshot = BrokerHoldingSnapshot(
        broker_connection_id=connection.id,
        portfolio_id=portfolio.id,
        user_id=user.id,
        holdings=holdings,
        raw_response=result.data,
    )
    db.add(snapshot)
    db.add(AuditLog(
        user_id=user.id,
        action="broker_holding_snapshot.created",
        resource_type="broker_holding_snapshot",
        resource_id=str(snapshot.id),
        ip_address=request.client.host if request.client else None,
        event_metadata={"portfolio_id": str(portfolio.id), "broker_connection_id": str(connection.id), "holding_count": len(holdings)},
    ))
    db.commit()
    db.refresh(snapshot)
    # Demat holdings remain a separate broker snapshot. They never mutate
    # PAPER positions, execution rows, cash balance or the realized-P&L ledger.
    return snapshot


@router.get("/{portfolio_id}/broker-holdings/latest", response_model=BrokerHoldingSnapshotOut)
def get_latest_broker_holdings(
    portfolio_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    portfolio = _get_owned_portfolio(db, user, portfolio_id)
    if portfolio.trading_mode != "LIVE":
        raise HTTPException(status.HTTP_409_CONFLICT, "Broker holdings are only available for LIVE portfolios.")
    allocation = db.query(BrokerPortfolioAllocation).filter(
        BrokerPortfolioAllocation.portfolio_id == portfolio.id,
        BrokerPortfolioAllocation.user_id == user.id,
    ).one_or_none()
    if allocation is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No broker account is currently allocated to this portfolio.")
    snapshot = db.query(BrokerHoldingSnapshot).filter(
        BrokerHoldingSnapshot.portfolio_id == portfolio.id,
        BrokerHoldingSnapshot.user_id == user.id,
        BrokerHoldingSnapshot.broker_connection_id == allocation.broker_connection_id,
    ).order_by(desc(BrokerHoldingSnapshot.created_at)).first()
    if snapshot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No verified broker holdings snapshot is available for the currently allocated account.")
    return snapshot


@router.get("/{portfolio_id}/positions", response_model=list[PositionOut])
def list_positions(portfolio_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    portfolio = _get_owned_portfolio(db, user, portfolio_id)  # ownership check before touching child resources
    if portfolio.trading_mode == "LIVE":
        # LivePosition is broker-connection scoped and has no verified portfolio
        # allocation yet. Never return rows from the PAPER positions table as
        # if they were broker holdings.
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "LIVE positions are unavailable until a verified broker sync and portfolio allocation are implemented.",
        )
    return db.query(Position).filter(Position.portfolio_id == portfolio_id, Position.quantity != 0).all()


@router.get("/{portfolio_id}/orders", response_model=list[OrderOut])
def list_orders(portfolio_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_owned_portfolio(db, user, portfolio_id)
    return OrderRepository(db).list_for_portfolio(portfolio_id)


@router.delete("/{portfolio_id}/orders/{order_id}", response_model=OrderOut)
def cancel_order(
    portfolio_id: UUID,
    order_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        return ExecutionService(db).cancel_order(user.id, portfolio_id, order_id)
    except OrderValidationError as exc:
        message = str(exc)
        code = status.HTTP_404_NOT_FOUND if message in {"Portfolio not found.", "Order not found."} else status.HTTP_400_BAD_REQUEST
        raise HTTPException(code, message)


@router.get("/{portfolio_id}/executions", response_model=list[ExecutionOut])
def list_executions(portfolio_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_owned_portfolio(db, user, portfolio_id)
    return (
        db.query(Execution)
        .filter(Execution.portfolio_id == portfolio_id)
        .order_by(Execution.executed_at.desc())
        .all()
    )


@router.post("/{portfolio_id}/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def place_order(
    portfolio_id: UUID,
    payload: PlaceOrderRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _rl=Depends(order_rate_limit),
):
    service = ExecutionService(db)
    try:
        order = await service.place_order(
            user.id,
            ServicePlaceOrderRequest(
                portfolio_id=portfolio_id,
                instrument_id=payload.instrument_id,
                side=Side(payload.side),
                order_type=payload.order_type,
                segment=Segment(payload.segment),
                quantity=payload.quantity,
                limit_price=payload.limit_price,
            ),
        )
    except OrderValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return order


@router.post("/{portfolio_id}/assistant/ask", response_model=AssistantAskResponse)
async def ask_assistant(
    portfolio_id: UUID,
    payload: AssistantAskRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    _rl=Depends(assistant_rate_limit),
):
    portfolio = _get_owned_portfolio(db, user, portfolio_id)
    try:
        answer = await AIAssistantService(db).ask(portfolio, payload.question)
    except AssistantError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    return AssistantAskResponse(answer=answer)


@router.get("/{portfolio_id}/analytics", response_model=PortfolioAnalyticsOut)
def get_portfolio_analytics(portfolio_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    portfolio = _get_owned_portfolio(db, user, portfolio_id)
    return analytics_service.portfolio_analytics(
        db, portfolio.id, Decimal(str(portfolio.virtual_capital)), trading_mode=portfolio.trading_mode
    )


@router.get("/{portfolio_id}/strategies/analytics", response_model=list[StrategyAnalyticsOut])
def get_strategy_analytics(portfolio_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_owned_portfolio(db, user, portfolio_id)
    return analytics_service.strategy_analytics(db, portfolio_id)
