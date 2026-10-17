# Tradepro Improved

A separate improvement track for Tradepro. The original `Tradepro` repository and its `main` branch remain untouched.

## Safety-first development rules

- Preserve existing functionality while fixing verified defects.
- Keep paper trading as the default mode.
- Keep live trading disabled until a separate broker execution lifecycle, broker-side idempotency, broker reconciliation, live-specific risk controls, an account-level emergency stop, and regulatory prerequisites are verified.
- Never commit API tokens, OAuth secrets, passwords, or other credentials.
- Validate changes with automated tests and build checks before deploying.

## Current status

The original source tree has been imported into this repository. Recent improvements include:
- A dashboard at `/` with portfolio summaries and navigation.
- Backend input validation for orders and rejection of invalid broker prices.
- One-time, expiring broker OAuth state backed by a database nonce digest.
- Paper LIMIT-order matching in the worker, using the shared transaction-cost, cash and position accounting.
- Atomic paper fills: order status, portfolio cash, aggregate position and execution record commit together.
- Strategy-owned position allocations and strategy-specific realized P&L, separate from aggregate portfolio positions.
- Fail-closed rejection of futures/options until verified derivative contracts, lot/tick sizing and contract risk controls are implemented.
- Automated backend and frontend checks in GitHub Actions.
- An environment-controlled emergency kill switch blocks new strategy entries when `AUTOMATED_ENTRIES_ENABLED=false`; strategy exits remain enabled.

See [AUDIT_REPORT.md](./AUDIT_REPORT.md) for findings, verification links and remaining work.

## Important trading behavior

- **Paper market orders:** use a current Upstox quote for the simulated fill; the application does not invent a price when the quote is unavailable or invalid.
- **Paper limit orders:** remain pending until the worker checks them during market hours (about every 5 minutes). A BUY can fill when LTP is at or below its limit; a SELL can fill when LTP is at or above its limit. The matcher uses the shared accounting engine, checks available cash / delivery holdings, and users can cancel pending orders from the portfolio order history.
- **Emergency kill switch:** set `AUTOMATED_ENTRIES_ENABLED=false` in the backend environment and restart the API/worker to stop automated strategy entries. Existing strategy exits are intentionally not blocked. This switch does not stop manual paper orders.
- **Live trading:** is **not implemented** by the shared execution service. Setting `TRADING_MODE=LIVE` is not sufficient to make real broker orders happen; do not treat this repository as ready for live trading.
- **Broker OAuth migration:** the new Alembic migration adds one-time OAuth state fields. Back up the database and verify `alembic upgrade head` in staging before deploying to an existing database.
- **Remaining work:** a complete live broker-order lifecycle and restart-safe reconciliation; broker-side idempotency and evaluation-level retry keys for strategy scheduling; portfolio exposure limits and a broker-error circuit breaker; full instrument-master support beyond NSE equities, tick-size unit normalization and derivative lot/margin accounting; exchange holiday handling; WebSocket market data; and production TLS/staging verification. Client idempotency is now integrated in the manual order UI; strategy entries have a position-allocation/locking guard. A PAPER-only gate, paper-order cap and automated-entry kill switch exist, but they are not a complete live risk system.
