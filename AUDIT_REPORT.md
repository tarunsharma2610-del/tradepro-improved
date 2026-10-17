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
| Live order placement | Incomplete / not enabled | Shared execution service still records PAPER orders; durable intent/outbox/audit/fill-identity storage and a read-only reconciliation worker exist, but no broker placement/cancel, no scheduling/API trigger and no accounting integration. Do not enable live orders. |
| Broker order status normalization and intent matching | Phase 2 helper layer implemented and tested | `backend/app/services/live_order_reconciliation.py` normalizes documented Upstox statuses and strictly matches a normalized observation to a candidate intent by connection scope, exact existing broker order ID or unique exact tag, and economic fields. Unknown/contradictory states, duplicate tags, cross-connection candidates and economic mismatches are never auto-linked. No network/database side effects. [Run 39050424898](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050424898): 255 passed, 1 warning. Not yet a reconciliation worker; no state persistence, fill ingestion or broker API calls. |
| Durable live-order records | Phase 1 partial; latest code CI passed | Additive Alembic revision `202610170002`, unique key + canonical request hash, ownership checks, transactionally persisted intent/outbox/initial event, and stable broker fill identity constraint. The latest code checkpoint [run 39049395091](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049395091) passed 247 tests, including the simultaneous same-key PostgreSQL test and new reconciliation-normalization tests. CI passed clean SQLite and PostgreSQL 16 migration upgrade → downgrade → re-upgrade. Backup-restored staging verification against an actual deployment database remains deferred because the project is not deployed. |
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


## Phase 1 — durable live-order records and repository safeguards — 2026-10-17

### Implemented in `tradepro-improved`
- User-approved design: `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`. The approval authorizes storage/repository safeguards only; it does not authorize enabling live trading.
- Added `backend/app/models/live_order_records.py` with `LiveOrderIntent`, `LiveOrderEvent`, `LiveOrderOutbox`, and `BrokerFillIdentity`. Records include scoped idempotency uniqueness, canonical request hash storage, broker order identity uniqueness, optimistic version/attempt counters, audit correlation metadata, and stable broker trade ID uniqueness.
- Added additive Alembic revision `backend/alembic/versions/202610170002_live_order_durability.py`, registered the models in `backend/app/models/__init__.py`, and added `backend/app/repositories/live_order_repository.py`.
- Repository checks that both portfolio and broker connection belong to the authenticated user. It computes SHA-256 from deterministic canonical JSON plus user/portfolio/connection scope; the client cannot supply a hash that disagrees with the snapshot. Same key + same canonical payload returns the original intent; same key + different payload raises `IdempotencyConflict`. Intent, initial event and outbox row commit together; unique-key races roll back and re-read the winner.
- Added `backend/tests/test_live_order_repository.py` for atomic record creation, idempotent reuse, payload conflict, ownership isolation, invalid/non-finite payload rejection, broker-fill uniqueness, audit ownership and transaction rollback atomicity.
- Latest code/test checkpoint `dd36b48a92057ad50618f6f9941f908832c9cea3` passed GitHub Actions [run 39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046): **215 passed, 1 warning**, with simultaneous PostgreSQL idempotency and SQLite/PostgreSQL reversible migration checks. The later workflow change passed migration upgrade → downgrade → re-upgrade on clean SQLite: [run 39043763339](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39043763339).
- Two intermediate commits failed CI during the canonical-hash API/test-fixture transition; the later checkpoint corrected the mismatch and is green. Those failures are retained in Actions history rather than hidden.
- No real broker order was submitted. No production database was migrated. This code does not yet implement a dispatch worker, live-order API, broker reconciliation or broker fill ingestion. CI contention coverage now exists for PostgreSQL; backup-restored staging verification and broader stress/failure testing remain open.

### Remaining Gate 1 work
- PostgreSQL CI now covers simultaneous same-key creation and reversible migrations; retain the exact run evidence above.
- Verify migration downgrade/upgrade and constraints against a backup-restored staging copy of the actual deployment database engine.
- Continue to preserve PAPER/live isolation; live submission remains disabled.


### Credential-field persistence guard — 2026-10-17
- `backend/app/repositories/live_order_repository.py` recursively checks order snapshots and audit `safe_details` for credential-like key names and rejects non-finite/non-JSON values before persistence.
- `backend/tests/test_live_order_repository.py` verifies nested access-token and authorization-header fields are rejected and no audit rows are added for rejected details.
- This is defense-in-depth only: callers must still redact secret values, and no live API or broker submission was added.


