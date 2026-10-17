# Change Log — Tradepro Improved

## 2026-10-17 — audit and safety branch

### Existing functionality retained
- Paper order placement, paper LIMIT matching/cancellation, position accounting and transaction-cost calculation.
- Strategy scoring, trailing-stop evaluation, strategy-level daily-loss controls and automated-entry kill switch.
- Existing Upstox OAuth, encrypted per-user credentials, quotes, historical candles, order-status/order-book/positions/holdings adapter methods.
- Existing frontend pages, API routes, model/table structure and migration history.
- Original `Tradepro` repository and its `main` branch were not modified.

### Changes
1. Added `REQUIREMENTS_AUDIT.md` to map the specification to existing code and document remaining gaps.
2. Added a fail-closed check in `ExecutionService.place_order` so the existing paper-only service refuses requests if `TRADING_MODE` is anything other than `PAPER`. This is a safety gate, not live execution.
3. Added `test_live_mode_fails_closed_before_creating_order`.
4. Corrected `UpstoxAdapter.place_order` to use the current documented HFT order-placement host (`https://api-hft.upstox.com/v2/order/place`) instead of the deprecated host.
5. Added `test_place_order_uses_current_upstox_hft_host_without_network`, which mocks the HTTP helper and verifies URL/payload without contacting Upstox.
6. Added `HANDOVER.md` and updated `AUDIT_REPORT.md` with findings, release gates and next priorities.

### Verification
- The fail-closed guard and its test passed the backend GitHub Actions workflow before the adapter URL correction.
- GitHub Actions passed for the code-bearing commit containing the adapter correction and mocked regression test: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39027387591.
- The test suite uses mocks/SQLite and does not verify real broker execution.
- No real broker orders were submitted.

### Additional improvement — portfolio daily-loss guard
7. Extended the existing risk engine to aggregate today's realized losses across every fill in a portfolio, including manual orders, and block new automated strategy entries when losses reach configurable PORTFOLIO_DAILY_LOSS_LIMIT_PCT of starting virtual capital (default 2%; set to 0 to disable).
8. Added regression coverage below, at, and above the threshold. This only gates automated strategy entries; it does not guard manual order submission or provide a live-trading risk system.

### Remaining blockers
- Durable order idempotency and broker reconciliation.
- Portfolio-wide exposure, max-order-value/position-size controls and broker-error circuit breaker.
- Complete live-order lifecycle (broker-confirmed partial/full fills, cancellation/modification, timeouts and restart recovery).
- Verified full instrument-master sync and WebSocket feed.
- Market-hours/holiday handling, operational monitoring and production TLS/staging verification.
- Live trading remains not ready and must stay disabled.

### Additional improvement — durable request idempotency
9. Added optional client `idempotency_key` to order requests and persisted it with a database-enforced unique constraint per portfolio.
10. Repeated requests with the same key and identical order payload return the existing order; reusing a key for a different payload is rejected. Concurrent duplicate inserts are arbitrated by the database constraint.
11. Added regression tests for sequential retries and key/payload mismatch. This reduces duplicate submissions but is not a substitute for broker-side idempotency and post-timeout broker reconciliation.

### Additional improvement — single-order value cap
12. Added `MAX_ORDER_VALUE_PCT_OF_VIRTUAL_CAPITAL` (default 25%) to reject paper orders whose estimated notional exceeds the configured percentage of starting virtual capital. LIMIT orders use their limit price; MARKET orders use the fetched quote. Set to 0 to disable.
13. Added tests for both LIMIT and MARKET order rejection above the cap. This is a per-order notional guard, not a portfolio exposure limit; derivative multipliers/lot-size data still require verification.
