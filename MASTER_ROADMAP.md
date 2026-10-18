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

## Immediate task — gate before further implementation
1. Re-read the current PR #1 head SHA and check Actions/check status.
2. If a run exists, inspect backend, migration and frontend jobs/logs. Fix only evidenced defects; rerun relevant checks.
3. If no run is available through the current integration, document that limitation and use repository GitHub Actions UI to inspect or trigger the configured workflow. Do not claim success.
4. Record exact run URL/SHA, test count, warning count, migration result and frontend result in `PROGRESS.md`, `AUDIT_REPORT.md`, `HANDOVER.md`, and `CHANGELOG.md`. Update this roadmap too.
5. Do not advance to live-service wiring until the margin parser change is verified.

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
