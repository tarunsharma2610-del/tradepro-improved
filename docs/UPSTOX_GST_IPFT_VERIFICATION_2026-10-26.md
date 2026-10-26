# Upstox GST/IPFT evidence review — 26 October 2026

## Decision summary

**Outcome: rate and exchange-charge arithmetic supported for a narrow NSE public-schedule estimate; GST component composition remains unresolved and must stay DRAFT.** This is an evidence update, not a legal opinion or actual-account charge certification.

Research covered the current Upstox public charges page, Upstox Brokerage Details and Trades Charges API documentation, NSE circular NSE/FA/73061, CBIC stock-broking GST FAQs and valuation rules, plus public historical Upstox contract-note examples and community-search results. No authenticated current 2026 contract note was found that conclusively establishes the present GST taxable-base treatment for all four candidate products. Public historical copies are useful for layout and field discovery only; their authenticity and current applicability are not independently established.

## Findings by rule

| Candidate | Evidence found | Decision now |
|---|---|---|
| GST rate: 18% | Upstox publishes 18% for these equity products; CBIC confirms stock-broking service is taxable. | Rate is strongly supported as a public-schedule assumption; keep candidate non-executable pending versioned legal/source review. |
| Equity delivery GST components | Upstox public schedule says brokerage + transaction + demat + IPFT. | DRAFT: delivery-specific demat and IPFT inclusion needs the actual tax-invoice/tariff mapping reconciled. |
| Equity intraday GST components | Upstox public schedule says brokerage + transaction + IPFT. | DRAFT: no tax-base approval from the published rate alone. |
| Equity futures GST components | Upstox public schedule says brokerage + transaction + IPFT. | DRAFT: product-specific tax base unresolved; STT is a separate charge, not brokerage. |
| Equity options GST components | Upstox public schedule says brokerage + transaction + IPFT. Transaction charge is based on premium under the published NSE schedule. | DRAFT: premium base for exchange charges does not mean trade premium/notional is itself a GST component. |
| NSE transaction charge + IPFT, effective 1 Mar 2026 | NSE circular NSE/FA/73061 and Upstox's current schedule agree on combined outflow: cash equity ₹307/crore, futures ₹183/crore, options ₹3,553/crore premium. IPFT contribution is ₹0.01/crore. | Arithmetic supported for this narrowly scoped NSE schedule. Model as one combined exchange-charge component for this tariff; do not add IPFT twice. This does not settle GST base. |
| BSE cash equity / futures / options | Upstox says cash rates vary by scrip group, futures nil, options 0.0325% on premium; independent effective-dated exchange corroboration is incomplete. | DRAFT / partial coverage only; no generic BSE cash/futures rule activation. |
| STT | Upstox current schedule and NSE's official derivatives STT reference show changes effective 1 Apr 2026, including futures sell 0.05% and options sell 0.15% of premium; exercised options have separate intrinsic-value treatment. | Candidate rows remain separately effective-dated and DRAFT pending final source/scope review. Never add STT to GST base automatically. |
| Stamp duty, SEBI, clearing, other and DP/demat | Some public rates exist, but the exact component basis, effective dates, account-specific pricing and tax-base treatment vary. | Keep unapproved until each rule has its own scope, date and evidence. |

## Source-specific interpretation

1. **Upstox pricing page** — https://upstox.com/brokerage-charges/  
   The page explicitly says GST is 18% on brokerage + transaction charges + IPFT, with demat additionally listed for equity delivery. It also says IPFT is combined with transaction charges in its newer schedule. Its historical tables remain on the page, so use the applicable effective-date section rather than older displayed rows.

2. **NSE Finance & Accounts Circular NSE/FA/73061, 27 February 2026** — https://nsearchives.nseindia.com/content/circulars/FA73061.pdf  
   Effective 1 March 2026: combined transaction/IPFT outflows are ₹307/crore cash, ₹183/crore equity futures and ₹3,553/crore options premium; the IPFT contribution is ₹0.01/crore. The model must represent one combined charge, not combined rate plus a second IPFT line.

3. **Upstox Brokerage Details API** — https://upstox.com/developer/api-documentation/get-brokerage/  
   An authenticated quote API can cross-check inputs such as instrument, quantity, product, side and price. It is an estimate/quote, not by itself proof of final invoiced charge or per-fill actual allocation.

