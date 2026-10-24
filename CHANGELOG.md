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


## 2026-10-24 — NSE IPFT representation reconciliation

- Added source-backed policy to `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md` in commit `295535e032a7ea542b67766c17e5186a83d54409`.
- NSE Circular NSE/FA/73061 confirms totals effective 1 March 2026: ₹307/crore cash, ₹183/crore equity futures, and ₹3,553/crore equity-option premium. Each splits into transaction-only ₹306.99/₹182.99/₹3,552.99 plus IPFT ₹0.01/crore.
- Upstox's public percentages are combined totals for those scopes; do not add IPFT a second time. Separate API fields require raw-response preservation and reconciliation to a dated contract note before canonical mapping approval.
- Documentation/research only: tariff candidates remain DRAFT, PR #6 remains draft/unmerged, live broker order submission remains disabled. Exact-head CI is required for this documentation commit.

## 2026-10-24 — IPFT combined-rate regression tests

- Added tests asserting NSE combined rates remain DRAFT/non-selectable, that no second IPFT tariff candidate is stacked on the combined rate, that GST base/amount are invariant between combined and split representations, and that NSE rates do not leak into MCX scope.
- Test commit: `69945f4854ea8ae7d20e7795b156750406759df7`.
- Updated source register with test scope and limitations in commit `626298aa9d8c60712189a744c86a3327eac1bb50`.
- These are synthetic consistency tests, not proof of live Upstox API field semantics or actual account-specific GST treatment. Exact-head CI is required; candidates remain DRAFT and PR #6 remains draft/unmerged.


## 2026-10-24 — IPFT exact-head CI result

- Recorded passing workflow #40101490646 for commit `a8166bafe77544bf958d0d393b71432379898b72`: 805 tests passed, 1 warning; broker-write guard and migration/restore checks passed.
- This CI result does not approve tariff candidates or establish live API field semantics/GST mapping. Candidates remain DRAFT, PR #6 remains draft/unmerged and live broker order submission remains disabled.


## 2026-10-24 — Historical Upstox statement evidence

- Recorded a user-provided redacted FY 2022–23 RKSV/Upstox Annual Global Transaction Statement screenshot in `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`, commit `9bb2fade8330e068022e5b2f6be0538e4f19206e`.
- The summary shows ₹111.61 transaction charges and no separately labelled IPFT row. This is not proof of bundling or API semantics; it is not an individual trade contract note. No actual per-fill charges are promoted and no tariff candidate is activated.

## 2026-10-24 — NSE IPFT rule clarified in source register

- Added the effective-dated scope and no-double-counting rule for NSE combined exchange outflow rates from 2026-03-01 to `UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`.
- The existing candidate implementation/tests already represent covered NSE rates as `exchange_charges` and assert that no separate `ipft` candidate is added. Candidate rules remain DRAFT/non-selectable; no live tariff activation.
- Source register commit: `6c85292d07d33e1e873293c40931895674f4e7fc`. Exact-head CI for this documentation checkpoint remains required.

## 2026-10-24 — Upstox response semantics and BSE/MCX scope

- Documented the distinction between Upstox's order-specific brokerage estimate and segment/FY trade-charge summary; missing/null/zero/numeric IPFT values must not be conflated.
- Added a secondary public schedule cross-check for BSE scrip/index-specific and MCX commodity rate boundaries; these remain research leads pending the governing exchange circulars.
- Source register commit: 2f6e55532e9704d4b41c9c736c38b1948ee5f05d. CI for this latest documentation head remains to be verified; no tariff candidates activated.

## 2026-10-24 — BSE/MCX tariff scope review

- Added official-source review notes for BSE scrip-group/exclusivity handling, BSE SENSEX monthly incremental slab mechanics, and MCX statutory charge scope. Source register commit: f978052402b2be79d99958427092a29eace83859.
- No generic BSE/MCX rates activated because the reviewed material does not prove all current effective-dated product schedules. Exact-head CI pending verification.


## 2026-10-24 — Exact-head Phase 3 CI and per-fill acceptance audit

- Verified open PR #6 head `5e256bc867409672a19025f0219c9d9c866ce898` with successful Backend tests workflow [#40105708790](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40105708790).
- Audited existing regression coverage for reviewed fill manifests/weights, source-document integrity, source-total and per-fill arithmetic, idempotent atomic promotion, authorization and rollback failures, and variance-only comparisons. No duplicate tests added in this checkpoint.
- Remaining gates are accounting policy acceptance by component, effective-dated authoritative tariff and GST mapping evidence, independent review, and final PR decision. Public tariff pages and the historical annual statement are not per-fill proof. Tariff candidates remain DRAFT/non-selectable; live broker writes remain disabled.
- Scope: `tarunsharma2610-del/tradepro-improved` only; original `Tradepro` remains out of scope.


## 2026-10-24 — Phase 3 charge component acceptance matrix

- Added docs/PHASE3_CHARGE_COMPONENT_ACCEPTANCE_MATRIX.md with source/effective-date, calculation-base, rounding/residual, GST/overlap, evidence and promotion gates for brokerage, STT, exchange/IPFT, SEBI, stamp duty and GST.
- Prior documentation head passed Backend workflow #40106273353; exact new matrix head is pending workflow #40106537998.
- No tariff candidates activated; automatic quantity/notional allocation remains disabled; PR #6 remains draft/unmerged; live broker writes remain disabled.
