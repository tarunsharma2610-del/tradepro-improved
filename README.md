# Tradepro Improved

A separate improvement track for Tradepro. The original `Tradepro` repository and its `main` branch remain untouched.

## Safety-first development rules

- Preserve existing functionality while fixing verified defects.
- Keep paper trading as the default mode.
- Keep live trading disabled until broker execution, order reconciliation, duplicate-order prevention, risk limits, and an emergency kill switch are implemented and tested.
- Never commit API tokens, OAuth secrets, passwords, or other credentials.
- Validate changes with automated tests and build checks before deploying.

## Current status

The original source tree has been imported into this repository. Recent improvements include:
- A dashboard at `/` with portfolio summaries and navigation.
- Backend input validation for orders and rejection of invalid broker prices.
- One-time, expiring broker OAuth state backed by a database nonce digest.
- Paper LIMIT-order matching in the worker, using the shared transaction-cost, cash and position accounting.
- Automated backend and frontend checks in GitHub Actions.
- An environment-controlled emergency kill switch blocks new strategy entries when `AUTOMATED_ENTRIES_ENABLED=false`; strategy exits remain enabled.

See [AUDIT_REPORT.md](./AUDIT_REPORT.md) for findings, verification links and remaining work.

## Important trading behavior

- **Paper market orders:** use a current Upstox quote for the simulated fill; the application does not invent a price when the quote is unavailable or invalid.
- **Paper limit orders:** remain pending until the worker checks them during market hours (about every 5 minutes). A BUY can fill when LTP is at or below its limit; a SELL can fill when LTP is at or above its limit. The matcher uses the shared accounting engine, checks available cash / delivery holdings, and users can cancel pending orders from the portfolio order history.
- **Emergency kill switch:** set `AUTOMATED_ENTRIES_ENABLED=false` in the backend environment and restart the API/worker to stop automated strategy entries. Existing strategy exits are intentionally not blocked. This switch does not stop manual paper orders.
- **Live trading:** is **not implemented** by the shared execution service. Setting `TRADING_MODE=LIVE` is not sufficient to make real broker orders happen; do not treat this repository as ready for live trading.
- **Broker OAuth migration:** the new Alembic migration adds one-time OAuth state fields. Back up the database and verify `alembic upgrade head` in staging before deploying to an existing database.
- **Remaining work:** broker order placement/reconciliation, idempotency and duplicate-order protection, a global account-level live-trading kill switch (the existing `AUTOMATED_ENTRIES_ENABLED` switch only blocks automated strategy entries), portfolio-wide risk limits, exchange holiday calendar, Upstox WebSocket market data, expired-contract deactivation after a validated full snapshot, and operational verification of the expanded NSE/BSE/MCX instrument sync still need implementation and verification.
