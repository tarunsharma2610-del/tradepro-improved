# Tradepro Improved — Persistent Progress Log

Last updated: 2026-10-18  
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

- Latest previously verified code commit: `e6abb6704b67c54f35bb5d7c2c41acd96846147d` — “Restore Upstox response helper to adapter class”. The branch has since received additional documentation-only commits; always retrieve the current PR head from PR #1 before checking CI. The new margin parser/tests are committed but CI for the current head is not yet confirmed. Backend [run 39035755714](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39035755714): **238 passed, 1 warning**, clean SQLite Alembic upgrade; frontend [run 39035755707](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39035755707): TypeScript and Next.js build passed.
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

## Completed code change; verification pending: audit and type-parse the margin-calculation response

1. Official docs and existing parser/test code were inspected; the response was raw and no matching typed parser existed.
2. Added `MarginEstimate`, `MarginBreakdown`, and pure `parse_margin_details`; added valid-response and malformed/error tests.
3. Code commit: `3c4dd6ac0d7d88a18916c241d28a224fc5031d5d`; test commit: `6995f64429b44134edfa5985ad4f50c3b54cfcab`.
4. Documentation has been updated in progress, handover, changelog and audit. **Tests have not been verified for the current PR head.** The last confirmed backend run was 238 passed with one warning and the frontend build passed on the prior code commit. Do not reuse those counts for this change.


## Completed code task: typed Upstox margin-estimate parser — 18 October 2026

