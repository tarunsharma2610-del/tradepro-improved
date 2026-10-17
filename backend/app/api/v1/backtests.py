from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.backtest import BacktestRun
from app.models.user import User
from app.repositories.backtest_repository import BacktestRepository
from app.repositories.instrument_repository import InstrumentRepository
from app.schemas.backtest import BacktestCreate, BacktestOut, BacktestTradeOut
from app.services.backtest_service import BacktestService

router = APIRouter(prefix="/backtests", tags=["backtests"])


@router.get("", response_model=list[BacktestOut])
def list_backtests(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return BacktestRepository(db).list_for_user(user.id)


@router.post("", response_model=BacktestOut, status_code=status.HTTP_201_CREATED)
async def create_backtest(payload: BacktestCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    instrument = InstrumentRepository(db).get_by_id(payload.instrument_id)
    if instrument is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Instrument not found.")
    if payload.to_date <= payload.from_date:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "to_date must be after from_date.")

    run = BacktestRun(user_id=user.id, status="RUNNING", **payload.model_dump(exclude={"instrument_id"}), instrument_id=instrument.id)
    run = BacktestRepository(db).create(run)

    # Synchronous: fetching + evaluating a few weeks of 5-minute candles is
    # fast pure-Python work once the network call returns. Long enough
    # date ranges to need a background job are a natural next increment,
    # not a redesign — see README known limitations.
    run = await BacktestService(db).run(user.id, run, instrument)
    return run


@router.get("/{backtest_id}", response_model=BacktestOut)
def get_backtest(backtest_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    run = BacktestRepository(db).get_for_user(user.id, backtest_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Backtest not found.")
    return run


@router.get("/{backtest_id}/trades", response_model=list[BacktestTradeOut])
def list_backtest_trades(backtest_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    repo = BacktestRepository(db)
    run = repo.get_for_user(user.id, backtest_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Backtest not found.")
    return repo.list_trades(run.id)


@router.delete("/{backtest_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_backtest(backtest_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    repo = BacktestRepository(db)
    run = repo.get_for_user(user.id, backtest_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Backtest not found.")
    db.delete(run)
    db.commit()
