from pydantic import BaseModel


class PlatformStatsOut(BaseModel):
    total_users: int
    total_portfolios: int
    total_active_strategies: int
    total_strategies: int
    total_news_items: int
    total_backtest_runs: int
