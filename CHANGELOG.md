# Change Log — Tradepro Improved

## 2026-10-18 — credential-bound preflight and CI hardening

- Added the unregistered async `LivePreflightCoordinator` for read-only Upstox risk snapshots and account-wide preflight checks.
- Validates intent and ownership before broker snapshot calls, refreshes the broker connection after async collection, and rejects credential rotation/token mismatch or connection identity changes.
- Added regression coverage for token rotation, missing connections, tenant isolation and invalid intent ordering. GitHub Actions [run #39112247035](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39112247035): 326 passed, 1 warning; SQLite migration check passed.
- No order routes/workers were wired; no real order was submitted.


## 2026-10-18 — preflight coordination and fail-closed request validation

- Added `LivePreflightCoordinator` to combine read-only Upstox risk snapshots with the existing live preflight and account-wide risk gate, without registering it to routes/workers or submitting orders.
- Hardened ordering so malformed intent, unsupported segment and disabled automated strategy entries fail before broker snapshot calls.
- GitHub Actions [run #39112112534](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39112112534): 323 passed, 1 warning; SQLite migration check passed. All broker interactions were mocked in CI.


## 2026-10-18 — read-only live risk snapshots and official session calendar

- Added a fail-closed account-wide live risk gate with absolute INR caps, broker-position exposure, unresolved-order exposure, order-frequency and daily-loss checks, and funds/margin checks.
- Added read-only Upstox full market quotes, positions, funds/margin-estimate and market holiday/timing requests; quote and calendar parsers reject malformed or mismatched payloads.
- Added `UpstoxLiveRiskSnapshotService` to collect validated broker snapshots without placing orders. The collector and risk gate remain unregistered and are not wired to submission routes/workers.
- Official NSE holiday/special-session data now governs the session decision; special sessions are not blocked by hardcoded normal hours.
- CI [run #39111682177](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39111682177): 315 passed, 1 warning; SQLite Alembic upgrade passed. No live orders were submitted.


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

### Additional improvement — read-only broker status reconciliation foundation
14. Added nullable broker-order reference/status/check timestamp/error metadata and a forward migration.
15. Added a read-only reconciliation service that checks ownership, refuses PAPER orders, requires a persisted broker order ID and usable Upstox session, validates the returned order ID, and records broker status without changing local order status, positions, or cash.
16. Added mocked tests for successful status capture, PAPER-mode refusal, and mismatched broker order IDs. This is a foundation only: there is no live order placement or automatic fill/cancel reconciliation.

### Additional improvement — authenticated broker-status API
17. Exposed a read-only authenticated endpoint `GET /portfolios/{portfolio_id}/orders/{order_id}/broker-status`. It checks portfolio ownership and returns the reconciliation service result. It does not place orders or modify local execution/accounting status.
18. The endpoint is useful only for a LIVE order that already has a stored broker order ID and a valid Upstox session; the app still has no live submission lifecycle.


### Second-pass audit fixes — 17 October 2026
19. Made paper fills atomic across order status, aggregate position, cash balance and execution row; added a rollback regression test.
20. Added per-strategy position allocation and strategy-specific realized P&L, preventing a strategy from treating a manual/other-strategy position as its own and preventing manual sells from consuming strategy-allocated shares.
21. Added a migration that backfills historical strategy-specific P&L and open allocations from strategy-tagged executions. The clean SQLite upgrade passes; populated staging-data validation remains required.
22. Added fail-closed instrument/segment validation to order, strategy and backtest paths. Futures/options are rejected until verified derivative instrument data, tick-size normalization, lot sizing and contract risk controls are implemented; frontend segment choices reflect this.
23. Corrected outdated documentation about the paper LIMIT matcher, kill switch, idempotency and instrument-master status.

### Verification after second-pass fixes
- Latest verified backend CI: **188 passed, 1 warning**, with clean SQLite Alembic upgrade: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39030790984.
- Latest frontend TypeScript and Next.js build checks passed after an earlier intermittent Google-font module resolution failure: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39030941702.
- No real broker orders were placed; live trading remains disabled.

24. Wired the manual portfolio order form to the existing backend idempotency key: the key is reused after network/server errors and cleared after success or when the payload changes.


### 17 October 2026 — migration verification and persistent instructions
- Added `PROJECT_INSTRUCTIONS.md`, a verbatim copy of the complete `Pasted text(6).txt` requirements, and `PROGRESS.md`, a persistent continuation checklist/state log.
- Added a populated legacy-database regression test for strategy-position migration backfill. It verifies realized P&L, weighted average/open allocation, long-only over-sell attribution, unchanged aggregate position/cash, and repeat upgrade.
- Verification on commit `1fe681246cb88a9505302a1763128c51ab72802d`: backend **190 passed, 1 warning** plus clean SQLite migration upgrade; frontend TypeScript and Next.js build passed.


### 17 October 2026 — strategy idempotency hardening
- Strategy orders now use stable per-candle idempotency keys; no strategy order is submitted when candle timestamp parsing fails.
- Reused keys must match strategy/manual execution reason and strategy ID, in addition to order parameters.
- Added regression tests for repeated same-candle entry, missing timestamps and cross-scope key reuse. First run exposed a test setup assumption (₹30,000 did not exceed the 25% cap on ₹500,000 virtual capital); the test was corrected with an explicit 1% cap.
- Latest verified code commit `e9f8b7bb56f3300d1016195a773a26845d94d717`: backend **193 passed, 1 warning**, migration upgrade passed, frontend TypeScript/build passed.


### 17 October 2026 — Upstox Place Order V3
- Updated `UpstoxAdapter.place_order` to the official V3 endpoint after verifying the current docs mark V2 place-order as deprecated. Updated the mocked test to assert the V3 URL and `data.order_ids` response shape.
- CI on `ded6138b93f8e18f96117f5bb4fce0ec8aeaeb1b`: backend **193 passed, 1 warning**, migration upgrade passed, frontend checks passed. No live requests.


### 17 October 2026 — Upstox V3 modify/cancel adapter methods
- Added abstract `modify_order` and `cancel_order` operations to the broker adapter contract and implemented the official Upstox V3 `PUT /order/modify` and `DELETE /order/cancel?order_id=...` calls.
- Added mocked tests for endpoint, payload/query and response shape. Methods remain unconnected; no local accounting is updated based on request acceptance.
- CI on `2bc21c59dc4c9b8d1cd2e38d24a611433e07d82c`: backend **195 passed, 1 warning**, migration upgrade passed, frontend checks passed.


### 17 October 2026 — live readiness audit
- Documented current risk, OAuth/token, instrument validation and reconciliation state in the progress/handover/audit records. The paper-only order guard remains mandatory.
- Selected a small read-only hardening task: reject broker status payloads without a matching order ID, using the documented Upstox Get Order Details response shape. No live order submission will be wired in this step.


### 17 October 2026 — broker status identity validation
- `BrokerReconciliationService` now requires the broker status payload to include a non-empty `order_id` matching the requested broker order before it stores the status.
- Added mocked coverage for missing broker order ID. The service remains read-only and does not infer fills/cancellations.
- CI on `9f1e1300acc15f85d8abf1e29e73de34f6ca14f3`: backend **195 passed, 1 warning**, migration check passed, frontend checks passed.


### 17 October 2026 — read-only per-order trade lookup
- Added `get_order_trades` to the broker interface and Upstox adapter using the documented `GET /v2/order/trades?order_id=...` endpoint. Added mocked endpoint/response test; no live request or local accounting mutation.
- CI on `ebda043d4537353529007b8f3aa1aacceb13d4c4`: backend **197 passed, 1 warning**, migration check passed, frontend checks passed.


### 17 October 2026 — read-only order history lookup
- Added `get_order_history` to the broker interface and Upstox adapter, supporting order ID and/or stable tag with local validation and the documented 40-character tag limit.
- Added mocked tests for tag lookup, order-ID lookup and invalid queries. The first CI run identified a missing `AsyncMock` import; fixed it, then verified the full suite.
- CI on `8b66df970d2dda91c060583ed6065c0101cd7837`: backend **200 passed, 1 warning**, migration check passed, frontend checks passed.


### 17 October 2026 — live order state-machine design
- Added `LIVE_ORDER_STATE_MACHINE.md` to define a safe future live lifecycle before coding. It covers multi-ID V3 responses, tag-based timeout recovery, partial-fill/trade deduplication, cancel/modify confirmation, restart recovery, required schema and release gates.
- Documentation only: no live order path added; PAPER-only execution gate unchanged.


### 17 October 2026 — additive live broker schema foundation
- Added `BrokerOrder` child rows (supports multiple broker IDs per local order), a unique nullable `Order.broker_tag`, expanded order status width, and broker-order/trade ID fields on `Execution` with per-broker trade-ID uniqueness.
- Added migration `202610170004_live_broker_order_state.py` and a populated legacy database regression test. Paper order/execution data remains intact; duplicate broker order IDs/trade IDs are blocked.
- CI on `dbd83c878753e7a0cb6e2a7935c55378ee56d7cb`: backend **201 passed, 1 warning**, migration check passed, frontend checks passed. New fields remain unused by execution.


### 17 October 2026 — pure Upstox response parsers
- Added typed pure parsers for Place Order V3, Order Details, Order History and Order Trades payloads. Tests cover malformed fields, mismatched identities, duplicate child/trade IDs, invalid quantities/prices, and empty history/trade results.
- Cross-checking official docs showed Order History may contain multiple timeline events with the same order ID; parser and test now accept that valid response shape.
- CI on `0d1ececff933e3271576096756192036963805ba`: backend **223 passed, 1 warning**, migration check passed, frontend checks passed.


### 17 October 2026 — live risk audit
- Audited current strategy/portfolio risk controls and confirmed they are not sufficient for live/manual orders. Documented missing broker funds, all-order exposure/loss limits, order-rate controls, stale quote/session checks and account-level live circuit breaker.
- Identified current official Upstox Funds & Margin V3 as the next read-only adapter foundation; no risk gate or live order path changed in this audit.


### 17 October 2026 — Upstox Funds & Margin V3 adapter
- Added `get_funds_and_margin` to the broker interface and Upstox adapter using the official V3 URL and required `Api-Version: 3.0` header.
- Added mocked tests for endpoint, auth/API-version headers, response shape and 423 maintenance error handling. No live requests; not used in order approval.
- CI on `6f92a7f9ead0f9fe2da6222e122945a3f419bd1c`: backend **225 passed, 1 warning**, migration check passed, frontend checks passed.


### 17 October 2026 — typed Funds & Margin V3 parser
- Added `FundsAndMarginV3` and `parse_funds_and_margin_v3` to validate nested funds data while keeping available-to-trade, cash and pledged margin separate. Includes realized/unrealized losses and signed unsettled-profit fields.
- Added tests for valid response, missing fields, invalid numeric values and error/423 envelopes. Not wired to order approval.
- CI on `27e87cca48c03528f5fe5fee5816ff2aa4438caa`: backend **235 passed, 1 warning**, migration check passed, frontend checks passed.


### 17 October 2026 — instrument margin calculation API
- Added read-only `get_margin_details` to the broker interface and Upstox adapter using `POST /v2/charges/margin`.
- Added input validation and normalization for batches up to 20 instruments, unique keys, quantity, transaction type, product, and optional price; invalid input is rejected before network calls.
- CI regression was investigated from logs: fixed missing decimal imports and moved `_to_result` back to the adapter class after finding it nested under a module-level validator. Latest CI on `e6abb6704b67c54f35bb5d7c2c41acd96846147d`: **238 backend tests passed, 1 warning**, migration passed, frontend checks passed.
- Response is still raw broker data; no order-approval/risk gate uses it. Next task is official response-schema audit and typed parsing if needed.


### 18 October 2026 — typed Upstox Margin Details response parser

- Added pure parse_margin_details and immutable typed MarginEstimate / MarginBreakdown results for the documented margin API response.
- Validates required aggregate and per-row fields, non-empty margin rows, finite non-negative numeric amounts, and successful response envelopes.
- Added tests for a documented response shape and malformed/error cases. This remains a read-only parser; no risk gate or order approval uses it.
- Commits: parser 3c4dd6ac0d7d88a18916c241d28a224fc5031d5d; tests 6995f64429b44134edfa5985ad4f50c3b54cfcab. CI status for the current PR head must be checked before claiming verification; the older green workflow does not validate these added tests.


### 18 October 2026 — roadmap and status reconciliation

- Added `MASTER_ROADMAP.md` to centralize sequencing, verified baseline, release blockers and continuation rules.
- Clarified that read-only `get_margin_details` adapter support and `parse_margin_details` are present; earlier statements describing these as missing are historical notes.
- Current CI for the parser/test commit remains unverified: no workflow run or commit status was returned by the connected GitHub integration. Earlier green checks do not cover this change.
- Next gate is inspect/trigger CI and record actual results; do not merge or enable live trading.


### 18 October 2026 — broker-reconciliation CI investigation

- Added regression coverage for an Upstox status-check failure response; commit `2625191740554efe5a41f99eff15306ebd68ec5c`.
- Investigated workflow run `39028914012` (`Backend pytest`): it ran against the earlier PR merge checkout `d04dfa5` and reported `177 passed, 3 errors`; all three errors were fixture setup failures (`portfolio` not found) in that checkout. The current branch version of `backend/tests/test_broker_reconciliation.py` defines the fixture, but this alone is not proof the current branch passes.
- The GitHub integration's commit-SHA workflow lookup and combined-status lookup returned no results for the current branch head. The old failed run is not a valid test of current head `2625191740554efe5a41f99eff15306ebd68ec5c`; current CI remains unverified.
- Next: inspect the latest PR run in GitHub Actions (PR workflows check out the generated merge ref), confirm backend tests, migration and frontend results, and fix only current-head failures. Do not claim green CI or enable live trading.


### 18 October 2026 — authoritative continuation checkpoint

- Reconciled the next task with the actual current branch artifacts: trade parser and `BrokerTrade` type, broker child-order schema, nullable broker references on executions, and uniqueness by `(broker_name, broker_trade_id)` already exist.
- The remaining concrete gap is transactional broker-confirmed trade ingestion, correct local parent/child order mapping, and tested idempotent persistence. First audit account/connection scoping; the existing uniqueness key does not itself include a broker connection/account ID.
- Latest PR head observed: `540e1285d3de934b43829948a1b60c67658d1343`. The integration returned no workflow runs or combined statuses for this SHA; current-head CI remains unverified. Do not present older green runs as current verification.
- No live order submission or accounting wiring is authorized by this checkpoint. Preserve paper/live isolation and do not merge the draft PR.


### 18 October 2026 — idempotent broker trade intake foundation

- Added a separate `broker_trade_records` staging table and `BrokerTradeIngestionService` to persist normalized broker trades once per broker connection, while rejecting conflicting trade-ID reuse.
- Added validation for LIVE-only order scope, owner isolation, child-order mapping and connection binding, side, positive quantity/price, instrument token, and order-quantity bounds.
- Added migrations 005/006 and changed broker child-order/execution identity constraints from global broker-name keys to connection-scoped keys; legacy links are backfilled only when the owning connection is identifiable.
- Added/updated regression tests for idempotent replay, conflicting replay, cross-user isolation, malformed trades, paper accounting isolation, and migration compatibility.
- Safety boundary: these rows are intake records, not accounted executions. The service does not mutate cash, positions, order status or P&L and is not wired to a live execution path.
- Current head `32eea17c141d4cfbc727eed2ff2a1b40d21dbba3`; current-head CI/status not returned and local clone failed because GitHub DNS was unavailable. Verification remains pending.


- Follow-up test: added populated legacy-data coverage for migration 006 backfilling `broker_orders.broker_connection_id` and `executions.broker_connection_id`. Latest head `a68c336e4a35ccc0bfe4d6539760ad03e40672f1`; CI verification remains pending.


- Verification clarification: code/test target `a68c336e4a35ccc0bfe4d6539760ad03e40672f1`; subsequent documentation-only commits advanced the branch. PR head observed at the last check `1b0056d9739cd55d50cd5484cddf955aa8bf07db` had no workflow run/status returned. The new code and migrations remain unverified.


### 18 October 2026 — Phase 2 broker intake validation hardening

- Resolved the exact broker connection from the child-order mapping and required it to belong to the requesting user and expected broker; unbound/foreign connection mappings fail closed.
- Required a non-empty instrument token that exactly matches the local instrument before staging a broker trade. Invalid non-text side input now produces a controlled validation error.
- Added regression cases for a foreign user's broker connection, missing instrument identity, and malformed side data.
- Commits: `2cdbbe290f8b661cb91110dbb4e165fcef36f800` (code), `b780c39f770a6839dab0af63fc424c341eff9d70` (initial tests), `264aa4c609d522cd01d07e8213bfee6f14c7a2bf` (legacy unbound-child test). Latest code/test target: `264aa4c609d522cd01d07e8213bfee6f14c7a2bf`.
- Verification remains pending: no Actions run is associated with the current code through the available integration; no local pytest/migration run was possible. Do not infer success from historical CI.


- Added regression coverage for rejecting a legacy broker child order without a resolvable connection binding (commit `264aa4c609d522cd01d07e8213bfee6f14c7a2bf`). Latest code/test target: `264aa4c609d522cd01d07e8213bfee6f14c7a2bf`; verification remains pending.


## Phase 2 migration audit continuation — 18 October 2026

A further audit found that migration `202610180006` used an arbitrary `LIMIT 1` to infer a legacy broker connection. That is unsafe if data cannot establish a unique match. The migration now backfills `broker_orders` and linked `executions` only when exactly one owner/broker connection match exists; rows without a determinable connection stay NULL and the ingestion service rejects them. This preserves fail-closed behavior and avoids silently binding legacy records to an arbitrary account.

- Migration hardening commit: `81faa9f0225a8b50f1036b5316e747517c3f02ed`.
- Migration regression coverage commit: `203c7fcf47626ea85c4dce9762c165a2cd74ab26`, refined to model a legacy owner with no matching broker connection in `d2f7f87c82b286e54284da2a8c186be0ea28e852` and `669a3fb98cd47dccea7e75a1301c74c01c4a3ce3`.
- Latest code/test target: `669a3fb98cd47dccea7e75a1301c74c01c4a3ce3`.
- Verification: still pending. Current-head Actions query returns no run/status; do not claim tests or migrations pass until the configured workflow runs against this target.
- Next action remains the backend pytest + SQLite Alembic workflow gate. No live service wiring, production migration, PR merge, or live order is authorized by this checkpoint.


## Verified CI checkpoint — 18 October 2026

GitHub Actions run [#39109239829](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39109239829) completed successfully on commit `8a256828d202e25e3fba77b496f0da01899969b9` (safety branch). Evidence from the job log:

- Backend pytest: **266 passed, 1 warning, in 16.08s**.
- SQLite migration check: **`alembic upgrade head` succeeded**, including revisions `202610180005` and `202610180006`.
- Warning: Starlette test-client deprecation for `anyio.abc.BlockingPortal`; no test failure.
- Workflow job and overall run conclusion: **success**.

This verifies the code present at that SHA in CI. It does not validate PostgreSQL migration behavior, live broker connectivity, real order submission, live accounting, frontend build, or production deployment. Keep those as separate gates.


## Authoritative continuation checkpoint — 18 October 2026 (supersedes older pending-CI and next-task notes)

### Latest verified state

- Latest verified code/workflow SHA: `677fcf882e0ce1e6e02be3bb8df0d074b8fbf220`; commits after this SHA update documentation only and do not change the verified backend code.
- GitHub Actions [run #39109587876](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39109587876) on that exact SHA: **286 passed, 1 warning in 18.93s**, followed by successful SQLite `alembic upgrade head`. Run conclusion: success.
- Earlier verified baseline run #39109239829 had 266 passed; the newer 286-test run includes the new preflight tests. Do not use older “CI pending” paragraphs below as current status.
- The single Python warning is the existing Starlette/AnyIO deprecation. No test or migration failures occurred in the verified run.

### Completed in this continuation

1. Hardened migration 006 so it backfills broker connection IDs only when a unique owner/broker match exists; unresolved legacy rows remain unbound. Added regression coverage.
2. Added a separate `LiveExecutionService` preflight-only module and default-off `LIVE_ORDER_SUBMISSION_ENABLED` environment interlock.
3. Preflight requires `TRADING_MODE=LIVE`, the separate default-off interlock, explicit per-request confirmation, an injected reviewed account-wide risk gate, owned/active portfolio, active supported equity instrument, verified Upstox connection and usable token. Invalid inputs and risk-gate failures block.
4. The service returns a non-secret preflight plan only. It creates no Order row, does not call any broker adapter, does not persist a tag/intent, and does not change cash, positions, executions or trade staging. It is not registered to any API or worker. Live trading remains disabled.
5. Backend workflow now runs on `safety/**` pushes and relevant backend/workflow changes, while documentation-only changes do not retrigger backend CI.

### Next implementation task

**Stable idempotency/tag recovery for ambiguous submissions — design and mocked tests only.** Audit existing `Order.idempotency_key`, `broker_tag`, and adapter `get_order_history(tag=...)` behavior. Add a deterministic tag/intent persistence design and tests proving a retry never submits a second POST after a timeout. Do not implement or invoke real broker submission in this task; do not wire the service into routes/workers; do not merge PR #1 or enable live trading. After code/test commit, update progress, audit, requirements, roadmap, changelog, architecture, state-machine and handover files with exact CI evidence.

## Authoritative checkpoint — 18 October 2026 (idempotent live intent and tag recovery)

### Current verified implementation
- Latest code/test SHA: `de2e2b7524f09b1be2d4378a9b5ac29bdf26f9e7`. GitHub Actions [run #39110239225](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39110239225) completed successfully: **296 passed, 1 warning in 22.04s**; SQLite `alembic upgrade head` passed.
- Added `backend/app/services/live_order_recovery_service.py`: deterministic opaque 40-character broker tag, durable LIVE intent persistence, idempotency-key replay with exact-payload validation, submission-unknown state persistence, and read-only recovery through Upstox order-history-by-tag.
- Added `backend/tests/test_live_order_recovery_service.py`: stable tag, repeated intent, key/payload mismatch, fail-closed preflight, timeout/no-match no-resubmit, mismatched tag/intent, sliced child-order quantity reconciliation and repeated recovery.
- No `place_order` call is made by the new service. No API route or worker invokes it. Recovery stores broker child IDs only and does not infer order status/fills or change cash, positions, executions or P&L.
- The CI warning is a dependency/runner deprecation warning; test and SQLite migration steps passed. This run does not verify PostgreSQL migration, real broker API behavior, frontend build, or production deployment.
- Code and tests were committed separately: service `4990f28e7b8cfeadca85598abfac8111c8fe7130`; tests `de2e2b7524f09b1be2d4378a9b5ac29bdf26f9e7`.

### Next task
Implement a concrete, testable **account-wide live pre-trade risk gate** and inject it into the preflight path: current positions/exposure, order-value and order-frequency limits, market-session/stale-quote requirements, and broker funds/margin checks with fail-closed behavior. Mock all external calls. Do not add a broker POST, wire any route/worker, merge PR #1, or enable live trading in that task.

### Release status
PR #1 remains draft/open/unmerged. Original `Tradepro` remains untouched. Live trading remains **NOT READY**; no real orders have been submitted.

## Authoritative checkpoint — 18 October 2026: Upstox risk snapshots and official session calendar

### Verified code and tests
- Latest verified code/test SHA: `c683fbd16d114b2a41a80a646fc91ee2d4cf25eb`. GitHub Actions [run #39111682177](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39111682177) succeeded: **315 passed, 1 warning in 25.97s**; SQLite Alembic migration verification passed.
- Added strict read-only parsers in `backend/app/brokers/upstox/risk_snapshot_parsing.py` for full market quotes, open positions, official market holidays, special sessions and NSE timings.
- Added adapter calls for full quote, positions, funds/margin, estimated margin and official calendar endpoints, plus `backend/app/services/upstox_live_risk_snapshot_service.py` to collect and validate snapshots. It includes quotes for broker positions and unresolved live-order instruments, respects Upstox's 500-key quote limit, and contains no order-placement call.
- Added mocked regression coverage for malformed/naive quote timestamps, instrument identity mismatch, duplicate positions, holidays/special sessions, provider failure and the read-only collector. Current CI: 315 passed.
- The collector is not wired into a route, worker or order submission. Live mode remains disabled; no real broker requests or real orders were used in these tests.

### Remaining caveats
- The adapter/parser contract has been verified against mocks, not live Upstox responses. Broker-specific response fields and official calendar behavior need documented API-contract review before staging.
- Snapshot collection uses the currently supplied access token; safe orchestration from the user's encrypted connection into a fresh snapshot bundle and the synchronous risk gate is not yet implemented.
- Full live order status/fill/cancel reconciliation, connection-scoped fill idempotency and live accounting remain incomplete. PostgreSQL migration, exact-head frontend build and staging remain unverified.

### Next task
Implement a separate asynchronous, **preflight-only coordinator** that obtains a valid per-user Upstox token through the existing credential service, collects read-only risk snapshots, injects the snapshot-backed providers into `AccountWideLiveRiskGate`, and then invokes the existing `LiveExecutionService.preflight` contract without submitting or persisting an order. Add mocked tests for wrong user/connection, token expiry/provider failures, stale snapshots and successful preflight. Keep it unregistered: no route/worker, no broker POST, no live-mode enablement.

### Release status
PR #1 remains draft/open/unmerged. Original `Tradepro` remains untouched. Live trading is **NOT READY** and disabled. No real orders have been submitted.

## Authoritative checkpoint — 18 October 2026: reconcile-before-promote coordinator

### Verified code and CI evidence
- Latest verified code/test SHA: `cfa038fe49dfde1c441f77d5c4a12fcb13ba695a`. GitHub Actions [run #39118263100](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39118263100) succeeded.
- Full backend suite: **380 passed, 1 skipped, 1 warning in 27.98s**; SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL concurrency integration passed (**1 passed in 0.36s**).
- Added unregistered `LiveOrderFillReconciliationCoordinator`. It reconciles every mapped Upstox child order and its durable trade list before promoting any staged fill for that conceptual parent order. If any child fails reconciliation, none of the parent's fills are promoted.
- Multiple fills require distinct timezone-aware exchange timestamps, preventing ambiguous position-accounting order. Promotion stops at the first charge/accounting failure; completed fills are reported and retries remain idempotent.
- Regression tests cover successful chronological promotion, sibling reconciliation failure, missing/duplicate timestamps, and promotion failure. The parent Order remains unchanged; the coordinator contains no order-placement call and is not registered to routes/workers.

### Remaining caveats
- Coordinator tests currently inject fake reconciliation/promotion collaborators; the separate PostgreSQL integration test covers real SQLAlchemy service concurrency with synthetic records, not live Upstox behavior.
- Contract-note references remain caller supplied and not independently authenticated. Frontend build, staging, monitoring, account-level kill switch, broker-error circuit breaker, and complete production live lifecycle remain unverified/incomplete.
- PR #1 remains draft/open/unmerged; original `Tradepro` is untouched; live trading remains disabled and not ready.

### Next task
Add a service-level integration test that composes the **real** `BrokerChildOrderReconciliationService`, `BrokerTradeIngestionService`, `LiveFillPromotionService`, and `LiveFillAccountingService` with a fully mocked read-only Upstox adapter and charge estimator. Verify reconciliation happens before promotion, repeated runs are idempotent, failures leave no accounting rows, and paper cash/positions remain unchanged. Keep all promotion services unregistered; no order submission, PR merge, or live-mode enablement.

### Release status
Live trading is **NOT READY** and disabled. No real orders have been submitted.


## 18 October 2026 — Phase 2 verification coverage

- Added service-composition integration tests for the existing reconcile-before-promote lifecycle (commit `b5783d421f64fcb8e7f1d75f1af5185fd9029f59`).
- Exercises real child reconciliation, durable trade ingestion, fill promotion, and live accounting with mocked read-only broker responses and mocked charge estimates.
- Adds assertions for repeated-run idempotency, sibling reconciliation failure blocking promotion, and paper/live accounting isolation.
- CI for this commit was **not yet confirmed** when this entry was written; passing status must be recorded only after checking the exact commit's workflow result.


### Follow-up — integration test now exercises fresh intake

Commit `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88` removes pre-seeded staged trades in both integration scenarios so real ingestion must insert them from mocked read-only broker data. CI has not yet been confirmed for this SHA.

## Superseding verified checkpoint — 18 October 2026: real-service fill reconciliation integration

### Exact verification evidence
- Latest tested code/test SHA: `c779f2543ea1f20efbd8b7dca38a9c2aed201749`.
- GitHub Actions [run #39118955335](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39118955335): **success**. Full suite: **385 passed, 1 skipped, 1 warning in 34.01s**. SQLite migration upgrade passed, PostgreSQL 16 migration upgrade passed, and PostgreSQL concurrency integration passed (**1 passed in 0.35s**).
- This exact-head run verifies the fresh-ingestion integration test refinement from commit `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88` and fixes for nondeterministic child order assertions and deleted ORM fixture access.
- The real-service integration test now begins with no staged trade rows: mocked Upstox trade reads must be inserted by the real `BrokerTradeIngestionService` before official status reconciliation and promotion. Repeated reconciliation/promotion is idempotent; sibling status failure prevents any fill accounting; charge-estimate failure creates no Execution/LivePosition rows; paper cash/positions and parent Order state remain unchanged.
- PostgreSQL 16 verifies migration compatibility and concurrent charge adjustments/fill promotion. Lock scoping explicitly avoids PostgreSQL's `FOR UPDATE` nullable outer-join error.

### Release status and caveats
- All broker API responses in tests are mocked. No live Upstox API requests or real orders were sent.
- The coordinator, fill promotion and charge-adjustment services remain unregistered in order routes/workers. Live order submission remains disabled.
- Frontend build/staging, real broker contracts, exchange holiday coverage, operational monitoring, account-level kill switch and broker-error circuit breaker remain outstanding. PR #1 remains draft/open/unmerged; original `Tradepro` untouched.

### Next distinct task
Implement and test the **persisted account-level live kill switch and broker-error circuit breaker**: durable state, fail-closed read behavior, reason/timestamp/audit trail, threshold-triggered circuit trips, manual-reset policy and account-wide scope across portfolios. Keep it unregistered from order submission until separately reviewed; do not merge PR #1 or enable live trading.

This checkpoint supersedes prior notes saying CI for `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88` was pending. The latest verified test SHA is `c779f2543ea1f20efbd8b7dca38a9c2aed201749`.


## 18 October 2026 — partial fill-promotion retry coverage

- Added a real-service integration test for a temporary charge-estimation failure on a later fill, followed by idempotent retry (commit `1a3475c69d3a93ece7bfad22ace4dce52231bfa1`).
- The test checks prior successful accounting is not duplicated and the remaining fill is accounted on retry. CI is not yet confirmed for this exact SHA.


## 18 October 2026 — persistent account safety controls

- Added `LiveAccountSafetyService` for a durable account-wide kill switch, broker-error counter/circuit breaker, fail-closed checks, audited idempotent events, health-check tracking and explicit manual reset.
- Added Alembic revision `202610180009` for safety state and event tables.
- Added focused service tests for safe initialization, threshold trips, idempotency, reset gates, stale health and unknown states.
- Current-head CI/migration verification is pending; no pass is claimed.


### Safety reset test correction

Commit `c97be866828bd47a23f22fc44fac2d3359e70f35` corrects the manual-reset test sequence so it asserts the error-counter guard only after a fresh passing health check, then requires broker success plus a second passing health check before reset. CI for this code SHA remains unverified.

## Superseding checkpoint — 18 October 2026: Alembic duplicate-revision fix under CI

- Regression test commit: [8e73e9156db260b26b92666ba4cb81b5cf0ff9ea](https://github.com/tarunsharma2610-del/tradepro-improved/commit/8e73e9156db260b26b92666ba4cb81b5cf0ff9ea) adds coverage that a database read exception in `LiveAccountSafetyService.check_allowed` denies permission.
- CI run [#605](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39120252989) exposed a migration graph defect: **392 passed, 1 skipped, 3 failed, 1 warning**. All three failures reported multiple Alembic heads caused by two migration files claiming revision `202610180009` (the charge-adjustment ledger and the newly added safety migration).
- Fix commit: [410e87e7ece87d72e33c717e42871028bd0e3c36](https://github.com/tarunsharma2610-del/tradepro-improved/commit/410e87e7ece87d72e33c717e42871028bd0e3c36) removes the duplicate `202610180009_live_account_safety.py`. The existing `202610180010_live_account_safety.py` is the canonical safety migration and follows the charge-adjustment revision `202610180009`.
- Verification for the fix: GitHub Actions [run #606](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39120397940) completed successfully. GitHub Actions run #606 reports **395 passed, 1 skipped, 1 warning in 28.61s**; SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL concurrency integration passed (**1 passed in 0.26s**). This closes the duplicate-revision verification gate for code/test SHA `410e87e7ece87d72e33c717e42871028bd0e3c36`.
- Safety unchanged: account safety service remains unregistered from order submission; live order submission is not enabled; PR #1 stays draft/open/unmerged; original `Tradepro` remains untouched.

Next distinct task: add PostgreSQL concurrency coverage for account-safety idempotency/threshold trips/manual-reset serialization, then test read-only composition with the existing preflight coordinator and risk gate. Keep it unregistered from order submission.
