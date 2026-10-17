# Tradepro Improved — Progress Tracker

Last updated: 2026-10-17
Repository: https://github.com/tarunsharma2610-del/tradepro-improved
Branch: `main`
Starting HEAD before this documentation step: `2cf83089070e064c61f3b75fcb6b663021cbf625`
- `PROJECT_INSTRUCTIONS.md` commit: `8d7d9d8257f852f3d26e0564be8b521b0fe75764`
- `PROGRESS.md` initial commit: `9986380d8f4ee8939718c858ea9ab925da3f65b1`

## Current state
- [x] Separate improved repository exists; original `Tradepro` repo is to remain untouched.
- [x] Existing project structure, README, audit report, live-trading safeguards, Upstox adapter and execution service inspected in this session.
- [x] Persistent project instructions and progress tracking are being added.
- [x] Existing audit reports 167 backend tests passing in a prior GitHub Actions run and frontend typecheck/build passing. These are reported historical CI results, not tests rerun in this session.
- [x] Existing paper MARKET and LIMIT paths are described as implemented; paper LIMIT matching/cancel tests are reported as passing in prior CI.
- [ ] Live trading is NOT ready: execution service currently constructs PAPER orders; live placement and broker reconciliation are incomplete. Do not enable.
- [x] Multi-segment instrument sync, snapshot-gated expiry/delisting reconciliation, and user-scoped Upstox V3 WebSocket client/routes implemented. Live instrument-master sync to disposable SQLite verified; live authenticated WebSocket session still needs account-level verification.
- [x] Manual per-portfolio risk settings and enforcement implemented for daily realized loss, estimated exposure, per-order value, open/pending positions, and daily order count. Latest test run is being checked.
- [ ] OAuth schema migration needs staging verification before deployment.

## Current phase
**Phase G in progress — manual portfolio controls, snapshot reconciliation, WebSocket streaming and live BOD verification implemented; final CI verification and docs are in progress.**
- Added `PROJECT_INSTRUCTIONS.md` with the mandatory workflow and safety rules (commit `8d7d9d8257f852f3d26e0564be8b521b0fe75764`).
- Added this `PROGRESS.md` tracker (commit `9986380d8f4ee8939718c858ea9ab925da3f65b1`).
- Inspected `backend/app/services/execution_service.py`, `backend/app/services/strategy_execution_service.py`, `backend/app/services/risk_engine.py`, `backend/app/core/config.py`, `backend/app/models/order.py`, `backend/app/brokers/upstox/adapter.py`, and relevant execution tests.
- Confirmed the execution service currently creates orders with `trading_mode="PAPER"`; live broker order placement is not wired into this service. This is a deliberate safety boundary, not something to bypass.
- Confirmed the risk engine currently covers strategy-specific realized daily loss only; portfolio-wide loss/exposure/order-frequency caps are not present in the inspected module.
- Confirmed the Upstox adapter explicitly returns incomplete/not-implemented results for instrument-master sync and WebSocket streaming.
- Added a requirements-to-code/test gap map to `AUDIT_REPORT.md` (commit `ed0d18a0f03a45274ced3a4f237fbcca74f8ac2e`). It maps paper/live isolation, idempotency, risk limits, kill-switch scope, instrument sync, streaming, and migration verification.
- Corrected `README.md` so it no longer incorrectly lists the existing automated-entry kill switch as wholly unimplemented; it now distinguishes that switch from a global live-account kill switch (commit `611d5edbf476bc56682bb8af86ff8c216a38097e`).
- Confirmed the backend CI workflow run for the preceding documentation commit succeeded: [run 39036087413](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39036087413). This is documentation-change CI, not new application-code test coverage.
- Added `test_paper_market_order_never_calls_broker_live_order_endpoint` in `backend/tests/test_execution_service.py` (commit `07afe398ec85dffd00969355bb9362e9848f81ad`). It asserts the simulated order is `PAPER`, fills as expected using a mocked quote, and never awaits the broker's real `place_order` method.
- GitHub Actions backend workflow passed for that test commit, including the full pytest suite and SQLite Alembic migration verification: [run 39036217193](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39036217193). The Actions job is green; no live broker orders were submitted.
- Audit documentation commits: `ed0d18a0f03a45274ced3a4f237fbcca74f8ac2e` and `8940872208ca851f8ee27b4087aaa0e1445a8ae6`; README clarification commits: `611d5edbf476bc56682bb8af86ff8c216a38097e` and `ca35809b97f3eb970a94b61f4395b7036f2aa0ae`.
- Verified official Upstox documentation confirms the BOD instrument master is available as gzip-compressed JSON and recommends `instrument_key`; the current `InstrumentService` already syncs NSE_EQ only, while the adapter-level method remains a stub. See https://upstox.com/developer/api-documentation/instruments/.
- Updated the stale `InstrumentService` module docstring to reflect the actual scope (commit `3d28863309a224977764593688eb32a6161f13ff`).
- Refined `AUDIT_REPORT.md` after tests passed, recording the CI run and clarifying the existing sync is partial rather than wholly missing (commit `b9b8976482ac8b80cb3c39c8e448688b0c898769`).
- Added `backend/tests/test_instrument_service.py` with mocked successful gzip/JSON sync (NSE_EQ imported, NSE_FO ignored) and HTTP-failure/no-write coverage (commit `9f0e15ff274ce0b8aa3faa74aaa2427c2da750b0`). Backend CI passed including the full pytest suite and SQLite migration verification: [run 39036316771](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39036316771).

