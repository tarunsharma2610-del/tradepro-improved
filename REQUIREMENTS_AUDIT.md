## Phase 3 verified checkpoint — 21 October 2026

- **Verified code/test HEAD:** `b64ba0494219dc9b5b05ba55c901d6a2e7fecc5a`; exact-head [Backend CI run 39605871413](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39605871413) passed **482 tests, 1 warning in 26.31s**, the broker-write boundary guard, and SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks.
- Live-fill accounting rejects a single staged fill above the local order quantity, cumulative fills across broker child orders above that quantity, and fills mapped to a local order marked `REJECTED`. A `CANCELLED` order can still account a broker-confirmed partial fill without changing the local status.
- Exchange-time ordering is fail-closed: a later trade cannot be promoted while an earlier staged trade for the same broker connection/instrument remains unaccounted; an earlier trade arriving after a later execution was accounted is blocked for manual review. Same-time fills with different sides or prices are treated as ambiguous and rejected. Broker trade ingestion and promotion share a connection-row lock to serialize this chronology check against normal staging.
- Regression coverage includes changed-fill and changed-charge replay rejection, ambiguous timestamps, out-of-order staged/late-arriving fills, PostgreSQL cross-child overfill concurrency, terminal order behavior, rollback, and paper-accounting isolation.
- **Phase 3 is in progress, not complete.** Continue reviewing the explicit coordinator/identity design, charge provenance, replay conflicts, partial-fill, out-of-order and crash/restart acceptance criteria before phase closure.
- Keep live broker submission, automatic accounting promotion, and automatic scheduling disabled. The original `Tradepro` repository remains untouched. Phase 2 remains closed.
- This is the current checkpoint summary. Older checkpoint notes below are retained as historical audit trail and must not be treated as newer than this entry.

---

## Current verified checkpoint — 21 October 2026

