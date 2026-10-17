# Live Trading: Safeguards Design (Not Implemented)

This document is the "reviewed design" the original spec calls for before
live trading is ever built -- it is analysis and recommendations, not
code, and nothing in this delivery places or can place a real order.
`TRADING_MODE` defaults to `PAPER`. The safety branch now fails closed in
`ExecutionService.place_order` unless the normalized value is `PAPER`.
This prevents the paper-only service from accepting orders in LIVE/unknown
mode; it does not implement live execution. See `app/services/execution_service.py`.

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

Three of these four are not fully implemented today: static IP whitelisting,
mandatory 2FA on every API session, and automatic end-of-day session logout.
OAuth exists, but these gaps still need direct broker/compliance verification
before any real order-placing API use.

## Engineering safeguards (needed regardless of which category)

Some foundations now exist, but the complete live-trading safeguards below
are still incomplete. In rough order of "must exist before the first real
order, no exceptions":

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
  The current branch has a per-paper-order notional cap and a portfolio daily-loss
  guard for automated entries, plus strategy-level loss checks. These do not
  provide live max-position, total-exposure or all-order daily-loss controls.
- **A kill switch reachable outside the normal trading flow.** A
  "disable all live trading for this account, right now" action that
  works even if the strategy/order UI itself is broken or the frontend
  hasn't loaded -- this matters exactly when things are already going
  wrong.
- **Real reconciliation against the broker's own records, not the
  platform's internal ledger.** A read-only status-check service and endpoint
  now exist for a known LIVE order with a stored broker ID, but no live
  submission service persists such IDs yet. Partial fills, cancellations,
  timeouts/restarts, positions and holdings still require full reconciliation
  and a halt-on-mismatch policy.
- **Idempotent order submission.** A per-portfolio client idempotency key is
  stored by the paper order API, and strategy fills reject a second entry while
  that strategy owns a position. The frontend/strategy callers do not yet
  consistently reuse stable retry keys, and broker-side idempotency plus
  timeout/restart reconciliation remain mandatory before live use.
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

`BrokerAdapter.place_order()` exists, but it is not wired into a complete
live order lifecycle. `ExecutionService` still simulates paper fills using
`calculate_costs()` and `apply_fill()` against a fetched price. The read-only
broker-status endpoint is a foundation, not live order placement. This gap is
deliberate, not an oversight to close casually. A live path would most naturally be a new
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
