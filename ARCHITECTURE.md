## PostgreSQL CI execution confirmation — 24 October 2026

- Inspected `.github/workflows/backend-tests.yml` and successful Backend pytest run [39921411680](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39921411680) on commit `db1053d7f7c53e1c57016f153f11c9897fa59682`. The workflow provisions PostgreSQL 16, sets `TEST_POSTGRES_URL` for `python -m pytest -q`, and the Backend pytest job completed successfully. Thus the `skipif(not TEST_POSTGRES_URL)` PostgreSQL-only tests were enabled for that run (job logs/test output should be consulted if exact per-test counts are needed).
- The workflow also passed Alembic upgrade/downgrade/re-upgrade checks on SQLite and PostgreSQL 16, the broker-write-boundary guard, and an isolated synthetic database/document-volume restore drill.
- The restore drill uses synthetic data created inside CI. It does not substitute for restoring the user's actual retained Oracle Cloud backup or validating an authentic account-specific Upstox contract note.
- The existing source-verification/promotion race test covers allocation-ledger functions, but the integrated concurrency scenario that races real `LiveFillAccountingService.promote_trade` against ledger verification/promotion remains open. Do not mark Phase 3 accounting sign-off complete until that integration gap is addressed or explicitly accepted with evidence.
- PR #6 remains draft/unmerged; live broker order submission remains disabled. All changes are confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains untouched.

---

## Phase 3 concurrency integration status — 24 October 2026

- Current branch head before this documentation update: `2cacf392e5104a8b16307395847239bba945c87b`; branch-head backend CI run [39920815737](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39920815737) passed. PR #6 is draft and unmerged.
- The PostgreSQL-only allocation concurrency suite already contains `test_concurrent_source_verification_and_promotion_serialize_on_evidence`. It concurrently runs the real `verify_component_allocation_ledger` and `promote_verified_component_allocations` functions against synthetic persisted evidence and asserts that both allocations finish reconciled under one reconciliation reference.
- This is a useful source-ledger race test, but it is not the same as a concurrent call to `LiveFillAccountingService.promote_trade` using the real `_load_reconciled_allocation_fees` path while ledger verification/promotion races. That end-to-end live-fill integration scenario remains unproven and is still an acceptance gate.
- The other PostgreSQL allocation test races competing fill sets for a source component and expects exactly one fill set to own that component. Tests are skipped locally without `TEST_POSTGRES_URL`; CI must be checked to confirm the PostgreSQL service actually ran these tests rather than only passing via skips.
- Next engineering task: add or extend a disposable-PostgreSQL integration test using reviewed synthetic evidence, real reconciled allocations, and the actual live-fill accounting service. Assert no partial execution/position writes on failed verification, exactly-once replay, and no acceptance of a conflicting/unreconciled ledger. Then verify the exact resulting head's job logs and test counts.
- Real account-specific broker contract-note validation and restoration from an actual retained Oracle Cloud PostgreSQL/document backup remain separate operational checks.
- Live broker order submission remains disabled. PR #6 stays draft/unmerged. All work remains confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains untouched.

---

## Final conflict-recovery review checkpoint — 24 October 2026

- Reviewed `LiveFillAccountingService.promote_trade` replay and `IntegrityError` recovery paths on branch head `78c66b50714175df7e6923fa0e9328b98bb30cf2`.
- Existing-execution replay locks and refreshes the broker trade record, checks its immutable execution snapshot, and compares execution identity, fill details, charge values and evidence before returning `inserted=False`; conflicting details fail closed.
- The integrity-conflict recovery rolls back the losing transaction, re-queries the execution by broker connection/trade identity, and only returns an idempotent result when the existing execution matches; otherwise it raises a conflict requiring review. Generic failures also roll back.
- Latest branch-head backend pytest CI passed in run [39920205395](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39920205395). The concurrent PostgreSQL test uses a test-only stub for the charge-ledger loader, so it verifies parent/child locking and duplicate-promotion behavior, not the real allocation verifier under the same concurrency interleaving. Ledger validation is covered by separate accounting tests. Do not overstate this as a full production-like concurrent allocation integration test.
- Review status: the inspected replay/rollback paths have coverage and no additional code change is justified by this inspection alone. Phase 3 accounting sign-off is still gated on a final review of the real verifier/promotion concurrency interaction and confirmation of exact-head CI after this documentation update.
- Real broker contract-note authenticity and a restore drill from an actual retained Oracle Cloud PostgreSQL/document backup remain outstanding operational acceptance checks.
- PR #6 stays draft and unmerged; live broker order submission remains disabled. Changes remain confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is untouched.

