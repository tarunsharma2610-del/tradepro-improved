# Tradepro Improved — Requirements Audit
Audit date: 2026-10-17
Audit target: `main` baseline plus the isolated safety branch where noted.
Original repository `Tradepro`: untouched.

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
