## Authoritative Phase 3 checkpoint — 26 October 2026 (latest verified CI)

- Target repository only: `tarunsharma2610-del/tradepro-improved`; branch `phase3/durable-per-fill-charge-allocation`; implementation/test head `44830ec48b50b4f470ec9ca95dd2d3f4339dd3df`. Do not modify original `Tradepro`.
- Exact-head Backend CI: [run #40294178677 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40294178677), including the test separating NSE/IPFT arithmetic reconciliation from GST taxable-base approval.
- GST estimate helper accepts exactly 18%; tests reject 0%, 5%, 100%, and 100.01%. Rate guard does not approve taxable-base composition; component inclusion needs reviewer and invoice/source evidence.
- ₹307/crore versus ₹306.99/crore transaction charge + ₹0.01/crore IPFT is arithmetic reconciliation only, not GST-base approval.
- Canonical live-fill integration is verified: six independently verified charge snapshots, evidence revalidated under lock, no raw-only fallback; brokerage cap applied once before deterministic paise-exact allocation.
- Remaining Phase 3 gates: effective-dated tariff applicability; component-specific per-fill allocation acceptance; invoice/source-backed GST/IPFT and product/segment evidence; adversarial/migration/recovery review; final exact-head docs/sign-off.
- Upstox public schedules/calculator are estimates; aggregate charges endpoint is not actual per-fill evidence. Null remains unknown, not zero. Synthetic restore is not actual Oracle recovery.
- PAPER mandatory; live broker writes, automatic live-fill promotion and automatic scheduling disabled. PR #6 open/draft/unmerged unless explicitly approved. Defer AI/open-source adaptations until Phase 3 acceptance. Documentation commit needs its own CI.

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

# Phase 3 — Charge Component Acceptance Matrix

**Status: working acceptance specification; not tariff approval.**  
**Scope:** Tradepro Improved, Indian broker charge evidence and per-fill reconciliation.  
**Safety:** All tariff candidates remain DRAFT/non-selectable. The matrix does not authorize automatic allocation or live broker order execution.

## Shared controls for every component

1. Preserve the original source document and its SHA-256/size; this proves byte continuity with the stored upload, not broker-origin authenticity.
2. Require independent reviewer approval of the transcribed component, exact eligible-fill manifest, and allocation basis. Extractor and reviewer must differ.
3. Require canonical, unique fill IDs and a matching digest; lock/revalidate evidence, component, trades and allocations in the same transaction used for promotion.
4. Use decimal arithmetic and INR paise precision. The per-fill amounts must sum exactly to the reviewed component total. Any residual paise assignment must be deterministic, documented, reproducible, and reviewed; never silently discard a residual.
5. Idempotent replay must return the same result; conflicting replay, mixed statuses, source mismatch, missing fills, stale references, or authorization loss must fail closed with no partial promotion.
6. Estimate-vs-actual variance is a separate audit record only; it must not mutate reviewed source evidence or allocations.
7. API responses preserve absent, null, numeric zero, and nonzero values as distinct states. Aggregate trade-charge reports are not per-fill actual-charge evidence.
8. Until an approved component-specific rule establishes the economic allocation basis, only explicit independently reviewed per-fill weights may be promoted. Generic quantity/notional allocation remains disabled.

## Representation-contract and component-set version gate

- Every transaction/IPFT source row must retain the exact supported representation-contract version used at review; null/legacy versions are not inferred.
- The set consumed by live accounting must be explicitly versioned and exact. Evidence-only source labels such as clearing, separate IPFT, other, or demat transaction charges remain preserved but cannot be silently dropped or added to the six-component accounting set.
- Acceptance requires positive and adversarial tests for missing/extra/duplicate components, mixed combined/split rows, inconsistent sibling versions, legacy null versions, and migration round-trips.

**Current canonical-set implementation:** exact six-component contract v1 is CI-verified at `f61cedd25f5982846774db3028fb646d2e108e07`. The pure combined/split source-canonicalization helper is CI-verified at `44c12acd133924711cd68c27f315d9298c6acfde`; wiring it into API review and durable allocations remains open. Additional source labels block promotion until mapped explicitly.

## Component matrix

| Component | Required source / effective scope | Calculation base and allocation | GST / overlap guard | Promotion gate |
|---|---|---|---|---|
| Brokerage | Dated broker tariff and applicable plan; instrument/segment, order side, order type and effective date; reconcile to individual contract-note line where available | Apply documented per-order / per-execution rule, including minimum/maximum caps where applicable. Aggregate brokerage across order legs only when the tariff says so. For actuals, exact reviewed component total and explicit reviewed per-fill weights until rule approval. | Include in GST base only according to approved invoice/tax treatment. Apply caps once at the tariff-defined level; do not reapply at fill level if the cap is order-level. | Dated rule + test vectors for below/at/above caps, multiple fills, partial fills, replay and paise residuals; independent accounting approval. |
| STT | Current statutory schedule effective on trade date; instrument, delivery/intraday/F&O classification, buy/sell side and relevant turnover/premium/settlement event | Base must be statutory turnover/premium/settlement base for the exact product and event; do not assume a universal notional base. Preserve rounding/aggregation level prescribed by applicable rule. | Do not include statutory STT in GST taxable value by default. Confirm pure-agent / invoice treatment from authoritative tax guidance and actual invoice; no universal assumption. | Product/event matrix, boundary and rounding tests, dated authority, and reviewed contract-note reconciliation. |
| Exchange transaction charges (including combined IPFT where applicable) | Exchange circular effective on trade date, exchange, segment, product/index and relevant scrip/expiry scope | Apply rate to the source-defined turnover or option premium. NSE 2026-03-01 combined rates already include IPFT for the documented NSE equity scopes; do not layer another IPFT charge on top. BSE and MCX require separate product/scrip schedules. | Where official broker schedule identifies combined transaction/IPFT, preserve representation metadata and avoid double counting. GST base depends on approved component representation and invoice treatment. | Effective-dated exchange rule; test combined vs split representations, null/missing/zero API values, no duplicate IPFT, no cross-exchange leakage; independent approval. |
| SEBI charges | Dated SEBI schedule and applicable turnover definition; trade date and segment/product | Use the applicable regulated base and source-defined aggregation/rounding. Do not assume exchange transaction-charge base is identical. | GST treatment must be supported by tax invoice/rule; no blanket inclusion/exclusion from this matrix alone. | Rate/base source, boundary/rounding fixtures, and invoice reconciliation. |
| Stamp duty | Current statutory schedule effective on trade date; state/territorial rule, instrument, buy/sell side and applicable transaction base | Use the legally defined side/base and aggregation level. Do not apply a generic rate across cash, futures, options and commodities. | Do not automatically include statutory stamp duty in GST base; establish actual tax treatment and applicable conditions from authoritative guidance. | Jurisdiction/product/date test matrix and reviewed evidence; unresolved base or applicability blocks promotion. |
| GST / IGST / CGST / SGST | Applicable tax invoice, place-of-supply and registration context, supply type, effective tax rule and charge-component mapping | Compute from the approved taxable value and tax rate; explicitly define whether rounding occurs per line, invoice or other prescribed level. Separate tax components must reconcile to invoice totals. | Avoid tax-on-tax and duplicate inclusion of combined transaction/IPFT charges. CBIC guidance about statutory recoveries depends on conditions and is not a blanket mapping. Do not assume all components share one base. | Approved component-level taxable-value map, invoice-aligned test vectors, line/invoice rounding tests, and independent tax/accounting review. |

## Source-specific open gates

- **NSE/IPFT:** Official effective-dated combined-rate arithmetic is recorded in docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md. Still open: authenticated Upstox field semantics and invoice/contract-note corroboration. Preserve API schema/version and raw response; no field name alone proves whether a value is combined.
- **BSE cash equity:** Must use effective-dated scrip group/exclusivity metadata where the exchange schedule depends on it. Do not enable a generic BSE cash rate.
- **BSE derivatives:** Identify product/index, expiry, applicable slab and cumulative monthly turnover state where required. Historical notice alone is not sufficient for a current production rule.
- **MCX / commodities:** Require current product-specific exchange rates, CTT and stamp-duty bases, effective dates and tax mapping. Do not inherit NSE equity rules.
- **Upstox API:** Brokerage Details API is an order-specific estimate; Get Trade Charges API is an aggregate segment/date/FY view. Neither aggregate response is a substitute for reviewed per-fill actual evidence. Missing/null/zero/numeric fields remain distinct.
- **Historical annual statement:** The FY 2022–23 summary screenshot is historical aggregate evidence only; it does not prove IPFT inclusion or per-fill charge mapping.

## Required acceptance tests before any component is promoted automatically

- Exact per-fill manifest and digest; missing/extra/duplicate/cross-connection fill rejection.
- Source hash/size tampering, changed review state, reviewer permission loss and transaction rollback.
- Component total, currency, allocation basis, weights and method-version mismatch.
- Decimal boundary cases at ₹0.00/₹0.01, fractional residual distribution, all-zero and invalid weights, deterministic output independent of input ordering.
- Duplicate request and idempotent replay; conflicting replay and concurrent promotion.
- Order-level brokerage caps with multiple/partial fills and proof cap is applied at the correct level.
- STT, exchange, SEBI, stamp duty and GST bases each have dated product-specific fixtures and documented rounding level.
- NSE combined-vs-split IPFT normalization, absent/null/zero distinction, double-count prevention and cross-segment isolation.
- Variance persistence/failure leaves reviewed evidence and allocation rows unchanged.
- CI passes on the exact final code/documentation head; independent review records accepted/rejected items and rationale.

## Exit criteria

Phase 3 cannot be marked complete solely because tests pass. Completion requires: (a) all applicable rows have approved source and calculation policy or remain explicitly unsupported and blocked; (b) all required acceptance tests pass on the exact head; (c) independent accounting/tax review and repository review are recorded; (d) documentation, handover and roadmap agree; and (e) the user approves any final PR merge. Until then, the ledger remains a fail-closed review workflow, tariffs stay DRAFT/non-selectable, and live broker writes stay disabled.


## 2026-10-24 — Resolver acceptance and CI checkpoint

- Backend workflow `40108183667` succeeded on prior head `8214430f562f6f425cfc1b9b6a6b3b547832b68a`. New resolver tests add exact broker/endpoint/schema/field/scope matching and non-finite-number rejection; newer commits still require CI.
- Mapping identity fixtures use immutable dataclass replacement. Intended-use semantics remain explicit; missing/null/invalid values remain unusable and retain provenance; numeric zero remains distinct.
- Accounting acceptance includes replay/conflict, ledger reconciliation, lock order, rollback, reviewer authority and PostgreSQL verification/promotion race coverage. Re-check exact test and workflow status before claiming complete. CI does not establish production tariff correctness or broker-origin authenticity.
- Safety gates unchanged: PR #6 draft/unmerged; live broker order submission and automatic quantity/notional allocation disabled; production Upstox mappings/tariffs unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Resolver field-identity guard added; CI pending

- Resolver now verifies that the payload field matches the terminal field in the approved mapping path. Implementation `77aa77aec37dc535c3e427ca3f88c2ccb5e75ed8`; regression test `5c5482c7f7fa623707698f64b6a061351e5e5b87`. CI is pending for these and subsequent documentation commits.
- The field-identity guard is a code correctness safeguard, not approval of production Upstox field semantics or tariffs. Existing live-fill tests cover lock order, replay idempotency and rollback; genuine concurrent verification-versus-promotion coverage still needs confirmation.
- PR #6 remains draft/unmerged. Live order submission and automatic quantity/notional allocation remain disabled. Work only in `tradepro-improved`; original `Tradepro` remains untouched.


## 2026-10-24 — Latest resolver CI and PostgreSQL concurrency suite verified

- Backend workflow [#40109041654](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40109041654) passed on head `ed346e823cbfae8448fae0134c4ff864bfcc60ac`: **872 passed, 1 warning**; broker-write boundary guard passed.
- Dedicated PostgreSQL concurrency tests cover competing fill sets, source verification vs allocation promotion, and live-fill promotion vs ledger verification. The successful test summary has no skipped tests, confirming the collected suite ran in CI's synthetic database environment.
- This is not approval of production Upstox tariff/field mappings. PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled; original `Tradepro` remains out of scope.


## 2026-10-24 — Official tariff/API source audit

- Upstox's `GET /v2/trade/profit-loss/charges` accepts segment, financial year and optional date bounds; documented output is aggregate `charges_breakdown`, not a per-fill schema. Example `charges.ipft` is null. Treat it as aggregate reconciliation evidence only, and never coerce null to zero. https://upstox.com/developer/api-documentation/get-trade-charges/
- NSE circular NSE/FA/73061 dated 27-Feb-2026 applies from 1-Mar-2026: combined member outflow ₹307/crore cash, ₹183/crore equity futures and ₹3,553/crore equity-options premium; included IPFT contribution is ₹0.01/crore each side. Use effective-dated rate versioning and guard against double counting. This circular does not establish Upstox-specific contract-note JSON field semantics. https://nsearchives.nseindia.com/content/circulars/FA73061.pdf
- Upstox's public charges page shows newer effective-date summary values alongside historical tables and lists a STT/CTT change effective 1-Apr-2026. Use the matching date/scope and prefer official exchange/statutory notices for rate authority. https://upstox.com/brokerage-charges/
- Acceptance: aggregate API response, null IPFT, stale tariff, combined-vs-split IPFT and effective-date boundary must fail closed when actual per-fill evidence is required. Production mappings and tariffs remain DRAFT/non-selectable.
- Latest prior implementation head `ee1b2a74d2a9f6141b9afbb6e06562b5cf263a9b` passed workflow #40110597753; rerun CI on the resulting documentation head.
- PR #6 remains draft/unmerged; live order submission and automatic quantity/notional allocation remain disabled; original `Tradepro` remains untouched.


## 2026-10-24 — Aggregate endpoint hard guard added; CI pending

- Upstox `/v2/trade/profit-loss/charges` is now explicitly blocked from `PER_FILL_ACTUAL` resolution regardless of a misleading mapping semantic. Its published schema is aggregate `charges_breakdown`, not per-fill evidence.
- Regression test `test_official_upstox_aggregate_charges_endpoint_cannot_be_promoted_to_per_fill` covers the guard. Implementation `cdc07afdd8cc0c8d0b37d7e4aa8cdf1bf6eac651`; test `8ae749017a8ba0016f2c9adeb77eaff41fb5ae70`. Latest test CI must pass before verification is complete.
- Keep production mappings/tariffs unapproved; null distinct from zero; automatic quantity/notional allocation and live order submission disabled. PR #6 draft/unmerged; original `Tradepro` out of scope.


## 2026-10-24 — Upstox brokerage calculator restricted to estimates; CI pending

- Official Upstox `GET /v2/charges/brokerage` takes proposed instrument, quantity, product, transaction type and price, returning a charge calculation; this is not proof of final booked per-fill charges. https://upstox.com/developer/api-documentation/get-brokerage/
- Resolver now blocks `/v2/charges/brokerage` from `PER_FILL_ACTUAL` and actual `AGGREGATE_SUMMARY` use even if a mapping is misleadingly labelled. Existing guard still blocks `/v2/trade/profit-loss/charges` from per-fill actual use. New regression tests cover both misuse cases.
- Implementation `3486d854dae2451858a858cb627602aca7338969`; tests `6c92101a1890a0f4d761e86ed3db047a269fd10d`. Prior head `6cc8b58f635fcb4f1b1cb3e5997099d074800a28` passed workflow #40111501429. CI for the new commits must be verified.
- Production mappings/tariffs remain unapproved; null is not zero; automatic quantity/notional allocation and live broker order submission remain disabled. PR #6 stays draft/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Expanded Upstox source components — 25 October 2026

- Intake can preserve separate transaction, clearing, IPFT, other and demat transaction source labels after migration `202610250019`; this is source-evidence capture only.
- The live-fill promotion contract still requires exactly six reconciled components and must reject a ledger containing an additional IPFT/clearing/demat/other allocation. Do not relax this guard until a versioned component set and combined-vs-split normalization contract is approved.
- Existing regression coverage establishes the narrow arithmetic equivalence between a documented combined NSE charge and its equivalent split representation. Production API and contract-note semantics, as well as GST base approval by product/date/invoice, remain open gates.


## Versioned exchange-charge representation contract — 25 October 2026

- Added `backend/app/services/broker_charge_representation_contract.py` with pinned contract version `exchange-charge-representation-v1`. The validator requires an explicit reviewed representation mode, preserves original source labels, validates normalized component names and paise-precision amounts, and rejects combined transaction charges plus a separate IPFT amount to prevent double counting.
- Added `backend/tests/test_broker_charge_representation_contract.py` covering combined versus split representations, equivalent ₹307.00 exchange-charge base, duplicate IPFT rejection, missing components, unknown/inferred modes, invalid amounts, raw-label retention, and unsupported component labels.
- This contract validates representation only. It deliberately returns `accounting_approved: false`; it does not authenticate a source document, approve a broker API mapping, decide GST taxable composition, allocate aggregate amounts to fills, or enable live accounting. Existing promotion remains fail-closed.
- Implementation/test commits: `3c9ac46ea58257ba4c9c87b1b664eee14c6bd35a` and `be505e3dbc0e93eaa25a012d6a9afba81712e9ab`. Exact-head CI for the final documentation head must be checked before this checkpoint is called verified.
- PR #6 remains draft/open/unmerged; PAPER mode remains mandatory; live broker order writes and automatic generic quantity/notional allocation remain disabled. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Persisted transaction/IPFT representation gate — 25 October 2026

- Added migration `202610250020` and nullable `source_label` / `representation_mode` fields on `broker_charge_source_components`. Existing rows retain their normalized component name as a source-label fallback, but representation mode is deliberately left undeclared rather than inferred.
- Source-component intake now preserves the original label and optional explicit mode. Review of `transaction_charges` / `ipft` rows invokes the versioned representation validator and remains blocked when mode is missing, when combined mode also has a separate IPFT row, when split mode lacks either row, or when sibling rows disagree on mode. Rejected review attempts leave rows pending.
- Added API regression tests for persisted label/mode, combined-plus-separate-IPFT rejection, and missing-mode rejection. Exact-head CI is required before calling this checkpoint verified.
- GST composition, endpoint/schema semantics, authenticated real contract-note evidence, and per-fill allocation approval remain separate gates. No live broker writes or generic quantity/notional allocation were enabled.


## Representation-gate CI correction — 25 October 2026

- The first API regression run exposed two assertion-message mismatches: the validator correctly rejected ambiguous combined-plus-IPFT input and undeclared representation mode, but the tests expected different wording. Updated the tests to assert the validator's actual fail-closed error messages; no safety rule was weakened.
- Follow-up exact-head CI for commit `df344e9c64aeb6ec3f2f01fef01f3c05739d4800` and subsequent documentation synchronization is pending. Do not call the current head green until the full workflow completes.


## Source-label completeness gate — 25 October 2026

- The source representation contract now requires one retained original source label for every normalized charge component. Incomplete label intake is rejected before review; this does not approve any API field mapping or production accounting rule.
- Regression coverage includes a split transaction/IPFT payload missing a source label. Exact-head CI for the synchronized documentation head remains a required verification gate.
- Tariff candidates remain DRAFT; GST component composition and Upstox API/contract-note field semantics remain open. No generic quantity/notional allocation or live broker order writes were enabled.
- Safety: work only in `tarunsharma2610-del/tradepro-improved`; PR #6 draft/unmerged; PAPER mode mandatory; original `Tradepro` untouched.


## Authoritative IPFT/GST decision — 25 October 2026

This is the carried-forward project decision. Do not restart the IPFT/GST policy discussion or describe the agreed arithmetic as undecided. Keep policy separate from source-evidence and production-approval gates.

### IPFT and NSE exchange-charge representation

Effective 1 March 2026, NSE circular NSE/FA/73061 records combined exchange-charge rates including IPFT: cash equity ₹307.00/crore, equity futures ₹183.00/crore, equity options ₹3,553.00/crore. Equivalent split arithmetic, with IPFT exactly once: cash ₹306.99 + ₹0.01; futures ₹182.99 + ₹0.01; options ₹3,552.99 + ₹0.01.

Combined source: use the combined amount and do not add IPFT. Split source: use transaction charges excluding IPFT plus separately evidenced IPFT once. Never infer representation from a field name. Preserve raw values, original labels, endpoint/schema/version. Missing, conflicting or ambiguous representation fails closed; null is not zero. Representation validation is not source authentication or production mapping approval.

NSE source: circular NSE/FA/73061, 27 February 2026, effective 1 March 2026: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf

### GST calculation policy

Apply 18% GST to the applicable evidence-backed taxable service-charge base using canonical components once. Working Upstox component policy: delivery = brokerage + transaction charges/IPFT + applicable demat transaction charges; intraday/futures/options = brokerage + transaction charges/IPFT. If transaction charges already include IPFT, count that combined amount once; if split, combine transaction charges excluding IPFT and separately evidenced IPFT once. Apply pure-agent/exclusion treatment only when supported by applicable tax rules and invoice evidence. Use product/segment/effective-date-specific rules, documented rounding and invoice reconciliation.

Reference: https://upstox.com/brokerage-charges/

### Status boundary

Settled: combined/split arithmetic, no IPFT double-counting, GST on applicable canonical taxable components once, ambiguous formats fail closed. Remaining production gates: authentic Upstox API/contract-note field semantics, effective-dated mapping and GST composition corroborated against invoices, per-fill equivalence/no-double-count tests, and exact-head CI. Upstox Get Trade Charges is aggregate reconciliation evidence, not per-fill actual evidence. These gates do not reverse the agreed policy.

Safety unchanged: PAPER mode mandatory; live broker order writes disabled; PR #6 draft/unmerged pending review and user approval. Work only in `tarunsharma2610-del/tradepro-improved`, never original `tarunsharma2610-del/Tradepro`.

## Added acceptance check — source label to component mapping (2026-10-25)

- [x] Implementation: representation contract requires explicit `labels_by_component` mapping with exact key coverage, non-empty/unique labels and consistent retained label order.
- [x] Integration wiring: source-component review passes the mapping from persisted rows.
- [x] Regression tests added for missing mapping, wrong component set and inconsistent label association.
- [ ] Exact-head CI passes for implementation HEAD `fb147a3c5580091574bc71c35e7a641cf7386935`.
- [ ] Authentic contract-note transcription is independently confirmed; code-level association alone does not authenticate source content.

- CI history: workflow [#40188703796](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40188703796) failed on the first implementation SHA due to a malformed test helper that raised before reaching validation. Corrected in commit `e2758ae3db5309641196f0cd0ce035591f6c03ac`; exact-head CI is still required.

## Added acceptance check — missing original source label

- [x] Intake no longer substitutes a normalized component name for a missing original source label.
- [x] Review rejects a component with a missing/blank original label and leaves it pending.
- [x] API regression test covers missing-label preservation and fail-closed review.
- [ ] Exact-head CI passes for implementation and documentation HEAD.
- [ ] Independent reviewer confirms the transcribed label and amount against integrity-checked original contract-note evidence.

- CI correction history: run [#40189211122](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40189211122) failed because missing-label validation ran before existing authorization/fill validation. Moved the new checks later in the review sequence in `b92d0185f588e24d54510b36659944e77f498a6e`; exact-head CI remains required.

- [x] Implementation source-label guard passes exact-head CI on `b92d0185f588e24d54510b36659944e77f498a6e` (run [#40189481491](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40189481491), 911 passed, 1 warning).
- [x] Documentation checkpoint `704d9d5caa8a893195d5213ae38b97c30639de96` passes [CI #40189515861](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40189515861).
- [ ] Exact-head CI passes for this subsequent progress-report synchronization commit.
- [ ] Independent reviewer confirms the transcribed label and amount against integrity-checked original contract-note evidence.



## Phase 3 forward checkpoint — persisted representation-contract version (2026-10-25)

- Audited the actual branch and confirmed the previous source-label authenticity guard is already implemented and CI-verified at `b92d0185f588e24d54510b36659944e77f498a6e`; this task does not repeat that work.
- Added nullable `representation_contract_version` to `BrokerChargeSourceComponent` and migration `202610250021`. Null is retained for legacy/undeclared rows; the migration does not infer a version for historical records.
- The source-component intake API now accepts, stores, and returns the version. Review of transaction/IPFT components requires the supported persisted version and requires sibling transaction/IPFT rows to agree on both mode and version before the existing combined/split validator runs.
- Added API regression assertions for persistence and response round-trip. Implementation commit: `1d327b145fe25d871a763985b5f746e12e107b75`. Exact-head backend workflow [#40190287853](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40190287853) was **in progress when this checkpoint was written**; do not mark the implementation CI-verified until its conclusion is successful. The documentation commit will require its own exact-head CI as well.
- This is an auditability step, not tariff approval, source authenticity proof, GST approval, or authorization to promote more components. Live accounting still requires its existing six-component set; extra components remain fail-closed. Paper mode and live-order safeguards are unchanged; PR #6 stays draft/unmerged; original `Tradepro` remains out of scope.
- Next single implementation gate: define and persist an explicit versioned component-set contract that distinguishes supported canonical accounting components from retained evidence-only components, then add tests proving missing, extra, duplicate, mixed-representation, and legacy-version rows cannot be silently omitted or promoted.


### CI correction history — persisted representation-contract version (2026-10-25)

- Workflow [#40190287853](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40190287853) failed on `1d327b145fe25d871a763985b5f746e12e107b75` due to one existing API regression assertion expecting the previous validation error wording. The underlying fail-closed mode check was still rejecting the request; the test stopped on the message mismatch.
- Corrected the response wording without relaxing validation in commit `db1ee170629fcb853b5c6e46f0d9d8654056bc44`. The failure remains recorded as history and is not counted as a successful verification.
- Workflow [#40190403007](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40190403007) was triggered for documentation HEAD `0abfa9a1ed5dcd553f1b92010ec86b41ccf77a2b`; that SHA predates the wording correction and must not be treated as verification of `db1ee170629fcb853b5c6e46f0d9d8654056bc44`. Exact-head CI for the corrected implementation and current documentation head remains pending.
- Next action: confirm the corrected exact-head workflow succeeds, then add explicit missing-version API regression coverage and continue the versioned component-set contract. No tariff candidates are promoted; live accounting still requires the existing six canonical components.


## Phase 3 forward checkpoint — versioned canonical component set (2026-10-25)

- Added `broker_charge_component_set_contract.py` with explicit `live-fill-accounting-component-set-v1` and the exact six canonical accounting components: brokerage, STT, exchange charges, SEBI charges, stamp duty, and GST.
- Added nullable `component_set_version` to source-component records via migration `202610250022`. No version is backfilled for legacy records. Canonical components receive the current set version only during independent review; evidence-only components remain unversioned and cannot be silently counted as canonical.
- Live-fill promotion now checks the full non-rejected source-component set before accounting: missing/extra/duplicate components, null/unsupported versions, and unreviewed rows fail closed. Additional evidence labels are preserved but block promotion until an explicit reviewed mapping exists. The prior six-allocation check remains in place.
- Added contract tests for exact set, missing/extra/duplicate components, legacy version and unreviewed rows. Updated the real PostgreSQL race fixture to declare the set version explicitly.
- Implementation/test checkpoint: `f61cedd25f5982846774db3028fb646d2e108e07`. Exact-head CI [#40191140007](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40191140007) passed: **917 passed, 1 warning, 0 failures**. Broker-write boundary guard, SQLite/PostgreSQL migration round-trips through migration `202610250022`, and synthetic restore drill passed. Synthetic restore does not prove actual Oracle Cloud recovery.
- Prior failed CI remains documented: run [#40190926423](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40190926423) exposed a missing set-version value in the PostgreSQL concurrency fixture; the fixture was corrected in the verified commit above. It is not counted as a successful run.
- This does not yet map raw `transaction_charges` + `ipft` source rows to canonical `exchange_charges`, approve tariffs/GST, or enable promotion of evidence-only rows. Live broker writes remain disabled; PR #6 remains draft/unmerged; original `Tradepro` remains untouched.
- Next single implementation gate: define and test an explicit, versioned source-to-canonical mapping for combined versus split transaction/IPFT evidence, preserving both raw source rows while producing one canonical exchange-charge amount only when the representation is explicitly reviewed. Other unsupported source components must continue to block promotion.


## Phase 3 forward checkpoint — combined/split source canonicalization contract (2026-10-25)

- Added `broker_charge_source_canonicalization.py` and focused tests. The pure contract maps explicit COMBINED transaction/IPFT source representation to one canonical `exchange_charges` amount, or sums SPLIT transaction charges plus separately evidenced IPFT exactly once. It retains source-row associations in its result and rejects ambiguous/mixed versions, double mapping, duplicate/missing labels, invalid amounts, and unsupported clearing/demat/other components.
- Exact-head CI [#40191589060](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40191589060) passed on implementation/test commit `44c12acd133924711cd68c27f315d9298c6acfde`: **930 passed, 1 warning, 0 failures**. Broker-write boundary guard and synthetic restore drill passed. Synthetic restore is not actual Oracle recovery.
- Important boundary: this is a tested pure canonicalization contract, **not yet wired into the API review flow or durable allocation ledger**. It does not authenticate source notes, approve tariffs/GST, allocate canonical totals to fills, or enable live accounting. Do not count the end-to-end mapping gate as complete.
- Current branch/PR safety remains unchanged: work only in `tarunsharma2610-del/tradepro-improved`; PR #6 stays draft/unmerged; PAPER mode mandatory; live broker writes disabled; original `Tradepro` untouched.
- Next single implementation gate: wire this canonicalization contract into reviewed source-component validation and per-fill allocation persistence so raw source rows remain immutable, canonical exchange charges reconcile exactly, and promotion cannot omit or double-count source components.


## Authoritative checkpoint — 26 October 2026 (documentation CI verified)

- Repository: `tarunsharma2610-del/tradepro-improved`; branch: `phase3/durable-per-fill-charge-allocation`.
- Latest implementation commit: `ac7d27f2c9922925483b5b906c484c0d5a4e3f53`; exact-head Backend CI [#40287765745 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40287765745).
- Documentation synchronization commit: `f90573d653c7103bf9cfdb1f867da97b176d3240`; its exact-head Backend CI [#40289107666 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40289107666). Backend tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore/evidence retention passed. Synthetic restore is not proof of actual Oracle Cloud recovery.
- Approved public Upstox STT/exchange rules are estimate-only. Account-specific actual charges, GST taxable-base composition, stamp duty, SEBI/DP/demat/other charges, unsupported exchange/segment mappings, and per-fill actual evidence remain unapproved. Candidate tariff entries remain DRAFT unless separately allowlisted and reviewed.
- Phase 3 remains in progress. Next gates: independently reviewed tariff applicability; component-specific per-fill allocation rules; invoice/source-backed GST/IPFT and product/segment evidence; final adversarial, migration and recovery review; exact-head acceptance sign-off. Do not repeat canonical live-fill integration.
- Safety: PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. PR #6 stays open/draft/unmerged without explicit user approval. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.
- This documentation commit’s CI is green. Continue only from this checkpoint and verify CI for every subsequent implementation/checkpoint commit. Historical entries do not supersede this checkpoint.


## GST/IPFT arithmetic regression checkpoint — 26 October 2026

- Added `test_gst_arithmetic_is_invariant_for_combined_vs_split_ipft_representation`: synthetic combined ₹307.00 exchange component and split ₹306.99 transaction + ₹0.01 IPFT representations produce equal GST of ₹55.26 at 18%. Exact test commit `8b4ae0b431d6aa03f1a8ae347a0b5fa7bda44c4f` passed Backend CI [#40296066304](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40296066304).
- This validates arithmetic equivalence only; it does not approve either representation for actual GST taxable-base inclusion. Product/segment mapping still requires reviewed source evidence and invoice/contract-note reconciliation. Upstox's public schedule lists 18% on specified brokerage, transaction, IPFT and (equity delivery) demat charges; NSE circular `NSE/FA/73061` sets combined charge outflows effective 1 March 2026. CBIC pure-agent requirements govern when statutory recoveries such as STT/stamp duty can be excluded from GST value. See https://upstox.com/brokerage-charges/, https://nsearchives.nseindia.com/content/circulars/FA73061.pdf, https://cbic-gst.gov.in/sectoral-faq.html, https://cbic-gst.gov.in/valuation-rules.html.
- No tariff rules are promoted. Do not apply GST to trade notional or indiscriminately to all costs; do not add IPFT again when already included in a combined exchange-charge representation. Continue next with component-level GST acceptance cases by product/segment, then exact-head CI. PAPER mandatory; live broker order writes disabled; PR #6 draft/unmerged; original `Tradepro` untouched.


## GST/API evidence checkpoint — 26 October 2026

- Implementation/test head `149d21fdbb82306ff1b800ff7d3ad33b99058d81`; exact-head Backend CI [#40296745348 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40296745348). Passing CI does not constitute legal approval of GST treatment.
- Source-backed Upstox GST component candidates now cover NSE/BSE equity delivery, equity intraday, equity futures and equity options. All remain `DRAFT`. Delivery includes `demat_charges`; the other categories do not. `exchange_charges` is the canonical combined transaction/IPFT component, so IPFT must not be counted twice. Trade notional is never a GST component.
- Official Upstox `GET /v2/charges/brokerage` calculates a quote for supplied instrument, quantity, product, side and price; response fields include GST, STT, stamp duty, transaction, clearing, IPFT and SEBI turnover. It is an estimate, not proof of actual executed-fill charges: https://upstox.com/developer/api-documentation/get-brokerage/.
- Official Upstox `GET /v2/trade/profit-loss/charges` returns a segment/financial-year date-range breakdown; `ipft` can be null. Treat it as aggregate reconciliation evidence, not per-fill attribution: https://upstox.com/developer/api-documentation/get-trade-charges/. Actual-charge approval still needs contract-note/tax-invoice and account-record reconciliation.
- Upstox's public schedule specifies 18% GST on brokerage + transaction charges + IPFT, with demat additionally for equity delivery, and says IPFT is combined with transaction charges: https://upstox.com/brokerage-charges/. NSE circular `NSE/FA/73061` supports revised combined NSE transaction/IPFT rates effective 1 March 2026: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf.
- CBIC permits exclusion of statutory recoveries such as STT/stamp duty only when pure-agent conditions are met; otherwise apply Section 15 and applicable valuation rules: https://cbic-gst.gov.in/sectoral-faq.html and https://cbic-gst.gov.in/valuation-rules.html. Do not hard-code universal exclusion without evidence.
- No GST candidate is promoted. Missing/null API fields remain unknown, not zero. Any later API ingestion must preserve raw response/hash, retrieval time, query segment/date range, schema version and invoice linkage. Do not use the brokerage calculator as actual-charge evidence or infer per-fill values from aggregate responses.
- Next gate: source-backed GST acceptance/reconciliation using actual invoice/contract-note evidence and per-product component sets, then exact-head CI and documentation verification. PAPER mandatory; live broker order writes disabled; PR #6 remains draft/unmerged; original `Tradepro` untouched.


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

## Cross-repository GST/IPFT audit — 26 October 2026

- OpenAlgo's composable charge schedule is a useful architecture reference, but its inspected India delivery preset taxes brokerage + exchange transaction charges + SEBI and does not explicitly model IPFT/demat; this conflicts with the current Upstox public GST wording. Do not copy its formula.
- A Shoonya backtest example taxes brokerage + SEBI + transaction charges and adds IPFT separately; it is hard-coded sample logic, not tax authority.
- NautilusTrader's pluggable per-fill fee models are relevant for simulation mechanics only, not Indian GST interpretation.
- Upstox official tariff wording names brokerage + transaction + IPFT (and delivery demat). Its documented brokerage API example's GST ₹1.02 matches 18% of transaction ₹5.68 alone, while IPFT is ₹0.17 separately; this is a docs-example arithmetic mismatch, not proof of live endpoint behavior. Aggregate trade-charges API is not per-fill evidence.
- Historical publicly surfaced Upstox notes dated 21-May-2024 and 12-Mar-2025 concern rights-entitlement/special-case transactions. They are conflict signals, not representative current evidence for ordinary trades.
- Decision: all four GST component sets remain DRAFT. Next evidence gate is current ordinary-trade contract notes/tax invoices for delivery, intraday, futures and options, plus clarification of the public-tariff/API-example mismatch. Do not promote actual per-fill GST based only on a third-party formula or estimate API.

## Canonical checkpoint update — 26 October 2026, after cross-repository GST/IPFT audit

- Validated parent commit: `0e15bba3bfa425296f4104c96be6d10e3b42bf40`; Backend tests PASS on exact SHA, run [#40329710846](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40329710846). This documentation-only sync needs its own exact-head CI pass before it is the next validated checkpoint.
- Cross-repository finding: OpenAlgo's configurable charge schedule is useful architecture, but not an Upstox tax authority; the inspected Shoonya formula is hard-coded and unverified; NautilusTrader is relevant only for fee-model mechanics. No inspected repository proves the correct current Upstox GST taxable base.
- Upstox's documented brokerage API example has a GST arithmetic discrepancy versus current public tariff wording; this is not proof of live API miscalculation. Aggregate trades charges and estimate API responses cannot alone establish actual per-fill GST.
- Keep all four product candidates `DRAFT` until current ordinary-trade Upstox contract notes/tax invoices or written broker clarification resolves taxable components for delivery, intraday, futures and options.
- Invariants: combined transaction/IPFT counted once; no legacy IPFT double-counting; never tax trade notional; missing/null remains unknown; no promotion from estimates/aggregates to actual per-fill tax.
- Safety: PAPER mode mandatory; live broker writes and automatic live-fill promotion/scheduling disabled; PR #6 remains draft/unmerged unless user explicitly approves.

## Follow-up source reconciliation — 26 October 2026

### Current public tariff wording is explicit; the API example remains inconsistent

- Upstox's current public brokerage-charge page explicitly states GST is 18% on brokerage + transaction + IPFT for intraday, futures and options, and brokerage + transaction + demat + IPFT for equity delivery. It also says that from 1 March 2026 IPFT is combined with transaction charges. Source: https://upstox.com/brokerage-charges/ (reviewed 26 October 2026; see GST and transaction/IPFT sections).
- For a schedule effective 1 March 2026 onward, the intended public-schedule estimate should therefore represent the exchange charge once as the combined transaction/IPFT amount. Do not add a separate legacy IPFT component on top of that combined value. For delivery, the public schedule also lists demat/DP charges in the GST base; do not infer DP is absent just because an estimate API example does not include it.
- The Upstox Brokerage Details API documentation example remains internally inconsistent with that wording: GST ₹1.02 equals 18% of transaction ₹5.68 alone (rounded), while IPFT ₹0.17 is separately displayed and the example's DP plan minimum is described as extra/not included in brokerage calculation. Source: https://upstox.com/developer/api-documentation/get-brokerage/ . This is a documentation example discrepancy; it does not prove live API behaviour or actual contract-note treatment.
- A third-party Upstox calculator surfaced in research (https://dematopen.com/tools/brokerage-calculator/) calculates GST on brokerage + transaction charges and lists DP charge with its own GST. That differs from Upstox's public delivery GST wording and is not authoritative; do not use it to override Upstox or invoice evidence.
- Result: we can align the **public schedule estimate model** to the explicit tariff wording, with versioned effective dates and a single combined transaction/IPFT input. The actual per-fill GST rule still cannot be promoted until ordinary-trade contract-note/tax-invoice evidence or written Upstox clarification reconciles the API example and confirms delivery DP treatment. Keep all four actual component candidates `DRAFT`.

## Revised evidence checklist

- [ ] Written Upstox clarification or current ordinary-trade contract note/tax invoice showing taxable value and GST for delivery (including DP/demat), intraday, futures and options.
- [ ] Clarify whether Brokerage Details API's sample GST is stale and whether actual live responses use the current tariff's combined transaction/IPFT base.
- [ ] Verify BSE and NSE separately where rates/charge presentation differ; verify date-effective tariff selection around 1 March 2026.
- [ ] Keep estimate rules separate from actual per-fill accounting; reconcile actual invoice/ledger totals without inferring per-fill tax from aggregates.


## Latest exact-head CI checkpoint — 26 October 2026

- Latest source/documentation head verified: `0ff70ee399a1b8fd3d7d3998dcc1c93cd89da7a3` on `phase3/durable-per-fill-charge-allocation`; exact-head Backend pytest workflow [#40331381116](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40331381116) completed successfully.
- All observed job steps passed: dependency install, full test suite, broker write boundary, SQLite and PostgreSQL 16 Alembic upgrade/downgrade/re-upgrade, isolated synthetic PostgreSQL/document-volume restore drill, and evidence retention.
- This CI result verifies the existing code/tests at `0ff70ee399a1b8fd3d7d3998dcc1c93cd89da7a3`; it does not certify a new docs-only commit until CI runs against that exact new head. Keep this note historical after the follow-up docs commit; check that commit's CI before calling the documentation checkpoint green.
- GST/IPFT decision unchanged: public-schedule estimate may count combined transaction/IPFT once; no legacy IPFT double-counting; actual per-fill GST component candidates remain `DRAFT` pending source/invoice or written broker clarification. Never request personal contract notes from the user; continue using public sources and clearly label unresolved points.
- Safety and scope unchanged: target `tarunsharma2610-del/tradepro-improved` only; original `Tradepro` untouched; PAPER mandatory; live broker order writes and automatic live-fill promotion/scheduling disabled; PR #6 remains draft/unmerged; AI/Algory work deferred until Phase 3 acceptance.


## Public-schedule GST estimate implementation — 26 October 2026

The estimate-only path is implemented in backend/app/services/upstox_public_gst_estimate.py with regression tests in backend/tests/test_upstox_public_gst_estimate.py. It requires explicit source components, uses 18%, labels results PUBLIC_SCHEDULE_ESTIMATE_ONLY, and is scoped to reviewed NSE/BSE product combinations from 1-Mar-2026. Delivery includes explicit demat_charges; all supported products include brokerage + exchange_charges; NSE exchange_charges already includes transaction/IPFT once. A separate ipft input is rejected to prevent double counting. BSE options must use the applicable BSE schedule and must not inherit NSE IPFT assumptions.

This does not resolve actual billing: the Upstox Brokerage Details API example (transaction ₹5.68, IPFT ₹0.17, GST ₹1.02) conflicts with the tariff base wording because 18% of ₹5.85 rounds to about ₹1.05. Public estimate calculation follows published tariff wording only; actual per-fill GST candidates remain DRAFT. CI for code/test head 221493eb17729533cfaf855e2ce52532ef0903ac was pending at note time. Final exact-head CI is required before accepting this update.


## Authoritative GST decision — 26 October 2026

**Decision: implement the current official Upstox public-schedule GST base for estimates now; do not let the inconsistent API documentation sample block it.** Upstox's pricing page explicitly states GST at 18% on brokerage + transaction charges + IPFT, with demat charges additionally included for equity delivery. From 1-Mar-2026, NSE Circular NSE/FA/73061 defines combined transaction/IPFT outflows (cash ₹307/crore, futures ₹183/crore, options ₹3,553/crore premium); represent that as one exchange_charges component and never add IPFT twice. The supported estimate path sums brokerage + combined exchange_charges, and adds explicit demat_charges for delivery. STT, stamp duty and SEBI are not added to this published GST base.

The Brokerage Details API example showing transaction ₹5.68, IPFT ₹0.17 and GST ₹1.02 is internally inconsistent with that page: 18% × ₹5.68 = ₹1.0224 → ₹1.02; 18% × (₹5.68 + ₹0.17) = ₹1.053 → ₹1.05. Treat this as a documentation-example discrepancy, not evidence that current production billing is wrong. Public schedule takes precedence for estimates; the API example does not override it. Trades Charges API is aggregate and its ipft:null is unknown, not zero.

This resolves the public-schedule estimate rule. It does not certify account-specific invoice totals or per-fill actual GST. Keep actual accounting/promotion evidence-gated until invoice/source evidence or written broker clarification is available. A personal contract note from the user is not required. Official sources: https://upstox.com/brokerage-charges/ ; https://upstox.com/developer/api-documentation/get-brokerage/ ; https://upstox.com/developer/api-documentation/get-trade-charges/ ; https://nsearchives.nseindia.com/content/circulars/FA73061.pdf ; https://cbic-gst.gov.in/sectoral-faq.html