## Prior audit / CI evidence
See `AUDIT_REPORT.md` and `LIVE_TRADING_SAFEGUARDS.md`. Audit report links to a prior backend CI run (167 passed, 1 deprecation warning) and reports frontend typecheck/build success. Treat these as prior reported results unless verified again through current Actions.

## Rules for updating this file
After each coherent step, update this tracker with:
1. What changed and why.
2. Exact files changed.
3. Test commands/workflows actually executed and results.
4. Commit SHA and CI status when confirmed.
5. Any failures or unverified assumptions.
6. The next single action.

## Workstream continuation — 2026-10-17

### 1. Expiry and delisting management
- instrument_service.py derives snapshot keys from the official BOD master, checks for at least 1,000 valid normalized instruments (or at least 90% of the current active supported catalog, whichever is greater), and requires all major NSE/BSE/MCX segments before reconciliation.
- Unknown upstream instrument types still count as present keys, preventing false delisting when Upstox adds a new type. Missing keys and expired futures/options are reconciled in the same transaction as batch upsert only after the completeness gate passes. Failed or incomplete snapshots leave the existing catalog unchanged.
- instrument_repository.py reconciles snapshot absence and expiry atomically with the upsert.
- Added regression tests for deactivation of missing/expired contracts and protection against incomplete snapshots.

### 2. Upstox WebSocket market data
- Added official Upstox V3 protobuf schema and generated decoder under backend/app/brokers/upstox/proto/, plus the streamer and per-user manager services.
- Added authenticated endpoints: POST /api/v1/market-data/stream, GET /api/v1/market-data/stream, and DELETE /api/v1/market-data/stream. Start requires a connected Upstox OAuth session and active catalog keys. Portfolio UI now has Start/Stop controls and polls for fresh selected-instrument LTP.
- The client obtains a fresh one-time authorized WebSocket URL per reconnect, validates the Upstox host, keeps TLS verification enabled, sends the V3 binary subscription message, decodes protobuf frames, uses library ping/pong, reconnects with exponential backoff, and rejects stale exchange/receive timestamps.
- ExecutionService prefers a fresh subscribed WebSocket quote and falls back to authenticated REST LTP if the stream has no fresh quote. A stale stream tick is never used for a fill.
- Added mocked tests for protobuf decoding, stale data, stream configuration, fresh-stream preference and REST fallback. A real authenticated WebSocket connection has not been tested because no user's live OAuth token/session is available. Streams are in-process and ephemeral; multi-worker deployment needs shared stream state/cache.

