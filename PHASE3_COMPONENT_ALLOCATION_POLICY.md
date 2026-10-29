<!-- Phase 3 continuation sync: 27 October 2026. Latest verified code/test head: 31ce2a10bcc789c223608c6566082b24aea7358c; Backend CI #40383076131 SUCCESS. Latest checkpoint-document commit: 61f23e5ce714c37a97f996f5f75c1963cc1136e6; docs-head CI #40383798007 must be checked for final conclusion. DP/demat Execution persistence and central charge-total recomputation are implemented; next gate is focused accounting audit. GST/IPFT implementation is not being restarted. PR #6/#7 stay Draft/unmerged; PAPER mandatory; live broker writes disabled; original Tradepro repository out of scope. -->

## Latest authoritative checkpoint — 26 October 2026, 21:06 IST

This section supersedes earlier statements in this file that identify an older commit or CI run as the latest checkpoint. Historical entries below are retained for audit history.

- **Only target repository:** [tarunsharma2610-del/tradepro-improved](https://github.com/tarunsharma2610-del/tradepro-improved). Branch: `phase3/durable-per-fill-charge-allocation`. Latest documentation commit before this sync: `73c4a7cdcde4490bd520d5e75cc87fe1b4ffa310`. Exact-head documentation CI [#40346810442 PASSED](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40346810442).
- GST estimate implementation commit `b75a97f6cd0043c185375cc253b84a1e6d6bfea1`; exact-head CI [#40345937942 PASSED](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40345937942): 1,012 tests passed, 1 warning. Broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore/evidence-retention checks passed.
- **GST estimate decision:** apply 18% to brokerage + combined exchange transaction/IPFT charge exactly once; include explicit demat/DP charges additionally for equity delivery. Do not add STT, stamp duty, SEBI or trade notional to this published GST estimate base. Upstox's Brokerage Details API sample arithmetic conflicts with the explicit public schedule; the sample does not override the schedule or prove live billing is wrong. Sources: [Upstox pricing](https://upstox.com/brokerage-charges/), [Brokerage Details API](https://upstox.com/developer/api-documentation/get-brokerage/), [Trades Charges API](https://upstox.com/developer/api-documentation/get-trade-charges/), [NSE transaction/IPFT circular](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf).
- **New Phase 3 gap found:** `demat_transaction_charges` is intentionally blocked by source-to-canonical mapping; canonical live accounting and `Execution` currently support six components only. Equity-delivery actual-charge accounting with a DP/demat charge is therefore not accepted yet. The estimate helper can include a demat amount, but that does not mean actual accounting can persist/reconcile it. Keep this fail-closed; do not drop DP charges or fold them into another component. Next implementation gate: product-aware canonical demat/DP component and total-charge persistence, migration, idempotency, allocation, and delivery/non-delivery regression tests—or keep delivery actual accounting unsupported until complete.
- Actual per-fill GST/invoice acceptance remains evidence-gated. Public schedules and calculators support estimates, not account-specific actuals; aggregate API values and null fields are not per-fill invoice proof. User is not required to provide a personal contract note. Actual tariff candidates remain DRAFT.
- Phase 3 remains IN PROGRESS; PR #6 remains open/draft/unmerged. PAPER mandatory; live broker order writes, automatic live-fill promotion and automatic scheduling remain disabled. Original `tarunsharma2610-del/Tradepro` must not be modified. AI/Algory integrations remain deferred until Phase 3 acceptance.

---

## Historical checkpoint (superseded) — 26 October 2026 (latest verified CI)

- Target repository only: `tarunsharma2610-del/tradepro-improved`; branch `phase3/durable-per-fill-charge-allocation`; implementation/test head `44830ec48b50b4f470ec9ca95dd2d3f4339dd3df`. Do not modify original `Tradepro`.
- Exact-head Backend CI: [run #40294178677 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40294178677), including the test separating NSE/IPFT arithmetic reconciliation from GST taxable-base approval.
- GST estimate helper accepts exactly 18%; tests reject 0%, 5%, 100%, and 100.01%. Rate guard does not approve the taxable base; components need reviewer and invoice/source evidence.
- ₹307/crore versus ₹306.99/crore transaction charge + ₹0.01/crore IPFT is arithmetic reconciliation only, not GST-base approval.
- Canonical live-fill integration is verified: six independently verified charge snapshots, evidence revalidated under lock, no raw-only fallback; brokerage cap applied once before deterministic paise-exact allocation.
- Remaining Phase 3 gates: effective-dated tariff applicability; component-specific per-fill allocation acceptance; invoice/source-backed GST/IPFT and product/segment evidence; adversarial/migration/recovery review; final exact-head docs/sign-off.
- Upstox public schedules/calculator are estimates; aggregate charges endpoint is not actual per-fill evidence. Null remains unknown, not zero. Synthetic restore is not actual Oracle recovery.
- PAPER mandatory; live broker writes, automatic live-fill promotion and automatic scheduling disabled. PR #6 open/draft/unmerged unless explicitly approved. Defer AI/open-source adaptations until Phase 3 acceptance. Documentation commit needs its own CI.

---

# Phase 3 — charge-component allocation policy review

Review date: 23 October 2026

## Purpose and release rule

This document separates (1) arithmetic allocation of a source amount, (2) the economic/legal basis that makes a per-fill allocation appropriate, and (3) evidence that the source amount actually came from Upstox. Passing one layer does not prove the others.

**Fail closed:** never infer that a component is suitable for QUANTITY, NOTIONAL, or EXPLICIT_REVIEWED merely because the generic allocation function supports that basis. A source amount shown only as an account/day/segment aggregate is not proof of a component total for an individual fill set. Do not auto-promote charge allocations to accounting until the source scope, component, effective date, segment/exchange, eligible fill set, and independent review are established.

## Public-source findings

- Upstox's [brokerage and charges page](https://upstox.com/brokerage-charges/) lists charges by product/segment and effective period. It currently shows transaction-charge changes effective 1 March 2026 and STT changes effective 1 April 2026. Therefore rates must be effective-dated; do not apply a single static rate to historical trades.
- Upstox's [brokerage calculator](https://upstox.com/calculator/brokerage-calculator/) illustrates a trade-specific charge breakdown, but a calculator output is not a broker-issued contract note or proof of charges actually booked to a user's account.
- NSE's [SEBI turnover fees, STT and other levies](https://www.nseindia.com/static/invest/first-time-investor-sebi-turnover-fees-stt-other-levies) describes rates and bases that differ by transaction, side and product; its current page shows changes effective 1 April 2026.
- NSE's [stamp duty reference](https://www.nseindia.com/static/invest/first-time-investor-stamp-duty-charges-taxes) lists different rates for delivery, non-delivery and derivatives and identifies the buyer-side basis.
- Public third-party copies of historical Upstox contract notes were reviewed for layout only. Their authenticity was not independently verified and historical values are not current tariff evidence. Synthetic fixtures remain synthetic.

## Component-by-component engineering policy

| Component | Basis / attribution concern | Required guard before promotion |
| --- | --- | --- |
| Brokerage | Often charged per executed order, not inherently proportional to each fill's quantity or notional. One order may have multiple fills and caps/minimums can matter. | Prefer broker-reported order/component totals with an explicit, reviewed order-to-fill allocation rule. Do not blindly distribute by notional or quantity where order-level caps or minimums affect the split. |
| STT/CTT | Depends on segment/product, buy/sell side and taxable value; options and exercised options have distinct rules. | Require the applicable effective-dated rule, correct taxable base and side. For broker-reported totals, retain the source scope and reviewer-approved eligible fill set. |
| Exchange transaction charges / IPFT | Depends on exchange, segment, effective period and turnover or premium basis; published rates can change. | Require exchange + segment + effective-dated rate/basis or an independently reviewed source total. Do not treat all exchange products as having the same basis. |
| SEBI turnover charges | Turnover-based and subject to applicable security category/rate. | Use a verified turnover basis and effective-dated rule, or reviewed source total with exact eligible fill manifest. |
| Stamp duty | Buy-side only; rate depends on delivery/non-delivery and product/segment. | Exclude ineligible sell fills; use applicable buy-side taxable value and effective-dated rate or reviewed source allocation. |
| GST | Derived from the applicable taxable service-charge base, not simply each fill's notional. Components included in the base can vary with applicable rules and broker charge categories. | Verify the GST base against its underlying charge components and applicable tax treatment before any per-fill split. Do not allocate GST directly by notional without an approved derivation rule. |
| DP/demat and other order/account/service fees | May be per scrip/day, per order, or account/service event rather than per fill. | Model at the actual economic event level. Do not force these charges into fill-level allocation if their source scope is order-, scrip-, day- or account-level. |

This matrix is an engineering control, not tax/legal advice. Rates and legal treatment must be validated against the applicable official source and effective date before implementing automatic calculation.

## Current implementation status

- The generic largest-remainder allocator provides deterministic paise-exact arithmetic and versioned rounding; it does **not** decide the legally/contractually correct basis.
- The source reconciliation service verifies reviewed evidence metadata, document hash/size, independent component review, exact fill-set manifest, component source total, allocation method/basis and each recomputed per-fill amount.
- The generic persisted component allowlist currently covers brokerage, STT, exchange charges, SEBI charges, stamp duty and GST. Do not interpret inclusion in that allowlist as automatic approval of any basis for that component.
- Public research and synthetic tests support development. They do not authenticate a real contract note or prove an account-specific charge.
- Automated tariff-derived per-fill allocation remains gated on explicit segment/product/effective-date rules and component-specific regression tests. Unsupported or ambiguous charge scopes must remain pending manual review rather than be promoted.

## Acceptance checklist

- [x] Public Upstox and exchange references reviewed for charge categories and effective-date changes.
- [x] Policy gap documented: generic arithmetic support is not a component-specific basis approval.
- [ ] Implement and test effective-dated rules by exchange, segment, product, transaction side and charge component before automatic tariff-derived allocation.
- [ ] Add tests for brokerage per-order caps / multi-fill orders, GST-base composition, buy-side stamp duty eligibility, option-premium versus futures turnover, and tariff changes across effective dates.
- [ ] Confirm source scope and reviewer approval are mandatory for any source-total allocation; aggregates must not be misrepresented as per-fill evidence.
- [ ] Keep live accounting promotion disabled until all relevant acceptance gates are approved.

## Safety and scope

PR #6 remains draft and unmerged pending acceptance review and explicit user approval. Live broker order writes remain disabled. All work is confined to `tarunsharma2610-del/tradepro-improved`; the original `tarunsharma2610-del/Tradepro` repository is out of scope.

## Verification checkpoint — 2026-10-24
Aggregate variance concurrency/replay passed exact-head CI run `40064129721` on `dbff090610028cfb9f5a87585d9c8e697449cd23` (738 passed, 1 warning). This does not close the component-specific tariff checklist above. Next: implement and test reviewed effective-dated applicability for brokerage caps/multi-fill orders, GST taxable-component composition, buy-side stamp duty and applicable segment/product/side rules before enabling tariff-derived automatic per-fill allocations. Ambiguous bases and event-level fees remain fail-closed.

## Current Upstox rate-source note — 2026-10-24
The official Upstox brokerage page now shows effective-date rows for STT/CTT from 1 April 2026 and exchange transaction charges from 1 March 2026, alongside legacy rows. The current page lists equity-futures STT/CTT at 0.05% sell-side and equity-options STT/CTT at 0.15% sell-side on premium, with a separate exercised-option sale row; NSE transaction charges are shown as 0.00307% for equity delivery/intraday, 0.00183% for futures and 0.03553% on option premium. These are source-review findings, not active rules. Archive/hash the source, corroborate statutory rates, define applicability/base and test effective-date boundaries before activating any rule. See `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`.

## Upstox API estimate boundary — 2026-10-24 (CI verified)
Upstox brokerage API amounts are stored as estimate-only component snapshots. Total and DP-plan minimum are metadata, not separately allocated charge components; transaction + clearing + IPFT are grouped as `exchange_charges` to align with the current reviewed source-component vocabulary. API estimates must match exact fill-set quantity, price, side and instrument before variance comparison. This does not activate tariff rates or enable automatic allocation. Exact-head CI run `40065219626` passed (**754 passed, 1 warning**).

## Brokerage calculator shape update — 2026-10-24 (CI verified)
The calculation engine now supports flat per-order brokerage (`ORDER_FIXED`/`INR_FIXED`) separately from capped percentage brokerage. This reflects the distinction in the Upstox tariff page between fixed per-executed-order charges and percentage rates subject to a ₹20 cap. No rates are active from this change; automatic allocation remains gated on source review, effective-dated applicability and component-specific tests. Exact-head CI run `40065607232` passed (**756 passed, 1 warning**).

## DRAFT tariff candidate registry — 2026-10-24 (CI verified)
The source excerpt `docs/source_snapshots/UPSTOX_CHARGES_2026-10-24.md` captures current Upstox rows and cross-checks the 2026 STT change against NSE. Eighteen effective-dated STT/exchange-charge candidates are stored as DRAFT and selector tests confirm they are not active. Stamp duty still requires current statutory corroboration; IPFT/transaction-charge combination is unresolved. Exact-head CI run `40065979244` passed (**760 passed, 1 warning**). No tariff-derived automatic allocation is enabled.


## Official tariff-source recheck — 24 October 2026

- Rechecked the official Upstox charges page on 2026-10-24 and recorded the findings in `docs/UPSTOX_CHARGE_RULE_SOURCE_REGISTER.md`. It lists 1 April 2026 STT/CTT changes and 1 March 2026 NSE transaction-charge changes, and states IPFT is combined with transaction charges while separately listing ₹0.01/crore (options on premium) plus GST. Current candidate rows represent transaction charges only; IPFT composition/effective-date treatment must be resolved before approval.
- The same page's ₹10/order API-order brokerage note is explicitly valid only through 31 December 2025 (excluding GTT); do not treat it as current pricing. Current authenticated API-order-specific terms remain unverified.
- NSE's official stamp-duty page is still marked updated 03/10/2023, so it is not a fresh 2026 publication. Independent current statutory corroboration remains a release gate.
- No tariff candidate was approved or activated, no estimate was promoted to actual per-fill accounting, and no live broker order was sent. Source excerpt remains normalized rather than byte-for-byte HTML. Exact-head CI must be checked after these documentation changes; prior green CI does not cover the new head.


## Brokerage tariff effective-date gate — 24 October 2026

- Reconfirmed the official Upstox public page lists brokerage examples: equity delivery/options ₹20 per executed order; equity intraday ₹20 or 0.1% (whichever lower); equity futures ₹20 or 0.05% (whichever lower). The source excerpt does not establish a precise effective_from date for these brokerage terms.
- A trial draft-registry addition was reverted because populating required `effective_from` with retrieval date would falsely imply a published effective date. No brokerage candidates with guessed effective dates remain in the tariff registry. Before registering these rows, obtain a source that establishes the effective date or model an evidence-backed “current as observed” state without pretending retrieval date is tariff effective date.
- Existing helpers can model flat per-order brokerage and capped percentage brokerage (`maximum_inr`), but helper capability is not source approval. Published “whichever lower” semantics need regression coverage before a reviewed rule can be eligible for use.
- Prior Backend pytest run [40067742361](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40067742361) passed on the then-current head. Later registry/documentation commits need exact-head CI confirmation; do not reuse that run as proof for later commits.
- No rates were activated, no estimates promoted to actual accounting, and no live broker order was sent. PR #6 remains draft/unmerged; original `Tradepro` remains out of scope.


## 2026-10-24 — Resolver acceptance and CI checkpoint

- Backend workflow `40108183667` succeeded on prior head `8214430f562f6f425cfc1b9b6a6b3b547832b68a`. New resolver tests add exact broker/endpoint/schema/field/scope matching and non-finite-number rejection; newer commits still require CI.
- Mapping identity fixtures use immutable dataclass replacement. Intended-use semantics remain explicit; missing/null/invalid values remain unusable and retain provenance; numeric zero remains distinct.
- Accounting acceptance includes replay/conflict, ledger reconciliation, lock order, rollback, reviewer authority and PostgreSQL verification/promotion race coverage. Re-check exact test and workflow status before claiming complete. CI does not establish production tariff correctness or broker-origin authenticity.
- Safety gates unchanged: PR #6 draft/unmerged; live broker order submission and automatic quantity/notional allocation disabled; production Upstox mappings/tariffs unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Resolver field-identity guard added; CI pending

- Resolver now checks that the payload field name matches the terminal field in the selected approved mapping path. This closes a semantic mismatch where a caller could select `charges.ipft` but normalize another payload field.
- Implementation commit: `77aa77aec37dc535c3e427ca3f88c2ccb5e75ed8`; regression test commit: `5c5482c7f7fa623707698f64b6a061351e5e5b87`. CI for the latest commits is pending; previous green runs apply only to earlier heads.
- Existing accounting tests cover lock ordering, replay idempotency, conflicting evidence and rollback. A genuine concurrent two-session verification-versus-promotion race is not demonstrated in the inspected live-fill test file; locate/verify other integration coverage before marking complete.
- PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled; production Upstox mappings/tariffs remain unapproved. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Latest resolver CI verified; PostgreSQL race coverage located

- Latest PR head `ed346e823cbfae8448fae0134c4ff864bfcc60ac` passed Backend workflow [#40109041654](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40109041654). This verifies the field-identity guard and regression test at that head.
- Located PostgreSQL-only integration tests in `backend/tests/test_broker_charge_allocation_postgres_concurrency.py`, including concurrent source verification vs allocation promotion and live-fill promotion vs ledger verification, as well as conflicting fill-set and tariff estimate/variance persistence races.
- These tests require `TEST_POSTGRES_URL`. Verify the PostgreSQL workflow actually ran these tests rather than skipped them before treating concurrency acceptance as complete.
- PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled; production Upstox mappings/tariffs remain unapproved. Work only in `tradepro-improved`; original `Tradepro` remains untouched.


## 2026-10-24 — Upstox brokerage calculator restricted to estimates; CI pending

- Official Upstox `GET /v2/charges/brokerage` takes proposed instrument, quantity, product, transaction type and price, returning a charge calculation; this is not proof of final booked per-fill charges. https://upstox.com/developer/api-documentation/get-brokerage/
- Resolver now blocks `/v2/charges/brokerage` from `PER_FILL_ACTUAL` and actual `AGGREGATE_SUMMARY` use even if a mapping is misleadingly labelled. Existing guard still blocks `/v2/trade/profit-loss/charges` from per-fill actual use. New regression tests cover both misuse cases.
- Implementation `3486d854dae2451858a858cb627602aca7338969`; tests `6c92101a1890a0f4d761e86ed3db047a269fd10d`. Prior head `6cc8b58f635fcb4f1b1cb3e5997099d074800a28` passed workflow #40111501429. CI for the new commits must be verified.
- Production mappings/tariffs remain unapproved; null is not zero; automatic quantity/notional allocation and live broker order submission remain disabled. PR #6 stays draft/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Authoritative checkpoint — 26 October 2026 (documentation CI verified)

- Repository: `tarunsharma2610-del/tradepro-improved`; branch: `phase3/durable-per-fill-charge-allocation`.
- Latest implementation commit: `ac7d27f2c9922925483b5b906c484c0d5a4e3f53`; exact-head Backend CI [#40287765745 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40287765745).
- Documentation synchronization commit: `f90573d653c7103bf9cfdb1f867da97b176d3240`; its exact-head Backend CI [#40289107666 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40289107666). Backend tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore/evidence retention passed. Synthetic restore is not proof of actual Oracle Cloud recovery.
- Approved public Upstox STT/exchange rules are estimate-only. Account-specific actual charges, GST taxable-base composition, stamp duty, SEBI/DP/demat/other charges, unsupported exchange/segment mappings, and per-fill actual evidence remain unapproved. Candidate tariff entries remain DRAFT unless separately allowlisted and reviewed.
- Phase 3 remains in progress. Next gates: independently reviewed tariff applicability; component-specific per-fill allocation rules; invoice/source-backed GST/IPFT and product/segment evidence; final adversarial, migration and recovery review; exact-head acceptance sign-off. Do not repeat canonical live-fill integration.
- Safety: PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. PR #6 stays open/draft/unmerged without explicit user approval. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.
- This documentation commit’s CI is green. Continue only from this checkpoint and verify CI for every subsequent implementation/checkpoint commit. Historical entries do not supersede this checkpoint.


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


## Session checkpoint sync — 26 October 2026

- Exact-head Backend CI [#40368554399 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40368554399) passed on code head `9d3f255480da9a71980a9d3819fbb69a34835753`. Later documentation-only commits are being synchronized; verify CI on the final new head before calling it green.
- CBIC statutory GST framework: CGST Act section 15 and CGST Rules Rule 33/Rule 27; pure-agent exclusion requires documented conditions and is not automatic. IGST Act section 12(12) governs stock-broking place of supply; supplier state vs place-of-supply state determines IGST or CGST+SGST. Sources: https://cbic-gst.gov.in/sectoral-faq.html ; https://cbic-gst.gov.in/valuation-rules.html
- Public GST schedule helper is estimate-only. Statutory valuation service/tests remain to be implemented; GST/IPFT acceptance is not complete. Next: implement Section 15 component treatment, Rule 33 evidence checks, tax-state split, Decimal/paise rounding, and fail-closed missing facts. IPFT combined/separate and DP/demat persistence/reconciliation remain open.
- No personal contract note available or required. Safety: only `tarunsharma2610-del/tradepro-improved`; PR #6/#7 Draft/unmerged; PAPER-only; live order writes disabled; original Tradepro repository out of scope.

## Verified checkpoint — 27 October 2026 (DP/demat completeness)

- Exact-head Backend CI #40459846143 passed on code/test commit `9400bc9aa221e2cf3b735e49a8e9a6d351237f02`: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40459846143. Backend pytest, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips and synthetic PostgreSQL/document-volume restore checks passed.
- DP completeness regression is verified: invalid status cannot yield a complete total; `KNOWN` needs valid paise-exact amount; `NOT_APPLICABLE` needs no amount; unknown/inconsistent states fail closed. This checkpoint does not approve statutory tariff or invoice-level GST/IPFT composition.
- Next gate: per-fill source mapping, replay/idempotency conflicts, atomic rollback and component applicability. Actual contract-note and production Oracle backup/restore acceptance remain evidence-gated.
- Safety: PAPER mandatory, live broker writes disabled, PR #6/#7 Draft/unmerged; original `Tradepro` repo out of scope.


## API-first paper-trade charge estimation decision — 29 October 2026

- User-approved behavior: use Upstox's pre-trade Brokerage Details API for paper-fill charge estimates when it returns a complete, valid, internally consistent breakdown. Keep the existing deterministic local calculator as the automatic fallback if the API is unavailable, expired/unauthorized, incomplete, null/invalid, or inconsistent. This is estimation only, not live-trading/accounting promotion.
- Implementation added on the Phase 3 branch: `backend/app/services/paper_trade_charge_estimator.py` plus deterministic tests. `ExecutionService` now uses API-first estimates for market and matched limit paper fills and records `PAPER_UPSTOX_API_ESTIMATE` versus `PAPER_ESTIMATE` in the existing execution charge-source field. Components are accepted only when paise-exact supported components sum exactly to the API total; transaction, clearing and IPFT are combined once in the existing exchange-charge field. Unknown/incomplete fields fall back rather than block paper trading.
- Existing post-trade Upstox charges endpoint remains aggregate reconciliation evidence, not per-fill actuals. The API route already exists. GST reconciliation remains available without blocking paper-trade P&L.
- Implementation commits: `b90c09dc82a51181bc9eae422cb025eb79c65bcb`; default-enabled setting `UPSTOX_CHARGE_ESTIMATES_ENABLED`. CI disables network estimates only for the broad execution suite; mocked estimator tests cover API and fallback paths.
- Backend CI [#40755234415](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40755234415) — **SUCCESS** on code/test head `778e76d3554a3baedc41f0396276c1cb3dafc38f`: **1,197 passed, 1 warning**; broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore/evidence retention passed. Documentation sync head `d57dd476ecd6acebd4dc9e169912b877811a8166` still needs exact-head CI verification before it is called green.
- Next: continue the next uncovered Phase 3 accounting acceptance gate after CI recovery. Do not reopen GST/IPFT from zero or make minor estimate variance a paper-trading blocker. Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled; original `Tradepro` out of scope.


## Authoritative Phase 3 engineering closure — 29 October 2026

This section supersedes older status/next-step notes above; earlier entries remain as historical audit trail.

**Status: Phase 3 engineering acceptance is complete for the agreed PAPER-mode scope.** Do not confuse this with live-money release approval or actual-charge promotion.

Verified code checkpoint: `3a0c464afcb10261d1590607f8440affd21295a0`, Backend CI [#40878367369 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40878367369), **1,207 passed, 1 warning**. Backend tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, synthetic restore, and restore-evidence retention passed. The documentation-sync head must pass its own CI before this sync is considered green.

Engineering closure covers deterministic paise-exact per-fill allocation; integrity-checked/reviewer-controlled evidence; canonical mapping; combined/split transaction/IPFT representation; replay/idempotency/conflict protection; locked total verification and rollback safeguards; explicit DP/demat persistence/completeness; statutory GST and GST/API diagnostic primitives; and Upstox API-first PAPER estimates with hardcoded fallback and standard disclaimer. The post-trade Upstox Trade Charges API remains aggregate-only and cannot be promoted to per-fill actual evidence.

Paper estimate disclaimer: “Estimated charges may differ from actual broker charges. For paper trading only; these are not actual booked charges.”

Operational gates are separate: credentialed Upstox OAuth/API smoke test and real Oracle backup/restore require deployment; any tariff lacking independently approved broker/exchange/segment/product/date evidence remains estimate-only/fail-closed for actual accounting. Historical contract-note fixtures are regression coverage, not a reason to promote estimates to actuals. These gates do not block PAPER engineering closure.

Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6/#7 remain Draft/unmerged; PAPER mandatory; live broker writes disabled. Phase 4 is the next separate increment after exact documentation-head CI passes.


## Resume checkpoint — 29 October 2026 (Upstox response-schema validation)

- **Code/test head:** `404c1e11ef4f2557c791c720c8d9a3fbc4e93bc1`; exact-head Backend CI [#40883660756 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40883660756). The workflow result confirms success; its summary did not expose a reliable pytest count, so no count is asserted here.
- **Concrete fix:** `UpstoxChargeApiOrchestrationService` no longer marks arbitrary successful HTTP JSON as usable. Brokerage estimates require `status == "success"` and `data.charges`; post-trade aggregate charges require `status == "success"` and `data.charges_breakdown`. Wrong/missing schema returns `usable=false`, clears the payload and records `INVALID_RESPONSE_SCHEMA`.
- **Regression coverage:** valid endpoint-specific response fixtures plus incorrect endpoint schema, unsuccessful/missing status, and aggregate wrong-shape payload cases.
- **Evidence boundary:** Brokerage Details remains estimate-only; Trade Charges remains aggregate reconciliation-only and never per-fill actual evidence. Null IPFT must not be silently coerced to zero. This fix validates response shape; it does not approve tariffs or promote accounting.
- **Contract-note continuity:** previously supplied January 2023 Upstox/RKSV contract-note examples remain available as historical regression fixtures; do not ask the user to provide them again. Their scope must be respected when using them for GST totals versus per-fill allocations.
- **Next:** verify CI on the exact synchronized documentation head. Keep PR #6/#7 Draft and unmerged, PAPER mode mandatory, live broker writes disabled, and the original `tarunsharma2610-del/Tradepro` repository untouched.