### Phase 2 normalization foundation — 2026-10-17
- Added pure order-status normalization and regression tests. Official contract references: [Upstox order book](https://upstox.com/developer/api-documentation/get-order-book/), [order details](https://upstox.com/developer/api-documentation/get-order-details/), [order history](https://upstox.com/developer/api-documentation/get-order-history/) and [order-status appendix](https://upstox.com/developer/api-documentation/appendix/order-status/).
- Exact test commit `b37452210bf07ad03acee1495e0627fae1378582`: [run 39049395091](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39049395091) — 247 passed, 1 warning, SQLite/PostgreSQL 16 reversible migrations passed.
- Next: strict local-intent matching and ambiguity quarantine. No broker reads, order submission/cancellation, or live reconciliation worker was added.

### Phase 2 strict intent matching — 2026-10-17
- Added ReconciliationIntentCandidate, IntentMatchResult and match_broker_order_to_intent() in backend/app/services/live_order_reconciliation.py. This remains a pure helper; no database or broker I/O.
- Matching is restricted to the supplied authenticated broker-connection scope. An already-known broker order ID takes precedence; otherwise an exact non-empty broker tag must identify exactly one local intent. In both cases, required instrument, side, type, quantity, product and applicable limit/trigger prices must match. Missing fields are mismatches, not wildcards.
- Duplicate tag candidates return AMBIGUOUS; economic mismatches return ECONOMIC_MISMATCH; unknown/contradictory observations return NEEDS_REVIEW; absent correlation returns NO_MATCH. The helper never treats a tag as broker-enforced idempotency and never makes a resubmission decision.
- Regression coverage includes exact matching, existing broker-order ID matching, wrong instrument/quantity, missing product, duplicate tags, cross-connection isolation and unknown statuses.
- Exact test commit e9b594ffc2e81c37e1b41c8c44947212d206f3e9 passed [GitHub Actions run 39050424898](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050424898): 255 passed, 1 warning, plus SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks.
- Remaining Phase 2 work: persist safe status transitions with audit/version checks, normalize and ingest broker trades idempotently, and test partial/out-of-order updates. No broker API reads, live order submissions, cancellations or production migrations were performed.


### Phase 2 — versioned reconciliation state persistence — 2026-10-17
- Added LiveOrderRepository.apply_reconciliation_transition() in backend/app/repositories/live_order_repository.py. It is a repository-only method: it does not call Upstox or trigger an order action.
- It uses an explicit state-transition allowlist, authenticated user ownership, expected-version and previous-state compare-and-set, broker order ID uniqueness, and one transaction for state/version/last-reconciled timestamp plus a BROKER_STATUS_RECONCILED audit event. Safe details reject credential-like keys. Repeated same-state observations at the current version are no-ops without duplicate audit events.
- Cancel/fill races are explicitly supported: CANCELLED may move to PARTIALLY_FILLED or FILLED when later broker trade evidence proves execution; terminal regressions such as FILLED → OPEN are rejected. RECONCILIATION_REQUIRED is frozen for manual resolution.
- Added tests for atomic state+event persistence, idempotent same-state observations, stale versions, terminal-state regression, cancel/fill race and secret-field rejection.
- Exact code checkpoint b3332b839b6f2c39bf2ae678e1aa62ac1f2a3409 passed [GitHub Actions run 39050941218](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39050941218): 261 passed, 1 warning; SQLite/PostgreSQL 16 migration checks passed.
- CI failures during this step were due to a malformed test import and then an undefined prior-state variable; both were corrected. Failed runs remain visible in Actions history. No broker API call, live order, production migration or fill ingestion occurred.
- Next: implement a pure, validated trade/fill normalizer and then a transactionally idempotent fill repository method keyed by (broker connection, broker trade ID).

### Phase 2 — validated broker trade identity persistence — 2026-10-17
- Added `normalize_upstox_trade()` in `backend/app/services/live_order_reconciliation.py`, a pure validator for documented per-order trade fields. It uses `trade_id` as the stable fill key, validates positive quantity/price and BUY/SELL, parses the documented exchange timestamp into UTC, and rejects malformed records.
- Added `LiveOrderRepository.record_broker_fill()` in `backend/app/repositories/live_order_repository.py`. It verifies broker connection ownership and any linked intent's user/connection scope; persists a single trade under the existing unique `(broker_connection_id, broker_trade_id)` constraint; and commits a `BROKER_FILL_RECORDED` event atomically when linked to an intent.
- Identical duplicate deliveries return the existing fill without another event. A duplicate trade ID with changed order/economic/time/metadata fields raises `LiveOrderVersionConflict`; credential-like keys in metadata are rejected. Cross-connection intent linking is rejected. This repository method performs no network calls and does not update positions, cash, P&L or the shared Order/Execution tables.
- Added normalization and repository tests for valid documented timestamps, malformed fields, idempotent replay, conflicting replay, account isolation and secret-field rejection. Exact code/test commit `001a6eed2bd7090e2c7a4d3a8f2f87e9d7fa62bc` passed [GitHub Actions run 39052203329](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052203329): 274 passed, 1 warning; SQLite/PostgreSQL 16 migration checks passed.
- Earlier fill-test run 39052095678 failed because the test tried to create two Upstox connections for one user, violating the existing unique `(user_id, broker)` constraint. The isolation test was corrected to use a second broker connection type; the later exact run passed.
- Official contract reference: [Upstox Get Order Trades](https://upstox.com/developer/api-documentation/get-trades-by-order/). No broker API read, real order, production migration, reconciliation worker, or live submission was performed.
- Remaining: validate a normalized fill against the matched intent's economic snapshot before persistence; aggregate partial fills and reconcile out-of-order status/fill evidence; then add a read-only broker reconciliation worker only after API contracts and failure handling are covered.


### Phase 2 — fill-to-intent economic validation — 2026-10-17
- Strengthened `record_broker_fill()` to require a linked intent already associated with the observed broker order ID. It compares instrument, side, order type and product against the immutable order snapshot; rejects missing/invalid requested quantity; enforces each fill and accumulated recorded quantity do not exceed the intent quantity; and enforces BUY limit/stop-limit fills are no higher than the limit, SELL fills no lower.
- Added tests for instrument mismatch, unlinked order ID, partial-fill aggregate overrun and both buy/sell limit-price violations. Exact code/test commit `b69939ece8edc47e1ae05f27c0d9e2144e87db04` passed [GitHub Actions run 39052939770](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052939770): 279 passed, 1 warning, with SQLite/PostgreSQL 16 migration checks.
- During development, CI caught test fixtures using fills priced above their own buy limit; fixtures were corrected to realistic limit-or-better fills. An intermediate run also caught tests not yet supplying the newly required product/order type fields. Final checkpoint is green.
- Remaining: reconcile out-of-order status vs fill events and actual broker-side trade list; ensure unmatched fills are quarantined/relinked safely; then build a read-only broker reconciliation worker. No network call, live order, production migration, or position/cash/P&L update was performed.


### Phase 2 — safe relinking of previously unmatched fills — 2026-10-17
- Added `LiveOrderRepository.link_existing_fill_to_intent()` for fills initially recorded without a local intent. It requires authenticated-user and broker-connection scope, exact already-linked broker order ID, instrument/side/product/order-type agreement, valid order quantity, limit-price protection and aggregate quantity ceilings.
- The link uses a conditional update that only changes an unlinked fill; repeat linking to the same intent is a no-op, while a different existing link or economic mismatch fails closed. The link and `BROKER_FILL_LINKED` audit event are committed atomically. Duplicate trade delivery without an intent can still be treated as an idempotent replay after later linking.
- Tests cover successful late linking, no duplicate audit on repeat link and rejection of an economic mismatch. Exact test commit `66802c2eae7adaddb8f1213c9c9a689e4190acaf` passed [run 39053352921](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053352921): 281 passed, 1 warning, with SQLite/PostgreSQL 16 migration checks.
- Still missing: real broker reads, worker retry/backoff, out-of-order status/fill reconciliation, fill revisions/sliced orders, and applying reconciled fills to shared order/execution/position/cash/P&L accounting. No real order or production migration occurred.


### Phase 2 — out-of-order status/fill evidence — 2026-10-17
- Added `resolve_order_state_with_fill_evidence()` and wired it into `LiveOrderRepository.apply_reconciliation_transition()` before idempotent same-state handling. Persisted fill identities now protect against stale active/cancel statuses overwriting execution evidence.
- Full persisted requested quantity resolves to `FILLED`; partial fill evidence with active statuses resolves to `PARTIALLY_FILLED`; partial fill plus cancellation resolves to `PARTIALLY_FILLED_CANCELLED`; contradictory partial-vs-filled/rejected evidence and invalid totals resolve to `RECONCILIATION_REQUIRED`.
- Audit events retain observed broker state, effective state, persisted fill quantity and resolution reason. Added parametrized normalizer/state tests and repository tests for stale OPEN, partial-fill cancellation and full-fill-vs-stale-cancel cases.
- Exact code/test checkpoint `59f562b62ef6af25ea3a5c6f15cab8a32d505da3` passed [GitHub Actions run 39056392873](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056392873): **294 passed, 1 warning**, plus SQLite/PostgreSQL 16 migration checks.
- One initial test run failed because two audit events shared the same timestamp precision and the test selected the wrong row; the test was corrected to select by resolved state, then the exact checkpoint passed. No broker API read, real order, production migration or accounting update occurred.
- Added [READ_ONLY_RECONCILIATION_WORKER_DESIGN.md](READ_ONLY_RECONCILIATION_WORKER_DESIGN.md), a design-only contract for the next read-only worker. It is not implemented yet.


### Phase 2 — narrow read-only Upstox client — 2026-10-17
- Added `backend/app/brokers/upstox/reconciliation_client.py` with fixed GET-only methods for order book, order details, order history by order ID or tag, and per-order trades. It intentionally does not expose place/modify/cancel methods.
- HTTP failures are categorized (401, 403, 429, 5xx, other client errors, timeout, network failure, non-JSON) without returning raw response bodies or exception text. A missing token fails before network access. Endpoint paths and parameters follow the official Upstox docs: [order book](https://upstox.com/developer/api-documentation/get-order-book/), [order history](https://upstox.com/developer/api-documentation/get-order-history/), [order details](https://upstox.com/developer/api-documentation/get-order-details/), [per-order trades](https://upstox.com/developer/api-documentation/get-trades-by-order/).
- Added mocked HTTP contract tests for paths/parameters, status classification, sanitization, timeout/network errors and absence of write methods. Exact test commit `10d9938d17c4c67649c5a4b9c305684ff8f36e52` passed [run 39056868434](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056868434): **309 passed, 1 warning**, plus SQLite/PostgreSQL 16 migration checks.
- This does not make any real Upstox request. No worker orchestration, token loading, retry/backoff, job lease, fill processing or accounting update has been implemented yet.


### Phase 2 — per-connection worker lease foundation — 2026-10-17
- Added `LiveReconciliationLease` and Alembic revision `202610170003` with a unique broker-connection key, lease token/expiry, generation, start/completion timestamps and sanitized error category.
- Added `LiveReconciliationLeaseRepository` with owner-scoped connection validation, bounded lease duration (1–3600 seconds), atomic claim/expiry reclaim, renewal restricted to the current unexpired token, and token-guarded completion.
- Added tests for second-worker exclusion, expiry/reclaim, stale owner rejection, valid completion, renewal/token/expiry handling, cross-user access and invalid lease durations.
- Exact test commit `4bbeb5f6ced81f66ae7720eb73557eebbc3409e9` passed [run 39057273255](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39057273255): **318 passed, 1 warning**, and SQLite/PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed.
- This is only lease storage/repository code; the worker is not implemented, no broker reads occurred, and no live order or accounting side effect is possible from this repository.


### Phase 2 — leased read-only reconciliation worker — 2026-10-17
- Implemented `backend/app/services/live_order_reconciliation_worker.py` (worker code commit [`4ee8427`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/4ee8427f890f7c31021e30f7b36177e2f3f227c)). The worker accepts only `UpstoxReadOnlyReconciliationClient`, checks user ownership, Upstox broker identity and connected state, gets the token through `BrokerCredentialsService`, claims/renews/completes a per-connection lease, reads order book and daily trades, normalizes observations, matches intents, and stores/link fills with existing repository checks.
- Retries are bounded and limited to read-only transient failures (429, 5xx, timeout/network). Token/permission errors stop the job. Malformed envelopes fail before any fill/status persistence. Summaries expose safe counts/error categories only.
- Added worker regressions for successful matching/fill linking, repeat-run dedupe, failed trade read atomicity, Retry-After, cross-user rejection, busy lease, missing token, unmatched fills, UNKNOWN-to-FILLED recovery, 403 without retry, bounded 503 retries and malformed envelope/data cases.
- PostgreSQL concurrency test confirms simultaneous lease claims allow only one worker token; exact test commit [`bf0c2b7`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/bf0c2b707aaa023a961f899502ed9f2ae4d265a4).
- Latest exact code/test checkpoint [`bffeefc`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/bffeefc7921fd96c8fbeab1b201eb3088e87f497) passed [GitHub Actions run 39058734080](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39058734080): **338 passed, 1 warning**; SQLite/PostgreSQL 16 reversible migration checks passed.
- Important limits: worker is not scheduled or exposed through an API route; current pass reads order book and daily trades, not historical-day pagination. There is no persistent run-summary/manual-review queue and no aggregation into Order/Execution/Position/cash/P&L. All worker transport tests are mocked; no real Upstox request, order action, production migration or accounting update occurred.


### Phase 2 — durable run summaries — 2026-10-17
- Added `LiveReconciliationRun` and Alembic revision `202610170004_reconciliation_runs.py`; `LiveReconciliationRunRepository` validates owner/connection scope, terminal status, safe error-code format and exactly the approved non-negative integer counters.
- Integrated the worker lifecycle: a `RUNNING` row is persisted after lease acquisition; success/conflict/failure/lease-loss ends in a terminal row with start/completion timestamps, sanitized error code and count-only summary. If run-row creation fails, the worker attempts to release its lease; if final summary persistence fails, the worker does not report clean success.
- Added worker tests for successful summary persistence and sanitized failure summary. Exact code commit [`0e69fb2`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/0e69fb2efea692f2f675604ef3312cb1954ecc39) passed [run 39059271937](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059271937): **340 passed, 1 warning**, and reversible SQLite/PostgreSQL 16 migration checks.
- Remaining: manual-review issue records/visibility, stale RUNNING-run recovery, crash-boundary tests, official history/pagination semantics and a separately approved read-only sandbox verification. No real broker reads, order actions, production migration or accounting changes occurred.


### Phase 2 — durable manual-review issue queue foundation — 2026-10-17
- Added `LiveReconciliationIssue`, migration `202610170005_reconciliation_issues.py`, and `LiveReconciliationIssueRepository`. Issue records are scoped to the authenticated user and broker connection, optionally tied to a run/intent, deduplicated by connection + fingerprint, and re-opened/incremented when the same issue recurs.
- Issue types are allowlisted. Safe details are credential-key-checked, finite JSON and limited to 2,048 characters; the worker records reason codes and normalized broker identifiers, not raw response records or exception strings.
- Worker now persists issues for invalid order/trade records, unmatched/ambiguous/economically mismatched orders, trade persistence conflicts, fill-link conflicts and status-transition conflicts. Tests cover deduplication of repeated unmatched-order issues and safe invalid-trade issue persistence.
- The initial issue-queue CI run [`39059726263`](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059726263) failed because malformed trade normalization was handled by the persistence-conflict branch before `trade` existed. The loop was split into normalization and persistence error handling. Exact fix commit [`71b5668`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/71b5668533f0461c12374319e496665cbda7e61c) passed [run 39059749652](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059749652): **342 passed, 1 warning**; SQLite/PostgreSQL 16 migration checks passed.
- Remaining: UI/API visibility and safe issue resolution, stale run recovery, crash-boundary tests, and historical-day pagination. No real broker reads/order actions, production migration or accounting update occurred.


### Phase 2 — authenticated read-only run/issue listing — 2026-10-17
- Added `GET /api/v1/reconciliation/runs` and `GET /api/v1/reconciliation/issues`, Pydantic response schemas and `LiveReconciliationQueryRepository`. Both endpoints require authentication and scope queries by the current user's ID; filters are optional and page size is bounded to 1–100.
- Tests cover unauthenticated access, user A versus user B isolation, filtering by another user's connection returning no records, status filter validation, maximum limit and no token leakage in issue responses.
- Exact code commit [`f65b4ba`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/f65b4ba20ce9a1dacfe40580d8042cd98f36c19f) passed [run 39060230705](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060230705): **345 passed, 1 warning**, and SQLite/PostgreSQL 16 upgrade/downgrade/re-upgrade checks.
- API is read-only; it cannot start a worker, resolve an issue, place/cancel orders or update portfolio accounting. Frontend UI, issue-resolution workflow, stale-run recovery, crash-boundary tests and historical trade pagination remain open.
