# Live Trading: Safeguards Design (Not Implemented)

This document is the "reviewed design" the original spec calls for before
live trading is ever built -- it is analysis and recommendations, not
code, and nothing in this delivery places or can place a real order.
`TRADING_MODE` stays a bootstrap environment variable, defaulting to
`PAPER`, checked nowhere in the order-placement path except to log a
warning -- see `app/core/config.py` and `app/main.py`.

**This is engineering analysis based on publicly available regulatory
information, not legal advice.** I'm not a lawyer or a compliance
professional. Before building or enabling any part of live trading,
verify the regulatory points below directly with Upstox (or whichever
broker you'd use) and, ideally, a SEBI-registered compliance
professional -- particularly the personal-use-vs-platform distinction
below, since that's the one place a wrong assumption could create real
legal exposure for a multi-user product specifically, not just a coding
mistake.

*Revised after a follow-up question surfaced a more precise regulatory
picture than the first pass had -- see "The order-frequency threshold"
and "The distinction that actually matters here" below, which meaningfully
refine (not just restate) what this document originally said.*

## The regulatory reality (checked live, August 2026)

SEBI's retail algorithmic trading framework (circular
SEBI/HO/MIRSD/MIRSD-PoD/P/2025/0000013, February 2025) became **mandatory
for all stockbrokers on 1 April 2026** -- already in effect as of today,
not an upcoming deadline. The picture is more layered than "every
automated order needs registration," and the layering matters a lot for
what this specific platform is.

### The order-frequency threshold

SEBI set a 10 orders-per-second (OPS) threshold, measured per exchange
per client. Below it, you're treated as a "regular API user," not a
registered algo trader -- no formal exchange registration or algo
approval process required. Above it, mandatory registration applies
regardless of anything else. This is well corroborated across multiple
independent sources, including brokers' own compliance explainers.

This platform's strategy engine evaluates every 5 minutes and places, at
most, a handful of orders per pass -- nowhere close to 10 orders *per
second*. On frequency alone, it would sit comfortably under the
threshold.

One wrinkle even here: orders below the threshold still get tagged with
a generic algorithm ID by the exchange for tracking purposes, even
without the full registration process. "No registration needed" means
no formal approval step is required -- not that the activity is
untracked.

### The distinction that actually matters here: personal use vs. offering it to others

The sub-10-OPS exemption is specifically for **your own personal or
immediate-family trading** (self, spouse, dependent children, dependent
parents) -- not for a strategy offered to other people. The moment an
algorithm is made available to *other* users, that's "distributing an
algo to other traders" in SEBI's framing, and it requires broker
empanelment and exchange registration **regardless of order frequency.**
At least one major broker's own compliance explainer states this
distinction directly: personal automated use can stay under the
threshold-based exemption; selling or providing a strategy to others
needs the full broker-partnership path no matter what the OPS number is.

This is the fork that actually matters for this codebase. It's a
multi-tenant SaaS platform -- the entire design (per-user portfolios,
per-user broker connections, a strategy builder any user can configure
and activate) is built around *other people* using it, not just one
person's own account. Concretely:

- **You running the strategy engine on your own account only**:
  plausibly the lighter path -- no formal exchange algo registration,
  just the technical requirements below.
- **Any other user on this platform running the strategy engine live**:
  needs real broker-mediated registration and exchange empanelment,
  because that's "providing an algo to other traders" -- and that
  categorization doesn't care how low any individual user's order
  frequency is. A hundred users each trading well under 10 OPS does not
  average out to "regular API use" once it's a platform serving them.

### White Box vs. Black Box, if registration is ever pursued

SEBI also classifies algos as **White Box** (transparent, disclosed,
rule-based logic -- e.g. "buy if RSI < 30") or **Black Box**
(proprietary/hidden logic, which requires the provider to hold a SEBI
Research Analyst license and disclose performance metrics). This
platform's strategy engine -- a disclosed, deterministic weighted
combination of five named indicators against a visible threshold -- reads
as White Box as built, which multiple sources describe as the easier,
faster registration track if that's ever pursued. Worth confirming with
Upstox directly rather than assuming, but it's a favorable starting
point, and not a coincidence: the "auditable, not a black-box model
call" design choice made throughout this project (the same reasoning
behind news instrument-matching using visible keyword rules instead of
an opaque model call) happens to line up with what SEBI treats as the
lower-friction category here too.

