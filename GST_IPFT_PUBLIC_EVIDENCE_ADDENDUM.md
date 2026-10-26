

## GST/IPFT statutory-engine implementation update — 26 October 2026 (code/test CI passed; docs head must be checked)

- Added `backend/app/services/statutory_stock_broking_gst.py` and `backend/tests/test_statutory_stock_broking_gst.py` on the current Phase 3 branch. The service implements CGST Act section 15's default taxable valuation, conditional CGST Rule 33 pure-agent exclusion requiring every evidence flag, and IGST Act section 12(12) recipient-location/fallback state selection for IGST versus CGST+SGST.
- Service/test changes are in commits `dcad71e148b89a2c384631b36090008c8fad193e` and `037ad2da02dca34c399e0ec454674c50ae65b5a7`, included in the verified checkpoint head above. Exact-head Backend CI [#40375335160 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40375335160) passed on checkpoint head `cc2d591cf74daea5d68b6ba704ae87a342cc96fd`: **1,051 passed, 1 warning**. Broker-write guard, SQLite/PostgreSQL 16 migration round-trips and synthetic restore drill passed. Later documentation commits are newer and still require exact-head CI verification.
- The statutory engine is a separate primitive and is not yet wired into actual per-fill accounting. It does not infer Rule 33 pure-agent status from a charge label; absent complete evidence, third-party recovery lines remain in the section 15 base. It keeps the Upstox published-schedule estimate separate from statutory valuation and does not override the unresolved API sample discrepancy.
- Regression coverage added for combined/separate exchange/IPFT values in the taxable base, Rule 33 all-conditions gate, same-state versus cross-state tax type, recipient-state fallback, invalid/missing money, duplicate line names, and paise rounding. Intra-state CGST/SGST tax heads are rounded independently to paise and the returned total equals the two heads.
- Remaining gates: run exact-head backend CI and fix failures; independently review tax-head rounding and legal policy; implement product/broker effective-dated mapping and IPFT resolver; complete DP/demat persistence + total reconciliation; integrate only reviewed policy paths; synchronize this checkpoint again to the final CI-verified head. Actual per-fill invoice evidence remains deferred until source records/deployment exist; no personal contract note is required.
- Official source basis: [CBIC stock-broking FAQ](https://cbic-gst.gov.in/sectoral-faq.html), [CGST Act section 15](https://cbic-gst.gov.in/hindi/CGST-bill-e.html), [Upstox Brokerage Details API](https://upstox.com/developer/api-documentation/get-brokerage/), and [Upstox public charges](https://upstox.com/brokerage-charges/).
- Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; PR #6/#7 Draft and unmerged; PAPER-only; live broker writes disabled; original `Tradepro` untouched.
## Latest authoritative checkpoint — 26 October 2026, 21:06 IST

This section supersedes earlier statements in this file that identify an older commit or CI run as the latest checkpoint. Historical entries below are retained for audit history.

- **Only target repository:** [tarunsharma2610-del/tradepro-improved](https://github.com/tarunsharma2610-del/tradepro-improved). Branch: `phase3/durable-per-fill-charge-allocation`. Latest documentation commit before this sync: `73c4a7cdcde4490bd520d5e75cc87fe1b4ffa310`. Exact-head documentation CI [#40346810442 PASSED](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40346810442).
- GST estimate implementation commit `b75a97f6cd0043c185375cc253b84a1e6d6bfea1`; exact-head CI [#40345937942 PASSED](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40345937942): 1,012 tests passed, 1 warning. Broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic restore/evidence-retention checks passed.
- **GST estimate decision:** apply 18% to brokerage + combined exchange transaction/IPFT charge exactly once; include explicit demat/DP charges additionally for equity delivery. Do not add STT, stamp duty, SEBI or trade notional to this published GST estimate base. Upstox's Brokerage Details API sample arithmetic conflicts with the explicit public schedule; the sample does not override the schedule or prove live billing is wrong. Sources: [Upstox pricing](https://upstox.com/brokerage-charges/), [Brokerage Details API](https://upstox.com/developer/api-documentation/get-brokerage/), [Trades Charges API](https://upstox.com/developer/api-documentation/get-trade-charges/), [NSE transaction/IPFT circular](https://nsearchives.nseindia.com/content/circulars/FA73061.pdf).
- **New Phase 3 gap found:** `demat_transaction_charges` is intentionally blocked by source-to-canonical mapping; canonical live accounting and `Execution` currently support six components only. Equity-delivery actual-charge accounting with a DP/demat charge is therefore not accepted yet. The estimate helper can include a demat amount, but that does not mean actual accounting can persist/reconcile it. Keep this fail-closed; do not drop DP charges or fold them into another component. Next implementation gate: product-aware canonical demat/DP component and total-charge persistence, migration, idempotency, allocation, and delivery/non-delivery regression tests—or keep delivery actual accounting unsupported until complete.
- Actual per-fill GST/invoice acceptance remains evidence-gated. Public schedules and calculators support estimates, not account-specific actuals; aggregate API values and null fields are not per-fill invoice proof. User is not required to provide a personal contract note. Actual tariff candidates remain DRAFT.
- Phase 3 remains IN PROGRESS; PR #6 remains open/draft/unmerged. PAPER mandatory; live broker order writes, automatic live-fill promotion and automatic scheduling remain disabled. Original `tarunsharma2610-del/Tradepro` must not be modified. AI/Algory integrations remain deferred until Phase 3 acceptance.

---

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


## GST/IPFT reconciliation checkpoint — 26 October 2026

- Official Upstox schedule https://upstox.com/brokerage-charges/ states GST 18% on brokerage + transaction charges + IPFT, including DP/demat for equity delivery. From 1-Mar-2026, published NSE combined transaction/IPFT totals are cash ₹307/crore, equity futures ₹183/crore and equity options ₹3,553/crore on premium. Count combined rates once. NSE circular: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf.
- The official Upstox Brokerage Details API example https://upstox.com/developer/api-documentation/get-brokerage/ shows transaction ₹5.68, IPFT ₹0.17, GST ₹1.02; that GST matches 18% of ₹5.68 alone, not ₹5.85 (about ₹1.05). This remains an example/documentation conflict, not proof of a live defect.
- The Trades Charges API https://upstox.com/developer/api-documentation/get-trade-charges/ provides aggregate segment/date-range charges and may return IPFT null. Null is unknown, not zero; aggregate totals are not per-fill evidence.
- Historical public contract-note copies dated 2024/2025 are third-party and pre-current-tariff; differing printed taxable bases mean they cannot settle current actual-charge treatment. Use for layout/schema only.
- Estimate-only rule may follow current tariff with product/exchange/effective-date handling and combined transaction/IPFT counted once. Actual per-fill GST candidates for delivery, intraday, futures, options remain DRAFT pending current public invoice evidence or written Upstox clarification. No production actual-charge GST logic promoted.
- Previous exact-head CI passed on commit 996b126ff678b97441f0214ea817451ee1592203: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40341429226. Tests, broker-write boundary, SQLite/PostgreSQL 16 migrations, synthetic restore and evidence retention passed; the next documentation commit needs its own exact-head CI.
- Only tarunsharma2610-del/tradepro-improved is in scope; original Tradepro untouched. PAPER mandatory; live order writes and automatic live-fill promotion/scheduling disabled; PR #6 draft/unmerged; no personal contract note requested; AI/Algory deferred until Phase 3 acceptance.


## GST estimate implementation update — 26 October 2026

- Added backend/app/services/upstox_public_gst_estimate.py and backend/tests/test_upstox_public_gst_estimate.py: explicit public-schedule estimate-only GST path, 18%, supported scope from 1-Mar-2026, provenance fingerprint and PUBLIC_SCHEDULE_ESTIMATE_ONLY label. This does not approve actual GST component sets or promote charges.
- Component contract: delivery requires brokerage + exchange_charges + explicit demat_charges; other supported products require brokerage + exchange_charges. For NSE from 1-Mar-2026, exchange_charges is the combined transaction/IPFT total once; separate ipft key is rejected. BSE options use applicable BSE schedule and must not inherit an NSE IPFT assumption.
- Open discrepancy: Upstox Brokerage Details API example shows transaction ₹5.68, IPFT ₹0.17, GST ₹1.02; 18% of ₹5.85 is approximately ₹1.05. The helper follows public tariff wording for estimates only. Actual per-fill GST candidates remain DRAFT pending current public invoice evidence or written Upstox clarification.
- Acceptance matrix: GST_IPFT_ACCEPTANCE_MATRIX.md. Code/test head 221493eb17729533cfaf855e2ce52532ef0903ac; CI run #40342805295 was pending at note time. The next documentation commit needs its own exact-head CI.
- Safety unchanged: Tradepro Improved only, original Tradepro untouched, PAPER mandatory, live broker writes and automatic live-fill promotion/scheduling disabled, PR #6 draft/unmerged, no personal contract note requested, AI/Algory deferred.


## Authoritative GST decision — 26 October 2026

**Decision: implement the current official Upstox public-schedule GST base for estimates now; do not let the inconsistent API documentation sample block it.** Upstox's pricing page explicitly states GST at 18% on brokerage + transaction charges + IPFT, with demat charges additionally included for equity delivery. From 1-Mar-2026, NSE Circular NSE/FA/73061 defines combined transaction/IPFT outflows (cash ₹307/crore, futures ₹183/crore, options ₹3,553/crore premium); represent that as one exchange_charges component and never add IPFT twice. The supported estimate path sums brokerage + combined exchange_charges, and adds explicit demat_charges for delivery. STT, stamp duty and SEBI are not added to this published GST base.

The Brokerage Details API example showing transaction ₹5.68, IPFT ₹0.17 and GST ₹1.02 is internally inconsistent with that page: 18% × ₹5.68 = ₹1.0224 → ₹1.02; 18% × (₹5.68 + ₹0.17) = ₹1.053 → ₹1.05. Treat this as a documentation-example discrepancy, not evidence that current production billing is wrong. Public schedule takes precedence for estimates; the API example does not override it. Trades Charges API is aggregate and its ipft:null is unknown, not zero.

This resolves the public-schedule estimate rule. It does not certify account-specific invoice totals or per-fill actual GST. Keep actual accounting/promotion evidence-gated until invoice/source evidence or written broker clarification is available. A personal contract note from the user is not required. Official sources: https://upstox.com/brokerage-charges/ ; https://upstox.com/developer/api-documentation/get-brokerage/ ; https://upstox.com/developer/api-documentation/get-trade-charges/ ; https://nsearchives.nseindia.com/content/circulars/FA73061.pdf ; https://cbic-gst.gov.in/sectoral-faq.html


## Latest GST/IPFT implementation checkpoint — 26 October 2026

- Implementation + synchronized GST decision commit b75a97f6cd0043c185375cc253b84a1e6d6bfea1 passed exact-head Backend CI [#40345937942](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40345937942): 1,012 passed, 1 warning in 62.33s. Broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and evidence retention passed.
- Estimate decision: use 18% on brokerage + combined transaction/IPFT exchange charges; add explicit demat charges for equity delivery. Count IPFT once. Exclude STT, stamp duty and SEBI from the published estimate base. API example GST mismatch is a docs-example inconsistency and does not override the current Upstox schedule.
- Actual invoice/per-fill GST acceptance remains separate and evidence-gated; actual component-set candidates stay DRAFT. Do not request a personal contract note. Safety: PAPER mandatory, live order writes/promotion/scheduling disabled, PR #6 draft/unmerged, original Tradepro untouched.


## Session checkpoint sync — 26 October 2026

- Exact-head Backend CI [#40368554399 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40368554399) passed on code head `9d3f255480da9a71980a9d3819fbb69a34835753`. Documentation-only synchronization is now creating newer commits; do not treat the new documentation head as green until its own CI completes.
- Statutory GST research: CBIC stock-broking FAQ and CGST Act section 15 / CGST Rules Rule 33 and Rule 27 are the legal framework. Rule 33 pure-agent exclusion is conditional on evidence, not an automatic classification for every charge. IGST Act section 12(12) provides stock-broking place of supply; compare supplier and place-of-supply states for IGST versus CGST+SGST. Sources: https://cbic-gst.gov.in/sectoral-faq.html ; https://cbic-gst.gov.in/valuation-rules.html
- Public GST schedule helper/tests are estimate-only. A statutory valuation engine and its tests are **not yet implemented**; GST/IPFT acceptance remains open. Next: implement Section 15 inclusion, Rule 33 evidence gates, state-based tax split, Decimal/paise rounding and fail-closed handling. IPFT combined/separate representation and DP/demat persistence/reconciliation remain open.
- No personal contract note is available or required. Safety: target only `tarunsharma2610-del/tradepro-improved`; PR #6/#7 Draft/unmerged; PAPER-only; live order writes disabled; original Tradepro out of scope.
