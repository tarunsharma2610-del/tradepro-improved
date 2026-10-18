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
- **Remaining work:** a complete live broker-order lifecycle and restart-safe reconciliation; broker-side idempotency and portfolio-wide exposure controls; account-level live kill-switch/circuit-breaker is covered by PostgreSQL concurrency tests and checked by the read-only preflight coordinator, but that coordinator remains unregistered from routes/workers; authentication/authorization and operator audit visibility still need review; full instrument-master support beyond NSE equities, tick-size unit normalization and derivative lot/margin accounting; exchange holiday handling; WebSocket market data; and production TLS/staging verification. Manual and strategy retry keys are implemented for paper/strategy paths. The Upstox adapter now uses official V3 place/modify/cancel endpoints, but these methods are not wired to the UI or execution service; the separate live service is not implemented. A PAPER-only gate, paper-order cap and automated-entry kill switch exist, but they are not a complete live risk system.


## Persistent project instructions and progress

- Read [`PROJECT_INSTRUCTIONS.md`](PROJECT_INSTRUCTIONS.md) before making changes.
- Read [`PROGRESS.md`](PROGRESS.md) at the start of every continuation; update it after every tested and committed task.


- Live execution design and prerequisites: [`LIVE_ORDER_STATE_MACHINE.md`](LIVE_ORDER_STATE_MACHINE.md). Additive broker child-order/trade-ID schema exists, but is not wired into execution; this is not an enabled live-order feature.


## Development status and roadmap

See [`MASTER_ROADMAP.md`](MASTER_ROADMAP.md) for the current implementation sequence, verification gate, safety constraints and release blockers. Live trading is not ready and remains disabled.


## Broker trade intake status (18 October 2026)

The safety branch includes a connection-scoped `BrokerTradeRecord` intake table and `BrokerTradeIngestionService` with ownership, child-order mapping, validation and replay protection. These records are **staged broker trade data, not accounted executions**: ingestion does not change balances, positions, P&L or order state, and is not wired to a live submission path. The account-wide safety service is also present but remains unregistered from order submission. CI run [#611](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39121063921) passed on code/test SHA `3e73efd441315294970cb652ddeb9b37b00b67b9`: 398 passed, 4 skipped, 1 warning; SQLite and PostgreSQL 16 migration upgrades passed, and dedicated PostgreSQL concurrency tests passed (4 passed). The read-only preflight coordinator also checks the persistent account safety decision before broker snapshots; it remains unregistered from order routes/workers. See `PROGRESS.md` and `AUDIT_REPORT.md` for the current checkpoint and remaining verification.


The broker-intake migration-backfill regression and the account-safety migration graph are covered by the successful CI run above. This does not constitute staging/production migration approval; back up and verify any existing deployment database separately.
