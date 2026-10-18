# Architecture notes

## Credential tiers — why almost nothing lives in `.env`

Everything sensitive the platform ever handles falls into one of three tiers:

**Tier 0 — bootstrap secrets (`.env`, irreducible).**
`POSTGRES_PASSWORD`, `SECRET_KEY` (JWT signing), `MASTER_ENCRYPTION_KEY`
(encrypts everything in Tier 1 and 2). These have to exist before the app
can even open a database connection or decrypt anything stored in it — you
can't put the key to the safe inside the safe. `setup.sh` generates all
three for you; you should never need to hand-type one. This is the only
tier that lives in a file.

**Tier 1 — platform-wide integration keys (admin Settings UI, DB-encrypted).**
WhatsApp Business token, Telegram bot token, AI provider key, News API
key. One value each, shared by the whole platform, set once by whoever has
`is_admin = true`, editable without redeploying. See
`app/services/platform_settings_service.py`.

**Tier 2 — per-user broker credentials (user Settings UI, DB-encrypted).**
Each user's own Upstox API key/secret/access token. This has to be
per-user regardless of the `.env` question — in a multi-tenant SaaS, a
single global broker credential wouldn't make sense once there's more than
one user trading under their own broker account. See
`app/services/broker_credentials_service.py`.

Tiers 1 and 2 use the same encryption (Fernet, keyed by
`MASTER_ENCRYPTION_KEY`) and the same rule: a value is never sent back to
the browser in full, only masked (`app/core/encryption.py:mask_secret`),
and a broker connection is never marked `is_connected` on the strength of
having *saved* credentials — only after a real, successful call to the
broker's API (`BrokerCredentialsService._verify_and_update`). That
distinction exists on purpose: an earlier project in this line
(TradeBot AI) showed demo data instead of live prices because a
credentials-related assumption didn't hold up in production, and the
"never present fake data as real" rule this project runs on takes that
lesson literally, not just as a policy statement — see
`tests/test_broker_credentials.py` for the regression test written
specifically against that failure mode.

## The shared order/position/execution model (Phase 2)

`Order`, `Position`, and `Execution` (`app/models/order.py`,
`position.py`, `execution.py`) are the one conceptual model manual
trading uses now and auto-trading, backtesting, and live trading will use
later — not three separate implementations that happen to look similar.
Concretely: `Order.execution_reason` is `"MANUAL"` today and will be
`"STRATEGY"` or `"BACKTEST"` later; `Order.strategy_id` is unused today
and populated starting Phase 3. Adding those phases means new rows with
different values in existing columns, not new tables or a rewrite of
`ExecutionService`.

`Position.quantity` is signed (positive = long, negative = short) on
purpose — see `app/services/position_math.py`. This is what lets the same
column represent an intraday short sale or, later, a written option,
without a separate short-position concept bolted on afterward.

`ExecutionService.place_order()` never fills against an invented price.
MARKET orders fetch a real LTP from the user's connected broker
(`BrokerCredentialsService.get_access_token` +
`BrokerAdapter.get_quote`); if there's no live connection or the quote
call fails, the order is REJECTED with a specific reason and recorded as
such — not silently skipped, not filled at a guess. This is the same
"never present fake data as real" principle from Phase 1's broker
`is_connected` handling, applied to fills.

## Transaction cost engine

`app/services/transaction_costs.py` is pure — no DB, no I/O, just Decimal
arithmetic — specifically so its rate table is the one place to update
when STT, exchange charges, SEBI fees, stamp duty, or Upstox's brokerage
schedule change (which they do, on a government/exchange timetable no
one controls; the F&O STT hike that took effect 1 April 2026 is a recent
example). The module docstring records which rates were independently
corroborated at implementation time (STT, SEBI fee, stamp duty) versus
which are best-effort approximations worth reconfirming (exchange
transaction charges, the exact Upstox delivery-brokerage figure).

