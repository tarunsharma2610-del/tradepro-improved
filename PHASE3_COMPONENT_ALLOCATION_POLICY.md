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
