<!-- Phase 3 checkpoint update — 27 Oct 2026. Latest code/test head 8feeb0cbb0c35e1e37012302c9075d43f1f33eb1 passed Backend CI #40458822529: 1,097 passed, 1 warning. Broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and evidence retention passed. DP completeness checks require a consistent KNOWN + explicit valid finite nonnegative paise-exact amount, or NOT_APPLICABLE + no amount; invalid status, UNKNOWN-with-amount, KNOWN-without-amount, NOT_APPLICABLE-with-amount, NaN, negative and fractional-paise amounts fail closed. DP canonical manifests are checked against persisted broker trade → child order → local order mappings; only mapped equity-delivery SELL fills are accepted. Delivery SELL still requires reviewed/reconciled DP evidence and durable per-fill allocation; DP is included once in total and replay identity. Maintained docs are being synchronized after the green code run; exact-head CI on the final docs/checkpoint commit must pass before it is called green. PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled; original Tradepro repository out of scope. -->

## Current Phase 3 checkpoint — 21 October 2026

- **Latest verified code/test HEAD:** `3963c2bf4e6ffe2bb33d327b10e2995cd243d003`. Exact-head [Backend CI run 39607630055](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39607630055) passed **484 tests, 1 warning in 29.34s**; the broker-write boundary guard passed, and SQLite/PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed.
- New Phase 3 guard: broker-reported live-fill charge references are trimmed for storage and rejected when longer than the `Execution.charge_reference` 200-character column limit. This prevents a predictable storage error from being misreported as a concurrent promotion conflict. Regression coverage is included in the 484-test result.
- The existing Phase 3 safety gates remain active: replay must match the accounted fill and exact charge evidence; only broker-reported, internally consistent charges with a non-empty audit reference are accepted; durable staged trade quantities must match broker-confirmed child fills before promotion; exchange-time ambiguity/out-of-order fills fail closed; paper positions and cash remain isolated.
- **Phase 3 remains in progress, not complete.** Remaining review includes coordinator/identity boundaries, charge provenance/allocation semantics, full partial-fill and crash/restart acceptance criteria, and any explicitly selected bridge design. Keep `BrokerFillIdentity` separate from manual `BrokerTradeRecord` unless a reviewed Phase 3 design explicitly authorizes a narrow bridge.
- Live broker submission, automatic accounting promotion, and automatic scheduling remain disabled. The original `tarunsharma2610-del/Tradepro` repository remains untouched. Phase 2 remains closed.
- This checkpoint describes the verified code commit above. The documentation synchronization commit will trigger its own CI; do not treat that documentation commit as green until its exact-head run passes. Older checkpoint entries below are historical audit trail, not current status.

---

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


## Owner-scoped reconciliation listing API — 2026-10-17
Two authenticated read-only endpoints expose safe run summaries and review issues for the current user only. The query repository scopes by `user_id`; limits are bounded; response schemas do not return raw broker bodies or tokens. They cannot start a reconciliation job or resolve/mutate an issue. Cross-user isolation tests passed in [run 39060230705](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060230705), 345 passed, 1 warning. No live order action is enabled.


## Read-only reconciliation UI — 2026-10-17
A `/reconciliation` frontend page displays owner-scoped run summaries and sanitized issues. It has no worker-trigger or issue-resolution control, and the API is read-only. TypeScript/Next.js build and backend CI passed for commit `e4343dcb225c1f332b6c89399694d0a29a5df739`. The UI is not evidence of a real broker reconciliation pass; no live order path is enabled.


## Live-fill accounting recovery and verification — 2026-10-20

The original live-fill accounting service, tests and migration 0008 were restored; supporting broker-order/trade/live-position models and migration revisions 0006/0007 were added. GitHub Actions [run 39475387511](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39475387511) passed **355 tests, 1 warning**, and SQLite/PostgreSQL 16 reversible migration checks at code/test checkpoint `a906274b98f3f7e0c913f376128f4996b996c52b`.

Important boundary: the accounting service remains unregistered; no broker trade intake or worker-to-accounting path invokes it yet. It is not proof of live accounting end-to-end or real-account reconciliation. Keep live submission disabled and continue Phase 2 recovery/fill-linkage gates before any integration.


## Current reconciliation and fill-staging boundary — 2026-10-21

