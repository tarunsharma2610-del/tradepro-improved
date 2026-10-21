<!-- Phase 3 docs sync: df8b73a2971cbcee949efa14e98bc16a070bf093 -->

> **Documentation synchronization:** commit [df8b73a2971cbcee949efa14e98bc16a070bf093](https://github.com/tarunsharma2610-del/tradepro-improved/commit/df8b73a2971cbcee949efa14e98bc16a070bf093) synchronized the Phase 3 checkpoint across all 16 top-level project Markdown documents. Verify the exact HEAD's CI before treating the documentation checkpoint as fully green.

## Current Phase 3 checkpoint — 21 October 2026

- **Latest verified code/test HEAD:** `3963c2bf4e6ffe2bb33d327b10e2995cd243d003`. Exact-head [Backend CI run 39607630055](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39607630055) passed **484 tests, 1 warning in 29.34s**; the broker-write boundary guard passed, and SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed.
- New Phase 3 guard: broker-reported live-fill charge references are trimmed for storage and rejected when longer than the `Execution.charge_reference` 200-character column limit. This prevents a predictable storage error from being misreported as a concurrent promotion conflict. Regression coverage is included in the 484-test result.
- The existing Phase 3 safety gates remain active: replay must match the accounted fill and exact charge evidence; only broker-reported, internally consistent charges with a non-empty audit reference are accepted; durable staged trade quantities must match broker-confirmed child fills before promotion; exchange-time ambiguity/out-of-order fills fail closed; paper positions and cash remain isolated.
- **Phase 3 remains in progress, not complete.** Remaining review includes coordinator/identity boundaries, charge provenance/allocation semantics, full partial-fill and crash/restart acceptance criteria, and any explicitly selected bridge design. Keep `BrokerFillIdentity` separate from manual `BrokerTradeRecord` unless a reviewed Phase 3 design explicitly authorizes a narrow bridge.
- Live broker submission, automatic accounting promotion, and automatic scheduling remain disabled. The original `tarunsharma2610-del/Tradepro` repository remains untouched. Phase 2 remains closed.
- This checkpoint describes the verified code commit above. The documentation synchronization commit will trigger its own CI; do not treat that documentation commit as green until its exact-head run passes. Older checkpoint entries below are historical audit trail, not current status.

---

## Current verified checkpoint — 21 October 2026

- **Last verified code/test checkpoint:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 reversible migration checks.
- **Last verified documentation checkpoint before this status refresh:** `391dfefc9580abf9537ee659877578033baae4fd`; exact-head backend CI [run 39568264419](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39568264419) passed.
- The Phase 2 audit covers the dependency/port matrix, broker-fill workflow boundary, idempotency and rollback, reconciliation crash recovery, transaction-level lease fencing, slow persistence, 20 concurrent expiry-boundary renewal/reclaim races, and official Upstox current-day API semantics.
- Official Upstox V2 [order-book](https://upstox.com/developer/api-documentation/get-order-book/) and [get-trades-for-day](https://upstox.com/developer/api-documentation/get-trade-history/) endpoints are current-day endpoints without documented pagination parameters. Historical trades use a separate [paginated API](https://upstox.com/developer/api-documentation/get-historical-trades/); it is not wired into the Phase 2 worker.
- **Phase 2 technical checklist is complete.** Before any Phase 3 work, require a passing exact-head CI run for the then-current `main` and explicit user approval; never infer a later commit is green from an earlier run.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. The original `Tradepro` repository remains untouched.

------

## Current verified checkpoint — 21 October 2026

- **Latest CI-verified `main` HEAD:** `7798f03200ba823d51bdd359539594b38e9830e1`; exact-head backend CI [run 39567592850](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567592850) passed.
- **Latest code/test checkpoint:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, the broker-write boundary guard and SQLite/PostgreSQL 16 reversible migration checks.
- The slow-persistence/lease-race audit is complete: the PostgreSQL row-lock test proves reclaim waits while a fenced write transaction is open; `test_postgres_high_volume_expiry_races_never_resurrect_stale_lease` passed 20 concurrent expiry-boundary renewal/reclaim races. Expired owners cannot renew, and ownership generation/token advance is verified.
- Official Upstox V2 order-book and get-trades-for-day endpoints are current-day endpoints without documented pagination parameters. Historical trades are a separate paginated API; that API is not wired into the Phase 2 worker.
- **Current task:** synchronize the remaining historical architecture/roadmap/reference-audit notes. This documentation commit needs its own exact-head CI and a final stale-status scan before Phase 2 is formally closed. Phase 3 remains blocked until then.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. The original `Tradepro` repository remains untouched.

------

# Tradepro Improved

A separate improvement track for Tradepro. The original `Tradepro` repository and its `main` branch remain untouched.

## Safety-first development rules

- Preserve existing functionality while fixing verified defects.
- Keep paper trading as the default mode.
- Keep live trading disabled until broker execution, order reconciliation, duplicate-order prevention, risk limits, and an emergency kill switch are implemented and tested.
- Never commit API tokens, OAuth secrets, passwords, or other credentials.
- Validate changes with automated tests and build checks before deploying.

## Current Phase 2 checkpoint — 21 October 2026

- Reconciliation crash recovery and transaction-level lease fencing have passed backend CI on the recorded checkpoint (470 tests, 1 warning, broker-write guard, SQLite/PostgreSQL 16 migration cycles).
- Latest test commit [e56bf4c66f74b875a3ba8fe388138a9d688dd1e2](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e56bf4c66f74b875a3ba8fe388138a9d688dd1e2) adds failed-commit rollback coverage. Exact-head backend CI [run 39564568154](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39564568154) passed 471 tests (1 warning), broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles. Documentation HEAD `adb69aeb05b70ba4fa9095fc73d9dea033d31eec` also passed backend CI [run 39565251793](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39565251793).
- Phase 2 is in final documentation verification: code/test HEAD `00ee9bad0e962d92244da6f63da1e46ba058ad6f` passed [CI run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) with 472 tests, source guard and SQLite/PostgreSQL 16 migration checks. The documentation sync must pass its own exact-head CI before closure. Intent-based BrokerFillIdentity and manual BrokerTradeRecord remain separate; live submission, automatic accounting promotion and automatic scheduling remain disabled. See MASTER_ROADMAP.md and SAFETY_BRANCH_PORT_MATRIX.md for authoritative scope.

## Current status

The original source tree has been imported into this repository. Recent improvements include:
- A dashboard at `/` with portfolio summaries and navigation.
- Backend input validation for orders and rejection of invalid broker prices.
- One-time, expiring broker OAuth state backed by a database nonce digest.
- Paper LIMIT-order matching in the worker, using the shared transaction-cost, cash and position accounting.
- Automated backend and frontend checks in GitHub Actions.
- An environment-controlled emergency kill switch blocks new strategy entries when `AUTOMATED_ENTRIES_ENABLED=false`; strategy exits remain enabled.

See [AUDIT_REPORT.md](./AUDIT_REPORT.md) for findings, verification links and remaining work. See [REFERENCE_REPOSITORY_AUDIT.md](./REFERENCE_REPOSITORY_AUDIT.md) for the external repository comparison and safe integration plan.

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


### Durable reconciliation run summaries
Every explicitly invoked read-only worker pass now creates a `live_reconciliation_runs` record after acquiring its lease. It stores timestamps, terminal status, a safe error category and count-only summary; raw broker responses, credentials and exception text are excluded. Migration `202610170004` and tests passed in [run 39059271937](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059271937): 340 passed, 1 warning, with SQLite/PostgreSQL 16 reversible migration checks. Stale `RUNNING` recovery and operator-facing manual-review records are not implemented yet.


### Durable manual-review queue foundation
The worker now persists deduplicated `live_reconciliation_issues` records for malformed broker rows, unmatched/ambiguous orders, trade conflicts, fill-link conflicts and status-transition conflicts. Issue details are allowlisted, credential-key-checked and limited to safe reason codes/normalized identifiers; repeat occurrences increment a counter and reopen the issue. Migration `202610170005` and tests passed in [run 39059749652](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059749652): 342 passed, 1 warning. The queue currently exists only in the database—no UI/API resolution workflow yet. This newer checkpoint supersedes older dated README statements saying the worker did not exist.


### Read-only reconciliation review endpoints
Authenticated users can list their own safe run summaries at `GET /api/v1/reconciliation/runs` and manual-review issues at `GET /api/v1/reconciliation/issues`. Both routes are owner-scoped, support bounded filters and return sanitized schema fields only. Cross-user/auth tests passed in [run 39060230705](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060230705): 345 passed, 1 warning, plus SQLite/PostgreSQL 16 migration checks. These endpoints do not trigger a worker or mutate issues/orders; frontend display and a separately reviewed resolution workflow are not implemented.


### Reconciliation review screen
The dashboard now links to `/reconciliation`, a read-only screen showing recent reconciliation run summaries and manual-review issues. It supports filtering by issue status and refreshing the list. It does not trigger broker reads or resolve issues. Frontend TypeScript/Next.js checks and backend CI passed for [commit e4343dcb](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e4343dcb225c1f332b6c89399694d0a29a5df739): 345 backend tests passed, 1 warning; SQLite/PostgreSQL 16 migrations passed. Issue resolution, stale-run recovery and historical trade windows remain unimplemented.


## Live-fill accounting recovery and verification — 2026-10-20

The deleted service, original tests and migration 0008 are restored to their original paths. Supporting models `BrokerOrder`, `BrokerTradeRecord`, `LivePosition` and migrations `202610180006` / `202610180007` were added to complete the chain. GitHub Actions [run 39475387511](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39475387511) passed **355 tests, 1 warning**, plus SQLite and PostgreSQL 16 migration upgrade → downgrade → re-upgrade checks at code/test checkpoint `a906274b98f3f7e0c913f376128f4996b996c52b`.

This is not a complete live-fill pipeline: the service remains unregistered, ingestion and reconciliation integration remain outstanding, and no real-account or production migration was performed. Keep live order submission disabled. Continue Phase 2 reconciliation release gates and crash/recovery/fill-linkage checks. Do not delete the recovered files without explicit user approval.


## Phase 3 live-fill accounting checkpoint — 2026-10-21

- Latest reviewed code HEAD at this checkpoint: `ef60ec93d39543c644dfd557f6f73b48ab793b60`.
- Exact-head [Backend CI run 39609474410](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39609474410) completed successfully: **485 passed, 1 warning in 30.25s**; broker-write boundary guard passed; SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed.
- The one warning is non-failing; CI logs also report GitHub Actions Node.js 20 deprecation notices.
- Existing safeguards cover replay identity/charge validation, broker-confirmed fill quantities, cumulative child/order quantity limits, rejected-order protection, and atomic live-position/execution updates. This CI result verifies the current HEAD, not completion of all Phase 3 requirements.
- **Open Phase 3 requirement:** define and test the fee-allocation contract when a broker contract-note charge total covers multiple fills. The current API accepts a per-promotion breakdown and validates that its total equals its six components; it does not itself establish how a multi-fill contract-note total is allocated. Do not claim this issue resolved or wire in a coordinator/identity bridge until the rule is designed and regression-tested.
- Safety constraints unchanged: do not enable live broker submission, automatic accounting promotion, or automatic scheduling; keep `BrokerFillIdentity` and `BrokerTradeRecord` separate pending a reviewed bridge design. Phase 2 remains closed.


## Phase 3 checkpoint refresh — 2026-10-21

- **Repository boundary:** all current Phase 3 work is confined to `tarunsharma2610-del/tradepro-improved`, branch `main`. The original `tarunsharma2610-del/Tradepro` is a protected baseline and must not be modified.
- **Current HEAD at audit start:** `3b5c8831d4f3475eee320176b3c06bdbd5364bd2` (source-ledger design-gate documentation). The documentation synchronization commit created after this note requires its own exact-HEAD CI result.
- **Latest confirmed backend CI during this audit:** [run 39618611385](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39618611385) completed successfully on **commit `49f95bdd5f20ee99b21a573087c6e97a9bc03526`**, with **485 passed, 1 warning in 30.65s**. The broker-write boundary guard and SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade steps passed. This run is an older SHA, not current HEAD; do not label later commits green based on it.
- **Phase 3 status:** in progress. Current blocker is verified actual-charge evidence and an approved allocation basis. Reviewed Upstox documented APIs provide trade data, aggregate charges, or estimates, but no verified per-fill actual-charge source/contract-note ingestion capability was found in the reviewed adapter/API catalogue. Do not treat estimates as actual charges or allocate aggregate totals by guess.
- **Next engineering sequence:** establish authoritative source format and retention/security boundary; then implement immutable source evidence and per-fill allocation records, migration, transactional reconciliation/idempotency, and required regression tests; finally verify exact-HEAD CI.
- **Safety:** live broker submission, automatic accounting promotion, and automatic scheduling remain disabled. Phase 2 remains closed. This checkpoint is status tracking, not a claim that Phase 3 charge allocation is implemented.