---

## Phase 3 accounting checkpoint — 24 October 2026

- The concurrent exact-replay PostgreSQL regression passed in implementation CI run [39919563611](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39919563611) for commit `f8441f6d11b863e3ad173282664663cd4985eeb2`. The test exercises two distinct fills and a simultaneous duplicate promotion, expecting two inserted executions and one idempotent replay.
- Documentation checkpoint run [39919590316](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39919590316) passed for commit `c99e4972cf4c2c902bddc076af6327c3bfd25fa7`.
- The next documentation CI checkpoint is still in progress: progress run `39919920878` succeeded, while handover run `39919925329` and audit run `39919932771` were in progress at last inspection. These are earlier documentation heads; any newly synchronized documentation needs its own exact-head CI.
- Accounting review remains open pending exact-head verification and final adversarial review. Passing tests are evidence for covered cases, not a guarantee against every possible concurrency interleaving.
- Real account-specific contract-note validation and restore of an actual retained Oracle Cloud PostgreSQL/document backup remain operational acceptance checks. Synthetic CI restore drills do not satisfy those real-environment checks.
- PR #6 remains draft and unmerged; live broker order submission remains disabled. All work is confined to `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope.

---

## Current acceptance clarification — 23 October 2026

- **Public contract-note research is complete for development:** third-party examples dated 12 March 2025 and 21 May 2024, plus a sample-note guide, were reviewed for structure and charge categories. See `docs/UPSTOX_CONTRACT_NOTE_AND_API_EVIDENCE.md`.
- The examples are not independently authenticated. No raw public document, personal identifier, or invented “real” evidence is stored in this repository. The checked-in Upstox-style fixture remains explicitly synthetic.
- **A personal/account-specific contract note is not required to continue or complete Phase 3 engineering.** It remains optional future validation for account-specific source authenticity and charge comparison; public aggregate figures must not be treated as proof of per-fill amounts.
- A separate real retained database/document backup and restore test remains a deployment/operational acceptance gate for the Oracle Free Cloud environment. Synthetic CI restore results do not prove recovery of real user data.
- Exact-head CI on commit `18c897a282ea5f8e7c6a55707ad24b6cf8da5b27` passed in [run 39915983869](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39915983869). This does not substitute for the next CI run after this documentation clarification.
- This section supersedes older checkpoint wording below that may imply a personal contract note is required before Phase 3 engineering can proceed. Historical notes remain for audit traceability.
- Scope: `tarunsharma2610-del/tradepro-improved` only. PR #6 remains draft/unmerged; live broker order writes remain disabled.

---

## Phase 3 allocation-weight integrity checkpoint — 23 October 2026

- Code review found that a charge ledger could sum to the correct source total while its individual per-fill amounts did not follow the reviewed allocation basis. Reconciliation now recomputes and verifies each fill's expected amount before promotion.
- Added migration `202610230013` and persisted canonical reviewer-approved weights for `EXPLICIT_REVIEWED`. Source review requires one weight per eligible fill; `QUANTITY` and `NOTIONAL` bases derive weights from persisted broker-trade quantity and price. The verifier checks the complete fill set, basis, method, total, and each per-fill allocation.
- Added regression coverage for a tampered per-fill split that preserves the aggregate total.
- Exact-head CI [run 39912330029](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39912330029) passed on code commit `776ee59485d79b880d7aee0f5c3ecb641eb7db3f`: **567 passed, 1 warning**. Broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore all passed.
- This CI result validates that code commit only; the documentation commits now being synchronized require a new exact-head run. Synthetic restore evidence is not proof of recovery of actual Oracle Free Cloud data or authenticity of a real Upstox contract note.
- PR #6 remains draft/unmerged pending the final review and explicit user approval. Live broker writes remain disabled. Scope remains `tarunsharma2610-del/tradepro-improved`; do not modify original `tarunsharma2610-del/Tradepro`.

---

## Phase 3 promotion rollback guard — 22 October 2026