Every cost component (brokerage, STT, exchange charges, SEBI charges,
stamp duty, GST) is stored on `Execution` individually, not collapsed
into one number — the spec calls for preserving gross P&L, transaction
costs, and net P&L as distinct, auditable figures, and that only works if
the components survive past the moment they're calculated.

## Automated strategy trading (Phase 3)

`Strategy` (`app/models/strategy.py`) is the "no-code builder" — every
field on it is something a plain form field sets: which instrument, five
indicator weights, entry/exit score thresholds, a trailing-stop
percentage, a daily loss limit. There's no drag-and-drop canvas, no rule
DSL to parse — that tradeoff was made deliberately over attempting a full
visual programming surface in this pass.

Three modules stay separate on purpose, mirroring how `transaction_costs.py`
and `position_math.py` stayed separate from `execution_service.py` in
Phase 2:
- `indicators.py` — five pure functions, each candle-series-in,
  bounded-score-out. Nothing about strategies or weights here.
- `strategy_engine.py` — combines those five scores into one composite
  score (weighted average) and turns a score into an ENTER/HOLD/EXIT
  decision. Nothing about the database or the broker here.
- `risk_engine.py` — its own module because the architecture rules list
  risk management as separate from strategies/backtesting. Phase 3's one
  rule (daily-loss kill-switch) lives here so Phase 4's backtester and any
  future live-trading path can call the same check rather than
  reimplementing it.

`strategy_execution_service.py` is the only place these get wired
together with real data and a real broker call, and it does that by
calling `ExecutionService.place_order()` — the exact function manual
trading in Phase 2 calls — with `execution_reason="STRATEGY"` and the
strategy's id. A strategy's fills get the same cost engine, the same
position accounting, the same "never fill at a fabricated price" rule
manual orders get, because it's not a second implementation.