4. **Upstox Trades Charges API** — https://upstox.com/developer/api-documentation/get-trade-charges/  
   Documents a segment and financial-year/date-range breakdown with GST, STT, stamp duty, transaction, clearing, IPFT, SEBI and demat fields. Its example allows `ipft: null`; null means unknown/not separately returned, not zero. This response is an aggregate reconciliation source, not a contract-note substitute or per-fill proof.

5. **CBIC Stock Broking FAQs** — https://cbic-gst.gov.in/sectoral-faq.html  
   Q78 confirms brokerage is taxable stock-broking service. Q77 says STT, stamp duty and other tax recoveries are excluded only if pure-agent conditions under Rule 33 are met; otherwise valuation follows Section 15 and Rule 27. This does not itself decide IPFT's treatment in Upstox's invoice or establish that every fee belongs in/out of the base.

6. **CBIC valuation rules** — https://cbic-gst.gov.in/valuation-rules.html  
   Pure-agent exclusion depends on the actual conditions, including separate indication and recovery of the amount paid to the third party. Do not apply a universal exclusion merely because a component is labelled a tax/levy.

7. **Public historical contract-note examples** — https://www.scribd.com/document/971660843/CW-T-3JCTYG-20250312-NSE-66319975-1 and https://www.scribd.com/document/735902961/CW-T-842243-20240521-NSE-35749411  
   These are third-party copies, not authenticated by Upstox. The historical example evidence is not enough to settle the current 2026 GST base, especially after the exchange/IPFT schedule change. Do not store personal identifiers or claim authenticity.

## Reproducible arithmetic sanity check

At ₹1 crore of eligible base, the new NSE combined cash-equity charge is ₹307. Its arithmetic split is ₹306.99 transaction charge + ₹0.01 IPFT, if representing the component split for explanatory reconciliation. Applying 18% to ₹307 gives ₹55.26; applying 18% to ₹306.99 and then adding a second IPFT charge would be an incorrect double-count model for the combined tariff. **This arithmetic example does not prove that the entire ₹307 is included in the legally/broker-defined GST taxable base.** That remains the open acceptance question.

## Required code / acceptance behavior

- Keep all four GST component-set candidates DRAFT; do not turn the public page into a live-account tax rule.
- Represent combined NSE transaction/IPFT as a single canonical `exchange_charges` component where the source schedule is combined; do not add a separate `ipft` on top.
- Preserve a separately reported IPFT field as source evidence if an API/statement reports it, then canonicalize against the combined tariff identity without double counting. A null field remains unknown.
- Never calculate GST on trade notional/turnover as a component. A percentage basis such as premium may define the exchange charge calculation, not the GST taxable-service base.
- Do not automatically include/exclude STT, stamp duty, SEBI, clearing, DP/demat or other charges from GST base without the reviewed tariff/invoice mapping.
- Maintain source URL, retrieval timestamp, effective dates, normalized excerpt hash, API schema/version, raw-response fingerprint, and reviewer decision.
- Tests must cover product-specific bases, combined-vs-split IPFT, null/unknown charges, rounding, effective-date transitions and “no trade_notional/turnover component”.
- Public-source evidence may support **estimate-only** tariff rules. Actual-charge/per-fill promotion remains based on reviewed source evidence and canonical allocation controls.

## Status and next gate

GST component composition is **not approved**. The 18% rate and the narrow March 2026 NSE combined-charge arithmetic are supported, but they are not enough to approve the four GST component sets. Continue researching public invoice examples and authoritative rules; then update tests and candidate decisions only when the taxable-base conflict is resolved. No user-supplied contract note is required to continue engineering, and none has been requested as a prerequisite.

PAPER mode remains mandatory. Live broker order writes, automatic live-fill promotion and automatic scheduling remain disabled. PR #6 stays open/draft/unmerged absent explicit user approval. Work only in `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is out of scope.


## Material discrepancy from the public historical contract-note example

The publicly indexed Upstox contract-note copy dated 21 May 2024 explicitly reports:

