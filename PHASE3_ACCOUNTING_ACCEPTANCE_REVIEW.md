## Authoritative Phase 3 checkpoint — 26 October 2026 (latest verified CI)

- Target repository only: `tarunsharma2610-del/tradepro-improved`; branch `phase3/durable-per-fill-charge-allocation`; implementation/test head `44830ec48b50b4f470ec9ca95dd2d3f4339dd3df`. Do not modify original `Tradepro`.
- Exact-head Backend CI: [run #40294178677 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40294178677), including the test separating NSE/IPFT arithmetic reconciliation from GST taxable-base approval.
- GST estimate helper accepts exactly 18%; tests reject 0%, 5%, 100%, and 100.01%. This is a rate guard only; taxable component composition remains evidence/reviewer-controlled.
- ₹307/crore versus ₹306.99/crore transaction charge + ₹0.01/crore IPFT is arithmetic reconciliation only, not GST-base approval.
- Canonical live-fill integration is verified: six independently verified charge snapshots, source/mapping/fill evidence revalidated under lock, no raw-only fallback; brokerage cap applied once before deterministic paise-exact allocation.
- Remaining Phase 3 gates: effective-dated tariff applicability; component-specific per-fill allocation acceptance; invoice/source-backed GST/IPFT and product/segment evidence; adversarial/migration/recovery review; final exact-head documentation/sign-off. Do not redo canonical integration.
- Upstox public schedules/calculator are estimates; aggregate charges endpoint is not actual per-fill evidence. Null remains unknown, not zero. Synthetic restore is not actual Oracle recovery.
- PAPER mandatory; live broker writes, automatic live-fill promotion and automatic scheduling disabled. PR #6 stays open/draft/unmerged unless explicitly approved. Defer AI/open-source adaptations until Phase 3 acceptance. This docs commit needs its own CI.

---

## Canonical checkpoint reconciliation — 26 October 2026 (canonical live-fill integration verified)

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. Never modify original `tarunsharma2610-del/Tradepro`.
- **Latest verified implementation head before this documentation sync:** `255fc208eed4bc8b922977717209d27912055377`. Exact-head Backend CI [run #40286205714 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40286205714): **962 passed, 1 warning**. Broker-write boundary guard, SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade, synthetic PostgreSQL/document-volume restore, and restore-evidence retention all passed. Synthetic restore does not prove actual Oracle Cloud recovery.
- **PR #6:** open, draft, unmerged. Do not merge without explicit user approval.
- **Phase 3 integration completed on this head:** `LiveFillAccountingService` now requires exactly six independently verified canonical charge snapshots. It revalidates each canonical ledger and its source hashes/links/mapping version, reviewed fill manifest and weights, INR totals, durable reconciliation references, and the contract-note reference under lock. There is no fallback to raw-only legacy allocation rows. Extra, unmapped, unlinked, or foreign-connection per-fill allocations fail closed.
- **Integration tests:** canonical snapshot creation → independent review → allocation → reconciliation; direct and combined/split transaction/IPFT source lines canonicalize to one exchange-charge component; exact replay, missing/unreconciled/extra allocations, and PostgreSQL live-fill-versus-ledger promotion race. No live broker order writes are enabled.
- **Remaining Phase 3 gates:** (2) independently reviewed effective-dated tariff applicability; (3) approved component-specific per-fill allocation rules; (4) invoice/source-backed GST/IPFT and product-specific component acceptance; (6) final adversarial, migration and recovery review; (7) exact-head documentation/sign-off. Official public tariff snapshots are research evidence, not proof of account-specific actual charges; candidate rates remain DRAFT until the required review is recorded. Synthetic restore is not a real Oracle recovery test.
- **Upstox controls:** no unused SDK runtime dependency; Agent Skill remains development/static-review-only; brokerage calculator is estimate-only; aggregate charge endpoints are not per-fill actual evidence.
- **Safety invariants:** PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. Keep PR #6 unmerged until explicit approval.
- **Next step:** resume at the remaining Phase 3 tariff/component evidence gates. Do not repeat canonical snapshot integration. Do not begin the separate AI/open-source adaptations until Phase 3 acceptance is complete.
- **Documentation-sync note:** this multi-document commit must pass its own exact-head CI before the next implementation change.

---


---

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

## Accounting acceptance CI — 24 October 2026

- Commit `0dee50af510c1f47e50093a3f796aef5fb32707b` passed Backend tests workflow [#40092273865](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40092273865).
- Pytest result: **787 passed, 1 warning in 48.24 seconds**. Broker-write boundary guard passed. SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade checks passed. Synthetic PostgreSQL/document-volume restore drill and evidence retention passed.
- The pytest warning is the Starlette/AnyIO `BlockingPortal` deprecation; the workflow also emitted Node.js 20 / dependency deprecation notices. No test or broker-write guard failure was reported.
- This validates commit `0dee50af` only. Any later change requires its own exact-head CI run.
- Acceptance remains open: tariff candidates are not approved; the current NSE source register explicitly limits what the NSE circular establishes, and actual Upstox invoice/contract-note evidence is still needed to approve product-scoped GST and tariff component mapping. Targeted rollback tests exist, but they are not exhaustive fault injection. PR #6 remains draft/unmerged and live broker order submission remains disabled. Work only in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` is out of scope.

## Upstox charge API audit and exact-head CI checkpoint — 24 October 2026

- Added official API guidance to `PROJECT_INSTRUCTIONS.md` and expanded `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`: use Brokerage Details API (`GET /v2/charges/brokerage`) for estimates; use supported selected-scope P&L charge breakdowns (aggregate, not per-trade) for reconciliation; compare realized charges with authenticated trade history and an actual broker-issued contract note/tax invoice.
- Exact branch head `640ebfba38a96c7d84d4ffc3501afcd2278b551b` passed Backend workflow [#40092513016](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40092513016): **787 passed, 1 warning in 48.85s**. Broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore drill, and evidence retention passed.
- Warning: Starlette/AnyIO `BlockingPortal` deprecation. Workflow also reports Node.js 20 and dependency deprecation notices. No test or broker-write guard failure was reported.
- Source discovery is not approval: no account-specific Upstox response or contract-note fixture was verified here. GST taxable-component mapping and tariff scope/effective dates remain unapproved; candidate rules remain inactive. Do not double-count legacy IPFT with the current combined NSE transaction schedule.
- Future documentation/code commits need their own exact-head CI run. This entry records the successful run above only.
- PR #6 remains draft/unmerged; live broker order submission remains disabled. Work only in `tarunsharma2610-del/tradepro-improved`; never modify the original `tarunsharma2610-del/Tradepro`.

## Upstox API coverage and tariff-source correction — 24 October 2026

- Added read-only `get_profit_loss_report` for official `GET /v2/trade/profit-loss/data`, with fixed endpoint, segment/financial-year/date/pagination validation, and regression coverage. The API supplies paginated trade-wise realized P&L rows but does not document per-row charge components; do not treat it as per-fill charge evidence.
- Kept the three Upstox surfaces distinct: `/charges/brokerage` is a request-specific estimate; `/trade/profit-loss/charges` returns selected-scope aggregate charge components; `/trade/profit-loss/data` returns trade-wise P&L rows. Contract-note evidence and reviewed allocation rules remain required for charge promotion.
- Corrected DRAFT equity STT candidates for delivery buy/sell (0.1%) and intraday sell (0.025%) to the source-stated 1 April 2023 effective date rather than incorrectly implying a new 1 April 2026 effective date. Added regression coverage. All candidate rules remain DRAFT and non-selectable.
- Intermediate backend CI run [#40093110292](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40093110292) passed **789 tests, 1 warning** plus broker-write guard; however, this run predates the final effective-date correction. Latest exact-head validation is still running in [#40093198960](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40093198960); do not mark the latest head green until it completes successfully.
- PR #6 remains draft/unmerged and live broker order submission remains disabled. All work is in `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` remains out of scope.

## Upstox P&L metadata API — 24 October 2026

- Added fixed-path read-only `get_profit_loss_report_metadata` for `GET /v2/trade/profit-loss/metadata`. It validates segment, financial year and optional date scope, and exposes the documented `trades_count` and `page_size_limit` metadata used to plan pagination of `/trade/profit-loss/data`.
- Added regression tests for normalized request scope, returned page-size metadata, and invalid scope/date rejection. The metadata endpoint contains no charge components and does not alter the contract-note evidence requirement.
- The metadata API and regression tests passed exact-head CI in [run #40093554718](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40093554718): 792 tests passed, 1 warning; broker-write guard, SQLite/PostgreSQL 16 migration checks, and synthetic restore/evidence retention passed.
- Tariff candidates remain DRAFT/non-selectable; PR #6 remains draft/unmerged; live broker order submission remains disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope.

## Latest verified checkpoint — 24 October 2026

- Exact-head CI for the Upstox P&L metadata API and its regression tests completed successfully in [run #40093554718](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40093554718): **792 tests passed, 1 warning**; broker-write boundary guard, SQLite migration round-trip, PostgreSQL 16 migration round-trip, isolated synthetic restore drill, and restore evidence retention all passed.
- The metadata endpoint is read-only and provides `trades_count` / `page_size_limit`; it informs pagination only. The P&L data endpoint remains trade-wise matching context, not per-fill charge evidence. The charges endpoint remains aggregate scope only.
- The three equity STT DRAFT candidates now use the source-stated 1 April 2023 effective date; candidates remain non-selectable. No charge-allocation or tariff-promotion gate has been bypassed.
- PR #6 remains draft/unmerged. Live broker order submission remains disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; the original `tarunsharma2610-del/Tradepro` is untouched.
- Next Phase 3 work: resume the durable per-fill charge-allocation acceptance audit, especially evidence identity/matching, rounding/residual handling, replay/idempotency, rollback, and aggregate variance regression coverage. Do not promote tariffs or allocate aggregate charge totals across fills without an approved deterministic policy and reviewed contract-note evidence.

## Variance rollback regression added — 24 October 2026

- Added `test_variance_insert_flush_failure_rolls_back_record_without_mutating_accounting` in `backend/tests/test_broker_charge_source_reconciliation_service.py`.
- The regression injects a failure at variance-record flush and asserts the nested savepoint leaves no variance row and does not mutate reviewed evidence, source component data, or pending allocation rows.
- Commit: `edbc0852a72978577d8da8651e8fdce932e9593d`. Exact-head CI must complete before this test is considered verified; the prior successful run does not cover this new test.
- Phase 3 acceptance remains open pending CI, source-backed tariff/GST mapping, and final charge-allocation acceptance. Tariff candidates remain DRAFT; live broker order submission remains disabled; PR #6 remains draft/unmerged.


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

- Latest PR head `ed346e823cbfae8448fae0134c4ff864bfcc60ac` passed Backend workflow [#40109041654](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40109041654). This verifies the field-identity guard and regression test at that head.
- Located PostgreSQL-only integration tests in `backend/tests/test_broker_charge_allocation_postgres_concurrency.py`, including concurrent source verification vs allocation promotion and live-fill promotion vs ledger verification, as well as conflicting fill-set and tariff estimate/variance persistence races.
- These tests require `TEST_POSTGRES_URL`. Verify the PostgreSQL workflow actually ran these tests rather than skipped them before treating concurrency acceptance as complete.
- PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled; production Upstox mappings/tariffs remain unapproved. Work only in `tradepro-improved`; original `Tradepro` remains untouched.


## 2026-10-24 — Accounting invariant audit checkpoint

- Reviewed `backend/app/services/live_fill_accounting_service.py` and its unit tests. New accounting writes (live position mutation and execution insert) are committed in one transaction; all exceptions roll back. A post-commit refresh failure is covered by retry-as-exact-replay tests.
- Verified test coverage for exact replay, conflicting fill/evidence payloads, unchanged paper position and portfolio cash, failed flush/commit rollback, charge totals matching six components, and deterministic paise allocation.
- Dedicated PostgreSQL concurrency tests exercise verification-vs-promotion, live-fill-vs-ledger verification, conflicting fill sets, and concurrent tariff snapshot replay/conflict. CI on head `bacbe9dd9dfa35d739bbcea2bfece6185dc391d0` passed workflow [#40109864007](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40109864007). This passing head predates the present audit-note commit(s); recheck CI on the new head.
- Remaining acceptance is not waived: ensure the PostgreSQL-only tests are exercised by required CI with `TEST_POSTGRES_URL`, verify latest branch checks after this documentation change, and continue authoritative tariff/API-field review. Synthetic test fixtures do not approve production tariff semantics.
- PR #6 remains draft/unmerged. Live broker order submission and automatic quantity/notional allocation remain disabled. Production Upstox mappings/tariffs remain unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Official tariff/API source audit

- The documented Upstox charges endpoint returns segment/financial-year/date-range aggregate breakdowns, not documented per-fill charge evidence; its example has `ipft: null`. Null remains distinct from zero and aggregate data cannot satisfy actual per-fill acceptance. https://upstox.com/developer/api-documentation/get-trade-charges/
- NSE/FA/73061 (27-Feb-2026; effective 1-Mar-2026) states combined outflow ₹307/crore cash, ₹183/crore equity futures and ₹3,553/crore equity-option premium, including ₹0.01/crore IPFT each side. Do not add IPFT a second time to those combined rates. https://nsearchives.nseindia.com/content/circulars/FA73061.pdf
- Upstox public pricing tables contain historical and newer effective-date values, including STT/CTT effective 1-Apr-2026. Tariff acceptance must bind broker, exchange, segment/product, basis, side and effective date; unresolved scopes remain blocked. https://upstox.com/brokerage-charges/
- These source findings do not approve production mappings. Backend workflow #40110597753 passed on prior head `ee1b2a74d2a9f6141b9afbb6e06562b5cf263a9b`; new docs require CI on the latest head. PR #6 draft/unmerged; live order submission and automatic quantity/notional allocation disabled.


## 2026-10-24 — Aggregate endpoint hard guard added; CI pending

- Upstox `/v2/trade/profit-loss/charges` is now explicitly blocked from `PER_FILL_ACTUAL` resolution regardless of a misleading mapping semantic. Its published schema is aggregate `charges_breakdown`, not per-fill evidence.
- Regression test `test_official_upstox_aggregate_charges_endpoint_cannot_be_promoted_to_per_fill` covers the guard. Implementation `cdc07afdd8cc0c8d0b37d7e4aa8cdf1bf6eac651`; test `8ae749017a8ba0016f2c9adeb77eaff41fb5ae70`. Latest test CI must pass before verification is complete.
- Keep production mappings/tariffs unapproved; null distinct from zero; automatic quantity/notional allocation and live order submission disabled. PR #6 draft/unmerged; original `Tradepro` out of scope.


## 2026-10-24 — Upstox brokerage calculator restricted to estimates; CI pending

- Official Upstox `GET /v2/charges/brokerage` takes proposed instrument, quantity, product, transaction type and price, returning a charge calculation; this is not proof of final booked per-fill charges. https://upstox.com/developer/api-documentation/get-brokerage/
- Resolver now blocks `/v2/charges/brokerage` from `PER_FILL_ACTUAL` and actual `AGGREGATE_SUMMARY` use even if a mapping is misleadingly labelled. Existing guard still blocks `/v2/trade/profit-loss/charges` from per-fill actual use. New regression tests cover both misuse cases.
- Implementation `3486d854dae2451858a858cb627602aca7338969`; tests `6c92101a1890a0f4d761e86ed3db047a269fd10d`. Prior head `6cc8b58f635fcb4f1b1cb3e5997099d074800a28` passed workflow #40111501429. CI for the new commits must be verified.
- Production mappings/tariffs remain unapproved; null is not zero; automatic quantity/notional allocation and live broker order submission remain disabled. PR #6 stays draft/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Authoritative checkpoint — 26 October 2026 (documentation CI verified)

- Repository: `tarunsharma2610-del/tradepro-improved`; branch: `phase3/durable-per-fill-charge-allocation`.
- Latest implementation commit: `ac7d27f2c9922925483b5b906c484c0d5a4e3f53`; exact-head Backend CI [#40287765745 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40287765745).
- Documentation synchronization commit: `f90573d653c7103bf9cfdb1f867da97b176d3240`; its exact-head Backend CI [#40289107666 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40289107666). Backend tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore/evidence retention passed. Synthetic restore is not proof of actual Oracle Cloud recovery.
- The approved public Upstox STT/exchange rules are estimate-only. Account-specific actual charges, GST taxable-base composition, stamp duty, SEBI/DP/demat/other charges, unsupported exchange/segment mappings, and per-fill actual evidence remain unapproved. Candidate tariff entries remain DRAFT unless separately allowlisted and reviewed.
- Phase 3 remains in progress. Next gates: independently reviewed tariff applicability; component-specific per-fill allocation rules; invoice/source-backed GST/IPFT and product/segment evidence; final adversarial, migration and recovery review; exact-head acceptance sign-off. Do not repeat canonical live-fill integration.
- Safety: PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. PR #6 stays open/draft/unmerged without explicit user approval. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.
- This documentation commit’s CI is green. Continue only from this checkpoint and verify CI for every subsequent implementation/checkpoint commit. Historical entries below or above this section do not supersede this checkpoint.


## Canonical latest Phase 3 checkpoint — 26 October 2026

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **Verified code/evidence head:** `d287da70ce184c904c6f9ede9e4a0edca5839f8f` (commit: “docs: reconcile public Upstox contract note GST examples”).
- **Exact-head CI:** PASS — [GitHub Actions run #40304398632](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40304398632), commit `d287da70ce184c904c6f9ede9e4a0edca5839f8f`; **1,004 passed, 1 warning**. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and restore-evidence retention also passed. This is CI evidence, not proof of a real Oracle recovery or broker-origin authenticity.
- **GST/IPFT research:** Three public third-party historical Upstox note copies were reconciled: 11-Feb-2025 base ₹2.97 / IGST ₹0.53; 21-May-2024 base ₹77.56 / IGST ₹13.96 (IPFT ₹0.11 listed outside that note's printed base); 12-Mar-2025 base ₹2.75 / IGST ₹0.50. Printed-base compositions differ historically. The current official Upstox schedule supports the **estimate-only** base of brokerage + transaction charges + demat where applicable + IPFT, with IPFT represented exactly once because it is combined with transaction charges. Do not add SEBI to this current estimate base without current applicable billing evidence; never calculate GST on trade notional or infer zero from missing/null fields.
- **Tax/accounting approval:** all four GST component candidates remain `DRAFT`. Historical public copies do not prove current actual per-fill billing across products/accounts. Actual-charge promotion stays gated; estimate logic and actual invoice reconciliation are distinct. Follow effective dates and preserve raw API/source evidence.
- **Next action when resuming:** continue Phase 3 from this exact commit and checkpoint. Next gate is component-specific GST acceptance cases for equity delivery, intraday, futures and options, then implementation review and exact-head CI; do not restart from earlier saved checkpoints.
- **Safety / PR:** PAPER mode mandatory; live broker `place_order`/`modify_order`/`cancel_order` and automatic live-fill promotion remain disabled. PR #6 remains open, draft and unmerged. Original `tarunsharma2610-del/Tradepro` is not the work target and must remain untouched.
- This checkpoint supersedes older statements in this document about CI being in progress or requiring verification for the pre-`d287da7` head. Historical notes remain history; this is the canonical resume point.
