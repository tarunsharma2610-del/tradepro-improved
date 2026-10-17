# Tradepro Improved — Audit and Change Log

Audit target: `main` in this repository. The original `Tradepro` repository is read-only and has not been modified.

## Current findings

| Area / requirement | Status | Evidence / next action |
|---|---|---|
| FastAPI APIs, SQLAlchemy models/repositories | Existing; tests pass | Backend test suite passed on the current backend changes. Continue adding coverage as features change. |
| Paper market orders | Implemented, still needs operational validation | Uses Upstox LTP for simulated fills and records transaction costs and position/cash updates. Never fall back to a made-up price. |
| Order input validation | Improved | Service boundary rejects non-positive quantities, unsupported order types, missing/non-positive LIMIT prices, and a limit price attached to MARKET orders. API schema also rejects non-positive limit prices. |
| Quote price parsing | Improved | Rejects malformed, non-finite, zero, and negative LTP values before paper accounting. |
| Paper limit orders | Implemented; tests passed | Worker checks pending PAPER LIMIT orders during market passes, fills only when LTP crosses the limit, uses limit-or-better pricing, shares cost/cash/position accounting, and rejects delivery sells without holdings. Owners can cancel pending orders from the portfolio page. |
| Live order placement | Incomplete / not enabled | Shared execution service still records PAPER orders; broker order placement and execution reconciliation are not complete. Do not enable live orders. |
| Strategy activation | Fixed | Strategy evaluation returns HOLD for inactive strategies before contacting the broker; regression test added. |
| Daily risk controls | Portfolio-level manual controls implemented; strategy guard preserved | The portfolio settings UI/API supports manually configured daily realized-loss, estimated exposure, per-order value, open/pending position and daily-order limits. They are disabled by default, enforced on paper/strategy order paths, and calculated using the Asia/Kolkata day. Exposure remains a cost-basis estimate, not broker margin/mark-to-market risk. |
| Broker OAuth | Improved | State is signed, expires after 10 minutes, and is bound to user/broker/connection. A nonce digest and expiry are persisted and consumed by a conditional database update, so repeated/concurrent callback attempts cannot consume the same state twice. |
| OAuth schema migration | Added; deployment not yet verified | `202608220001_oauth_state_replay.py` adds the two nullable state columns. Apply and verify migrations in a backup-safe staging environment before deploying to an existing database. |
| Upstox instrument sync / streaming | Multi-segment sync and stream client implemented; live BOD verification passed | Snapshot-gated reconciliation and expiry deactivation are atomic. Live workflow run 39037390129 downloaded the real official BOD master and synced 123,930 active instruments into disposable in-memory SQLite. The V3 WebSocket client/API includes auth URL validation, reconnect, ping/pong, protobuf decode and stale-quote rejection; a live OAuth session is still unverified. |
| Frontend dashboard | Improved | Root page is now a dashboard with portfolio/cash summaries and links to portfolios, backtests, news, broker settings, and notifications. It no longer duplicates the broker settings page. |
| Frontend typecheck/build | Verified in CI | TypeScript check and Next.js production build passed. The `lint` script runs TypeScript checking because the project uses Next.js 16, where the old `next lint` command is not available. |
| Database migrations | CI migration check passed on SQLite; staging still required | The full Alembic chain, including the OAuth nonce migration, successfully upgraded a clean SQLite database in CI. Verify against a backup and staging copy of the actual deployment database before production rollout. |

## Changes committed

1. Added a service-level inactive-strategy guard and a regression test.
2. Added signed, expiring OAuth state validation bound to the requesting user and broker connection.
3. Added persisted, one-time OAuth nonce consumption with an atomic conditional update and Alembic migration.
4. Added order validation at both the API schema and execution-service boundary.
5. Hardened last-traded-price parsing so invalid prices cannot enter paper-accounting calculations.
6. Added a worker-driven paper LIMIT matcher with crossing rules, limit-or-better pricing, cash/holding checks, and shared accounting.
7. Added an authenticated cancel endpoint and portfolio UI action for pending paper orders, with ownership and status checks.
8. Replaced the duplicate root broker-settings page with an account dashboard.
9. Updated the frontend check command for Next.js 16.
11. Added an environment-controlled emergency kill switch for automated strategy entries, with a regression test proving it blocks entry without creating a position; exits remain available.
10. Added GitHub Actions workflows for backend tests and frontend typecheck/build.

## Verification

- **Backend:** Latest code CI passed — **203 tests passed, 1 warning**, including portfolio position-cap, daily-order-cap, daily-loss/India-midnight boundary, exact-instrument quote-key, WebSocket reconnect and authorization-URL checks, incomplete-snapshot reconciliation, and official-format V3 authorization coverage; clean SQLite Alembic migration verification passed. [View latest backend run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039645511).
- **Frontend:** TypeScript check and Next.js production build passed after portfolio risk and stream-control UI changes. [View frontend run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037642093).
- The tests use SQLite and mocked broker calls; they do not prove a live Upstox session or live market-order execution works.
- The OAuth migration passed a clean SQLite upgrade in CI but has not been applied to your production database.
- No live orders have been submitted.

