from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.middleware.rate_limit import assistant_rate_limit, order_rate_limit
from app.models.execution import Execution
from app.models.position import Position
from app.models.user import User
from app.repositories.portfolio_repository import PortfolioRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.analytics import PortfolioAnalyticsOut, StrategyAnalyticsOut
from app.schemas.assistant import AssistantAskRequest, AssistantAskResponse
from app.schemas.order import ExecutionOut, OrderOut, PlaceOrderRequest, PositionOut
from app.schemas.portfolio import PortfolioCreate, PortfolioOut
from app.services.ai_assistant_service import AIAssistantService, AssistantError
from app.services import analytics_service
from app.services.execution_service import ExecutionService, OrderValidationError
from app.services.execution_service import PlaceOrderRequest as ServicePlaceOrderRequest
from app.services.transaction_costs import Segment, Side

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


@router.get("", response_model=list[PortfolioOut])
def list_portfolios(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return PortfolioRepository(db).list_for_user(user.id)


@router.post("", response_model=PortfolioOut, status_code=status.HTTP_201_CREATED)
def create_portfolio(payload: PortfolioCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return PortfolioRepository(db).create(user_id=user.id, name=payload.name, virtual_capital=payload.virtual_capital)


def _get_owned_portfolio(db: Session, user: User, portfolio_id: UUID):
    portfolio = PortfolioRepository(db).get_for_user(user.id, portfolio_id)
    if portfolio is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Portfolio not found.")
    return portfolio


@router.get("/{portfolio_id}", response_model=PortfolioOut)
def get_portfolio(portfolio_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_owned_portfolio(db, user, portfolio_id)


@router.get("/{portfolio_id}/positions", response_model=list[PositionOut])
def list_positions(portfolio_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_owned_portfolio(db, user, portfolio_id)  # ownership check before touching child resources
    return db.query(Position).filter(Position.portfolio_id == portfolio_id, Position.quantity != 0).all()


@router.get("/{portfolio_id}/orders", response_model=list[OrderOut])
def list_orders(portfolio_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_owned_portfolio(db, user, portfolio_id)
    return OrderRepository(db).list_for_portfolio(portfolio_id)


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
    return analytics_service.portfolio_analytics(db, portfolio.id, Decimal(str(portfolio.virtual_capital)))


@router.get("/{portfolio_id}/strategies/analytics", response_model=list[StrategyAnalyticsOut])
def get_strategy_analytics(portfolio_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_owned_portfolio(db, user, portfolio_id)
    return analytics_service.strategy_analytics(db, portfolio_id)
