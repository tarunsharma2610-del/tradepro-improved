# Tradepro Improved — Roadmap and Release Gates

Last reviewed: 2026-10-17
Scope: this repository only. The original `Tradepro` repository must remain untouched.

## Current verified checkpoint

- User-approved live-order idempotency/reconciliation design is implemented partially for Phase 1: [LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md](LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md).
- Architecture, safeguards, README, audit, project instructions and progress tracker link to the design.
- Phase 1 records/repository/tests are on `main`; latest verified code/test checkpoint `dd36b48a92057ad50618f6f9941f908832c9cea3` passed: [workflow 39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046), **215 tests passed, 1 warning**; the same run passed clean SQLite and PostgreSQL 16 Alembic upgrade → downgrade to `202610170001` → re-upgrade.
- The code checkpoint adds Phase 1 durable storage/repository safeguards and tests only. It does not implement live submission or reconciliation, does not run a production migration and does not prove live trading readiness.

## Status summary

| Workstream | Status | Evidence / next gate |
|---|---|---|
| Paper execution and existing safeguards | Existing functionality; preserve | Keep regression tests proving paper path cannot call live broker placement |
| Instrument-master snapshot validation | Implemented and regression-tested; operational sync was disposable/in-memory | Repeat verified staging sync before deployment; never mutate production from an incomplete snapshot |
| Upstox V3 WebSocket authorization/reconnect protections | Partial implementation and unit/regression coverage | Real authorized session test remains open; shared stream state across workers remains open |
| Portfolio-wide risk controls | Existing configurable controls, still require deployment-aware review | Confirm atomic reservations, exposure semantics and user-adjustable thresholds; don't represent cost-basis/realized-loss checks as mark-to-market broker margin |
| Durable live-order idempotency | Phase 1 partially implemented; CI green for latest code checkpoint | Add concurrency/race tests and cross-database migration review; no broker submission |
| Broker order/trade reconciliation | Design only | Phase 2 reconciliation-only service; no order placement |
| Live submission orchestration | Not implemented / disabled | Sandbox-only workflow after prior phases pass |
| Production deployment verification | Incomplete | Backup-restored staging migration against actual DB engine, rollback/restore drill and operational runbook |

## Ordered roadmap

### Gate 0 — Design review (complete — user approved 2026-10-17)
- Read [PROJECT_INSTRUCTIONS.md](PROJECT_INSTRUCTIONS.md), [ARCHITECTURE.md](ARCHITECTURE.md), [LIVE_TRADING_SAFEGUARDS.md](LIVE_TRADING_SAFEGUARDS.md), [AUDIT_REPORT.md](AUDIT_REPORT.md), and [LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md](LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md).
- Confirm order-field canonicalization, supported Upstox products/order varieties, broker tag limits, order-history/trade API semantics and status mapping against current official docs.
- User explicitly approved `LIVE_ORDER_IDEMPOTENCY_RECONCILIATION.md`; approval is recorded in `PROGRESS.md`. This authorizes Phase 1 durable storage/repository safeguards only, not live-order submission.

### Gate 1 — Durable records only (no broker POST) — in progress
- [x] Additive SQLAlchemy records and Alembic migration for live intents, audit events, dispatch/outbox and broker-fill identities.
- [x] Unique idempotency key scoped to user/broker connection, canonical JSON payload hash, same-key/same-payload reuse and same-key/different-payload conflict.
- [x] Transactionally persist intent + initial event + outbox; enforce portfolio and broker-connection ownership in the repository.
- [x] Focused repository tests and clean SQLite Alembic migration run passed in GitHub Actions: [run 39043177545](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39043177545), 210 tests passed, 1 warning.
- [x] Add rollback atomicity test and a deterministic independent-session simulation of a competing unique-key winner; repository recovery returns the committed winner.
- [x] Validate order snapshots and audit event details as finite JSON and reject credential-like keys (nested access/refresh tokens, secrets, passwords, API keys, authorization headers and cookies); regression tests pass.
- [x] Add simultaneous same-key creation coverage using two independent PostgreSQL sessions and a barrier that forces both requests past an initial empty lookup; [workflow 39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046) passed.
- [x] CI verifies clean SQLite and PostgreSQL 16 upgrade → downgrade of revision `202610170002` → re-upgrade: [run 39048147046](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39048147046).
- [ ] Verify upgrade/downgrade and constraints against a backup-restored staging copy of the actual deployment DB engine. No production migration has run.
- Scope boundary: no worker, API route or code path submits/cancels/reconciles broker orders in this phase.

### Gate 2 — Reconciliation-only workflow
- Normalize broker order book/history/details/trades into local states.
- Deduplicate fills by documented stable broker trade identity.
- Handle partial fills, duplicate/out-of-order updates, missing/multiple tag matches, unknown statuses, API outages, session boundaries and sliced orders.
- No order-placement call in this phase.

### Gate 3 — Disabled sandbox submission workflow
- Transactionally persist intent, risk decision, audit and outbox before network I/O.
- Unknown submission after timeout/crash is reconciled; never blindly retry an ambiguous POST.
- Test crashes before/after broker acceptance, concurrent workers, rate limits, token expiry, rejection and cancellation races with mocks/sandbox only.
- Global live-submit switch stays hard-disabled in deployed configuration.

### Gate 4 — Operational readiness
- Verify account kill switch, portfolio risk recheck/reservation, alerts, safe audit redaction, monitoring, backup/restore, migration rollback and incident runbook.
- Verify real authenticated market-data stream separately; stream verification is not order-path certification.
- Resolve process-local WebSocket state before using multiple API workers.

### Gate 5 — Explicit controlled release
- Requires successful prior gates, official API contract verification, broker/account configuration, applicable compliance review and explicit user authorization.
- Start with a limited manually confirmed pilot and low risk limits. No autonomous live rollout by default.

## Completion/reporting rules

- After every meaningful change, update `PROGRESS.md`; update `AUDIT_REPORT.md`, `README.md`, `ARCHITECTURE.md` and safeguards when the verified behavior or safety boundary changes.
- Commit changes to `tradepro-improved` and verify the exact commit SHA and GitHub Actions result. A successful older workflow does not validate a newer commit.
- Distinguish implemented, unit-tested, sandbox-tested, staging-verified and production-verified states. Never claim a real Upstox session or order test without evidence.
- Keep live trading disabled until all release gates and explicit authorization are complete.
