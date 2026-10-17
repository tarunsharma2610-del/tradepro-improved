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

- **Paper market orders:** use a current Upstox quote for the simulated fill; the application does not invent a price when the quote is unavailable or invalid. The quote parser requires the exact requested instrument key and will not substitute another instrument's price if that key is missing.
- **Paper limit orders:** remain pending until the worker checks them during market hours (about every 5 minutes). A BUY can fill when LTP is at or below its limit; a SELL can fill when LTP is at or above its limit. The matcher uses the shared accounting engine, checks available cash / delivery holdings, and users can cancel pending orders from the portfolio order history.
- **Emergency kill switch:** set `AUTOMATED_ENTRIES_ENABLED=false` in the backend environment and restart the API/worker to stop automated strategy entries. Existing strategy exits are intentionally not blocked. This switch does not stop manual paper orders.
- **Live trading:** is **not implemented** by the shared execution service. Phase 1 has durable intent/idempotency/outbox storage; Phase 2 has pure order/trade normalization, strict local-intent matching, versioned status persistence and idempotent individual fill identity persistence. These do not fetch broker data, aggregate partial fills into account accounting, or submit/cancel orders. Setting `TRADING_MODE=LIVE` is not sufficient to make real broker orders happen; do not treat this repository as ready for live trading.
- **Portfolio settings:** each portfolio has a manual settings form for renaming and optional risk controls: maximum daily realized loss, estimated open exposure, per-order value, simultaneous open/pending positions and orders per day. Controls are disabled until enabled. Limits are checked for paper manual and strategy orders; closing/reducing orders are allowed. Exposure is a conservative cost-basis estimate, not broker margin.
- **Upstox WebSocket:** authenticated endpoints are POST /api/v1/market-data/stream, GET /api/v1/market-data/stream, and DELETE /api/v1/market-data/stream. The portfolio order form has Start/Stop controls for the selected instrument and displays fresh LTP updates. Subscribe only to active catalog keys. Streams are process-local and disappear on API restart; use one API worker until a shared stream/cache layer is added. ExecutionService uses fresh stream ticks when available and otherwise falls back to REST.
- **Instrument sync:** admin POST /api/v1/instruments/sync now reconciles absent/expired instruments only after a completeness gate passes. A separate GitHub Actions workflow successfully downloaded the real official Upstox master and synced it into temporary in-memory SQLite (123,930 active instruments); it never touched production.
- **Migration/deployment:** the portfolio-risk migration is CI-tested on clean SQLite. Back up the deployed database and verify alembic upgrade head in staging before deploying to an existing database.
- **Remaining work:** broker reads/worker and full reconciliation (including fill-vs-intent economic validation, partial-fill aggregation/accounting and out-of-order updates), live order placement, a global account-level live-trading kill switch, exchange holiday calendar, real authenticated WebSocket verification with a user OAuth session, multi-worker stream sharing, and staging migration verification. Live trading is not implemented and must remain disabled.


## Verified status — 17 October 2026
- Latest backend CI after documentation updates: [run 39039714203](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039714203) — **203 tests passed, 1 warning**; clean SQLite Alembic migration verification passed.
- Safety regression coverage includes exact-instrument quote matching, portfolio order-count cap, incomplete instrument snapshot rejection, WebSocket silence reconnect, and V3 authorization URL validation.
- Official Upstox instrument master was downloaded and synchronized into a disposable in-memory SQLite database: **123,930 active instruments** ([verification workflow](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037390129)). This did not modify production data.
- Frontend TypeScript/build verification for the stream controls passed ([run 39037642093](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037642093)).
- **Not production-ready for live trading:** real OAuth WebSocket verification, multi-worker stream sharing, backup-safe staging migration, idempotent live submission and broker reconciliation remain open. Keep live trading disabled; no live orders have been submitted.


## Live-order idempotency and reconciliation — design review (17 October 2026)

The approved live-trading design is now in **Phase 1 implementation** (durable records/repository safeguards only). See [`LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`](LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md) for the detailed architecture, implementation sequence and acceptance tests.

The design requires durable idempotency keys, payload-hash conflict detection, a committed intent/outbox before broker I/O, explicit UNKNOWN state after ambiguous submissions, broker order/trade reconciliation, fill deduplication, risk rechecks and an account-level emergency stop. Upstox order tags are for correlation/history lookup; the project does not assume they guarantee broker-side idempotency.

**Live broker submission and reconciliation are still not implemented.** Phase 1 adds only durable records/repository safeguards; the shared execution service still creates PAPER orders, live submission remains disabled, no production migration ran and no real orders were submitted. Do not set `TRADING_MODE=LIVE` or connect the paper path to the live broker method. Latest Phase 1 code CI: [run 39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046), 215 tests passed, 1 warning; simultaneous idempotency requests passed against PostgreSQL 16, and Alembic upgrade → downgrade → re-upgrade passed on both SQLite and PostgreSQL 16.