- Exact-head CI run [39813721425](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39813721425) **PASSED** on commit `121741f32ff74c46ccc059f672b3e9f0e020ef14`: backend pytest **565 passed, 1 warning**; configured PostgreSQL 16 migration/safety checks completed successfully.
- Added a regression test that injects a flush failure during charge-allocation promotion and verifies that, after rollback/reload, all allocation rows remain `PENDING_RECONCILIATION` with no reconciliation reference.
- This CI result validates the above commit only. Any subsequent documentation commits require a fresh exact-head run.
- PR #6 remains open, draft, and unmerged pending continued accounting review and explicit user approval. Live broker order writes remain disabled.
- Synthetic restore evidence does not prove recovery of the user's real Oracle Free Cloud data or authenticity of a real broker contract note. Real-data acceptance remains deferred until the user supplies the evidence.
- Scope remains `tarunsharma2610-del/tradepro-improved` only. Do not modify original `tarunsharma2610-del/Tradepro`.

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


## Phase 3 checkpoint — lock-order regression verified (22 October 2026)

- Latest exact-head CI run [39817017949](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39817017949) passed on commit `7809e8d7981a19625142dc73e689caa2976c97d6`: backend pytest **565 passed, 1 warning**.
- Live-fill accounting now defers target allocation-row locks until after source-component verification, refreshes target allocations under lock, and fails closed if their state changed. The regression test checks lock-order invariants rather than a brittle exact query prefix.
- A preceding implementation run failed on an outdated test expectation; the test was corrected and the latest run passed.
- PostgreSQL concurrency coverage exists for competing allocation requests on one evidence record. Concurrent source verification versus promotion, deadlock/retry handling, and conflicting fill-set replay still need further review.
- Real contract-note authenticity and a real retained Oracle Cloud database/document restore remain deferred until real evidence is available. Synthetic restore testing does not prove real-data recovery.
- PR #6 remains open/draft/unmerged pending review and explicit user approval. Live broker order writes remain disabled.
- Scope remains `tarunsharma2610-del/tradepro-improved` only; do not modify original `tarunsharma2610-del/Tradepro`.


## 2026-10-23 — live-fill/ledger concurrency checkpoint

- Added PostgreSQL integration test `test_live_fill_promotion_races_with_component_ledger_verification` in `backend/tests/test_broker_charge_allocation_postgres_concurrency.py`.
- Commit: `66fda569b1e4879d270a970cb5b6d216c2f55f9c`; exact-head CI run `39923699033` passed: **570 passed, 1 warning in 30.89s**. Broker-write boundary guard, SQLite/PostgreSQL 16 migration checks, and synthetic database/document-volume restore drill passed.
- CI: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39923699033
- Safety: only `tarunsharma2610-del/tradepro-improved` changed; PR #6 remains draft/unmerged and live broker order writes remain disabled.
- Limitation: fixtures and document bytes are synthetic; authentic Upstox contract-note validation and a real Oracle-host backup restore remain outstanding.


## Exact-head CI checkpoint — 2026-10-23

- Verified PR #6 head `f75471c5bc64bc9ede61c7dc621d1200e97fa078` with GitHub Actions run [39927004048](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39927004048): Backend pytest job completed successfully; broker-write boundary guard, SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks, synthetic PostgreSQL/document-volume restore drill, and evidence-retention step all passed.
- This result applies to that exact PR head. Any documentation commit creates a new head and must receive its own CI verification before the checkpoint is considered current.
- Synthetic restore evidence is not proof of restoring the user's real Oracle Cloud database/document backup. Actual retained-backup restore and authenticated real broker-source validation remain separate acceptance items.
- The integrated concurrency test that races real `LiveFillAccountingService.promote_trade` with allocation-ledger verification/promotion remains an open Phase 3 acceptance gate; do not treat the accounting review as complete yet.
- PR #6 remains draft and unmerged pending acceptance-gate review and explicit user approval. Live broker order writes remain disabled. All changes remain confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains out of scope.


## Follow-up verification — 23 October 2026 (supersedes stale pending wording)