- **Last verified code/test checkpoint:** `00ee9bad0e962d92244da6f63da1e46ba058ad6f`; exact-head backend CI [run 39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386) passed **472 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 reversible migration checks.
- **Last verified documentation checkpoint before this status refresh:** `391dfefc9580abf9537ee659877578033baae4fd`; exact-head backend CI [run 39568264419](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39568264419) passed.
- The Phase 2 audit covers the dependency/port matrix, broker-fill workflow boundary, idempotency and rollback, reconciliation crash recovery, transaction-level lease fencing, slow persistence, 20 concurrent expiry-boundary renewal/reclaim races, and official Upstox current-day API semantics.
- Official Upstox V2 [order-book](https://upstox.com/developer/api-documentation/get-order-book/) and [get-trades-for-day](https://upstox.com/developer/api-documentation/get-trade-history/) endpoints are current-day endpoints without documented pagination parameters. Historical trades use a separate [paginated API](https://upstox.com/developer/api-documentation/get-historical-trades/); it is not wired into the Phase 2 worker.
- **Phase 2 technical checklist is complete.** Before any Phase 3 work, require a passing exact-head CI run for the then-current `main` and explicit user approval; never infer a later commit is green from an earlier run.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled. The original `Tradepro` repository remains untouched.

---

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

<!-- Authoritative checkpoint audit: 2026-10-21; supersedes older status notes below. -->
## Superseding verification note — 21 October 2026

- Latest code/test commit: [e56bf4c66f74b875a3ba8fe388138a9d688dd1e2](https://github.com/tarunsharma2610-del/tradepro-improved/commit/e56bf4c66f74b875a3ba8fe388138a9d688dd1e2), adding failed-commit rollback coverage for live-fill accounting.
- Exact-head CI for this commit is verified: [run 39564568154](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39564568154) passed 471 tests, 1 warning, the broker-write boundary guard and SQLite/PostgreSQL 16 reversible migrations. The subsequent documentation HEAD `adb69aeb05b70ba4fa9095fc73d9dea033d31eec` passed [run 39565251793](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39565251793).
- Phase 2 workflow boundary: resolved by keeping BrokerFillIdentity and manual BrokerTradeRecord independent. No bridge or dual-write is approved. SAFETY_BRANCH_PORT_MATRIX.md is the dependency map; live account-safety endpoints, charge adjustments, preflight, central broker-write service and actual live submission are not silently treated as Phase 2-complete.
- Historical checkpoint note: Phase 2 engineering checks and the cited code/test CI were verified on their respective commits. See the top checkpoint for current-head documentation CI and Phase 2 closure status.

## Current verified checkpoint — 21 October 2026

- The reconciliation crash-recovery/lease-fencing sub-slice is complete; backend CI run 39561621808 passed 470 tests, 1 warning, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles.
- The defined Phase 2 dependency/port matrix and workflow-boundary decision are complete; the code/test checkpoint and current documentation HEAD have passing exact-head backend CI (runs 39564568154 and 39566324985). Phase 3 accounting integration and Phase 4 live-trading release gates remain blocked by design while final historical-status consistency review is completed.
- The latest documentation HEAD `0bd502f83118799d5564e8fd5724d01e8dc975af` passed exact-head backend CI [run 39566324985](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39566324985). Any subsequent commit requires its own exact-head CI verification.
- Live broker submission, automatic accounting promotion and automatic scheduling remain disabled.

- Current `main` HEAD is the latest documentation synchronization commit; the verified code/test checkpoint is `fe07b77b193da1232787384efb38cb589e0d71b6`. Check the live repository HEAD and Actions page for the newest documentation-only commit and its CI result.
- Latest exact-HEAD backend CI: [run 39562094642](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39562094642) passed **470 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles.
- Phase 2 slow-persistence/high-volume lease-expiry audit is complete. The PostgreSQL slow-persistence lock test and new 20-iteration concurrent expiry-boundary renewal/reclaim regression passed exact-head CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386): 472 tests, 1 warning; source guard and SQLite/PostgreSQL 16 migration cycles passed.
- Latest frontend CI remains [run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474), passing TypeScript and Next.js build; no frontend code changed in this checkpoint.
- Documentation files were synchronized in commit `f369839f20efed60f62abdbc329fe6d4454faeaa`. Historical references to earlier commits and counts below are historical records, not current status.
- Phase 3 is not started. External-repository borrowing remains paused; live broker submission, automatic accounting promotion, and automatic scheduling remain disabled.


- **Repository/branch:** `tarunsharma2610-del/tradepro-improved`, `main`. The original `tarunsharma2610-del/Tradepro` repository is a protected baseline and must remain untouched.
- **Latest repository HEAD before this audit update:** `a297b1a356c133aaca0ed10079eb5226c03b747b` — documentation-only commit `docs: synchronize Phase 2 status with passing CI evidence`.
- **Latest code/test commit:** `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`. Recorded exact-commit backend CI run [39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles. Frontend run [39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript and Next.js build.
- **Previously verified documentation CI:** commit `6407c5a05865c1be0ef673d3bb5e71c0231ef8da`, run [39556816828](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556816828), backend job completed successfully. The later documentation-only commit `a297b1a356c133aaca0ed10079eb5226c03b747b` was found on `main`; CI for that exact HEAD was not independently established before this audit update. Do not infer exact-head CI success from an earlier commit.
- **Phase 2 checkpoint verified in project records:** atomic run/lease finalization; stale-owner protection; cancellation and interrupted-run recovery; inconsistent lease token/expiry rejection; five-record renewal boundary; and incomplete-summary warnings for `WORKER_INTERRUPTED` and `LEASE_LOST`.
- **Historical audit disposition — superseded:** the slow-persistence and high-volume lease-expiry/renewal race audit is now complete. Existing transaction-level fencing plus the two PostgreSQL regression tests cover the demonstrated row-lock and stale-owner behavior; no production-code change was required for this audit.
- **Safety constraints remain:** no real broker orders in tests; live broker submission, automatic accounting promotion, and automatic scheduling remain disabled; keep `BrokerFillIdentity` separate from `BrokerTradeRecord`; do not wholesale-merge the divergent safety branch.
- Older checkpoint entries below are retained as history, not current instructions. This top section is the authoritative current state. After this documentation commit, verify CI for its exact HEAD before treating the checkpoint audit as fully closed.

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

## Scope and inventory
The recursive Git tree inventory now contains 219 files, including backend application code/tests, frontend routes/components, migrations, configuration, documentation and deployment files. The second-pass review covered the primary API routes, models/repositories, trading/accounting/strategy/risk services, Upstox adapter, auth/OAuth, middleware, frontend workflows, migrations, CI and deployment configuration. The full automated backend suite and CI migration check were run; this remains a static review, not a production end-to-end test.

## Requirement matrix

Status meanings: **Complete in current scope** means existing implementation and relevant automated coverage were found; **Partial** means useful code exists but the complete requirement is not met; **Missing** means no implementation was found; **Verify in staging** means static inspection/CI cannot prove operational behavior.

| Requirement | Status | Existing evidence / finding | Change decision |
|---|---|---|---|
| Preserve separate improved repository | Complete | `tradepro-improved` is separate; changes are confined to `safety/fail-closed-trading-mode`. | Keep original `Tradepro` untouched. |
| Backend API and user/portfolio isolation | Complete in tested scope | Authenticated routes and ownership checks; tests cover cross-user portfolio, strategy, backtest and order access. | Retain; add regressions if shared paths change. |
| Password/MFA/session security | Partial | Argon2id password hashes, JWT access/refresh tokens, TOTP MFA, httpOnly cookie use and rate limits exist. Refresh-token revocation/session inventory is not present in the reviewed model. | Do not rewrite; review only if a requirement or defect demands it. |
| Upstox OAuth and credential storage | Mostly complete; staging verification required | Credentials are encrypted at rest and masked in responses; OAuth state is signed, bound to user/connection, expires, and uses a one-time DB nonce. Access-token expiry is checked. Real broker login was not tested here. | Preserve existing implementation; keep OAuth tests. |
| Real quotes and historical candles | Partial | Upstox LTP and historical candle methods exist; paper orders reject absent/invalid quotes instead of inventing prices. WebSocket streaming is a stub. | Keep existing quote/candle path; implement streaming only with verified API docs and tests. |
| Instrument master | Partial | Official Upstox docs list the complete JSON BOD instrument file and fields including segment, instrument type, lot size and tick size. The current importer still filters to `NSE_EQ` only and does not map derivative contract fields. The tick-size unit/normalization is not yet verified, so tick-increment enforcement is not safe yet. The adapter's separate `sync_instruments` method remains a stub. Seed list contains ten equities. | Expand only after implementing and testing full field mapping, tick-size units, expiries/strikes, contract quantities and supported-segment validation. |
| Paper order placement and accounting | Implemented with operational limitations | Shared `ExecutionService` uses real quotes for simulated market fills; pending LIMIT matching and cancellation exist. Paper fill writes now update order status, aggregate position, cash and execution in one transaction, with a regression test proving rollback on execution-persistence failure. Strategy-owned allocation is separately tracked. Derivatives are rejected until instrument sizing and risk accounting are verified. | Preserve paper/live separation; add tests for any accounting changes and never route paper orders to the broker. |
| Paper/live isolation | Partial; safety guard now added on branch | Baseline service always writes `trading_mode="PAPER"`; `TRADING_MODE` previously only warned at startup. Branch adds a fail-closed check in `ExecutionService.place_order` and a regression test. CI passed on PR branch. This is not live execution. | Keep guard while no separate live execution service exists; review its effect on PAPER orders if environment is set to LIVE. |
| Atomic live-fill accounting | Partial; unregistered promotion coordinator tested | Coordinator validates a staged trade, obtains an explicit Upstox `APPROVED_ESTIMATE`, revalidates identity after async I/O, then writes connection-scoped `LivePosition` + `Execution` atomically. Replay reuses persisted provenance; unsupported DP allocation fails closed. Actual per-trade charges remain unverified; no route/worker wiring. | Audit child-order cumulative-fill invariants and contract-note reconciliation; verify PostgreSQL/staging before any route/worker wiring. |\n| Live order lifecycle | Partial; read-only status check foundation added | Adapter has broker `place_order`, `get_order_status`, `get_order_book`, `get_positions`, and `get_holdings` methods. The safety branch now stores optional broker order metadata and adds a read-only service to check a known LIVE order's broker status after ownership/session/order-ID validation. It validates any returned broker order ID and records the raw status without changing local FILLED/CANCELLED state or cash/positions. An authenticated read-only broker-status endpoint is now exposed for orders that already have a stored broker ID. Live placement is still absent; no automatic reconciliation of partial fills, cancellation, timeouts or restart recovery exists. | Build and review a separate live lifecycle; only map statuses and account for fills after verified payload contracts and reconciliation tests. Do not replace paper execution. |
| Duplicate-order prevention/idempotency | Partial | Optional client idempotency key and a per-portfolio database uniqueness constraint protect matching API retries. Strategy entries also check their strategy-owned position under the portfolio lock, preventing a second fill when overlapping evaluations race. The frontend and strategy scheduler do not yet consistently supply idempotency keys, and broker-side idempotency/unknown-timeout reconciliation are missing. | Keep DB constraints and fill guards; wire stable retry keys into callers and implement broker correlation/reconciliation before live execution. |
| Risk controls | Partial | Strategy-level realized daily-loss checks and an automated-entry kill switch exist. The safety branch adds a portfolio-wide realized daily-loss guard for automated strategy entries (default 2%) and a single-order notional cap for paper orders (default 25% of starting virtual capital), both configurable. The order cap uses price × quantity as represented by current paper accounting; derivative multipliers/lot sizes are not yet verified. Neither is a complete live risk system. Portfolio-wide exposure and a broker-error circuit breaker remain missing. | Keep controls server-side; add exposure/circuit-breaker and verify derivative contract sizing before live use. |
| Strategy engine/scheduler | Partial | Five-indicator scoring, trailing-stop logic, worker cadence and isolated per-strategy sessions exist. New strategy-position allocations stop a strategy from closing a manual/other-strategy position and calculate strategy P&L on its own entry basis. The fill path also rejects duplicate entries for a strategy that already owns a position. Exchange holiday handling and stable evaluation-level idempotency remain incomplete. | Preserve engine; retain strategy-allocation regression tests and add calendar/evaluation-key safeguards as needed. |
| Orders/P&L/costs/analytics/backtesting | Partial to complete by feature | Decimal-based cost calculation, position math, backtests, realized analytics and tests exist. Live broker-confirmed fills/unrealized P&L are not supported because live execution is absent. Cost rates and live-market assumptions require periodic verification. | Retain tested paper/backtest logic; do not imply live-accounting parity. |
| Frontend workflows | Partial | Dashboard, portfolios, orders, strategies, backtests, analytics, broker settings, notifications and admin pages exist. Dashboard explicitly says live trading is not enabled; no live mode workflow/confirmation UI exists. | Do not add duplicate pages; add UI only after backend live workflow is safe. |
| Audit logs and operational visibility | Partial | Audit log writes exist for important auth/broker/settings events; no complete order lifecycle audit/reconciliation dashboard or circuit-breaker status exists. | Extend existing logging when execution lifecycle is implemented. |
| Database migrations | Existing chain; staging verification required | Six original revisions plus three forward safety-branch revisions exist. The latest migration adds strategy-owned position tracking and backfills legacy strategy executions/positions. CI checks a clean SQLite upgrade; a real existing production database has not been upgraded in staging. | Keep migrations forward-only, test clean upgrades and data backfills, and back up/verify staging before production. |
| Deployment and CI | Partial | GitHub Actions cover backend tests/migrations and frontend typecheck/build. Compose deploys Postgres, Redis, backend, worker, frontend and Nginx. Nginx is HTTP-only until TLS setup; production configuration still needs environment-specific verification. | Keep CI; validate deployment and TLS before OAuth/live use. |

## Baseline and verification evidence
- Main branch's existing audit records a previous backend run of 167 passing tests and a successful frontend typecheck/build. These are historical results.
- Latest verified backend CI: **188 tests passed, 1 warning**, and the full Alembic chain upgraded a clean SQLite database: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39030941704. Latest frontend TypeScript/build checks passed: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39030941702. The migration's legacy-data backfill path is reviewed in code but not yet exercised against a copy of a populated production database.
- This backend workflow result does not prove a real Upstox session, market feed, broker order, production database, TLS configuration, or live-trading behavior.
- No real broker orders were placed.

## Prioritized change plan
1. **Next:** audit `BrokerOrder`, execution/fill models, migrations and reconciliation services; implement the smallest additive, transaction-safe broker trade/fill idempotency and partial-fill aggregation foundation.
2. Test repeated trade IDs, concurrent/replayed intake, quantity aggregation and rollback with mocked broker responses. Never double-count or mutate PAPER accounting.
3. Keep the preflight coordinator unregistered from routes/workers and live submission disabled.
4. Complete broker-confirmed order status/fill/cancel reconciliation, account-level kill switch, broker-error circuit breaker and operational recovery.
5. Verify derivative mapping, tick/lot sizes and margin treatment before enabling non-equity segments.
6. Run backend tests, SQLite/PostgreSQL migration checks, frontend typecheck/build and staging verification. Keep live trading disabled until all release gates and explicit review are complete.

## Retained unchanged after review
- Existing paper order/accounting engine, order and position models, cost engine, strategy scoring, backtest engine, notification integrations, OAuth/credential encryption, existing pages, and current migration history.
- Existing adapter methods for broker order/status/book/positions/holdings are to be reused where correct, not duplicated.
- The original `Tradepro` repository and its `main` branch remain untouched.

## Release gate
Live trading is **NOT READY**. No live order placement should be enabled until current official API contracts, durable idempotency, risk limits, broker-confirmed fills, cancellation/timeout/restart reconciliation, credential/session controls, kill switch, audit trail, tests, deployment controls, and required broker/compliance authorization have been verified.


## Verification update — 17 October 2026

- The strategy-position migration backfill is no longer only statically reviewed: `backend/tests/test_strategy_position_migration.py` creates a populated database at revision `202610170002`, upgrades to head and verifies closed/open allocations, per-execution realized P&L, legacy over-sell behavior and preservation of aggregate portfolio accounting.
- CI on commit `1fe681246cb88a9505302a1763128c51ab72802d`: [backend 190 passed, 1 warning, migration upgrade passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39031526388); [frontend TypeScript/build passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39031526360).
- Remaining unverified items are populated PostgreSQL/staging migration execution, production rollout and all live broker order lifecycle behavior.


## Idempotency verification update — 17 October 2026

- The manual order UI's existing retry-key behavior was inspected and retained unchanged: it reuses the same key after a failed response and clears it after a successful response or when the user changes order parameters.
- Strategy order submissions now use deterministic keys for strategy + side + latest candle timestamp. Orders are not submitted automatically when that timestamp is missing. Existing-key validation now includes strategy/manual execution reason and strategy ID.
- Regression tests cover same-candle retry, invalid candle timestamp and cross-scope key reuse. Latest CI: [backend 193 passed, 1 warning and migration upgrade passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032153163); [frontend checks passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032153157).
- The complete live order lifecycle is still not implemented; this idempotency is a paper/strategy safeguard, not broker-side idempotency.


## Upstox order endpoint audit — 17 October 2026

- Current official Upstox documentation marks the legacy V2 place-order endpoint as deprecated and documents Place Order V3 at `https://api-hft.upstox.com/v3/order/place`; the V3 response uses `data.order_ids`. See [Place Order V3](https://upstox.com/developer/api-documentation/v3/place-order/) and the legacy [Place Order API](https://upstox.com/developer/api-documentation/place-order/).
- Updated the isolated adapter and mocked test only. The method is still not wired to `ExecutionService`; live trading remains disabled.
- Current official docs also provide V3 modify and cancel endpoints. The base adapter interface does not yet expose either operation; this is a verified gap for the next task. See [Modify Order V3](https://upstox.com/developer/api-documentation/v3/modify-order/) and [Cancel Order V3](https://upstox.com/developer/api-documentation/v3/cancel-order/).
- Latest CI for endpoint correction: [backend 193 passed, 1 warning, migration passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032413141); [frontend passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032413150).


## Upstox V3 modify/cancel adapter update — 17 October 2026

- Added `modify_order` and `cancel_order` to the adapter interface and Upstox V3 implementation. The official endpoints are documented at [Modify Order V3](https://upstox.com/developer/api-documentation/v3/modify-order/) and [Cancel Order V3](https://upstox.com/developer/api-documentation/v3/cancel-order/).
- Mocked regression tests verify the V3 routes and arguments. These adapter methods are not wired to the app's order management, do not submit orders during tests, and do not mutate local accounting.
- Latest CI: [backend 195 passed, 1 warning and migration upgrade passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032570839); [frontend checks passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032570823).
- Remaining: separate live order lifecycle, broker-side idempotency, response handling for one-or-many order IDs, confirmed modify/cancel state, partial-fill and restart reconciliation, and live risk controls.


## Live execution readiness audit — 17 October 2026

- Safety guard: `ExecutionService.place_order` rejects LIVE/unknown mode before order creation. Keep it until a separate service is independently reviewed.
- Authentication: OAuth state has signature, expiry, user/broker/connection binding and single-use nonce; credentials/tokens are encrypted; expired access tokens return unavailable. Refresh-token automation is not present.
- Risk/instruments: strategy and automated-entry portfolio loss guards and a paper notional cap exist. They do not amount to a live/manual pre-trade risk system. Instrument validation is deliberately equity-only; derivative contracts/tick sizes/lot/margin remain unverified.
- Order lifecycle: V3 adapter methods exist for place/modify/cancel, but they are not wired. V3 place response may return multiple `order_ids`; the local model lacks partial-fill state. Current broker status reconciliation is read-only and does not reconcile trades, fills, cash, positions, timeout/restart ambiguity or broker/local mismatches.
- Immediate safe improvement selected: the official [Get Order Details API](https://upstox.com/developer/api-documentation/get-order-details/) documents `data.order_id` and `data.status`. Require the response ID to be present and match the requested broker order before storing its status.


## Broker status identity validation — 17 October 2026

- The read-only status checker now rejects missing/blank broker `order_id` values as well as mismatches. This matches the documented [Get Order Details response](https://upstox.com/developer/api-documentation/get-order-details/), which returns `data.order_id` and `data.status`.
- Mocked tests confirm no local order status/fill state is inferred on malformed identity responses. CI: [backend 195 passed, 1 warning and migration check passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032760874); [frontend passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032760872).
- Next gap: the adapter lacks a per-order trade lookup, needed as a foundation for partial-fill reconciliation. Add read-only adapter support only; do not mutate local accounting yet.


## Read-only per-order trade lookup — 17 October 2026

- Added `get_order_trades` to the adapter contract and Upstox implementation. Official documentation specifies `GET https://api.upstox.com/v2/order/trades?order_id=...` and returns a list of trade records, including `trade_id`, `quantity`, `average_price` and `order_id`: [Get Order Trades](https://upstox.com/developer/api-documentation/get-trades-by-order/).
- Mocked test passes in CI. This method is not wired to reconciliation/accounting yet.
- Next safe foundation: read-only Order History lookup by stable tag or order ID to help recover a lost submission response without blindly resubmitting.
- Latest CI: [backend 197 passed, 1 warning, migration check passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032909906); [frontend passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39032909935).


## Read-only order-history lookup — 17 October 2026

- Added `get_order_history` to the adapter contract and Upstox implementation using the official [Get Order History API](https://upstox.com/developer/api-documentation/get-order-history/). It accepts `order_id`, `tag`, or both; rejects empty queries, blank identifiers and tags longer than 40 characters before network access.
- Mocked tests cover tag and order-ID queries plus invalid inputs. After fixing a missing test import found by CI, latest result is [200 backend tests passed, 1 warning, migration check passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033094768) and [frontend passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033094833).
- This method is not wired into a live submit/recovery workflow. Next deliverable is a reviewed live order state-machine design; no live submission yet.


## Live order state-machine design — 17 October 2026

- Added [`LIVE_ORDER_STATE_MACHINE.md`](LIVE_ORDER_STATE_MACHINE.md), a design-only specification grounded in official Upstox docs for Place Order V3, Modify/Cancel V3, Order Details, Order History and Order Trades.
- The design identifies the missing data model for one local order to multiple broker order IDs, unique trade IDs and partial fills; it also defines timeout recovery by stable tag, broker-confirmed cancel/modify states, atomic fill accounting, restart recovery and account-level risk gates.
- This is documentation only; no live submission or accounting behavior changed. Next task is additive model/migration support with tests, still not wired to execution.


## Broker-order schema foundation — 17 October 2026

- Added migration `202610170004_live_broker_order_state.py`, a `BrokerOrder` child model for one-to-many broker IDs, a unique nullable stable tag on local orders, wider order status field, and nullable execution fields for child-order linkage and per-broker unique trade IDs.
- Populated migration test upgrades from revision 003 and verifies preservation of paper data, multi-child mapping, duplicate ID/trade rejection and `PARTIALLY_FILLED` storage. Latest CI: [201 passed, 1 warning, clean migration](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033460748); [frontend passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033460785).
- Schema only: no live execution or reconciliation path uses these new fields yet. Next step is pure response validation/mapping helpers before any live service is wired.


## Pure Upstox response validation — 17 October 2026

- Added `backend/app/brokers/upstox/response_parsing.py` with typed, pure parsers for Place Order V3 IDs, Order Details, Order History and Order Trades. No network/database calls and no live execution wiring.
- Tests cover malformed payloads, mismatched IDs, duplicate place IDs/trade IDs, invalid quantity/price and valid empty history/trades. Official docs show Order History may contain repeated order IDs as a timeline; this is accepted.
- Latest CI: [223 passed, 1 warning, clean SQLite migration](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033704367); [frontend passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033704247).
- Next audit: define all-order live risk preflight and account circuit-breaker requirements before any live service is implemented.


## Live pre-trade risk gap audit — 17 October 2026

- Current `RiskEngine` is for strategy entries and uses realized P&L; manual orders bypass it and unrealized drawdown is not included. The paper order cap, virtual-cash checks and holdings protection in `ExecutionService` are not a live risk system.
- No broker funds/margin method exists in `BrokerAdapter`. Current official Upstox [Funds & Margin V3](https://upstox.com/developer/api-documentation/get-funds-and-margin-v3/) was released on 10 April 2026 and returns `available_to_trade.total` plus detailed cash/pledge balances. It requires `Api-Version: 3.0` and uses `GET https://api.upstox.com/v3/user/get-funds-and-margin` without a segment parameter. See the [release announcement](https://upstox.com/developer/api-documentation/announcements/get-funds-and-margin-v3/).
- Other live risk gaps: max notional/exposure/position limits for all order sources, realized+unrealized daily loss, order rate/frequency, stale quote and market-session guards, and a live account kill switch/circuit breaker.
- Next safe implementation: read-only funds/margin adapter support with mocked tests. Do not use it to approve an order until risk controls and the separate live service are complete.


## Funds & Margin V3 adapter update — 17 October 2026

- Added read-only `get_funds_and_margin` to the broker interface and Upstox adapter using `GET https://api.upstox.com/v3/user/get-funds-and-margin`, with required `Api-Version: 3.0` header. Official docs show `available_to_trade.total`, `cash_available_to_trade.total`, and `pledge_available_to_trade.total`; the service is unavailable from 00:00 to 05:30 IST and returns 423 during maintenance. [Official V3 docs](https://upstox.com/developer/api-documentation/get-funds-and-margin-v3/).
- Mocked tests verify URL, header, response shape and maintenance error propagation. The data is not yet used by risk checks.
- Latest CI: [225 passed, 1 warning, clean migration](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033992221); [frontend passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39033992223).
- Next: parse this nested response into a typed object and preserve separate cash vs pledged margin fields before any risk logic uses it.


## Funds & Margin V3 parser — 17 October 2026

- Added a pure typed parser for the official Funds & Margin V3 response. It keeps `available_to_trade.total`, `cash_available_to_trade.total`, and `pledge_available_to_trade.total` distinct; parses realized/unrealized loss; and supports signed unsettled-profit/loss amounts. It rejects malformed structure and non-finite/negative available balances.
- Tests cover valid response, missing nested fields, NaN/Infinity, negative available balances, malformed unsettled profit and error/423 envelopes. Latest CI: [235 passed, 1 warning, migration passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39034164505); [frontend passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39034164514).
- Next: read-only instrument margin calculation API support, still not used to authorize orders.


## Instrument margin calculation adapter — 17 October 2026

- Added read-only `BrokerAdapter.get_margin_details` and Upstox `POST /v2/charges/margin` call. Local validation caps requests at 20 instruments, rejects duplicate/empty keys, non-positive/non-integer quantities, unsupported transaction/product values, and invalid optional prices. Tests use mocks only.
- Latest CI: [238 passed, 1 warning, clean SQLite migration](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39035755714); [frontend checks passed](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39035755707).
- Status: read-only adapter foundation only. Response remains untyped/raw and does not authorize orders. Next: audit official response schema and add a typed parser only if no suitable existing parser exists.


## Upstox Margin Details parser — 18 October 2026

- Classification: **implemented in code; test execution requires CI confirmation**. Added typed `MarginEstimate` / `MarginBreakdown` models and pure `parse_margin_details` for documented `required_margin`, `final_margin`, and per-instrument margin components.
- Validation includes successful response envelope, non-empty margins array, required fields, and finite non-negative numeric values. Added valid-response and malformed/error regression tests.
- Code commits: `3c4dd6ac0d7d88a18916c241d28a224fc5031d5d`; tests `6995f64429b44134edfa5985ad4f50c3b54cfcab`.
- Safety classification unchanged: read-only estimate parsing only; no order approval, live submission, or account-risk decision consumes these values. Live trading remains not implemented.
- Verification gap: available Actions results show successful backend/frontend runs for the earlier verified commit, but no run could be confirmed for the current PR head. Do not mark these new tests passed until CI for the current head is inspected.


## Status correction — 18 October 2026 (supersedes stale next-step notes)

The following are now present in the branch: `BrokerAdapter.get_margin_details`, the Upstox `POST /v2/charges/margin` implementation with local request validation, pure `parse_margin_details`, and unit tests for success/error/malformed response shapes. Older notes saying the adapter method or typed parser is still missing are historical snapshots, not current status. The parser is read-only and is not used to authorize orders.

The current blocker is verification: the GitHub integration returned no workflow run and no commit status for the current PR head when checked. Earlier CI results (238 backend tests, one warning, migration/frontend checks green) belong to an older commit and do not verify the margin parser changes. No pass/fail conclusion is possible from the available evidence. Inspect or trigger the configured workflow from GitHub Actions and record actual results before advancing.

`MASTER_ROADMAP.md` is now the current sequencing guide. After this verification gate, the next implementation phase is a separate, initially unregistered `LiveExecutionService` with mocked tests, while preserving the current PAPER-only execution guard. Do not merge the draft PR, place real orders, or enable live trading.


## Status update — broker trade ingestion (18 October 2026)

| Requirement | Status | Evidence / limitation | Next action |
|---|---|---|---|
| Normalize broker trade-book rows | Implemented in parser; validation pending on current head | `parse_order_trades` returns typed `BrokerTrade` values and validates broker order ID, trade ID, quantity, price and side. | Verify parser tests on current head. |
| Persist broker trade rows idempotently | Implemented; verification pending | `BrokerTradeRecord` and `BrokerTradeIngestionService` stage rows with a unique `(broker_connection_id, broker_trade_id)` key. Exact replay is skipped; conflicting reuse is rejected. | Run test suite and migration check. |
| Tenant isolation and parent/child broker mapping | Implemented in intake service; verification pending | Service requires the authenticated owner, a LIVE local order, a mapped child broker order, and a child-order connection matching that owner's broker connection. | Verify negative-path tests. |
| Account-scoped broker identifiers | Schema change implemented; migration verification pending | Migration 006 changes broker child-order and execution uniqueness to include broker connection; legacy child rows are backfilled when identifiable. | Test populated legacy rows and current migration chain on SQLite; verify PostgreSQL separately. |
| Promote staged broker trades into accounted executions | Missing | Intake intentionally does not mutate cash, positions, order status, execution ledger or P&L. Actual fee handling and atomic live accounting are not complete. | Design and test a separate reconciliation/accounting step only after current intake CI is green. |
| Current branch CI | Requires verification | Current head `32eea17c141d4cfbc727eed2ff2a1b40d21dbba3` returned no workflow runs/statuses through the connected integration; local network could not clone GitHub. | Obtain exact-SHA backend and migration results; do not infer success. |


### Verification note — 18 October 2026

Migration 006 now has a targeted populated-data test for backfilling broker connection IDs on legacy broker child-order and execution rows. This is test code added, not a verified pass. Current head is `a68c336e4a35ccc0bfe4d6539760ad03e40672f1`; current-head CI must be checked before this requirement is marked verified.


Final verification note: code/test target `a68c336e4a35ccc0bfe4d6539760ad03e40672f1`; documentation-only commits followed it. The PR head observed at the last check (`1b0056d9739cd55d50cd5484cddf955aa8bf07db`) had no workflow run/status returned. Keep ingestion and migration requirements marked “verification pending.”


## Phase 2 follow-up audit — 18 October 2026

| Requirement | Current status | Evidence | Remaining gate |
|---|---|---|---|
| Bind ingested trades to the exact user's broker connection | Code hardened; verification pending | Commit `2cdbbe290f8b661cb91110dbb4e165fcef36f800` resolves the connection using the broker child order's connection ID plus owner and broker; null/unowned mappings fail closed. | Run cross-user binding regression test on current code. |
| Require instrument identity before staging broker fills | Code hardened; verification pending | Intake now rejects missing/non-text tokens and mismatches against the local instrument key. | Run parser + ingestion tests against current head and confirm Upstox trade-book payload contains the expected instrument token. |
| Malformed broker trade side | Code hardened; verification pending | Non-string/blank side input now returns a controlled validation error rather than an attribute error. | Run new negative-path tests. |
| Current-head backend/migration verification | Blocked/pending | Code/test target `264aa4c609d522cd01d07e8213bfee6f14c7a2bf`; no Actions run returned for this branch/head. | Manually dispatch `.github/workflows/backend-tests.yml` on the safety branch and record actual results. |

No live-order, execution-ledger, position, cash, order-status or P&L behavior was added by this continuation. The live-trading release gate remains closed.


Additional regression: commit `264aa4c609d522cd01d07e8213bfee6f14c7a2bf` adds coverage that legacy broker child orders left without a determinable connection are rejected by ingestion. Latest code/test target is `264aa4c609d522cd01d07e8213bfee6f14c7a2bf`; this test has been added but not executed on current-head CI.


## Phase 2 migration audit continuation — 18 October 2026

A further audit found that migration `202610180006` used an arbitrary `LIMIT 1` to infer a legacy broker connection. That is unsafe if data cannot establish a unique match. The migration now backfills `broker_orders` and linked `executions` only when exactly one owner/broker connection match exists; rows without a determinable connection stay NULL and the ingestion service rejects them. This preserves fail-closed behavior and avoids silently binding legacy records to an arbitrary account.

- Migration hardening commit: `81faa9f0225a8b50f1036b5316e747517c3f02ed`.
- Migration regression coverage commit: `203c7fcf47626ea85c4dce9762c165a2cd74ab26`, refined to model a legacy owner with no matching broker connection in `d2f7f87c82b286e54284da2a8c186be0ea28e852` and `669a3fb98cd47dccea7e75a1301c74c01c4a3ce3`.
- Latest code/test target: `669a3fb98cd47dccea7e75a1301c74c01c4a3ce3`.
- Verification: still pending. Current-head Actions query returns no run/status; do not claim tests or migrations pass until the configured workflow runs against this target.
- Next action remains the backend pytest + SQLite Alembic workflow gate. No live service wiring, production migration, PR merge, or live order is authorized by this checkpoint.


## Verified CI checkpoint — 18 October 2026

GitHub Actions run [#39109239829](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39109239829) completed successfully on commit `8a256828d202e25e3fba77b496f0da01899969b9` (safety branch). Evidence from the job log:

- Backend pytest: **266 passed, 1 warning, in 16.08s**.
- SQLite migration check: **`alembic upgrade head` succeeded**, including revisions `202610180005` and `202610180006`.
- Warning: Starlette test-client deprecation for `anyio.abc.BlockingPortal`; no test failure.
- Workflow job and overall run conclusion: **success**.

This verifies the code present at that SHA in CI. It does not validate PostgreSQL migration behavior, live broker connectivity, real order submission, live accounting, frontend build, or production deployment. Keep those as separate gates.


## Authoritative continuation checkpoint — 18 October 2026 (supersedes older pending-CI and next-task notes)

### Latest verified state

- Latest verified code/workflow SHA: `677fcf882e0ce1e6e02be3bb8df0d074b8fbf220`; commits after this SHA update documentation only and do not change the verified backend code.
- GitHub Actions [run #39109587876](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39109587876) on that exact SHA: **286 passed, 1 warning in 18.93s**, followed by successful SQLite `alembic upgrade head`. Run conclusion: success.
- Earlier verified baseline run #39109239829 had 266 passed; the newer 286-test run includes the new preflight tests. Do not use older “CI pending” paragraphs below as current status.
- The single Python warning is the existing Starlette/AnyIO deprecation. No test or migration failures occurred in the verified run.

### Completed in this continuation

1. Hardened migration 006 so it backfills broker connection IDs only when a unique owner/broker match exists; unresolved legacy rows remain unbound. Added regression coverage.
2. Added a separate `LiveExecutionService` preflight-only module and default-off `LIVE_ORDER_SUBMISSION_ENABLED` environment interlock.
3. Preflight requires `TRADING_MODE=LIVE`, the separate default-off interlock, explicit per-request confirmation, an injected reviewed account-wide risk gate, owned/active portfolio, active supported equity instrument, verified Upstox connection and usable token. Invalid inputs and risk-gate failures block.
4. The service returns a non-secret preflight plan only. It creates no Order row, does not call any broker adapter, does not persist a tag/intent, and does not change cash, positions, executions or trade staging. It is not registered to any API or worker. Live trading remains disabled.
5. Backend workflow now runs on `safety/**` pushes and relevant backend/workflow changes, while documentation-only changes do not retrigger backend CI.

### Next implementation task

**Stable idempotency/tag recovery for ambiguous submissions — design and mocked tests only.** Audit existing `Order.idempotency_key`, `broker_tag`, and adapter `get_order_history(tag=...)` behavior. Add a deterministic tag/intent persistence design and tests proving a retry never submits a second POST after a timeout. Do not implement or invoke real broker submission in this task; do not wire the service into routes/workers; do not merge PR #1 or enable live trading. After code/test commit, update progress, audit, requirements, roadmap, changelog, architecture, state-machine and handover files with exact CI evidence.

## Authoritative checkpoint — 18 October 2026 (idempotent live intent and tag recovery)

### Current verified implementation
- Latest code/test SHA: `de2e2b7524f09b1be2d4378a9b5ac29bdf26f9e7`. GitHub Actions [run #39110239225](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39110239225) completed successfully: **296 passed, 1 warning in 22.04s**; SQLite `alembic upgrade head` passed.
- Added `backend/app/services/live_order_recovery_service.py`: deterministic opaque 40-character broker tag, durable LIVE intent persistence, idempotency-key replay with exact-payload validation, submission-unknown state persistence, and read-only recovery through Upstox order-history-by-tag.
- Added `backend/tests/test_live_order_recovery_service.py`: stable tag, repeated intent, key/payload mismatch, fail-closed preflight, timeout/no-match no-resubmit, mismatched tag/intent, sliced child-order quantity reconciliation and repeated recovery.
- No `place_order` call is made by the new service. No API route or worker invokes it. Recovery stores broker child IDs only and does not infer order status/fills or change cash, positions, executions or P&L.
- The CI warning is a dependency/runner deprecation warning; test and SQLite migration steps passed. This run does not verify PostgreSQL migration, real broker API behavior, frontend build, or production deployment.
- Code and tests were committed separately: service `4990f28e7b8cfeadca85598abfac8111c8fe7130`; tests `de2e2b7524f09b1be2d4378a9b5ac29bdf26f9e7`.

### Next task
Implement a concrete, testable **account-wide live pre-trade risk gate** and inject it into the preflight path: current positions/exposure, order-value and order-frequency limits, market-session/stale-quote requirements, and broker funds/margin checks with fail-closed behavior. Mock all external calls. Do not add a broker POST, wire any route/worker, merge PR #1, or enable live trading in that task.

### Release status
PR #1 remains draft/open/unmerged. Original `Tradepro` remains untouched. Live trading remains **NOT READY**; no real orders have been submitted.

## Authoritative checkpoint — 18 October 2026: Upstox risk snapshots and official session calendar

### Verified code and tests
- Latest verified code/test SHA: `c683fbd16d114b2a41a80a646fc91ee2d4cf25eb`. GitHub Actions [run #39111682177](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39111682177) succeeded: **315 passed, 1 warning in 25.97s**; SQLite Alembic migration verification passed.
- Added strict read-only parsers in `backend/app/brokers/upstox/risk_snapshot_parsing.py` for full market quotes, open positions, official market holidays, special sessions and NSE timings.
- Added adapter calls for full quote, positions, funds/margin, estimated margin and official calendar endpoints, plus `backend/app/services/upstox_live_risk_snapshot_service.py` to collect and validate snapshots. It includes quotes for broker positions and unresolved live-order instruments, respects Upstox's 500-key quote limit, and contains no order-placement call.
- Added mocked regression coverage for malformed/naive quote timestamps, instrument identity mismatch, duplicate positions, holidays/special sessions, provider failure and the read-only collector. Current CI: 315 passed.
- The collector is not wired into a route, worker or order submission. Live mode remains disabled; no real broker requests or real orders were used in these tests.

### Remaining caveats
- The adapter/parser contract has been verified against mocks, not live Upstox responses. Broker-specific response fields and official calendar behavior need documented API-contract review before staging.
- Snapshot collection uses the currently supplied access token; safe orchestration from the user's encrypted connection into a fresh snapshot bundle and the synchronous risk gate is not yet implemented.
- Full live order status/fill/cancel reconciliation, connection-scoped fill idempotency and live accounting remain incomplete. PostgreSQL migration, exact-head frontend build and staging remain unverified.

### Next task
Implement a separate asynchronous, **preflight-only coordinator** that obtains a valid per-user Upstox token through the existing credential service, collects read-only risk snapshots, injects the snapshot-backed providers into `AccountWideLiveRiskGate`, and then invokes the existing `LiveExecutionService.preflight` contract without submitting or persisting an order. Add mocked tests for wrong user/connection, token expiry/provider failures, stale snapshots and successful preflight. Keep it unregistered: no route/worker, no broker POST, no live-mode enablement.

### Release status
PR #1 remains draft/open/unmerged. Original `Tradepro` remains untouched. Live trading is **NOT READY** and disabled. No real orders have been submitted.

## Authoritative checkpoint — 18 October 2026: reconcile-before-promote coordinator

### Verified code and CI evidence
- Latest verified code/test SHA: `cfa038fe49dfde1c441f77d5c4a12fcb13ba695a`. GitHub Actions [run #39118263100](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39118263100) succeeded.
- Full backend suite: **380 passed, 1 skipped, 1 warning in 27.98s**; SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL concurrency integration passed (**1 passed in 0.36s**).
- Added unregistered `LiveOrderFillReconciliationCoordinator`. It reconciles every mapped Upstox child order and its durable trade list before promoting any staged fill for that conceptual parent order. If any child fails reconciliation, none of the parent's fills are promoted.
- Multiple fills require distinct timezone-aware exchange timestamps, preventing ambiguous position-accounting order. Promotion stops at the first charge/accounting failure; completed fills are reported and retries remain idempotent.
- Regression tests cover successful chronological promotion, sibling reconciliation failure, missing/duplicate timestamps, and promotion failure. The parent Order remains unchanged; the coordinator contains no order-placement call and is not registered to routes/workers.

### Remaining caveats
- Coordinator tests currently inject fake reconciliation/promotion collaborators; the separate PostgreSQL integration test covers real SQLAlchemy service concurrency with synthetic records, not live Upstox behavior.
- Contract-note references remain caller supplied and not independently authenticated. Frontend build, staging, monitoring, account-level kill switch, broker-error circuit breaker, and complete production live lifecycle remain unverified/incomplete.
- PR #1 remains draft/open/unmerged; original `Tradepro` is untouched; live trading remains disabled and not ready.

### Next task
Add a service-level integration test that composes the **real** `BrokerChildOrderReconciliationService`, `BrokerTradeIngestionService`, `LiveFillPromotionService`, and `LiveFillAccountingService` with a fully mocked read-only Upstox adapter and charge estimator. Verify reconciliation happens before promotion, repeated runs are idempotent, failures leave no accounting rows, and paper cash/positions remain unchanged. Keep all promotion services unregistered; no order submission, PR merge, or live-mode enablement.

### Release status
Live trading is **NOT READY** and disabled. No real orders have been submitted.


## Requirements audit update — 18 October 2026

- **Requirement:** broker-confirmed fills must be reconciled before live accounting, retries must not duplicate executions, and paper/live accounting must remain isolated.
- **Change:** commit `b5783d421f64fcb8e7f1d75f1af5185fd9029f59` adds service-level integration coverage against the real existing reconciliation, ingestion, promotion and accounting services. It does not add a second coordinator or change production runtime wiring.
- **Classification:** tests added; verification **pending CI** at this checkpoint. Do not classify as verified until the workflow for the exact commit succeeds.
- **Remaining caveat:** mocks verify application orchestration and response parsing, not live Upstox behavior or production deployment. No real order submission is tested or authorized.


### Latest test evidence status

The latest test commit is `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88`, superseding `b5783d421f64fcb8e7f1d75f1af5185fd9029f59`. The test now exercises fresh durable trade insertion through the real ingestion service. CI is still pending/unverified for this exact SHA.

## Superseding verified checkpoint — 18 October 2026: real-service fill reconciliation integration

### Exact verification evidence
- Latest tested code/test SHA: `c779f2543ea1f20efbd8b7dca38a9c2aed201749`.
- GitHub Actions [run #39118955335](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39118955335): **success**. Full suite: **385 passed, 1 skipped, 1 warning in 34.01s**. SQLite migration upgrade passed, PostgreSQL 16 migration upgrade passed, and PostgreSQL concurrency integration passed (**1 passed in 0.35s**).
- This exact-head run verifies the fresh-ingestion integration test refinement from commit `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88` and fixes for nondeterministic child order assertions and deleted ORM fixture access.
- The real-service integration test now begins with no staged trade rows: mocked Upstox trade reads must be inserted by the real `BrokerTradeIngestionService` before official status reconciliation and promotion. Repeated reconciliation/promotion is idempotent; sibling status failure prevents any fill accounting; charge-estimate failure creates no Execution/LivePosition rows; paper cash/positions and parent Order state remain unchanged.
- PostgreSQL 16 verifies migration compatibility and concurrent charge adjustments/fill promotion. Lock scoping explicitly avoids PostgreSQL's `FOR UPDATE` nullable outer-join error.

### Release status and caveats
- All broker API responses in tests are mocked. No live Upstox API requests or real orders were sent.
- The coordinator, fill promotion and charge-adjustment services remain unregistered in order routes/workers. Live order submission remains disabled.
- Frontend build/staging, real broker contracts, exchange holiday coverage, operational monitoring, account-level kill switch and broker-error circuit breaker remain outstanding. PR #1 remains draft/open/unmerged; original `Tradepro` untouched.

### Next distinct task
Implement and test the **persisted account-level live kill switch and broker-error circuit breaker**: durable state, fail-closed read behavior, reason/timestamp/audit trail, threshold-triggered circuit trips, manual-reset policy and account-wide scope across portfolios. Keep it unregistered from order submission until separately reviewed; do not merge PR #1 or enable live trading.

This checkpoint supersedes prior notes saying CI for `4d8941f436bed1f61b46c4123a4a7c6d5c6b6f88` was pending. The latest verified test SHA is `c779f2543ea1f20efbd8b7dca38a9c2aed201749`.


## Requirement update — partial promotion recovery

- Requirement: a charge/accounting failure after earlier fills have been promoted must stop subsequent processing and allow safe retries without duplicating earlier executions.
- Added test coverage in commit `1a3475c69d3a93ece7bfad22ace4dce52231bfa1`, using the real reconciliation, ingestion, promotion and accounting services with broker reads/charge estimates mocked.
- Status: **pending exact-SHA CI**. Do not mark verified until the workflow for this SHA passes. No production wiring or real broker order was introduced.


## Requirement — durable account-wide kill switch and broker circuit breaker

- Implemented service logic in `backend/app/services/live_account_safety_service.py`, durable schema in migration `202610180009`, and tests in `backend/tests/test_live_account_safety_service.py`.
- Expected contract: absent/stale/unknown safety state blocks; new state is latched off; threshold of consecutive broker errors opens the circuit and trips the kill switch; repeated idempotency keys do not double-count; successful broker calls do not auto-close the circuit; manual reset requires a fresh passing health check, zero error count, explicit actor and reason.
- Status: implementation committed, **verification pending** on head `57939799b7e8b436d5095924b86a89ce380a956e`. Await backend pytest and SQLite/PostgreSQL migration CI; PostgreSQL concurrency coverage remains a follow-up.
- Not wired into order submission and does not authorize live trading.


### Reset gate test refinement

Latest test code SHA: `c97be866828bd47a23f22fc44fac2d3359e70f35`. The test now isolates the broker-error counter reset condition by recording a passing health check while the counter is still nonzero, then clearing the counter via broker success and recording another passing health check before manual reset. CI/migration verification remains pending.

## Superseding verified checkpoint — 18 October 2026: account-safety PostgreSQL concurrency

- Code/test target SHA: [872eab69082b231117184d80b1bb4a7a96c15b6b](https://github.com/tarunsharma2610-del/tradepro-improved/commit/872eab69082b231117184d80b1bb4a7a96c15b6b). This includes the PostgreSQL account-safety concurrency tests and the workflow change that runs them alongside the existing charge-adjustment concurrency test.
- GitHub Actions [run #608](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39120699215): **success**. Full backend suite: **395 passed, 4 skipped, 1 warning in 29.36s**. SQLite Alembic upgrade passed. PostgreSQL 16 Alembic upgrade passed. Dedicated PostgreSQL integration: **4 passed in 0.44s**.
- PostgreSQL safety coverage now proves: two concurrent submissions with the same broker-error idempotency key count once; two distinct concurrent broker errors serialize and trip the circuit exactly at the configured threshold; concurrent manual resets permit only one reset and preserve the audit trail.
- Migration issue resolved: removed duplicate revision 202610180009_live_account_safety.py; canonical safety migration is 202610180010_live_account_safety.py, chained after 202610180009_live_charge_adjustment_ledger.py. The prior duplicate-revision failure is superseded by successful run #606 and then run #608.
- The account safety service remains unregistered from order submission. These tests use a real PostgreSQL test database and synthetic test users only; no live broker API or order-write endpoint was called. PR #1 remains draft/open/unmerged; original Tradepro remains untouched.
- **Next task:** add read-only preflight composition coverage using the existing LivePreflightCoordinator, AccountWideLiveRiskGate, and persisted LiveAccountSafetyService decision. Fail closed on any denial/error; do not register the composition with order routes/workers or enable live order submission.

## Superseding verified checkpoint — 18 October 2026: safety-aware read-only preflight composition

- Code/test target SHA: [3e73efd441315294970cb652ddeb9b37b00b67b9](https://github.com/tarunsharma2610-del/tradepro-improved/commit/3e73efd441315294970cb652ddeb9b37b00b67b9). The coordinator change is in commit [866336676b24b0da34fe833263b0f2c33204bf17](https://github.com/tarunsharma2610-del/tradepro-improved/commit/866336676b24b0da34fe833263b0f2c33204bf17).
- GitHub Actions [run #611](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39121063921): **success**. Full backend suite: **398 passed, 4 skipped, 1 warning in 29.51s**. SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL integration passed (**4 passed in 0.41s**).
- LivePreflightCoordinator now checks the persisted account-wide LiveAccountSafetyService decision after local intent/ownership validation and before credentials or any broker snapshot. Missing safety state, a tripped latch/open circuit, stale health or an unexpected safety-check exception blocks preflight. The service is injectable for testing; default construction uses the same preflight clock.
- Regression tests prove missing state, a tripped latch, and an unexpected safety-check exception all block before any read-only broker call. Existing successful preflight tests explicitly establish a passing health check and manual reset in the test fixture.
- This is read-only preflight composition only. LivePreflightCoordinator remains unregistered from order routes/workers, no broker order-write method is called, live trading remains disabled, PR #1 stays draft/open/unmerged, and the original Tradepro repository remains untouched.
- **Next task:** audit authentication/authorization and operator audit visibility for any future safety-control endpoint. Do not create or wire a control route until that review is complete; keep live order submission disabled.


## Security and operator-audit requirements — 18 October 2026

New review: [SECURITY_CONTROL_ENDPOINT_AUDIT.md](SECURITY_CONTROL_ENDPOINT_AUDIT.md), commit [10d87d9d9010b2c48ebcf25c832a2ea574100889](https://github.com/tarunsharma2610-del/tradepro-improved/commit/10d87d9d9010b2c48ebcf25c832a2ea574100889).

- [x] Inspect existing auth/JWT dependency, admin guard, MFA routes, audit model/helper, API router and relevant route tests.
- [x] Identify current protections and missing operator audit visibility.
- [ ] Define least-privilege safety permissions and cross-account query boundaries.
- [ ] Define step-up authentication and CSRF/origin controls for privileged mutations.
- [ ] Define atomic safety-state + audit-event persistence, append-only enforcement and strict redacted event schema.
- [ ] Add HTTP-level negative, replay, audit-failure and concurrent-reset tests after API design approval.
- [ ] Audit all manual, strategy, worker, retry/recovery and broker-write entry points before live safety wiring.

No endpoint or live execution wiring was added in this audit step. Production/security sign-off remains open.


## Order-entry path inventory requirements — 18 October 2026

See [ORDER_ENTRY_PATH_INVENTORY.md](ORDER_ENTRY_PATH_INVENTORY.md), commit [a477489c7e2d5b6883c299c1e9a8aee1cbef055f](https://github.com/tarunsharma2610-del/tradepro-improved/commit/a477489c7e2d5b6883c299c1e9a8aee1cbef055f).

- [x] Inventory manual order/cancel route, strategy immediate-evaluation route, scheduled worker, paper execution service and adapter write primitives.
- [x] Record that current order service rejects LIVE/unknown modes and is PAPER-only.
- [x] Record the LiveOrderRecoveryService composition gap: it uses LiveExecutionService, not LivePreflightCoordinator.
- [ ] Implement one reviewed central broker-write service as the only caller of adapter place/modify/cancel methods.
- [ ] Add source-call guardrails and fail-closed tests for every route/worker/strategy entry point.
- [ ] Resolve auth/operator-audit design findings and atomic state/audit persistence before creating safety-control routes.
- [ ] Verify all order paths in CI and explicit broker sandbox tests before any live-enable decision.


## Requirements checkpoint — central write and operator safety controls (18 October 2026)

Design requirements are consolidated in `CENTRAL_BROKER_WRITE_BOUNDARY_DESIGN.md`. New explicit gates: only one production broker-write service; no unapproved direct adapter calls (CI-enforced); account-wide safety/risk/freshness checks for submit/modify; narrowly defined risk-reducing cancellation semantics; durable intent+event before external I/O; no blind retry on ambiguous broker outcomes; least-privilege scopes; server-derived actor; recent MFA step-up for reset; CSRF/Origin controls; tenant-scoped paginated audit reads; strict redaction; PostgreSQL append-only protection; and service/API/worker/PostgreSQL concurrency tests.

Status is **design specified, implementation pending**. Do not treat the requirements as satisfied. Live submission stays disabled.


### CI guard verification — 18 October 2026

The source-call guard requirement now has a CI implementation and a passing verification on code SHA `bdf208efcc32b44a6367157dd2ab0aab946e6574`, run #617: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39123311281. Backend suite 402 passed / 4 skipped; migrations and PostgreSQL concurrency checks passed. Mark only the guardrail requirement as verified; central writer, safety permissions/API, atomic event semantics, DB-enforced immutability and end-to-end enforcement remain pending.


## Safety audit storage requirement checkpoint — 18 October 2026

Partially implemented: request fingerprint and idempotency mismatch rejection; unique state-version audit sequence; DB triggers rejecting UPDATE/DELETE in SQLite and PostgreSQL; transaction rollback test when audit insertion fails; PostgreSQL trigger tests; and stale expected-version validation for manual reset.

Still pending: exact-head CI green confirmation; operational restrictions against privileged trigger removal; endpoint-level mandatory expected-version enforcement; authorization/MFA/CSRF; and central broker-write integration. The latest CI run `39124312326` was pending when this note was written, so do not mark all storage requirements verified yet.


### Storage-hardening verification update

The exact-head CI run #39124312326 failed one stale-version test due to a mutable ORM fixture reference; the test was corrected in commit `6cd0ced108e35d715359d649a463d80709dd1fb1`. Run #39124498280 is pending, so database immutability and the final test matrix are not yet marked fully verified.


### Storage verification superseding pending status — 18 October 2026

The storage hardening changes passed CI run #625 on SHA `6cd0ced108e35d715359d649a463d80709dd1fb1`: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39124498280. Backend tests 406 passed / 5 skipped; SQLite and PostgreSQL migrations passed; five PostgreSQL integration tests passed including append-only enforcement. Mark only these storage/transaction controls verified. Authorization, MFA, CSRF, safety endpoints, central writer and end-to-end composition remain open.


## 18 October 2026 — safety authorization foundation (partial; CI pending)

- Implemented the safety_permissions user grant field with default-empty migration, allowlisted permission dependency, malformed JWT subject 401 normalization, and a reusable cookie-Origin mutation dependency.
- Added tests for explicit grant enforcement, no implicit is_admin grant, invalid permission names, malformed signed subject, and Origin policy.
- Open: recent-MFA step-up, trusted grant management, wiring guards into safety endpoints, tenant-scoped safety/audit queries, endpoint-level negative HTTP matrix, and CI verification for these commits. No safety route was registered.

### Follow-up correction — 18 October 2026

The Origin guard now requires an exact Origin serialization match (including rejecting a trailing slash), and unused imports were removed from the user model. Follow-up commits: f7c08e2605fb7f7828792154570af79cf5ccf724 and 4337d0ce4ef645914f32c56db87c81699c04763e. CI/status lookup has returned no run/status for the authorization changes; do not claim tests or migration passed until a workflow result is tied to the code/test SHA. Recent-MFA step-up and route wiring remain outstanding.

## Superseding checkpoint — recent-MFA step-up foundation (18 October 2026)

- Added a dedicated `POST /api/v1/auth/mfa/step-up` challenge. It requires an authenticated active user, MFA already enabled, fresh password verification and a valid TOTP code; it is rate-limited and applies the configured same-origin guard to cookie-authenticated requests. Successful challenges return a purpose-bound `step_up` JWT with `scope=safety.reset`, `amr=[pwd,totp]`, a verification timestamp, and a five-minute expiry. Failed credentials are audited without logging credentials or the token.
- Added `require_recent_safety_mfa`, which requires the separate `X-Safety-Step-Up` header, validates token type and purpose, verifies recent MFA and issuance timestamps, and binds the token to the authenticated user. It is not yet attached to a safety reset route because no safety-control routes have been exposed.
- Added unit/dependency tests for missing/wrong-scope/stale/user-mismatched step-up tokens and HTTP tests for success, invalid password and accounts without MFA. These tests are committed but **not yet verified by a GitHub Actions run for the latest code/test SHA**; do not claim they pass until exact-head CI is green.
- Latest code/test commit for this checkpoint: `ee8968f9d7d8698703e59911c7091d5f7c870c23`. Related commits: `325d9a854c05bb7dead6f6f626bf749383804a8e`, `9b65f92b060c0745c1e84e535ec5397cdf490b5d`, `1450a3d0dd8c3629e72142fe06cec699be7202f0`, `0bf5f86d9dd07ecaebe10b93149841647dfbccdf`, `1afd892fb1fa7aaf6c1b0028c248b59e06ec9994`, `aaad1d020cb629cb6d554bd08ff02d25fb1c4666`, and `ee8968f9d7d8698703e59911c7091d5f7c870c23`.
- Remaining authorization gates: trusted safety-permission provisioning, tenant-scoped/paginated audit reads, route-level permission + Origin + step-up enforcement, comprehensive negative HTTP tests, and latest-head CI. The helper does not solve these by itself. The safety status/audit/trip/reset routes and central broker-write service remain absent/unwired.
- Keep PR #1 draft/open/unmerged, keep `TRADING_MODE=PAPER` and `LIVE_ORDER_SUBMISSION_ENABLED=false`, never call broker order-write endpoints, and leave the original `Tradepro` repository untouched. Phase 2 remains incomplete.

### Superseding MFA guard correction

The step-up verifier now also denies a token if the authenticated user's MFA has since been disabled; regression coverage was added. Latest code/test commit: `ecf09e800c0dc7fc83d200d603f510348433aa58` (guard change `8a46241e766b9504c3a9bc3ba182043bac98a75d`). Exact-head GitHub Actions/status remains unverified; prior CI results do not cover this change. This remains a foundation only: the dependency is not wired to a safety-reset endpoint because those endpoints do not yet exist.

## Superseding checkpoint — audited safety-permission provisioning (18 October 2026)

- Added `PUT /api/v1/admin/users/{user_id}/safety-permissions` for one explicit grant/revoke operation at a time. The request schema only accepts the four defined `safety.*` scopes; arbitrary scopes are rejected by validation.
- The actor must be a platform admin, must pass the five-minute user-bound password+TOTP step-up, and cookie-authenticated mutations must pass the configured Origin guard. `is_admin` alone is not enough. Self-grants are rejected; revocation remains allowed for an admin's own account to support removal of access.
- Target user's permission list and the audit record (`safety.permission.grant/revoke`, actor ID, target ID and scope) are committed in the same DB transaction. The route does not grant access to read other users' audit data and does not expose the safety status/audit/trip/reset endpoints.
- Added HTTP regression tests for missing step-up denial, self-grant denial, and grant/revoke behavior with audit evidence. **These tests have not been executed in this environment and exact-head CI has not been confirmed.** Treat them as committed, unverified tests, not passing tests.
- Relevant commits: endpoint `ed1cae900a326a4922dbf42a5dbe2b7ed9d50d13`; constrained schema `8a50e8176d25e26a58f52649b21ab01cafa60cad`; test additions `b1b326e7ff409b84d2feab438f69275678939d2f`; formatting follow-up `1d464907a2aec9d0a4e257cb960bf32b24d032ee`.
- Remaining gates: CI on latest code/test SHA, independent review of the permission-provisioning threat model, tenant-scoped audit reads, safety status/audit/trip/reset routes with explicit permission enforcement, state/event atomicity at endpoint level, central broker-write service and end-to-end path enforcement.
- Continue to keep PR #1 draft/open/unmerged and keep live order submission disabled. Phase 2 is incomplete; original `Tradepro` remains untouched.

### Follow-up correction and verification checkpoint (18 October 2026)

- Corrected the safety-permission endpoint import formatting and cleaned test imports after reviewing the committed source through GitHub. Latest test-file commit: `ae46db76e86ea28116bcaf80b9a02c64eb713e9b`; endpoint import correction: `3ef5d32ddeb97ffbd43c61acb74945dd4f564729`.
- The repository connector did not expose a local test runner, and GitHub Actions/combined-status lookups returned no run/status for the latest code/test SHA. Tests remain **unexecuted/unverified**; the older CI run is not evidence for these changes. The next action must be to get CI running on the current branch head and resolve any failures before adding further security-sensitive behavior.
- Phase 2 remains incomplete. Keep PR #1 draft/open/unmerged, preserve PAPER-only defaults and live-order submission disabled, and leave the original `Tradepro` repository untouched.

## Phase 2 checkpoint — tenant-scoped safety audit read (18 October 2026)

- Added `GET /api/v1/admin/safety/audit`, protected by the explicit `safety.audit.read` permission. It accepts bounded pagination (`limit=1..100`, `offset=0..100000`), returns a page envelope and uses a stable `created_at DESC, id DESC` order.
- The SQL query scopes rows to `AuditLog.user_id == authenticated_user.id` and `action LIKE 'safety.%'` before counting or pagination. The caller cannot provide a target user ID; unrelated audit actions and other users' events are not returned. This is an actor-scoped view of safety events, not an administrator-wide or target-account audit browser.
- Added HTTP regression tests for permission denial, pagination bounds, and tenant isolation / filtering. **The tests are committed but have not been executed locally; exact-head GitHub Actions status has not been confirmed.** Do not call the feature CI-verified yet.
- Relevant commits: endpoint `d608f4fdd8a9f10b0647fbe4083d35809b27061f`; response schemas `d46c9268c7c05ca9e207898ca80674df56883a03`; tenant isolation tests `eda5a3589765211105457e2b8950d0c20f00f011`; follow-up import/test cleanup `584b774e175b1aecd74784286bd5fca566e1be6d`.
- Remaining Phase 2 work: run/fix CI on the latest branch head; implement persistent safety status and kill-switch trip/reset routes with the correct permission, Origin and MFA gates; decide and document operator-vs-account audit visibility before expanding audit scope; ensure atomic state/event transactions and concurrency semantics; implement the central broker-write service and enforce it across every execution path. Live trading remains disabled and PR #1 remains draft/open/unmerged.

## Phase 2 checkpoint — authenticated safety control endpoints (18 October 2026)

- Added and registered `backend/app/api/v1/safety.py` with three user-scoped endpoints: `GET /api/v1/safety/status` requires `safety.status.read`; `POST /api/v1/safety/kill-switch/trip` requires `safety.kill_switch.trip`, cookie-Origin validation and an `Idempotency-Key`; `POST /api/v1/safety/kill-switch/reset` requires `safety.reset`, a fresh user-bound password+TOTP step-up token, cookie-Origin validation, an idempotency key, and a required `expected_version`.
- Status reads only the authenticated user's Upstox account safety state. Missing state is reported as blocked/unsafe without initializing or creating a state. Trip initializes missing state in the safe/tripped state before applying the idempotent trip. Reset delegates to the existing transaction-safe service and returns conflict if state/version/health requirements are not met.
- Reset deliberately does **not** accept a client assertion that a health check passed. The existing service requires a recent persisted `HEALTH_CHECK_PASSED` event, zero consecutive broker errors, and matching expected state version. No new public health-check endpoint was added because a caller-supplied “passed” flag would be unsafe without real broker/session/account snapshot validation.
- Added HTTP regression tests for permission denial, safe missing-state response, trip behavior, required idempotency key, reset MFA denial, reset blocked without a fresh successful health check, and cookie-Origin rejection. **These tests have not been executed in this environment.** GitHub Actions lookup exposed no PR-triggered run for the latest test commit and combined status was empty; the connector's workflow-run lookup filters to PR-triggered runs, so this is not proof that no push-triggered run exists. Exact-head test status remains unverified.
- Relevant commits: safety route/import cleanup `267da864b5187cfad91ac68b76ba86cf06b7848f`; schema `01f0deb4949cd13072fb2feda9924e0a97eaf5cf`; router registration `fc95e748197be9e8848c990f55079fbd8afc4a30`; endpoint tests `3ae21dac71edb449835124f99794f510c8b80761`.
- Review caveat: the existing `GET /api/v1/admin/safety/audit` still reads legacy `AuditLog` rows with `safety.*` action names; the durable state-transition history is in `LiveAccountSafetyEvent`. Before treating operator audit visibility as complete, update that endpoint to read the immutable event table and scope by the associated state owner and authorized actor.
- Remaining gates: run and fix CI on the current branch head; fix the safety audit endpoint's event source; perform security review of the grant/reset token purpose boundaries; add negative HTTP tests for every route and error path; verify atomic state/event concurrency at endpoint level; implement the central broker-write service and enforce it across API, strategy worker, recovery and adapter paths. Keep `TRADING_MODE=PAPER`, `LIVE_ORDER_SUBMISSION_ENABLED=false`, PR #1 draft/open/unmerged, and original `Tradepro` untouched. Phase 2 is incomplete.


## Superseding Phase 2 checkpoint — immutable safety audit source (18 October 2026)

- Updated `GET /api/v1/admin/safety/audit` to read `LiveAccountSafetyEvent` joined to `LiveAccountSafetyState`, rather than the legacy `AuditLog` table. Tenant scoping is performed in SQL using the authenticated user's state ownership before counting and pagination; callers cannot select another user/state. Output omits idempotency keys and request fingerprints and exposes only the safety event fields needed for audit review.
- Reworked the tenant-isolation/pagination HTTP test to seed durable safety events for two different account owners and a non-safety legacy audit row. It checks that only the authenticated tenant's immutable safety events are returned and sensitive replay metadata is not serialized.
- Commits: endpoint `cd68384c48a98f2bd2ded054f37bb04d24885b12`; regression test `7913f821a7ac194c537adf911a4ef39ba4410e41`.
- Verification status: exact-head CI/status lookup returned no runs/statuses for the latest test commit. Tests have **not** been run in this environment; treat this change as committed but unverified until GitHub Actions runs against the current branch head. No live broker write was called.
- Next: verify/fix current-head CI; then review reset/idempotency and endpoint transaction behavior, followed by central broker-write boundary implementation and enforcement across API, strategy workers, recovery/retry and adapter paths. Phase 2 remains incomplete. Keep PAPER mode, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.


## Authorization/MFA route-matrix verification checkpoint — 18 October 2026

- During matrix review, identified a compatibility defect in the first scoped-MFA dependency refactor: existing direct unit tests and callers invoke `require_recent_safety_mfa(step_up_token=..., user=...)`, so turning that function itself into a factory would break those calls. Corrected by restoring `require_recent_safety_mfa` as the default `safety.reset` validator and adding `require_recent_safety_mfa_scope(scope)` for FastAPI route dependencies. Reset and admin permission routes now explicitly use their corresponding scope-specific dependency.
- Added route-level regression coverage proving a `safety.reset` token cannot grant safety permissions; existing coverage includes non-admin privilege denial, direct cross-purpose rejection, stale tokens, disabled MFA, wrong user/scope, Origin checks, default-deny permissions, tenant isolation, idempotency-header validation, and safe reset requiring fresh health evidence.
- Relevant commits: dependency compatibility fix `24b463894eca1fde37381bef66d47366a806fe32`; route wiring `0cfc3e290dbc730af9fb854954a95875809ad3cf` and `17088f172d40aa106d1cd1d5f8b674c056919a86`; test matrix update `6e77aa77a7c0bba84d2aae539b37fa6228c088b9`; route-level cross-purpose test `c40edddbeb8b65ec468ae0419897d1cd6cc2c325`.
- CI: GitHub Actions backend workflow is running for the preceding dependency/test commit (`39132630566`) and queued for latest route-level test commit (`39132698515`). The preceding run has not yet reached pytest; do not mark the matrix passed until latest-head workflow concludes. Monitor [latest workflow run](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39132698515).
- Still outstanding: wait for latest-head CI; fix any failures and re-run; verify SQLite/PostgreSQL migrations and concurrency checks. This is a route-matrix review, not a complete authorization/security certification. PAPER mode remains mandatory, live broker order submission remains disabled, PR #1 remains draft/open/unmerged, and Phase 2 is incomplete.


## CI failure triage update — 18 October 2026

- GitHub Actions run `39132630566` failed at `Run test suite`: `433 passed, 5 skipped, 1 failed`. The single failure was `test_non_admin_cannot_request_permission_management_step_up`, which returned 401 rather than the expected 403 because its test fixture enabled MFA but did not mock TOTP verification. The authorization code was not reached by that test.
- Fixed the test fixture to mock a valid `123456` TOTP code, isolating the authorization behavior under test. Fix commit: `b5c96fc5115bd4b9fae7be6fc0a168d55c5ace9c`.
- A new backend CI run is in progress for the fix: [run 39132803282](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39132803282). Do not consider the suite green until this exact-head run finishes successfully. Previous failures skipped migrations/concurrency stages because pytest failed first.


## CI verification result — PASS (18 October 2026)

- Backend workflow run `39132803282` passed for backend commit `b5c96fc5115bd4b9fae7be6fc0a168d55c5ace9c`: broker-write boundary guard passed; full backend suite **435 passed, 5 skipped, 1 warning**; SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL account-safety/charge-adjustment concurrency tests **5 passed**. One Starlette/AnyIO deprecation warning remains non-blocking.
- The earlier failing test was corrected by mocking valid TOTP in the non-admin purpose-denial test; the passing run confirms the corrected test setup and current backend changes. Documentation-only commits followed, so the tested application code is unchanged, but the docs commit itself did not trigger backend CI due workflow path filters.
- This is evidence for the current authorization/MFA test changes and listed CI gates, not a complete security certification or Phase 2 completion. Continue with broader authorization route matrix and broker-write boundary implementation; live order submission remains disabled and PAPER mode remains mandatory.


## MFA HTTP route-matrix follow-up — 18 October 2026

- Added two missing HTTP-level cases to `backend/tests/test_api_authorization.py`: cookie-authenticated `POST /api/v1/auth/mfa/step-up` without an Origin header must return 403; unsupported step-up purpose `safety.live_trade` must be rejected by request validation with 422. These complement existing tests for missing/disabled MFA, wrong password, non-admin privileged-purpose denial, reset-vs-admin token scope separation, stale/user-bound tokens, cross-origin mutations, permission denial, and reset health prerequisites.
- Test commit: `58778259324119379c69b03c822c13849b223d22`. GitHub Actions run [#39133596645](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39133596645) is running; broker-write boundary guard has passed and pytest is in progress at time of this note. Do not claim the new tests pass until the run completes and its pytest/migration/PostgreSQL steps conclude successfully.
- Review outcome so far: reset and permission-management routes explicitly use distinct MFA scopes; platform-admin status alone does not grant safety permissions; user audit is tenant-scoped to immutable safety events. The matrix is broader but not exhaustive, and no independent security certification is implied.
- Next after CI: fix only demonstrated failures; if green, proceed to the central broker-write authorization/gating design and enumerate every order-write path before wiring anything. Keep PAPER mode, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.


## MFA HTTP route-matrix CI result — PASS (18 October 2026)

- GitHub Actions [run #39133596645](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39133596645) passed for test commit `58778259324119379c69b03c822c13849b223d22`: broker-write boundary guard passed; backend suite **437 passed, 5 skipped, 1 warning in 28.01s**; SQLite Alembic migration passed; PostgreSQL 16 Alembic migration passed; PostgreSQL safety/charge-adjustment concurrency tests **5 passed**.
- This run verifies the added missing-Origin and unsupported-purpose HTTP tests plus the existing MFA/authorization matrix at that tested code SHA. Later documentation-only commits did not alter application code. One non-blocking Starlette/AnyIO deprecation warning remains.
- This does not certify every auth route or complete Phase 2. Next task: map all broker order-write entry points and design a single fail-closed broker-write authorization gate, then test that all paths are blocked in PAPER mode and remain disabled absent explicit future approval. Do not wire real order submission in this task. Keep PR #1 open/unmerged and original `Tradepro` untouched.


## Central broker-write boundary — deny-all foundation (18 October 2026)

- Added `backend/app/services/live_broker_write_service.py` as the single planned choke point for place/modify/cancel operations. This is intentionally a deny-all foundation: every write method raises `LiveExecutionBlocked` with an explicit no-request-sent message. It does not import or call a broker adapter, and it is not registered with routes, strategy workers, recovery, or any execution path.
- Added `backend/tests/test_live_broker_write_service.py` covering all three write verbs and asserting each fails closed. Commits: service `3726484932e4d46d9f92a7ff41cb5b761cfb1720`; tests `f4442607b8b71df7fffbf4354ea11a532efb99d6`.
- Verification pending at this note: the backend workflow for test commit `f4442607b8b71df7fffbf4354ea11a532efb99d6` has passed the broker-write source guard and is in pytest. See [run #39134040222](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39134040222). Do not claim tests/migrations passed until the run concludes.
- This does **not** complete the broker-write service. Next design must enumerate the persisted-intent lifecycle, ownership, user confirmation, account safety state, fresh pre-trade risk, token/connection stability, and timeout/recovery behavior before any adapter call can be implemented. Do not wire it or enable live orders. PAPER mode, disabled live submission, PR #1 draft/open/unmerged, and original `Tradepro` untouched remain mandatory.


## Central broker-write deny-all CI result — PASS (18 October 2026)

- GitHub Actions [run #39134040222](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39134040222) passed for test commit `f4442607b8b71df7fffbf4354ea11a532efb99d6`: broker-write source guard passed; full backend suite **440 passed, 5 skipped, 1 warning in 32.49s**; SQLite Alembic upgrade passed; PostgreSQL 16 Alembic upgrade passed; PostgreSQL safety/charge-adjustment concurrency tests **5 passed**. A separate workflow for the service-only commit also passed.
- The deny-all broker-write service remains deliberately unwired and makes no adapter calls. This step proves the central choke-point stub refuses place/modify/cancel; it does not verify live submission (which remains disabled) and is not a complete broker-write implementation.
- Documentation-only checkpoint commits followed. Next: inspect every existing order-writing entry point and add a call-graph/inventory, then design the central gate around ownership, persisted intent/idempotency, account-level safety latch, live pre-trade risk, explicit confirmation, and ambiguous timeout recovery. Keep PAPER mode, live submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.


## Broker-write path inventory and guard hardening — 18 October 2026

- Added `BROKER_WRITE_PATH_INVENTORY.md` documenting current adapter definitions, PAPER execution routes, read-only live preflight/recovery/reconciliation, and controls required before any live write is implemented. Commit `68f528edf4fe2dcb958161943b878b5863bbcd74`.
- Strengthened `backend/scripts/check_broker_write_boundary.py` to reject broker-write method references regardless of receiver name, rather than relying on adapter-like variable names. It now permits only the known PAPER `self.execution.place_order` calls in `strategy_execution_service.py` and the existing `ExecutionService(...).place_order/cancel_order` endpoints in `api/v1/portfolios.py`. The first strict run correctly exposed those two existing PAPER API call sites as exceptions that needed explicit, narrowly-scoped allowlisting; no live adapter write path was identified in those failures.
- Added guard tests for generic receiver bypass, central-service adapter-call rejection, and the approved PAPER call sites. Test updates are committed through `e9c31a043465e3d09223894ddfe45629cfc0302e`.
- CI for the latest guard/test fix is in progress: [run #39134878791](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39134878791). Do not treat this guard hardening as verified until the exact-head workflow passes. The preceding strict-guard failures were expected detection/allowlist gaps and prevented pytest/migration stages from running.
- Live broker writes remain unimplemented and denied by the central service. Keep PAPER mode mandatory, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.

## Central safety-preflight + durable intent composition — VERIFIED (18 October 2026)

- Added LiveOrderRecoveryService.persist_preflighted_intent(...). It accepts only a LiveOrderPreflight plan, verifies user/portfolio/instrument/broker and exact intent fields, rechecks the currently connected Upstox connection ID, then persists one stable PENDING_SUBMISSION LIVE intent with an opaque broker tag and portfolio-scoped idempotency key. It does not call a broker order endpoint.
- Updated LiveBrokerWriteService to expose prepare_order_intent(...): run LivePreflightCoordinator.preflight first (environment interlocks, explicit confirmation, ownership/instrument validation, persisted account safety latch, fresh read-only broker risk snapshots and account-wide risk gate), then persist the plan. If preflight fails, persistence is not attempted.
- Place/modify/cancel methods remain unconditional deny-all; this service does not send real orders and is not registered with routes/workers. PAPER-only ExecutionService is unchanged.
- Added tests for preflight-before-persistence, no persistence on denied preflight, exact plan matching, idempotent intent replay, and broker connection change after preflight.
- Verified GitHub Actions run #39136080295 on code/test SHA 27c4a4e5ed9fd9d864e38816c945e37371ee22f7: broker-write source guard passed; backend 448 passed, 5 skipped, 1 warning in 39.34s; SQLite migration upgrade passed; PostgreSQL 16 migration upgrade passed; PostgreSQL safety/charge-adjustment concurrency tests 5 passed.
- Code commits: recovery persistence 66675d34bee98cdc6c0f24388f4fb097e79348ac; central composition 4d8268ca86e08a36025182a8e46f43b18ba951e6; orchestration tests ab010e8106b02b182594c0a664df34647a234bdb; persistence tests 27c4a4e5ed9fd9d864e38816c945e37371ee22f7.
- Remaining: review persisted intent status transitions and duplicate/concurrent races, require account safety to be rechecked at any future submission boundary, and design broker-confirmed submission/recovery with ambiguous outcomes. No submit method is approved. Keep PAPER mode, live submission disabled, PR #1 draft/open/unmerged, and original Tradepro untouched.

## Post-preflight instrument revalidation — VERIFIED (18 October 2026)

- Hardened persist_preflighted_intent to re-read the instrument row after asynchronous broker snapshots and reject missing/inactive instruments or any instrument-key change since the preflight plan was produced. This closes the same time-of-check/time-of-use gap already covered for broker-connection identity.
- Added regression test mutating the instrument key after snapshot-plan creation; persistence is rejected and no LIVE Order row is created.
- GitHub Actions [run #39136563051](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39136563051) passed on code/test SHA c40689ac227ab56ca58993072112d6fd575aff46: broker-write source guard passed; backend **449 passed, 5 skipped, 1 warning in 32.68s**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL safety/charge-adjustment concurrency tests **5 passed**.
- Next: add concurrency/state-transition tests around persisted intent creation and submission-unknown marking. Any future submitter must recheck the account safety latch and independent interlocks immediately before network I/O. Actual place/modify/cancel remain denied and no live broker order request is enabled.

## Concurrent order-intent and submission-state checkpoint — VERIFIED (18 October 2026)

- Changed `LiveOrderRecoveryService.mark_submission_unknown` to use a SQL compare-and-set update restricted to tagged LIVE intents in `PENDING_SUBMISSION` or `SUBMISSION_UNKNOWN`. It reloads after commit and refuses to overwrite a concurrently written terminal/reconciled state. Repeated transition to `SUBMISSION_UNKNOWN` is idempotent.
- Added unit coverage for repeated `SUBMISSION_UNKNOWN` and refusal to transition a terminal `FILLED` order back into recovery.
- Added PostgreSQL independent-session concurrency tests for two simultaneous identical intent-persistence requests (exactly one durable Order row and shared ID) and two simultaneous `SUBMISSION_UNKNOWN` transitions (both return the same safe state). Updated `.github/workflows/backend-tests.yml` to actually execute `test_live_order_recovery_postgres.py`; this integration coverage was not included by the prior workflow.
- Verified GitHub Actions [run #39137705194](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39137705194), SHA `3626e0cdb8a5b7b3fe012fd00b07d2b7bc3bbe26`: broker-write source guard passed; backend **450 passed, 7 skipped, 1 warning**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL integration tests **7 passed** (including the two new order-recovery concurrency cases).
- Recovery lifecycle review: timeout, lookup failure, invalid response, no match, and identity mismatch remain review-required outcomes; the service never blindly retries a broker POST. Recovered broker IDs are identity mapping only and do not imply fill/accounting confirmation.
- Remaining: production-grade submit/modify/cancel remains intentionally unimplemented and denied. Before any future broker POST, implement a separately reviewed submission state machine that commits a unique submission claim, rechecks account safety and independent interlocks immediately before I/O, handles crash/timeout ambiguity via read-only recovery, and requires broker-confirmed state reconciliation. Keep PAPER mode mandatory, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.

## Submission-claim state separation — VERIFIED (18 October 2026)

- Added `SUBMISSION_CLAIMED` as a distinct, durable state before any future broker network I/O. `claim_submission_attempt` uses a SQL compare-and-set from `PENDING_SUBMISSION`; only one concurrent worker can win. This is a local database operation only and contains no broker write call.
- Read-only tag recovery now accepts `SUBMISSION_CLAIMED` as well as pending/unknown states, because a process crash after committing a claim cannot prove whether a request was sent. The recovery rule remains conservative: no-match, lookup error, malformed response or identity mismatch never authorizes an automatic resubmit.
- Added unit tests for one-time claim semantics and a PostgreSQL independent-session concurrency test requiring exactly one winner. Existing concurrent duplicate-intent and `SUBMISSION_UNKNOWN` transition tests remain enabled in the PostgreSQL CI step.
- Verified GitHub Actions [run #39138626298](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39138626298), SHA `b18841ff591eb943c25d3f85894d824923f2f371`: broker-write source guard passed; backend **451 passed, 8 skipped, 1 warning**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL integration tests **8 passed**.
- Safety boundary: this is state-machine groundwork only. No adapter place/modify/cancel call was added, no live submission route or worker was enabled, and no real order was sent. Before any future submitter is considered, require a dedicated reviewed protocol that rechecks the account safety latch and independent interlocks immediately before I/O, handles claim-crash ambiguity via read-only recovery, and only accepts broker-confirmed reconciliation. Keep PAPER mode mandatory, live order submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.

## Broker-account binding for recovery — VERIFIED (18 October 2026)

- Added nullable `orders.broker_connection_id` with FK/index and Alembic revision `202610180013`. New live intents persist the exact broker connection ID validated by preflight. Legacy rows are intentionally not backfilled because the currently connected account cannot prove which account was used originally.
- Read-only recovery now fails closed before calling order history if the original connection is missing, disconnected, or differs from the currently verified connection. Existing child mappings are reused only when connection ID, broker name, and stable tag match the persisted intent.
- Added regression tests proving a disconnected/original-connection mismatch and a legacy unbound intent produce `UNKNOWN_REQUIRES_REVIEW`, make no order-history call, create no child mapping, and never invoke a broker write. Migration runs are verified on SQLite and PostgreSQL 16.
- Verified GitHub Actions [run #39139728102](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39139728102), SHA `9cb7ab055a0cd55028f0001aa90d647f1518b667`: broker-write source guard passed; backend **453 passed, 8 skipped, 1 warning**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL integration tests **8 passed**.
- Remaining: this is still recovery identity binding, not broker submission. No place/modify/cancel network write is enabled. Any future submitter must perform a fresh account safety/interlock check immediately before I/O, commit and honor the single-winner claim, and route crashes/timeouts into read-only reconciliation. Keep PAPER mode mandatory, live submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.

## Fresh pre-submission interlock revalidation — VERIFIED (18 October 2026)

- Added `LiveOrderRecoveryService.validate_claimed_submission(user_id, order_id)` as a validation-only primitive for any future separately reviewed submitter. It requires `TRADING_MODE=LIVE`, `LIVE_ORDER_SUBMISSION_ENABLED=true`, a user-owned tagged LIVE intent in `SUBMISSION_CLAIMED`, the original still-connected broker connection, automated-entry enablement for strategy orders, and a positive `LiveAccountSafetyService.check_allowed` result.
- The method does not call a broker adapter and no current write method invokes it. It explicitly documents that a future submitter must still solve the race between this check and network I/O; this check alone is not a safe live-submit implementation.
- Added regression tests for disabled runtime submission flag, missing account-wide safety state, and disconnected original broker connection. The first CI attempt exposed a test-fixture reference error; that fixture was corrected and the latest run is green.
- Verified GitHub Actions [run #39140514552](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39140514552), SHA `9085d9fbdcc8ee2dd8baac6f5e73f92bd76cfa8b`: broker-write source guard passed; backend **456 passed, 8 skipped, 1 warning**; SQLite and PostgreSQL 16 migrations passed; PostgreSQL integration tests **8 passed**.
- Remaining: no actual broker order write is enabled. A future submitter must implement a race-safe final interlock protocol (e.g. coordinated safety-state lock/version and claim semantics), without holding unsafe database locks across network I/O, and must handle post-request crashes through read-only reconciliation. Keep PAPER mode mandatory, live submission disabled, PR #1 draft/open/unmerged, and original `Tradepro` untouched.


## Main-branch continuation note — 2026-10-21

The current main-branch checkpoint is summarized at the top of this file. Historical branch-specific findings and commit references below remain useful context, but the safety branch was not merged wholesale. For the latest Phase 2 status, follow `PROGRESS.md`, `HANDOVER.md`, `MASTER_ROADMAP.md`, and `AUDIT_REPORT.md`.


## Main-branch continuation note — 2026-10-21

The latest verified main-branch Phase 2 checkpoint is summarized at the top of this file. Historical branch-specific findings remain useful context, but the safety branch was not merged wholesale. See `PROGRESS.md`, `HANDOVER.md`, `MASTER_ROADMAP.md`, and `AUDIT_REPORT.md` for current lifecycle changes.


## Main-branch continuation note — 2026-10-21

The latest verified main-branch Phase 2 checkpoint is summarized at the top of this file. Historical branch-specific findings remain useful context, but the safety branch was not merged wholesale. See `PROGRESS.md`, `HANDOVER.md`, `MASTER_ROADMAP.md`, and `AUDIT_REPORT.md` for current lifecycle changes.


## Main-branch continuation note — 2026-10-21

The latest verified main-branch Phase 2 checkpoint is summarized at the top of this file. Historical branch-specific findings remain useful context, but the safety branch was not merged wholesale. See `PROGRESS.md`, `HANDOVER.md`, `MASTER_ROADMAP.md`, and `AUDIT_REPORT.md` for current lifecycle changes.