The background worker (`app/worker.py`) is a second entrypoint into the
same backend image (`python -m app.worker` instead of `uvicorn
app.main:app` — see `docker-compose.yml`'s `worker` service), not a
separate codebase or a Celery deployment. It evaluates every active
strategy on a fixed interval during NSE market hours, with each strategy
getting its own DB session so one failing evaluation can't corrupt or
block the others in the same pass.

## Multi-tenancy

Every table that belongs to a user (`broker_connections`, and everything
Phase 2+ adds — portfolios, orders, positions) is queried through a
repository method that takes `user_id` as a required argument and filters
by it. There is no repository method anywhere that fetches one of these
rows by its own id alone. See
`app/repositories/broker_connection_repository.py` for the pattern to
follow when Phase 2 adds portfolios/orders/positions repositories.

## Broker abstraction

`app/brokers/base.py` defines `BrokerAdapter` — authentication, quotes,
historical data, WebSocket streaming, orders, positions, holdings.
`app/brokers/upstox/adapter.py` is the first (and only, for now)
implementation. `app/brokers/registry.py` maps a string key (`"upstox"`)
to an adapter instance; nothing outside `app/brokers/` imports
`UpstoxAdapter` directly. Adding Zerodha or Groww later is a new file in
`app/brokers/zerodha/` plus one line in the registry — the trading engine
(Phase 2+) never changes.

## Phase roadmap

Phase 1 and 2 are in this delivery. Rough shape of what comes next — each
phase gets its own review before the next one starts:

1. **Foundation** *(done)* — auth, multi-tenancy, broker
   abstraction, tiered credentials, migrations, Docker/Nginx.
2. **Core trading engine + manual paper trading** *(done)* — instruments
   (seed set + best-effort Upstox sync), multi-portfolio accounts with
   configurable virtual capital, the shared order/position/execution
   model, the transaction-cost engine (brokerage/STT/GST/SEBI/exchange
   charges/stamp duty), manual market and limit order placement against
   real live prices. Not yet in Phase 2: WebSocket streaming, TradingView
   charts, and auto-filling limit orders — see README known limitations.
3. **Automated strategy trading** *(done)* — no-code strategy builder
   (typed form, not a visual canvas), a five-indicator scoring engine
   (RSI, SMA crossover, MACD, volume spike, momentum — the same factors
   an earlier project, AlgoEdge, used), trailing stops, a standalone risk
   engine with a per-strategy daily-loss kill-switch, and a background
   worker evaluating active strategies every 5 minutes during market
   hours. Strategy entries/exits run through the identical
   `ExecutionService.place_order()` manual trading uses — see below.
4. **Backtesting** *(done)* — reuses the exact same scoring
   (`strategy_engine.py`), trailing-stop (`position_math.py`), and
   cost-calculation (`transaction_costs.py`) functions live trading and
   strategies use, walked forward bar-by-bar over real historical candles
   instead of live broker calls, with a slippage assumption added since a
   backtest has to simulate market friction a live fill wouldn't need
   simulated. Runs as a standalone, user-scoped analysis tool — never
   touches a real portfolio's cash or positions.
5. **Intelligence layer** *(done)* — AI trading assistant grounded in
   real server-assembled context (never its own database access),
   market-news intelligence via RSS with ticker-and-company-name
   matching, Telegram notifications (linking + trade alerts), WhatsApp
   notifications (same hook, heavier real-world setup burden). See below.
6. **Analytics, polish, live-trading safeguards** *(done)* — portfolio
   analytics (realized P&L, win rate, cash-balance-over-time chart,
   honestly labeled as realized-only) and strategy comparison, an admin
   panel wired to Phase 1–5's previously API-only endpoints, per-user
   rate limiting on order placement and the AI assistant, and a full
   live-trading safeguards review grounded in current SEBI regulation —
   see `LIVE_TRADING_SAFEGUARDS.md`. Broader broker support (Zerodha,
   Groww) remains unimplemented; the `BrokerAdapter` interface from
   Phase 1 was built to make that additive when it happens.

## Backtesting (Phase 4)

`backtest_engine.py` is the walk-forward loop, and nothing else — every
calculation inside it is a function imported from somewhere else that
Phase 2 or 3 already built and tested: `compute_score`/`decide`
(`strategy_engine.py`), `check_trailing_stop`/`apply_fill`
(`position_math.py`), `calculate_costs` (`transaction_costs.py`). The
loop's only genuinely new logic is the bar-by-bar walk and
`_apply_slippage` — a backtest has to simulate the market friction a real
fill already reflects on its own. `backtest_service.py` fetches real
candles via the same `BrokerAdapter.get_historical_data` call and the
same `candle_parsing.py` module `strategy_execution_service.py` uses (not
a second parser), then persists what the pure engine returns.

`BacktestRun`/`BacktestTrade` are deliberately their own tables,
user-scoped rather than portfolio-scoped — a backtest is a what-if
analysis, and letting it write into a real `Portfolio`'s `cash_balance`
or `Position` rows would let a simulation corrupt real trading history.
Reusing the calculation logic (the architecture rule) and reusing the
storage (which the rule doesn't ask for, and which would be actively
harmful here) are different things.

## Intelligence layer (Phase 5)

Three genuinely separate concerns share the word "notification," and it's
worth keeping them separate in your head the way the code keeps them
separate in modules:

- **News** (`news_parsing.py` pure, `news_service.py` fetch/persist) —
  RSS ingestion, deduplicated by link, tagged by matching both an
  instrument's ticker AND a cleaned version of its company name against
  each article's title/summary. That second matching key isn't
  precautionary — testing against a genuinely live-fetched Business
  Standard headline ("ICICI Bank raises fresh $750 million") showed the
  exact ticker "ICICIBANK" never appears in real prose, only the company
  name does. Ticker-only matching would have silently tagged almost
  nothing.
- **AI assistant** (`ai_assistant_service.py`) — the model gets a
  server-assembled context block (real positions, real recent orders,
  real tagged news for held instruments) appended to the question, and
  nothing else. It has no tool access, no database connection, no way to
  look anything up on its own — the same "never present fake data as
  real" principle applied to an LLM, where the failure mode is
  plausible-sounding fabrication rather than an obvious bug.
- **Telegram / WhatsApp** (`telegram_notifier.py`, `whatsapp_notifier.py`,
  unified behind `notification_service.py`) — both are thin, verified
  wrappers around their respective platforms' current APIs. Telegram
  linking is a deep-link + `/start <code>` handshake, completed by the
  worker polling `getUpdates` rather than requiring a public webhook
  (this app doesn't have HTTPS configured yet — see known limitations —
  so a webhook wasn't a realistic Phase 5 option). `notification_service.py`
  is deliberately fire-and-forget from the caller's side: a channel
  failing (not configured, API error) never blocks or fails the trade
  that triggered it — notifications are a side effect of trading, not a
  precondition for it.

## Trading-mode safety

`TRADING_MODE` (`PAPER` / `LIVE`) is an environment variable, not a
database row or an API-settable value — flipping it requires editing the
environment and redeploying. That's deliberate: it means no bug, no bad
default, and no compromised admin session can turn live trading on by
itself. It stays `PAPER` through every phase above until live trading is
explicitly implemented and reviewed, per the project's own ground rules.

That review happened in Phase 6, then got more precise after a
follow-up question — see `LIVE_TRADING_SAFEGUARDS.md` for the full,
current analysis. The short version: India's retail algo-trading
framework (mandatory for all brokers since 1 April 2026) exempts
personal/family automated trading under a 10-orders-per-second threshold
from formal exchange registration — but that exemption is specifically
for *your own* trading, not for offering a strategy to other people.
Since this is a multi-tenant SaaS platform built around other users
running strategies, live trading for anyone but the platform's own
operator falls into "providing an algo to other traders," which needs
broker-mediated exchange registration regardless of how low any one
user's order frequency is. Nothing in the codebase currently acts on
`LIVE` even when set.


## Broker trade intake and accounting boundary

The `BrokerTradeIngestionService` stages validated broker-confirmed trade rows in `broker_trade_records`, uniquely scoped by broker connection and broker trade ID. It requires a LIVE local order, tenant ownership, a mapped broker child order bound to the owner's broker connection, and consistent side/instrument/quantity/price fields. This is an ingestion ledger only: it does not create `Execution` rows, update order status or child fill aggregates, or change cash, positions or P&L. Live accounting must be a separate atomic reconciliation step that handles actual costs and partial fills; the paper `ExecutionService` must never be reused for broker fills. Migration verification for this addition remains pending.


The connection-scoped broker identity migration includes legacy-link backfill logic and a populated-data regression test. Current-head test/migration verification is pending; do not treat the migration as deployment-verified until CI passes.


### Intake identity hardening — 18 October 2026

The staging service resolves the broker connection by the exact `BrokerOrder.broker_connection_id` and confirms the connection owner and broker match the request and child-order record. Missing or foreign bindings fail closed. A staged trade must include a non-empty instrument token matching the local instrument key; absent identity is not treated as safe. This remains a staging-only path, with no execution-accounting mutation or live submission wiring. Current-head tests/migrations remain unverified.


Legacy child orders whose broker connection cannot be identified remain unbound and are intentionally rejected by trade intake. Regression test added in `264aa4c609d522cd01d07e8213bfee6f14c7a2bf`; current-head test/migration verification remains pending.


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


## Architecture verification note — 18 October 2026

The reconcile-before-promote architecture already exists in `LiveOrderFillReconciliationCoordinator`; this continuation did not add a duplicate coordinator or alter runtime registration. Commit `b5783d421f64fcb8e7f1d75f1af5185fd9029f59` adds integration coverage that composes the existing child reconciler, durable trade intake, promotion and accounting services. Broker status/trade reads and charge estimation are mocked. CI verification for the test commit remains pending and must be checked before claiming success. Live order submission remains disabled.
