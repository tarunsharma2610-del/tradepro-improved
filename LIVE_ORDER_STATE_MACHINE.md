# Live Broker Order State Machine — Design Before Implementation

**Status:** design plus an unregistered preflight and read-only Upstox risk-snapshot collector; no live submission is enabled or wired.  
**Scope:** future Upstox live order lifecycle, using the existing Paper Trading code without routing live orders through the paper fill path.

## 1. Current implementation audit

The repository currently has:
- A fail-closed guard in `ExecutionService.place_order`; shared execution remains PAPER-only.
- An unregistered `LiveExecutionService` preflight contract with independent default-off interlock, explicit confirmation and a mandatory injected risk gate.
- Durable LIVE intent idempotency and opaque broker-tag recovery via read-only Upstox order history. Unknown outcomes never trigger automatic resubmission.
- A CI-tested `AccountWideLiveRiskGate` foundation. It checks weekday/session hours, quote and broker-position freshness, broker-snapshot exposure, absolute INR per-order/gross-exposure/daily-loss limits, daily live-order attempt count, unresolved order exposure, broker cash and estimated margin. Missing or malformed providers/data fail closed.
- Default caps: ₹10,000 per order, ₹50,000 gross exposure, ₹1,000 daily realized loss, 10 live attempts per UTC day and 5-second data age.

Important boundaries: the read-only Upstox snapshot collector and official holiday/special-session parser are implemented and mocked-CI tested, but are not yet orchestrated into the synchronous preflight path or wired to any route/worker. No live order submission path is connected. Full broker-confirmed status/fill/cancel reconciliation and accounting remain incomplete. **Live trading is not ready and remains disabled.**

## 2. Upstox API facts used in this design

