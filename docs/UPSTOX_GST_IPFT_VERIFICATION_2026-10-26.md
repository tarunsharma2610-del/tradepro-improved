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
