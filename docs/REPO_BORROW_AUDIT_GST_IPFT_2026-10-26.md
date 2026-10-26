# Cross-repository GST/IPFT borrowing audit — 26 October 2026

**Status: research/design only; no GST component promoted.**  
**Target:** `tarunsharma2610-del/tradepro-improved` only.  
**Safety:** PAPER mode mandatory; live broker writes remain disabled; PR #6 remains draft/unmerged.

## Executive decision

No inspected third-party implementation proves the correct current Upstox GST taxable base for every Indian product/segment. Reuse generic architecture only; do not copy another repository's Indian tax formula into actual accounting.

The strongest evidence is a conflict between (a) Upstox's current public charge schedule, (b) its documented brokerage API example, and (c) historical public contract-note examples. The historical notes found in this search are rights-entitlement/special-case notes rather than sufficient representative evidence for ordinary current delivery/intraday/futures/options trades. They flag a conflict; they do not settle it.

## Findings by source

### 1. Upstox official sources — primary broker evidence, but not yet sufficient to approve per-fill GST

- Public charge schedule: https://upstox.com/brokerage-charges/
  - Current published wording says GST is 18% on brokerage + transaction charges + IPFT for intraday/futures/options, with delivery additionally including demat charges.
  - Since 1 March 2026, the page says IPFT is combined with transaction charges. Canonicalize this as one exchange-charge outflow; never add legacy IPFT rates on top of the combined tariff.
  - The public schedule is a published estimate/tariff statement, not a substitute for the actual account's invoice.
- Brokerage Details API: https://upstox.com/developer/api-documentation/get-brokerage/
  - The documentation example reports GST ₹1.02, transaction charges ₹5.68, IPFT ₹0.17 and SEBI turnover ₹0.17. ₹1.02 equals 18% of ₹5.68 rounded to paise; 18% of transaction + IPFT would be ₹1.05 before rounding. This is a **documentation-example arithmetic discrepancy**, not proof of the live API's actual behaviour. The example must not override current tariff wording.
  - API is estimate-oriented, not the actual contract-note tax invoice.
- Trades Charges API: https://upstox.com/developer/api-documentation/get-trade-charges/
  - Returns aggregate segment/FY charges including GST and an IPFT field that may be null. It can support aggregate reconciliation but cannot uniquely determine a per-fill taxable component breakdown. Null means unknown, not zero.
- Upstox SDK exposes these documented endpoints; an SDK wrapper adds no independent tax interpretation.

### 2. Historical Upstox contract-note examples — conflict signals, not approval evidence

- Public note dated 21 May 2024 (rights-entitlement context): https://www.scribd.com/document/735902961/CW-T-842243-20240521-NSE-35749411
  - Prints taxable value ₹77.56 = brokerage ₹0.01 + SEBI ₹0.11 + turnover charges ₹3.44 + demat ₹74.00; IGST ₹13.96; IPFT ₹0.11 shown separately outside the printed taxable-value equation.
  - This note includes a special rights-entitlement context and is historical; do not generalize its base to all regular products or today's tariff.
- Public note dated 12 March 2025 (rights-entitlement context): https://www.scribd.com/document/971660843/CW-T-3JCTYG-20250312-NSE-66319975-1
  - Prints GST taxable value as brokerage ₹2.75 and IGST ₹0.50; it does not provide representative ordinary-trade evidence for the current tariff.
- These examples show why a generic formula or public calculator alone is not enough. Obtain current ordinary-trade contract notes/tax invoices covering delivery, intraday, futures and options, including cases where IPFT and transaction charges are separately or jointly displayed.

### 3. OpenAlgo — borrow the composable schedule pattern, not its Indian GST formula

- Repository/source: https://github.com/marketcalls/openalgo/blob/main/portfolio/costs.py
- Useful design: a `Charge` record declares basis (turnover/buy/sell/order), rate/flat/cap and a `taxed` flag; `CostSchedule.breakdown` itemizes charges and calculates tax over marked components. This is a good pattern for explicit, auditable, market-specific rules.
- Its inspected India delivery preset marks brokerage, exchange transaction charges and SEBI charges as taxable, while STT and stamp duty are not marked taxable. It does not explicitly model IPFT as its own line in that preset and does not model delivery demat there.
- This preset therefore conflicts with the current Upstox published base (which names IPFT and delivery demat, but does not name SEBI). It is not an Upstox-specific authority and must not be copied as the answer.

### 4. Shoonya backtesting example — reject as tax authority

- Source: https://github.com/ctrlaltprofit/backtesting_with_real_bokerage_charges_shoonya/blob/main/backtesting_brokerage_and_slippage.py
- The function computes GST as 18% of brokerage + SEBI + transaction charges, then adds IPFT separately to total cost.
- It is a small hard-coded backtest example, not a documented Upstox tax invoice or authoritative GST ruling. Its GST formula has the same component-treatment uncertainty as our unresolved question; do not reuse its formula.