- **Place Order V3** uses `POST https://api-hft.upstox.com/v3/order/place`. The response contains `data.order_ids`, an array, and can contain multiple broker order IDs when slicing is used. The request `tag` is limited to 40 characters. Official docs: [Place Order V3](https://upstox.com/developer/api-documentation/v3/place-order/).
- **Modify Order V3** uses `PUT https://api-hft.upstox.com/v3/order/modify`; **Cancel Order V3** uses `DELETE https://api-hft.upstox.com/v3/order/cancel?order_id=...`. Acceptance of either request is not proof that the broker has reached the requested terminal state. Docs: [Modify](https://upstox.com/developer/api-documentation/v3/modify-order/), [Cancel](https://upstox.com/developer/api-documentation/v3/cancel-order/).
- **Order Details** provides a broker order's current status and order ID: [Get Order Details](https://upstox.com/developer/api-documentation/get-order-details/).
- **Order History** supports lookup by broker `order_id` and/or `tag`, allowing recovery after a response is lost: [Get Order History](https://upstox.com/developer/api-documentation/get-order-history/).
- **Order Trades** returns trade-level fills for a broker order, including trade ID, quantity, average price and order ID: [Get Order Trades](https://upstox.com/developer/api-documentation/get-trades-by-order/).

These endpoints are currently only adapter methods and mocked tests. There has been no live order submission.

## 3. Required data model changes

Use additive migrations; do not repurpose or delete existing paper fields.

### `Order` — conceptual user order
Retain the local idempotency key and add a stable broker `tag` (maximum 40 chars) generated before any broker request. Extend the live lifecycle statuses to include at least:
- `SUBMITTING`: local intent committed before the network request.
- `SUBMISSION_UNKNOWN`: request timed out or response was ambiguous; broker may have accepted it.
- `PENDING`: broker confirms an open/unfilled order.
- `PARTIALLY_FILLED`: broker confirms some, but not all, requested quantity executed.
- `CANCEL_REQUESTED` / `MODIFY_REQUESTED`: request sent, broker outcome not yet confirmed.
- Existing terminal `FILLED`, `REJECTED`, `CANCELLED` where supported by confirmed broker data.

Paper statuses and paper accounting must remain unchanged.

### New `BrokerOrder` — one row per broker child order
A conceptual local order can map to multiple broker orders, so do not treat the legacy singular `Order.broker_order_id` field as the only source of truth. Add a child table with:
- FK to local `Order`, broker name, broker order ID (unique per broker), stable tag, broker status.
- Requested quantity, cumulative filled quantity, average fill price, last status-check time, error text and timestamps.
- Constraints/indexes that prevent duplicate child-order IDs and make recovery queries efficient.

Keep `Order.broker_order_id` populated with a primary/first ID only for backward compatibility until all readers are migrated; the child table is authoritative for multi-order reconciliation.

### `Execution` — one confirmed broker trade per row
Add nullable `broker_trade_id` (unique when non-null) and `broker_order_id` so each broker-reported trade is applied at most once. Paper executions keep these fields NULL. A unique trade-ID constraint is the deduplication barrier when reconciliation retries or restarts.

The live reconciliation transaction must insert the trade execution and update the live position/cash ledger atomically. Do not write a fill merely because Place Order returned success or Order Details reports a terminal status; use validated trade records for executed quantity/price.

## 4. Submission lifecycle

1. **Preflight:** confirm explicit user authorization and environment-level live enablement, correct broker connection/token, market session, verified equity instrument, valid tick/quantity, sufficient funds/margin, per-order notional, position/exposure and daily-loss limits. Any missing control blocks submission.
2. **Persist intent first:** create a local order with a stable idempotency key and deterministic tag before network I/O. A tag such as `tp` plus the 32-character hex local UUID is 34 characters and stable across retries. Commit the intent so a restart can recover it.
3. **Submit once:** call V3 Place Order with `slice` behavior explicitly chosen by the live-service policy. Never automatically repeat a POST after a timeout. A timeout is an unknown outcome, not a rejection.
4. **Parse response:** require a successful response and a non-empty list of `data.order_ids`. Persist every returned child order in one transaction. If the response is malformed or ambiguous, mark `SUBMISSION_UNKNOWN` and recover by tag; do not blindly resubmit.
5. **Recover uncertain submission:** query Order History by the stable tag, verify every returned order belongs to the expected instrument/side/quantity where the response provides those fields, and persist discovered child IDs. Only an explicit broker response proving no order exists can permit a carefully bounded retry policy.
6. **Track status:** query Order Details for each known broker order. Require the returned broker order ID to match the requested ID. Status checks update broker metadata, not fills/cash.
7. **Reconcile trades:** fetch Order Trades per child order; validate `order_id`, non-empty `trade_id`, positive quantity, valid price, instrument and side. Deduplicate by broker trade ID. Apply each new trade once, in a DB transaction that includes execution record, position/cash accounting and cumulative fill totals.
8. **Derive parent state:** `FILLED` only when confirmed executed quantity reaches requested quantity; `PARTIALLY_FILLED` while a positive remainder remains; do not erase partial executions when the rest is cancelled or rejected. If all children are terminal with unfilled remainder, preserve the actual filled quantity and expose the terminal outcome clearly.
9. **Modify/cancel:** validate that the order is still modifiable/cancellable, persist a request-in-progress marker, send the V3 request, then poll Order Details/History until confirmed or unresolved. A successful API response alone must not set local status to `CANCELLED` or rewrite quantities/prices.
10. **Restart recovery:** on startup and on a schedule, find `SUBMITTING`, `SUBMISSION_UNKNOWN`, `PENDING`, `PARTIALLY_FILLED`, `CANCEL_REQUESTED` and `MODIFY_REQUESTED` orders. Reconcile by stable tag/order ID and trade ID. Never resubmit an unknown order without resolving its broker state.
11. **Mismatch circuit breaker:** if broker identity, order quantity, trade IDs, positions, holdings or cash cannot be reconciled, stop new live entries for that account and require explicit review. Do not silently “fix” discrepancies with synthetic fills.

## 5. Risk and authorization gates before live submission

The current paper order cap and automated-entry loss limit are not a complete live risk system. Before a live service is wired, implement and test:
- Separate environment-level live enablement plus explicit per-user opt-in/confirmation; no UI/database flag alone may bypass the server gate.
- All-order pre-trade limits for manual and strategy orders: notional, available funds/margin, position size, aggregate exposure, daily loss and order frequency.
- Verified instrument master, tick size, quantity/lot rules and supported segments.
- Account-level emergency stop and broker-error/unknown-order circuit breaker.
- Rate-limit-aware polling and bounded backoff that never blindly repeats an ambiguous order submission.
- Audit logging without secrets, and staging/sandbox tests for the broker integration.

OAuth state/credential encryption currently exist; expired tokens are rejected. Token refresh/reconnection automation and production static-IP/regulatory prerequisites still require verification.

## 6. Test plan and release gates

All tests below must use mocked HTTP or an authorized Upstox sandbox; never place a real order just to test.

- V3 Place Order returns one ID, multiple IDs, malformed response, explicit rejection, network timeout after acceptance and network timeout before acceptance.
- Stable tag recovery finds an existing order after timeout and proves the service does not POST a second time.
- Partial fills across several trade IDs update position/cash/executions exactly once; replaying the same trade does not double-count.
- One local order mapped to several broker child orders aggregates correctly.
- Modify/cancel request accepted but status remains open; eventual cancellation; cancellation after partial fill; broker rejects modification/cancellation.
- Restart with unknown submission, open order, partial fill and pending cancellation.
- Mismatched broker order ID, trade ID/order ID mismatch, duplicate trade ID, malformed price/quantity and broker/local position mismatch all fail closed.
- PAPER mode can never invoke place/modify/cancel; LIVE mode cannot reach the paper fill method.
- Migration upgrade and backfill tested against both a clean DB and a populated staging-like DB.
- Frontend shows broker-confirmed states and unresolved/unknown states distinctly; it never implies that a request was filled/cancelled before confirmation.

## 7. Implementation order

1. Add schema/model support for broker child orders, trade-ID deduplication and partial-fill states, with additive migration and model/migration tests. No execution path uses the new tables yet.
2. Add pure response validation/mapping helpers and tests for V3 place/order-history/order-details/order-trades payloads.
3. Implement a separate, initially unregistered `LiveExecutionService` with explicit gates and mocked tests.
4. Implement a reconciliation worker that recovers unknown submissions, syncs broker statuses and applies deduplicated trades atomically.
5. Add account-wide live risk controls and circuit breakers; test direct API calls and concurrent submissions.
6. Only after independent review and sandbox/staging evidence, consider wiring explicit live UI/API routes. Keep the existing paper `ExecutionService` isolated.
7. Obtain explicit user authorization before enabling any real order path.

**Current release decision: Live Trading is NOT READY. The current adapter methods are foundations only; the PAPER-only execution gate must remain unchanged.**


## Schema foundation status update — 17 October 2026

The first schema-only implementation step is now committed in migration `202610170004_live_broker_order_state.py`: `BrokerOrder` supports multiple broker IDs per local order; `Order.broker_tag` is unique when populated; order status width supports partial/unknown states; and `Execution` has a child-order reference plus per-broker trade-ID uniqueness. The populated migration regression test passed. No execution/reconciliation code uses these fields yet.


## Response validation helper status update — 17 October 2026

Added pure typed parsing helpers in `backend/app/brokers/upstox/response_parsing.py` for Place Order V3 IDs, Order Details, Order History and Order Trades. They are tested but not wired into any live submission or accounting path. The history parser intentionally allows repeated order IDs because the official endpoint can return multiple status events for one order.


## Pre-trade risk audit update — 17 October 2026

The existing risk engine gates automated strategy entries using realized losses; manual orders bypass it and unrealized drawdown is not included. The paper order cap/cash/holding checks are not a live risk system. Live exposure/loss/rate limits, stale-quote/session checks and an account-level circuit breaker remain missing. Upstox Funds & Margin V3 (released 10 April 2026) is now the verified source for available-to-trade funds, via `GET /v3/user/get-funds-and-margin` with `Api-Version: 3.0`; the adapter lacks this method, so the next step is read-only support only.


## Funds & Margin V3 adapter status — 17 October 2026

The adapter now has read-only `get_funds_and_margin` using the official V3 endpoint and `Api-Version: 3.0`. Tests cover the documented response envelope and the daily 00:00–05:30 IST maintenance response (423). This raw response is not yet used by any risk decision. The next step is a pure parser that keeps cash available and pledged margin distinct.


## Funds response parser status — 17 October 2026

The pure `parse_funds_and_margin_v3` parser is implemented and tested. It intentionally separates total available-to-trade from cash and pledge margin; this avoids treating pledged collateral as cash. It is not connected to order approval. Next is read-only instrument-specific margin calculation support, still without live execution wiring.


## Status correction — 18 October 2026 (supersedes stale next-step notes)

The following are now present in the branch: `BrokerAdapter.get_margin_details`, the Upstox `POST /v2/charges/margin` implementation with local request validation, pure `parse_margin_details`, and unit tests for success/error/malformed response shapes. Older notes saying the adapter method or typed parser is still missing are historical snapshots, not current status. The parser is read-only and is not used to authorize orders.

The current blocker is verification: the GitHub integration returned no workflow run and no commit status for the current PR head when checked. Earlier CI results (238 backend tests, one warning, migration/frontend checks green) belong to an older commit and do not verify the margin parser changes. No pass/fail conclusion is possible from the available evidence. Inspect or trigger the configured workflow from GitHub Actions and record actual results before advancing.

`MASTER_ROADMAP.md` is now the current sequencing guide. After this verification gate, the next implementation phase is a separate, initially unregistered `LiveExecutionService` with mocked tests, while preserving the current PAPER-only execution guard. Do not merge the draft PR, place real orders, or enable live trading.


## Broker trade intake validation update — 18 October 2026

The staging-only `BrokerTradeIngestionService` was hardened to resolve the exact broker connection from the mapped child order and verify owner/broker binding. It rejects missing instrument tokens and malformed side values, with regression tests added. It remains separate from `Execution` accounting and is not registered as a live execution path. Current code/test target `264aa4c609d522cd01d07e8213bfee6f14c7a2bf` has no current-head Actions result available; do not proceed to live lifecycle wiring until tests and migration checks are verified.


A further regression test now confirms intake rejects legacy child-order rows with no resolvable broker connection. Code/test target `264aa4c609d522cd01d07e8213bfee6f14c7a2bf`; verification still pending.


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


## Verification addendum — 18 October 2026

The existing state flow remains: broker read/reconcile → durable staged trades → all-child reconciliation gate → chronological/idempotent promotion → live Execution/LivePosition. Commit `b5783d421f64fcb8e7f1d75f1af5185fd9029f59` adds integration tests for the real service composition, repeat-run behavior, sibling reconciliation failure, and paper-account isolation. No state transition or order-submission wiring was changed. CI is pending confirmation for this commit; do not treat the new test coverage as passing until verified.


### Latest test checkpoint

Commit `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88` makes the integration test start with no staged rows, verifying the real intake transition (broker trade response → durable staged record) before status confirmation and promotion. CI is not yet verified for this SHA; no test pass is claimed.

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


## Latest retry-path test checkpoint

Commit `1a3475c69d3a93ece7bfad22ace4dce52231bfa1` adds a service-composition regression for: broker read/reconcile → fresh staged trade intake → first fill accounted → second-fill charge estimation fails → retry skips the already-accounted fill and accounts the remaining fill. This is test intent only until exact-SHA CI passes. Live order submission remains outside this state machine.


## Account-safety interlock — new, not yet wired to submission

Before any future live order may be considered, the account-level persisted safety decision must be checked in addition to the existing environment interlocks and pre-trade risk gate. The decision is denied if state is absent, kill switch is tripped, circuit is not CLOSED, error counter is nonzero, health check is missing/stale, or the database read fails. Threshold broker errors open the circuit and trip the latch. Only an explicit manual reset after a fresh passing health check and zero consecutive errors can clear the latch. Service/migration/tests are committed but exact-head CI is pending. No order route or worker currently invokes this service.


### Latest safety reset verification note

The account-safety manual-reset test correction is in commit `c97be866828bd47a23f22fc44fac2d3359e70f35`. Reset remains denied without health evidence or while consecutive broker errors remain; after the error counter is cleared, a new passing health check is required before explicit manual reset. Exact-SHA CI is pending; no order-submission wiring was added.

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