- Exact current head `3c592de0bb2262ec4753196dfba26d7a31c70986` passed GitHub Actions Backend tests in [run 39927573489](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39927573489). The job passed pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade, synthetic PostgreSQL/document-volume restore, and restore-evidence retention.
- Code inspection confirms `backend/tests/test_broker_charge_allocation_postgres_concurrency.py::test_live_fill_promotion_races_with_component_ledger_verification` exists. It races `LiveFillAccountingService.promote_trade` against `verify_component_allocation_ledger` using synthetic persisted evidence and asserts no errors, one inserted execution, one live position, and reconciled component allocations. The CI job passed this PostgreSQL-enabled integration suite.
- Therefore, earlier checkpoint text describing this exact integrated race test as still absent is superseded. Remaining Phase 3 acceptance is broader review of charge-component allocation policy and evidence provenance, source authenticity limits for public examples, plus separate real Oracle backup/restore validation; synthetic tests do not prove real-account authenticity or actual backup recovery.
- PR #6 remains draft/open/unmerged until all acceptance gates are reviewed and the user explicitly approves. Live broker order writes remain disabled. Scope remains only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains outside scope.


## Component-specific allocation policy review — 23 October 2026

- Added `PHASE3_COMPONENT_ALLOCATION_POLICY.md` documenting the key distinction between deterministic allocation arithmetic and a justified charge-specific attribution basis.
- Public references reviewed: [Upstox brokerage/charges](https://upstox.com/brokerage-charges/), [Upstox brokerage calculator](https://upstox.com/calculator/brokerage-calculator/), [NSE levies/STT](https://www.nseindia.com/static/invest/first-time-investor-sebi-turnover-fees-stt-other-levies), and [NSE stamp duty](https://www.nseindia.com/static/invest/first-time-investor-stamp-duty-charges-taxes). Public tariff pages show effective-date and segment/product differences; rates must not be hardcoded as timeless or inferred from historical sample notes.
- Policy gap: the generic allocator's support for QUANTITY, NOTIONAL and EXPLICIT_REVIEWED is not blanket approval for those bases for every component. Brokerage/order caps, GST tax-base composition, buy-side-only stamp duty, side/product-specific STT and exchange charges, and account/scrip-level fees need component-appropriate rules and tests. The new policy file records the acceptance matrix and tests still required.
- Exact head before this policy-doc addition, `6d922d3436dcf2b3def7b5c77665056be173fab1`, passed Backend tests in [run 39928182307](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39928182307), including pytest, broker-write guard, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore/evidence retention. The new policy documentation commit and subsequent doc-sync commit(s) require their own exact-head CI before being marked verified.
- PR #6 remains draft/open/unmerged pending policy gates, full acceptance review and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` is out of scope.


## Fail-closed allocation gate — CI verified 23 October 2026

- Commit `2e14ce6feed8357a85813ec5924e577879b2e4ca` passed GitHub Actions [run 39929331878](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39929331878). Backend pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore, evidence retention, and cleanup all completed successfully.
- The source-reconciliation verification gate now rejects `QUANTITY` and `NOTIONAL` allocation bases until component-specific effective-dated rules are approved. A regression test verifies unsupported notional allocation raises and rows remain `PENDING_RECONCILIATION`. Explicitly reviewed per-fill weights remain available, subject to existing provenance/reviewer/promotion checks.
- This is a conservative fail-closed safeguard, not completion of component-specific tariff automation. Still required: reviewed tests/rules for brokerage caps and multi-fill orders, GST taxable base, buy-side stamp duty, side/product-specific STT/CTT, exchange/segment charges and effective-date transitions. Ambiguous source scope must remain pending.
- Publicly shared Upstox contract-note examples are for layout/research only and are not independently authenticated. Actual Oracle Cloud backup recovery remains separate from synthetic restore CI.
- PR #6 remains draft and unmerged until acceptance gates are reviewed and the user explicitly approves. Live broker order writes remain disabled. Changes are confined to `tarunsharma2610-del/tradepro-improved`; original `Tradepro` remains out of scope.


## Phase 3 charge-calculation checkpoint — 23 October 2026

- Verified code/test commit `b37e6cab7c9cbba0897e5c02161812d121ba2c7e` passed the full Backend pytest workflow: [run 39933579727](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39933579727). Steps passed included pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade, synthetic PostgreSQL/document-volume restore, evidence retention, and cleanup.
- The branch now has arithmetic helpers/regression coverage for brokerage caps, GST on an explicit taxable base, buyer-side stamp duty, STT/CTT on an explicit base, and exchange/SEBI charges on explicit bases. These are arithmetic helpers, not a verified tariff engine: they do not establish official effective-dated rates, applicability by exchange/segment/instrument/product/side, exemptions, or per-fill attribution.
- Latest exchange/SEBI test commit: `b37e6cab7c9cbba0897e5c02161812d121ba2c7e` (CI passed). Documentation checkpoint commit `1c3906551903acc0bb5a4450c7b8a56b3f9a659a` was created afterward; exact-head CI has not yet returned a workflow result.
- Remaining Phase 3 gates: source and version official effective-dated tariffs with provenance; model applicability and taxable/calculation bases; connect rule evaluation to durable per-fill allocations; test rounding, caps, effective-date transitions, replay/idempotency, and reconciliation; verify full CI on the final documentation/code head.
- Automatic `QUANTITY`/`NOTIONAL` allocation remains fail-closed until the relevant component-specific rules are reviewed and accepted. Do not promote ambiguous or unsupported charges.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. All changes are confined to `tarunsharma2610-del/tradepro-improved`; the original `Tradepro` repository is out of scope and must remain untouched.


## Exact-head documentation CI result — 23 October 2026

- Exact checkpoint commit `d0de363bd0b034582754b41de17ae991f6c043aa` passed GitHub Actions [run 39934671391](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39934671391). This verifies the nine-document checkpoint head at the time of the run.
- Resume from the `phase3/durable-per-fill-charge-allocation` branch in `tarunsharma2610-del/tradepro-improved`. Next work: obtain/record official Upstox and statutory charge-rule sources with effective dates and provenance; model applicability by exchange/segment/instrument/product/side; then implement and test tariff-driven durable per-fill allocation and reconciliation.
- Arithmetic helpers are groundwork only, not a verified tariff engine. Keep unknown/ambiguous allocation fail-closed. PR #6 stays draft and unmerged until acceptance gates and explicit user approval. Live broker order writes remain disabled. Original `Tradepro` is outside scope and must remain untouched.


## Exact-head CI confirmation for saved checkpoint — 23 October 2026

- The nine-document checkpoint head `c2959ffed34f6dd1c299bdb36091b987df06c11a` passed full GitHub Actions run [39935827529](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39935827529). Verified steps: backend pytest, broker-write boundary enforcement, SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade, isolated synthetic PostgreSQL/document-volume restore, evidence retention and cleanup.
- Resume work on `phase3/durable-per-fill-charge-allocation`. Next engineering task: verify and record current official Upstox, exchange and statutory charge rules with URLs, effective dates, applicability and provenance. Then implement tariff-driven component calculation and durable per-fill allocation, with regression tests for effective-date transitions, rounding, order caps, replay and reconciliation.
- Existing helpers for brokerage cap, GST, stamp duty, STT/CTT, exchange and SEBI charges are arithmetic groundwork only. They do not constitute a verified tariff engine. Keep unsupported/ambiguous scopes fail-closed.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Work only in `tarunsharma2610-del/tradepro-improved`; the original `Tradepro` repository remains outside scope.


## Upstox charge-rule source register — 23 October 2026

- Added `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md` at commit `de97bd3bfe90e82b888181cf109ed6a1b8e41d41`. It records the official Upstox brokerage pricing page, Brokerage Details API, Get Trades Charges API, and official contract-note guidance, with their limits and implementation requirements.
- Key source URLs: https://upstox.com/brokerage-charges/ ; https://upstox.com/developer/api-documentation/get-brokerage/ ; https://upstox.com/developer/api-documentation/get-trade-charges/ ; https://upstox.com/help-center/how-can-i-access-and-download-the-contract-note-248457/ ; https://upstox.com/help-center/understanding-the-contract-note-248458/
- Research indicates the pricing page contains historical and current rate sections, including STT/CTT changes effective 1 April 2026 and NSE transaction-charge changes effective 1 March 2026. Therefore, do not hardcode a single timeless rate or use a rate from the wrong effective period. BSE scrip-group variation, commodity/currency segments, option premium/futures turnover, DP charges, GST base composition and per-crore unit normalization require explicit rules.
- The authenticated brokerage API can calculate supported orders from instrument, quantity, product, side and price; the trades-charges API provides a segment/financial-year breakdown. Treat the latter as aggregate reconciliation only, not per-fill evidence.
- Next: implement a versioned tariff-rule model with effective dates, explicit normalized units/bases, source provenance and review status; add applicability/rounding/effective-date regression tests before wiring rules into durable per-fill allocation. Unknown or ambiguous cases remain fail-closed.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Effective-dated tariff registry groundwork — 23 October 2026

- Added `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md` (commit `de97bd3bfe90e82b888181cf109ed6a1b8e41d41`) documenting official Upstox pricing/API/contract-note sources, rate effective-date cautions, API limitations and the required provenance fields.
- Added `backend/app/services/broker_tariff_rules.py` (commit `0ec5590579c67c2575c8c4c72cf75bc56605120b`), a fail-closed rule selector requiring exact broker/exchange/segment/product/side/component/basis match, an effective date, source URL and SHA-256-shaped provenance, and APPROVED status. It rejects missing and overlapping rules and intentionally ships without active rates.
- Added `backend/tests/test_broker_tariff_rules.py` (commit `74240f2cc0af05befeee1fa97f988f2372a73be6`) covering exact-scope selection, review-state gating, scope mismatch, effective-date boundaries, overlap and invalid provenance/rates. CI has not yet returned a result for this latest test commit; do not mark it verified until the full workflow passes.
- This is rule-selection groundwork, not a complete tariff calculator and not proof that any specific rate is legally applicable. The next step is CI verification, then source-reviewed rules for specific segments/components and integration with durable per-fill allocation/reconciliation.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Tariff amount calculation and CI checkpoint — 23 October 2026

- Both the tariff registry regression-test commit `74240f2cc0af05befeee1fa97f988f2372a73be6` and its nine-document checkpoint `14fa83fe144228bb81a3b935b48b73c7f454afe2` passed their full Backend tests workflows: [code run 39953794565](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39953794565) and [documentation run 39953906848](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39953906848).
- Added `calculate_tariff_amount` to `backend/app/services/broker_tariff_rules.py`, with distinct `PERCENT`, `INR_PER_CRORE`, and `INR_FIXED` units and paise rounding. Added tests for units, rounding and invalid bases. Latest test commit is `782d2d2c63905adfa6862f43abcdc057c47894a7`; its CI is pending and must be verified before treating the new calculation as green.
- No live tariff rates are activated. The new calculator requires a previously selected approved rule; rule selection still fails closed for missing or overlapping rules. This does not yet integrate the registry with durable per-fill allocation or prove component-specific legal applicability.
- Next: verify CI on the latest code commit, then build reviewed, source-backed test fixtures for exact tariff applicability and connect approved component calculations to durable allocation/reconciliation without enabling ambiguous QUANTITY/NOTIONAL allocation.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Tariff calculation safety refinement — 23 October 2026

- Confirmed prior tariff-calculator code CI passed: [run 39954309954](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39954309954). The prior nine-document checkpoint CI also passed: [run 39954408580](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39954408580).
- Tightened `calculate_tariff_amount` so it refuses non-`TariffRule` values and any rule whose review status is not `APPROVED`. Added regression tests for DRAFT, REVIEWED and REJECTED rules.
- Latest safety-fix test commit: `83a70bdc88dfbc2cfabe8e80b8adfc858b516a6e`. Its full CI is pending; no green status should be inferred yet.
- Active rates remain intentionally absent pending rule-by-rule source verification and approval. Next: verify CI, then implement only specifically sourced rules with explicit applicability, normalized unit, basis, effective date and provenance before connecting to durable per-fill allocation.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Scoped tariff-calculation entry point — 23 October 2026

- Confirmed prior safety-fix code CI passed: [run 39954730200](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39954730200). The previous nine-document checkpoint also passed: [run 39954836920](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39954836920).
- Added `calculate_charge_for_trade` to `backend/app/services/broker_tariff_rules.py` (commit `d2d9c0c99a0cf31bca96fbde39c615b2569b1a97`) to select exactly one approved rule for the full trade scope/date and then calculate using its declared unit. Added tests for calculation result and fail-closed behavior without an approved match (commit `98c514d59d1b1da986a1d00117c2653c1e82d4c6`).
- Latest code CI is pending; do not mark this addition green until full Backend pytest, broker-write boundary, migrations and restore workflow pass.
- This entry point does not persist charge rows or allocate across fills. No production tariff rates are enabled. Next: verify CI, then design a persistence/integration boundary that records the selected rule version and calculation basis alongside the durable source component and per-fill allocation ledger.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Tariff CI verification and estimate/allocation boundary — 23 October 2026

- Verified full Backend CI passed for tariff calculation commit `98c514d59d1b1da986a1d00117c2653c1e82d4c6`: [run 39955151533](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39955151533). Verified the nine-document checkpoint CI passed for `2a5c3cf5075c2ab217603868f6272cc366784b26`: [run 39955284700](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39955284700). Both include pytest, broker-write boundary, SQLite and PostgreSQL migration downgrade/re-upgrade, and isolated synthetic restore steps.
- Added `docs/PHASE3_TARIFF_TO_FILL_ALLOCATION_DESIGN.md` (commit `a49b37509db1658ce7026f8328a35e26422afaad`) to define the boundary between a tariff estimate, actual broker-evidenced source charge and reviewed per-fill allocation; it sets out idempotency, immutable rule snapshots, component-specific acceptance gates and safety constraints.
- Next: CI-check this design/documentation checkpoint, then implement persistence for estimates as a separate, immutable, idempotent record before wiring estimates into source-charge reconciliation. Estimates must never be represented as contract-note actuals or automatically promoted into accounting.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Immutable tariff-estimate snapshot groundwork — 23 October 2026

- Added `backend/app/services/tariff_estimate_snapshot.py` (commit `00ec9fcd449fb9c9c091b29ebc7c68377246242b`) with canonical JSON snapshots, rule/source provenance, SHA-256 fingerprints, explicit calculation base/rounding metadata, stable idempotency keys and exact-replay/conflict comparison.
- Added `backend/tests/test_tariff_estimate_snapshot.py` (commit `f89517a3ca0bc034dc84da6d2239f0fd18026990`) for deterministic serialization, exact replay, conflicting base replay, changed rule, unapproved rules, invalid base, missing identity and effective-date rejection.
- This is a deterministic snapshot and replay-comparison layer only; it does NOT yet persist estimates. Durable enforcement still requires a database table with a unique idempotency constraint, transactional insert/read comparison and a migration tested on SQLite/PostgreSQL. No estimate can become a broker actual or source component.
- Latest code CI must be verified before this work is considered green. Next: confirm test and migration conventions, add durable persistence plus migration, concurrency-safe idempotency, and tests proving rollback/replay behaviour.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Snapshot CI verification and idempotency correction — 23 October 2026

- Verified CI passed for the immutable snapshot implementation `f89517a3ca0bc034dc84da6d2239f0fd18026990`: [code run 39956149855](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39956149855). Verified the associated nine-document checkpoint passed: [run 39956272786](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39956272786). Both runs completed pytest, broker-write boundary, SQLite and PostgreSQL migration downgrade/re-upgrade, and synthetic restore checks successfully.
- Code review identified an idempotency-key flaw: including the tariff rule fingerprint in the key would allow the same trade/component event with a changed rule to receive a new key instead of conflicting. Corrected `tariff_estimate_snapshot.py` so event key is stable across rate/rule changes, and changed the regression test to require a same-event rule change to fail as a conflicting replay.
- Latest correction commits: `204574082c7953ac08262a9f51801f04fd09ead7` and test `fafa26b6fb686471ac38a041256659b273f97712`. CI for this correction is pending.
- The snapshot remains in-memory/canonical only. Durable database persistence is not implemented yet; adding a table/migration requires identifying the current Alembic head and testing a unique idempotency constraint with transactional exact-replay/conflict behavior.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Durable estimate-only tariff persistence — 23 October 2026

- Verified the previous idempotency-correction code CI passed: [run 39956721476](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39956721476). Verified the previous nine-document checkpoint CI passed: [run 39956881266](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39956881266).
- Added `TariffEstimateSnapshotRecord` model and model registration (commits `08fec41026dabf250bd8756e0a711c20bbbf1e2a`, `0f47e07abd8bad51e4a7e11a851c726dd9008882`), Alembic revision `202610240015` after `202610240014` (commit `d98f5e259c610f8a5d392461ea1b75f6b9471912`), and `persist_tariff_estimate_snapshot` (commit `bc8b7bb2666e73cf30aa3fa4a796ebfe4e4874e5`).
- Added persistence regression tests for create/exact replay, changed-base conflict, changed-rule conflict, and estimate-only status (commit `cc121e7c710038ee25a434634a86ec4296cd0d68`). The unique database idempotency key is the concurrency arbiter; the service uses a nested transaction and leaves the outer commit to its caller.
- Latest implementation CI is pending; do not consider durable persistence verified until full pytest, broker-write boundary, SQLite/PostgreSQL migration downgrade/re-upgrade and synthetic restore checks pass.
- The database record stores only estimate snapshot JSON and a digest and has a database constraint that fixes status at `ESTIMATE_ONLY`; it does not create or modify contract-note actual charge/source-component rows.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Persistence CI result and append-only enforcement — 23 October 2026

- Full CI passed for durable estimate persistence implementation commit `cc121e7c710038ee25a434634a86ec4296cd0d68`: [run 39957564616](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39957564616). Backend pytest, broker-write boundary, SQLite and PostgreSQL migration downgrade/re-upgrade, and synthetic restore steps all succeeded.
- Review then identified that the database row had no ORM-level guard against updates to the snapshot payload. Added an append-only SQLAlchemy `before_update` guard to `TariffEstimateSnapshotRecord` (commit `596d4396bfaa58da3f4bf8ad11978370cfc8edf2`) and a regression test proving payload mutation is rejected (commit `af07ad77c3c7621774f49771c5d9cb4665778c03`).
- The append-only guard is an ORM protection, not a database trigger; direct SQL updates outside the ORM are not blocked by this guard. Consider a portable DB-level immutability trigger only if required by the release threat model. The unique key and ESTIMATE_ONLY check remain database-enforced.
- Latest append-only change CI and this documentation checkpoint's CI are pending. Do not treat them as verified until all jobs complete successfully.
- PR #6 remains draft and unmerged pending acceptance gates and explicit user approval. Live broker order writes remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Tariff estimate snapshot boundary (2026-10-23)

Tariff estimate snapshots are immutable, append-only audit records. Migration `202610240016` enforces this at the database layer with PostgreSQL and SQLite triggers rejecting UPDATE/DELETE; ORM guards and regression tests provide an additional layer. The snapshot's `ESTIMATE_ONLY` status is constrained separately. This record is not a broker actual and must never be used as the source amount for per-fill allocation. Actual per-fill charge allocation remains grounded in reviewed broker evidence and reconciled source components. Conditional/order-level tariff rules and variance-only estimate-versus-actual integration remain outstanding.


## Tariff snapshot transaction and audit guarantees (2026-10-23)

`TariffEstimateSnapshotRecord` remains `ESTIMATE_ONLY`, unique by idempotency key, and append-only at both ORM and database layers. Migration `202610240016` installs PostgreSQL/SQLite triggers blocking UPDATE/DELETE. Concurrent PostgreSQL tests validate exact replay convergence and conflicting-payload rejection. CI run 39960409771 passed 677 tests plus broker-write guard, migration round-trips and synthetic restore.

Architecture boundary: estimates can be compared to actuals for variance only. Per-fill actual allocation must originate from reviewed broker-evidenced source components. Conditional/order-level tariff caps, minimums, GST taxable-base composition and special charge models remain unsupported until modeled and tested.


## Estimate-versus-actual variance boundary (2026-10-23)

`TariffEstimateVarianceRecord` is a separate append-only audit table. The comparison service requires a valid estimate snapshot, exact broker fill identity, a VERIFIED source component, REVIEWED contract-note evidence with intact bytes, matching reviewer/broker/component/currency, and a manifest containing only that exact fill. It stores signed variance and percentage, but never mutates `BrokerChargeAllocation` rows or changes source/evidence status. CI run 39961777103 passed 680 tests plus broker-write, migration and synthetic restore checks.

Aggregate order-level/multi-fill variance is not supported. A single-fill estimate must not be compared to an aggregate actual amount. Advanced tariff caps, conditional rules and special component bases remain open.


## Verified exact PR-head CI 39962196672 — 2026-10-23
PR #6 head `c47bc3e3eeb4c8da4415132735d2d4ef457551f7` passed [CI](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39962196672): 680 passed, 1 warning; broker-write guard passed; no failed steps. Variance stays append-only and must not mutate allocation rows. Aggregate order/multi-fill actuals need an explicit scope model; advanced tariff shapes must be implemented and tested or fail closed.


## Aggregate variance scope proposal — 2026-10-23
The proposed design distinguishes a single `TRADE_FILL` from an `ORDER_FILL_SET` whose canonical exact member list is hashed and revalidated transactionally. Nonlinear/capped tariff calculations must occur at order scope. Variance records remain append-only and isolated from actual allocation/position/P&L writes. Aggregate support is not implemented yet.