### 5. NautilusTrader — borrow fee-model separation only

- Docs: https://nautilustrader.io/docs/latest/concepts/behavioral_models/
- Its pluggable fee model and fill-level commission accounting are relevant architecture patterns for simulation. They do not encode Indian GST law or Upstox IPFT treatment.
- Keep deterministic GST/tariff and ledger logic within Tradepro Improved's existing reviewed accounting services. Do not import a trading engine to solve the tax interpretation.

### 6. CBIC / exchange sources

- CBIC sector FAQs: https://cbic-gst.gov.in/sectoral-faq.html
- GST valuation rules: https://cbic-gst.gov.in/valuation-rules.html
- NSE circular for the combined transaction/IPFT schedule: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf
- These help interpret the law and exchange fee schedule, but neither generic repository formulas nor a broad FAQ alone proves the broker's actual invoice component mapping.

## Recommended implementation direction

1. Keep the existing four Upstox product GST component candidates `DRAFT`.
2. Retain the current single canonical `exchange_charges` component for the combined transaction/IPFT tariff when reconciling the published schedule; do not create an additional IPFT charge from the same combined schedule.
3. Add an explicit, versioned taxable-component policy object only after the evidence gate is satisfied. Each component needs source provenance, product/segment/exchange scope, effective dates, taxability status and reviewer decision. Keep estimates separate from actual-charge ledger entries.
4. Reconcile the Upstox estimate endpoint and aggregate charges endpoint separately, marking their evidence scope clearly; neither should silently promote actual per-fill GST.
5. Obtain current ordinary-trade Upstox contract notes/tax invoices across the four products, preferably with broker-provided clarification of why the public tariff and API example arithmetic differ. Preserve redacted source files and hashes in the private project/repo evidence process; do not publish personal/account identifiers.
6. Only then write per-product expected-base tests and actual-invoice reconciliation tests. Include rounding, split/combined IPFT, missing/null, stale schedule, DP applicability and effective-date cases.
7. Do not modify the original `tarunsharma2610-del/Tradepro` repository. Do not start deferred AI integrations until Phase 3 acceptance.

## Acceptance gate

- [ ] Current ordinary-trade contract-note/tax-invoice evidence for delivery, intraday, futures and options.
- [ ] Broker explanation or authoritative evidence resolving the Upstox public schedule vs documented brokerage-API example mismatch.
- [ ] Taxable-base component decision recorded for each applicable product/segment and effective date.
- [ ] Independent review; candidates remain DRAFT until approved.
- [ ] Exact-head CI passes after any implementation.

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


## Estimate implementation follow-up — 26 October 2026

