# Tradepro Improved — Master Roadmap

Last reviewed: 18 October 2026
Working branch: `safety/fail-closed-trading-mode`
Pull request: #1 (draft; do not merge without explicit review)

## Operating rules
- Work only in `tarunsharma2610-del/tradepro-improved`; leave original `Tradepro` untouched.
- Read `PROJECT_INSTRUCTIONS.md`, this roadmap, `PROGRESS.md`, `AUDIT_REPORT.md`, `REQUIREMENTS_AUDIT.md`, `HANDOVER.md`, and `LIVE_ORDER_STATE_MACHINE.md` before substantive work.
- Preserve functioning code; prefer small, targeted changes. Update this roadmap and the relevant status files whenever a task is completed.
- Never claim a test passed unless it was actually executed. No live orders for testing. Live trading remains disabled and the existing PAPER-only execution guard must remain in place.

## Current verified state

### Implemented in code; current CI verification pending
- Additive schema foundations for broker child orders, order tags, partial/unknown order state and deduplicated broker trade IDs.
- Pure response parsers for place-order IDs, order details, order history, order trades and Funds & Margin V3.
- Read-only Upstox adapter methods for Funds & Margin V3 and instrument margin estimates (`POST /v2/charges/margin`), with local input validation.
- Pure `parse_margin_details` returning typed `MarginEstimate` / `MarginBreakdown`; tests cover a documented success payload and malformed/error payloads.
- Documentation status is intentionally **implemented but not verified by CI for the current PR head**.

### Last verified baseline (not verification of the newest margin parser)
- Previously reported CI: 238 backend tests passed, one warning; migration and frontend checks passed on an earlier code commit.
- Current PR head had no workflow runs or commit statuses returned by the connected GitHub integration at the last check. This is a verification gap, not a pass or failure.
- Do not reuse the old baseline as evidence that new tests passed.

## Immediate task — Phase 2 verification gate (current; supersedes older gate notes)

1. Current code/test target: `b780c39f770a6839dab0af63fc424c341eff9d70`. The later documentation commits do not change code; use the latest PR head to start the workflow and record both SHAs.
2. Verify the margin parser changes and broker-trade intake/migration changes together: run `.github/workflows/backend-tests.yml` on `safety/fail-closed-trading-mode` using `workflow_dispatch` from GitHub Actions, or obtain a workflow run tied to the current code. The workflow runs backend pytest and `alembic upgrade head` on SQLite.
3. The connected GitHub integration has no workflow-dispatch action and current branch/head lookup returns no Actions run. Do not use an older `main` run as evidence. If the UI must be used, this is the explicit manual gate.
4. Inspect actual logs; fix only evidenced defects; rerun after fixes. Record exact run URL/SHA, test count, warning count, migration result, and frontend result if run in `PROGRESS.md`, `AUDIT_REPORT.md`, `REQUIREMENTS_AUDIT.md`, `HANDOVER.md`, and `CHANGELOG.md`.
5. Keep the PR draft/unmerged and Live Trading disabled. Do not begin the next live lifecycle task until the current code/migration gate passes.


## Next implementation phase after verification
Follow `LIVE_ORDER_STATE_MACHINE.md` implementation order:
1. Build a separate, initially unregistered `LiveExecutionService` with explicit fail-closed gates and mocked tests. Do not change the existing paper `ExecutionService` or route any real orders.
2. Add stable idempotency/tag recovery for ambiguous submissions and prove a retry cannot submit a duplicate.
3. Add broker reconciliation for parent/child orders and status events, including partial fills and restart recovery.
4. Apply broker trade-ID deduplication and atomic accounting updates.
5. Add account-wide pre-trade risk checks (funds vs pledged margin, order notional, position/exposure, daily loss, order frequency, market session/stale quote) and an account-level kill switch.
6. Test paper/live isolation, concurrent submissions, migrations on clean and populated databases, and broker error/timeout paths.
7. Only after independent review and authorized sandbox/staging evidence may live API/UI wiring be considered. Obtain explicit user authorization before any real order path can be enabled.

## Release blockers
- Current PR CI for the new margin parser/tests is not confirmed.
- A complete live order lifecycle and broker reconciliation are not verified end-to-end.
- Live risk controls, account-level kill switch, OAuth/token operational recovery and production prerequisites require further verification.
- Live trading is **NOT READY**. Keep it disabled.


### 18 October 2026 — broker-reconciliation CI investigation

- Added regression coverage for an Upstox status-check failure response; commit `2625191740554efe5a41f99eff15306ebd68ec5c`.
- Investigated workflow run `39028914012` (`Backend pytest`): it ran against the earlier PR merge checkout `d04dfa5` and reported `177 passed, 3 errors`; all three errors were fixture setup failures (`portfolio` not found) in that checkout. The current branch version of `backend/tests/test_broker_reconciliation.py` defines the fixture, but this alone is not proof the current branch passes.
- The GitHub integration's commit-SHA workflow lookup and combined-status lookup returned no results for the current branch head. The old failed run is not a valid test of current head `2625191740554efe5a41f99eff15306ebd68ec5c`; current CI remains unverified.
- Next: inspect the latest PR run in GitHub Actions (PR workflows check out the generated merge ref), confirm backend tests, migration and frontend results, and fix only current-head failures. Do not claim green CI or enable live trading.


