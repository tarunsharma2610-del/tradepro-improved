## Current verified checkpoint — 21 October 2026

- **Verified code/test checkpoint:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, the broker-write boundary guard, and SQLite/PostgreSQL 16 reversible migration checks.
- **Previously verified documentation checkpoint:** `a2e639f61e2c50070deb26d1a9a0741545c9737d`; exact-head backend CI [run 39568011689](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39568011689) passed. This is historical evidence for that SHA; every new commit still requires its own exact-head CI.
- The slow-persistence/lease-race audit is complete: the PostgreSQL row-lock test proves reclaim waits while a fenced write transaction is open; `test_postgres_high_volume_expiry_races_never_resurrect_stale_lease` passed 20 concurrent expiry-boundary renewal/reclaim races. Expired owners cannot renew, and ownership generation/token advance is verified.
- Official Upstox V2 [order-book](https://upstox.com/developer/api-documentation/get-order-book/) and [get-trades-for-day](https://upstox.com/developer/api-documentation/get-trade-history/) endpoints are current-day endpoints without documented pagination parameters. Historical trades use a separate [paginated API](https://upstox.com/developer/api-documentation/get-historical-trades/); it is not wired into the Phase 2 worker.
- Phase 2 technical audit and scope reconciliation are complete. Keep Phase 3 blocked until this final documentation commit's exact-head CI passes. Do not enable live broker submission, automatic accounting promotion or automatic scheduling. The original `Tradepro` repository remains untouched.

------

## Current verified checkpoint — 21 October 2026

- **Latest verified code/test HEAD:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, the broker-write boundary guard, and SQLite/PostgreSQL 16 reversible migration checks.
- The lease-race audit now has both pieces of evidence: PostgreSQL test `test_postgres_write_fence_blocks_reclaim_until_persistence_transaction_finishes` proves reclaim waits while a fenced transaction holds the lease-row lock; new `test_postgres_high_volume_expiry_races_never_resurrect_stale_lease` runs 20 concurrent expiry-boundary renewal-versus-reclaim races and asserts expired owners cannot renew and generation/token ownership advances safely.
- CI logs confirm the full backend suite and source guard passed; the successful workflow includes SQLite and PostgreSQL 16 upgrade/downgrade/re-upgrade checks. The one Python warning is the existing Starlette/AnyIO deprecation.
- **Current task:** synchronize all authoritative documents with this result. The resulting documentation HEAD still needs exact-head CI and a final stale-status scan before Phase 2 is formally closed. Do not start Phase 3 before then.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. The original `Tradepro` repository remains untouched.

------

<!-- Authoritative checkpoint audit: 2026-10-21; updated after Phase 2 lease-fencing verification. -->
## Authoritative checkpoint audit — 21 October 2026

- **Repository/branch:** `tarunsharma2610-del/tradepro-improved`, `main`. The original `tarunsharma2610-del/Tradepro` repository is a protected baseline and must remain untouched.
- **Latest code/test commit:** `e56bf4c66f74b875a3ba8fe388138a9d688dd1e2` adds failed-commit rollback coverage. Exact-head backend CI [run 39564568154](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39564568154) passed 471 tests, 1 warning, source guard and SQLite/PostgreSQL 16 reversible migrations. Documentation HEAD `adb69aeb05b70ba4fa9095fc73d9dea033d31eec` passed [run 39565251793](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39565251793).
- **Exact-commit backend CI:** [run 39561621808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561621808) passed **470 tests, 1 warning**, the broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles. It includes lease-fence ownership/expiry tests, a high-volume batch-stop regression, and a PostgreSQL contention test proving an expired lease cannot be reclaimed while a fenced persistence transaction still holds the row lock.
- **Documentation checkpoint CI:** [run 39561881539](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561881539) passed on documentation commit `292cad087bf0febad7793dcec164ebb5435726e8`; this follow-up synchronizes the closure wording and design note.
- **Frontend:** no frontend files changed in this Phase 2 patch. The latest verified frontend CI remains [run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474), which passed TypeScript and Next.js build on code/test commit `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`.
- **Previously completed Phase 2 protections:** atomic run/lease finalization; stale-owner protection; cancellation and interrupted-run recovery; inconsistent token/expiry rejection; five-record renewal checks; and incomplete-summary warnings for `WORKER_INTERRUPTED` and `LEASE_LOST`.
- **Newly completed lease-expiry audit:** every worker-owned reconciliation persistence operation (fill identity, review issue, order transition and fill-to-intent link) now obtains a current, unexpired lease fence immediately before the write. The lease row is locked through the repository's persistence transaction, so a competing claimant must wait until that transaction commits or rolls back. Lease loss fails closed before the next mutation.
- **Scope clarification:** Phase 2's defined engineering checks are verified; remaining live-account safety, central broker-write/preflight and live-accounting coordinator work is explicitly classified as Phase 3/Phase 4 in the dependency matrix. Keep Phase 3 blocked until the final documentation sync passes exact-head CI.
- **Scope remains unchanged:** external-repository borrowing/adaptation is paused; no outside application code was imported. Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`; do not wholesale-merge the divergent safety branch.
- Intermediate CI runs on partially applied commits were red while the new regression test preceded its matching fix; the final code/test commit above is the authoritative green result. Do not count those intermediate failures as the current code status.

## Current scope and backlog clarification — 21 October 2026

- The **reconciliation crash-recovery/lease-fencing slice** is complete. Code/test commit `fe07b77b193da1232787384efb38cb589e0d71b6` passed backend CI run [39561621808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39561621808): 470 tests, 1 warning, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles.
- The documentation synchronization commit is CI-checked separately; use the live [GitHub Actions page](https://github.com/tarunsharma2610-del/tradepro-improved/actions) to verify the exact current `main` HEAD. Do not infer exact-HEAD CI from an earlier commit.
- **This does not mean the entire Phase 2/Phase 2 roadmap is backlog-free.** Phase 2 still has open work: complete the safety-branch dependency matrix, resolve the `BrokerFillIdentity` versus manual `BrokerTradeRecord` workflow boundary before any bridge, and complete the remaining focused accounting/idempotency/rollback tests for any selected port slice.
- Phase 3 live-fill accounting integration and Phase 4 live-trading release gates remain future work and are intentionally blocked. No live submission, automatic accounting promotion, or automatic scheduling is enabled.
- External-repository borrowing remains paused; the original `Tradepro` repository remains untouched. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`; do not wholesale-merge the divergent safety branch.

<!-- Latest verified status, updated 2026-10-21 -->
> **Latest verified checkpoint — 21 October 2026**
>
> - Repository: `tarunsharma2610-del/tradepro-improved`; branch: `main`. Original `Tradepro` repository remains protected and untouched.
> - Latest code/test commit: `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`. Backend [CI run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration checks. Frontend [CI run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript and Next.js build.
> - Documentation audit commit `6407c5a05865c1be0ef673d3bb5e71c0231ef8da` passed [CI run 39556816828](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556816828).
> - Phase 2 checkpoint complete through atomic run/lease finalization, stale-run and cancellation recovery, lease-loss fencing, five-record renewal, and incomplete-summary warnings.
> - **Completed engineering task:** audited single slow-write and high-volume lease-expiry races; transaction-level fencing and regression coverage passed backend CI run 39561621808 (470 passed, 1 warning).
> - Deferred safety-branch work remains tracked in `SAFETY_BRANCH_PORT_MATRIX.md`; no wholesale branch merge. Keep live broker submission and automatic accounting promotion disabled. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`.
>
> The CI status above refers to the stated code and documentation commits. This documentation refresh will create a new commit and trigger its own CI run; do not call that new run passed until GitHub reports success.

## Latest continuation — accounting commit-failure rollback test (2026-10-21)

- **Commit:** [e56bf4c66f74b875a3ba8fe388138a9d688dd1e2](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e56bf4c66f74b875a3ba8fe388138a9d688dd1e2).
- Added test_failed_commit_rolls_back_execution_and_live_position in backend/tests/test_live_fill_accounting_service.py. The regression injects a commit failure and checks no live execution/position survives rollback and the paper position is unchanged.
- **Superseded historical checkpoint:** code/test CI [39564568154](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39564568154) passed 471 tests, 1 warning, source guard and SQLite/PostgreSQL 16 migration checks; documentation HEAD `0bd502f83118799d5564e8fd5724d01e8dc975af` passed [39566324985](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39566324985). Current status is recorded at the top of this file.
- Phase 2 workflow boundary remains explicit: BrokerFillIdentity and manual BrokerTradeRecord stay separate. Safety-branch dependency decisions are recorded in SAFETY_BRANCH_PORT_MATRIX.md; Phase 3/Phase 4-only live-safety features are deferred, not wholesale-merged.
- **Historical status note — superseded:** the latest code/test checkpoint and its CI are recorded at the top of this file. The current documentation synchronization must pass its own exact-head CI before Phase 2 is formally closed.

# Tradepro Improved — Progress Tracker

Last updated: 2026-10-21
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

## Latest continuation step — portfolio position-cap regression test
- Inspected the current `PROJECT_INSTRUCTIONS.md`, `PROGRESS.md`, `README.md`, `AUDIT_REPORT.md`, current `main` tree and recent GitHub Actions before editing.
- Added `test_portfolio_open_position_cap_rejects_new_instrument` in `backend/tests/test_execution_service.py`. It proves a manually configured max-open-position cap rejects a new instrument when an existing position already occupies the cap; no real broker order is submitted.
- Commit: `3a518d8f7605ab066297b37dc18f4df4d225259c`.
- Backend CI passed: **195 tests passed, 1 warning**; SQLite Alembic migration verification passed. Workflow: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039143042.

## Latest continuation step — exact-instrument quote safety
- Audited `_extract_ltp` in `backend/app/services/execution_service.py`. The old fallback scanned unrelated response entries when the requested key was absent, risking use of a different instrument's LTP.
- Removed the arbitrary-entry fallback; quote parsing now returns no price unless the exact requested `instrument_key` has a valid positive finite `last_price`.
- Added `test_quote_parser_uses_only_the_requested_instrument_key` in `backend/tests/test_execution_service.py`, covering both exact-key acceptance and wrong-key rejection.
- Code commit: `8bddac0ae09e43d91b3da990dc7a014f6721c325`; regression-test commit: `7403739c5a1f97aaed84e145958f9aa05f2f3f61`.
- CI passed: **196 tests passed, 1 warning**; SQLite Alembic migration verification passed. Workflow: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039234333.

## Latest continuation step — daily order-count risk cap
- Added `test_portfolio_daily_order_cap_rejects_additional_order` in `backend/tests/test_execution_service.py`. It verifies cancelled orders do not consume the daily allowance, the first active order is accepted, and the next order is rejected at the configured cap.
- Commit: `167d67fdb953f0b75991e3e809062c845733b877`.
- Backend CI passed: **197 tests passed, 1 warning**; SQLite Alembic migration verification passed. Workflow: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039335585.
- The exact-instrument quote safety change and max-open-position cap test are also recorded above; live trading remains disabled.

## Latest continuation step — WebSocket silence/reconnect regression
- Added `test_stream_reconnects_after_silence_timeout` to `backend/tests/test_upstox_market_data_streamer.py`, using a mocked socket and token provider. It verifies that a silent feed causes the client to reconnect and that the stream is marked disconnected after stopping.
- Commit: `ff417ec7ea3ed326c93d7c11703da07a18e2eb05`.
- Backend CI passed: **198 tests passed, 1 warning**; SQLite Alembic migration verification passed. Workflow: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039414286.
- Live OAuth streaming still requires the user's authenticated session; no live account or order was used.

## Latest continuation step — WebSocket authorization URL validation
- Added parameterized tests in `backend/tests/test_upstox_market_data_streamer.py` proving authorization URLs are rejected when they use plain HTTP, an unrelated host, or a deceptive `upstox.com.evil.example` hostname.
- Commit: `c67c13ca30c4c2add6acab58633503f157b72420`.
- Backend CI passed: **201 tests passed, 1 warning**; SQLite Alembic migration verification passed. Workflow: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039490249.
- Previous tested stream step: silence timeout triggers reconnect, while stream status returns disconnected after stop (commit `ff417ec7ea3ed326c93d7c11703da07a18e2eb05`, 198-test CI run).

## Latest continuation step — snapshot completeness regression
- Added `test_incomplete_snapshot_never_deactivates_existing_catalog` in `backend/tests/test_instrument_service.py`. A syntactically valid but incomplete master omitting required segments must fail before upsert/reconciliation, leaving the existing active catalog unchanged.
- Commit: `50bcca84080b771e65d8c727965d00745455ad6f`.
- Backend CI passed: **202 tests passed, 1 warning**; SQLite Alembic migration verification passed. Workflow: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039577808.
- Cross-checked the stream auth/subscription implementation against official Upstox V3 docs: current auth endpoint is the V3 market-data authorize route; it returns a one-time `authorized_redirect_uri`; subscription is a binary V3 message; LTPC supports up to 5,000 keys on a single-category connection; and ping/pong heartbeats are expected. The current implementation uses `Accept: application/json`, binary subscription frames, and the official protobuf format. References: https://upstox.com/developer/api-documentation/get-market-data-feed-authorize-v3/ and https://upstox.com/developer/api-documentation/v3/get-market-data-feed/.

## Latest continuation step — official-format V3 authorization success path
- Added `test_authorization_accepts_official_upstox_v3_url_and_headers` to `backend/tests/test_upstox_market_data_streamer.py`. It checks that a valid `wss://xyz.upstox.com/...` URL is accepted and the official V3 authorize endpoint receives `Authorization: Bearer ...` and `Accept: application/json`.
- Commit: `da65b64aed2e733761db5c1659f6cb4c8ea93ac6`.
- Backend CI passed: **203 tests passed, 1 warning**; SQLite Alembic migration verification passed. Workflow: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039645511.
- Official docs checked: V3 auth endpoint/one-time URL, binary subscription payload, LTPC subscription limit, protobuf feed, and ping/pong heartbeat. No discrepancy was found in the reviewed path. Real account streaming is still unverified.

## Next action
Review the live-order idempotency/reconciliation gap and write a safe implementation plan before any live-order code. Live order placement remains intentionally unimplemented; do not connect it to the paper execution service or submit real orders. Frontend TypeScript and production build passed for stream-control UI commit 6ec32fefda4ba357bde0fc5997cd32d6b58b4979: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037642093. The live instrument-master workflow passed with 123,930 active instruments in temporary SQLite: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037390129. Keep live trading disabled.


## Checkpoint — 2026-10-17 (verified against latest default-branch CI)
- Re-read `PROJECT_INSTRUCTIONS.md`, `PROGRESS.md`, `README.md` and `AUDIT_REPORT.md`. This checkpoint reconciles older audit text with the latest verified state.
- Latest CI after documentation changes: [39039714203](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039714203) — **203 passed, 1 warning**; clean SQLite Alembic migration chain reached `202610170001` (manually configurable portfolio risk controls).
- Regression coverage already on `main`: portfolio daily order cap, incomplete instrument-master snapshot rejection, WebSocket silence reconnect, authorization URL allow/deny checks, and official-format V3 authorization success path. Do not duplicate tests without inspecting current files.
- Upstream instrument-master verification previously passed in disposable in-memory SQLite: **123,930 active instruments**; workflow [39037390129](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037390129). This is not a production sync.
- Frontend TypeScript/build passed for stream-control UI: [39037642093](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037642093). Stream manager is process-local; deploy one API worker until shared state is implemented.
- Still unverified: real OAuth-authenticated WebSocket; backup-safe staging migration against the actual deployed DB; multi-worker stream sharing; and live order workflow. Live order placement remains unimplemented and disabled.
- README refreshed in commit `92d328f5f16ac1df114f06249dc645165524fc11`; audit refreshed in commit `128bbf4265012acbde32e06b69af118ebdafed6f`. The latest documentation commit's CI run [39040259560](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39040259560) was still in progress at checkpoint time; do not claim it passed until completed.
- **Next step:** inspect broker adapter, order model, audit trail and execution service; write a design for idempotency keys, uncertain-submit handling and broker reconciliation before coding. Preserve paper/live isolation; do not submit live orders.


## Latest continuation — durable live-order idempotency/reconciliation design (2026-10-17)
- Re-read `PROJECT_INSTRUCTIONS.md`, `PROGRESS.md`, `README.md`, `AUDIT_REPORT.md`, `ARCHITECTURE.md`, `LIVE_TRADING_SAFEGUARDS.md`, order/execution models, order repository, execution service, broker interface, Upstox adapter and execution tests.
- Confirmed current boundary: `ExecutionService.place_order()` still constructs PAPER orders; no complete live orchestration, durable idempotency key, submit-attempt ledger, broker-fill dedupe identity or reconciliation workflow exists. The adapter methods alone do not make live trading safe.
- Created `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` as a design-only plan (commit `f74386a99722d761bcd23848f442cb754dd0e231`). It specifies additive intent/event/outbox/fill identity records, key+payload-hash semantics, uncertain-submit behavior, no blind retries, broker reconciliation, partial-fill dedupe, cancellation races, risk recheck, kill switch, migration gates, implementation phases and a regression-test matrix.
- Reviewed official Upstox documentation for Place Order V2/V3, Order History, Order Book, Order Details and Order Trades. A broker `tag` is treated as correlation/search, NOT as guaranteed broker-enforced idempotency. Sources are linked in the design file.
- No application code changed, no migration ran, no live broker session was used, and no orders were submitted. Tests were not rerun because this step only adds design documentation.
- Current phase: design review; implementation is deliberately not started.
- Next action: cross-link the reviewed design and correct status/roadmap language in `ARCHITECTURE.md`, `LIVE_TRADING_SAFEGUARDS.md`, `README.md`, `AUDIT_REPORT.md` and this progress tracker. Keep live submission disabled.


### Cross-document update — 2026-10-17
- Added the design-only document and cross-linked the safety boundary across architecture, safeguards, README, audit and persistent instructions.
- Commits:
  - Design: `f74386a99722d761bcd23848f442cb754dd0e231`
  - Progress checkpoint: `23038aec23be3ea84f5f7b311b58b07a7a20e79e`
  - Architecture: `dca8482b9f3959ed4708955aed25b1129e6d8673`
  - Live safeguards: `0543eb7fce6aa874bd565764ed89768c0b1c5146`
  - README: `230ff457e61136b249edaed435c9b3b9ef11a320`
  - Audit: `412f02f1864896bca8eba6239083e20aebefefcb`
  - Persistent instructions: `9b6133132d11aec17fa63d409ee476aceaaeb34c`
- Documentation CI verified green for design [run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39040603270), progress [run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39040613801), architecture [run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39040622827), safeguards [run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39040633919) and README [run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39040640928). Audit run 39040650847 and instruction run 39040662516 were still in progress at the latest check; the newest progress commit CI is queued. Do not claim the entire series is green until those complete.
- This was documentation/design only; no application tests were rerun locally, no code/migration was added, and no broker order was submitted.
- Verified cross-links and design-only safety status in `ARCHITECTURE.md`, `LIVE_TRADING_SAFEGUARDS.md`, `README.md`, `AUDIT_REPORT.md` and `PROJECT_INSTRUCTIONS.md` against current default-branch contents.
- **Next action:** verify the remaining audit/instruction/progress CI runs, then pause at the design-review gate for user approval before Phase 1 schema/repository implementation.


## Repository completeness and roadmap checkpoint — 2026-10-17
- Rechecked the default `main` tree after the prior continuation. All seven live-order design/status documents exist: `PROJECT_INSTRUCTIONS.md`, `PROGRESS.md`, `README.md`, `AUDIT_REPORT.md`, `ARCHITECTURE.md`, `LIVE_TRADING_SAFEGUARDS.md`, `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`. No separate roadmap file existed, so added `ROADMAP.md` and linked it from README, architecture, audit and persistent instructions.
- Confirmed prior progress commit `3263eda9d1329d17069dd4140162602631639a0b` CI succeeded: [run 39040715054](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39040715054).
- New roadmap commit: `3024aed473f28409bd075ec7e764576890c4ecfa`.
- Cross-links/status commits: README `748a20b227c8f55d4c75276b36fa00c5f5075569`; instructions `25b4e39e6636ef527785dccdd7e627fe0a991447`; architecture `a6fd111534681e18392df6e9be6d1c09b9deb6f2`; audit `914d9d12f5872d3061770461b110dff1cf98cd29`.
- This is documentation/roadmap only. No live-order code, migration, or real broker order was executed. Each new commit's CI must be checked independently; do not use the previous green workflow as proof for later commits.
- Next: verify the newest branch tip and CI for every commit in this documentation series, ensure the final progress update itself is committed and green, and inspect final file links. Then pause for design approval before any schema/code implementation.

## Latest continuation — final documentation CI verified — 2026-10-17
- Re-read the persistent instructions, current progress tracker, README, audit, architecture, safeguards, live-order design and roadmap; checked the current `main` tree and relevant order/execution model and repository files.
- Confirmed `main` currently points to `5c288b7796083c6de8e210cd9e49a7e95daac72f` (`docs: record roadmap addition and repository completeness audit`).
- Verified GitHub Actions for that exact HEAD completed successfully: [workflow 39041041406](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39041041406). The preceding roadmap, README, instructions, architecture and audit documentation commits also have successful individual CI runs (39040992954, 39041003884, 39041013848, 39041020582, 39041026871). These are documentation CI runs, not new application-code tests.
- Cross-checked the design against current source: `Order` has no durable live-intent/idempotency/submit-attempt fields; `Execution` has no broker-fill identity uniqueness; `OrderRepository` commits ordinary create/save operations; the shared execution service remains PAPER-only. This supports the documented blocker rather than just assuming it.
- No source code or migration was changed, no local tests were run, no production/staging database was touched and no broker order was submitted.
- **Current gate remains Gate 0 — design review.** Per the persistent project instructions and roadmap, do not start Phase 1 schema/repository code until the user explicitly acknowledges/accepts the design review and that acknowledgement is recorded here. Live submission remains disabled.
- **Next action:** obtain explicit approval of `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` as the implementation design; then record that approval and begin Phase 1 with additive durable records and concurrency/transaction tests only (no broker POST).


## User design approval and Phase 1 start — 2026-10-17
- **Explicit approval recorded:** the user approved `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` for implementation and directed that changes be committed to this repository, with roadmap/audit and other required documents updated.
- Gate 0 design-acceptance requirement is satisfied. This approval authorizes Phase 1 durable records and repository safeguards only; it is **not** authorization to enable or submit real broker orders.
- Phase 1 scope: additive durable live-order intent, append-only event, transactional outbox and broker-fill identity records; uniqueness constraints; same-key/same-payload reuse and same-key/different-payload conflict; focused tests. Keep the existing PAPER execution path isolated and do not call broker order placement.
- Current verified base commit before implementation: `03dce02de8777fe02aa7cc8da485f118b9403a50`; its backend CI passed: [run 39041376889](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39041376889).
- Implementation status at start: no Phase 1 source changes or migration have been committed yet. Do not report completion until source, migration and tests are committed and the exact final commit's CI is checked.
- Next action: add the additive SQLAlchemy records and Alembic migration, register models, then implement repository idempotency transaction behavior and focused tests.


## Phase 1 implementation checkpoint — 2026-10-17 (latest status supersedes earlier gate notes)

### Approval and scope
- The user explicitly approved `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`; Gate 0 is complete. This is approval to implement durable records/repository safeguards, **not** approval to enable live order submission.
- Work is on `main` in `tradepro-improved` only. The original `Tradepro` repository remains untouched.

### Implemented and committed
- `backend/app/models/live_order_records.py`: durable `LiveOrderIntent`, `LiveOrderEvent`, `LiveOrderOutbox`, and `BrokerFillIdentity` models. Database constraints cover scoped client idempotency, broker order identity, one outbox row per intent, unique broker trade identity, nonnegative attempts and positive fill values.
- `backend/app/models/__init__.py`: registers the new models with SQLAlchemy metadata.
- `backend/alembic/versions/202610170002_live_order_durability.py`: additive migration after `202610170001`, with reversible table/index creation.
- `.github/workflows/backend-tests.yml`: CI now verifies a clean SQLite upgrade to head, downgrade to `202610170001`, and re-upgrade to head.
- `backend/app/repositories/live_order_repository.py`: validates authenticated-user ownership of both portfolio and broker connection; derives SHA-256 from deterministic canonical JSON plus user/portfolio/connection scope; same key + same payload reuses the existing intent; same key + different payload raises `IdempotencyConflict`; persists intent, initial audit event and outbox row in one transaction; handles a unique-key race by rollback and winner lookup.
- `backend/tests/test_live_order_repository.py`: covers transactionally created records, duplicate reuse, payload conflict, ownership isolation, invalid key/non-finite payload rejection, duplicate broker-fill identity, audit ownership, rollback atomicity and deterministic independent-session winner recovery. True simultaneous multi-transaction contention remains unverified.
- Updated `ROADMAP.md`, `AUDIT_REPORT.md`, `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`, `ARCHITECTURE.md`, `LIVE_TRADING_SAFEGUARDS.md`, `README.md` and `PROJECT_INSTRUCTIONS.md` to record approval, current implementation boundary and evidence.

### Verification
- Latest application-code/test commit: `c098d1c23bd4d422e6d86c56e43c2c65e22d8ab4`.
- Exact application-code/test commit GitHub Actions: [run 39043589541](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39043589541) — **212 tests passed, 1 warning**.
- CI workflow commit `01212a5c2cd5e8d5fa916cb7fdfe285ce5cc150c` passed [run 39043763339](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39043763339), including clean SQLite migration upgrade → downgrade to `202610170001` → re-upgrade. This is not a staging or production DB verification.
- The intermediate canonical-hash API/test mismatch caused two red runs (39043143640 and 39043156888); the fixture was corrected and the later exact code checkpoint passed. Failures are not concealed.
- Latest evidence-document commits: roadmap `3a0908abdb9654206f44dff81faec2e2e34dd0cb`; audit `55e0fa86449b7aa4cfccad2c96c8d97bb86cc148`; README `1e5c464217bc4f53be8df649a5354fc8ae8c209b`; design `6c49ce3fe1f34ee17a520f1c211090f1fc89b478`. Architecture `d8f8fb9be71edc7f29fed9d31579a63654a7aea4`, safeguards `c1bc5babe0e1ba700fbb048b213d37c7f2d01f39`, and instructions `a23e84155f3cdd8faea135cddb4906cf03a4723f` also reflect the Phase 1 boundary. These documentation commits and this progress update's exact-commit CI must be checked independently.
- No broker order POST, cancellation, live reconciliation, production migration or real-money test was performed.

### Remaining Phase 1 gates
- Add true simultaneous multi-transaction contention coverage against the deployment database engine; current independent-session test deterministically simulates the competing commit and exercises winner recovery.
- Verify migration downgrade/upgrade and constraints on a backup-restored staging copy of the actual deployment database engine.
- Review append-only audit enforcement and safe-details redaction policy before any API exposes these records.
- No live-order API, dispatcher worker or reconciliation service is part of this phase. Keep live trading disabled.

**Next action:** check CI for the documentation commits and this progress update; then continue with the concurrent unique-key test and staging-engine migration review.


## Continued Phase 1 — credential-field persistence guard — 2026-10-17

### Change
- Added _validate_safe_json() in backend/app/repositories/live_order_repository.py. It recursively rejects credential-like key names in order snapshots and audit event details (including nested access/refresh tokens, secrets, passwords, API keys, authorization headers and cookies) and rejects non-finite/non-JSON-compatible data before database persistence.
- Added tests in backend/tests/test_live_order_repository.py for nested access-token rejection in order snapshots, nested Authorization-header rejection in audit details, and rejection of non-object audit details.
- This is defense-in-depth key-name validation, not a guarantee that arbitrary secret values are detected. Callers must continue to redact secrets. No API route, broker call, order submission or reconciliation workflow was added.

### Verification
- Combined code/test checkpoint: 5508b272efe55997252e8d8a51fdd29761a1070b.
- Exact GitHub Actions run [39047300286](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39047300286) succeeded: **214 passed, 1 warning**. Clean SQLite migration upgrade → downgrade to 202610170001 → re-upgrade also succeeded in the same workflow.
- Commits: repository guard 46f85a345dfff6a673ee19d3760191a07eff2f5b; tests 5508b272efe55997252e8d8a51fdd29761a1070b.
- Evidence/docs updated: roadmap f245e5d0402f06c72889bdd308e284cf2d21e523; audit 2c781f27734b8642f1861f505242f108b3c2a6c7; README 518f2ac606c7b2513aa62a5d18daa175a40e701f; design e9218829e814db1ab9c09358705fc1f48ea549b8; architecture e5889f7ab3765eac1cbf937f85aa0f28d24919a2; safeguards 0f36d6a095bd4b5c02253b9e68dab46b948feeb2. Each documentation commit's own CI still needs exact-commit verification.
- No production migration or real broker action occurred.

### Next single action
- Verify the documentation commits' CI, then add a concurrency test appropriate to the actual deployment database engine. The engine and staging access must be confirmed before claiming true simultaneous contention or production-engine migration verification.


## PostgreSQL contention integration — implementation committed, verification pending — 2026-10-17

- Added backend/tests/test_live_order_postgres_concurrency.py. When TEST_POSTGRES_URL is set, it creates an isolated test schema, synchronizes two independent PostgreSQL sessions after both miss the idempotency lookup, then asserts both requests return one intent ID and only one intent/outbox/event exists.
- Updated .github/workflows/backend-tests.yml to provision PostgreSQL 16, run the concurrency test, and test Alembic upgrade → downgrade to 202610170001 → re-upgrade on PostgreSQL as well as SQLite.
- Commits: integration test 84b12804538a931980d29b6847e655e2bebc59b1; CI configuration e79d6f3bc758bd0e868d4be795eeef865e7c8ee9.
- The test-only commit passed the SQLite-only workflow, but the PostgreSQL-enabled workflow [39047545900](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39047545900) is still in progress at container initialization. PostgreSQL concurrency and PostgreSQL migration results are **not yet verified**. Do not mark the gate complete until the exact workflow reports success.
- No production database or broker was contacted; this PostgreSQL service is disposable CI infrastructure only.

### Next action
Check workflow 39047545900. If the PostgreSQL service starts, resolve any concurrency-test or migration failures, then update this tracker with the exact successful run. If service initialization times out, inspect and adjust the CI service configuration before proceeding.


## PostgreSQL integration failure analysis and correction — 2026-10-17

- The first PostgreSQL-enabled CI run [39047545900](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39047545900) failed in the concurrency test setup: the test inserted the broker connection in the same flush as its user without an ORM relationship ordering guarantee, triggering a foreign-key violation.
- Corrected the test setup to commit the parent user first, then insert the portfolio and broker connection. Fix commit: dd36b48a92057ad50618f6f9941f908832c9cea3.
- Verification rerun: [39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046). Status must be checked before marking this resolved; PostgreSQL test and migration verification remain pending until that exact run succeeds.


## PostgreSQL concurrency + reversible migration verification — passed — 2026-10-17

- Exact code/test commit: `dd36b48a92057ad50618f6f9941f908832c9cea3`.
- Exact GitHub Actions run [39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046) succeeded: **215 passed, 1 warning**.
- The test starts two independent PostgreSQL sessions and synchronizes them after both initially miss the same idempotency key; it verifies both requests return the same intent ID and that exactly one intent, outbox row and initial audit event exist.
- In the same successful run, Alembic upgrade → downgrade to `202610170001` → re-upgrade passed on both clean SQLite and PostgreSQL 16.
- The first PostgreSQL run failed because the test setup inserted child rows without first committing the parent user. This was corrected in `dd36b48a92057ad50618f6f9941f908832c9cea3`; the rerun is green. The failed run remains visible in Actions history.
- CI configuration commit: `e79d6f3bc758bd0e868d4be795eeef865e7c8ee9`; concurrency test commit: `84b12804538a931980d29b6847e655e2bebc59b1`; test setup fix: `dd36b48a92057ad50618f6f9941f908832c9cea3`.
- Updated design, roadmap, audit, architecture, README and project instructions to match the verified state. Documentation commits: roadmap `9d661313adcb9bb75e558a257ab4569979e14652`; audit `63baafc4822e032e65ea871fea0b0c52fb3a8998`; design `849e4a4fcf18bf255b402cc00b156158188049db`; architecture `0285b2bd8890bf26feba690b3159702077d5c18c`; README `889312894a57cb1b9eb2705e5e8317be1059cad4`; instructions `a347a1e68b5db844df7f83d8677f79c03ff37844`.
- No real broker order was submitted and no production database was migrated.

### Current gate and next action
- Automated Phase 1 concurrency and reversible migration checks are complete for SQLite and PostgreSQL 16.
- Phase 1 remains open until schema/constraints are verified on a backup-restored staging copy of the actual deployment database engine, and broader crash/rollback/contention checks are reviewed.
- Next: verify CI for each documentation commit; then confirm the deployment database engine and safe staging access before claiming staging verification. Do not start broker submission. Phase 2 is reconciliation-only and must remain unable to submit orders.


## Documentation CI verification — all current Phase 1 updates green — 2026-10-17

Each updated Markdown file's exact commit has its own successful GitHub Actions run:
- ROADMAP.md commit `9d661313adcb9bb75e558a257ab4569979e14652`: [run 39048272612](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048272612) — success.
- AUDIT_REPORT.md commit `63baafc4822e032e65ea871fea0b0c52fb3a8998`: [run 39048279286](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048279286) — success.
- LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md commit `849e4a4fcf18bf255b402cc00b156158188049db`: [run 39048287427](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048287427) — success.
- ARCHITECTURE.md commit `0285b2bd8890bf26feba690b3159702077d5c18c`: [run 39048295538](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048295538) — success.
- README.md commit `889312894a57cb1b9eb2705e5e8317be1059cad4`: [run 39048303900](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048303900) — success.
- PROJECT_INSTRUCTIONS.md commit `a347a1e68b5db844df7f83d8677f79c03ff37844`: [run 39048311971](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048311971) — success.
- PROGRESS.md commit `a6deeafe078915955725953b2bc9f21d0f48e0bf`: [run 39048329434](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048329434) — success.
- LIVE_TRADING_SAFEGUARDS.md commit `437fb1446ecddfed72c6e9773d0d1f95258f7ba2`: [run 39048342181](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048342181) — success.

The latest verified application/test checkpoint remains `dd36b48a92057ad50618f6f9941f908832c9cea3` with [run 39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046): 215 passed, 1 warning, plus SQLite/PostgreSQL 16 reversible migration checks. This is separate from the documentation commits' own green CI runs.

Actual deployment database engine and access to a backup-restored staging copy are not established by repository CI. Phase 1 remains open until that environment is verified. No live broker submission, production migration or reconciliation worker was introduced.


## Phase 2 — conservative broker order normalization — 2026-10-17

- Added `backend/app/services/live_order_reconciliation.py`, a pure normalization module with no network, database, submit or cancel capability.
- Added `backend/tests/test_live_order_reconciliation.py` for documented Upstox order statuses, partial/full-fill consistency, unknown statuses, missing fields, invalid quantities/prices and the cancelled-order pending-quantity edge case.
- The normalizer preserves the broker's raw status, maps only known documented statuses, rejects malformed/inconsistent fields, and flags unknown or contradictory observations as `RECONCILIATION_REQUIRED` rather than guessing.
- Source contract references: [Upstox order book](https://upstox.com/developer/api-documentation/get-order-book/), [order details](https://upstox.com/developer/api-documentation/get-order-details/), [order history](https://upstox.com/developer/api-documentation/get-order-history/) and [order-status appendix](https://upstox.com/developer/api-documentation/appendix/order-status/). These APIs report current-day order records; durable local history and cross-session recovery remain future work.
- Exact test commit: `b37452210bf07ad03acee1495e0627fae1378582`; GitHub Actions [run 39049395091](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049395091) passed **247 tests, 1 warning**, including SQLite/PostgreSQL 16 reversible migration checks.
- Earlier implementation-only commit `c5f0f937367b9d74610d8ddef2885da6b309fa48` also passed existing CI: [run 39049387990](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049387990).
- This is a tested Phase 2 foundation, not a complete reconciliation worker. It does not fetch broker data, persist status transitions, link broker orders to intents, import fills, or place/cancel orders. Live trading remains disabled.
- Next step: add strict local-intent-to-broker-record matching and duplicate/ambiguous-match handling with tests; do not link an order based on tag alone or unknown/mismatched economics.


### Phase 2 documentation CI verification — 2026-10-17

All four documentation commits for the normalization foundation have their own successful CI runs:
- `PROGRESS.md` commit `75d72b7fbd3de3e6f352a3f68579ab82b152f250`: [run 39049553343](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049553343) — success.
- `ROADMAP.md` commit `edf44ae22ca540b2406ee332b508ef595b3bdd1e`: [run 39049563456](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049563456) — success.
- `AUDIT_REPORT.md` commit `4e922603a3157afd866de07d4ce4ce99d891e997`: [run 39049572086](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049572086) — success.
- `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` commit `7647296f2c4244027e1382633d5982ab009a9cc5`: [run 39049581913](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049581913) — success.

The latest application-code test checkpoint remains `b37452210bf07ad03acee1495e0627fae1378582`, verified by [run 39049395091](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049395091): 247 passed, 1 warning, plus SQLite/PostgreSQL 16 migration checks. The current work is only a normalization foundation; matching, durable status updates, fill ingestion and any broker I/O remain future work.


## Phase 2 — strict broker-order-to-intent matching — 2026-10-17

- Re-read PROJECT_INSTRUCTIONS.md, PROGRESS.md, README.md, AUDIT_REPORT.md, ROADMAP.md, ARCHITECTURE.md, LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md and LIVE_TRADING_SAFEGUARDS.md before continuing. Confirmed the repository target is tradepro-improved; original Tradepro remains untouched.
- Consulted current official Upstox order book, order details, order history and per-order trades docs. The order book/history are current-trading-day data, so a missing result is not proof an uncertain order was never accepted. References: [order book](https://upstox.com/developer/api-documentation/get-order-book/), [order details](https://upstox.com/developer/api-documentation/get-order-details/), [order history](https://upstox.com/developer/api-documentation/get-order-history/), [trades by order](https://upstox.com/developer/api-documentation/get-trades-by-order/).
- Updated backend/app/services/live_order_reconciliation.py: normalized broker price and trigger_price; added ReconciliationIntentCandidate, IntentMatchResult, and pure match_broker_order_to_intent(). Candidates are scoped to the requested broker connection. Match uses existing broker order ID when known, otherwise an exact non-empty tag that identifies one candidate, then requires economic-field equality. Duplicate candidates, cross-connection candidates, missing local economic fields, mismatches and unknown/contradictory observations are not auto-linked.
- Updated backend/tests/test_live_order_reconciliation.py with focused matching/ambiguity/isolation tests. Exact test commit: e9b594ffc2e81c37e1b41c8c44947212d206f3e9; [GitHub Actions run 39050424898](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050424898) passed 255 tests, 1 warning, and clean SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks.
- Implementation commit: f0f46e4ab364d2a304a1e8d2d4aafd7cd77b8ebd; test commit: e9b594ffc2e81c37e1b41c8c44947212d206f3e9.
- Documentation updated in ROADMAP.md, ARCHITECTURE.md, AUDIT_REPORT.md, README.md, LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md, and PROJECT_INSTRUCTIONS.md; exact per-commit CI results are being verified.
- Limitations: matching is pure and not persisted; no broker reads, API route, worker, order submission/cancellation, fill ingestion, production migration, or real order was performed. Deployment/staging DB verification remains unavailable because the project is not deployed.
- Next single action: implement a repository-only status transition with allowed-transition rules, optimistic version checks and atomic audit events; no broker I/O.


## Phase 2 — versioned reconciliation state persistence — 2026-10-17

- Added repository-only LiveOrderRepository.apply_reconciliation_transition() in backend/app/repositories/live_order_repository.py. It validates allowed transitions, enforces authenticated-user ownership and expected-version/previous-state compare-and-set, optionally stores the unique broker order ID, and commits the state/version/last-reconciled timestamp and BROKER_STATUS_RECONCILED audit event atomically.
- Safe event details are validated against credential-like keys. Repeated same-state observations at the current version are no-ops. Invalid terminal regressions are rejected; CANCELLED → PARTIALLY_FILLED/FILLED is allowed to represent later broker trade evidence in a cancel/fill race. RECONCILIATION_REQUIRED remains frozen for manual resolution.
- Added tests for atomic state/event persistence, same-state idempotency, stale-version conflict, terminal regression rejection, cancel/fill race and secret-field rejection.
- Code checkpoint commit b3332b839b6f2c39bf2ae678e1aa62ac1f2a3409 passed [GitHub Actions run 39050941218](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050941218): **261 passed, 1 warning**, and SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed.
- Intermediate CI failures were not hidden: run 39050728922 / 39050744745 failed on a malformed test import; run 39050840969 exposed an undefined previous-state variable. Both were corrected; exact final code checkpoint above is green.
- Updated ROADMAP.md (f4e22341829300c8613bf14ac6f4f4f89444a6cd; removed a duplicate Phase 2 checklist item), ARCHITECTURE.md (bfbc8a33bd792c8561c8dfb81c17025c3ad926ce), AUDIT_REPORT.md (db2a2a6335754150fbbf4f7c0234a297b2f05395), README.md (56cb32553696898268d55f71bc0b43da5ddbf6c0), LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md (4021f51377f0a025a706969bec2cca62689d5855), LIVE_TRADING_SAFEGUARDS.md (99016f1ae2349b5fa800bda65930d1c14ef7a280), and PROJECT_INSTRUCTIONS.md (1fbd12d35202f51a332dcf8369244bbc0c8f2b51). Verify the CI run for each exact documentation commit before declaring docs fully verified.
- No broker API reads, fill ingestion, live order submission/cancellation, production migration or real order occurred. The project is not deployed; staging DB verification remains outstanding.
- Next single action: implement pure validation for Upstox per-order trade records, then a transactionally idempotent fill-ingestion repository operation using the existing unique broker-connection + broker-trade-ID constraint. Do not add broker API calls yet.


### Phase 2 documentation CI verification — 2026-10-17
The exact documentation commits for versioned reconciliation persistence have successful GitHub Actions runs:
- ROADMAP.md a25a9c4c4c50c6adc8eb7a2b997f241667e2cf79: [run 39051061693](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39051061693) — success.
- ARCHITECTURE.md bfbc8a33bd792c8561c8dfb81c17025c3ad926ce: [run 39051073011](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39051073011) — success.
- AUDIT_REPORT.md db2a2a6335754150fbbf4f7c0234a297b2f05395: [run 39051083433](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39051083433) — success.
- README.md 56cb32553696898268d55f71bc0b43da5ddbf6c0: [run 39051100719](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39051100719) — success.
- LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md 4021f51377f0a025a706969bec2cca62689d5855: [run 39051113701](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39051113701) — success.
- LIVE_TRADING_SAFEGUARDS.md 99016f1ae2349b5fa800bda65930d1c14ef7a280: [run 39051121157](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39051121157) — success.
- PROJECT_INSTRUCTIONS.md 1fbd12d35202f51a332dcf8369244bbc0c8f2b51: [run 39051130597](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39051130597) — success.
- Prior PROGRESS.md checkpoint 9b52357889ac335326173b1300009e8c7c94dd9f: [run 39051148864](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39051148864) — success.

The latest application-code checkpoint remains b3332b839b6f2c39bf2ae678e1aa62ac1f2a3409, [run 39050941218](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050941218): 261 passed, 1 warning, and SQLite/PostgreSQL 16 migration checks passed. Documentation CI is separate from this application-code verification.

- Final roadmap cleanup commit f4e22341829300c8613bf14ac6f4f4f89444a6cd removes a duplicate fill-ingestion checklist line; roadmap cleanup CI passed [run 39051273827](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39051273827).


## Phase 2 — validated trade normalization and idempotent fill identity persistence — 2026-10-17

- Re-read `PROJECT_INSTRUCTIONS.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `PROGRESS.md`, `AUDIT_REPORT.md`, `README.md`, `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` and `LIVE_TRADING_SAFEGUARDS.md` before implementation. Target remains `tradepro-improved`; original `Tradepro` was not modified.
- Consulted the official [Upstox Get Order Trades API](https://upstox.com/developer/api-documentation/get-trades-by-order/). Added `normalize_upstox_trade()` in `backend/app/services/live_order_reconciliation.py` to validate trade/order IDs, instrument, BUY/SELL, positive integer quantity, finite positive price, and exchange timestamp converted to UTC. It performs no network calls.
- Added `LiveOrderRepository.record_broker_fill()` in `backend/app/repositories/live_order_repository.py`. It scopes writes to an authenticated user's broker connection and optional intent in the same connection; stores individual trade identities under the existing unique `(broker_connection_id, broker_trade_id)` constraint; treats identical replays as no-ops; raises `LiveOrderVersionConflict` for reused IDs with changed payloads; and atomically commits a linked `BROKER_FILL_RECORDED` event. It rejects credential-like metadata keys. It does not update positions, cash, P&L, shared `Order`/`Execution`, or fetch broker data.
- Added normalization tests in `backend/tests/test_live_order_reconciliation.py` and repository tests in `backend/tests/test_live_order_repository.py` covering valid documented timestamp, malformed fields, idempotent replay, changed-payload conflict, connection isolation and credential rejection.
- One initial repository test run failed because the isolation test attempted two Upstox connections for one user, conflicting with the existing unique `(user_id, broker)` constraint. Changed the test's second connection to a distinct broker type; exact final code/test commit `001a6eed2bd7090e2c7a4d3a8f2f87e9d7fa62bc` passed [GitHub Actions run 39052203329](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052203329): **274 passed, 1 warning**, with SQLite/PostgreSQL 16 reversible migration checks.
- Code commits: normalizer `fe884209c8ba3474e7b00577c0ed17c5d7b3f796`; fill repository `9a8be276621afa9cd3bf0b39cf7b7197c78c878b`; normalizer tests `f27bd848c79d8fba33f0618b10d6df3c271292a8`; fill tests `efe0fa54610a6248cc281ca29b62a2dcfbf7ecbd`; corrected isolation test `001a6eed2bd7090e2c7a4d3a8f2f87e9d7fa62bc`.
- Documentation commits: `ROADMAP.md` fc34c20dfafb5adb0ced51a945233e8f644c9100; `ARCHITECTURE.md` 9afe7f552252a8e041d6bf52c805bb71fdbad5e2; `AUDIT_REPORT.md` 939e81b8a1acbef090ac0e81afe5c78f572a28a6; `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` 16718a9c977da1685957da213b055dcbf7a8d7fa; `README.md` fae2b9dbd5a6f7ed2c5a6a6de257d7045943ff75; `LIVE_TRADING_SAFEGUARDS.md` 188083da2ab4ddc7f7619834a7985d5ee9546dcb; `PROJECT_INSTRUCTIONS.md` 4c32f49f35434aeab2b2499ba47e7b0de35254ea. Exact documentation CI runs are being verified and will be recorded below.
- Remaining Phase 2 work: validate each normalized fill against the matched immutable intent snapshot, aggregate partial fills and reconcile out-of-order observations; then build a read-only broker reconciliation worker only after API/error/session contracts are tested. No broker API calls, order submission/cancellation, production migration or real order occurred. App is not deployed; staging DB verification remains outstanding.
- Next single action: implement fill-vs-intent economic validation before `record_broker_fill()` can accept a linked fill, with mismatch/quarantine tests. Keep live submission disabled.


### Phase 2 fill-persistence documentation CI verification — 2026-10-17
All documentation commits for the fill-identity checkpoint have successful GitHub Actions runs:
- `ROADMAP.md` fc34c20dfafb5adb0ced51a945233e8f644c9100: [run 39052328938](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052328938) — success.
- `ARCHITECTURE.md` 9afe7f552252a8e041d6bf52c805bb71fdbad5e2: [run 39052351579](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052351579) — success.
- `AUDIT_REPORT.md` 939e81b8a1acbef090ac0e81afe5c78f572a28a6: [run 39052366324](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052366324) — success.
- `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` 16718a9c977da1685957da213b055dcbf7a8d7fa: [run 39052382345](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052382345) — success.
- `README.md` fae2b9dbd5a6f7ed2c5a6a6de257d7045943ff75: [run 39052403682](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052403682) — success.
- `LIVE_TRADING_SAFEGUARDS.md` 188083da2ab4ddc7f7619834a7985d5ee9546dcb: [run 39052416578](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052416578) — success.
- `PROJECT_INSTRUCTIONS.md` 4c32f49f35434aeab2b2499ba47e7b0de35254ea: [run 39052428182](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052428182) — success.
- `PROGRESS.md` checkpoint 29eac681a6d93a83f05262c60f7eb4163b505c8c: [run 39052450839](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052450839) — success.

The exact final code/test checkpoint remains [run 39052203329](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052203329): **274 passed, 1 warning**, with SQLite/PostgreSQL 16 migration checks. The intermediate failure at run 39052095678 is documented above and was fixed before the passing checkpoint.


## Phase 2 — fill-to-intent economic validation — 2026-10-17

- Continued from the previous checkpoint and added pre-persistence checks in `LiveOrderRepository.record_broker_fill()`: the linked intent must already reference the same broker order ID; instrument, side, product and order type must match the immutable order snapshot; requested quantity must be a valid positive integer; each fill and aggregate persisted fills cannot exceed order quantity; BUY LIMIT/SL fills cannot exceed limit price and SELL LIMIT/SL fills cannot be below it.
- Added tests for mismatched instrument, missing broker-order link, aggregate partial-fill overrun and BUY/SELL limit-price violations.
- Final code/test commit `b69939ece8edc47e1ae05f27c0d9e2144e87db04` passed [GitHub Actions run 39052939770](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052939770): **279 passed, 1 warning**, and SQLite/PostgreSQL 16 reversible migration checks passed. Earlier CI runs in this step caught fixtures with invalid prices and missing new method arguments; fixtures were corrected before the green checkpoint.
- Documentation commits: `ROADMAP.md` cc919b11844b584518f74f7fda0793443f68b9ab; `ARCHITECTURE.md` eee0b6a08f4052a40f7dc17e2f8c3440775f4179; `AUDIT_REPORT.md` 262b7c49cd3e80a9a353ff898d8474a722c81b66; `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` d893483cc29e8e943ab2ba8191ada0139daaf9ef; `README.md` e0e5c92d0ac19c117aca982537c0ba44c84c4335; `LIVE_TRADING_SAFEGUARDS.md` 6ee838b3ffd09cc241f989b980b412e52d2fed89; `PROJECT_INSTRUCTIONS.md` b5b3c3bdb0c8cdbfd5287e651d52df31a4e762de. Exact CI results for these documentation commits are being checked.
- Important limitation: the code persists validated individual fill identities only. It does not fetch broker trades, quarantine/relink unmatched fills, reconcile out-of-order observations, or update the shared `Order`, `Execution`, `Position`, cash or P&L models. Live submission remains unavailable and disabled.
- Next single action: design and test safe handling for unmatched fills and out-of-order status/fill observations before implementing any broker-read worker.


### Phase 2 fill-economic-validation documentation CI verification — 2026-10-17
- `ROADMAP.md` cc919b11844b584518f74f7fda0793443f68b9ab: [run 39053082665](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053082665) — success.
- `ARCHITECTURE.md` eee0b6a08f4052a40f7dc17e2f8c3440775f4179: [run 39053098480](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053098480) — success.
- `AUDIT_REPORT.md` 262b7c49cd3e80a9a353ff898d8474a722c81b66: [run 39053112774](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053112774) — success.
- `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` d893483cc29e8e943ab2ba8191ada0139daaf9ef: [run 39053125136](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053125136) — success.
- `README.md` e0e5c92d0ac19c117aca982537c0ba44c84c4335: [run 39053145371](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053145371) — success.
- `LIVE_TRADING_SAFEGUARDS.md` 6ee838b3ffd09cc241f989b980b412e52d2fed89: [run 39053158840](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053158840) — success.
- `PROJECT_INSTRUCTIONS.md` b5b3c3bdb0c8cdbfd5287e651d52df31a4e762de: [run 39053172125](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053172125) — success.
- `PROGRESS.md` checkpoint e2e06037696e1f608a76610a521e0c0f41f26b2a: [run 39053194020](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053194020) — success.

Exact fill economic validation code/test checkpoint remains [run 39052939770](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052939770): **279 passed, 1 warning**, SQLite/PostgreSQL 16 migration checks passed. This documentation verification does not imply live broker integration or production readiness.


## Phase 2 — safe relinking of previously unmatched fills — 2026-10-17

- Added `LiveOrderRepository.link_existing_fill_to_intent()` so an individual fill can be safely recorded while intent matching is unresolved, then linked later after the intent's broker order ID is known. It revalidates user/connection scope, exact broker order ID, instrument, side, product, order type, requested quantity, limit-price protection and aggregate quantity ceiling.
- Linking uses conditional update on `intent_id IS NULL`; repeat linking to the same intent is a no-op, conflicting links and economic mismatches are rejected, and the link plus `BROKER_FILL_LINKED` audit event commit atomically. Adjusted duplicate delivery semantics so a replay without an intent remains idempotent even if that fill has since been safely linked.
- Added tests for successful late linking, repeat-link no-op/no duplicate audit and economic mismatch rejection. Exact test commit `66802c2eae7adaddb8f1213c9c9a689e4190acaf` passed [GitHub Actions run 39053352921](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053352921): **281 passed, 1 warning**, plus SQLite/PostgreSQL 16 migration checks.
- Documentation commits: `ROADMAP.md` 92724a8bc0685a5e1c2659adc884f52ec3547464; `ARCHITECTURE.md` 70f2d4cb8102092430131fa81bee877cbcd3e169; `AUDIT_REPORT.md` c3f16e80beed1ea7ce2d3e226f80e13676152b63; `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` 4130229c5b9f0d5d13ed00e0f18d71c0837d06eb; `README.md` e0b1bcda069fa2267f3d27817c8c1595f39c3ef0; `LIVE_TRADING_SAFEGUARDS.md` 98a49a064cbde8f916183923f9dbcc17774cb0dc; `PROJECT_INSTRUCTIONS.md` 5488ef3baba3187b6945b87265a63562b430325a. Exact documentation CI runs are being verified.
- Remaining Phase 2 work: broker status/fill out-of-order reconciliation, actual broker read worker with session/expiry/error handling, and applying reconciled fills to shared accounting models. No broker API call, real order, production migration or live accounting occurred.
- Next single action: add explicit tests and state rules for out-of-order broker status after fill evidence, then design a read-only reconciliation worker. Live submission remains disabled.


### Phase 2 unmatched-fill documentation CI verification — 2026-10-17
- `ROADMAP.md` 92724a8bc0685a5e1c2659adc884f52ec3547464: [run 39053474931](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053474931) — success.
- `ARCHITECTURE.md` 70f2d4cb8102092430131fa81bee877cbcd3e169: [run 39053488827](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053488827) — success.
- `AUDIT_REPORT.md` c3f16e80beed1ea7ce2d3e226f80e13676152b63: [run 39053502737](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053502737) — success.
- `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` 4130229c5b9f0d5d13ed00e0f18d71c0837d06eb: [run 39053515056](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053515056) — success.
- `README.md` e0b1bcda069fa2267f3d27817c8c1595f39c3ef0: [run 39053533797](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053533797) — success.
- `LIVE_TRADING_SAFEGUARDS.md` 98a49a064cbde8f916183923f9dbcc17774cb0dc: [run 39053545257](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053545257) — success.
- `PROJECT_INSTRUCTIONS.md` 5488ef3baba3187b6945b87265a63562b430325a: [run 39053678487](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053678487) — success.
- `PROGRESS.md` checkpoint e97cb3112612946d8a08f5d9618645026df66343: [run 39053579681](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053579681) — success.

The verified code checkpoint for unmatched fill relinking remains [run 39053352921](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053352921): 281 passed, 1 warning, with SQLite/PostgreSQL 16 migration checks.


### Final checkpoint — 2026-10-17
- Latest documentation-verification commit `c11c80d1c5cb0835fbcd59ebe6d0cd153ed97539` passed [GitHub Actions run 39053681082](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053681082).
- Latest implementation test evidence for safe unmatched-fill linking: [run 39053352921](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053352921), 281 passed, 1 warning; SQLite/PostgreSQL 16 migrations passed. Latest fill-to-intent economic validation: [run 39052939770](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052939770), 279 passed, 1 warning.
- All seven documentation commits for the unmatched-fill relinking checkpoint have successful exact-commit CI runs. No production deploy, database migration, broker API call, live order or live accounting occurred.
- Next implementation step remains explicit out-of-order status/fill reconciliation rules and tests, then design a read-only broker reconciliation worker with session expiry, rate-limit/backoff, and current-trading-day limitations before adding any broker reads.


## Phase 2 — out-of-order status/fill reconciliation — 2026-10-17

- Re-read `PROJECT_INSTRUCTIONS.md`, `PROGRESS.md`, `README.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `AUDIT_REPORT.md`, `LIVE_TRADING_SAFEGUARDS.md` and `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` before making this step.
- Added pure `resolve_order_state_with_fill_evidence()` to `backend/app/services/live_order_reconciliation.py`; it resolves stale broker status against persisted deduplicated trade quantity and fails closed on contradictions.
- Wired the resolver into `LiveOrderRepository.apply_reconciliation_transition()` before same-state no-op logic. Audit records preserve observed broker state, resolved state, persisted fill quantity and reason.
- State rules: full requested fill quantity resolves to `FILLED`; partial fill plus stale active status resolves to `PARTIALLY_FILLED`; partial fill plus cancellation resolves to `PARTIALLY_FILLED_CANCELLED`; partial fill conflicting with `FILLED`/`REJECTED`, invalid quantity totals or overfill resolves to `RECONCILIATION_REQUIRED`.
- Added parameterized resolver tests and repository regression tests for stale OPEN after a partial fill, partial fill then cancel, and full persisted fill against stale cancellation.
- Exact code/test commit `59f562b62ef6af25ea3a5c6f15cab8a32d505da3` passed [GitHub Actions run 39056392873](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056392873): **294 passed, 1 warning**; SQLite/PostgreSQL 16 reversible migration checks passed.
- One earlier test run failed because it selected the wrong audit event when event timestamps tied at database precision. The assertion was made deterministic by selecting the event using its resolved state; the exact checkpoint above passed.
- Added design-only [READ_ONLY_RECONCILIATION_WORKER_DESIGN.md](READ_ONLY_RECONCILIATION_WORKER_DESIGN.md), commit `7fb6c86e837636a41d25a79610246ab711eab295`. It specifies a read-only client boundary, user/connection scoping, token and rate-limit handling, idempotent fills, safe audit, and failure recovery. No worker or broker reads are implemented yet.
- Updated docs: `ROADMAP.md` `e205cca474ba8263dc0b91ee156ea8dd06cd0bbc`; `ARCHITECTURE.md` `a5c411e3b3b88dac54348d3b9dea3bbf964d5694`; `AUDIT_REPORT.md` `59c02811698d24e634ea6024c0c1eb540643bc3f`; `README.md` `dd9450b77d2e16441d3765b2bd6189552805a12a`; `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md` `5c6bd1f93e3b7fdaafee1bc83120467e455289d4`; `LIVE_TRADING_SAFEGUARDS.md` `311db585ed102db53778bd7f4634bca89f05ca73`; `PROJECT_INSTRUCTIONS.md` `5a2f42b5ccee2f5020c198748a8c2b4457350e02`. Exact documentation CI runs must be checked before calling this fully verified.
- No real Upstox API reads, order submission/cancellation, production migration or local portfolio accounting updates occurred. App remains undeployed; staging verification is still pending.
- Next step: implement a narrow read-only Upstox client/worker against official GET-only endpoints and mocked contract fixtures, with token-expiry, 403, 429/Retry-After, bounded 5xx retry, pagination, lease contention and repeated-run tests. Do not inject the full write-capable execution adapter; keep live submission disabled.


## Phase 2 — GET-only Upstox client boundary — 2026-10-17

- Added `backend/app/brokers/upstox/reconciliation_client.py` with fixed GET-only methods for order book, order details, order history (by order ID or tag), and per-order trades. It intentionally exposes no place/modify/cancel methods.
- The client returns sanitized error categories for missing token, 401, 403, 429, other 4xx, 5xx, timeout, network failure and non-JSON responses. It does not return raw error bodies or exception text.
- Added `backend/tests/test_upstox_reconciliation_client.py` contract tests for official endpoint paths/parameters, missing-token short-circuit, sanitized HTTP/network failures, and absence of write methods.
- Exact test commit `10d9938d17c4c67649c5a4b9c305684ff8f36e52` passed [GitHub Actions run 39056868434](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056868434): **309 passed, 1 warning**, plus SQLite/PostgreSQL 16 reversible migration checks. Tests use a mocked HTTP client; no Upstox request was made.
- Added [READ_ONLY_RECONCILIATION_WORKER_DESIGN.md](READ_ONLY_RECONCILIATION_WORKER_DESIGN.md) and updated roadmap, architecture, audit, README, reconciliation design, safeguards and project instructions. The exact docs CI runs for the previous out-of-order checkpoint passed: roadmap [39056606410](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056606410), architecture [39056618397](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056618397), audit [39056630473](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056630473), README [39056642292](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056642292), reconciliation design [39056653110](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056653110), safeguards [39056663764](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056663764), instructions [39056675913](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056675913), progress [39056709672](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056709672), worker design [39056552758](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056552758). All reported success.
- Latest remaining docs commits for the client boundary are: roadmap `59d7351fe91d34a17c860ad64ac6fea75a85b2df`; architecture `925e7f00ae56ce18037a2acc09858fac500cdabe`; audit `b0ff85bc6133ab61724e4ca99669ae1a41781f6c`; README `a1681218e43b55e36885a95af9b0db26430233ca`; reconciliation design `e91241dbf910279fa70c555fb74a4884917a36de`; safeguards `6f65fcdf68e81db1e433eaa8f3658014605d802b`; instructions `61dbece6164e0a8e5799a840e00fb524bf6781aa`; worker design `14625c1c2d7532263c4955e39e14eff2d2498671`. Their exact CI runs are being checked.
- Next implementation action: implement the worker orchestrator with user/connection ownership checks, token expiry checks, bounded retries and lease/concurrency controls. It must use this narrow GET-only client, never the general write-capable adapter. No broker polling, real order, production migration or accounting update has happened.


## Phase 2 — leased read-only reconciliation worker and failure-path tests — 2026-10-17

### Read instructions and current repo first
- Read `PROJECT_INSTRUCTIONS.md`, `PROGRESS.md`, `README.md`, `ROADMAP.md`, `ARCHITECTURE.md`, `AUDIT_REPORT.md`, `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`, `LIVE_TRADING_SAFEGUARDS.md` and `READ_ONLY_RECONCILIATION_WORKER_DESIGN.md`; inspected the current `main` tree, worker/client/repository/model/test code and latest GitHub Actions before editing.

### Implementation already on main and verified
- Worker commit [`4ee8427f890f7c31021e30f7b36177e2f3f227c3`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/4ee8427f890f7c31021e30f7b36177e2f3f227c3): `backend/app/services/live_order_reconciliation_worker.py`. It uses only the fixed GET-only client, validates user-owned Upstox connection and usable token, claims/renews/completes the durable lease, performs bounded retry for read-only transient errors, reads order book + daily trades, normalizes trades/orders, strictly matches intents, persists unmatched fills then links only after repository economic checks, and reconciles state against persisted trade evidence. No schedule/API route is wired.
- PostgreSQL concurrency test commit [`bf0c2b707aaa023a961f899502ed9f2ae4d265a4`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/bf0c2b707aaa023a961f899502ed9f2ae4d265a4) verifies two simultaneous lease claims allow only one lease owner.
- This continuation added `test_worker_does_not_retry_forbidden_response`, `test_worker_bounds_server_error_retries_before_any_mutation`, and parametrized malformed envelope/data cases in `backend/tests/test_live_order_reconciliation_worker.py` (commit [`bffeefc7921fd96c8fbeab1b201eb3088e87f497`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/bffeefc7921fd96c8fbeab1b201eb3088e87f497)). The tests prove 403 is not retried, 503 retries are bounded, malformed order-book envelopes fail before fill/status writes, and the intent remains unchanged.
- Exact latest code/test run [39058734080](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39058734080) passed **338 tests, 1 warning**; SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed.

### Documentation commits from this continuation
- `ROADMAP.md`: `ce41b45047ecfb0a2de1a1101c6be380013b67bc`
- `READ_ONLY_RECONCILIATION_WORKER_DESIGN.md`: `4af221c79f2d55818a820617521048855f613af2`
- `ARCHITECTURE.md`: `46f27dfb503c9eed64f7039ea0dafbe656d06c60`
- `AUDIT_REPORT.md`: `b62252599168d2f6eb91eed900851285d7fa13a1`
- `README.md`: `b729eb4e11605867dd23ce144ceab009159990b0`
- `LIVE_TRADING_SAFEGUARDS.md`: `69a3388db68b6fe7098bbf7ed56277d0eca06f59`
- `PROJECT_INSTRUCTIONS.md`: `2da55ce235d03c14eeca0aeec90d4d415db18ae1`
- `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`: documented in a separate commit during this continuation; verify the exact SHA and its CI result before calling all docs verified.

### Explicit limitations / what did not happen
- The worker is an on-demand Python service, not scheduled and not exposed by an API route. Tests use mocks. No real Upstox request, live order submission/modification/cancellation, production migration, or local Order/Execution/Position/cash/P&L update occurred.
- Current run reads order book and daily trades; historical-day/session pagination semantics are not implemented/verified. There is no durable operator-facing run-summary/manual-review queue yet. CI passing does not equal staging/production verification.
- Earlier worker implementation CI attempts had failures during iterative development; fixes were made in later commits. The latest exact run cited above is green; earlier failures remain visible in Actions.

### Next single action
Review official Upstox current-day trade/order-book response and history/window semantics; then add persistent, credential-safe reconciliation run summaries/manual-review visibility and crash-boundary tests. Keep live submission disabled and do not add any broker write method to the worker.


### Durable run-summary documentation verification — 2026-10-17
The eight-file documentation bundle commit [`091eab31cbc93b29b88118b61693c5fc4f763da2`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/091eab31cbc93b29b88118b61693c5fc4f763da2) updated `ROADMAP.md`, `ARCHITECTURE.md`, `AUDIT_REPORT.md`, `README.md`, `PROJECT_INSTRUCTIONS.md`, `LIVE_TRADING_SAFEGUARDS.md`, `READ_ONLY_RECONCILIATION_WORKER_DESIGN.md`, and `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`. Its exact workflow [39059521781](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059521781) passed **340 tests, 1 warning**, plus SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks. Earlier worker documentation commits also passed their own CI runs: roadmap 39058899956, worker design 39058934654, architecture 39058945827, audit 39058984056, README 39058992933, safeguards 39059003264 and instructions 39059012444. The current next implementation action is durable manual-review issue records with deduplication and safe detail fields; no UI/API exposure until separately reviewed.


### Manual-review issue queue documentation checkpoint — 2026-10-17
- Updated docs commit [`45dd099ddfda5107ec3502fbe5cb1fedbfce02d3`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/45dd099ddfda5107ec3502fbe5cb1fedbfce02d3) updated `ROADMAP.md`, `ARCHITECTURE.md`, `AUDIT_REPORT.md`, and `README.md`.
- Updated docs commit [`5ff6cad81664ed5827b5050a0021dc3a0c462209`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/5ff6cad81664ed5827b5050a0021dc3a0c462209) updated `PROJECT_INSTRUCTIONS.md`, `LIVE_TRADING_SAFEGUARDS.md`, `READ_ONLY_RECONCILIATION_WORKER_DESIGN.md`, and `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`.
- These docs describe the verified code checkpoint [`71b5668533f0461c12374319e496665cbda7e61c`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/71b5668533f0461c12374319e496665cbda7e61c), which passed [run 39059749652](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059749652): **342 passed, 1 warning**, plus SQLite/PostgreSQL 16 reversible migration checks. Exact CI for these two newest documentation commits is being verified separately.
- Current status: durable run summaries and deduplicated issue records are stored in the database; no operator-facing issue API/UI exists. The worker is not scheduled and remains GET-only. No live order actions, production migration or local accounting updates occurred.
- Next single action: implement authenticated read-only listing endpoints for reconciliation runs and issues, with strict current-user and broker-connection scoping, sanitized response schemas and cross-user isolation tests. Do not add issue-resolution mutation yet.


## Phase 2 — owner-scoped reconciliation read API — 2026-10-17

- Added `backend/app/api/v1/reconciliation.py` with authenticated read-only `GET /api/v1/reconciliation/runs` and `GET /api/v1/reconciliation/issues`; added Pydantic response schemas, `LiveReconciliationQueryRepository`, and mounted the router in `backend/app/api/v1/router.py`.
- Every query filters by current authenticated `user_id`; optional broker-connection/status/type filters and bounded limit (1–100) are supported. Schemas expose safe run counters and issue metadata/details only, not raw broker payloads or credentials. No route starts a worker or mutates an issue/order.
- Added `backend/tests/test_api_reconciliation_isolation.py`: unauthenticated requests rejected, owner sees only own run/issues, another user's connection filter returns an empty list, status/limit validation works, and response does not expose token fields.
- Exact code commit [`f65b4ba20ce9a1dacfe40580d8042cd98f36c19f`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/f65b4ba20ce9a1dacfe40580d8042cd98f36c19f) passed [run 39060230705](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060230705): **345 passed, 1 warning**, plus SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks.
- Documentation commit [`81b27463ca3709e8669a1f7c233128bf439646f0`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/81b27463ca3709e8669a1f7c233128bf439646f0) updated roadmap, architecture, audit and README. Documentation commit [`4a0c64294714a5ea951c195ca9878838d28b5e3d`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/4a0c64294714a5ea951c195ca9878838d28b5e3d) updated project instructions, safeguards, worker design and live-order design. Exact docs CI is being checked.
- Remaining: frontend review UI; separately authorized issue-resolution workflow; stale `RUNNING` recovery and crash/restart tests; official historical trade retrieval/pagination; no real read-only sandbox test yet. No live order action, production migration or accounting update occurred.
- Next single action: verify the latest documentation CI, then add frontend screens to view run history/open review issues without exposing secrets or enabling issue mutations.


## Reference-repository audit checkpoint — 2026-10-20

- Audited the current `tradepro-improved` tree and recent commits, plus relevant source/docs/tests/licences for four references: [AI Trading Platform](https://github.com/afnanadil2007-design/AI-Trading-Platform), [Algo Options Platform](https://github.com/iamadarsha/algo-options-platform), [OpenAlgo](https://github.com/marketcalls/openalgo), and [Kite Algo Bot](https://github.com/KoshIndia/kite-algo-bot).
- Added [REFERENCE_REPOSITORY_AUDIT.md](REFERENCE_REPOSITORY_AUDIT.md) with overlap, useful patterns, licence constraints, prioritized integration ideas and verification limitations. No external code was copied and no application code/schema was changed by the audit.
- **Historical blocker (resolved at code/test checkpoint `a906274`):** run 39113589752 failed collection because live-fill accounting dependencies were absent. The missing models and migration revisions have now been added; run 39475387511 passed 355 tests and SQLite/PostgreSQL 16 reversible migration checks. See the recovery checkpoint below.
- The protected original repository `tarunsharma2610-del/Tradepro` was read only; no write action was made against it. All audit documentation changes are confined to `tradepro-improved`.
- No live broker request/order, production migration, or production-data write was performed.
- **Temporary rollback on 2026-10-20, then recovery:** the three incomplete live-fill accounting files were removed to investigate a CI collection/migration-chain blocker, but the user requested restoration. All three original file contents have now been recovered from their pre-deletion Git blobs and restored to their original paths on `main` in commits `8c7fef18f7e23b31e072df7cc1b70a8c85f4ae44`, `bdbc1fb24f9c64a916c7a0fe7a012875e258265e`, and `28af2b521e8e840ab03546f22a1c08cf9b99e358`. No redesign or content rewrite was made to those recovered files.
- Removal commits: `eb0048bacd2e57c1d3348030fb9a97875304caa4`, `df68f0544b844d4c4dab14812bea5d89d6417e2e`, `bcaa08cc95bc1ac8e5709ff7f4ac3cb1d1ab3879`. No other application behavior was intentionally changed in this repair.
- **Validation status:** GitHub Actions must rerun on the repaired HEAD. Until the new workflow completes successfully, do not claim CI is green. No real broker orders or production migrations were run.
- **Next single action:** inspect the CI run triggered by this repair; if it passes, audit migration graph and then resume reconciliation gates. If it fails, fix the first new failure before proceeding.


## Live-fill accounting recovery and verification — 2026-10-20

The three files deleted during the temporary rollback have been restored byte-for-byte from their pre-deletion Git blobs at their original paths. Supporting models and migration revisions have now been implemented in this repository.

- Restored originals: `backend/app/services/live_fill_accounting_service.py`, `backend/tests/test_live_fill_accounting_service.py`, `backend/alembic/versions/202610180008_execution_charge_provenance.py`.
- Added models: `backend/app/models/broker_order.py`, `backend/app/models/broker_trade_record.py`, `backend/app/models/live_position.py`; registered them in `backend/app/models/__init__.py`.
- Added migrations `202610180006_broker_trade_intake.py` (down revision `202610170005`) and `202610180007_live_position_execution_provenance.py` (down revision `202610180006`), completing the chain to revision `202610180008`.
- Updated `Execution` model to match charge-provenance migration and added a guard/test rejecting a broker trade quantity above the broker-confirmed child-order fill quantity.
- Exact code/test checkpoint `a906274b98f3f7e0c913f376128f4996b996c52b` passed GitHub Actions [run 39475387511](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39475387511): **355 passed, 1 warning**; Alembic upgrade → downgrade → re-upgrade passed on SQLite and PostgreSQL 16.
- Scope limitation: this is a tested accounting service/storage foundation, not a complete live-fill pipeline. The service remains unregistered; broker trade ingestion, invoking the service from reconciliation, shared live order/status accounting, production staging verification and real-account reconciliation remain outstanding. No real broker orders or production migrations were run. Live order submission remains disabled.
- Next action: continue the existing Phase 2 reconciliation release gates, inspect crash/recovery and broker-confirmed fill linkage, and only integrate live accounting through a separately reviewed, tested path. Do not delete the recovered files without explicit user approval.


## Test-baseline and branch reconciliation — 2026-10-21

- Verified the exact 18 October safety checkpoint from GitHub Actions run [39140514552](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39140514552), commit `9085d9fbdcc8ee2dd8baac6f5e73f92bd76cfa8b`: **456 passed, 8 skipped, 1 warning**. This was the submission-gate checkpoint before later partial-fill and response-parser commits; CI for those later safety-branch commits was not established by that run.
- Verified current `main` HEAD `074dd533bb84ac8102a6602f50cf9d0f57323a3d` and GitHub Actions run [39476051343](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39476051343): **355 passed, 1 warning**. This is a real difference in the checked-out code/test suite, not just an unsupported estimate.
- Compared the recursive Git trees: current `main` contains 35 `backend/tests/test_*.py` files; `safety/fail-closed-trading-mode` contains 48. Twenty-three safety-branch test modules are absent from `main`, including broker trade ingestion, live account safety, broker-write boundary, live execution/recovery, fill-reconciliation coordinator/integration, Upstox response parsing, and live pre-trade/preflight coverage. The branches also differ in application code: 19 safety-branch API/model/service paths related to those tests are absent from `main`. The current `main` also has reconciliation-worker and live-fill accounting implementation that is not a drop-in match for the safety branch.
- GitHub compare reports the refs as diverged (389 commits ahead and 1,029 behind for the selected comparison). Therefore **do not merge or cherry-pick the safety branch wholesale** and do not copy tests without first porting/validating their required production code. The 101-test count difference is explained by materially different test trees; it is not yet evidence that exactly 101 tests were deleted from the same code line.
- Audited the 14 migration files on `main`: the chain is linear from `202608170001` through `202610180008`, with no missing parent revision and one terminal head `202610180008`. Current CI confirms SQLite and PostgreSQL 16 upgrade → downgrade → re-upgrade checks pass.
- Live-fill accounting remains a foundation only: `LiveFillAccountingService` is present but intentionally unregistered; broker-trade intake/reconciliation integration, shared parent-order state accounting, and end-to-end crash/replay verification remain outstanding. Live broker submission remains disabled; no live broker request or production migration was performed.
- Next safe step: create a controlled porting plan from the safety branch by grouping its missing tests with their required source/migration dependencies; port one coherent unit at a time onto `main`, run focused tests plus the complete backend/PostgreSQL migration suite, and update this log only with exact-head CI evidence. Keep the original `Tradepro` repository untouched.


## Upstox response-validation slice — CI VERIFIED (2026-10-21)

- Ported the pure response-validation module `backend/app/brokers/upstox/response_parsing.py` from the 18 October safety branch into `main` as commit [`6a33882`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/6a338820c37ec44632023327cf8e6fa671682ed0).
- Added its regression suite `backend/tests/test_upstox_response_parsing.py` in commit [`03d2607`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/03d2607792e46272566b6871a452e612b1d6ca7a). It covers order IDs/details/history/trades, strict fill quantity versus average-price consistency, funds and pledged-margin separation, margin estimates, and brokerage-estimate component consistency.
- Exact-head GitHub Actions [run 39477976464](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39477976464) passed: **406 passed, 1 warning**. SQLite and PostgreSQL 16 Alembic upgrade → downgrade → re-upgrade steps also passed.
- This is a pure parser/validation slice only. It makes no network requests, does not call a broker, does not alter accounting, and does not enable order submission. The parser is not yet wired into the current main reconciliation client/worker.
- Next: inspect how the current main reconciliation client consumes order/trade payloads; map the missing broker-trade-ingestion tests to current-main models and migrations before adapting a staging service. Preserve current stricter DB constraints and keep the service unregistered until the end-to-end path is reviewed.


## Broker trade staging port — verified checkpoint (2026-10-21)

- Ported `backend/app/services/broker_trade_ingestion_service.py` and `backend/tests/test_broker_trade_ingestion.py` from the safety branch as a dependency-complete first slice, then adapted the tests to current `main` schema constraints.
- Current-main `BrokerOrder` requires a non-null broker connection and status; tests now supply those fields. A historical test expecting an unbound child order to persist was replaced with a database-invariant test proving the stricter main schema rejects that state. A stale `Order.broker_order_id` fixture was removed because current main maps broker child IDs in `BrokerOrder` instead.
- Staging now rejects trades with missing/blank exchange timestamps because current-main `BrokerTradeRecord.exchange_timestamp` is non-null. A regression case covers this fail-closed behavior.
- Exact code/test checkpoint `3f210e592c8aa2e643e536a04f186da8187bc06b`, GitHub Actions [run 39480002328](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39480002328): **431 passed, 1 warning**. SQLite and PostgreSQL 16 Alembic upgrade → downgrade → re-upgrade checks passed.
- Service scope is staging only: it does not update `Execution`, `Position`, portfolio cash, or local `Order` status. It is not wired into the reconciliation worker or registered as an automatic/live submission path. No broker network call or real order was made by CI.
- Added [`SAFETY_BRANCH_PORT_MATRIX.md`](SAFETY_BRANCH_PORT_MATRIX.md), listing the 21 safety-only test modules and dependencies/port decisions. The historical 456-pass and newer 406-pass runs are different branch/test trees; do not interpret the 50-pass difference as 50 deleted tests.
- Next: review child-order reconciliation against current main's worker and repository; port only the required partial-fill/parent-order behavior with explicit idempotency, transaction rollback, and accounting-isolation tests. Keep live-write and fill-promotion paths disabled.


## Cumulative live-fill quantity guard — verified checkpoint (2026-10-21)

- Found a correctness gap in the unregistered `LiveFillAccountingService`: each staged trade was compared individually with the child order's filled quantity, so two distinct trade records could each pass even when their combined accounted quantity exceeded that child fill total.
- Added a per-child aggregate check that sums already-accounted `Execution.quantity` rows for the same broker connection/child order before promotion. The child order is locked first to serialize competing promotions on PostgreSQL. Replays of an already-accounted identical trade remain idempotent.
- Added regression coverage that promotes one trade, then proves a second distinct trade cannot overrun the same child's aggregate fill cap; the live position and paper position remain unchanged after rejection.
- Exact code/test checkpoint `5ad579f60e78dcb5fdee14dcdb17dc4c9d8956a1`, GitHub Actions [run 39480669799](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39480669799): **432 passed, 1 warning**. SQLite and PostgreSQL 16 reversible migration checks passed.
- This is defensive accounting-service validation only. `LiveFillAccountingService` remains deliberately unregistered; staged trades are not automatically promoted and live broker submission remains disabled.
- Architecture issue for next step: the read-only reconciliation worker currently stores trade identity in `BrokerFillIdentity`, while the staging/accounting path uses `BrokerTradeRecord`. Before wiring either path into the other, choose and document one authoritative flow (or a deliberate, transactional bridge) to prevent split-brain fill state and duplicate processing.


## Broker child-order reconciliation port — verified checkpoint (2026-10-21)

- Ported `BrokerChildOrderReconciliationService` and its regression suite from the safety branch, adapting it to current main's stricter `BrokerOrder` schema. Main's child row persists status and filled quantity; weighted average fill price is computed from validated staged trades and checked against the broker snapshot, not persisted to a nonexistent column.
- Reconciliation validates owner/order/connection mapping, rechecks the broker token after asynchronous reads, locks and refreshes the child row, requires staged trade quantity to equal broker-reported filled quantity, checks weighted average price, rejects quantity regressions and terminal-state conflicts, and changes only child-order metadata. It does not mutate parent `Order`, `Execution`, `Position`, or portfolio cash.
- Exact code/test checkpoint `0b1224b3df446a1fcfd1725adcde29a35f722631`, GitHub Actions [run 39481385581](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39481385581): **438 passed, 1 warning**. SQLite and PostgreSQL 16 reversible migration checks passed.
- The service is not wired to an API route or automatic worker. It uses mocked broker responses in tests; no real broker call/order was made by CI.
- Next: resolve the architecture boundary between the intent-based worker's `BrokerFillIdentity` and the legacy/manual-order staging/accounting path's `BrokerTradeRecord`. Decide whether these are intentionally separate workflows or require a transaction-safe bridge before connecting reconciliation to live accounting.


## Parent-order reconciliation lock guard — 2026-10-21

- Child reconciliation now locks/revalidates the owned parent Order after broker status I/O, checks LIVE mode and the pre-network instrument/side/quantity snapshot, then locks the BrokerOrder child before reading staged trade totals. This matches ingestion's parent→child lock order.
- Added a regression test that switches the local order to PAPER during the status read and confirms child status/fill quantity remain unchanged. Staged evidence remains available; no accounting rows are created.
- Exact code/test checkpoint `84f3a3e48a64b6e1d764a87a2b337b2a8f052741`, [CI run 39482592808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39482592808): **439 passed, 1 warning**, with SQLite/PostgreSQL 16 reversible migrations passing.
- This does not enable parent Order accounting or live submission. Keep `BrokerFillIdentity` and `BrokerTradeRecord` workflows isolated until their intended boundary is decided.



## Broker-write source guard — implementation checkpoint (2026-10-21)

- Added `backend/scripts/check_broker_write_boundary.py`, an AST-based source guard that rejects unapproved production references to `place_order`, `modify_order`, and `cancel_order`, while allowing the known PAPER execution call sites and the low-level Upstox adapter definitions.
- Added seven focused unit tests in `backend/tests/test_broker_write_boundary_guard.py` for unauthorized writes, generic receiver bypass, central write boundary, adapter definitions, docstring false positives, and approved PAPER call sites.
- Added a mandatory CI step to `.github/workflows/backend-tests.yml` that runs `python -m scripts.check_broker_write_boundary` against the real application source tree.
- Code/config commits: `fe6700528469a91100f3bf8862a6e4eca3831951` (guard), `c0d8f9293ba44d6abccd41818599fe7dfdcbd0a2` (tests), `e7885101dbbb850cd69c73e4d390177caaa21024` (fixture correction), and `c563683b85d7801cd19dcf3d1c7784ec6e433d1f` (CI integration).
- **Verification status:** the latest commit is `c563683b85d7801cd19dcf3d1c7784ec6e433d1f`. The connected GitHub workflow tool does not expose push-triggered run listings, so the CI result for this exact head is not yet verified here. Do not treat the earlier 439-pass run as verification of this guard. The next action is to inspect the workflow result for this exact head and fix any guard findings before proceeding.
- Scope remains static source protection, not proof against reflection/dynamic dispatch. Live broker order submission and automatic accounting promotion remain disabled.



### Source-guard fixture follow-up

- Corrected the docstring/newline fixture in `backend/tests/test_broker_write_boundary_guard.py`; follow-up commit `a9105fdfc2252c067782649c5c659460db042cc4`.
- This correction has not been independently run locally in this session. The exact-head CI gate remains open; check the workflow result for the current `main` head before proceeding.


## Broker-write guard hardening follow-up — 2026-10-21

- Reviewed the first AST guard and found its exemptions too broad: the entire Upstox adapter file was skipped, and any `service.place_order` reference in the portfolios module could pass regardless of function context.
- Narrowed exceptions to the exact known PAPER strategy call and the named PAPER `place_order` / `cancel_order` endpoint functions. The adapter file is now scanned normally; method definitions are not AST attribute references, while unexpected calls inside that file are detected.
- Added regression coverage for unexpected adapter calls and for a broker-write reference hidden in an unrelated helper in the otherwise approved portfolios module.
- Commits: `00c0986a0628cc6b55b842cfcf6e7fc01b071de4`, `30c1aa7b78de357e070f7cdb37b3719112ee8850`, newline correction `a75a15a0feae98fb2eb4d4301f199d33566c0acf` / `430d00ae787a250f5c7f425e2b72ad02a38c396a`.
- Historical broker-write-guard checkpoint superseded by current verified CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386): the guard passed on the latest code/test HEAD. The static guard still cannot prove safety against reflection/dynamic dispatch; live writes/accounting promotion remain disabled.


## Exact-head broker-write guard verification — 2026-10-21

- Verified current `main` HEAD `975717b05a3aa5faa030f3f9e177dbcf6066daf3`; GitHub Actions [run 39550130192](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39550130192) passed **447 tests, 1 warning**.
- The run confirms the real application-source broker-write guard passed, and SQLite plus PostgreSQL 16 upgrade → downgrade → re-upgrade migration checks passed.
- The immediately preceding run for `6273a3178e37a27e47a8634564f634075f375f3e` failed; the latest test fix corrected a line-number assertion in the guard test. This was a test assertion failure, not evidence that production broker logic was broken.
- Next Phase 2 work: review the dependency map and design the explicit boundary between intent-based `BrokerFillIdentity` and manual-order `BrokerTradeRecord` before any integration. Keep live submission and automatic accounting promotion disabled.

## Fill-workflow boundary review and regression guard — 2026-10-21

- Reviewed the current worker, repository, staging service, and accounting service. The intent path uses `BrokerFillIdentity`; the manual Order path uses `BrokerOrder` + `BrokerTradeRecord` and a separate explicit-charge accounting service. Their unique constraints are separate, so cross-table duplicate detection is not automatic.
- Decision: preserve them as separate workflows for now; do not dual-write or add a bridge until canonical identity, conflict semantics, ownership/account linkage, transaction, replay, rollback and crash-recovery rules are designed.
- Added assertions to `test_worker_links_trade_and_resolves_full_fill_without_order_write_methods` and `test_worker_repeat_run_deduplicates_fill_and_audit` proving reconciliation and replay do not create `BrokerTradeRecord`, `Execution`, or `LivePosition` rows and do not change portfolio cash.
- Test commit: `3683082509c4b331ab9c7ebceb928e925414de35`. Exact-head CI is pending; do not treat prior 447-pass CI as verification of this test change.
- Next: run the exact-head backend/source-guard/SQLite/PostgreSQL CI. If green, proceed to the next dependency-complete safety slice and add stale-run/crash-recovery coverage. Live order submission and automatic accounting promotion remain disabled.

## Orphaned reconciliation-run recovery — 2026-10-21

- Added `LiveReconciliationRunRepository.fail_orphaned_runs(...)` to mark stale `RUNNING` summaries as `FAILED` with the safe category `WORKER_INTERRUPTED` only when no unexpired lease currently owns the specified user/connection.
- The recovery operation is scoped to the authenticated owner and broker connection, only affects runs older than the explicit cutoff, preserves numeric summary counters, and does not retry broker requests or alter fill/accounting evidence. It locks the lease row where supported and releases the transaction when recovery is deferred.
- Added tests for stale-run recovery, active-lease protection, owner/connection and age scoping, and invalid cutoff times. Normalized SQLite's naive persisted UTC lease timestamps before comparison.
- Implementation commits: `c21dc711c9102c4a6f0aad36b404ba8c1b57d5f8`, `007383da7f0ca5a1793098288f610ed98de9eb71`, `298caa0a1a05124cdf6fdc9d94ff0644f20295a5`. Exact-head CI pending; do not claim green until the latest commit passes backend tests, guard, and both database migration checks.
- Recovery is currently an explicit repository operation, not automatically scheduled. Live broker submission and automatic accounting promotion remain disabled.

## Exact-head stale-run recovery verification — 2026-10-21

- Integrated stale-run recovery into the on-demand reconciliation worker before lease claim. Stale `RUNNING` summaries older than the lease-duration cutoff are marked `FAILED/WORKER_INTERRUPTED` only when no unexpired lease owns the user/connection. If recovery fails, the worker fails closed before claiming a lease or calling the broker.
- Active-lease protection is tested; expired orphan recovery is tested end-to-end through the worker; recovery-error handling is tested to make no broker calls. The repository method preserves stored counters and does not retry broker requests or mutate fill/accounting rows.
- Exact current code head `c1c0d8c6fbbb5dcc1389d2da77e911c815958d88`, [GitHub Actions run 39551504884](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39551504884): **455 tests passed, 1 warning**; broker-write guard and SQLite/PostgreSQL 16 migration cycles passed.
- Caveat: stale-run summary counters are not a durable progress ledger; `WORKER_INTERRUPTED` must be interpreted as incomplete/unknown work, not proof that zero fills occurred. No automatic broker retry, live order submission or accounting promotion is enabled.
- Next Phase 2 gate: add PostgreSQL concurrency coverage for orphan recovery versus lease claim and review the UI/API presentation of interrupted runs so incomplete counters are not shown as authoritative.


## Exact-head crash-recovery race and UI verification — 2026-10-21

- Added PostgreSQL concurrency coverage for orphan-run recovery racing an expired-lease claim. The test verifies the outcome is serialized: either the stale run is marked `FAILED/WORKER_INTERRUPTED` before a new lease wins, or an active new lease prevents recovery.
- The reconciliation review UI now explicitly warns that a `WORKER_INTERRUPTED` run's counters may be incomplete and zero values do not prove that no fills were processed.
- Exact current code/test HEAD `d0437be8ef27c4e86d659a9b85bf42dbdb99ecc4`: backend [run 39552046237](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552046237) passed **456 tests, 1 warning**, source guard and SQLite/PostgreSQL 16 migration cycles; frontend [run 39552046207](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552046207) passed TypeScript and Next.js build.
- This supersedes the previous pending verification note. Stale-run recovery remains metadata-only: it does not retry broker reads, promote fills or mutate accounting. Live submission and automatic promotion remain disabled.
- Next Phase 2 task: audit the crash window between lease release and run-summary persistence, and fail-closed behavior for inconsistent lease state (for example a non-null lease token with no expiry). Preserve idempotency and do not introduce automatic scheduling or broker writes without review.


## Phase 2 exact-head checkpoint — 2026-10-21

- Current verified code/test HEAD `0ce59a7965e3e96a425fa8ae30c841eb0cb755bc`: [backend CI run 39552821228](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39552821228) passed **461 tests, 1 warning**, broker-write boundary guard, SQLite migration cycle, and PostgreSQL 16 migration cycle.
- Added fail-closed checks for inconsistent lease token/expiry state in both stale-run recovery and the lease claim repository. Claim predicates no longer treat either half-populated state as an expired lease.
- Added a crash-window regression test: lease release succeeds, terminal summary persistence fails, the run remains marked RUNNING, and later stale-run recovery marks it WORKER_INTERRUPTED before the next run.
- Crash-window test commit `cc01b7143bafba57ed20feaa6cef40c57f122c27` passed 459 tests; the latest exact-head run above includes the additional claim-state tests.
- Next: review whether lease completion and run-summary terminal persistence should be one atomic transaction; add tests for lost-lease / summary ordering before changing lifecycle semantics. Keep recovery metadata-only, preserve separate fill workflows, and keep live submission/accounting promotion disabled.


## Phase 2 atomic lifecycle finalization — 2026-10-21

- Current verified code/test HEAD: `8f967adaa2328f16a0a08a104c3ec394e62f9310`.
- Exact-head [backend CI run 39553655005](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553655005) passed **463 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles.
- Added `LiveReconciliationRunRepository.finish_with_lease`: lease completion and terminal run-summary persistence now share one database transaction. If run finalization fails, the lease release rolls back too.
- Worker finalization now uses that atomic method. If the lease token is no longer owned, the run is finalized as `LEASE_LOST` without releasing the newer owner's lease.
- Tests cover atomic rollback on a terminal/missing run, protection of a newer lease, and recovery after a simulated worker crash/finalization failure. The worker leaves the lease intact until expiry if summary finalization fails, then stale-run recovery handles the incomplete run.
- Next: review cancellation/exception paths and lease renewal/expiry behavior under concurrent worker activity. Keep reconciliation read-only; no automatic broker writes, live submission, accounting promotion, or scheduler.


## Phase 2 lease-loss and cancellation checks verified — 2026-10-21

- Current verified code/test HEAD: `2ac6bfaafd3475ee63360bd0049b0b6987236bc1`.
- Exact-head [backend CI run 39553981172](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39553981172) passed **465 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles.
- Added a worker test that replaces the lease owner before local processing; the old worker stops before persisting fills, marks its run `LEASE_LOST`, and leaves the new owner's lease intact.
- Added cancellation coverage: cancellation during broker read leaves a RUNNING run and owned lease for expiry-based recovery; the next worker marks the stale run `WORKER_INTERRUPTED` before starting a fresh run.
- Atomic finalization remains in place: lease release and terminal run-summary update share one transaction; failed finalization rolls back lease release.
- Next: review whether lease renewal is frequent enough during large trade/order batches and confirm all cancellation/error paths converge on safe recovery. Keep broker access read-only and live submission/accounting promotion disabled.


## Phase 2 lease-renewal boundary and UI verification — 2026-10-21

- Current code/test HEAD: `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`; backend [run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write guard, and SQLite/PostgreSQL 16 migration cycles; frontend [run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript/Next.js build. Latest documentation HEAD `7f9a1f3293ffc67579042a87b82cb2fb03ffba1f`; [CI run 39556090575](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556090575) passed.
- Reduced worker lease renewal interval from 25 to 5 records in both trade and order batches. Regression coverage proves a lost lease at a renewal boundary stops before persisting the next batch record; already-persisted fills remain idempotent evidence and the newer lease is preserved.
- The reconciliation UI now warns for both `WORKER_INTERRUPTED` and `LEASE_LOST` runs because their summary counters may be incomplete.
- Phase 2 lease-expiry audit closed: per-write transaction-level fencing and regression tests are implemented and verified by backend CI run 39561621808 (470 passed, 1 warning).