### Confirmed technical requirements (apply broadly to API trading, not just registered algos)

These showed up consistently enough across sources to treat as settled,
not speculative:

- **Static IP whitelisting** -- the broker only accepts API requests
  from a pre-registered static IP, not from anywhere.
- **OAuth-based authentication only** -- already how this platform's
  Upstox integration works (see `app/brokers/upstox/adapter.py`), so
  this one's already aligned.
- **Mandatory 2FA on every API session.**
- **Automatic session logout at the end of each trading day** -- no
  continuous, indefinite API sessions.

Three of these four aren't built into this platform today. None of them
are optional extras -- they read as baseline requirements for any real
order-placing API use, personal or platform-provided, independent of the
registration question above.

## Engineering safeguards (needed regardless of which category)

None of this exists yet either. In rough order of "must exist before the
first real order, no exceptions":

- **A hard, code-level gate independent of any user-facing toggle.**
  `TRADING_MODE` already exists for this -- the requirement is that
  enabling live trading means changing an environment variable and
  redeploying, never an API call, never a database row, never something
  a compromised session or a UI bug could flip.
- **Explicit, specific, repeated confirmation.** Not a checkbox once --
  something closer to re-entering a password or MFA code before *each*
  live order, or at minimum each session, with the real amount and
  instrument shown plainly. Paper trading can afford to be frictionless;
  this should not be.
- **Server-side position and loss limits that don't trust the client.**
  Max order size, max position size, max daily loss -- enforced in the
  same place `ExecutionService` already enforces cash sufficiency, not
  as a frontend warning that a direct API call could skip.
- **A kill switch reachable outside the normal trading flow.** A
  "disable all live trading for this account, right now" action that
  works even if the strategy/order UI itself is broken or the frontend
  hasn't loaded -- this matters exactly when things are already going
  wrong.
- **Real reconciliation against the broker's own records, not the
  platform's internal ledger.** Paper trading can trust
  `position_math.apply_fill`'s output as ground truth because it *is*
  the ground truth -- there's no external system to disagree with. Live
  trading cannot: `Position` and `Order` rows would need to be checked
  against `BrokerAdapter.get_positions()` / `get_order_status()`
  regularly, and any mismatch should halt further live activity on that
  account until resolved, not be silently trusted.
- **Idempotent order submission.** A network retry, a double-click, or a
  timeout-then-resend must never risk placing the same order twice with
  real money. This needs a client-generated idempotency key the broker
  (or this platform, pre-broker) can deduplicate on -- paper trading has
  never needed this because a duplicate simulated fill only ever cost a
  test run some accuracy.
- **A circuit breaker on broker API errors.** Repeated failures calling
  Upstox should pause live order placement for that account rather than
  retry into an unknown state -- this is a different failure mode than a
  paper order being rejected for insufficient funds, which is expected
  and handled cleanly today.
- **Materially tighter, per-order-not-per-minute rate limiting** on any
  live order-placement endpoint, separate from `order_rate_limit` in
  `app/middleware/rate_limit.py`, which was tuned for paper trading's
  much lower stakes -- and this would need to stay well under the 10 OPS
  regulatory threshold on top of its own risk-control purpose.
- **A minimum paper track record before live eligibility**, if
  strategies are ever in scope at all -- e.g. a strategy must show some
  minimum number of paper trades or days active before it can even be
  *considered* for the (separate, broker-mediated) live registration
  process above.

## What this means for this codebase specifically

`BrokerAdapter.place_order()` has existed since Phase 1 and has never
been called -- `ExecutionService` only ever simulates a fill using
`calculate_costs()` and `apply_fill()` against a real fetched price,
never submits an order anywhere. That gap is deliberate, not an
oversight to close casually. A live path would most naturally be a new
service sitting alongside `ExecutionService` (not a modified version of
it) that reuses the same `Order`/`Position`/`Execution` models and the
same cost engine, but replaces "simulate a fill" with "submit to
`place_order()`, then poll `get_order_status()` until it actually fills,
then reconcile against `get_positions()`" -- a fundamentally different
and much riskier control flow than paper trading's, which is exactly why
it belongs in its own service rather than a flag inside the existing
one.

