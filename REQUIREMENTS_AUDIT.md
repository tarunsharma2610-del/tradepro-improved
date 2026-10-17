# Tradepro Improved — Requirements Audit
Audit date: 2026-10-17
Audit target: `main` baseline plus the isolated safety branch where noted.
Original repository `Tradepro`: untouched.

## Scope and inventory
The recursive Git tree returned 172 files (129 Python, 21 TypeScript/TSX, and configuration, migration, documentation and deployment files). The review covered the backend API/routes, models and repositories, trading and strategy services, Upstox adapter, authentication/OAuth, middleware, all backend test modules, frontend routes/components, migrations, CI, and deployment files. This is a static code review plus review of recorded GitHub Actions results; it is not a production end-to-end test.

## Requirement matrix

Status meanings: **Complete in current scope** means existing implementation and relevant automated coverage were found; **Partial** means useful code exists but the complete requirement is not met; **Missing** means no implementation was found; **Verify in staging** means static inspection/CI cannot prove operational behavior.

| Requirement | Status | Existing evidence / finding | Change decision |
|---|---|---|---|
| Preserve separate improved repository | Complete | `tradepro-improved` is separate; changes are confined to `safety/fail-closed-trading-mode`. | Keep original `Tradepro` untouched. |
| Backend API and user/portfolio isolation | Complete in tested scope | Authenticated routes and ownership checks; tests cover cross-user portfolio, strategy, backtest and order access. | Retain; add regressions if shared paths change. |
| Password/MFA/session security | Partial | Argon2id password hashes, JWT access/refresh tokens, TOTP MFA, httpOnly cookie use and rate limits exist. Refresh-token revocation/session inventory is not present in the reviewed model. | Do not rewrite; review only if a requirement or defect demands it. |
| Upstox OAuth and credential storage | Mostly complete; staging verification required | Credentials are encrypted at rest and masked in responses; OAuth state is signed, bound to user/connection, expires, and uses a one-time DB nonce. Access-token expiry is checked. Real broker login was not tested here. | Preserve existing implementation; keep OAuth tests. |
| Real quotes and historical candles | Partial | Upstox LTP and historical candle methods exist; paper orders reject absent/invalid quotes instead of inventing prices. WebSocket streaming is a stub. | Keep existing quote/candle path; implement streaming only with verified API docs and tests. |
| Instrument master | Partial | `InstrumentService.sync_from_upstox` has a best-effort compressed-file path but only imports NSE equities and explicitly says URL/schema need verification. The adapter's `sync_instruments` method is a stub. Seed list contains ten equities. | Reuse service; verify official file schema before extending to derivatives/exchanges. |
| Paper order placement and accounting | Implemented with operational limitations | Shared `ExecutionService` uses real quotes for simulated market fills; pending paper LIMIT matching, cancellation, cash/holding checks, position math and transaction-cost components exist with tests. | Preserve; never route paper orders to the broker. |
| Paper/live isolation | Partial; safety guard now added on branch | Baseline service always writes `trading_mode="PAPER"`; `TRADING_MODE` previously only warned at startup. Branch adds a fail-closed check in `ExecutionService.place_order` and a regression test. CI passed on PR branch. This is not live execution. | Keep guard while no separate live execution service exists; review its effect on PAPER orders if environment is set to LIVE. |
| Live order lifecycle | Partial; read-only status check foundation added | Adapter has broker `place_order`, `get_order_status`, `get_order_book`, `get_positions`, and `get_holdings` methods. The safety branch now stores optional broker order metadata and adds a read-only service to check a known LIVE order's broker status after ownership/session/order-ID validation. It validates any returned broker order ID and records the raw status without changing local FILLED/CANCELLED state or cash/positions. An authenticated read-only broker-status endpoint is now exposed for orders that already have a stored broker ID. Live placement is still absent; no automatic reconciliation of partial fills, cancellation, timeouts or restart recovery exists. | Build and review a separate live lifecycle; only map statuses and account for fills after verified payload contracts and reconciliation tests. Do not replace paper execution. |
| Duplicate-order prevention/idempotency | Partial for API request retries; missing for broker lifecycle | The safety branch adds an optional client idempotency key, persisted with a unique (portfolio_id, idempotency_key) constraint. Same-key/same-payload retries return the prior order; key reuse with a changed payload is rejected. Broker-side idempotency and timeout/restart reconciliation are still missing. | Keep this guard; implement broker correlation and reconciliation before live execution. |
| Risk controls | Partial | Strategy-level realized daily-loss checks and an automated-entry kill switch exist. The safety branch adds a portfolio-wide realized daily-loss guard for automated strategy entries (default 2%) and a single-order notional cap for paper orders (default 25% of starting virtual capital), both configurable. The order cap uses price × quantity as represented by current paper accounting; derivative multipliers/lot sizes are not yet verified. Neither is a complete live risk system. Portfolio-wide exposure and a broker-error circuit breaker remain missing. | Keep controls server-side; add exposure/circuit-breaker and verify derivative contract sizing before live use. |
| Strategy engine/scheduler | Partial | Five-indicator scoring, trailing-stop logic, worker cadence and isolated per-strategy sessions exist with tests. Exchange holiday calendar and protection against repeated/overlapping strategy evaluations are incomplete. | Preserve engine; add concurrency/risk safeguards based on a demonstrated gap. |
| Orders/P&L/costs/analytics/backtesting | Partial to complete by feature | Decimal-based cost calculation, position math, backtests, realized analytics and tests exist. Live broker-confirmed fills/unrealized P&L are not supported because live execution is absent. Cost rates and live-market assumptions require periodic verification. | Retain tested paper/backtest logic; do not imply live-accounting parity. |
| Frontend workflows | Partial | Dashboard, portfolios, orders, strategies, backtests, analytics, broker settings, notifications and admin pages exist. Dashboard explicitly says live trading is not enabled; no live mode workflow/confirmation UI exists. | Do not add duplicate pages; add UI only after backend live workflow is safe. |
| Audit logs and operational visibility | Partial | Audit log writes exist for important auth/broker/settings events; no complete order lifecycle audit/reconciliation dashboard or circuit-breaker status exists. | Extend existing logging when execution lifecycle is implemented. |
| Database migrations | Existing chain; staging verification required | Six ordered Alembic revisions exist. CI workflow runs migration upgrade on SQLite; production database upgrade has not been verified. | Use forward-only, tested migrations; back up and verify staging first. |
| Deployment and CI | Partial | GitHub Actions cover backend tests/migrations and frontend typecheck/build. Compose deploys Postgres, Redis, backend, worker, frontend and Nginx. Nginx is HTTP-only until TLS setup; production configuration still needs environment-specific verification. | Keep CI; validate deployment and TLS before OAuth/live use. |

