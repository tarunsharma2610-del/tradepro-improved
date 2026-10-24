# Phase 3 accounting acceptance review — 24 October 2026

## Exact-head CI result
- Branch: `phase3/durable-per-fill-charge-allocation`.
- Documentation checkpoint commit: `eea64329723715857f274e6694bbc37a8daa4e39`.
- Exact-head GitHub Actions run: [40088788447](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40088788447) — **success**.
- Completed: backend pytest, broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, evidence-artifact retention.
- This is CI validation, not proof of production financial correctness, real cloud backup recoverability, or broker-origin authenticity.

## Code-review observations
1. Live-fill accounting verifies six reconciled charge components against reviewed source components and the target fill manifest before accounting writes. Caller-supplied amounts are treated as consistency assertions, not as the source of truth.
2. Source-component verification is read-only and checks the stored source bytes, independent reviewer provenance, canonical fill manifest, fill-set digest, full allocation set, exact source total, and individual allocations against reviewed weights.
3. Tariff estimate snapshots are persisted with immutable canonical JSON/digest semantics. Estimate-versus-actual comparisons write separate `VARIANCE_ONLY` records and do not promote allocations.
4. Reviewer authorization is checked at promotion time by `promote_verified_component_allocations`: the recorded reviewer must still exist, be active, and hold platform-admin status. Regression `test_promotion_rechecks_admin_role_at_time_of_promotion` verifies a role/status change blocks promotion and leaves allocations pending. The standalone source-component verification helper is read-only; the promotion service is the enforcement boundary.
5. Regression coverage is present for partial fills/cancelled orders, staged child-fill completeness, cumulative quantity limits, failed flush/commit rollback, post-commit refresh failure followed by exact replay, and PostgreSQL concurrency between live-fill accounting and charge-component verification/promotion. The concurrency test explicitly allows the live fill to fail closed while the component is still pending, then verifies retry succeeds and exactly one execution/position remains. The dedicated component-promotion race also verifies source verification and promotion serialize on PostgreSQL.

## Decision / next work
- No production live-order execution is enabled by this review.
- Do not merge PR #6 yet; keep it draft pending explicit accounting acceptance.
- Do not add duplicate tests for scenarios already covered. Remaining work is a focused review of whether write-boundary failure injection is sufficient, reconciliation of the source-approved tariff/GST scope, and exact-head CI after documentation changes.
- Only work in `tarunsharma2610-del/tradepro-improved`; never modify `tarunsharma2610-del/Tradepro`.

## Flush-failure regression and exact-head CI — 24 October 2026

- Added `test_flush_failure_after_accounting_rows_are_staged_rolls_back_everything` to `backend/tests/test_live_fill_accounting_service.py` in commit [`6ee7b122e139f3ce923635a81944a43dd86da46e`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/6ee7b122e139f3ce923635a81944a43dd86da46e).
- Exact-head Backend tests workflow [#40091448624](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40091448624) completed successfully. Pytest, broker-write boundary guard, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and evidence retention all passed. PostgreSQL-specific tests were enabled by the CI job configuration.
- The new regression injects a flush failure while execution/live-position rows are pending, then asserts no execution or live position remains and the paper position is unchanged. This supplements existing staged-row, failed-commit, and post-commit refresh/replay tests; it does not claim every conceivable persistence failure point is covered.
- This exact-head CI result applies to the code/test commit above. This documentation update and any subsequent commit require their own exact-head CI run.
- Phase 3 accounting acceptance remains open for final review and remaining tariff/source applicability decisions. PR #6 remains draft/unmerged; live broker order submission remains disabled. Work only in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` remains out of scope.

## Exact-head CI checkpoint — 24 October 2026

- Documentation checkpoint commit `3e0ae8034f333e082bfa11b6da50aec9e620f242` passed GitHub Actions Backend tests run [`40091642139`](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40091642139).
- Result: **787 passed, 1 warning** in pytest. Broker-write boundary guard passed; SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed; synthetic PostgreSQL/document-volume restore drill and evidence-artifact retention passed.
- The warning is a Starlette/AnyIO deprecation warning; the run also reports GitHub Actions Node.js 20 deprecation notices. No test or safety-guard failure was reported.
- This verifies commit `3e0ae803` only. Any new documentation commit must receive its own exact-head CI run before the checkpoint is considered green.
- Phase 3 remains open pending final accounting acceptance and tariff-source applicability decisions. PR #6 remains draft/unmerged; live broker order submission remains disabled. Work only in `tarunsharma2610-del/tradepro-improved`, never the original `tarunsharma2610-del/Tradepro`.

## Latest exact-head CI verification — 24 October 2026

- The documentation checkpoint at branch head commit `8c97a952eadec31ce302d42907a3e8516c160ae8` passed Backend tests workflow [#40091844691](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40091844691).
- Pytest: **787 passed, 1 warning**. Broker-write boundary guard passed. SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade checks passed. Synthetic PostgreSQL/document-volume restore drill and evidence retention passed.
- The pytest warning is Starlette/AnyIO deprecation; the workflow also emits Node.js 20 deprecation notices. No test or broker-write guard failure was reported.
- This validates the code and documentation state at `8c97a952`; future changes need their own exact-head CI run.
- This is not production financial validation or proof of broker-document authenticity. Accounting acceptance remains open for the explicitly documented tariff applicability, GST component mapping, reviewer policy, and residual failure/concurrency coverage decisions. PR #6 remains draft/unmerged; live broker order submission remains disabled. Work only in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` is out of scope.