- The intent-based read-only reconciliation worker exists and is on-demand only; it uses a GET-only client and writes `BrokerFillIdentity`/intent audit evidence. It is not scheduled or triggered by an API route.
- The separate manual-Order staging path validates and stores broker trades in `BrokerTradeRecord`, then checks broker child-order status/filled quantity against durable trade quantity and weighted average price. It changes only `BrokerOrder.status` and `filled_quantity`; parent Order/accounting is unchanged.
- `LiveFillAccountingService` remains unregistered. A cumulative guard rejects promotions that would exceed the broker-confirmed child fill quantity. Explicit broker-reported charges are still required.
- Do not connect the worker's `BrokerFillIdentity` records to `BrokerTradeRecord` accounting without an explicit reviewed bridge or a clear statement that these are separate workflows. Keep live writes and automatic promotion disabled.
- Exact code/test checkpoint [run 39481385581](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39481385581) passed 438 tests, 1 warning; SQLite/PostgreSQL 16 reversible migration checks passed. All broker calls in CI are mocked.


## Parent-order lock guard — 2026-10-21

After broker status I/O, child reconciliation locks/revalidates the owned parent Order, verifies LIVE mode and the pre-network instrument/side/quantity snapshot, then locks the BrokerOrder child before reading staged trade totals. This matches ingestion's parent→child lock order and blocks stale responses after a local order mode/economic change. A regression test switches the order to PAPER during the status read and confirms child state remains unchanged. Exact-head [run 39482592808](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39482592808) passed **439 tests, 1 warning**, with SQLite/PostgreSQL 16 reversible migrations. No parent accounting or live submission is enabled.


## 2026-10-24 — Resolver acceptance and CI checkpoint