## Authoritative continuation checkpoint — 18 October 2026

This checkpoint supersedes the earlier “next implementation phase after verification” sequencing above. The current concrete task is **broker-trade/fill ingestion**, not live order submission/service wiring.

1. Audit `Execution`, `BrokerOrder`, `Order`, broker-connection ownership, migrations, and accounting repositories/services. Confirm what fields and uniqueness guarantees actually exist.
2. Review `parse_order_trades` / `BrokerTrade` and tests; reuse them rather than duplicate the parser.
3. Implement a transaction-safe ingestion path for broker-confirmed fills only, with durable deduplication and explicit mapping to the correct local order/child broker order. Resolve whether uniqueness should be scoped to broker connection/account instead of only broker name.
4. Add regression tests for replayed trades, repeated ingestion, wrong/missing child-order mapping, invalid quantity/price/side, transaction rollback, and separation from paper accounting. Do not infer fills from status events.
5. Run/inspect current-head CI and migrations. Record only evidence for the exact tested SHA.
6. Update progress/audit/handover/changelog after the code/test commit. Keep the PAPER-only guard; no real order placement, live service registration, or PR merge.

Current PR #1 head last observed: `540e1285d3de934b43829948a1b60c67658d1343`. Workflow-run and combined-status lookups returned no results for that head, so verification remains pending. The project is **not live-trading ready**.


## Broker trade intake — implementation present, verification gate open (18 October 2026)

**Implemented on the safety branch:** normalized staging table and service, idempotency scoped to broker connection, ownership and child-order mapping checks, validation of side/quantity/price/instrument, conflicting replay rejection, quantity bound checks, and tests for paper isolation and same trade IDs across users. Schema migrations 005 and 006 add the staging table and scope broker order/execution identity constraints by connection.

**Important limit:** this records broker trade intake only; it does not account fills, change order states, update positions/cash/P&L, or call the broker. It is not wired to a route, worker, or live execution service. Actual live accounting, actual fee reconciliation, partial-fill aggregation and restart recovery remain incomplete.

**Current gate:** backend test suite and Alembic upgrade must pass on current head `32eea17c141d4cfbc727eed2ff2a1b40d21dbba3`. The connected GitHub API returned no workflow runs/statuses for this SHA and the local runtime could not clone GitHub due unavailable DNS. Do not proceed to live accounting wiring until current-head tests/migrations are verified.

Next sequence: (1) verify/fix current implementation, (2) add populated migration backfill coverage for connection-scoped IDs, (3) design actual charge reconciliation and safe live accounting promotion, (4) only later integrate a dedicated live lifecycle. PAPER-only guard stays in force; no merge or real orders.


### Latest test-scope update — 18 October 2026

Added populated legacy-data coverage for migration 006: a child order and execution created before the connection-scope migration must be backfilled to the owner's broker connection. Current head is `a68c336e4a35ccc0bfe4d6539760ad03e40672f1`; the verification gate remains open until CI proves the new test and full migration chain pass.


### Final verification clarification — 18 October 2026

Code/test target SHA: `a68c336e4a35ccc0bfe4d6539760ad03e40672f1`. The later branch commits only updated documentation; at the check, the PR head was `1b0056d9739cd55d50cd5484cddf955aa8bf07db`, with no workflow run/status returned. The verification gate is still open.


## Latest Phase 2 checkpoint — 18 October 2026

The latest code hardening commit is `2cdbbe290f8b661cb91110dbb4e165fcef36f800`; targeted regression tests were committed at `b780c39f770a6839dab0af63fc424c341eff9d70`. Intake now binds to the exact broker connection, rejects foreign/unbound connection references, requires a matching instrument token, and validates malformed side values. Documentation commits after the code/test commit update the progress/audit/handover files only. The current-head Actions result is absent; these changes are not verified. The next task after this gate passes is the separate, initially unregistered `LiveExecutionService` foundation with mocked tests, then durable submission recovery and broker lifecycle reconciliation in the order above. The intake service remains staging-only; no real orders, no live wiring, no merge.


### Latest regression coverage — 18 October 2026

Commit `264aa4c609d522cd01d07e8213bfee6f14c7a2bf` adds a test proving legacy child orders without a determinable broker connection are rejected by trade intake. This is added coverage, not a test pass. Current code/test target is `264aa4c609d522cd01d07e8213bfee6f14c7a2bf`; the verification gate stays open.


## Branch divergence / PR safety note — 18 October 2026

The latest repository comparison reports PR branch `safety/fail-closed-trading-mode` is **198 commits ahead and 349 commits behind** current `main` (main SHA observed: `a2767e646ec19248e9b2c4a3d8fc688195c91eb3`; merge base: `2cf83089070e064c61f3b75fcb6b663021cbf625`). PR #1 remains draft/open/unmerged. This comparison makes merge/rebase unsafe to do casually: before any merge or rebase, audit the new main changes and reconcile conflicts in a separate reviewed step. Do not merge PR #1 as part of this task; keep working isolated on the safety branch and do not modify `main` or the original `Tradepro` repository.
