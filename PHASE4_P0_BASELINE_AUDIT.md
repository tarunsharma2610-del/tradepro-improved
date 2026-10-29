# Phase 4 P4-0 Baseline Audit — 29 October 2026

## Scope and method
- Repository audited: `tarunsharma2610-del/tradepro-improved` only.
- Branch: `phase4/roadmap-progress-checkpoints`.
- Audit commit baseline: `39952e8d091a6ed55d7eff2cb9a48f60c4e1288d` (Phase 4 planning/doc checkpoint head).
- Audit is static inspection of tracked GitHub source and workflows. No runtime tests or deployed credentialed smoke tests were executed in this audit.
- Original `tarunsharma2610-del/Tradepro` repository was not accessed or modified.

## Executive result
The repository already contains substantial backend functionality: authenticated Upstox OAuth/API adapter, a user-scoped Market Data Feed V3 streamer with reconnect/stale-data handling, strategy/backtest services, portfolio risk checks, paper order/fill accounting, charge/GST/IPFT services, extensive backend tests, and CI checks for broker-write boundaries and SQLite/PostgreSQL migration round-trips plus synthetic restore.

Therefore Phase 4 should harden existing functionality rather than rewrite it. The most important confirmed follow-up is to make the PAPER-only configuration an enforceable fail-closed invariant at startup and to strengthen regression coverage around every route that could reach broker order-write methods. Existing code already labels `TRADING_MODE=LIVE` as not implemented, and the paper execution service writes `trading_mode="PAPER"`; nevertheless, `main.py` currently only logs a warning if the mode is LIVE, so configuration alone does not fail startup. The adapter contains an HTTP `place_order` implementation; current static guard limits unapproved call references, but dynamic/reflection bypasses are explicitly not fully proven safe by the scanner. Treat this as defense-in-depth hardening, not evidence that live orders have been sent.

## Evidence-based gap matrix

| Area | Current evidence | Audit status | Next action |
|---|---|---|---|
| Branch/checkpoint | Phase 4 roadmap, progress and checkpoint records created | Present; exact-head CI still unverified | Establish a green exact-head CI checkpoint before claiming green |
| Paper execution | `ExecutionService.place_order` sets new orders to `trading_mode="PAPER"`; risk checks apply to MARKET and LIMIT paths | Implemented in inspected path; full acceptance not re-run in this audit | Add/retain tests proving mode configuration cannot route orders to broker writes |
| Broker-write boundary | `backend/scripts/check_broker_write_boundary.py` AST guard and `test_broker_write_boundary_guard.py`; backend workflow runs guard | Present, with documented static-analysis limitation | Add a startup hard stop for non-PAPER mode and targeted tests; preserve the guard |
| Upstox OAuth | Adapter exchanges auth code, computes next 03:30 IST expiry; credential service is used for tokens | Present; account-specific refresh/reconnect remains operationally unverified | Audit token refresh/expiry paths and test expired-token failure behavior |
| Upstox market data | `upstox_market_data_streamer.py` uses V3 authorize handshake, user-scoped token provider, bounded reconnect and stale tick rejection | Implemented in code; live credentials not tested | Verify streamer lifecycle/authorization error cases in tests; real smoke test remains deployment-gated |
| Strategy and risk | Strategy execution routes through shared ExecutionService; portfolio risk checks include open/pending exposure | Present | Verify emergency stop and entry/exit asymmetry under direct/manual evaluation |
| Paper lifecycle | Execution, position, cost estimator and charge-total modules/tests exist | Present; Phase 4 full lifecycle review pending | Trace order→fill→position→P&L→estimated charges, including failure rollback/replay |
| Accounting | Phase 3 per-fill allocation, evidence, GST/IPFT and reconciliation modules/tests exist | Preserve; do not reopen without regression | Regression-test estimates/aggregate API never become per-fill actual evidence |
| Persistence/migrations | Backend CI has SQLite + PostgreSQL 16 upgrade/downgrade/re-upgrade and synthetic restore drill | CI coverage present; production Oracle restore is not evidenced | Keep production backup/restore as post-deployment gate |
| Frontend | Next.js app routes exist for admin, backtests, login, news, portfolios, reconciliation, register and settings; CI workflow typechecks/builds | Present; UI acceptance not part of P4-0 | Keep major UI build changes for planned UI phase unless hardening requires them |
| CI trigger coverage | Backend workflow triggers on push to main, pull_request, workflow_dispatch; frontend workflow triggers on main/path changes, pull_request/path changes, workflow_dispatch | Push to the Phase 4 branch alone does not trigger backend workflow; frontend workflow is path-filtered | Use an authorized PR/workflow dispatch to obtain exact-head checks; never call empty status “passed” |

## Prioritized Phase 4 actions
1. **P4-0A (safety first):** implement fail-closed startup validation so any `TRADING_MODE` value other than `PAPER` prevents the app/worker from starting trading services; test PAPER, LIVE, invalid and case-normalized values. This must not create a live mode or order-write path.
2. **P4-0B:** review all references to adapter `place_order`, `modify_order`, `cancel_order`, dynamic dispatch and order routes. Ensure tests demonstrate no application execution path can submit live writes.
3. **P4-0C:** inspect automated-entry kill switch, strategy exit behavior, stale market-data checks and service-boundary risk checks.
4. **P4-0D:** paper order/fill/P&L/charge lifecycle and persistence failure/restart/replay tests.
5. **P4-0E:** Upstox token expiry/streamer lifecycle and deployment checklist.
6. **P4-0F:** full CI on exact head, update all Phase 4 resume/checkpoint records and continue at the first unchecked item.

## CI status
- The Phase 3 baseline run cited in prior checkpoint records is not CI evidence for the new Phase 4 documentation head.
- At the time of this audit, commit `39952e8d091a6ed55d7eff2cb9a48f60c4e1288d` returned no combined status entries; that is **not a pass**.
- The repository's backend workflow is configured for pull requests and workflow_dispatch, not arbitrary branch pushes. No Phase 4 green run is claimed here.

## Safeguards confirmed for this work
- Only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is out of scope.
- No `main` update and no merge of PR #6/#7.
- PAPER mode remains mandatory; live `place_order`, `modify_order`, `cancel_order` writes remain disabled.
- Brokerage Details estimates remain estimates; aggregate Trade Charges responses remain reconciliation-only.
- No live broker write, credentialed smoke test, production deployment or real Oracle restore was performed.