### 3. Real instrument-master operational verification
- Added backend/scripts/verify_upstox_instrument_master.py and .github/workflows/upstox-live-verification.yml. The workflow downloads the real official Upstox BOD gzip JSON and syncs it into a disposable in-memory SQLite database; it never connects to the configured application database.
- Live verification succeeded in workflow run 39037390129: 123,930 active instruments imported and segment coverage validated. Counts: BCD_FO 10,422; BSE_EQ 13,096; BSE_FO 5,180; BSE_INDEX 79; MCX_FO 15,601; NCD_FO 8,644; NSE_COM 22,585; NSE_EQ 9,832; NSE_FO 38,352; NSE_INDEX 139. This is a real upstream download plus temporary-database sync, not a production sync.
- Verification link: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037390129

### 4. Manual portfolio management and risk controls
- Added six portfolio columns through migration 202610170001_portfolio_risk_controls.py: enable flag, max daily realized loss, max estimated open exposure, max order value, max open/pending positions and max orders per day. Limits remain disabled by default for existing portfolios.
- Added PortfolioRiskSettings validation, owner-scoped PATCH /api/v1/portfolios/{portfolio_id}/risk-settings and a portfolio UI form for manual rename/configuration. Starting capital/cash ledger is deliberately not editable after trading begins, to avoid rewriting historical accounting.
- Added portfolio_risk_service.py and wired checks into market-order submission, limit-order submission and limit fills. Pending limit-order exposure is included; reducing orders that close an existing position are allowed through risk caps so users are not trapped in positions. Exposure is estimated from position cost and pending limit notional, not exchange margin or live liquidation exposure.
- Added schema and order-risk regression tests. The migration passed clean SQLite Alembic verification in CI.

### Files changed in this workstream
- Backend: portfolio model/schema/API, portfolio risk service, execution service, instrument service/repository, WebSocket streamer/manager/API/schema, Upstox protobuf schema/decoder, main lifecycle, migration, verification script and requirements.
- Frontend: API client PATCH support and portfolio settings UI.
- Tests: instrument snapshot reconciliation, portfolio risk schema/order limits, WebSocket protobuf/stale handling and stream quote selection.
- Docs/workflows: README, audit report, project instructions, progress tracker and live master verification workflow.

### Current limitations / safety boundaries
- No production application database was written and no production migration was run.
- No real order was submitted. Live order placement/reconciliation is still unimplemented; TRADING_MODE=LIVE must not be enabled.
- The WebSocket code has mocked transport/decoder tests, but no live authenticated stream test; the manager is process-local and ephemeral.
- Exposure uses cost-basis estimates, not broker margin, greeks-based risk, or mark-to-market P&L. Daily loss cap is based on realized P&L only.
- OAuth schema migration needs backup-safe staging verification before deployment.

## Next action
Backend CI passed for code commit dc0faae66d730ddc3494f1bc453aa75c8ba85532: 194 tests passed, 1 warning, and SQLite Alembic migration verification passed. Daily risk limits use the Asia/Kolkata market-session day, with a regression test at the midnight boundary. Workflow: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037826596. Frontend TypeScript and production build passed for stream-control UI commit 6ec32fefda4ba357bde0fc5997cd32d6b58b4979: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037642093. The live instrument-master workflow passed with 123,930 active instruments in temporary SQLite: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037390129. Frontend TypeScript and production build passed for the stream-control UI commit 6ec32fefda4ba357bde0fc5997cd32d6b58b4979: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037642093. The live instrument-master workflow passed with 123,930 active instruments in temporary SQLite: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037390129. Keep live trading disabled.
