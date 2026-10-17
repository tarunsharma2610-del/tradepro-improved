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

- Last code commit reviewed before this progress-file commit: `ac93eb82688d573f9839da48ef1182d9929e56c4` — “Remove duplicate strategy model imports”.
- At that point, branch head was `ac93eb82688d573f9839da48ef1182d9929e56c4`; main remained `2cf83089070e064c61f3b75fcb6b663021cbf625`.
- PR #1 was open, draft, and not merged.
- Baseline CI before the migration regression test: backend [run 39031184000](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39031184000) — 189 passed, 1 warning, clean SQLite Alembic upgrade; frontend [run 39031184092](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39031184092) — TypeScript and Next.js build passed.
- Migration regression-test commit: `1fe681246cb88a9505302a1763128c51ab72802d` — [backend run 39031526388](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39031526388) 190 passed, 1 warning; clean SQLite Alembic upgrade; [frontend run 39031526360](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39031526360) passed.
- Latest idempotency code commit: `044243476acce70dccc02fcc0e9d61b98bcd62ff`. Its first backend run failed because the test assumed a ₹30,000 quote exceeded the default cap, but the strategy test fixture has ₹500,000 virtual capital (25% cap = ₹125,000). This was a test-setup defect, not a strategy-idempotency failure. The test was made deterministic by explicitly setting a 1% cap.
- Latest verified code commit before Upstox endpoint update: `e9f8b7bb56f3300d1016195a773a26845d94d717` — [backend run 39032153163](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032153163) 193 passed, 1 warning, clean SQLite migration; [frontend run 39032153157](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032153157) passed.
- Latest verified code commit before V3 modify/cancel methods: `ded6138b93f8e18f96117f5bb4fce0ec8aeaeb1b` — [backend run 39032413141](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032413141) 193 passed, 1 warning and clean migration; [frontend run 39032413150](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032413150) passed.
- Latest verified code commit: `2bc21c59dc4c9b8d1cd2e38d24a611433e07d82c` — [backend run 39032570839](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032570839) **195 passed, 1 warning**, clean SQLite migration; [frontend run 39032570823](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032570823) TypeScript and Next.js build passed.
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


## Current active task: audit live broker execution readiness

**Next step:** review existing `BrokerAdapter` methods, Upstox adapter endpoints, `BrokerReconciliationService`, broker-status API, order metadata/model, OAuth/token handling, risk checks and tests. Do not wire real submission into the paper service. First map what exists vs what is missing and validate endpoint semantics against current official Upstox documentation. The first implementation task should be the smallest safe read-only or state-management improvement with mocked tests; keep the PAPER-only guard and never place real orders.


## Completed task: add Upstox V3 modify/cancel adapter methods

The `BrokerAdapter` interface and Upstox implementation now expose V3 modify and cancel methods. Mocked tests verify method URLs, payload/query, and response shape. They are not wired to the UI or execution service and do not change local order status/accounting. Latest CI passed with 195 backend tests and frontend checks.

## Current active task: audit prerequisites for a separate live execution service

Next, inspect the current risk engine, instrument validation, broker token/authorization handling, order state model, reconciliation service and all relevant tests. Produce a precise gap matrix for a separate live service: pre-trade risk checks, explicit enablement/confirmation, order tag/idempotency, broker response parsing (V3 may return multiple `order_ids`), partial fills, cancel/modify confirmation, timeout/restart recovery, trade-book reconciliation, and broker/local position mismatch handling. Do not implement or wire real submission until this audit demonstrates the required safe lifecycle; keep `ExecutionService.place_order` PAPER-only.
