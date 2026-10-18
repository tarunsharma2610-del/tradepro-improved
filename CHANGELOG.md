## 2026-10-18 — authoritative verification and reconciliation checkpoint

- Current PR-reported branch head: `15ff31122ba2f7e2f9f2ac1c1a7e80d6b77c80d1`. Workflow #722 passed on `e6a69138e2fd132da0b7a526c35f40aea4630432`, not the current head; exact-head CI remains unverified.
- `e9a69472e54b84333134568a559fa2592dcc12ce`: staged partial-fill replay/overfill/rollback regression tests.
- `c2e881103e961aaa999e94ff2436fd1f91c80140` and `e6a69138e2fd132da0b7a526c35f40aea4630432`: fail-closed average-price/fill-quantity validation and negative parser tests.
- Staging is not accounting. Fill promotion, atomic cash/position/P&L, parent/child terminal states, cancellation after partial fill, and exact-head verification remain open.
- PAPER mandatory; live broker writes blocked; original `Tradepro` untouched; PR #1 draft/open/unmerged.

---

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

## Superseding verified checkpoint — 18 October 2026: account-safety PostgreSQL concurrency

- Code/test target SHA: [872eab69082b231117184d80b1bb4a7a96c15b6b](https://github.com/tarunsharma2610-del/tradepro-improved/commit/872eab69082b231117184d80b1bb4a7a96c15b6b). This includes the PostgreSQL account-safety concurrency tests and the workflow change that runs them alongside the existing charge-adjustment concurrency test.
- GitHub Actions [run #608](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39120699215): **success**. Full backend suite: **395 passed, 4 skipped, 1 warning in 29.36s**. SQLite Alembic upgrade passed. PostgreSQL 16 Alembic upgrade passed. Dedicated PostgreSQL integration: **4 passed in 0.44s**.
- PostgreSQL safety coverage now proves: two concurrent submissions with the same broker-error idempotency key count once; two distinct concurrent broker errors serialize and trip the circuit exactly at the configured threshold; concurrent manual resets permit only one reset and preserve the audit trail.
- Migration issue resolved: removed duplicate revision 202610180009_live_account_safety.py; canonical safety migration is 202610180010_live_account_safety.py, chained after 202610180009_live_charge_adjustment_ledger.py. The prior duplicate-revision failure is superseded by successful run #606 and then run #608.
- The account safety service remains unregistered from order submission. These tests use a real PostgreSQL test database and synthetic test users only; no live broker API or order-write endpoint was called. PR #1 remains draft/open/unmerged; original Tradepro remains untouched.
- **Next task:** add read-only preflight composition coverage using the existing LivePreflightCoordinator, AccountWideLiveRiskGate, and persisted LiveAccountSafetyService decision. Fail closed on any denial/error; do not register the composition with order routes/workers or enable live order submission.

## Superseding verified checkpoint — 18 October 2026: safety-aware read-only preflight composition

- Code/test target SHA: [3e73efd441315294970cb652ddeb9b37b00b67b9](https://github.com/tarunsharma2610-del/tradepro-improved/commit/3e73efd441315294970cb652ddeb9b37b00b67b9). The coordinator change is in commit [866336676b24b0da34fe833263b0f2c33204bf17](https://github.com/tarunsharma2610-del/tradepro-improved/commit/866336676b24b0da34fe833263b0f2c33204bf17).
- GitHub Actions [run #611](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39121063921): **success**. Full backend suite: **398 passed, 4 skipped, 1 warning in 29.51s**. SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL integration passed (**4 passed in 0.41s**).
- LivePreflightCoordinator now checks the persisted account-wide LiveAccountSafetyService decision after local intent/ownership validation and before credentials or any broker snapshot. Missing safety state, a tripped latch/open circuit, stale health or an unexpected safety-check exception blocks preflight. The service is injectable for testing; default construction uses the same preflight clock.
- Regression tests prove missing state, a tripped latch, and an unexpected safety-check exception all block before any read-only broker call. Existing successful preflight tests explicitly establish a passing health check and manual reset in the test fixture.
- This is read-only preflight composition only. LivePreflightCoordinator remains unregistered from order routes/workers, no broker order-write method is called, live trading remains disabled, PR #1 stays draft/open/unmerged, and the original Tradepro repository remains untouched.
- **Next task:** audit authentication/authorization and operator audit visibility for any future safety-control endpoint. Do not create or wire a control route until that review is complete; keep live order submission disabled.


## 2026-10-18 — Safety-control endpoint security audit

- Added SECURITY_CONTROL_ENDPOINT_AUDIT.md documenting existing authentication, authorization and audit visibility controls plus required gaps before any safety-control endpoint can be designed.
- Confirmed from source review that no audit-history API or dedicated safety permission model is registered. Identified step-up authentication, CSRF/origin policy, atomic state/event persistence, database-level append-only enforcement, metadata redaction and HTTP negative-test gaps.
- Documentation-only checkpoint; no runtime code, safety routes or live order submission paths changed. Review is not a penetration test or production sign-off.


## 2026-10-18 — Order-entry path inventory

- Added ORDER_ENTRY_PATH_INVENTORY.md documenting manual, strategy, worker, paper service, broker adapter, preflight, recovery and reconciliation paths.
- Confirmed current order submission service is PAPER-only and refuses non-PAPER mode. Adapter broker-write primitives exist but no production call site was found in the reviewed paths. Recorded the uncomposed LiveOrderRecoveryService → LiveExecutionService path as a gap before any live exposure.
- Documentation-only change; no route/worker wiring or live broker write was introduced.


## 2026-10-18 — Central broker-write boundary design

- Added `CENTRAL_BROKER_WRITE_BOUNDARY_DESIGN.md` defining the single approved broker-write boundary, atomic intent/event transaction contract, unknown-outcome recovery, least-privilege permissions, operator audit visibility, step-up MFA, CSRF/Origin, append-only event controls and source-call CI guard.
- Documentation/design only: no endpoints or broker write integration added; live submission remains disabled.


### 2026-10-18 — Broker-write source guard

- Added a source scanner and tests to prevent unapproved production references to broker place/modify/cancel methods.
- Added the scanner to backend CI. Run #614 is pending verification: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123034569.
- No central writer, API endpoint, route/worker wiring, or live submission was added.


### 2026-10-18 — Guard false-positive fix

- The first guard workflow failed before pytest due to matching PAPER service `.place_order` methods as broker-adapter writes.
- Narrowed matching to adapter-named receivers in commit `30599b1bd8d32293b856c88cdfb4e2facaa9ce0f`; new CI run #615 is pending.


### 2026-10-18 — Broker-write guard verified

- CI run #617 passed on code SHA `bdf208efcc32b44a6367157dd2ab0aab946e6574`: guard PASS; backend tests 402 passed / 4 skipped / 1 warning; SQLite and PostgreSQL migrations PASS; PostgreSQL concurrency tests 4 passed.
- The guard is a preventive static check only. Central broker-write service, safety API, permission foundation, append-only storage protection and path wiring remain pending.


### 2026-10-18 — Safety-event storage hardening

- Added migration `202610180011` with request fingerprint support, unique state-version event ordering, and SQLite/PostgreSQL triggers preventing audit event updates/deletes.
- Safety idempotency replays now reject payload mismatches; broker-error threshold and reset expected-version are fingerprinted.
- Added tests for audit-write rollback, conflicting idempotency payloads, threshold mismatch, stale reset version, and PostgreSQL rejection of direct audit UPDATE/DELETE.
- Exact-head CI run `39124312326` was pending at the checkpoint; earlier green run `39124213016` predates the last expected-version/threshold change.


### 2026-10-18 — Stale-version test fix

- Fixed a regression-test setup bug by capturing the expected state version before a later ORM mutation.
- Commit: `6cd0ced108e35d715359d649a463d80709dd1fb1`.
- Exact-head CI run #39124498280 is pending.


### 2026-10-18 — Safety storage verification

- CI run #625 passed on code/test SHA `6cd0ced108e35d715359d649a463d80709dd1fb1`: 406 passed, 5 skipped, 1 warning; SQLite/PostgreSQL migrations passed; PostgreSQL integration 5 passed.
- Verified request fingerprint behavior, stale reset version test, audit-insert rollback and PostgreSQL event immutability tests. This does not complete Phase 2.


## 2026-10-18 — least-privilege safety authorization foundation (verification pending)

- Added explicit per-user safety_permissions grants and a default-deny permission dependency for safety status, audit reads, kill-switch trips and resets. is_admin does not implicitly grant safety permissions.
- Normalized malformed JWT subject claims to HTTP 401 and added a reusable Origin check for cookie-authenticated mutation requests.
- Added focused regression tests. CI has not yet verified the commits. Recent-MFA step-up, grant provisioning, route wiring and end-to-end tenant/HTTP tests remain outstanding; no safety route or live broker write was enabled.

### Follow-up correction — 18 October 2026

The Origin guard now requires an exact Origin serialization match (including rejecting a trailing slash), and unused imports were removed from the user model. Follow-up commits: f7c08e2605fb7f7828792154570af79cf5ccf724 and 4337d0ce4ef645914f32c56db87c81699c04763e. CI/status lookup has returned no run/status for the authorization changes; do not claim tests or migration passed until a workflow result is tied to the code/test SHA. Recent-MFA step-up and route wiring remain outstanding.

## Superseding checkpoint — recent-MFA step-up foundation (18 October 2026)

- Added a dedicated `POST /api/v1/auth/mfa/step-up` challenge. It requires an authenticated active user, MFA already enabled, fresh password verification and a valid TOTP code; it is rate-limited and applies the configured same-origin guard to cookie-authenticated requests. Successful challenges return a purpose-bound `step_up` JWT with `scope=safety.reset`, `amr=[pwd,totp]`, a verification timestamp, and a five-minute expiry. Failed credentials are audited without logging credentials or the token.
- Added `require_recent_safety_mfa`, which requires the separate `X-Safety-Step-Up` header, validates token type and purpose, verifies recent MFA and issuance timestamps, and binds the token to the authenticated user. It is not yet attached to a safety reset route because no safety-control routes have been exposed.
- Added unit/dependency tests for missing/wrong-scope/stale/user-mismatched step-up tokens and HTTP tests for success, invalid password and accounts without MFA. These tests are committed but **not yet verified by a GitHub Actions run for the latest code/test SHA**; do not claim they pass until exact-head CI is green.
- Latest code/test commit for this checkpoint: `ee8968f9d7d8698703e59911c7091d5f7c870c23`. Related commits: `325d9a854c05bb7dead6f6f626bf749383804a8e`, `9b65f92b060c0745c1e84e535ec5397cdf490b5d`, `1450a3d0dd8c3629e72142fe06cec699be7202f0`, `0bf5f86d9dd07ecaebe10b93149841647dfbccdf`, `1afd892fb1fa7aaf6c1b0028c248b59e06ec9994`, `aaad1d020cb629cb6d554bd08ff02d25fb1c4666`, and `ee8968f9d7d8698703e59911c7091d5f7c870c23`.
- Remaining authorization gates: trusted safety-permission provisioning, tenant-scoped/paginated audit reads, route-level permission + Origin + step-up enforcement, comprehensive negative HTTP tests, and latest-head CI. The helper does not solve these by itself. The safety status/audit/trip/reset routes and central broker-write service remain absent/unwired.
- Keep PR #1 draft/open/unmerged, keep `TRADING_MODE=PAPER` and `LIVE_ORDER_SUBMISSION_ENABLED=false`, never call broker order-write endpoints, and leave the original `Tradepro` repository untouched. Phase 2 remains incomplete.

### Superseding MFA guard correction

The step-up verifier now also denies a token if the authenticated user's MFA has since been disabled; regression coverage was added. Latest code/test commit: `ecf09e800c0dc7fc83d200d603f510348433aa58` (guard change `8a46241e766b9504c3a9bc3ba182043bac98a75d`). Exact-head GitHub Actions/status remains unverified; prior CI results do not cover this change. This remains a foundation only: the dependency is not wired to a safety-reset endpoint because those endpoints do not yet exist.

## Superseding checkpoint — audited safety-permission provisioning (18 October 2026)

- Added `PUT /api/v1/admin/users/{user_id}/safety-permissions` for one explicit grant/revoke operation at a time. The request schema only accepts the four defined `safety.*` scopes; arbitrary scopes are rejected by validation.
- The actor must be a platform admin, must pass the five-minute user-bound password+TOTP step-up, and cookie-authenticated mutations must pass the configured Origin guard. `is_admin` alone is not enough. Self-grants are rejected; revocation remains allowed for an admin's own account to support removal of access.
- Target user's permission list and the audit record (`safety.permission.grant/revoke`, actor ID, target ID and scope) are committed in the same DB transaction. The route does not grant access to read other users' audit data and does not expose the safety status/audit/trip/reset endpoints.
- Added HTTP regression tests for missing step-up denial, self-grant denial, and grant/revoke behavior with audit evidence. **These tests have not been executed in this environment and exact-head CI has not been confirmed.** Treat them as committed, unverified tests, not passing tests.
- Relevant commits: endpoint `ed1cae900a326a4922dbf42a5dbe2b7ed9d50d13`; constrained schema `8a50e8176d25e26a58f52649b21ab01cafa60cad`; test additions `b1b326e7ff409b84d2feab438f69275678939d2f`; formatting follow-up `1d464907a2aec9d0a4e257cb960bf32b24d032ee`.
- Remaining gates: CI on latest code/test SHA, independent review of the permission-provisioning threat model, tenant-scoped audit reads, safety status/audit/trip/reset routes with explicit permission enforcement, state/event atomicity at endpoint level, central broker-write service and end-to-end path enforcement.
- Continue to keep PR #1 draft/open/unmerged and keep live order submission disabled. Phase 2 is incomplete; original `Tradepro` remains untouched.

### Follow-up correction and verification checkpoint (18 October 2026)

- Corrected the safety-permission endpoint import formatting and cleaned test imports after reviewing the committed source through GitHub. Latest test-file commit: `ae46db76e86ea28116bcaf80b9a02c64eb713e9b`; endpoint import correction: `3ef5d32ddeb97ffbd43c61acb74945dd4f564729`.
- The repository connector did not expose a local test runner, and GitHub Actions/combined-status lookups returned no run/status for the latest code/test SHA. Tests remain **unexecuted/unverified**; the older CI run is not evidence for these changes. The next action must be to get CI running on the current branch head and resolve any failures before adding further security-sensitive behavior.
- Phase 2 remains incomplete. Keep PR #1 draft/open/unmerged, preserve PAPER-only defaults and live-order submission disabled, and leave the original `Tradepro` repository untouched.

## Phase 2 checkpoint — tenant-scoped safety audit read (18 October 2026)

- Added `GET /api/v1/admin/safety/audit`, protected by the explicit `safety.audit.read` permission. It accepts bounded pagination (`limit=1..100`, `offset=0..100000`), returns a page envelope and uses a stable `created_at DESC, id DESC` order.
- The SQL query scopes rows to `AuditLog.user_id == authenticated_user.id` and `action LIKE 'safety.%'` before counting or pagination. The caller cannot provide a target user ID; unrelated audit actions and other users' events are not returned. This is an actor-scoped view of safety events, not an administrator-wide or target-account audit browser.
- Added HTTP regression tests for permission denial, pagination bounds, and tenant isolation / filtering. **The tests are committed but have not been executed locally; exact-head GitHub Actions status has not been confirmed.** Do not call the feature CI-verified yet.
- Relevant commits: endpoint `d608f4fdd8a9f10b0647fbe4083d35809b27061f`; response schemas `d46c9268c7c05ca9e207898ca80674df56883a03`; tenant isolation tests `eda5a3589765211105457e2b8950d0c20f00f011`; follow-up import/test cleanup `584b774e175b1aecd74784286bd5fca566e1be6d`.
- Remaining Phase 2 work: run/fix CI on the latest branch head; implement persistent safety status and kill-switch trip/reset routes with the correct permission, Origin and MFA gates; decide and document operator-vs-account audit visibility before expanding audit scope; ensure atomic state/event transactions and concurrency semantics; implement the central broker-write service and enforce it across every execution path. Live trading remains disabled and PR #1 remains draft/open/unmerged.

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


## MFA HTTP route-matrix follow-up — 18 October 2026

- Added two missing HTTP-level cases to `backend/tests/test_api_authorization.py`: cookie-authenticated `POST /api/v1/auth/mfa/step-up` without an Origin header must return 403; unsupported step-up purpose `safety.live_trade` must be rejected by request validation with 422. These complement existing tests for missing/disabled MFA, wrong password, non-admin privileged-purpose denial, reset-vs-admin token scope separation, stale/user-bound tokens, cross-origin mutations, permission denial, and reset health prerequisites.
- Test commit: `58778259324119379c69b03c822c13849b223d22`. GitHub Actions run [#39133596645](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39133596645) is running; broker-write boundary guard has passed and pytest is in progress at time of this note. Do not claim the new tests pass until the run completes and its pytest/migration/PostgreSQL steps conclude successfully.
- Review outcome so far: reset and permission-management routes explicitly use distinct MFA scopes; platform-admin status alone does not grant safety permissions; user audit is tenant-scoped to immutable safety events. The matrix is broader but not exhaustive, and no independent security certification is implied.
- Next after CI: fix only demonstrated failures; if green, proceed to the central broker-write authorization/gating design and enumerate every order-write path before wiring anything. Keep PAPER mode, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.


## MFA HTTP route-matrix CI result — PASS (18 October 2026)

- GitHub Actions [run #39133596645](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39133596645) passed for test commit `58778259324119379c69b03c822c13849b223d22`: broker-write boundary guard passed; backend suite **437 passed, 5 skipped, 1 warning in 28.01s**; SQLite Alembic migration passed; PostgreSQL 16 Alembic migration passed; PostgreSQL safety/charge-adjustment concurrency tests **5 passed**.
- This run verifies the added missing-Origin and unsupported-purpose HTTP tests plus the existing MFA/authorization matrix at that tested code SHA. Later documentation-only commits did not alter application code. One non-blocking Starlette/AnyIO deprecation warning remains.
- This does not certify every auth route or complete Phase 2. Next task: map all broker order-write entry points and design a single fail-closed broker-write authorization gate, then test that all paths are blocked in PAPER mode and remain disabled absent explicit future approval. Do not wire real order submission in this task. Keep PR #1 open/unmerged and original `Tradepro` untouched.


## Central broker-write boundary — deny-all foundation (18 October 2026)

- Added `backend/app/services/live_broker_write_service.py` as the single planned choke point for place/modify/cancel operations. This is intentionally a deny-all foundation: every write method raises `LiveExecutionBlocked` with an explicit no-request-sent message. It does not import or call a broker adapter, and it is not registered with routes, strategy workers, recovery, or any execution path.
- Added `backend/tests/test_live_broker_write_service.py` covering all three write verbs and asserting each fails closed. Commits: service `3726484932e4d46d9f92a7ff41cb5b761cfb1720`; tests `f4442607b8b71df7fffbf4354ea11a532efb99d6`.
- Verification pending at this note: the backend workflow for test commit `f4442607b8b71df7fffbf4354ea11a532efb99d6` has passed the broker-write source guard and is in pytest. See [run #39134040222](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39134040222). Do not claim tests/migrations passed until the run concludes.
- This does **not** complete the broker-write service. Next design must enumerate the persisted-intent lifecycle, ownership, user confirmation, account safety state, fresh pre-trade risk, token/connection stability, and timeout/recovery behavior before any adapter call can be implemented. Do not wire it or enable live orders. PAPER mode, disabled live submission, PR #1 draft/open/unmerged, and original `Tradepro` untouched remain mandatory.


## Central broker-write deny-all CI result — PASS (18 October 2026)

- GitHub Actions [run #39134040222](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39134040222) passed for test commit `f4442607b8b71df7fffbf4354ea11a532efb99d6`: broker-write source guard passed; full backend suite **440 passed, 5 skipped, 1 warning in 32.49s**; SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL safety/charge-adjustment concurrency tests **5 passed**. A separate workflow for the service-only commit also passed.
- The deny-all broker-write service remains deliberately unwired and makes no adapter calls. This step proves the central choke-point stub refuses place/modify/cancel; it does not verify live submission (which remains disabled) and is not a complete broker-write implementation.
- Documentation-only checkpoint commits followed. Next: inspect every existing order-writing entry point and add a call-graph/inventory, then design the central gate around ownership, persisted intent/idempotency, account-level safety latch, live pre-trade risk, explicit confirmation, and ambiguous timeout recovery. Keep PAPER mode, live submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.


## Broker-write path inventory and guard hardening — 18 October 2026

- Added `BROKER_WRITE_PATH_INVENTORY.md` documenting current adapter definitions, PAPER execution routes, read-only live preflight/recovery/reconciliation, and controls required before any live write is implemented. Commit `68f528edf4fe2dcb958161943b878b5863bbcd74`.
- Strengthened `backend/scripts/check_broker_write_boundary.py` to reject broker-write method references regardless of receiver name, rather than relying on adapter-like variable names. It now permits only the known PAPER `self.execution.place_order` calls in `strategy_execution_service.py` and the existing `ExecutionService(...).place_order/cancel_order` endpoints in `api/v1/portfolios.py`. The first strict run correctly exposed those two existing PAPER API call sites as exceptions that needed explicit, narrowly-scoped allowlisting; no live adapter write path was identified in those failures.
- Added guard tests for generic receiver bypass, central-service adapter-call rejection, and the approved PAPER call sites. Test updates are committed through `e9c31a043465e3d09223894ddfe45629cfc0302e`.
- CI for the latest guard/test fix is in progress: [run #39134878791](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39134878791). Do not treat this guard hardening as verified until the exact-head workflow passes. The preceding strict-guard failures were expected detection/allowlist gaps and prevented pytest/migration stages from running.
- Live broker writes remain unimplemented and denied by the central service. Keep PAPER mode mandatory, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.

## Central safety-preflight + durable intent composition — VERIFIED (18 October 2026)

- Added LiveOrderRecoveryService.persist_preflighted_intent(...). It accepts only a LiveOrderPreflight plan, verifies user/portfolio/instrument/broker and exact intent fields, rechecks the currently connected Upstox connection ID, then persists one stable PENDING_SUBMISSION LIVE intent with an opaque broker tag and portfolio-scoped idempotency key. It does not call a broker order endpoint.
- Updated LiveBrokerWriteService to expose prepare_order_intent(...): run LivePreflightCoordinator.preflight first (environment interlocks, explicit confirmation, ownership/instrument validation, persisted account safety latch, fresh read-only broker risk snapshots and account-wide risk gate), then persist the plan. If preflight fails, persistence is not attempted.
- Place/modify/cancel methods remain unconditional deny-all; this service does not send real orders and is not registered with routes/workers. PAPER-only ExecutionService is unchanged.
- Added tests for preflight-before-persistence, no persistence on denied preflight, exact plan matching, idempotent intent replay, and broker connection change after preflight.
- Verified GitHub Actions run #39136080295 on code/test SHA 27c4a4e5ed9fd9d864e38816c945e37371ee22f7: broker-write source guard passed; backend 448 passed, 5 skipped, 1 warning in 39.34s; SQLite migration upgrade passed; PostgreSQL 16 migration upgrade passed; PostgreSQL safety/charge-adjustment concurrency tests 5 passed.
- Code commits: recovery persistence 66675d34bee98cdc6c0f24388f4fb097e79348ac; central composition 4d8268ca86e08a36025182a8e46f43b18ba951e6; orchestration tests ab010e8106b02b182594c0a664df34647a234bdb; persistence tests 27c4a4e5ed9fd9d864e38816c945e37371ee22f7.
- Remaining: review persisted intent status transitions and duplicate/concurrent races, require account safety to be rechecked at any future submission boundary, and design broker-confirmed submission/recovery with ambiguous outcomes. No submit method is approved. Keep PAPER mode, live submission disabled, PR #1 draft/open/unmerged, and original Tradepro untouched.

## Post-preflight instrument revalidation — VERIFIED (18 October 2026)

- Hardened persist_preflighted_intent to re-read the instrument row after asynchronous broker snapshots and reject missing/inactive instruments or any instrument-key change since the preflight plan was produced. This closes the same time-of-check/time-of-use gap already covered for broker-connection identity.
- Added regression test mutating the instrument key after snapshot-plan creation; persistence is rejected and no LIVE Order row is created.
- GitHub Actions [run #39136563051](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39136563051) passed on code/test SHA c40689ac227ab56ca58993072112d6fd575aff46: broker-write source guard passed; backend **449 passed, 5 skipped, 1 warning in 32.68s**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL safety/charge-adjustment concurrency tests **5 passed**.
- Next: add concurrency/state-transition tests around persisted intent creation and submission-unknown marking. Any future submitter must recheck the account safety latch and independent interlocks immediately before network I/O. Actual place/modify/cancel remain denied and no live broker order request is enabled.

## Broker-account binding for recovery — VERIFIED (18 October 2026)

- Added nullable `orders.broker_connection_id` with FK/index and Alembic revision `202610180013`. New live intents persist the exact broker connection ID validated by preflight. Legacy rows are intentionally not backfilled because the currently connected account cannot prove which account was used originally.
- Read-only recovery now fails closed before calling order history if the original connection is missing, disconnected, or differs from the currently verified connection. Existing child mappings are reused only when connection ID, broker name, and stable tag match the persisted intent.
- Added regression tests proving a disconnected/original-connection mismatch and a legacy unbound intent produce `UNKNOWN_REQUIRES_REVIEW`, make no order-history call, create no child mapping, and never invoke a broker write. Migration runs are verified on SQLite and PostgreSQL 16.
- Verified GitHub Actions [run #39139728102](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39139728102), SHA `9cb7ab055a0cd55028f0001aa90d647f1518b667`: broker-write source guard passed; backend **453 passed, 8 skipped, 1 warning**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL integration tests **8 passed**.
- Remaining: this is still recovery identity binding, not broker submission. No place/modify/cancel network write is enabled. Any future submitter must perform a fresh account safety/interlock check immediately before I/O, commit and honor the single-winner claim, and route crashes/timeouts into read-only reconciliation. Keep PAPER mode mandatory, live submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.

## Fresh pre-submission interlock revalidation — VERIFIED (18 October 2026)

- Added `LiveOrderRecoveryService.validate_claimed_submission(user_id, order_id)` as a validation-only primitive for any future separately reviewed submitter. It requires `TRADING_MODE=LIVE`, `LIVE_ORDER_SUBMISSION_ENABLED=true`, a user-owned tagged LIVE intent in `SUBMISSION_CLAIMED`, the original still-connected broker connection, automated-entry enablement for strategy orders, and a positive `LiveAccountSafetyService.check_allowed` result.
- The method does not call a broker adapter and no current write method invokes it. It explicitly documents that a future submitter must still solve the race between this check and network I/O; this check alone is not a safe live-submit implementation.
- Added regression tests for disabled runtime submission flag, missing account-wide safety state, and disconnected original broker connection. The first CI attempt exposed a test-fixture reference error; that fixture was corrected and the latest run is green.
- Verified GitHub Actions [run #39140514552](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39140514552), SHA `9085d9fbdcc8ee2dd8baac6f5e73f92bd76cfa8b`: broker-write source guard passed; backend **456 passed, 8 skipped, 1 warning**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL integration tests **8 passed**.
- Remaining: no actual broker order write is enabled. A future submitter must implement a race-safe final interlock protocol (e.g. coordinated safety-state lock/version and claim semantics), without holding unsafe database locks across network I/O, and must handle post-request crashes through read-only reconciliation. Keep PAPER mode mandatory, live submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.


## 2026-10-18
- Added regression coverage for multiple partial broker fills across repeated snapshots, duplicate replay handling, cumulative order-quantity enforcement, rollback on attempted overfill, and the no-accounting-mutation invariant for staged trades. CI verification pending.



## 2026-10-18
- Reject internally inconsistent Upstox order-detail snapshots where filled quantity and average fill price disagree; add malformed-response tests.