That new service would also need to know, per account, which regulatory
lane applies -- your own account trading your own strategies (lighter
path, still needs the technical requirements above) versus any other
user doing the same (needs the broker-empanelment path first, before any
code-level safeguard matters at all). That's an account-level
distinction this platform's data model doesn't currently represent
anywhere, because paper trading never needed it.

## Recommendation

For your own account only, running strategies you built yourself: this
is a real but bounded project. The order-frequency exemption plausibly
applies, the White Box classification is favorable if you ever do
register, and the technical requirements (static IP, 2FA, daily session
reset) are concrete and buildable -- OAuth is already done. That's the
version of "live trading" that engineering effort alone can get you
most of the way toward.

For any other user on this platform trading live through it -- which is
what a multi-tenant SaaS product actually is -- the gate is a real-world
conversation with Upstox about algo empanelment and registration, not
a coding project, and it comes before any of the engineering safeguards
above start to matter. No amount of code in this repository changes
that. If live trading for your users specifically is a real goal, that
conversation is the actual next step.


## Durable idempotency and reconciliation — reviewed design checkpoint (2026-10-17)

The implementation-level design is in [`LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`](LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md). This is a proposal, not a completed feature. The current shared execution service remains PAPER-only; do not wire it to `UpstoxAdapter.place_order()`.

Required minimum before any live-order implementation:

1. Create a durable intent with a unique idempotency key scoped to user and broker connection, plus a canonical hash of all economic order fields. Same key/same payload returns the original intent; same key/different payload is rejected.
2. Commit intent, risk decision, audit event and dispatch record before network I/O. Treat the external POST as an uncertain side effect: timeout/crash after send means UNKNOWN, not safe-to-retry.
3. Use a broker tag only as correlation/search unless Upstox explicitly documents idempotency semantics. Reconcile using documented order history, order book, order details and trades. If zero/multiple/mismatched matches leave uncertainty, block automatic resubmission and alert.
4. Persist broker order IDs, normalize statuses, and deduplicate fills by stable broker trade identity. A placement acknowledgment is not a fill; cancellation acknowledgment is not proof no fill occurred.
5. Recheck portfolio/account risk and account-level kill switch immediately before dispatch. Pending and unknown orders reserve exposure. Preserve paper/live isolation.
6. Use additive, reviewed migrations; test uniqueness races, process crashes, duplicate requests, partial fills, sliced orders, cancellation races and multi-worker contention. Test on clean SQLite and a backup-restored staging copy of the actual deployment DB engine before deployment.
7. Never test by submitting real orders. Live release requires official API-contract verification, broker/account setup and applicable compliance review, sandbox drills, operational alerts/runbook, explicit user authorization and a limited controlled pilot.

