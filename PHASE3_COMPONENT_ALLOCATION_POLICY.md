## Authoritative Phase 3 checkpoint — 26 October 2026

- Repository `tarunsharma2610-del/tradepro-improved`; branch `phase3/durable-per-fill-charge-allocation`; implementation head `eeea33a11303d03bee508be2f5af887dd5ee26e0`; exact-head Backend CI [#40290116323 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40290116323).
- Latest change: brokerage minimum/maximum cap is applied once to the whole order estimate before deterministic, paise-exact allocation to reviewed fill weights. Tests cover capped/unequal fills, stable tie rounding, invalid weights, and DRAFT tariff rejection.
- Phase 3 is NOT complete. Remaining gates: independently reviewed effective-dated tariff applicability; approved component-specific per-fill allocation; invoice/source-backed GST/IPFT and product/segment evidence; adversarial, migration and recovery review; exact-head final sign-off.
- Public tariff rules are estimate-only. They do not establish actual account-specific booked charges or approve unsupported GST, stamp-duty, exchange, or segment mappings. Do not repeat verified canonical live-fill integration.
- Safety: PAPER mode mandatory; live broker order writes, automatic live-fill promotion and automatic scheduling disabled. PR #6 remains open/draft/unmerged without explicit approval. AI/open-source adaptation only after Phase 3 acceptance. The documentation commit needs its own CI.

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