- Added backend/app/services/upstox_public_gst_estimate.py with tests in backend/tests/test_upstox_public_gst_estimate.py. It calculates an explicitly labelled PUBLIC_SCHEDULE_ESTIMATE_ONLY GST amount from a caller-supplied, source-backed component set at 18% for supported product/exchange scopes from 1-Mar-2026. It does not turn a calculator or aggregate API output into actual charge evidence.
- For NSE, exchange_charges is the combined transaction/IPFT amount from 1-Mar-2026 and must be counted once. The helper rejects a separate ipft key. Equity delivery requires explicit demat_charges; other supported products use brokerage + exchange_charges. BSE options use the applicable BSE source and do not inherit an NSE IPFT assumption.
- The Upstox Brokerage Details API example's GST ₹1.02 still conflicts with the public schedule base: transaction ₹5.68 + IPFT ₹0.17 gives a ₹5.85 base, whose 18% is about ₹1.05. The helper follows public schedule wording for estimates only; actual product GST candidates remain DRAFT until current public invoice evidence or written Upstox clarification resolves the discrepancy.
- No reviewed external repo currently removes the need for this broker/product/date-specific evidence gate; reusable repositories can inform architecture but cannot establish Upstox's current invoiced GST base. No personal contract note is required from the user.
- Code/test head 221493eb17729533cfaf855e2ce52532ef0903ac passed Backend CI [#40342805295](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40342805295). The documentation sync at 41fb8555c6cb26dc7bdbcd3fce69ab7c3cdce1e7 requires its own exact-head CI.


## Authoritative GST decision — 26 October 2026

**Decision: implement the current official Upstox public-schedule GST base for estimates now; do not let the inconsistent API documentation sample block it.** Upstox's pricing page explicitly states GST at 18% on brokerage + transaction charges + IPFT, with demat charges additionally included for equity delivery. From 1-Mar-2026, NSE Circular NSE/FA/73061 defines combined transaction/IPFT outflows (cash ₹307/crore, futures ₹183/crore, options ₹3,553/crore premium); represent that as one exchange_charges component and never add IPFT twice. The supported estimate path therefore sums brokerage + combined exchange_charges, and adds explicit demat_charges for delivery. STT, stamp duty and SEBI are not added to this published GST base.

The Brokerage Details API example showing transaction ₹5.68, IPFT ₹0.17 and GST ₹1.02 is internally inconsistent with that page: 18% × ₹5.68 = ₹1.0224 → ₹1.02; 18% × (₹5.68 + ₹0.17) = ₹1.053 → ₹1.05. Treat this as a documentation-example discrepancy, not evidence that current production billing is wrong. Public schedule takes precedence for the estimate path; the API example does not override it. Trades Charges API is aggregate and its ipft:null is unknown, not zero.

This resolves the public-schedule estimate rule. It does not certify account-specific invoice totals or per-fill actual GST. Keep actual accounting/promotion evidence-gated until invoice/source evidence or written broker clarification is available. A personal contract note from the user is not required. Official sources: https://upstox.com/brokerage-charges/ ; https://upstox.com/developer/api-documentation/get-brokerage/ ; https://upstox.com/developer/api-documentation/get-trade-charges/ ; https://nsearchives.nseindia.com/content/circulars/FA73061.pdf ; https://cbic-gst.gov.in/sectoral-faq.html


## Latest GST/IPFT implementation checkpoint — 26 October 2026

- Implementation + synchronized GST decision commit b75a97f6cd0043c185375cc253b84a1e6d6bfea1 passed exact-head Backend CI [#40345937942](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40345937942): 1,012 passed, 1 warning in 62.33s. Broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and evidence retention passed.
- Estimate decision: 18% on brokerage + combined transaction/IPFT exchange charges; explicit demat charges are additionally included for equity delivery. IPFT is counted once. STT, stamp duty and SEBI are excluded from the published estimate base. The inconsistent Brokerage Details API example is a documentation-example discrepancy, not proof of a live billing defect and not a reason to override the current public schedule.
- Actual invoice/per-fill GST acceptance remains separate and evidence-gated; actual component-set candidates stay DRAFT. Do not request a personal contract note. PAPER mandatory; live writes/promotion/scheduling disabled; PR #6 draft/unmerged; original Tradepro untouched.


## Phase 3 CI synchronization — 26 October 2026 (GST/IPFT resolver)

- Latest verified code head: `13e201661d26b04c9bf75bb7e3aaf567ad1e69c4`; exact-head Backend CI [#40378072884 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40378072884): **1,056 passed, 1 warning**. Broker-write boundary, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill and retained restore evidence passed.
- Added scope/effective-date-selected GST policy resolution for `COMBINED`, `SEPARATE`, and `NOT_APPLICABLE` IPFT representation. It rejects double representation, wrong-exchange reuse, missing/extra components, and unapproved or out-of-window policies. This is estimate-policy plumbing, not actual invoice reconciliation or tariff approval.
- Next Phase 3 gate: persist optional DP/demat charges safely, migrate canonical accounting/persistence and total-charge recomputation, then integrate statutory GST valuation only through reviewed source-backed policy paths. Actual per-fill invoice acceptance remains evidence-gated; no personal contract note is required.
- Safety unchanged: PR #6/#7 Draft and unmerged; PAPER mandatory; live broker order writes and automatic live-fill promotion/scheduling disabled; original `tarunsharma2610-del/Tradepro` untouched and out of scope.


## Phase 3 CI synchronization — 26 October 2026 (DP/demat snapshot gate)

- Latest verified code head: `6a6a3560aff18bb94d34b77640058a17d2a208b8`; exact-head Backend CI [#40381396722 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40381396722): **1,057 passed, 1 warning**. Broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore drill and retained restore evidence passed.
- Optional `demat_transaction_charges` can now be represented as a distinct pending canonical snapshot and allocated into the durable per-fill allocation ledger when source rows are independently reviewed. Migration expands the canonical snapshot vocabulary. It does **not** authorize final accounting: DP/demat reconciliation promotion deliberately fails closed until Execution persistence and total-charge recomputation are implemented.
- Next Phase 3 gate: add dedicated optional Execution DP/demat persistence and a single verified total-charge recomputation path, with migration/idempotency/rollback and delivery-vs-non-delivery tests. Keep actual invoice/per-fill acceptance evidence-gated; no personal contract note is required.
- Safety unchanged: PR #6/#7 Draft and unmerged; PAPER mandatory; live broker order writes and automatic live-fill promotion/scheduling disabled; original `tarunsharma2610-del/Tradepro` untouched and out of scope.
