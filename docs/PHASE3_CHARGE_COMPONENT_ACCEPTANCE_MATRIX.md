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
