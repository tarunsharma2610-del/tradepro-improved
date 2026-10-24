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


## 2026-10-24 — Lossless broker charge API field normalization

- Added a normalization helper and tests preserving MISSING, NULL, ZERO, VALUE and INVALID states without inferring whether an API amount is combined, aggregate or per-fill.
- Exact-head CI is required for the new code/test commits; prior matrix head passed workflow #40106582037.
- No tariff activation, automatic allocation enablement, PR merge or live broker writes.


## 2026-10-24 — Reviewed broker API mapping gate

- Added an exact-scope, effective-dated mapping registry for broker charge API fields. Only approved mappings matching broker, endpoint, schema version, field path, scope and trade date can be selected; unknown/unapproved/overlapping mappings fail closed.
- Field-state normalizer CI passed in workflow #40106757433 on commit `f0e815c5b788744966bf2bacbfbe9c79dbfdd822`. New mapping code/tests and follow-up documentation still require exact-head CI.
- No live API semantics were approved, no tariff activated, no PR merge, and no live broker writes.


## 2026-10-24 — API mapping CI checkpoint

- Verified successful Backend workflows #40106949357 for the API mapping guard/test commit and #40106989369 for the source-register documentation commit.
- Exact-head CI remains required after subsequent documentation changes. No production Upstox mapping or tariff was approved.


## 2026-10-24 — Controlled charge API value resolution

- Added resolver + regression tests requiring exact approved mappings and preventing aggregate/estimate fields from being consumed as per-fill actuals. Missing/null/invalid values remain unusable; numeric zero is preserved as a separate state.
- Synthetic fixtures do not approve any live Upstox API semantics. Exact-head CI remains pending for these new changes.


## 2026-10-24 — Charge API unusable-value provenance hardening

- Review found that `resolve_charge_api_value` retained the approved mapping's semantic and source fingerprint for usable values, but omitted source URL and SHA-256 provenance when the normalized field was `MISSING`, `NULL`, or `INVALID`. These values were already unusable, but their interpretation path was less auditable.
- Fixed the resolver to return approved mapping provenance for every normalized state while keeping missing/null/invalid values `usable=False`. Numeric zero remains a distinct present value; this change does not promote allocations or approve production Upstox mappings.
- Added regression coverage for missing, null, NaN, negative, boolean, and object values; assertions now require mapping source URL, source SHA-256, and semantic to remain present. Added mapping effective-date and estimate-vs-actual guard cases.
- Implementation commit: `845e9e0dc924f11ae89b96ef73c94c59c2efb4b4`. Test commit / branch head: `1d7e24b0ba8c89062ec1eeddb93d0c4cd22a226f`.
- Exact-head backend CI is running as workflow [#40107754617](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40107754617); do not mark this code/test head green until all workflow gates complete successfully.
- PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains out of scope.


## 2026-10-24 — Effective-date test fixture correction

- CI exposed one failing test among 850 total: the future-date case expected rejection while its synthetic mapping used `effective_to=None` (no end date). The resolver behavior was consistent with the fixture.
- Corrected the synthetic approved mapping to an explicit validity window ending `2026-12-31`, so both before-start and after-end cases test the intended boundary.
- Test fix commit: `9cb89301075a8b532ad634f2c9c60590b16deacc`. Awaiting CI for this commit and the final branch head; earlier run #40107829270 failed on the incorrect fixture and must not be treated as green.
- PR #6 remains draft/unmerged. Live broker order submission and automatic quantity/notional allocation remain disabled. Work stays in `tradepro-improved`; original `Tradepro` remains out of scope.


## 2026-10-24 — Intended-use semantic matrix regression tests

- Corrected effective-date fixture commit `9cb89301075a8b532ad634f2c9c60590b16deacc` passed its backend workflow (#40107967404); progress and handover documentation workflows also passed (#40107977310 and #40107980514). Latest branch documentation head `26daee136ab1e7b3dd9a9d985f986e063bb8f80e` passed workflow #40107984994. PR #6 remains draft/unmerged.
- Added resolver tests ensuring mapping semantics cannot be relabelled across intended use: per-fill actual, aggregate summary, and estimate; included valid semantic/use pairs and rejection of an unknown intended use. Test commit: `53ba96dc3700de75a64b415c095f6a5810efdaf0`.
- New test commit still requires CI. This test-only step does not approve production broker mappings, enable allocation promotion, or enable live broker order submission.
- Next accounting acceptance gap: test concurrent verification/promotion against a shared database with separate sessions, or explicitly document the limitation if the existing test harness cannot reliably exercise it. Keep lock order and rollback protections intact.
- Work remains in `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is out of scope.


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


## 2026-10-24 — Official tariff/API source audit

- Upstox Developer API `GET /v2/trade/profit-loss/charges` is scoped by segment, financial year and optional dates; it returns a `charges_breakdown` summary, not a documented per-fill record. Its published example has `charges.ipft: null`. Do not use this endpoint alone to ground actual per-fill charges; null remains distinct from zero. https://upstox.com/developer/api-documentation/get-trade-charges/
- NSE Finance & Accounts circular NSE/FA/73061 dated 27-Feb-2026 is effective 1-Mar-2026: combined member outflow ₹307/crore cash, ₹183/crore equity futures, ₹3,553/crore equity-options premium; IPFT contribution ₹0.01/crore each side. This is scoped exchange schedule evidence, not proof of Upstox's contract-note field mapping. https://nsearchives.nseindia.com/content/circulars/FA73061.pdf
- Upstox's public charges page lists newer effective-date summary tables alongside older historical tables. Apply effective-dated versioning; don't select stale rates based on page position. STT/CTT values also change from 1-Apr-2026 on the published page. https://upstox.com/brokerage-charges/
- No production mapping or tariff is approved. Keep mappings DRAFT; reject aggregate/estimate/null values for actual per-fill evidence; do not separately add IPFT where already included in combined exchange outflow.
- Latest code/test head before this note, `ee1b2a74d2a9f6141b9afbb6e06562b5cf263a9b`, passed Backend workflow #40110597753. This documentation change needs fresh CI verification.
- PR #6 remains draft/unmerged. Live order submission and automatic quantity/notional allocation remain disabled. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.
