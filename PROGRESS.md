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
- `backend/app/repositories/live_order_repository.py`: validates authenticated-user ownership of both portfolio and broker connection; derives SHA-256 from deterministic canonical JSON plus user/portfolio/connection scope; same key + same payload reuses the existing intent; same key + different payload raises `IdempotencyConflict`; persists intent, initial audit event and outbox row in one transaction; handles a unique-key race by rollback and winner lookup.
- `backend/tests/test_live_order_repository.py`: covers transactionally created records, duplicate reuse, payload conflict, ownership isolation, invalid key/non-finite payload rejection, duplicate broker-fill identity, audit ownership and rollback atomicity.
- Updated `ROADMAP.md`, `AUDIT_REPORT.md`, `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`, `ARCHITECTURE.md`, `LIVE_TRADING_SAFEGUARDS.md`, `README.md` and `PROJECT_INSTRUCTIONS.md` to record approval, current implementation boundary and evidence.

### Verification
- Latest application-code/test commit: `54671fd57f21e93938c4c265d29266e50b5f350c`.
- Exact-commit GitHub Actions: [run 39043386194](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39043386194) — **211 tests passed, 1 warning**; clean SQLite `alembic upgrade head` passed.
- The intermediate canonical-hash API/test mismatch caused two red runs (39043143640 and 39043156888); the fixture was corrected and the later exact code checkpoint passed. Failures are not concealed.
- Documentation update commits: roadmap `4c180c79609ea70d69202a675fc488e9bcd8cb50`; audit `2f0d257d60f433f95b1fc3a748692ca9ced2eac9`; README `2a66095026bd3cf589e16a94af1133f068bdc04f`; design `beabddea4392e5579c10b41502b7075c7cedbe1c`; architecture `d8f8fb9be71edc7f29fed9d31579a63654a7aea4`; safeguards `c1bc5babe0e1ba700fbb048b213d37c7f2d01f39`; instructions `a23e84155f3cdd8faea135cddb4906cf03a4723f`. Their CI verification is being checked independently; the final progress commit must also be checked.
- No broker order POST, cancellation, live reconciliation, production migration or real-money test was performed.

### Remaining Phase 1 gates
- Add an explicit concurrent duplicate-key race test using independent database sessions/transactions.
- Verify migration downgrade/upgrade and constraints on a backup-restored staging copy of the actual deployment database engine.
- Review append-only audit enforcement and safe-details redaction policy before any API exposes these records.
- No live-order API, dispatcher worker or reconciliation service is part of this phase. Keep live trading disabled.

**Next action:** check CI for the documentation commits and this progress update; then continue with the concurrent unique-key test and staging-engine migration review.
