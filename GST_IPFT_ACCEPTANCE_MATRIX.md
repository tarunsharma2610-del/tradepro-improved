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
