# Changelog

Changes that materially affect safety, accounting, integrations, or acceptance gates are recorded here.

## 2026-10-24 — Phase 3 accounting acceptance and Upstox source register

- Added `UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md` to separate broker estimates, realized charge evidence, and effective-dated tariff rules.
- Recorded the official Upstox Brokerage Details API and Profit and Loss on Trades API as relevant integration/evidence sources, with strict limits on what each source proves.
- Kept all tariff candidates DRAFT/non-selectable until authoritative source documents, effective dates, applicability, calculation bases, rounding and independent review are recorded.
- Verified the variance rollback regression fix at code commit `5e036d7fcc1f5f439d4054700366d284d7b78061`: Backend CI #40096380843 passed 793 tests with 1 warning; broker-write guard, SQLite/PostgreSQL 16 migration checks and synthetic restore drill passed.
- Latest documentation-only commits have not yet received a fresh exact-head CI result. PR #6 remains draft/unmerged. Live broker order submission remains disabled.
- Scope: `tarunsharma2610-del/tradepro-improved` only. Original `tarunsharma2610-del/Tradepro` remains out of scope.


## 2026-10-24 — Reviewed fill-ID input validation hardening

- Added defensive validation in `backend/app/services/broker_charge_source_reconciliation_service.py`: each reviewed allocation-weight `fill_record_id` must be a string before UUID parsing. This prevents malformed JSON values such as `null`, numbers, or arrays from escaping the expected validation path as an unexpected exception.
- Added parameterized regression coverage in `backend/tests/test_broker_charge_source_reconciliation_service.py` for `null`, numeric, and list-valued fill IDs. Expected behavior is a controlled `ValueError`; no allocation is promoted by this validation path.
- Code commit: `10febb7a14c779ab7e308b9175ff4f16ad5fec44`; regression test commit: `067e76687eda71aa81aae1df6b8b16133cf42d86`.
- CI for this new code/test head is not yet reported by GitHub Actions at the time of this note; the previous 793-pass run does not verify these new changes. Combined commit status currently reports no status checks for the new head, so this fix remains unverified pending CI.
- Phase 3 remains open: effective-dated tariff source approval, per-fill accounting acceptance, exact-head CI and final PR review remain required. PR #6 stays draft/unmerged; live broker order submission remains disabled.
- Repository boundary remains `tarunsharma2610-del/tradepro-improved` only; do not modify original `tarunsharma2610-del/Tradepro`.


## 2026-10-24 — Reviewed fill-ID validation CI result

- Exact code/test head `ddeed926a16f235de777025db1053d9e110bbc11` passed GitHub Actions run [#40099389651](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40099389651).
- Result: **796 passed, 1 warning in 43.75s**. Broker-write boundary guard passed; SQLite and PostgreSQL migration upgrade/downgrade/re-upgrade checks passed; synthetic PostgreSQL/document-volume restore drill passed.
- This CI includes the new parameterized regression tests rejecting malformed reviewed `fill_record_id` values (null, numeric, list) before UUID parsing. It does not yet include the documentation-only updates made after this code/test head.
- Phase 3 remains open: component-by-component per-fill accounting acceptance, authoritative effective-dated tariff evidence and independent review, and final PR gates remain outstanding. Tariff candidates stay DRAFT/non-selectable. PR #6 remains draft/unmerged. Live broker order submission remains disabled.
- Scope guard: only `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` must remain untouched.


## 2026-10-24 — Invalid reviewed-weight regression coverage

- Added regression tests in `backend/tests/test_broker_charge_source_reconciliation_service.py` for negative weights, non-finite weights (`NaN`, `Infinity`), malformed decimal values, all-zero weight sets, and duplicate fill IDs in the reviewed weights manifest.
- Each case must fail closed before allocation promotion and leave ledger rows in `PENDING_RECONCILIATION`.
- Test commit: `cb577cd1c917da9f2af1e5a01607dd42377067ca`. GitHub Actions backend workflow #40099823190 was still running at the time of this documentation update; do not treat the prior 796-pass run as verification of these new tests. The new documentation commits will also require exact-head CI verification.
- Phase 3 remains open: allocation acceptance, authoritative effective-dated tariff evidence and independent review, exact-head CI, and final PR gates are pending. PR #6 remains draft/unmerged; live broker order submission remains disabled.
- Scope guard: work only in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` must remain untouched.


## 2026-10-24 — Reviewed-weight validation tests CI verified

- Backend workflow [#40099906234](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40099906234) passed for code/test head `0d563f060055bb31c14a20f407a5f4b577843d48`: **802 passed, 1 warning in 48.62s**.
- The run includes the new invalid reviewed-weight regression cases (negative, NaN, Infinity, malformed decimal, all-zero and duplicate fill IDs), in addition to the malformed fill-ID tests. Broker-write boundary guard passed and synthetic restore-drill evidence was uploaded. The workflow also exercised PostgreSQL 16 migration downgrade/upgrade checks.
- This run verifies the code/test head before this documentation update, not the documentation commits below. A fresh exact-head CI result is required before treating the current branch tip as fully verified.
- Phase 3 remains open: per-component accounting acceptance and authoritative, effective-dated tariff evidence with independent review remain pending. PR #6 stays draft/unmerged; live broker order submission remains disabled.
- Repository scope is `tarunsharma2610-del/tradepro-improved` only. Do not modify original `tarunsharma2610-del/Tradepro`.
