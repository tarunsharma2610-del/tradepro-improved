from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.order import Order
from app.models.strategy import Strategy
from app.models.user import User
from app.repositories.instrument_repository import InstrumentRepository
from app.repositories.strategy_repository import StrategyRepository
from app.services.instrument_validation import validate_instrument_segment
from app.schemas.order import OrderOut
from app.schemas.strategy import StrategyCreate, StrategyEvaluationOut, StrategyOut, StrategyUpdate
from app.services.strategy_execution_service import StrategyExecutionService

# Mounted under /portfolios in router.py so URLs read
# /portfolios/{portfolio_id}/strategies/... — a strategy always belongs to
# exactly one portfolio, same relationship as orders/positions.
router = APIRouter(prefix="/portfolios/{portfolio_id}/strategies", tags=["strategies"])


def _get_owned_portfolio(db: Session, user: User, portfolio_id: UUID):
    from app.repositories.portfolio_repository import PortfolioRepository

    portfolio = PortfolioRepository(db).get_for_user(user.id, portfolio_id)
    if portfolio is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Portfolio not found.")
    return portfolio


def _get_owned_strategy(db: Session, user: User, portfolio_id: UUID, strategy_id: UUID) -> Strategy:
    _get_owned_portfolio(db, user, portfolio_id)
    strategy = StrategyRepository(db).get_for_portfolio(portfolio_id, strategy_id)
    if strategy is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Strategy not found.")
    return strategy


@router.get("", response_model=list[StrategyOut])
def list_strategies(portfolio_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_owned_portfolio(db, user, portfolio_id)
    return StrategyRepository(db).list_for_portfolio(portfolio_id)


@router.post("", response_model=StrategyOut, status_code=status.HTTP_201_CREATED)
def create_strategy(
    portfolio_id: UUID, payload: StrategyCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    _get_owned_portfolio(db, user, portfolio_id)
    instrument = InstrumentRepository(db).get_by_id(payload.instrument_id)
    if instrument is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Instrument not found.")
    try:
        validate_instrument_segment(instrument, payload.segment)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    strategy = Strategy(portfolio_id=portfolio_id, is_active=False, **payload.model_dump())
    return StrategyRepository(db).create(strategy)


@router.get("/{strategy_id}", response_model=StrategyOut)
def get_strategy(portfolio_id: UUID, strategy_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _get_owned_strategy(db, user, portfolio_id, strategy_id)


@router.patch("/{strategy_id}", response_model=StrategyOut)
def update_strategy(
    portfolio_id: UUID, strategy_id: UUID, payload: StrategyUpdate,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    strategy = _get_owned_strategy(db, user, portfolio_id, strategy_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(strategy, field, value)
    return StrategyRepository(db).save(strategy)


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy(portfolio_id: UUID, strategy_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    strategy = _get_owned_strategy(db, user, portfolio_id, strategy_id)
    StrategyRepository(db).delete(strategy)


@router.post("/{strategy_id}/activate", response_model=StrategyOut)
def activate_strategy(portfolio_id: UUID, strategy_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    strategy = _get_owned_strategy(db, user, portfolio_id, strategy_id)
    strategy.is_active = True
    strategy.paused_until = None  # an explicit user activation overrides an automatic risk-engine pause
    return StrategyRepository(db).save(strategy)


@router.post("/{strategy_id}/deactivate", response_model=StrategyOut)
def deactivate_strategy(portfolio_id: UUID, strategy_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    strategy = _get_owned_strategy(db, user, portfolio_id, strategy_id)
    strategy.is_active = False
    return StrategyRepository(db).save(strategy)


@router.post("/{strategy_id}/evaluate", response_model=StrategyEvaluationOut)
async def evaluate_strategy_now(
    portfolio_id: UUID, strategy_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    """Runs one evaluation pass immediately, outside the worker's normal
    schedule — for testing a strategy's configuration without waiting."""
    strategy = _get_owned_strategy(db, user, portfolio_id, strategy_id)
    result = await StrategyExecutionService(db).evaluate(strategy)
    return result


@router.get("/{strategy_id}/orders", response_model=list[OrderOut])
def list_strategy_orders(portfolio_id: UUID, strategy_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_owned_strategy(db, user, portfolio_id, strategy_id)
    return db.query(Order).filter(Order.strategy_id == strategy_id).order_by(Order.placed_at.desc()).all()