- `[IGST 18% On Charges]`: ₹13.96.
- `GST Taxable Value of Supply`: brokerage ₹0.01 + SEBI fees ₹0.11 + turnover charges ₹3.44 + demat transaction charges ₹74.00 = ₹77.56.
- `[IPFT CHG]`: ₹0.11 appears as a separate levy but is not included in that displayed taxable-value sum.

The arithmetic is internally consistent: ₹77.56 × 18% = ₹13.9608, rounded to ₹13.96. This is **materially different** from Upstox's current public pricing page, which says its GST base includes IPFT and does not list SEBI fees in that base. The note is a third-party Scribd copy and cannot be authenticated; it is also from 2024, before the current combined transaction/IPFT tariff. It therefore proves a documented historical presentation, not the correct current 2026 rule. It is strong enough to block automatic approval until the discrepancy is explained by a current official source, current authentic invoice example, or documented billing policy. Do not infer that IPFT is universally excluded or that SEBI is universally included.


## Additional public evidence review — 26 October 2026

Further searches found publicly indexed Upstox realized-P&L reports covering FY 2025–26. These reports show aggregate `INTEGRATED GST` and `IPFT CHG` as separate charge totals, but they do not show the contract-note GST taxable-value composition needed to establish the per-trade GST base. Examples: https://www.scribd.com/document/1074573680/realizedPnL-EQ-2025-04-01_To_2026-03-31-6LBU3B and https://www.scribd.com/document/1061368614/realizedPnL-EQ-2025-04-01-To-2026-03-31-4ZBKKF. These are third-party copies and are not authenticated; they support only the narrow observation that aggregate reports list GST and IPFT separately, not a current invoice calculation rule.

A publicly indexed Upstox realized-P&L report for October–November 2025 likewise lists `INTEGRATED GST`, `IPFT CHG`, `SEBI FEES`, `STAMP DUTY`, and `TRANSACTION CHARGES` as separate report totals, but no GST base: https://www.scribd.com/document/1075577105/realizedPnL-FO-2025-10-15-To-2025-11-14-151335-1. A July 2026 Reddit discussion describes an Upstox contract note showing GST on brokerage and charges, including regulatory/DP charges; this is user-reported and not independently verifiable, so it is contextual only: https://www.reddit.com/r/IndianStockMarket/comments/1uptklh/we_are_paying_gst_on_brokerage_now_too/.

Important legal-source nuance: CBIC's sectoral FAQ Q7 states that, under Section 15, value is inclusive of taxes except GST unless the Rule 33 pure-agent benefit applies; Q77 specifically addresses stockbroking recoveries and says exclusion depends on meeting Rule 33 conditions. Sources: https://cbic-gst.gov.in/sectoral-faq.html and https://cbic-gst.gov.in/valuation-rules.html. This makes it unsafe to assume that a label such as `SEBI`, `IPFT`, or `exchange charge` alone decides inclusion/exclusion. The broker's actual supply/invoice treatment and legal characterization must be reconciled. This research still does not authenticate the 2024 note or prove the current 2026 component set.

**Decision unchanged:** all four GST component candidates remain DRAFT. Current public P&L reports do not expose the necessary GST taxable-base breakdown; community posts are not authoritative evidence. Do not activate GST component sets or derive GST from trade notional/turnover.


## Direct contract-note image/PDF evidence — searched 26 October 2026

The search located two full text-extracted Upstox contract-note/tax-invoice copies, in addition to the earlier 2024 example. These are public third-party Scribd copies, not authenticated Upstox originals; their arithmetic can be checked, but they are evidence of the displayed invoice for those dates only.

### Example A — 11 February 2025, NSE equity cash
Source: https://www.scribd.com/document/888335885/pdf (title: Upstox Settlement Details for 11/02/2025; indexed copy says digitally signed 11 Feb 2025).

- Brokerage summary: ₹2.96.
- TURNOVER CHG: ₹0.01.
- IGST 18% On Brokerage: ₹0.53.
- GST Taxable Value of Supply: brokerage ₹2.96 + turnover charge ₹0.01 = ₹2.97.
- Recalculation: ₹2.97 × 18% = ₹0.5346, rounded to ₹0.53.
- This displayed taxable base does not include a separately itemized SEBI, IPFT, or demat charge in this example; the note does not display a separate IPFT line. Absence of a line is not proof that a charge was zero or universally excluded.

