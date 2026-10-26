# Public GST/IPFT evidence addendum — 26 October 2026

Scope: Tradepro Improved Phase 3 charge evidence. Public-source research only. No personal contract note is required from the user.

## Findings

1. **Current Upstox public tariff:** https://upstox.com/brokerage-charges/ states GST at 18% on brokerage + transaction charges + IPFT for intraday, futures and options, and includes demat/DP charges in the listed equity-delivery GST base. It also says IPFT is combined with transaction charges. For estimates effective 1 March 2026 onward, represent the exchange transaction/IPFT charge once; do not add a legacy IPFT component on top of a combined amount.
2. **Upstox Brokerage Details API documentation example:** https://upstox.com/developer/api-documentation/get-brokerage/ shows transaction ₹5.68, IPFT ₹0.17 and GST ₹1.02. ₹1.02 is approximately 18% of ₹5.68 alone, not 18% of ₹5.85. This is an inconsistency between the published example and the public tariff wording. It does not prove that live API responses are wrong or that the example reflects current production behaviour.
3. **Public Upstox contract note, 21 May 2024:** https://www.scribd.com/document/735902961/CW-T-842243-20240521-NSE-35749411 shows IGST ₹13.96 and a stated taxable supply total ₹77.56 composed of brokerage ₹0.01, SEBI fees ₹0.11, turnover charges ₹3.44 and demat transaction charges ₹74.00; IPFT ₹0.11 appears separately in the charge summary. This historical example is useful evidence of invoice presentation, but predates the March 2026 tariff changes and cannot settle current treatment.
4. **Public Upstox contract note, 12 March 2025:** https://www.scribd.com/document/971660843/CW-T-3JCTYG-20250312-NSE-66319975-1 shows GST taxable value of ₹2.75 for brokerage ₹2.75 in a small trade example. It does not resolve the current IPFT/tax-base discrepancy.
5. **General contract-note structure:** the contract note can show aggregate GST and charges, while trade-wise levy detail may be available separately on request; aggregate totals alone cannot establish per-fill GST allocation.

## Decision

- Public-schedule **estimate** may follow the explicit current Upstox tariff and count combined transaction/IPFT once, with exchange/segment/product and effective-date rules.
- Do not infer a production/API fix from the API example alone. Do not promote actual per-fill GST component candidates from public tariff pages, historical contract notes, calculators, or aggregate charges alone.
- All four actual product GST candidates remain `DRAFT`: equity delivery (including DP/demat treatment), equity intraday, futures and options.
- Remaining evidence gate: current post-1-March-2026 Upstox invoice/contract-note evidence or written Upstox clarification resolving the API example and current GST taxable base; verify relevant NSE/BSE and product differences.
- Never request the user's own contract note; continue public-source research. Synthetic examples remain test-only and must never be presented as genuine broker documents.
- Safety: PAPER mode mandatory; live broker order writes and automatic live-fill promotion/scheduling remain disabled; PR #6 stays draft/unmerged absent explicit user approval. Work only in `tarunsharma2610-del/tradepro-improved`; do not modify original `Tradepro`. Defer AI/Algory integration until Phase 3 acceptance.
