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
| Live order lifecycle | Partial; read-only status check foundation added | Adapter has broker `place_order`, `get_order_status`, `get_order_book`, `get_positions`, and `get_holdings` methods. The safety branch now stores optional broker order metadata and adds a read-only service to check a known LIVE order's broker status after ownership/session/order-ID validation. It validates any returned broker order ID and records the raw status without changing local FILLED/CANCELLED state or cash/positions. An authenticated read-only broker-status endpoint is now exposed for orders that already have a stored broker ID. Live placement is still absent; no automatic reconciliation of partial fills, cancellation, timeouts or restart recovery exists. | Build and review a separate live lifecycle; only map statuses and account for fills after verified payload contracts and reconciliation tests. Do not replace paper execution. |
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
1. Keep the fail-closed PAPER-only service guard until a separate, reviewed live service exists.
2. Complete strategy-position attribution and atomic paper-fill accounting; regression tests now cover both.
3. Finish supported instrument validation. Official Upstox docs confirm the public instrument JSON fields, but tick-size units, full derivative mapping, lot sizes and margin treatment still need verification before F&O can be enabled.
4. Add evaluation-level de-duplication for strategy scheduling; manual order UI idempotency keys are now wired and backend strategy-position guards prevent duplicate fills.
5. Add portfolio-wide exposure controls and a broker-error circuit breaker; distinguish paper controls from live controls.
6. Implement a separate live execution lifecycle only after Upstox/regulatory prerequisites, broker-side idempotency, partial-fill/cancel/timeout/restart reconciliation and an account-level kill switch are verified.
7. Fix remaining documentation drift and repeat backend tests, migration/data-backfill checks, frontend typecheck/build and staging verification after each relevant change.

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
