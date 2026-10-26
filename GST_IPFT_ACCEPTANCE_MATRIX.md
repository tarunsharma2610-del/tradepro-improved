# GST/IPFT acceptance matrix — estimate vs actual evidence

Updated 26 October 2026. This matrix separates estimate calculations from actual per-fill invoice reconciliation.

## Scenarios and acceptance criteria

| Scenario | Estimate acceptance | Actual-charge acceptance |
|---|---|---|
| NSE equity delivery, tariff boundary 1-Mar-2026 | Effective-dated cash rate; combined transaction/IPFT once; GST estimate base per Upstox schedule includes brokerage, transaction/IPFT and DP/demat where applicable. Do not apply DP per fill indiscriminately. | DRAFT pending current invoice or written broker clarification; DP is typically sell-side per scrip/day. |
| NSE equity intraday, boundary 1-Mar-2026 | Effective-dated cash rate; combined transaction/IPFT once. | DRAFT; resolve API sample mismatch first. |
| NSE equity futures, boundary 1-Mar-2026 | Current total ₹183/crore; don't add IPFT separately. | DRAFT; current invoice/base evidence needed. |
| NSE equity options, boundary 1-Mar-2026 | Current total ₹3,553/crore on premium; don't add IPFT separately. | DRAFT; current invoice/base evidence needed. |
| BSE products | Use current BSE/scrip-group/product-specific schedule, never substitute NSE rate. | DRAFT until applicable schedule and tax base sourced. |
| API example: transaction ₹5.68, IPFT ₹0.17, GST ₹1.02 | Flag discrepancy: 18% × ₹5.68 = ₹1.0224 (₹1.02); 18% × ₹5.85 = ₹1.053 (about ₹1.05). No silent choice for actuals. | Block promotion until Upstox clarifies current billing/API semantics. |
| Aggregate API IPFT null | Treat null as unknown, not zero. | Cannot satisfy per-fill evidence gate. |
| Historical public contract-note copy | Layout/historical comparison only. | Cannot prove current per-fill tax composition. |
| Rounding/allocation | Deterministic paise rounding and tariff/source fingerprint. | Reviewed component provenance, exact eligible-fill set, approved method/basis, and paise-exact source-total reconciliation required; fail closed on mismatch. |

## Gate to promote DRAFT GST candidates

1. Current public evidence after 1-Mar-2026 or written Upstox clarification resolves GST/IPFT base when API fields are separate.
2. Confirm delivery (including DP/demat), intraday, futures, options and relevant NSE/BSE/MCX product-specific treatment.
3. Add cited expected-value fixtures for tariff boundaries and verified invoice component breakdown only after source evidence is sufficient.
4. Tests prove null is not zero, combined transaction/IPFT is not double-counted, GST is not applied to trade notional, and STT/stamp duty/SEBI are not included without explicit source support.
5. Actual allocations must reconcile exactly to reviewed source totals; synthetic examples must be labelled test-only and never represented as genuine broker documents.

Current disposition: no actual-charge GST logic is approved by this matrix. PAPER mandatory; live order writes and automatic live-fill promotion/scheduling disabled; PR #6 remains draft/unmerged.


## Public-schedule GST estimate implementation — 26 October 2026

The estimate-only path is implemented in backend/app/services/upstox_public_gst_estimate.py with regression tests in backend/tests/test_upstox_public_gst_estimate.py. It requires explicit source components, uses 18%, labels results PUBLIC_SCHEDULE_ESTIMATE_ONLY, and is scoped to reviewed NSE/BSE product combinations from 1-Mar-2026. Delivery includes explicit demat_charges; all supported products include brokerage + exchange_charges; NSE exchange_charges already includes transaction/IPFT once. A separate ipft input is rejected to prevent double counting. BSE options must use the applicable BSE schedule and must not inherit NSE IPFT assumptions.

This does not resolve actual billing: the Upstox Brokerage Details API example (transaction ₹5.68, IPFT ₹0.17, GST ₹1.02) conflicts with the tariff base wording because 18% of ₹5.85 rounds to about ₹1.05. Public estimate calculation follows published tariff wording only; actual per-fill GST candidates remain DRAFT. CI for code/test head 221493eb17729533cfaf855e2ce52532ef0903ac was pending at note time. Final exact-head CI is required before accepting this update.


## Authoritative GST decision — 26 October 2026

**Decision: implement the current official Upstox public-schedule GST base for estimates now; do not let the inconsistent API documentation sample block it.** Upstox's pricing page explicitly states GST at 18% on brokerage + transaction charges + IPFT, with demat charges additionally included for equity delivery. From 1-Mar-2026, NSE Circular NSE/FA/73061 defines combined transaction/IPFT outflows (cash ₹307/crore, futures ₹183/crore, options ₹3,553/crore premium); represent that as one exchange_charges component and never add IPFT twice. The supported estimate path therefore sums brokerage + combined exchange_charges, and adds explicit demat_charges for delivery. STT, stamp duty and SEBI are not added to this published GST base.

The Brokerage Details API example showing transaction ₹5.68, IPFT ₹0.17 and GST ₹1.02 is internally inconsistent with that page: 18% × ₹5.68 = ₹1.0224 → ₹1.02; 18% × (₹5.68 + ₹0.17) = ₹1.053 → ₹1.05. Treat this as a documentation-example discrepancy, not evidence that current production billing is wrong. Public schedule takes precedence for the estimate path; the API example does not override it. Trades Charges API is aggregate and its ipft:null is unknown, not zero.

This resolves the public-schedule estimate rule. It does not certify account-specific invoice totals or per-fill actual GST. Keep actual accounting/promotion evidence-gated until invoice/source evidence or written broker clarification is available. A personal contract note from the user is not required. Official sources: https://upstox.com/brokerage-charges/ ; https://upstox.com/developer/api-documentation/get-brokerage/ ; https://upstox.com/developer/api-documentation/get-trade-charges/ ; https://nsearchives.nseindia.com/content/circulars/FA73061.pdf ; https://cbic-gst.gov.in/sectoral-faq.html