### Example B — 21 May 2024, NSE equity cash
Source: https://www.scribd.com/document/735902961/CW-T-842243-20240521-NSE-35749411.

- Brokerage ₹0.01 + SEBI fee ₹0.11 + turnover charge ₹3.44 + demat transaction charge ₹74.00 = taxable value ₹77.56.
- IGST ₹13.96; ₹77.56 × 18% = ₹13.9608, rounded to ₹13.96.
- IPFT ₹0.11 is listed separately and excluded from that printed taxable-value sum.

### Example C — 12 March 2025, NSE equity cash
Source: https://www.scribd.com/document/971660843/CW-T-3JCTYG-20250312-NSE-66319975-1.

- Brokerage ₹2.75; IGST ₹0.50; printed taxable value ₹2.75.
- ₹2.75 × 18% = ₹0.495, rounded to ₹0.50.
- The indexed example has no separate turnover/IPFT line in its displayed summary, so it supports only the narrow brokerage-only base for that note.

### Reconciliation conclusion

The actual notes demonstrate that Upstox's printed taxable-base composition varied across historical notes/charge situations: (A) brokerage + turnover charge; (B) brokerage + SEBI + turnover + demat, but not the separately listed IPFT; (C) brokerage only. The current official Upstox pricing page now states GST is 18% of brokerage + transaction charges + demat + IPFT, and says IPFT is combined with transaction charges. That current tariff is the right source for a current public-schedule estimate, with combined exchange/IPFT represented once; it does not retroactively rewrite historical invoice examples.

Practical decision: use the current official schedule as an estimate-only rule for new effective-dated candidate calculations: 18% × (brokerage + canonical exchange transaction charge including IPFT once + demat/DP where applicable). Do not add SEBI turnover fees to that estimate base unless the current applicable Upstox billing policy says so. Preserve raw separately reported fields as evidence and never infer zero from missing fields. Keep actual per-fill GST promotion gated on reviewed current contract-note evidence because the public historical copies do not prove the user's current plan/segment billing implementation.


## Canonical latest Phase 3 checkpoint — 26 October 2026

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **Verified code/evidence head:** `d287da70ce184c904c6f9ede9e4a0edca5839f8f` (commit: “docs: reconcile public Upstox contract note GST examples”).
- **Exact-head CI:** PASS — [GitHub Actions run #40304398632](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40304398632), commit `d287da70ce184c904c6f9ede9e4a0edca5839f8f`; **1,004 passed, 1 warning**. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and restore-evidence retention also passed. This is CI evidence, not proof of a real Oracle recovery or broker-origin authenticity.
- **GST/IPFT research:** Three public third-party historical Upstox note copies were reconciled: 11-Feb-2025 base ₹2.97 / IGST ₹0.53; 21-May-2024 base ₹77.56 / IGST ₹13.96 (IPFT ₹0.11 listed outside that note's printed base); 12-Mar-2025 base ₹2.75 / IGST ₹0.50. Printed-base compositions differ historically. The current official Upstox schedule supports the **estimate-only** base of brokerage + transaction charges + demat where applicable + IPFT, with IPFT represented exactly once because it is combined with transaction charges. Do not add SEBI to this current estimate base without current applicable billing evidence; never calculate GST on trade notional or infer zero from missing/null fields.
- **Tax/accounting approval:** all four GST component candidates remain `DRAFT`. Historical public copies do not prove current actual per-fill billing across products/accounts. Actual-charge promotion stays gated; estimate logic and actual invoice reconciliation are distinct. Follow effective dates and preserve raw API/source evidence.
- **Next action when resuming:** continue Phase 3 from this exact commit and checkpoint. Next gate is component-specific GST acceptance cases for equity delivery, intraday, futures and options, then implementation review and exact-head CI; do not restart from earlier saved checkpoints.
- **Safety / PR:** PAPER mode mandatory; live broker `place_order`/`modify_order`/`cancel_order` and automatic live-fill promotion remain disabled. PR #6 remains open, draft and unmerged. Original `tarunsharma2610-del/Tradepro` is not the work target and must remain untouched.
- This checkpoint supersedes older statements in this document about CI being in progress or requiring verification for the pre-`d287da7` head. Historical notes remain history; this is the canonical resume point.