Official Upstox API documentation reviewed for this design:
- [Place Order V2](https://upstox.com/developer/api-documentation/place-order/)
- [Place Order V3](https://upstox.com/developer/api-documentation/v3/place-order/)
- [Order History](https://upstox.com/developer/api-documentation/get-order-history/)
- [Order Book](https://upstox.com/developer/api-documentation/get-order-book/)
- [Order Details](https://upstox.com/developer/api-documentation/get-order-details/)
- [Order Trades](https://upstox.com/developer/api-documentation/get-trades-by-order/)

Do not claim exactly-once broker submission based on local database idempotency alone. The design targets durable intent deduplication and safe reconciliation, with no blind retries for ambiguous external outcomes.


## Phase 1 verification checkpoint — 2026-10-17

The current automated CI run [39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046) passed 215 tests and verified Alembic upgrade → downgrade → re-upgrade on clean SQLite and PostgreSQL 16. The simultaneous idempotency test uses two independent PostgreSQL sessions. This is CI evidence only; it does not replace a backup-restored staging migration check against the actual deployment database. No production migration or real broker order was performed. Live submission remains disabled.


## 17 October 2026 — Phase 2 repository-only implementation note
The improved repository now has pure broker-order status normalization, strict candidate matching, and a versioned repository method for persisting a matched observation plus audit event atomically. These are not broker integration: no order-book/history/trades API is called by this code, no fill is imported, and no live order is placed or cancelled. A successful CI run is not a staging or production verification. Keep live submission disabled and require the remaining roadmap gates and explicit authorization before adding submission behavior.


## 17 October 2026 — individual fill identity persistence
The repository now validates normalized Upstox per-order trade records and stores individual fill identities idempotently using `(broker_connection_id, broker_trade_id)`. Identical replay is a no-op; conflicting reuse of a trade ID fails closed. A linked fill and audit event are atomic. This is still not full reconciliation: no broker reads/worker, fill-vs-intent economic validation, partial-fill accounting, position/cash/P&L update, or live order submission is present. Keep live trading disabled.


## 17 October 2026 — fill-to-intent economic checks
Linked fill identity persistence now requires the same broker order ID already linked to the intent, exact instrument/side/product/order-type agreement, valid requested quantity, and per-fill plus aggregate quantity ceilings. BUY LIMIT/SL fills above limit and SELL LIMIT/SL fills below limit are rejected before persistence. CI [run 39052939770](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39052939770) passed 279 tests, 1 warning, and SQLite/PostgreSQL 16 migration checks. These are repository safeguards only; no broker polling, live accounting, or live submission is present.


## 17 October 2026 — unmatched-fill relinking
Unmatched individual fills may now be linked later using a conditional update after rechecking authenticated user/connection, broker order ID, instrument, side, product, order type, quantity ceilings and limit-price constraints. A linked fill cannot be silently reassigned; the link and audit event are atomic. CI [run 39053352921](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39053352921) passed 281 tests. No broker reads, worker, live accounting or order submission is present.


## 17 October 2026 — out-of-order status/fill safeguard
Reconciliation status transitions now consult persisted, deduplicated fill quantity. Stale active order states cannot overwrite known partial fills; partial fills plus cancellation remain explicit; contradictory partial/full or reject/fill observations are quarantined. Audit events preserve observed status and resolution reason. Exact test run [39056392873](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056392873) passed 294 tests, 1 warning. The read-only worker is design-only; no broker reads, order actions or portfolio accounting updates are implemented. Live submission remains disabled.


## 17 October 2026 — GET-only reconciliation client
A separate `UpstoxReadOnlyReconciliationClient` now exposes only fixed-path GET methods for order book/details/history/trades. It cannot submit, modify or cancel orders; upstream response bodies and exception text are not surfaced on failure. Mocked contract tests passed [run 39056868434](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056868434): 309 passed, 1 warning. No real broker request has been made; a worker with connection scoping, token checks, retry limits and leases is still required. Live submission remains disabled.


## 17 October 2026 — worker lease foundation
A durable one-per-connection reconciliation lease now supports atomic claims, expiry/reclaim, renewal and stale-owner-safe completion. The model and reversible migration passed [run 39057273255](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39057273255), 318 tests, 1 warning. The lease is not connected to a worker yet. Do not infer that broker polling or live trading is enabled.


## Phase 2 worker boundary — 2026-10-17
A read-only reconciliation worker now exists but is not scheduled or exposed through an API route. It injects only `UpstoxReadOnlyReconciliationClient` (fixed GET methods), validates user/connection ownership and token usability, uses a durable lease and bounded retries, and persists normalized trade identities and status/audit evidence. Tests are mocked; no real broker read has occurred. The current worker only reads the order book and daily trades and does not provide historical pagination, persistent operator summaries/manual-review queue, or accounting aggregation. It must not be used as evidence that live submission is safe. Keep all order-write paths disabled until later release gates and explicit authorization.


## Durable worker summary boundary — 2026-10-17
The worker now records count-only run summaries and sanitized error categories in `live_reconciliation_runs`; a summary contains no raw broker payload, credential, authorization header or exception text. The schema/migration is CI-tested, not staging/production migrated. The worker remains unscheduled and not exposed by an API route. A stale `RUNNING` record may remain after a crash; recovery/manual-review visibility is not yet implemented. This telemetry does not authorize live order submission.


## Manual-review queue foundation — 2026-10-17
`live_reconciliation_issues` stores deduplicated issue categories and minimal safe details; it does not store raw broker payloads or exception strings. The worker records malformed rows, unmatched/ambiguous orders and reconciliation conflicts. The schema is CI-tested only, not staging/production migrated. There is no UI/API issue browser or resolution action yet, so operators cannot rely on this as a complete incident-management interface. Keep live order writes disabled.