- Cross-checked the official [Upstox Margin Details API](https://upstox.com/developer/api-documentation/margin/). The documented success payload has data.margins[] plus data.required_margin and data.final_margin; each row has seven numeric margin components.
- Added immutable typed MarginEstimate and MarginBreakdown results plus pure parse_margin_details. It rejects unsuccessful envelopes, missing/empty margin rows, missing fields, malformed/non-finite amounts and negative margin values.
- Added tests for the documented futures-style response and malformed/error cases. The parser remains read-only and is not connected to order approval.
- Code commits: parser 3c4dd6ac0d7d88a18916c241d28a224fc5031d5d; tests 6995f64429b44134edfa5985ad4f50c3b54cfcab.
- **Verification pending:** do not mark this task verified until GitHub Actions completes for the test commit and any failure is inspected. No live broker request or order was made.

## Next task

Check CI for the margin parser/test commits. If green, record the exact test/migration/frontend results and commit final documentation updates. If red, inspect failing job logs, correct the specific defect, rerun CI, and update this file before moving on. Keep live trading disabled.


## Immediate next action — Phase 2 CI verification gate

Verify the current broker-trade intake hardening and the earlier margin parser using `.github/workflows/backend-tests.yml` on `safety/fail-closed-trading-mode`. Current code/test target: `b780c39f770a6839dab0af63fc424c341eff9d70`; subsequent documentation commits do not alter code. The connected GitHub integration exposes no workflow-dispatch action and returned no run for this branch/head, so manually dispatch the workflow from GitHub Actions or obtain a run tied to this code. The workflow runs backend pytest and SQLite `alembic upgrade head`. Record the actual run URL/SHA, test count, warning count, migration outcome and any frontend result; do not claim success based on historical CI. Fix failures before the next Phase 2 task. Keep PR #1 draft/unmerged and live trading disabled.


## Status correction — 18 October 2026 (supersedes stale next-step notes)

The following are now present in the branch: `BrokerAdapter.get_margin_details`, the Upstox `POST /v2/charges/margin` implementation with local request validation, pure `parse_margin_details`, and unit tests for success/error/malformed response shapes. Older notes saying the adapter method or typed parser is still missing are historical snapshots, not current status. The parser is read-only and is not used to authorize orders.

The current blocker is verification: the GitHub integration returned no workflow run and no commit status for the current PR head when checked. Earlier CI results (238 backend tests, one warning, migration/frontend checks green) belong to an older commit and do not verify the margin parser changes. No pass/fail conclusion is possible from the available evidence. Inspect or trigger the configured workflow from GitHub Actions and record actual results before advancing.

`MASTER_ROADMAP.md` is now the current sequencing guide. After this verification gate, the next implementation phase is a separate, initially unregistered `LiveExecutionService` with mocked tests, while preserving the current PAPER-only execution guard. Do not merge the draft PR, place real orders, or enable live trading.


### 18 October 2026 — broker-reconciliation CI investigation

- Added regression coverage for an Upstox status-check failure response; commit `2625191740554efe5a41f99eff15306ebd68ec5c`.
- Investigated workflow run `39028914012` (`Backend pytest`): it ran against the earlier PR merge checkout `d04dfa5` and reported `177 passed, 3 errors`; all three errors were fixture setup failures (`portfolio` not found) in that checkout. The current branch version of `backend/tests/test_broker_reconciliation.py` defines the fixture, but this alone is not proof the current branch passes.
- The GitHub integration's commit-SHA workflow lookup and combined-status lookup returned no results for the current branch head. The old failed run is not a valid test of current head `2625191740554efe5a41f99eff15306ebd68ec5c`; current CI remains unverified.
- Next: inspect the latest PR run in GitHub Actions (PR workflows check out the generated merge ref), confirm backend tests, migration and frontend results, and fix only current-head failures. Do not claim green CI or enable live trading.


## Authoritative continuation checkpoint — 18 October 2026

This section supersedes older “current task/next task” paragraphs elsewhere in this file. Historical entries above remain a record of earlier work and must not be read as the current next step.

- Repository/branch: `tarunsharma2610-del/tradepro-improved` / `safety/fail-closed-trading-mode`. Original `tarunsharma2610-del/Tradepro` remains untouched.
- PR #1 is open, draft, and unmerged. Latest PR head observed before this checkpoint: `540e1285d3de934b43829948a1b60c67658d1343`.
- The PR-head workflow lookup and combined-status lookup returned no runs/statuses. Current-head CI is **unverified**. Earlier green CI results apply only to their explicitly listed older commits; the old failing run `39028914012` used an earlier merge checkout and is not proof of current-head status.
- Present foundation: Upstox trade response parser `parse_order_trades` and typed `BrokerTrade`; additive `BrokerOrder` child-order model; nullable execution broker references; unique constraint on `(broker_name, broker_trade_id)`; read-only order/trade/history adapter methods. These pieces are not yet wired into fill ingestion/accounting.
- Critical schema/audit question to resolve before implementation: trade identity is currently unique by broker name + trade ID, not by broker connection/account + trade ID. Check whether this is sufficiently scoped for multiple users/accounts; do not assume it is.
- **Current implementation task:** audit the exact execution schema, migrations, connection ownership and accounting path; then implement broker-confirmed trade ingestion with transactional idempotency and tests. Do not mutate paper accounting from broker fills, infer a fill from status alone, submit live orders, or enable live trading.
- No new ingestion code has been claimed complete in this checkpoint. Do not mark the task done until code/tests are committed and current CI evidence is recorded.

### Current sequence
1. [x] Commit this progress/audit/roadmap/handover/changelog checkpoint before more feature work.
2. [ ] Audit relevant code, migrations, ownership boundaries and test fixtures for fill ingestion.
3. [ ] Implement only the verified missing ingestion/idempotency behavior and regression tests.
4. [ ] Verify tests/CI; record exact commit and results. If CI cannot be retrieved, explicitly leave verification pending.
5. [ ] Update this log and audit docs after implementation; stop before wiring any live order-submission path.


## Latest implementation checkpoint — 18 October 2026 (code committed; verification pending)

- Code commits for this task: initial ingestion implementation `e5052d791aed71eb4e393165902a3505a73bc55e`; connection-scoped broker identity correction `bd91bd577b470897097bb45a09a61dc6516baab2`; cross-account regression test `0865dcf2ddbafba43a4adbc1c3ab6a0c841aa5d7`; migration regression fixture update `32eea17c141d4cfbc727eed2ff2a1b40d21dbba3`. The current branch head is `32eea17c141d4cfbc727eed2ff2a1b40d21dbba3`.
- Added `BrokerTradeRecord` as a separate normalized intake/staging table, plus `BrokerTradeIngestionService`. It checks LIVE-only scope, user ownership, local-to-broker child-order mapping, connection binding, side, quantity, price, instrument token, replay consistency, and total ingested quantity. Duplicate identical trades are skipped; conflicting reuse is rejected.
- Staging is deliberately **not an accounted Execution**. The service does not alter order status, child-order fill totals, paper/live cash, positions, or P&L. Charge calculation and safe promotion into live accounting remain separate work.
- Added migrations `202610180005_broker_trade_ingestion.py` and `202610180006_broker_connection_scoped_trade_ids.py`. Broker child-order and execution uniqueness are now scoped to broker connection rather than globally by broker name/trade ID; legacy child rows are backfilled when the owner's connection can be identified and otherwise remain unusable by the fail-closed ingestion service.
- Added `backend/tests/test_broker_trade_ingestion.py` for replay idempotency, paper-order rejection, child-order mismatch, malformed/overfilled trade data, conflicting replay, ownership, batch safety and same trade ID across separate user connections. Updated `test_live_broker_schema_migration.py` to exercise the connection-scoped schema.
- **Verification is still pending.** The GitHub workflow/status lookup for current head `32eea17c141d4cfbc727eed2ff2a1b40d21dbba3` returned no runs/statuses. Network access from the local execution environment was unavailable, so no local test run is claimed. Do not treat older CI as validation of these changes.
- Next gate: obtain backend pytest + migration upgrade results for the current head. Fix any failures before calling the ingestion task verified. Do not wire this staging service into live execution or enable live trading.


### Verification checkpoint correction — 18 October 2026

The migration test suite now also includes `test_connection_scope_migration_backfills_existing_broker_links`, which seeds a pre-006 child order and execution and asserts migration 006 backfills both to the owning connection. Latest branch head is `a68c336e4a35ccc0bfe4d6539760ad03e40672f1`. Current-head Actions/status still needs a fresh check; no test result is claimed until that SHA is actually tested.


### Final checkpoint clarification — 18 October 2026

The last **code/test** commit for this task is `a68c336e4a35ccc0bfe4d6539760ad03e40672f1`. The subsequent commits updating README/architecture/progress/audit/handover/roadmap/changelog/requirements audit are documentation-only. The PR head observed after those docs updates was `1b0056d9739cd55d50cd5484cddf955aa8bf07db`; no workflow run or combined status was returned for that observed head. Do not confuse an earlier green run on the previous code with verification of this ingestion/migration work.


## Continuation checkpoint — 18 October 2026 (Phase 2 broker-trade intake hardening)

Read before continuing: `PROJECT_INSTRUCTIONS.md`, `ARCHITECTURE.md`, `MASTER_ROADMAP.md`, this progress log, `AUDIT_REPORT.md`, `REQUIREMENTS_AUDIT.md`, `HANDOVER.md`, and `LIVE_ORDER_STATE_MACHINE.md`. The instructions require audit-first changes, preservation of paper execution, targeted regression tests, honest verification reporting, and no live orders.

### Code changes in this continuation

- Code commit `2cdbbe290f8b661cb91110dbb4e165fcef36f800`: broker trade ingestion now resolves the exact connection recorded on the broker child order and verifies that connection belongs to the requesting user and expected broker. It no longer looks up a connection merely by user/broker and then compares afterward.
- Test commit `b780c39f770a6839dab0af63fc424c341eff9d70`: regression tests now cover a child order linked to another user's connection, missing instrument identity, and invalid non-text side data. Intake now fails closed when the broker trade row has no instrument token to validate against the local instrument.
- Accounting boundary unchanged: records are staged in `broker_trade_records`; no `Execution` is created, and no order state, child fill aggregate, cash, position, or P&L is modified. No broker call or live submission is wired.

### Verification status

The current code/test target is `b780c39f770a6839dab0af63fc424c341eff9d70`. Direct GitHub Actions lookup shows no workflow run for the safety branch/current SHA; the connected GitHub tools expose workflow inspection and reruns, but no workflow-dispatch action. The local runtime has no usable GitHub network path, so pytest and Alembic have not been run locally. **These new tests and migrations are not yet verified; no pass is claimed.** The old green baseline belongs to earlier commits only.

### Required gate and next action

1. Manually run `.github/workflows/backend-tests.yml` with `workflow_dispatch` from GitHub Actions on branch `safety/fail-closed-trading-mode`, or otherwise obtain a run tied to the current code. The workflow runs backend pytest and `alembic upgrade head` on SQLite.
2. Inspect the actual logs; fix failures and rerun. Record exact SHA, test count, warning count, migration outcome, and frontend status if separately run.
3. Only after this gate passes, continue Phase 2 with the next audited live-lifecycle foundation task. Do not register/wire the service, merge PR #1, deploy migrations to production, or enable/place live orders.


### Additional Phase 2 regression test — 18 October 2026

Added `test_ingestion_rejects_legacy_child_order_without_connection_binding` in commit `264aa4c609d522cd01d07e8213bfee6f14c7a2bf`. This covers legacy child-order rows whose connection ID remains NULL after migration backfill cannot safely identify an owner connection; ingestion must reject them without creating staging records. Latest code/test target is now `264aa4c609d522cd01d07e8213bfee6f14c7a2bf`. Test/migration execution remains pending.


## Branch divergence / PR safety note — 18 October 2026

The latest repository comparison reports PR branch `safety/fail-closed-trading-mode` is **198 commits ahead and 349 commits behind** current `main` (main SHA observed: `a2767e646ec19248e9b2c4a3d8fc688195c91eb3`; merge base: `2cf83089070e064c61f3b75fcb6b663021cbf625`). PR #1 remains draft/open/unmerged. This comparison makes merge/rebase unsafe to do casually: before any merge or rebase, audit the new main changes and reconcile conflicts in a separate reviewed step. Do not merge PR #1 as part of this task; keep working isolated on the safety branch and do not modify `main` or the original `Tradepro` repository.


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

- Latest verified code/workflow SHA: `677fcf882e0ce1e6e02be3bb8df0d074b8fbf220`; subsequent commits only update documentation. Current branch head after those docs commits: `7fb582f5ce75165f178e296472beb0a50cd03ac9`.
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
