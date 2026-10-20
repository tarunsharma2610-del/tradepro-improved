# Tradepro Improved — Master Roadmap

Last reviewed: 2026-10-21  
Repository: `tarunsharma2610-del/tradepro-improved`  
Working branch: `main`

## Rules of execution
1. Work only in this improved repository; never modify the original `Tradepro` repository.
2. Read `PROJECT_INSTRUCTIONS.md`, `PROGRESS.md`, `AUDIT_REPORT.md`, `ARCHITECTURE.md`, and `HANDOVER.md` before substantive work.
3. Implement one coherent slice at a time. No wholesale branch merges or unreviewed test-file copying.
4. No real broker orders in tests. Live order submission stays disabled.
5. Record exact commit SHAs and CI run URLs; don't label a checkpoint green until the run corresponds to the exact code HEAD.

## Current verified baseline
- Latest verified code/test checkpoint: `5ad579f60e78dcb5fdee14dcdb17dc4c9d8956a1`.
- [GitHub Actions run 39480669799](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39480669799): **432 passed, 1 warning**; SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade passed.
- 18 October safety checkpoint: [run 39140514552](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39140514552), SHA `9085d9fbdcc8ee2dd8baac6f5e73f92bd76cfa8b`, 456 passed, 8 skipped, 1 warning. It belongs to a materially different, diverged branch.
- Tree audit: `main` has 37 test modules; the safety branch has 48. Twenty-one safety-branch test modules remain absent from main; see `SAFETY_BRANCH_PORT_MATRIX.md` for the dependency map. This explains why the test suites differ, but doesn't mean 101 tests were removed from an identical code line.
- Migration graph: 14 files, one linear path from `202608170001` to `202610180008`; no missing parents. The live-fill service is present but unregistered.

## Roadmap and gates

### Gate 1 — Baseline reconciliation and documentation
- [x] Verify the exact 18 October CI checkpoint and current main CI checkpoint.
- [x] Compare test-tree and application-path differences across the two branches.
- [x] Audit the current main migration graph.
- [x] Record findings in `PROGRESS.md` and `AUDIT_REPORT.md`; restore current handover/roadmap documents on main.
- [ ] Verify CI after the documentation commits against the exact new HEAD.

### Gate 2 — Port missing safety behavior in dependency-complete slices
- [ ] Build a file-by-file dependency matrix for missing tests and required models, services, API routes, migrations, and configuration.
- [x] Port pure Upstox response parsing and regression tests as an isolated, read-only validation slice; exact-head CI passed 406 tests.
- [x] Port broker trade staging with current-main schema adaptations and fail-closed timestamp validation; exact-head CI passed 431 tests.
- [x] Add cumulative live-fill accounting guard so already-accounted trades plus a new trade cannot exceed the broker-confirmed child fill quantity; exact-head CI passed 432 tests.
- [ ] Resolve the dual intake representation (`BrokerFillIdentity` in the read-only worker versus `BrokerTradeRecord` in the staging/accounting service) and document a single authoritative path or transactional bridge before integration.
- [ ] Add focused regression coverage for idempotent trade identity, partial-fill aggregation, overfill rejection, batch rollback, malformed snapshots, and paper-accounting isolation as applicable to the chosen slice.
- [ ] Run focused tests, full backend pytest, PostgreSQL concurrency/integration tests, and reversible migrations on SQLite/PostgreSQL 16.
- [ ] Commit the slice and update progress/audit with exact-head CI evidence.

### Gate 3 — Live-fill accounting correctness
- [ ] Review `LiveFillAccountingService`, charge provenance, position math, and broker trade/order linkage.
- [ ] Implement a reviewed coordinator path for broker-confirmed trades with connection-scoped identity and transaction-safe idempotency.
- [ ] Prove replay safety, concurrency behavior, rollback behavior, partial fills, out-of-order updates, and crash/restart recovery.
- [ ] Ensure the paper `Position`, paper portfolio cash, and local order state cannot be changed by staged trades before validated promotion.
- [ ] Verify parent-order partial-fill and terminal-state behavior with integration tests.
- [ ] Keep the service unregistered until all gates pass and the path has been reviewed.

### Gate 4 — Live-trading release gates (blocked)
- [ ] Final race-safe safety interlock across authorization, intent claim, kill switch and broker request lifecycle.
- [ ] Broker status/fill/cancel reconciliation and ambiguous-outcome recovery.
- [ ] Account-level risk controls, circuit breaker, credential/token lifecycle and operational alerts.
- [ ] Exact-head unit, PostgreSQL concurrency/integration, migration, frontend build/typecheck, and security/source-guard checks.
- [ ] Backup-safe staging verification with no real-money order.
- [ ] Explicit user approval before any change that enables live submission.

## Current status and constraints
- Paper trading remains the usable execution mode. The current mainline includes portfolio risk controls, instrument-master sync, Upstox streaming, a read-only reconciliation interface/worker foundation, and live-fill accounting storage/service foundations.
- No claim of complete live trading, broker order submission, end-to-end live accounting, or production readiness is allowed.
- The original repository remains untouched. No production migrations or real broker orders have been performed.
