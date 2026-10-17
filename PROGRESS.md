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
- Latest backend CI for that code commit: [run 39031184000](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39031184000) — **189 tests passed, 1 warning**, clean SQLite Alembic upgrade passed.
- Latest frontend CI for that code commit: [run 39031184092](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39031184092) — TypeScript and Next.js build both passed.
- These checks validate the commit above, not any future changes. Re-check CI after each new code commit.

## Completed and committed work (safety branch)

1. Added a PAPER-only fail-closed order-placement guard; LIVE/unknown modes are rejected by the paper execution service.
2. Updated the Upstox HFT place-order endpoint and added a mocked endpoint/payload regression test. No real broker orders were placed.
3. Added optional per-portfolio client idempotency-key protection and tests for duplicate/reused keys.
4. Made paper fill accounting atomic across order status, aggregate position, cash and execution persistence, with rollback regression coverage.
5. Added strategy-owned position allocations and strategy-specific realized P&L. Strategy execution no longer treats a manual/other-strategy position as its own; manual delivery sells are prevented from consuming strategy-allocated shares.
6. Added fail-closed futures/options validation to backend order, strategy and backtest paths and removed unsupported derivative choices from relevant UI forms.
7. Added a migration to backfill strategy-specific P&L and open strategy allocations from existing strategy-tagged executions.
8. Updated README, audit, handover, changelog and live-safeguards documentation across the branch.

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

**Next task (do not skip the audit):** add a targeted migration regression test for `202610170003_strategy_position_attribution.py` that starts from revision `202610170002`, seeds realistic legacy strategy-tagged BUY/SELL executions and existing strategy/instrument/portfolio rows, upgrades to head, and verifies:
- the new `strategy_realized_pnl` values on historical executions;
- remaining open strategy quantity and average entry price;
- realized P&L for a fully closed strategy position;
- correct handling of legacy strategy-tagged sales that would create a negative position under the new long-only strategy allocation;
- idempotent/clean upgrade behavior and no loss of aggregate portfolio records.

Before writing that test, inspect `backend/alembic/env.py`, the three latest migrations, test/dependency setup and CI workflow. Pick a migration-test method compatible with the repository's actual configuration. Do not change the migration's behavior unless a test demonstrates a defect. Add the smallest test and run it in CI. If the populated-data test fails, stop and diagnose the exact migration/data issue before editing it again.

## Task state

- [x] Re-read the original `Pasted text(6).txt` from the Library in full.
- [x] Re-inspect current branch head, main SHA, PR state, latest backend/frontend CI.
- [x] Re-read README, HANDOVER, requirements audit, audit report, changelog and live safeguards.
- [x] Identify the next concrete gap from the audit: populated legacy migration backfill is untested.
- [ ] Commit the verbatim project instruction file and this progress log to the improved branch.
- [ ] Add and run the populated legacy migration regression test.
- [ ] Update progress with test result, code commit SHA and next task.