## Remaining high-priority work

1. Add durable order idempotency/reconciliation before any live-trading implementation. The automated-entry kill switch is now present but must be included in deployment configuration and operational runbooks.
2. Validate the new portfolio-risk migration and manually configured limits against a backup/staging copy of the deployed database; decide whether mark-to-market/margin-aware risk is required.
3. Verify WebSocket streaming using a real authorized Upstox session and decide whether deployment needs shared stream state for multiple API workers.
4. Verify the Alembic migration path in staging and check current deployment configuration. The exchange holiday calendar remains outstanding.
5. Review remaining analytics and backtest behavior against the requested product requirements.


## Requirements-to-code/test gap map (reviewed 2026-10-17)

This is a repository-source review, not a live-broker certification. The current backend CI run for commit `a8faa2581a05778df0f7d30a7a0fb3f0d4e6164a` completed successfully (workflow run [39036087413](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39036087413)). That run was triggered by documentation changes; it confirms the existing test workflow is green, not that untested live-trading features work.

| Requirement | Source evidence reviewed | Status | Next safe action |
|---|---|---|---|
| Paper orders must not submit real orders | `backend/app/services/execution_service.py` constructs orders with `trading_mode="PAPER"`; `backend/app/brokers/base.py` defines broker placement separately; `test_paper_market_order_never_calls_broker_live_order_endpoint` | Regression test present and passing in backend CI | Preserve this boundary; never wire paper execution to adapter `place_order` |
| Live order lifecycle and reconciliation | `ExecutionService.place_order` simulates accounting; adapter has `place_order`, `get_order_status`, `get_order_book`, `get_positions`, but no live orchestration service was found in reviewed files | Not implemented / not enabled | Design a separate live execution service only after idempotency, risk and broker rules are specified; no real orders in tests |
| Duplicate submission protection | `Order` model has no visible broker idempotency key in reviewed fields; safeguards document calls this out | Gap | Define unique client intent key + persisted submission state and retry semantics before live execution |
| Strategy-specific daily loss | `backend/app/services/risk_engine.py` checks strategy realized loss; portfolio risk service checks portfolio realized loss | Strategy guard preserved; portfolio daily limit uses Asia/Kolkata calendar day with midnight-boundary regression test | Consider unrealized P&L/margin-aware limits separately; do not imply realized-only controls are full account risk |
| Portfolio-wide loss / exposure / order-frequency caps | `backend/app/services/portfolio_risk_service.py`, Portfolio risk fields, owner-scoped settings API and portfolio UI | Implemented for paper/strategy order paths; configurable and disabled by default | Keep threshold, India-session boundary and concurrency coverage current. These controls use realized daily P&L and cost-basis exposure; they are not a broker-margin or mark-to-market risk model. |
| Emergency stop for automated entries | `backend/app/core/config.py` exposes `AUTOMATED_ENTRIES_ENABLED`; `strategy_execution_service.py` blocks entries while preserving exits | Implemented for automated strategy entries, not manual paper orders or live orders | Add runbook/monitoring; do not describe as a global account-wide live kill switch |
| Upstox instrument master | InstrumentService, InstrumentRepository batch upsert/reconciliation and live verification script | Real official master download and disposable SQLite sync passed | Live verification run [39037390129](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037390129) imported 123,930 active instruments across supported segments. Missing-key and expired derivative deactivation is snapshot-gated and atomic; a regression test confirms a syntactically valid snapshot missing required segments cannot alter the existing catalog. This did not write to production. See [official Upstox Instruments docs](https://upstox.com/developer/api-documentation/instruments/).
| Upstox WebSocket market data | V3 streamer/manager, authenticated /market-data/stream routes, official V3 protobuf schema/decoder; ExecutionService prefers fresh stream quotes | Implemented with mocked transport/data tests; live account session unverified | One-time authorize URL, TLS verification, binary subscription, protobuf decoding, ping/pong, exponential reconnect and stale-data rejection are implemented. Fresh stream ticks are preferred before REST fallback. The stream manager is process-local; multi-worker deployment needs shared state. See [V3 stream docs](https://upstox.com/developer/api-documentation/v3/get-market-data-feed/) and [authorize docs](https://upstox.com/developer/api-documentation/get-market-data-feed-authorize-v3/).
| OAuth replay prevention | Audit documents persisted nonce digest, expiry and conditional consumption; migration file exists | CI clean-SQLite tested; production/staging not verified | Backup and validate upgrade against a staging copy of the actual DB before deployment |
| Production migration safety | Existing clean SQLite migration CI is not equivalent to the deployed DB engine/data | Unverified | Record DB engine/version, backup, staging upgrade and rollback plan before deployment |
| Frontend checks | Portfolio risk settings and live stream controls in portfolio UI | TypeScript and Next.js production build passed in run 39037642093 | Keep CI required for future frontend changes |

### Review sequence / acceptance gates

1. Paper/live adapter-isolation regression coverage is implemented and passing. Keep the service boundary intact.
2. Portfolio-wide configurable controls are implemented for daily realized loss, estimated exposure, per-order value, open/pending positions and daily order count. Keep strengthening threshold, boundary and concurrency coverage; these controls do not yet account for unrealized P&L or broker margin.
3. Instrument sync and streaming are implemented with mocked tests; the real BOD master sync was validated only in disposable SQLite, while an authenticated live WebSocket session and production topology remain unverified.
4. Treat idempotent live order submission, broker reconciliation, account-level emergency stop, static-IP/2FA/session requirements, authorization and applicable compliance review as mandatory blockers before any real-order feature.
5. Run full backend/frontend CI after code changes; do not call CI triggered by docs a code regression test.

### Scope boundary

This workstream added portfolio risk settings/enforcement, snapshot-gated expiry/delisting reconciliation, a V3 WebSocket client/API and real upstream master verification against disposable SQLite. Latest verified backend CI passed 203 tests and clean SQLite migration verification; frontend typecheck/build passed for the stream-control UI. No live orders were submitted. No production database sync or production/staging migration was run. Live authenticated WebSocket behavior still requires account-level verification. Live trading remains unimplemented and must remain disabled.


### Latest verification checkpoint — 2026-10-17

- Latest backend workflow after documentation changes: [39039714203](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39039714203) — **203 passed, 1 warning**. Clean SQLite Alembic upgrade completed through `202610170001`; this is not proof of safe migration on the deployed database engine/data.
- Regression tests on `main` cover the portfolio daily-order cap, rejection of incomplete instrument snapshots without catalog mutation, WebSocket silence reconnect, unsafe authorization URL rejection, and valid official-format V3 authorization URL/headers.
- Real upstream instrument master was downloaded and synced to disposable in-memory SQLite with **123,930 active instruments**: [workflow 39037390129](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037390129). Production database was not touched.
- Frontend TypeScript and production build passed for stream-control UI: [workflow 39037642093](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39037642093).
- Remaining release blockers: authenticated real-session WebSocket test; multi-worker/shared stream state; backup-safe staging migration against the actual deployment DB; and idempotent live order submission plus broker reconciliation and emergency stop. No live orders were submitted. Keep live trading disabled.
- Next safe step: document idempotency and reconciliation design against the existing adapter/order model/audit trail before implementing live order submission.


## Live-order idempotency/reconciliation design review — 2026-10-17

### Source review findings
- `backend/app/models/order.py` stores local order intent/status but has no durable client idempotency key, broker connection/order identity, submission-attempt ledger or reconciliation state.
- `backend/app/models/execution.py` can represent multiple executions conceptually but has no broker trade ID uniqueness guard to deduplicate imported fills.
- `backend/app/repositories/order_repository.py` performs ordinary create/save commits; it does not implement a transactional outbox or an atomic idempotency claim.
- `backend/app/services/execution_service.py` constructs `trading_mode="PAPER"` orders. Keep that behavior isolated; do not connect this method directly to live broker submission.
- `backend/app/brokers/base.py` and `backend/app/brokers/upstox/adapter.py` expose order placement, status, order-book, positions and holdings calls, but adapter methods alone do not provide durable idempotency, uncertain-submit recovery, fill deduplication or reconciliation orchestration.

### Design deliverable
Added [`LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`](LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md) (commit `f74386a99722d761bcd23848f442cb754dd0e231`). It defines additive intent/event/outbox/fill identity records; key + canonical request hash semantics; unknown-submit handling and no blind retries; broker history/order-book/trade reconciliation; partial-fill and cancellation-race handling; risk/kill-switch rechecks; migration and deployment gates; implementation phases; and a regression-test matrix. Related architecture/safety/README documentation links this design.

### Official API contract notes
Reviewed official Upstox Place Order V2/V3, Order History, Order Book, Order Details and Order Trades pages. Upstox tags support correlation and history lookup; this design does **not** assume a tag is broker-enforced idempotency. External exactly-once submission cannot be promised by a local database alone; ambiguous network outcomes must be reconciled before any further submission.

### Status and verification
- This step changed documentation only. No application code or database schema changed, no migration ran and no real broker session/order was used.
- No tests were rerun for the documentation-only design step. Existing historical CI results above remain historical evidence, not validation of live trading.
- Live order placement/reconciliation remains **not implemented and not enabled**. Required future work: schema/repository and concurrency tests; reconciliation-only service; sandbox-only outbox submission with crash/timeout drills; fill dedupe; staging restore/migration verification; operational alerts/runbook; broker/account and compliance checks; explicit authorization.
- Next action: cross-document consistency review and CI confirmation for this documentation commit series. Do not start live-order code until the design review gate is accepted.


## Roadmap and commit-integrity review — 2026-10-17
- Added [ROADMAP.md](ROADMAP.md) to consolidate the verified status, phased implementation plan and release gates across market-data, risk, live-order safety and deployment verification.
- Verified the prior documentation commit series exists on default branch `main`; latest prior progress commit `3263eda9d1329d17069dd4140162602631639a0b` has successful CI: [run 39040715054](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39040715054).
- The new roadmap commit is `3024aed473f28409bd075ec7e764576890c4ecfa`; its own CI must be checked separately before reporting it green.
- No application code or schema was changed by the roadmap addition. No tests were run locally, no production migration was run, and no real broker order was submitted.