- Latest previously verified documentation head: `8214430f562f6f425cfc1b9b6a6b3b547832b68a`; backend workflow [#40108183667](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40108183667) succeeded on that head. New resolver test commits `0f05f52cbb7c3afbe1c159fb94837c9776eb9262` and `65e7b56de6b193423106d57101a11d54dcc7894c` add exact broker/endpoint/schema/field/scope matching and non-finite-number rejection cases; these newer commits still require CI.
- The mapping identity test fixtures use immutable dataclass replacement. Intended-use semantics remain explicit; missing/null/invalid states remain unusable and preserve mapping provenance; zero remains distinct.
- Accounting acceptance already covers replay/conflict, ledger reconciliation, lock order, rollback, reviewer authority and a PostgreSQL verification/promotion race. Re-check exact test and workflow status before claiming complete; CI does not establish production tariff correctness or broker-origin authenticity.
- Safety gates unchanged: PR #6 draft/unmerged; live broker order submission disabled; automatic quantity/notional allocation disabled; production Upstox mappings/tariffs unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` must remain untouched.


## 2026-10-24 — Resolver field-identity guard added; CI pending

- Review found a mapping-identity gap: the resolver selected a mapping by `field_path` but normalized the separate `field` argument without checking that it was the mapped field. A caller could otherwise pair the approved `charges.ipft` mapping with a different top-level payload field.
- Added a fail-closed check requiring the normalized payload field to match the terminal field name in the approved mapping path. Added a regression test proving a mismatched payload field is rejected.
- Implementation commit: `77aa77aec37dc535c3e427ca3f88c2ccb5e75ed8`; regression-test commit: `5c5482c7f7fa623707698f64b6a061351e5e5b87`. CI for these commits is pending; do not claim green until the latest branch head is verified.
- Prior backend workflow `40108552948` passed on earlier head `cf5497aec438a3b6c91ae4d67c445cdbacd7b34b`; this does not validate the new field-identity guard.
- Accounting concurrency review remains a separate acceptance item: existing promotion tests assert canonical lock order and rollback/idempotency, but the current test file does not itself demonstrate a genuinely concurrent two-session verification-versus-promotion race. Confirm whether another integration test exercises that race before marking the item complete.
- PR #6 remains draft/unmerged. Live broker order submission and automatic quantity/notional allocation remain disabled; production Upstox mappings/tariffs remain unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Latest resolver CI verified; PostgreSQL race coverage located

- Latest PR head `ed346e823cbfae8448fae0134c4ff864bfcc60ac` passed Backend workflow [#40109041654](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40109041654). This head includes the resolver payload-field/mapping-path identity guard and its regression test, plus the synchronized docs through this checkpoint.
- Located PostgreSQL-only integration coverage in `backend/tests/test_broker_charge_allocation_postgres_concurrency.py`: conflicting fill-set serialization; concurrent source verification and allocation promotion; full live-fill promotion racing ledger verification; and concurrent tariff estimate/variance persistence cases. These tests require `TEST_POSTGRES_URL`; their execution depends on the PostgreSQL CI job actually provisioning and running that suite.
- Therefore the earlier concern that no dedicated verification-versus-promotion race test exists is corrected: a dedicated test is present. Next verify the workflow job log confirms this PostgreSQL test was run rather than skipped, then inspect its assertions for accounting/position side effects.
- PR #6 remains draft/unmerged. Live broker order submission and automatic quantity/notional allocation remain disabled; production Upstox mappings/tariffs remain unapproved. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Accounting invariant audit checkpoint

- Reviewed `backend/app/services/live_fill_accounting_service.py` and its unit tests. New accounting writes (live position mutation and execution insert) are committed in one transaction; all exceptions roll back. A post-commit refresh failure is covered by retry-as-exact-replay tests.
- Verified test coverage for exact replay, conflicting fill/evidence payloads, unchanged paper position and portfolio cash, failed flush/commit rollback, charge totals matching six components, and deterministic paise allocation.
- Dedicated PostgreSQL concurrency tests exercise verification-vs-promotion, live-fill-vs-ledger verification, conflicting fill sets, and concurrent tariff snapshot replay/conflict. CI on head `bacbe9dd9dfa35d739bbcea2bfece6185dc391d0` passed workflow [#40109864007](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40109864007). This passing head predates the present audit-note commit(s); recheck CI on the new head.
- Remaining acceptance is not waived: ensure the PostgreSQL-only tests are exercised by required CI with `TEST_POSTGRES_URL`, verify latest branch checks after this documentation change, and continue authoritative tariff/API-field review. Synthetic test fixtures do not approve production tariff semantics.
- PR #6 remains draft/unmerged. Live broker order submission and automatic quantity/notional allocation remain disabled. Production Upstox mappings/tariffs remain unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Upstox brokerage calculator restricted to estimates; CI pending

- Official Upstox `GET /v2/charges/brokerage` calculates charges from proposed order inputs; it is not proof of final booked per-fill charges. https://upstox.com/developer/api-documentation/get-brokerage/
- Resolver blocks this endpoint from `PER_FILL_ACTUAL` and actual `AGGREGATE_SUMMARY` use, even if a mapping is misleadingly labelled. `/v2/trade/profit-loss/charges` remains aggregate-only for per-fill purposes. Regression tests cover both mislabelled cases.
- Implementation `3486d854dae2451858a858cb627602aca7338969`; tests `6c92101a1890a0f4d761e86ed3db047a269fd10d`. The prior head passed workflow #40111501429; latest implementation/test CI must be verified.
- Production mappings/tariffs unapproved; null is not zero; automatic quantity/notional allocation and live order submission disabled. PR #6 draft/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` untouched.


## Canonical latest Phase 3 checkpoint — 26 October 2026

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **Verified code/evidence head:** `d287da70ce184c904c6f9ede9e4a0edca5839f8f` (commit: “docs: reconcile public Upstox contract note GST examples”).
- **Exact-head CI:** PASS — [GitHub Actions run #40304398632](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40304398632), commit `d287da70ce184c904c6f9ede9e4a0edca5839f8f`; **1,004 passed, 1 warning**. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and restore-evidence retention also passed. This is CI evidence, not proof of a real Oracle recovery or broker-origin authenticity.
- **GST/IPFT research:** Three public third-party historical Upstox note copies were reconciled: 11-Feb-2025 base ₹2.97 / IGST ₹0.53; 21-May-2024 base ₹77.56 / IGST ₹13.96 (IPFT ₹0.11 listed outside that note's printed base); 12-Mar-2025 base ₹2.75 / IGST ₹0.50. Printed-base compositions differ historically. The current official Upstox schedule supports the **estimate-only** base of brokerage + transaction charges + demat where applicable + IPFT, with IPFT represented exactly once because it is combined with transaction charges. Do not add SEBI to this current estimate base without current applicable billing evidence; never calculate GST on trade notional or infer zero from missing/null fields.
- **Tax/accounting approval:** all four GST component candidates remain `DRAFT`. Historical public copies do not prove current actual per-fill billing across products/accounts. Actual-charge promotion stays gated; estimate logic and actual invoice reconciliation are distinct. Follow effective dates and preserve raw API/source evidence.
- **Next action when resuming:** continue Phase 3 from this exact commit and checkpoint. Next gate is component-specific GST acceptance cases for equity delivery, intraday, futures and options, then implementation review and exact-head CI; do not restart from earlier saved checkpoints.
- **Safety / PR:** PAPER mode mandatory; live broker `place_order`/`modify_order`/`cancel_order` and automatic live-fill promotion remain disabled. PR #6 remains open, draft and unmerged. Original `tarunsharma2610-del/Tradepro` is not the work target and must remain untouched.
- This checkpoint supersedes older statements in this document about CI being in progress or requiring verification for the pre-`d287da7` head. Historical notes remain history; this is the canonical resume point.

## Canonical resume checkpoint — 26 October 2026 (latest branch head verified)

- **Target:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **PR #6:** open, draft, unmerged. Never modify original `tarunsharma2610-del/Tradepro`.
- **Latest branch head before this documentation synchronization:** `5c929ff933d627dd81d5c32ec863843c2ef0f19b`. Exact-head Backend CI **PASS**, run [#40315135121](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40315135121): **1,004 passed, 1 warning**. Broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore and evidence retention passed; synthetic restore is not proof of real Oracle recovery.
- **GST/IPFT finding:** current official Upstox guidance supports an 18% public-schedule estimate base of brokerage + combined transaction/IPFT charges + delivery demat where applicable. Count combined transaction/IPFT once. CBIC FAQ Q77 makes exclusion of STT/stamp duty/other recoveries conditional on Rule 33 pure-agent conditions. Three public historical third-party notes show differing bases (11-Feb-2025 ₹2.97/IGST ₹0.53; 21-May-2024 ₹77.56/IGST ₹13.96 with IPFT outside that printed base; 12-Mar-2025 ₹2.75/IGST ₹0.50); they are not authenticated current evidence.
- **Decision:** all four product GST component candidates remain `DRAFT`; actual per-fill GST promotion is blocked pending reviewed current source/invoice mapping. Never tax trade notional, infer zero from missing/null fields, or double-count IPFT. Aggregate charges API data is not per-fill evidence; the brokerage calculator is estimate-only.
- **Next gate:** continue Phase 3 product/segment-specific GST component acceptance and evidence reconciliation. Do not repeat canonical live-fill integration or restart from older checkpoints. Defer AI/open-source adaptations, including Algory.app, until Phase 3 acceptance.
- **Safety:** PAPER mode mandatory; live broker order writes and automatic live-fill promotion/scheduling remain disabled. Do not merge PR #6 without explicit user approval. This documentation-sync commit must pass exact-head CI.


## Session checkpoint sync — 26 October 2026

- Exact-head Backend CI [#40368554399 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40368554399) passed on code head `9d3f255480da9a71980a9d3819fbb69a34835753`. Documentation-only synchronization is now creating newer commits; do not treat the new documentation head as green until its own CI completes.
- Statutory GST research: CBIC stock-broking FAQ and CGST Act section 15 / CGST Rules Rule 33 and Rule 27 are the legal framework. Rule 33 pure-agent exclusion is conditional on evidence, not an automatic classification for every charge. IGST Act section 12(12) provides stock-broking place of supply; compare supplier and place-of-supply states for IGST versus CGST+SGST. Sources: https://cbic-gst.gov.in/sectoral-faq.html ; https://cbic-gst.gov.in/valuation-rules.html
- Public GST schedule helper/tests are estimate-only. A statutory valuation engine and its tests are **not yet implemented**; GST/IPFT acceptance remains open. Next: implement Section 15 inclusion, Rule 33 evidence gates, state-based tax split, Decimal/paise rounding and fail-closed handling. IPFT combined/separate representation and DP/demat persistence/reconciliation remain open.
- No personal contract note is available or required. Safety: target only `tarunsharma2610-del/tradepro-improved`; PR #6/#7 Draft/unmerged; PAPER-only; live order writes disabled; original Tradepro out of scope.


## API-first paper-trade charge estimation decision — 29 October 2026

- User-approved behavior: use Upstox's pre-trade Brokerage Details API for paper-fill charge estimates when it returns a complete, valid, internally consistent breakdown. Keep the existing deterministic local calculator as the automatic fallback if the API is unavailable, expired/unauthorized, incomplete, null/invalid, or inconsistent. This is estimation only, not live-trading/accounting promotion.
- Implementation added on the Phase 3 branch: `backend/app/services/paper_trade_charge_estimator.py` plus deterministic tests. `ExecutionService` now uses API-first estimates for market and matched limit paper fills and records `PAPER_UPSTOX_API_ESTIMATE` versus `PAPER_ESTIMATE` in the existing execution charge-source field. Components are accepted only when paise-exact supported components sum exactly to the API total; transaction, clearing and IPFT are combined once in the existing exchange-charge field. Unknown/incomplete fields fall back rather than block paper trading.
- Existing post-trade Upstox charges endpoint remains aggregate reconciliation evidence, not per-fill actuals. The API route already exists. GST reconciliation remains available without blocking paper-trade P&L.
- Implementation commits: `b90c09dc82a51181bc9eae422cb025eb79c65bcb`; default-enabled setting `UPSTOX_CHARGE_ESTIMATES_ENABLED`. CI disables network estimates only for the broad execution suite; mocked estimator tests cover API and fallback paths.
- Backend CI [#40755234415](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40755234415) — **SUCCESS** on code/test head `778e76d3554a3baedc41f0396276c1cb3dafc38f`: **1,197 passed, 1 warning**; broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore/evidence retention passed. Documentation sync head `d57dd476ecd6acebd4dc9e169912b877811a8166` still needs exact-head CI verification before it is called green.
- Next: continue the next uncovered Phase 3 accounting acceptance gate after CI recovery. Do not reopen GST/IPFT from zero or make minor estimate variance a paper-trading blocker. Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled; original `Tradepro` out of scope.


## Authoritative Phase 3 engineering closure — 29 October 2026

This section supersedes older status/next-step notes above; earlier entries remain as historical audit trail.

**Status: Phase 3 engineering acceptance is complete for the agreed PAPER-mode scope.** This is not authorization to enable live broker writes, promote estimates to booked actuals, or merge Draft PRs.

**Verified code checkpoint:** `3a0c464afcb10261d1590607f8440affd21295a0`, Backend CI [#40878367369 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40878367369): **1,207 passed, 1 warning**. Broker-write boundary, SQLite upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore, and restore-evidence retention passed. The new documentation head still requires its own CI run.

### Completed engineering scope

- Paise-exact deterministic per-fill allocation; source integrity/reviewer controls; canonical source-to-component mapping; explicit combined/split transaction-charge/IPFT handling.
- Idempotent replay and conflicting-replay rejection; locked charge verification; rollback protection for accounting/position mutation.
- Explicit DP/demat persistence and total completeness. Delivery SELL fails closed when required DP evidence is unknown, invalid, inconsistent, or missing.
- GST valuation and GST/API comparison primitives preserve Decimal/paise precision, state/place-of-supply, missing/null/zero distinctions, and review-required variances. They do not silently approve actual charges.
- Upstox Brokerage Details API first for PAPER estimates; hardcoded calculator fallback on unavailable/invalid/inconsistent responses. Persist source as `PAPER_UPSTOX_API_ESTIMATE` or `PAPER_HARDCODED_FALLBACK` and display: “Estimated charges may differ from actual broker charges. For paper trading only; these are not actual booked charges.”
- Post-trade Trade Charges API is aggregate-only evidence, never per-fill actuals; aggregate responses are sanitized before persistence/return.

### Non-blocking operational/release gates

Credentialed Upstox OAuth/API smoke testing and real Oracle/database-plus-document-volume restore acceptance require deployment and user-authorized credentials/backups. Tariffs without independently approved scope/date evidence remain estimate-only/fail-closed for actual accounting. Historical contract-note fixtures support regression tests; estimates and aggregate summaries never become booked per-fill actuals. These constraints do not block PAPER-mode engineering completion.

**Safety:** only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker writes disabled. Phase 4 is the next separate increment after exact documentation-head CI passes.


## Latest Phase 4 verification — 30 October 2026

- Transactional PAPER stop-event claim implementation: `6ac3882a98f3c66abb4cd62848971b6277ab3be7`.
- Exact-head Backend CI #41080156436 passed: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41080156436.
- Claims validate user/portfolio/strategy/instrument ownership, lock portfolio → strategy → position, reject flat or ambiguously shared positions, and persist unique quote identity, claim token and bounded lease. Duplicate claims fail closed.
- No claim consumer or order path is enabled by this slice. PAPER-only remains mandatory; live broker order writes remain disabled; PR #9 remains Draft/unmerged; original Tradepro repository is out of scope.
- Next: PostgreSQL 16 multi-worker claim tests, safe lease reclamation and crash recovery, then controlled PAPER dispatcher integration only after those gates.
