## Latest authoritative checkpoint — 26 October 2026, 21:06 IST

This section supersedes earlier statements in this file that identify an older commit or CI run as the latest checkpoint. Historical entries below are retained for audit history.

- **Only target repository:** [tarunsharma2610-del/tradepro-improved](https://github.com/tarunsharma2610-del/tradepro-improved). Branch: `phase3/durable-per-fill-charge-allocation`. Latest documentation commit before this sync: `73c4a7cdcde4490bd520d5e75cc87fe1b4ffa310`. Exact-head documentation CI [#40346810442 PASSED](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40346810442).
- GST estimate implementation commit `b75a97f6cd0043c185375cc253b84a1e6d6bfea1`; exact-head CI [#40345937942 PASSED](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40345937942): 1,012 tests passed, 1 warning. Broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore/evidence-retention checks passed.
- **GST estimate decision:** apply 18% to brokerage + combined exchange transaction/IPFT charge exactly once; include explicit demat/DP charges additionally for equity delivery. Do not add STT, stamp duty, SEBI or trade notional to this published GST estimate base. Upstox's Brokerage Details API sample arithmetic conflicts with the explicit public schedule; the sample does not override the schedule or prove live billing is wrong. Sources: [Upstox pricing](https://upstox.com/brokerage-charges/), [Brokerage Details API](https://upstox.com/developer/api-documentation/get-brokerage/), [Trades Charges API](https://upstox.com/developer/api-documentation/get-trade-charges/), [NSE transaction/IPFT circular](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf).
- **New Phase 3 gap found:** `demat_transaction_charges` is intentionally blocked by source-to-canonical mapping; canonical live accounting and `Execution` currently support six components only. Equity-delivery actual-charge accounting with a DP/demat charge is therefore not accepted yet. The estimate helper can include a demat amount, but that does not mean actual accounting can persist/reconcile it. Keep this fail-closed; do not drop DP charges or fold them into another component. Next implementation gate: product-aware canonical demat/DP component and total-charge persistence, migration, idempotency, allocation, and delivery/non-delivery regression tests—or keep delivery actual accounting unsupported until complete.
- Actual per-fill GST/invoice acceptance remains evidence-gated. Public schedules and calculators support estimates, not account-specific actuals; aggregate API values and null fields are not per-fill invoice proof. User is not required to provide a personal contract note. Actual tariff candidates remain DRAFT.
- Phase 3 remains IN PROGRESS; PR #6 remains open/draft/unmerged. PAPER mandatory; live broker order writes, automatic live-fill promotion and automatic scheduling remain disabled. Original `tarunsharma2610-del/Tradepro` must not be modified. AI/Algory integrations remain deferred until Phase 3 acceptance.

---

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


## Latest GST/IPFT implementation checkpoint — 26 October 2026

- Implementation + synchronized GST decision commit b75a97f6cd0043c185375cc253b84a1e6d6bfea1 passed exact-head Backend CI [#40345937942](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40345937942): 1,012 passed, 1 warning in 62.33s. Broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and evidence retention passed.
- Estimate decision: use 18% on brokerage + combined transaction/IPFT exchange charges; add explicit demat charges for equity delivery. Count IPFT once. Exclude STT, stamp duty and SEBI from the published estimate base. API example GST mismatch is a docs-example inconsistency and does not override the current Upstox schedule.
- Actual invoice/per-fill GST acceptance remains separate and evidence-gated; actual component-set candidates stay DRAFT. Do not request a personal contract note. Safety: PAPER mandatory, live order writes/promotion/scheduling disabled, PR #6 draft/unmerged, original Tradepro untouched.
