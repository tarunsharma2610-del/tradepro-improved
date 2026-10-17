from uuid import UUID

from sqlalchemy.orm import Session

from app.models.backtest import BacktestRun
from app.models.backtest_trade import BacktestTrade


class BacktestRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_user(self, user_id: UUID) -> list[BacktestRun]:
        return self.db.query(BacktestRun).filter(BacktestRun.user_id == user_id).order_by(BacktestRun.created_at.desc()).all()

    def get_for_user(self, user_id: UUID, backtest_id: UUID) -> BacktestRun | None:
        return self.db.query(BacktestRun).filter(BacktestRun.id == backtest_id, BacktestRun.user_id == user_id).first()

    def create(self, run: BacktestRun) -> BacktestRun:
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def save(self, run: BacktestRun) -> BacktestRun:
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def list_trades(self, backtest_run_id: UUID) -> list[BacktestTrade]:
        return (
            self.db.query(BacktestTrade)
            .filter(BacktestTrade.backtest_run_id == backtest_run_id)
            .order_by(BacktestTrade.candle_index)
            .all()
        )

    def add_trades(self, trades: list[BacktestTrade]) -> None:
        self.db.add_all(trades)
        self.db.commit()