## Baseline and verification evidence
- Main branch's existing audit records a previous backend run of 167 passing tests and a successful frontend typecheck/build. These are historical results.
- The safety branch PR's GitHub Actions backend workflow completed successfully, including pytest and SQLite Alembic upgrade: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39026925132.
- This backend workflow result does not prove a real Upstox session, market feed, broker order, production database, TLS configuration, or live-trading behavior.
- No real broker orders were placed.

## Prioritized change plan
1. Keep the fail-closed PAPER-only service guard and its regression test until a separate, reviewed live service exists.
2. Completed first adapter correction: place-order URL updated to the current official HFT host, with a mocked regression test. Await CI confirmation. Continue reviewing other adapter contracts against official docs; never place live orders for tests.
3. Client request idempotency and a read-only broker status-check foundation are present; next persist broker IDs from a separately reviewed live submission service and add restart-safe reconciliation of fills/cancellations.
4. Add portfolio-wide exposure and broker-error circuit-breaker controls to the existing risk engine; verify derivative contract sizing before extending order-value controls to live execution.
5. Verify instrument-master URL/schema and expand supported instruments only from official Upstox data.
6. Implement live execution in a separate service that uses existing adapter/models, requires explicit enablement/confirmation, broker-confirmed statuses and reconciliation, and has a hard emergency stop.
7. Add mode-aware UI only after backend semantics are established.
8. Run backend suite, migrations, frontend checks, and integration tests after each relevant change. Document all unrun tests and remaining limits.

## Retained unchanged after review
- Existing paper order/accounting engine, order and position models, cost engine, strategy scoring, backtest engine, notification integrations, OAuth/credential encryption, existing pages, and current migration history.
- Existing adapter methods for broker order/status/book/positions/holdings are to be reused where correct, not duplicated.
- The original `Tradepro` repository and its `main` branch remain untouched.

## Release gate
Live trading is **NOT READY**. No live order placement should be enabled until current official API contracts, durable idempotency, risk limits, broker-confirmed fills, cancellation/timeout/restart reconciliation, credential/session controls, kill switch, audit trail, tests, deployment controls, and required broker/compliance authorization have been verified.