## Project roadmap
See [ROADMAP.md](ROADMAP.md) for the phased implementation plan, verified status, release gates and the evidence required before live trading can be considered.


## Live-order safety development status — 17 October 2026
- Phase 1 durable intent/idempotency storage and Phase 2 pure broker-order normalization + strict intent-matching helpers are CI-tested.
- Latest Phase 2 matching test checkpoint: [GitHub Actions run 39050424898](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050424898), 255 passed, 1 warning, including SQLite/PostgreSQL 16 reversible migration checks.
- The helpers do not make broker API calls and do not persist reconciled states or import fills. Live order submission/cancellation remains unavailable and disabled.


### Phase 2 reconciliation repository update — 17 October 2026
- A repository-only versioned transition now persists a validated normalized status and an audit event atomically. It rejects stale versions and invalid regressions, and duplicate same-state observations do not add duplicate audit rows.
- Cancel/fill races can be represented if subsequent broker trade evidence confirms execution after a cancel. This code does not fetch that evidence itself.
- Latest verified test checkpoint: [run 39050941218](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050941218), 261 passed, 1 warning. Broker reads, fill ingestion and live order placement/cancellation remain unimplemented.


### Phase 2 individual fill identity checkpoint — 17 October 2026
- Pure Upstox trade normalization and repository-only idempotent fill identity persistence are implemented and CI-tested. Identical duplicate trades are ignored; conflicting payloads are quarantined as conflicts. The repository does not fetch broker trades or update positions/P&L.
- Latest code/test run: [39052203329](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052203329) — 274 passed, 1 warning, with SQLite/PostgreSQL 16 migration checks.
- Live trading remains unavailable and disabled.


### Phase 2 fill-to-intent validation checkpoint — 17 October 2026
Linked fill persistence now requires the same broker order ID and exact instrument, side, product and order type as the intent snapshot; it enforces order quantity ceilings and limit-price protection. [Run 39052939770](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052939770) passed 279 tests, 1 warning, with SQLite/PostgreSQL 16 migration checks. It still does not fetch broker data or update live positions/P&L.


### Phase 2 unmatched-fill recovery foundation — 17 October 2026
A previously unmatched fill can now be linked to a local intent later, but only after broker order ID, account, instrument, side, product, order type, quantity and limit-price checks pass. The link and audit event are atomic; repeat linking is a no-op. [Run 39053352921](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053352921) passed 281 tests, 1 warning. No broker polling or live accounting is implemented.


### Phase 2 out-of-order status/fill checkpoint — 17 October 2026
Order-state persistence now resolves broker status against already-persisted individual fill evidence before applying a transition. A stale OPEN/PENDING status cannot erase known partial fills; a partial fill followed by cancellation is represented separately; contradictory quantities/statuses are quarantined for review. Exact code checkpoint [run 39056392873](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056392873) passed **294 tests, 1 warning**, including SQLite/PostgreSQL 16 migration checks. The read-only broker worker remains design-only; no live broker reads, order actions or accounting updates are implemented. See [READ_ONLY_RECONCILIATION_WORKER_DESIGN.md](READ_ONLY_RECONCILIATION_WORKER_DESIGN.md).


### Read-only Upstox reconciliation client — 17 October 2026
Added a separate fixed-path GET-only client for order book, details, history and per-order trades. It exposes no order-write methods and sanitizes upstream failures. Mocked contract tests passed in [run 39056868434](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056868434): 309 passed, 1 warning, with SQLite/PostgreSQL 16 migration checks. The worker has not been implemented or invoked; no real broker requests or order actions occurred.


### Reconciliation lease foundation — 17 October 2026
Added a durable one-per-broker-connection lease with atomic claim, expiry/reclaim, renewal and stale-owner protection. Exact CI run [39057273255](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39057273255) passed 318 tests, 1 warning, including reversible SQLite/PostgreSQL 16 migrations. The lease is not yet connected to a worker; no broker polling has started.


### Latest Phase 2 checkpoint — leased read-only reconciliation worker
`backend/app/services/live_order_reconciliation_worker.py` now provides an explicit on-demand, read-only reconciliation pass. It validates the user-owned Upstox connection and usable token, claims a per-connection lease, reads the order book and daily trades through the fixed GET-only client, uses bounded transient retries, matches local intents, and persists/deduplicates individual trade identities. It never places/modifies/cancels orders and never updates local portfolio accounting. The worker is not scheduled or wired to an API route; tests use mocks only. Latest CI [run 39058734080](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39058734080) passed **338 tests, 1 warning**, including SQLite/PostgreSQL 16 migration checks. Remaining: validate historical-day/session/pagination semantics, persist operator-facing summaries/manual-review cases, add crash-boundary tests, and only then consider a separately approved read-only sandbox check. Live submission remains disabled.
