## Phase 3 exact-head CI checkpoint — 22 October 2026

- Backend CI passed on commit `1fcbb06a78fd06226f0e0e6438cf72b422dc2d4e`: **563 passed, 1 warning**. Broker-write boundary guard, SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks, and the isolated synthetic database/document-volume restore drill all passed.
- This result validates that code commit only. Documentation changes require exact-head CI again.
- Synthetic restore evidence does not prove recovery of real Oracle Free Cloud data or authenticity of a real broker contract note.
- PR #6 remains draft and unmerged pending accounting/idempotency review and explicit user approval. Live broker writes remain disabled.
- Real contract-note and retained real-backup/restore evidence remain pending; the user plans to provide these later.
- Repository scope is `tarunsharma2610-del/tradepro-improved` only. Do not modify the original `tarunsharma2610-del/Tradepro`.

## Current Phase 3 checkpoint — 21 October 2026

- **Latest verified code/test HEAD:** `3963c2bf4e6ffe2bb33d327b10e2995cd243d003`. Exact-head [Backend CI run 39607630055](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39607630055) passed **484 tests, 1 warning in 29.34s**; the broker-write boundary guard passed, and SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed.
- New Phase 3 guard: broker-reported live-fill charge references are trimmed for storage and rejected when longer than the `Execution.charge_reference` 200-character column limit. This prevents a predictable storage error from being misreported as a concurrent promotion conflict. Regression coverage is included in the 484-test result.
- The existing Phase 3 safety gates remain active: replay must match the accounted fill and exact charge evidence; only broker-reported, internally consistent charges with a non-empty audit reference are accepted; durable staged trade quantities must match broker-confirmed child fills before promotion; exchange-time ambiguity/out-of-order fills fail closed; paper positions and cash remain isolated.
- **Phase 3 remains in progress, not complete.** Remaining review includes coordinator/identity boundaries, charge provenance/allocation semantics, full partial-fill and crash/restart acceptance criteria, and any explicitly selected bridge design. Keep `BrokerFillIdentity` separate from manual `BrokerTradeRecord` unless a reviewed Phase 3 design explicitly authorizes a narrow bridge.
- Live broker submission, automatic accounting promotion, and automatic scheduling remain disabled. The original `tarunsharma2610-del/Tradepro` repository remains untouched. Phase 2 remains closed.
- This checkpoint describes the verified code commit above. The documentation synchronization commit will trigger its own CI; do not treat that documentation commit as green until its exact-head run passes. Older checkpoint entries below are historical audit trail, not current status.

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

<!-- Authoritative checkpoint audit: 2026-10-21; supersedes older status notes below. -->
## Historical checkpoint audit — 21 October 2026 (superseded)

