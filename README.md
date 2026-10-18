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


### Safety-control security review (18 October 2026)

Before any safety-control API is designed, read [SECURITY_CONTROL_ENDPOINT_AUDIT.md](SECURITY_CONTROL_ENDPOINT_AUDIT.md). The static review found that authentication and basic ownership/admin checks exist, but operator audit visibility and safety-specific permissions are not yet implemented; step-up authentication, CSRF policy, atomic state/audit persistence, strict redaction and endpoint-level security tests remain open. No safety-control route is registered, and live order submission remains disabled.


### Order-path safety review (18 October 2026)

See [ORDER_ENTRY_PATH_INVENTORY.md](ORDER_ENTRY_PATH_INVENTORY.md) for the current manual, strategy, worker and broker-write path map. The shared order service remains PAPER-only. Live preflight and recovery are not registered as submission routes, and the live recovery foundation does not yet compose the account-safety-aware coordinator. No live order route is ready or enabled.

## Phase 2 checkpoint — authenticated safety control endpoints (18 October 2026)

- Added and registered `backend/app/api/v1/safety.py` with three user-scoped endpoints: `GET /api/v1/safety/status` requires `safety.status.read`; `POST /api/v1/safety/kill-switch/trip` requires `safety.kill_switch.trip`, cookie-Origin validation and an `Idempotency-Key`; `POST /api/v1/safety/kill-switch/reset` requires `safety.reset`, a fresh user-bound password+TOTP step-up token, cookie-Origin validation, an idempotency key, and a required `expected_version`.
- Status reads only the authenticated user's Upstox account safety state. Missing state is reported as blocked/unsafe without initializing or creating a state. Trip initializes missing state in the safe/tripped state before applying the idempotent trip. Reset delegates to the existing transaction-safe service and returns conflict if state/version/health requirements are not met.
- Reset deliberately does **not** accept a client assertion that a health check passed. The existing service requires a recent persisted `HEALTH_CHECK_PASSED` event, zero consecutive broker errors, and matching expected state version. No new public health-check endpoint was added because a caller-supplied “passed” flag would be unsafe without real broker/session/account snapshot validation.
- Added HTTP regression tests for permission denial, safe missing-state response, trip behavior, required idempotency key, reset MFA denial, reset blocked without a fresh successful health check, and cookie-Origin rejection. **These tests have not been executed in this environment.** GitHub Actions lookup exposed no PR-triggered run for the latest test commit and combined status was empty; the connector's workflow-run lookup filters to PR-triggered runs, so this is not proof that no push-triggered run exists. Exact-head test status remains unverified.
- Relevant commits: safety route/import cleanup `267da864b5187cfad91ac68b76ba86cf06b7848f`; schema `01f0deb4949cd13072fb2feda9924e0a97eaf5cf`; router registration `fc95e748197be9e8848c990f55079fbd8afc4a30`; endpoint tests `3ae21dac71edb449835124f99794f510c8b80761`.
- Review caveat: the existing `GET /api/v1/admin/safety/audit` still reads legacy `AuditLog` rows with `safety.*` action names; the durable state-transition history is in `LiveAccountSafetyEvent`. Before treating operator audit visibility as complete, update that endpoint to read the immutable event table and scope by the associated state owner and authorized actor.
- Remaining gates: run and fix CI on the current branch head; fix the safety audit endpoint's event source; perform security review of the grant/reset token purpose boundaries; add negative HTTP tests for every route and error path; verify atomic state/event concurrency at endpoint level; implement the central broker-write service and enforce it across API, strategy worker, recovery and adapter paths. Keep `TRADING_MODE=PAPER`, `LIVE_ORDER_SUBMISSION_ENABLED=false`, PR #1 draft/open/unmerged, and original `Tradepro` untouched. Phase 2 is incomplete.


## Superseding Phase 2 checkpoint — immutable safety audit source (18 October 2026)

- Updated `GET /api/v1/admin/safety/audit` to read `LiveAccountSafetyEvent` joined to `LiveAccountSafetyState`, rather than the legacy `AuditLog` table. Tenant scoping is performed in SQL using the authenticated user's state ownership before counting and pagination; callers cannot select another user/state. Output omits idempotency keys and request fingerprints and exposes only the safety event fields needed for audit review.
- Reworked the tenant-isolation/pagination HTTP test to seed durable safety events for two different account owners and a non-safety legacy audit row. It checks that only the authenticated tenant's immutable safety events are returned and sensitive replay metadata is not serialized.
- Commits: endpoint `cd68384c48a98f2bd2ded054f37bb04d24885b12`; regression test `7913f821a7ac194c537adf911a4ef39ba4410e41`.
- Verification status: exact-head CI/status lookup returned no runs/statuses for the latest test commit. Tests have **not** been run in this environment; treat this change as committed but unverified until GitHub Actions runs against the current branch head. No live broker write was called.
- Next: verify/fix current-head CI; then review reset/idempotency and endpoint transaction behavior, followed by central broker-write boundary implementation and enforcement across API, strategy workers, recovery/retry and adapter paths. Phase 2 remains incomplete. Keep PAPER mode, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.
