# Tradepro Improved — Persistent Progress Log

Last updated: 2026-10-17  
Repository: `tarunsharma2610-del/tradepro-improved`  
Working branch: `safety/fail-closed-trading-mode`  
Original repository: `tarunsharma2610-del/Tradepro` — **must remain untouched**  
Pull request: [#1 — draft, open, not merged](https://github.com/tarunsharma2610-del/tradepro-improved/pull/1)

## How every continuation must start

1. Read `PROJECT_INSTRUCTIONS.md` in full.
2. Read this `PROGRESS.md` in full.
3. Read `README.md`, `HANDOVER.md`, and `REQUIREMENTS_AUDIT.md`.
4. Verify the branch head, PR status and latest GitHub Actions results. Never assume a remembered SHA is current.
5. Inspect only files relevant to the next task; search for existing implementation and tests before editing.
6. State the current task and expected files before making code changes.
7. Make one coherent, minimal change. Add targeted regression tests.
8. Verify tests from actual results. If local execution is unavailable, say so and wait for CI; do not claim unrun tests passed.
9. Commit the code and tests. Only then mark the task complete.
10. Update this file, `HANDOVER.md`, and `CHANGELOG.md` when behavior changes. Commit the progress update too.
11. Stop at the end of the coherent task and state the next step. Do not merge PR #1 without explicit authorization.

## Current verified repository state

- Latest verified code commit: `e6abb6704b67c54f35bb5d7c2c41acd96846147d` — “Restore Upstox response helper to adapter class”. Backend [run 39035755714](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39035755714): **238 passed, 1 warning**, clean SQLite Alembic upgrade; frontend [run 39035755707](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39035755707): TypeScript and Next.js build passed.
- Main remains `2cf83089070e064c61f3b75fcb6b663021cbf625`; all code changes remain on the safety branch.
- PR #1 was open, draft, and not merged.
- Baseline CI before the migration regression test: backend [run 39031184000](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39031184000) — 189 passed, 1 warning, clean SQLite Alembic upgrade; frontend [run 39031184092](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39031184092) — TypeScript and Next.js build passed.
- Migration regression-test commit: `1fe681246cb88a9505302a1763128c51ab72802d` — [backend run 39031526388](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39031526388) 190 passed, 1 warning; clean SQLite Alembic upgrade; [frontend run 39031526360](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39031526360) passed.
- Latest idempotency code commit: `044243476acce70dccc02fcc0e9d61b98bcd62ff`. Its first backend run failed because the test assumed a ₹30,000 quote exceeded the default cap, but the strategy test fixture has ₹500,000 virtual capital (25% cap = ₹125,000). This was a test-setup defect, not a strategy-idempotency failure. The test was made deterministic by explicitly setting a 1% cap.
- Latest verified code commit before Upstox endpoint update: `e9f8b7bb56f3300d1016195a773a26845d94d717` — [backend run 39032153163](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032153163) 193 passed, 1 warning, clean SQLite migration; [frontend run 39032153157](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032153157) passed.
- Latest verified code commit before V3 modify/cancel methods: `ded6138b93f8e18f96117f5bb4fce0ec8aeaeb1b` — [backend run 39032413141](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032413141) 193 passed, 1 warning and clean migration; [frontend run 39032413150](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032413150) passed.
- Latest verified code commit before status-response hardening: `2bc21c59dc4c9b8d1cd2e38d24a611433e07d82c` — [backend run 39032570839](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032570839) 195 passed, 1 warning and clean migration; [frontend run 39032570823](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032570823) passed.
- Latest verified code commit before per-order trade lookup: `9f1e1300acc15f85d8abf1e29e73de34f6ca14f3` — backend [run 39032760874](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032760874), 195 passed, 1 warning and clean migration; frontend [run 39032760872](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032760872) passed.
- Latest verified code commit before order-history lookup: `ebda043d4537353529007b8f3aa1aacceb13d4c4` — backend [run 39032909906](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032909906), 197 passed, 1 warning and clean migration; frontend [run 39032909935](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032909935) passed.
- Latest verified code commit before broker schema foundation: `8b66df970d2dda91c060583ed6065c0101cd7837` — backend [run 39033094768](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033094768), 200 passed, 1 warning and clean migration; frontend [run 39033094833](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033094833) passed.
- Latest verified code commit before pure response parsing: `dbd83c878753e7a0cb6e2a7935c55378ee56d7cb` — backend [run 39033460748](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033460748), 201 passed, 1 warning and clean migration; frontend [run 39033460785](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033460785) passed.
- Latest verified code commit before funds adapter: `0d1ececff933e3271576096756192036963805ba` — backend [run 39033704367](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033704367), 223 passed, 1 warning and clean migration; frontend [run 39033704247](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033704247) passed.
- Latest verified code commit before funds parser: `6f92a7f9ead0f9fe2da6222e122945a3f419bd1c` — backend [run 39033992221](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033992221), 225 passed, 1 warning and clean migration; frontend [run 39033992223](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033992223) passed.
- Latest verified code commit: `27e87cca48c03528f5fe5fee5816ff2aa4438caa` — [backend run 39034164505](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39034164505) **235 passed, 1 warning**, clean SQLite migration; [frontend run 39034164514](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39034164514) TypeScript and Next.js build passed.
- The initial order-history commit run failed because the new test omitted its `AsyncMock` import. The failure was identified from CI logs, the import was added in the follow-up commit, and the latest full CI then passed.
- These checks validate the listed commit only, not future changes. Re-check CI after each code commit.

## Completed and committed work (safety branch)

1. Added a PAPER-only fail-closed order-placement guard; LIVE/unknown modes are rejected by the paper execution service.
2. Updated the Upstox HFT place-order endpoint and added a mocked endpoint/payload regression test. No real broker orders were placed.
3. Added optional per-portfolio client idempotency-key protection and tests for duplicate/reused keys.
4. Made paper fill accounting atomic across order status, aggregate position, cash and execution persistence, with rollback regression coverage.
5. Added strategy-owned position allocations and strategy-specific realized P&L. Strategy execution no longer treats a manual/other-strategy position as its own; manual delivery sells are prevented from consuming strategy-allocated shares.
6. Added fail-closed futures/options validation to backend order, strategy and backtest paths and removed unsupported derivative choices from relevant UI forms.
7. Added a migration to backfill strategy-specific P&L and open strategy allocations from existing strategy-tagged executions.
8. Added `PROJECT_INSTRUCTIONS.md` with the complete verbatim instruction text from `Pasted text(6).txt`, and this persistent `PROGRESS.md` with current branch/CI state and next step.
9. Added `backend/tests/test_strategy_position_migration.py`, which upgrades a populated database from revision 002 to head and verifies closed/open positions, weighted average, realized P&L, over-sell attribution, preservation of aggregate positions/cash, and repeat upgrade. It passed in CI.
10. Strategy orders now use stable keys scoped to strategy + side + latest candle timestamp. Strategies skip automated order submission if the latest candle has no parseable timestamp. Idempotency validation also rejects reusing the same key across manual vs strategy orders or different strategy IDs.
11. Added tests for repeated same-candle entry retries, missing candle timestamps and idempotency-key scope. Latest suite: 193 passed, 1 warning; migration and frontend checks passed.
12. Updated README, audit, handover, changelog and live-safeguards documentation across the branch.
13. Audited current official Upstox order documentation and changed the isolated adapter's place-order endpoint from deprecated V2 to V3. The mocked test checks the V3 URL and V3 response shape (`data.order_ids`); no real broker request was sent.
14. Added V3 `modify_order` and `cancel_order` methods to the `BrokerAdapter` interface and Upstox implementation, plus mocked endpoint tests. They are not wired to execution or UI and do not mutate local order/accounting state.
15. Hardened read-only broker status checks to require a non-empty returned `order_id` that exactly matches the requested broker order before saving status. Added a missing-ID regression test; no local fill/accounting state is inferred.
16. Added read-only `get_order_trades(access_token, order_id)` to the broker interface and Upstox adapter using the documented `/v2/order/trades` endpoint, with mocked query/response tests. It is not wired into accounting.
17. Added read-only `get_order_history(access_token, order_id=None, tag=None)` using the documented `/v2/order/history` endpoint. It requires a non-empty order ID and/or tag, enforces the documented 40-character tag limit, and has mocked tests for tag lookup, ID lookup and invalid queries. It is not wired to submission/recovery yet.
18. Added additive live broker schema foundations: unique nullable `Order.broker_tag`, expanded order status length for partial/unknown states, `BrokerOrder` child rows for multiple broker IDs, and broker-trade identity fields/uniqueness on `Execution`. Added migration 004 and a populated legacy-data regression test. These fields are not used by execution yet.
19. Added pure typed response parsers for Place Order V3, Order Details, Order History and Order Trades. Tests cover missing/malformed payloads, mismatched IDs, duplicate child IDs/trade IDs, invalid quantities/prices, and empty history/trade lists. Official Order History is a timeline, so multiple status events with the same order ID are correctly accepted.
20. Added read-only Upstox Funds & Margin V3 support to the broker interface and adapter, including the required `Api-Version: 3.0` header. Mocked tests verify endpoint, response shape, header and the official 423 maintenance error; this data is not used to approve orders yet.
21. Added a pure typed Funds & Margin V3 parser that preserves separate available-to-trade, cash and pledged-margin totals; validates realized/unrealized loss and signed unsettled profit; and rejects missing/malformed/error payloads. It is not wired into order approval.

## Known limitations / not complete

- **Live trading is NOT READY and must remain disabled.** The current paper execution service does not implement the full live broker order lifecycle.
- Broker-confirmed partial fills, cancellations, unknown timeout/restart reconciliation and broker-side idempotency are not complete.
- Frontend/strategy callers do not yet consistently use stable idempotency keys; evaluation-level de-duplication still needs work.
- Full instrument-master mapping, tick-size unit normalization, derivative contracts/lot sizing/margin accounting are not complete. Futures/options are deliberately rejected.
- Portfolio-wide exposure limits and a broker-error circuit breaker need review/implementation.
- Migration `202610170003_strategy_position_attribution.py` has passed a clean SQLite upgrade, but its **legacy-data backfill has not yet been tested against a populated pre-migration database**.
- Production/staging rollout, TLS, broker/compliance prerequisites and real Upstox end-to-end verification remain unverified.
- Latest CI reports one warning; inspect it before deciding whether it needs action. Do not upgrade dependencies just to remove a warning without proving it is necessary.

## Current phase and next task

**Current focus:** trading safety and accounting correctness, before implementing live submission.

**Completed task:** add a targeted migration regression test for `202610170003_strategy_position_attribution.py` that starts from revision `202610170002`, seeds realistic legacy strategy-tagged BUY/SELL executions and existing strategy/instrument/portfolio rows, upgrades to head, and verifies:
- the new `strategy_realized_pnl` values on historical executions;
- remaining open strategy quantity and average entry price;
- realized P&L for a fully closed strategy position;
- correct handling of legacy strategy-tagged sales that would create a negative position under the new long-only strategy allocation;
- idempotent/clean upgrade behavior and no loss of aggregate portfolio records.

Completed verification: the populated legacy migration test passed as part of the full CI suite (193 passed).

## Task state

- [x] Re-read the original `Pasted text(6).txt` from the Library in full.
- [x] Re-inspect current branch head, main SHA, PR state, latest backend/frontend CI.
- [x] Re-read README, HANDOVER, requirements audit, audit report, changelog and live safeguards.
- [x] Identify the next concrete gap from the audit: populated legacy migration backfill is untested.
- [x] Commit the verbatim project instruction file and this progress log to the improved branch (instruction/progress commit: `197d645a06f173ee717cc23bee7b88d7f5ed9034`).
- [x] Add and run the populated legacy migration regression test (test commit: `1fe681246cb88a9505302a1763128c51ab72802d`; backend CI 190 passed, 1 warning; frontend CI passed).
- [x] Update progress with test result, code commit SHA and next task.


## Next-task audit plan — stable order idempotency

**Task:** inspect the existing order-creation callers and worker/scheduler paths to determine whether they generate/reuse a stable idempotency key for retries and repeated strategy evaluations. Do not add a second idempotency service: first inspect the existing `ExecutionService`, order API schemas/routes, frontend order submit handler, strategy scheduler/worker, and current idempotency tests. Identify whether the key is generated client-side, persisted, reused for the same logical action, and scoped correctly. Then implement only the proven gap and add a regression test for repeated evaluation/retry. Keep paper/live isolation and existing API contracts intact. No live orders.


## Completed task: add Upstox V3 modify/cancel adapter methods

The `BrokerAdapter` interface and Upstox implementation now expose V3 modify and cancel methods. Mocked tests verify method URLs, payload/query, and response shape. They are not wired to the UI or execution service and do not change local order status/accounting. Latest CI passed with 195 backend tests and frontend checks.

## Completed audit: live broker execution prerequisites

- `ExecutionService.place_order` is explicitly PAPER-only and rejects LIVE/unknown mode before order creation. Keep this guard.
- OAuth state is signed, user/broker/connection-bound, expiring and single-use; tokens are encrypted and expired tokens are not returned. Token refresh/reconnection automation is not implemented.
- `validate_instrument_segment` intentionally permits only verified equity instruments and rejects derivatives. Current risk engine has strategy and automated-entry portfolio loss limits, and a paper order-notional cap; it does not supply live/manual all-order exposure limits or a broker-error circuit breaker.
- `Order` has basic local states plus separate broker metadata, but no PARTIALLY_FILLED state. The reconciliation service is read-only and does not update local fills/cash/positions. There is no broker trade-book reconciliation or restart-safe live order submission lifecycle.
- Upstox V3 place response returns `data.order_ids` (plural list). Modify/cancel V3 adapter methods now exist but are not wired. A future live service must define multi-ID/slicing behavior, idempotency, partial fills, timeout ambiguity, confirmed cancel/modify, and broker/local position reconciliation before any real order can be enabled.

## Completed task: require exact order identity in broker status responses

The read-only reconciliation service now rejects a missing/blank `order_id` and a mismatched ID before recording broker status. The mocked regression test confirms local order status and fill timestamp remain unchanged. CI passed: backend 195 passed, 1 warning and migration check; frontend checks passed.

## Completed task: add read-only per-order trade lookup

Added `get_order_trades(access_token, order_id)` to the adapter interface and Upstox implementation using the documented `GET /v2/order/trades?order_id=...` endpoint. A mocked test checks the route, query and trade-list response. It is not wired into accounting. Latest CI: 197 passed, 1 warning, migration and frontend checks passed.

## Completed task: add read-only order-history lookup by stable tag

Added `get_order_history(access_token, order_id=None, tag=None)` using the official `GET /v2/order/history` endpoint. It rejects empty identifiers, blank values and tags longer than 40 characters before any request. Mocked tests cover tag lookup, order-ID lookup, and invalid queries. Initial CI exposed a missing test import; the log was inspected, the import fixed in a follow-up commit, and the latest full suite passed: 200 passed, 1 warning, migration and frontend checks passed.

## Completed task: live order state-machine design

Added `LIVE_ORDER_STATE_MACHINE.md`, covering current audit findings, official Upstox V3 response shapes, multi-order mapping, stable tag recovery, partial fills, trade-ID deduplication, modify/cancel confirmation, timeout/restart recovery, risk gates, schema needs, tests and release criteria. This is design only; no live submission was implemented and the PAPER-only gate is unchanged.

## Completed task: additive broker-order/trade schema foundation

Added migration `202610170004_live_broker_order_state.py`, `BrokerOrder`, a unique nullable `Order.broker_tag`, expanded status length, and nullable execution fields linking to broker child orders and unique broker trade IDs. The populated migration test starts from revision 003, upgrades a database containing a paper order/execution, verifies existing paper data remains intact, allows multiple broker child IDs per local order, rejects duplicate broker order IDs/trade IDs, and accepts `PARTIALLY_FILLED`. Latest CI: 201 passed, 1 warning, migration and frontend checks passed. New structures are not wired into execution.

## Completed task: pure Upstox response validation helpers

Added `backend/app/brokers/upstox/response_parsing.py` with typed immutable results and pure validation for V3 place response IDs, order details, order history and order trades. The test suite covers malformed/missing fields, wrong order IDs, duplicate child IDs/trade IDs, invalid quantities/prices, and valid empty history/trade lists. A docs cross-check caught an important detail: Order History is a timeline and can legitimately repeat the same order ID for different status events; the parser was corrected to allow this. Latest CI: 223 passed, 1 warning, clean migration and frontend checks passed. The parsers are not wired into live execution.

## Completed audit: live pre-trade risk controls

- `RiskEngine.check_can_enter` is strategy/automated-entry focused; portfolio loss uses realized P&L only and does not block manual orders. Strategy loss also uses realized P&L, not unrealized drawdown.
- `ExecutionService` has a paper-only mode gate, paper order-notional cap, virtual cash check, delivery-holding checks and strategy-allocation protection. These controls do not authorize live orders and must not be reused as if they were a complete live risk system.
- Instrument validation deliberately allows only verified NSE/BSE equities. It has no derivative lot/tick/margin support.
- Missing live prerequisites: no funds/margin API in the broker interface, no verified broker-available-funds check, no all-order live exposure/position/daily loss/rate limits, no stale-quote or market-session guard, and no account-level live circuit breaker. `AUTOMATED_ENTRIES_ENABLED` is only an automated-strategy entry stop, not a live-account kill switch.
- Official Upstox released Funds & Margin V3 on 10 April 2026. It returns `available_to_trade.total` and a detailed cash/pledge breakdown at `GET https://api.upstox.com/v3/user/get-funds-and-margin`, requiring `Api-Version: 3.0` and no segment parameter. See [official docs](https://upstox.com/developer/api-documentation/get-funds-and-margin-v3/) and [announcement](https://upstox.com/developer/api-documentation/announcements/get-funds-and-margin-v3/).

## Completed task: read-only Upstox Funds & Margin V3 support

Added `get_funds_and_margin` to the adapter interface and Upstox implementation using `GET https://api.upstox.com/v3/user/get-funds-and-margin` with the required `Api-Version: 3.0` header. Mocked tests verify URL, headers, the documented `available_to_trade` response structure and preservation of the 423 maintenance error. Latest CI: 225 passed, 1 warning, clean migration and frontend checks passed. The method is not used to approve orders.

## Completed task: parse Funds & Margin V3 safely

Added `FundsAndMarginV3` and `parse_funds_and_margin_v3`. It validates the nested response and numeric values, preserves cash and pledged margin separately, rejects malformed/error payloads, and preserves signed unsettled profit/loss values. Tests include missing nested fields, NaN/Infinity/negative available values, malformed unsettled profit and 423/error envelopes. Latest CI: 235 passed, 1 warning, migration and frontend checks passed. Parser is not used to approve orders.

## Completed task: read-only Upstox instrument margin calculation

- Added `get_margin_details` to the broker interface and Upstox adapter using `POST https://api.upstox.com/v2/charges/margin`.
- Added local input validation for non-empty batches of at most 20 instruments, unique non-empty keys, positive integer quantities, supported transaction types/products, and finite positive optional prices. Inputs are normalized before sending. Mocked tests verify endpoint/payload and reject invalid requests before network access; broker errors remain errors and never approve an order.
- First CI attempt exposed missing `Decimal`/`InvalidOperation` imports and `_to_result` accidentally nested inside the module-level validator. The first correction fixed imports but repeated the helper-placement issue; logs were checked and the exact indentation/scope defect was then corrected. This debugging history is recorded so a future continuation does not repeat the mistake.
- Latest verified code commit `e6abb6704b67c54f35bb5d7c2c41acd96846147d`: backend **238 passed, 1 warning**, clean SQLite Alembic upgrade ([run 39035755714](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39035755714)); frontend TypeScript/build passed ([run 39035755707](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39035755707)).
- This is a read-only margin estimate only. It is not connected to order approval, does not validate live funds, and is not a complete risk preflight.

## Next task (not started): audit and type-parse the margin-calculation response

1. Read the official current Upstox Margin Details docs and inspect representative documented success/error response structures.
2. Inspect existing broker result parsers and tests first; do not duplicate an existing parser.
3. Add a small typed parser only if the current response is raw/unvalidated and a typed result materially improves correctness. Validate required fields, numeric finiteness/non-negativity where appropriate, and error envelopes.
4. Add mocked tests for valid response, missing/malformed fields and broker errors. Do not connect it to order approval or enable live trading.
5. Run targeted tests, full backend suite/migration check and frontend checks if shared interfaces change. Then update `PROGRESS.md`, `HANDOVER.md`, and `CHANGELOG.md` and commit the progress update.