- **Repository/branch:** `tarunsharma2610-del/tradepro-improved`, `main`. The original `tarunsharma2610-del/Tradepro` repository is a protected baseline and must remain untouched.
- **Latest repository HEAD before this audit update:** `a297b1a356c133aaca0ed10079eb5226c03b747b` — documentation-only commit `docs: synchronize Phase 2 status with passing CI evidence`.
- **Latest code/test commit:** `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`. Recorded exact-commit backend CI run [39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration cycles. Frontend run [39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript and Next.js build.
- **Previously verified documentation CI:** commit `6407c5a05865c1be0ef673d3bb5e71c0231ef8da`, run [39556816828](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556816828), backend job completed successfully. The later documentation-only commit `a297b1a356c133aaca0ed10079eb5226c03b747b` was found on `main`; CI for that exact HEAD was not independently established before this audit update. Do not infer exact-head CI success from an earlier commit.
- **Phase 2 checkpoint verified in project records:** atomic run/lease finalization; stale-owner protection; cancellation and interrupted-run recovery; inconsistent lease token/expiry rejection; five-record renewal boundary; and incomplete-summary warnings for `WORKER_INTERRUPTED` and `LEASE_LOST`.
- **Historical audit disposition — superseded:** slow database persistence and high-volume lease-expiry/renewal races are now tested and passed in CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386).
- **Safety constraints remain:** no real broker orders in tests; live broker submission, automatic accounting promotion, and automatic scheduling remain disabled; keep `BrokerFillIdentity` separate from `BrokerTradeRecord`; do not wholesale-merge the divergent safety branch.
- Older checkpoint entries below are retained as history, not current instructions. This top section is the authoritative current state. After this documentation commit, verify CI for its exact HEAD before treating the checkpoint audit as fully closed.

<!-- Latest verified status, updated 2026-10-21 -->
> **Latest verified checkpoint — 21 October 2026**
>
> - Repository: `tarunsharma2610-del/tradepro-improved`; branch: `main`. Original `Tradepro` repository remains protected and untouched.
> - Latest code/test commit: `14995e5b41b3014b7de9d50a8466ac1cce4a77e6`. Backend [CI run 39554328380](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328380) passed **466 tests, 1 warning**, broker-write boundary guard, and SQLite/PostgreSQL 16 migration checks. Frontend [CI run 39554328474](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39554328474) passed TypeScript and Next.js build.
> - Documentation audit commit `6407c5a05865c1be0ef673d3bb5e71c0231ef8da` passed [CI run 39556816828](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39556816828).
> - Phase 2 checkpoint complete through atomic run/lease finalization, stale-run and cancellation recovery, lease-loss fencing, five-record renewal, and incomplete-summary warnings.
> - **Historical next-task note — completed:** the slow-persistence lock test and 20-round concurrent expiry-boundary renewal/reclaim regression passed in CI run [39567242386](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39567242386).
> - Deferred safety-branch work remains tracked in `SAFETY_BRANCH_PORT_MATRIX.md`; no wholesale branch merge. Keep live broker submission and automatic accounting promotion disabled. Keep `BrokerFillIdentity` separate from `BrokerTradeRecord`.
>
> The CI status above refers to the stated code and documentation commits. This documentation refresh will create a new commit and trigger its own CI run; do not call that new run passed until GitHub reports success.

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


## Live order idempotency and reconciliation (Phase 1 storage implemented; live execution not implemented)

The live order path is a separate future workflow, not a mode switch on the current paper execution path. `ExecutionService.place_order()` creates PAPER orders; preserve that boundary and its regression test.

Reviewed design and implementation gates live in [`LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`](LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md). Core invariants:

- Persist a client intent, canonical request hash, risk decision, audit event and transactional dispatch/outbox record before any broker POST. Scope the unique idempotency key to the authenticated user and broker connection. Same key + same payload returns the existing intent; same key + different payload is a conflict.
- A local database cannot make an external broker POST exactly-once. If the network times out or the process crashes after a request may have reached Upstox, mark the outcome unknown and reconcile before any further submission. Never blindly retry an ambiguous POST.
- Upstox order tags support correlation/history lookup; do not assume they are broker-enforced idempotency tokens. Match by documented account/order attributes and tag, and freeze on multiple or mismatched matches.
- Persist broker order IDs and normalized status transitions. Treat broker acceptance as distinct from execution. Deduplicate individual fills by stable broker trade identity and reconcile partial fills/cancel races against broker trade records.
- Recheck risk and account-level kill switch at dispatch time. Unknown/pending intents reserve exposure until resolved. Paper execution must remain structurally unable to call the live placement method.
- Add schema only through reviewed additive migrations, test clean SQLite and staging copies of the deployed DB engine, and never migrate production during implementation.

Phase 1 includes durable idempotency schema and repository safeguards, including rejection of credential-like keys in persisted snapshots/audit details. Phase 2 now includes a pure Upstox order-status normalizer and a pure intent matcher. The matcher scopes candidates to one broker connection; uses an existing broker order ID or one exact correlation tag; and requires instrument, side, order type, quantity, product and applicable price fields to match. Multiple tag matches, economic mismatches, cross-connection candidates and unknown/contradictory observations are not auto-linked. The matcher performs no network calls. The repository now exposes a versioned reconciliation transition that updates an intent and appends a safe audit event in one transaction, rejects invalid regressions and stale versions, and treats repeat same-state observations as no-ops. No helper fetches broker data. A pure Upstox trade normalizer and repository-only `record_broker_fill()` now validate and persist individual broker trade identities idempotently; when linked to an intent, fill + audit event are atomic. Linked fills must match the already-associated broker order ID and intent instrument/side/product/order type; quantity ceilings and limit-price protection are checked before persistence. Previously unmatched fills can be linked later with account/order/economic checks and an atomic audit event. The read-only worker now exists in `app/services/live_order_reconciliation_worker.py`. It receives only `UpstoxReadOnlyReconciliationClient`, validates the user-owned Upstox connection and usable token, uses a durable per-connection lease, reads the order book and daily trades, retries only bounded read-only transient failures, and persists validated fill identities/status audit. It is not scheduled or wired to an API route, and current tests use mocks. There is no aggregation into Order/Execution/Position/cash/P&L and no live submission service. Keep live submission disabled. Official Upstox order-history/order-book/trade endpoints and links are documented in `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`.


## Roadmap and delivery gates
The ordered delivery sequence and evidence requirements are maintained in [ROADMAP.md](ROADMAP.md). This architecture document describes component boundaries; the roadmap is the source of truth for phase ordering and release gates. Phase 1 storage/repository implementation is CI-tested; Phase 2 has CI-tested order/trade normalization, strict matching, versioned status persistence, and individual fill identity persistence. Broker reads, a worker, partial-fill aggregation/accounting and live submission remain unimplemented. Live submission remains unimplemented.


## Out-of-order broker status and fill evidence — 2026-10-17
`resolve_order_state_with_fill_evidence()` combines the latest observed order state with deduplicated persisted fill quantity. Persisted full requested quantity resolves to `FILLED`; partial trades override stale active statuses to `PARTIALLY_FILLED`; partial trades plus cancellation become `PARTIALLY_FILLED_CANCELLED`; partial trades conflicting with `FILLED` or `REJECTED`, invalid quantity totals, and unknown conflicts become `RECONCILIATION_REQUIRED`. `LiveOrderRepository.apply_reconciliation_transition()` records both observed and resolved states plus the fill evidence count in its audit event. This remains repository/service logic only: no Upstox API reads, worker, or accounting updates exist. The next worker boundary is specified in [READ_ONLY_RECONCILIATION_WORKER_DESIGN.md](READ_ONLY_RECONCILIATION_WORKER_DESIGN.md).


## Read-only Upstox reconciliation client — 2026-10-17
`app/brokers/upstox/reconciliation_client.py` is a separate narrow client with fixed GET-only methods for order book, details, history and per-order trades. It has no place/modify/cancel methods and returns sanitized error categories rather than raw upstream error bodies. Contract tests use a mocked HTTP client; they do not make real Upstox requests. Exact test checkpoint [run 39056868434](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056868434) passed 309 tests, 1 warning. The worker implementation is present but not scheduled or wired to an API route. It validates connection ownership/token usability, applies bounded retry and a lease, and uses durable matching. CI mocks do not verify live account behavior; no real broker request has been made.


## Reconciliation worker lease — 2026-10-17
`LiveReconciliationLease` stores one lease per broker connection. `LiveReconciliationLeaseRepository` claims by compare-and-set, permits reclaim only after expiry, supports renewal only for the current unexpired token, and token-guards completion so an expired/stale worker cannot clear a newer lease. Alembic revision `202610170003` adds the table and CI verifies upgrade/downgrade/re-upgrade on SQLite and PostgreSQL 16. The lease is a foundation only; no worker invokes it yet.


## Read-only worker implementation — 2026-10-17
`LiveOrderReconciliationWorker` is an explicit on-demand service, not a scheduled background task. It validates connection ownership, Upstox broker identity and connection readiness before claiming the lease; retrieves a usable unexpired access token through `BrokerCredentialsService`; reads order book and daily trades through the fixed GET-only client; and uses bounded retry for 429/5xx/network/timeout responses. It normalizes and persists daily trade identities as unmatched, then matches order observations to one local intent and links fills only after repository economic/account checks. Missing fill evidence for a broker `complete` status leaves the intent `UNKNOWN`; later trade evidence can resolve it. The worker does not expose broker write methods and does not update accounting models. Mocked tests and PostgreSQL lease-claim concurrency passed in CI; no live Upstox request or production migration occurred. Remaining constraints: no scheduling/API trigger, no historical-day pagination/window logic, and no durable operator-facing run summary/manual-review queue.


## Durable reconciliation run summaries — 2026-10-17
`LiveReconciliationRun` records one row for each worker pass that acquires the per-connection lease. It stores owner/connection scope, start/completion timestamps, a finite status set, sanitized error category, and a whitelist of numeric counters only. `LiveReconciliationRunRepository` refuses unknown counter keys, negative/non-integer values, and unsafe error strings. Migration `202610170004` is reversible and tested on SQLite and PostgreSQL 16. The worker persists `RUNNING` before broker reads and a terminal result after releasing the lease. A process crash can leave a durable `RUNNING` row; detecting and presenting stale runs and manual-review issues is the next step. No raw broker body, credential or exception text is persisted.


## Durable manual-review issue records — 2026-10-17
`LiveReconciliationIssue` stores owner/connection scope, optional run/intent links, a whitelisted issue type, a SHA-256 fingerprint, broker order/trade IDs when safely normalized, `OPEN`/`RESOLVED` state, safe details, first/last-seen timestamps and occurrence count. The repository validates ownership, bounds the JSON details, rejects credential-like keys, deduplicates repeated occurrences per broker connection and reopens an issue if it recurs after resolution. The worker records issues instead of persisting raw broker rows or exception strings. Migration `202610170005` is CI-tested on SQLite/PostgreSQL 16. This is database persistence only: no operator UI/API or resolution endpoint exists yet.


## Owner-scoped reconciliation read API — 2026-10-17
`GET /api/v1/reconciliation/runs` and `GET /api/v1/reconciliation/issues` are authenticated read-only endpoints. They use `get_current_user`, filter every query by the authenticated `user_id`, support optional connection/status/type filters, and cap responses at 100 rows. Pydantic schemas expose only safe run counters and issue metadata/details, not raw broker records or credentials. Cross-user and unauthenticated route tests passed in [run 39060230705](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060230705), 345 passed, 1 warning. There is no API to trigger reconciliation or resolve issues; those are separate reviewed changes.


## Reconciliation review UI — 2026-10-17
The dashboard links to `/reconciliation`, which reads only the owner-scoped `/api/v1/reconciliation/runs` and `/api/v1/reconciliation/issues` endpoints. It displays recent run counters, sanitized issue details and OPEN/RESOLVED filtering. It has no worker-trigger, issue-resolution or order-write controls. Exact commit `e4343dcb225c1f332b6c89399694d0a29a5df739` passed the frontend TypeScript/Next.js build and backend CI (345 passed, 1 warning). The page is UI-only and does not prove broker reconciliation has been run against a real account.


## Live-fill accounting recovery and verification — 2026-10-20

The deleted service, original tests and migration 0008 are restored to their original paths. Supporting models `BrokerOrder`, `BrokerTradeRecord`, `LivePosition` and migrations `202610180006` / `202610180007` were added to complete the chain. GitHub Actions [run 39475387511](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39475387511) passed **355 tests, 1 warning**, plus SQLite and PostgreSQL 16 migration upgrade → downgrade → re-upgrade checks at code/test checkpoint `a906274b98f3f7e0c913f376128f4996b996c52b`.

This is not a complete live-fill pipeline: the service remains unregistered, ingestion and reconciliation integration remain outstanding, and no real-account or production migration was performed. Keep live order submission disabled. Continue Phase 2 reconciliation release gates and crash/recovery/fill-linkage checks. Do not delete the recovered files without explicit user approval.


## Current live-order reconciliation versus manual-fill staging boundary — 2026-10-21

The codebase currently has two isolated models of broker trade evidence; do not conflate them:

1. The intent-based workflow uses `LiveOrderIntent` and `BrokerFillIdentity`. `LiveOrderReconciliationWorker` reads through the fixed GET-only Upstox client, links validated fills to intents, and records safe status/audit evidence. It does not mutate the shared `Order`, `Execution`, `Position`, `LivePosition`, or portfolio cash accounting path.
2. The manual Order-based staging workflow uses `BrokerOrder` and `BrokerTradeRecord`. `BrokerTradeIngestionService` stages broker-confirmed trades, and `BrokerChildOrderReconciliationService` validates aggregate staged trade quantity/weighted average price against broker order details before updating only child status and filled quantity. The parent `Order` and accounting are deliberately unchanged.
3. `LiveFillAccountingService` promotes a `BrokerTradeRecord` only with explicit broker-reported charges. It remains unregistered; its per-child aggregate guard prevents already-accounted plus new fill quantity from exceeding the broker-confirmed child fill total.

Before integrating these paths, decide whether they are separate supported workflows or require a common lifecycle. Do not dual-write or translate records without transaction-safe idempotency, account/intent linkage, conflict semantics, and replay/rollback tests. Current code/test checkpoint [run 39481385581](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39481385581) passed 438 tests, 1 warning, with SQLite/PostgreSQL 16 reversible migration checks. The worker and staging services are not scheduled or wired to automatic live execution; no real broker order was placed.


## Parent-order lock guard — 2026-10-21

After broker status I/O, child reconciliation locks/revalidates the owned parent Order, verifies LIVE mode and the pre-network instrument/side/quantity snapshot, then locks the BrokerOrder child before reading staged trade totals. This matches ingestion's parent→child lock order and blocks stale responses after a local order mode/economic change. A regression test switches the order to PAPER during the status read and confirms child state remains unchanged. Exact-head [run 39482592808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39482592808) passed **439 tests, 1 warning**, with SQLite/PostgreSQL 16 reversible migrations. No parent accounting or live submission is enabled.


## Explicit fill-workflow boundary decision — 2026-10-21

Decision: keep the intent-based reconciliation evidence path and manual-order trade staging/accounting path separate for this Phase 2 slice. The worker persists `BrokerFillIdentity` under `(broker_connection_id, broker_trade_id)` and links it to a `LiveOrderIntent` only after validated order matching. The manual Order path persists `BrokerTradeRecord` linked to `BrokerOrder`, with separate charge-validated accounting promotion. They currently have independent uniqueness constraints; the database does not provide cross-table deduplication.

Do not dual-write, copy, or promote one model into the other. Before a future bridge, define one canonical broker-fill identity, deterministic conflict handling when the same broker trade appears in both tables, owner/connection/intent/order linkage, transaction boundaries, idempotent replay, rollback, and crash recovery. The worker must remain read-only with respect to broker APIs and must not mutate `BrokerTradeRecord`, `Execution`, `LivePosition`, or portfolio cash. Regression coverage now enforces that boundary. No broker submission or automatic promotion is enabled.

## Reconciliation run crash-recovery boundary — 2026-10-21

`LiveReconciliationRunRepository.fail_orphaned_runs` is an explicit maintenance primitive for stale `RUNNING` run summaries. It is scoped to one user and broker connection and will not alter runs if that connection has an unexpired lease. It only records a terminal failure category and completion timestamp; it never invokes the broker, retries a request, links fills, or updates accounting. The method is not scheduled automatically. Callers must supply a timezone-aware stale cutoff; SQLite-loaded lease timestamps are normalized as UTC before Python comparisons.

## Phase 3 live-fill accounting checkpoint — 2026-10-21

- Latest reviewed code HEAD at this checkpoint: `ef60ec93d39543c644dfd557f6f73b48ab793b60`.
- Exact-head [Backend CI run 39609474410](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39609474410) completed successfully: **485 passed, 1 warning in 30.25s**; broker-write boundary guard passed; SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed.
- The one warning is non-failing; CI logs also report GitHub Actions Node.js 20 deprecation notices.
- Existing safeguards cover replay identity/charge validation, broker-confirmed fill quantities, cumulative child/order quantity limits, rejected-order protection, and atomic live-position/execution updates. This CI result verifies the current HEAD, not completion of all Phase 3 requirements.
- **Open Phase 3 requirement:** define and test the fee-allocation contract when a broker contract-note charge total covers multiple fills. The current API accepts a per-promotion breakdown and validates that its total equals its six components; it does not itself establish how a multi-fill contract-note total is allocated. Do not claim this issue resolved or wire in a coordinator/identity bridge until the rule is designed and regression-tested.
- Safety constraints unchanged: do not enable live broker submission, automatic accounting promotion, or automatic scheduling; keep `BrokerFillIdentity` and `BrokerTradeRecord` separate pending a reviewed bridge design. Phase 2 remains closed.
