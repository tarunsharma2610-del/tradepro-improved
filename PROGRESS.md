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

- Branch `safety/fail-closed-trading-mode`; PR #1 draft/open/unmerged; original `Tradepro` untouched.
- Latest verified code/test SHA `e7a2ca8d473f9536839b02e0538bf6768343a627`: [Actions #39112247035](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39112247035) — **326 passed, 1 warning in 26.85s**; SQLite Alembic upgrade passed.
- Implemented the fail-closed account-wide risk gate, strict read-only Upstox snapshots and credential-bound async preflight coordinator. Token/connection changes during asynchronous snapshot collection are detected.
- Tests use mocked broker responses only. The coordinator is not wired to routes/workers, submits no order and changes no accounting; live mode remains disabled.
- Real broker behavior, PostgreSQL migration behavior, exact-head frontend build, staging and production readiness remain unverified.

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

**Phase 2:** live lifecycle safety foundations. The durable intent/tag recovery task is complete; the account-wide risk-gate foundation is now implemented and verified.

**Next:** design an async preflight orchestration boundary to connect the collector to the risk gate only after environment, confirmation and ownership gates pass. Add tests proving rejected requests make no broker snapshot calls. Keep it unregistered and do not add live submission.

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


## Continuation checkpoint — 18 October 2026: service-composition integration tests

- Change commit: `b5783d421f64fcb8e7f1d75f1af5185fd9029f59` ([GitHub](https://github.com/tarunsharma2610-del/tradepro-improved/commit/b5783d421f64fcb8e7f1d75f1af5185fd9029f59)).
- Added two tests to `backend/tests/test_live_order_fill_reconciliation_coordinator.py` that use the real child reconciler/trade ingestion, coordinator, promotion service, and accounting service; only Upstox read responses and charge estimation are mocked.
- Intended assertions: successful chronological promotion and duplicate-safe replay; a sibling broker-status failure prevents any promotion; paper cash and paper positions stay unchanged; no order-write calls.
- Status: **committed; CI pending/unverified at time of this note**. No test result is claimed here. Check CI for this exact SHA before marking complete.
- Next: inspect CI, fix only observed failures, and then update this file plus roadmap/audit/handover with exact final evidence. Do not recreate the already-existing coordinator.


### Superseding code checkpoint

Latest test code commit is `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88`. It strengthens the earlier `b5783d421f64fcb8e7f1d75f1af5185fd9029f59` test commit by removing pre-seeded staged trades, forcing real ingestion to insert the mocked broker trades. CI is still unverified for this exact SHA; do not mark the tests passing until confirmed.

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


## Latest task — real-service partial promotion retry regression

- Committed test change: `1a3475c69d3a93ece7bfad22ace4dce52231bfa1`.
- Added a real-service integration test where trade intake/reconciliation succeed, the first fill is accounted, charge estimation fails for the second fill, and a subsequent retry must account only the missing fill while recognizing the first as duplicate.
- Expected checks: 1 execution after first attempt; 2 executions after retry; one live position of quantity 2; no paper cash/position changes; no broker write calls.
- Status: **committed; CI and execution result not verified in this continuation**. Do not mark green without workflow evidence.
- Next: inspect CI for the exact SHA. If green, add/verify PostgreSQL integration coverage for this lifecycle before considering any runtime wiring.


## Latest task — persistent account-wide safety state and circuit breaker

- Service: `backend/app/services/live_account_safety_service.py`.
- Migration: `backend/alembic/versions/202610180009_live_account_safety.py`, revision `202610180009` after `202610180008`.
- Tests: `backend/tests/test_live_account_safety_service.py`.
- Latest code/test commit: `57939799b7e8b436d5095924b86a89ce380a956e`.
- Behavior implemented: missing state denies; initialization is kill-switch-tripped; broker errors increment a durable counter and open circuit/trip kill switch at threshold; idempotency keys suppress duplicate events; broker success does not close an open circuit; reset requires a fresh passing health check, zero error count, an explicit reason and actor; stale/unknown state denies.
- Verification: **not verified yet**. GitHub status checks and associated workflow runs were empty for the exact head. Do not claim tests/migrations passed. Await backend Actions run covering pytest, SQLite and PostgreSQL 16 Alembic upgrades.
- Next: CI verification, then PostgreSQL concurrency tests and read-only preflight composition. No live order submission wiring.


### Superseding test correction

Latest code/test commit: `c97be866828bd47a23f22fc44fac2d3359e70f35`. The manual-reset test now establishes a fresh passing health check before asserting that a nonzero broker-error counter blocks reset, then requires broker success and a second fresh passing health check before reset can succeed. This supersedes `57939799b7e8b436d5095924b86a89ce380a956e`. Exact-SHA GitHub status and workflow queries returned no results; no test pass is claimed.

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


## Security-control endpoint audit checkpoint — 18 October 2026

- Added [SECURITY_CONTROL_ENDPOINT_AUDIT.md](SECURITY_CONTROL_ENDPOINT_AUDIT.md) in commit [10d87d9d9010b2c48ebcf25c832a2ea574100889](https://github.com/tarunsharma2610-del/tradepro-improved/commit/10d87d9d9010b2c48ebcf25c832a2ea574100889).
- Static review covered auth dependencies/JWT, MFA routes, admin guard, route registration, audit-log helper/model, safety-event service, manual order route, strategy evaluate route and worker entry points.
- Positive controls: authenticated user dependency, server-side admin guard, tenant ownership checks in reviewed routes, MFA capability, audit persistence helper, and fail-closed preflight service.
- Open gaps: no operator audit-read endpoint; no separate safety permissions; no step-up auth for reset; audit transaction/immutability and metadata policy need design; cookie-CSRF and malformed JWT subject handling need hardening; safety-control HTTP tests do not exist yet.
- No API endpoint or live-order integration was added. This is a design-gate audit, not a penetration test. Keep PR #1 draft and live order submission disabled.
- **Next:** approve permission model, atomic state+event persistence, event schema/redaction and operator audit read scopes; then map every broker-write/retry entry point before endpoint design or wiring.


## Order-entry path inventory checkpoint — 18 October 2026

- Added [ORDER_ENTRY_PATH_INVENTORY.md](ORDER_ENTRY_PATH_INVENTORY.md), commit [a477489c7e2d5b6883c299c1e9a8aee1cbef055f](https://github.com/tarunsharma2610-del/tradepro-improved/commit/a477489c7e2d5b6883c299c1e9a8aee1cbef055f).
- Static inventory covered manual portfolio order/cancel routes, manual strategy evaluation, scheduled worker, shared PAPER execution service, strategy enter/exit, Upstox adapter write primitives, live preflight, intent recovery, and fill reconciliation.
- Current manual and strategy order callers use a shared PAPER-only service that rejects non-PAPER mode. Adapter place/modify/cancel write methods exist, but no production caller was found in reviewed service paths. Live intent recovery still uses LiveExecutionService directly rather than the account-safety-aware LivePreflightCoordinator; it does not submit orders, but this composition gap must be resolved before exposure.
- No runtime code changed. No order route or worker was wired to live preflight. Keep TRADING_MODE=PAPER and LIVE_ORDER_SUBMISSION_ENABLED=false. Static review is not production sign-off.
- **Next:** design the single allowed broker-write service, state/audit atomicity, permission model and source-call guardrails; then add tests before wiring any entry path.


## Central broker-write boundary design checkpoint — 18 October 2026

- Added `CENTRAL_BROKER_WRITE_BOUNDARY_DESIGN.md` (commit `40f9ca652cf4bf5e86ed51a9c5f21a3071ce7e06`) defining the sole approved broker-write service, operation policies, account-wide safety composition, atomic intent/event transaction, unknown submission recovery, scoped permissions, operator audit visibility, MFA step-up, CSRF/Origin controls, database append-only enforcement, CI source guard and test matrix.
- **Docs/design only:** no application code or endpoints changed; no routes/workers were wired; no broker writes were enabled.
- Baseline remains: last verified backend CI #611 had 398 passed / 4 skipped; later documentation commits were not covered by a new backend run. PR #1 is open/draft. Keep `TRADING_MODE=PAPER` and `LIVE_ORDER_SUBMISSION_ENABLED=false`.
- **Next engineering step:** review and implement storage transaction/append-only protections with PostgreSQL tests, then authorization/step-up/CSRF foundations and malformed JWT handling. Only then implement the typed broker-write boundary, source-call CI guard, safety API and end-to-end path wiring. Phase 2 is not complete.


### Broker-write source guard checkpoint — 18 October 2026

- Added `backend/scripts/check_broker_write_boundary.py`, three scanner behavior tests, and a required workflow step. Commit: `04583cd35ecf5360624bc0164c7b91231a058e5e`.
- The scanner flags attribute references to `place_order`, `modify_order`, and `cancel_order` under production `backend/app` sources except the low-level adapter definitions and the exact future boundary file `app/services/live_broker_write_service.py`. The test suite covers unapproved call rejection, the exact allowlist, and method-reference alias detection.
- CI run #614 is in progress at the time of this checkpoint: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123034569. Do not mark it passed until the run concludes.
- This is guardrail work only. Central writer, permissions, safety API, audit storage hardening and route/worker composition remain pending; Phase 2 remains incomplete.


### Guard false-positive correction — 18 October 2026

- CI run #614 exposed a real scanner-design false positive: generic `.place_order()` matches included PAPER `ExecutionService` methods and docstring text, not just broker-adapter writes. Run #614 failed at the guard step before the suite ran: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123034569.
- Corrected the guard to inspect adapter-named receivers (e.g. `adapter.place_order`, `self.adapter.cancel_order`) rather than generic service method names. This keeps normal paper execution calls outside the broker-adapter scan while preserving explicit adapter naming as a source convention. Commit: `30599b1bd8d32293b856c88cdfb4e2facaa9ce0f`.
- New CI run #615 is pending: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123199888. Await its result before treating the guard as verified. The scanner cannot detect dynamic dispatch/reflection and is one layer of defense, not proof of safety.


### AST scanner correction / latest verification — 18 October 2026

- Guard run #615 then exposed a second false positive from a `.place_order` mention in a docstring; it failed before pytest, not because an order path wrote to the broker: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123199888.
- Replaced line regex with AST inspection so comments/docstrings are ignored and adapter-named attribute references are checked; added a regression test for docstring mentions. Commits: `a5d0acd58d582e53263965cb17f05a9cc89035eb`, `bdf208efcc32b44a6367157dd2ab0aab946e6574`.
- Latest run #617 has passed the broker-write guard and is currently running the full test suite; migration and PostgreSQL integration steps are pending: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123311281.
- **Not yet verified:** the complete CI workflow. Do not proceed on the assumption that the whole suite passed until the run completes.


### Verified source guard and backend CI checkpoint — 18 October 2026

- **PASS — CI run #617:** https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123311281
- Verified code/test SHA: `bdf208efcc32b44a6367157dd2ab0aab946e6574`.
- Broker-write source guard passed. Full backend suite: **402 passed, 4 skipped, 1 warning in 29.81s**. SQLite Alembic upgrade passed. PostgreSQL 16 Alembic upgrade passed. PostgreSQL concurrency integration tests: **4 passed in 0.39s**.
- The two preceding guard runs failed before pytest due scanner false positives (PAPER service method matching, then a docstring mention); both were corrected. The successful AST-based scanner is covered by regression tests and ignores comments/docstrings.
- Later commits to progress/handover/roadmap/instructions are documentation-only and are not part of SHA `bdf208e`; the verified code files and workflow configuration are unchanged by those doc updates.
- Guardrail is now verified on the exact code SHA above. It is a static guard and cannot prove safety against dynamic dispatch/reflection. Central writer, transaction/append-only hardening, scoped permissions, safety API, route/worker composition and end-to-end negative tests remain pending. Phase 2 remains incomplete.


## Safety-event storage hardening checkpoint — 18 October 2026

- Added Alembic revision `202610180011` (`backend/alembic/versions/202610180011_safety_event_immutability.py`) after `202610180010`. It adds a request fingerprint and per-state unique event version constraint, plus SQLite and PostgreSQL triggers rejecting event UPDATE/DELETE.
- Added SHA-256 request fingerprints to new safety events. Reusing a state-scoped idempotency key with a different or unverifiable payload now fails closed; the broker-error threshold and reset expected version are part of the fingerprint.
- Added optional expected-version validation to manual reset; stale versions are rejected before changing the state. The future safety-control API must require this field rather than rely on the service's compatibility default.
- State mutation and audit insert remain in the same SQLAlchemy transaction. Added a regression test proving audit-insert failure rolls back the safety-state change, plus idempotency mismatch/threshold and stale-version tests.
- Added PostgreSQL integration coverage that attempts direct event UPDATE and DELETE and verifies both are rejected and the event remains unchanged.
- Earlier CI run #612? Do not infer a run number here: run [#? pending current head](https://github.com/tarunsharma2610-del/tradepro-improved/actions) must be checked against the exact latest code SHA before declaring this whole checkpoint verified. Run #39124213016 (SHA `2b38a0f0ba4dd167419ec116a630ebe63fabac92`) passed guard, tests, SQLite/PostgreSQL migrations and concurrency checks, but it predates the expected-version/threshold-context additions. Latest code CI run #39124312326 is pending at this checkpoint: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39124312326.
- No endpoints, central writer, route/worker wiring or broker writes were added. Keep `TRADING_MODE=PAPER`, `LIVE_ORDER_SUBMISSION_ENABLED=false`, PR #1 draft/open/unmerged, and the original `Tradepro` repository untouched. Phase 2 remains incomplete.


### Expected-version regression-test correction — 18 October 2026

Run #39124312326 failed with 405 passed / 1 failed / 5 skipped because the test kept a reference to a mutable ORM state object; its `health.version` reflected the later trip mutation instead of the earlier version. This was a test setup defect, not a failure of the version comparison. The test now snapshots the integer before the mutation in commit `6cd0ced108e35d715359d649a463d80709dd1fb1`. Latest CI run #39124498280 is queued/pending: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39124498280. Await exact-head results before marking storage hardening verified.


### Verified safety-event storage checkpoint — 18 October 2026 (supersedes pending note)

- **PASS:** GitHub Actions run #625, URL https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39124498280, exact code/test SHA `6cd0ced108e35d715359d649a463d80709dd1fb1`.
- AST broker-write guard passed. Backend suite: **406 passed, 5 skipped, 1 warning in 29.76s**. SQLite Alembic upgrade passed. PostgreSQL 16 Alembic upgrade passed. PostgreSQL charge-adjustment/account-safety integration: **5 passed in 0.69s**, including direct audit UPDATE/DELETE rejection.
- The stale-version test now captures the version integer before mutating the ORM row; exact-head verification is green. Subsequent documentation commits do not change the verified code/test/workflow files.
- Storage hardening checkpoint verified. Authorization/MFA/CSRF, central writer, safety-control API and route/worker/recovery composition remain pending. Phase 2 remains incomplete; live submission remains disabled.


## Authorization foundation checkpoint — 18 October 2026

- Added explicit User.safety_permissions grants with an empty default and migration 202610180012 chained after safety-event immutability revision 202610180011. Allowlisted permissions: safety.status.read, safety.audit.read, safety.kill_switch.trip, safety.reset. is_admin grants none of them.
- Added require_safety_permission() (default deny), normalized malformed signed JWT subject UUIDs to HTTP 401, and added require_same_origin_for_cookie_mutation() for future cookie-authenticated POST/PUT/PATCH/DELETE routes.
- Added regression tests for admin-without-permission denial, explicit permission acceptance, unknown permission rejection, malformed JWT subject handling, and allowed/missing/untrusted Origin behavior.
- Commits created by the GitHub API: c20aa41 (auth dependency), 87d151f (user model), a52d1ea / 1344ee6 (permission migration; portable SQLite/PostgreSQL version), 7ad2502 (tests), and c10a8e6 / 504c105 (Origin guard and tests). These commits have not yet been verified by CI.
- Important incomplete controls: recent-MFA step-up is not implemented; Origin guard is reusable but not attached to any safety route; permission-grant administration/bootstrapping is not implemented; safety status/audit/trip/reset routes remain unregistered. No live-order path was wired.
- Next: implement a dedicated recent-MFA step-up challenge and dependency with HTTP tests; then enforce tenant/account scope in safety route design and attach CSRF/Origin + permission dependencies before adding any safety-control endpoint. Keep live trading disabled and PR #1 draft/unmerged.

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

- Updated `GET /api/v1/admin/safety/audit` to read `LiveAccountSafetyEvent` joined to `LiveAccountSafetyState`, rather than legacy `AuditLog`. Tenant scoping is applied in SQL using authenticated-user state ownership before count/pagination; callers cannot select another user/state. Output omits idempotency keys and request fingerprints.
- Reworked the tenant-isolation/pagination HTTP test to seed durable safety events for two account owners and a non-safety legacy audit row. It checks tenant isolation and excludes sensitive replay metadata from the response.
- Commits: endpoint `cd68384c48a98f2bd2ded054f37bb04d24885b12`; test `7913f821a7ac194c537adf911a4ef39ba4410e41`.
- Verification: exact-head CI/status lookup returned no runs/statuses for the latest test commit. Tests have **not** been run in this environment; this change is committed but unverified until CI runs against the current branch head. No live broker write was called.
- Next: verify/fix current-head CI, review reset/idempotency and endpoint transaction behavior, then implement and enforce the central broker-write boundary across API, strategy workers, recovery/retry and adapter paths. Phase 2 remains incomplete. Keep PAPER mode, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.


## Phase 2 checkpoint — MFA purpose separation (18 October 2026)

- Changed the MFA step-up request to accept only two explicit purposes: `safety.reset` (default for backward compatibility) and `safety.admin.permissions`. Permission-management purpose issuance is denied unless the authenticated user is a platform admin.
- Changed the recent-MFA dependency into a purpose-specific dependency factory. A token for `safety.reset` no longer satisfies the permission-grant/revoke route, which now requires `safety.admin.permissions`; unknown scopes fail at dependency construction. The issued purpose is included in the MFA step-up audit metadata.
- Added/updated HTTP and dependency regression tests for admin purpose usage, non-admin denial, and cross-purpose token rejection.
- Commits: schema `4c09723127b545fe111adc6bf6ff70cd509fa13d`; dependency `36e23c178b7fadcee0f5b9d0304363d6093cf9f3`; auth issuance `61dfcc54abe66825a2f3eccfc728920a3faef7c8`; admin route `af9b1d32b3d91d313a0cd9451f2b60f4a60d2df1`; tests `c9e35bc102c14683c4c1a8216abd9f6cd19908e` and `9d5eee236f252a5b8ef6c263553ac89100a52c44`.
- Verification remains pending: tests were not run locally; query available for exact-head workflow/status returned no records on the previous checkpoint and must be repeated for this latest head. Do not treat this change as passing until CI executes.
- Next: run CI and address failures, review the full safety MFA dependency/route matrix, then proceed to the central broker-write boundary. PAPER mode and disabled live order submission remain mandatory; Phase 2 is incomplete.


- Follow-up integration fix: explicitly bound `/api/v1/safety/kill-switch/reset` to the `safety.reset` MFA dependency after introducing the scope-specific dependency factory. Commit: `c0e20109f1372109c81dca06cba528ea8c2c37c8`. This is also unverified pending CI.


## Authorization/MFA route-matrix verification checkpoint — 18 October 2026

- During matrix review, identified a compatibility defect in the first scoped-MFA dependency refactor: existing direct unit tests and callers invoke `require_recent_safety_mfa(step_up_token=..., user=...)`, so turning that function itself into a factory would break those calls. Corrected by restoring `require_recent_safety_mfa` as the default `safety.reset` validator and adding `require_recent_safety_mfa_scope(scope)` for FastAPI route dependencies. Reset and admin permission routes now explicitly use their corresponding scope-specific dependency.
- Added route-level regression coverage proving a `safety.reset` token cannot grant safety permissions; existing coverage includes non-admin privilege denial, direct cross-purpose rejection, stale tokens, disabled MFA, wrong user/scope, Origin checks, default-deny permissions, tenant isolation, idempotency-header validation, and safe reset requiring fresh health evidence.
- Relevant commits: dependency compatibility fix `24b463894eca1fde37381bef66d47366a806fe32`; route wiring `0cfc3e290dbc730af9fb854954a95875809ad3cf` and `17088f172d40aa106d1cd1d5f8b674c056919a86`; test matrix update `6e77aa77a7c0bba84d2aae539b37fa6228c088b9`; route-level cross-purpose test `c40edddbeb8b65ec468ae0419897d1cd6cc2c325`.
- CI: GitHub Actions backend workflow is running for the preceding dependency/test commit (`39132630566`) and queued for latest route-level test commit (`39132698515`). The preceding run has not yet reached pytest; do not mark the matrix passed until latest-head workflow concludes. Monitor [latest workflow run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39132698515).
- Still outstanding: wait for latest-head CI; fix any failures and re-run; verify SQLite/PostgreSQL migrations and concurrency checks. This is a route-matrix review, not a complete authorization/security certification. PAPER mode remains mandatory, live broker order submission remains disabled, PR #1 remains draft/open/unmerged, and Phase 2 is incomplete.


## CI failure triage update — 18 October 2026

- GitHub Actions run `39132630566` failed at `Run test suite`: `433 passed, 5 skipped, 1 failed`. The single failure was `test_non_admin_cannot_request_permission_management_step_up`, which returned 401 rather than the expected 403 because its test fixture enabled MFA but did not mock TOTP verification. The authorization code was not reached by that test.
- Fixed the test fixture to mock a valid `123456` TOTP code, isolating the authorization behavior under test. Fix commit: `b5c96fc5115bd4b9fae7be6fc0a168d55c5ace9c`.
- A new backend CI run is in progress for the fix: [run 39132803282](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39132803282). Do not consider the suite green until this exact-head run finishes successfully. Previous failures skipped migrations/concurrency stages because pytest failed first.


## CI verification result — PASS (18 October 2026)

- Backend workflow run `39132803282` passed for backend commit `b5c96fc5115bd4b9fae7be6fc0a168d55c5ace9c`: broker-write boundary guard passed; full backend suite **435 passed, 5 skipped, 1 warning**; SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL account-safety/charge-adjustment concurrency tests **5 passed**. One Starlette/AnyIO deprecation warning remains non-blocking.
- The earlier failing test was corrected by mocking valid TOTP in the non-admin purpose-denial test; the passing run confirms the corrected test setup and current backend changes. Documentation-only commits followed, so the tested application code is unchanged, but the docs commit itself did not trigger backend CI due workflow path filters.
- This is evidence for the current authorization/MFA test changes and listed CI gates, not a complete security certification or Phase 2 completion. Continue with broader authorization route matrix and broker-write boundary implementation; live order submission remains disabled and PAPER mode remains mandatory.


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
