<!-- Phase 3 checkpoint update — 27 Oct 2026. Latest code/test head 8feeb0cbb0c35e1e37012302c9075d43f1f33eb1 passed Backend CI #40458822529: 1,097 passed, 1 warning. Broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore and evidence retention passed. DP completeness checks require a consistent KNOWN + explicit valid finite nonnegative paise-exact amount, or NOT_APPLICABLE + no amount; invalid status, UNKNOWN-with-amount, KNOWN-without-amount, NOT_APPLICABLE-with-amount, NaN, negative and fractional-paise amounts fail closed. DP canonical manifests are checked against persisted broker trade → child order → local order mappings; only mapped equity-delivery SELL fills are accepted. Delivery SELL still requires reviewed/reconciled DP evidence and durable per-fill allocation; DP is included once in total and replay identity. Maintained docs are being synchronized after the green code run; exact-head CI on the final docs/checkpoint commit must pass before it is called green. PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled; original Tradepro repository out of scope. -->

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


## Phase 3 CI synchronization — 26 October 2026 (GST/IPFT resolver)

- Latest verified code head: `13e201661d26b04c9bf75bb7e3aaf567ad1e69c4`; exact-head Backend CI [#40378072884 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40378072884): **1,056 passed, 1 warning**. Broker-write boundary, SQLite migration round-trip, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill and retained restore evidence passed.
- Added scope/effective-date-selected GST policy resolution for `COMBINED`, `SEPARATE`, and `NOT_APPLICABLE` IPFT representation. It rejects double representation, wrong-exchange reuse, missing/extra components, and unapproved or out-of-window policies. This is estimate-policy plumbing, not actual invoice reconciliation or tariff approval.
- Next Phase 3 gate: persist optional DP/demat charges safely, migrate canonical accounting/persistence and total-charge recomputation, then integrate statutory GST valuation only through reviewed source-backed policy paths. Actual per-fill invoice acceptance remains evidence-gated; no personal contract note is required.
- Safety unchanged: PR #6/#7 Draft and unmerged; PAPER mandatory; live broker order writes and automatic live-fill promotion/scheduling disabled; original `tarunsharma2610-del/Tradepro` untouched and out of scope.


## Phase 3 CI synchronization — 26 October 2026 (DP/demat snapshot gate)

- Latest verified code head: `6a6a3560aff18bb94d34b77640058a17d2a208b8`; exact-head Backend CI [#40381396722 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40381396722): **1,057 passed, 1 warning**. Broker-write boundary, SQLite and PostgreSQL 16 migration round-trips, synthetic PostgreSQL/document-volume restore drill and retained restore evidence passed.
- Optional `demat_transaction_charges` can now be represented as a distinct pending canonical snapshot and allocated into the durable per-fill allocation ledger when source rows are independently reviewed. Migration expands the canonical snapshot vocabulary. It does **not** authorize final accounting: DP/demat reconciliation promotion deliberately fails closed until Execution persistence and total-charge recomputation are implemented.
- Next Phase 3 gate: add dedicated optional Execution DP/demat persistence and a single verified total-charge recomputation path, with migration/idempotency/rollback and delivery-vs-non-delivery tests. Keep actual invoice/per-fill acceptance evidence-gated; no personal contract note is required.
- Safety unchanged: PR #6/#7 Draft and unmerged; PAPER mandatory; live broker order writes and automatic live-fill promotion/scheduling disabled; original `tarunsharma2610-del/Tradepro` untouched and out of scope.

## Verified checkpoint — 27 October 2026 (DP/demat completeness)

- Exact-head Backend CI #40459846143 passed on code/test commit `9400bc9aa221e2cf3b735e49a8e9a6d351237f02`: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40459846143. Backend pytest, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips and synthetic PostgreSQL/document-volume restore checks passed.
- DP completeness regression is verified: invalid status cannot yield a complete total; `KNOWN` needs valid paise-exact amount; `NOT_APPLICABLE` needs no amount; unknown/inconsistent states fail closed. This checkpoint does not approve statutory tariff or invoice-level GST/IPFT composition.
- Next gate: per-fill source mapping, replay/idempotency conflicts, atomic rollback and component applicability. Actual contract-note and production Oracle backup/restore acceptance remain evidence-gated.
- Safety: PAPER mandatory, live broker writes disabled, PR #6/#7 Draft/unmerged; original `Tradepro` repo out of scope.

## Public-source review — 27 October 2026 (GST valuation and NSE IPFT)

- CBIC's stock-broking FAQ says CGST Act section 15 generally includes statutory taxes/levies, SEBI fees and stamp duty in the GST value, except where pure-agent treatment under Rule 33 is valid: https://cbic-gst.gov.in/sectoral-faq.html
- Section 15 statutory text: https://cbic-gst.gov.in/hindi/CGST-bill-e.html ; Rule 33 conditions: https://cbic-gst.gov.in/valuation-rules.html . Rule 33 must be evidence-driven and cannot be assumed merely because a charge is described as a reimbursement.
- NSE Finance & Accounts circular NSE/FA/73061 dated 27 February 2026 states revised member outflow effective 1 March 2026 for cash, equity futures and equity options, with a separately stated tiny IPFT contribution (₹0.01 per crore) and corresponding transaction-charge change: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf . This is an exchange/member schedule, not sufficient by itself to prove every broker's client invoice representation or every exchange/segment tariff.
- Zerodha's public IPFT explanation says NSE IPFT is included under exchange transaction charges in its contract note and lists separate segment rates, including currency segments: https://support.zerodha.com/category/account-opening/resident-individual/ri-charges/articles/ipft-charges . Treat this as corroboration for one broker's representation, not a universal broker rule. The code must map exchange + segment + trade date + source-field identity and reject duplicate transaction/IPFT mapping.
- GST line normalizer commit `57730a21da77fa583fe19c12740bd03eb779fed6` passed Backend CI [#40462246316](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40462246316); regression tests commit `4290b46e55275e4a005b3661da327adc1b216028` passed [#40462263615](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40462263615). Normalization accepts IGST or paired CGST+SGST and rejects mixed/incomplete/invalid lines; it does not decide rate, jurisdiction, taxable base, or source authenticity.
- Remaining acceptance: effective-dated, independently reviewed statutory rates and state/jurisdiction inputs; authoritative broker/exchange/segment IPFT mapping; prove no double-counting across transaction charge/IPFT source rows; maintain estimate versus actual invoice reconciliation as separate modes. Until reviewed rule rows are approved, estimate paths must remain labelled estimates and actual accounting fail closed.

## Newly identified GST-base conflict requiring policy resolution — 27 October 2026

- Cross-source comparison found a material discrepancy: the CBIC stock-broking FAQ says Section 15 value includes all taxes except GST unless Rule 33 pure-agent treatment applies, and explicitly discusses SEBI fees and stamp duty. Zerodha's public schedule states GST on brokerage + SEBI charges + transaction charges, while Upstox's published schedule describes GST on brokerage + transaction charges + demat (delivery only) + IPFT and does not list SEBI charges in that base.
- Sources: CBIC FAQ https://cbic-gst.gov.in/sectoral-faq.html (Levy Q7); Zerodha https://zerodha.com/charges/; Upstox https://upstox.com/brokerage-charges/ . The Upstox public schedule also lists GST/IPFT composition, while its charge API schema exposes separate GST, STT, stamp duty, transaction, IPFT, SEBI turnover and demat fields: https://upstox.com/developer/api-documentation/get-trade-charges/ . The API schema describes fields but is not proof that a particular endpoint supplies final per-fill actual values.
- Existing `upstox_gst_component_set_candidates()` remains DRAFT and currently lists brokerage + exchange charges (plus demat for equity delivery), not SEBI turnover charges. Do NOT approve or silently broaden this candidate based on inference. Legal interpretation of Section 15/Rule 33, actual broker invoice treatment and the source schedule discrepancy require independent review and a documented effective-dated decision.
- Safe implementation rule: retain source-backed estimates as broker-specific; do not assume the Upstox public schedule or Zerodha's GST base is universal. Until the discrepancy is resolved by reviewed policy, actual accounting must use reviewed source invoice/tax totals and fail closed for automated tax-base reconstruction when the needed evidence is absent.


## Cross-broker source comparison — 27 October 2026 (public-source findings)

Fresh public-page comparison reinforces that GST taxable-base membership is broker-specific in published schedules and must not be generalized:

- **CBIC:** stock-broking FAQ Q77 says STT, stamp duty and other central/state tax recoveries are outside GST value only while Rule 33 pure-agent conditions are satisfied; otherwise valuation follows Section 15 read with Rule 27. https://cbic-gst.gov.in/sectoral-faq.html
- **Zerodha:** current charges page explicitly states 18% GST on brokerage + SEBI charges + transaction charges; IPFT is described separately by segment. https://zerodha.com/charges/
- **Dhan:** current pricing page states 18% GST on brokerage + transaction charges + SEBI turnover + IPFT/other tax. https://dhan.co/pricing/
- **FYERS:** current charges page states brokerage + exchange transaction charges + clearing charges + SEBI turnover fee + NSE IPFT, while a separate FYERS support article describes GST on brokerage and transaction charges and says it is not applied to SEBI fees, STT/CTT or stamp duty. These are conflicting public descriptions and must be versioned/reviewed rather than silently reconciled. https://fyers.in/charges-list ; https://support.fyers.in/portal/en/kb/articles/what-are-the-statutory-charges-on-trades-at-fyers-stt-gst-sebi-turnover-fee-ipft-etc
- **Upstox:** pricing page describes brokerage + transaction charges + IPFT, with DP/demat additionally for equity delivery; the Brokerage Details API example remains arithmetically inconsistent with that wording. https://upstox.com/brokerage-charges/ ; https://upstox.com/developer/api-documentation/get-brokerage/
- **Angel One:** its public table lists transaction charges, IPFT, GST, SEBI and stamp duty, but the table alone does not specify enough detail to infer every taxable-base member. https://www.angelone.in/exchange-transaction-charges

### Engineering conclusion

1. Do not hard-code one universal GST base across brokers. Store broker, exchange, segment/product, effective interval, source URL/version, reviewer, and explicit included/excluded component identities.
2. Track charge identity separately from how the source presents it. Combined transaction/IPFT and separate transaction/IPFT representations must normalize to one canonical economic charge exactly once, using effective-dated exchange and broker evidence.
3. Rule 33 is a conditional evidence-based exclusion, not a label-based rule. If pure-agent conditions cannot be established, do not automatically exclude statutory recoveries from the taxable base.
4. Conflicting sources (demonstrated by FYERS public pages) require explicit source-precedence review and an unresolved status until adjudicated. Never choose the lower GST result merely because it matches a sample or estimate.
5. This research supports implementation of a reviewed policy resolver and regression tests; it does **not** approve any actual per-fill GST component candidate or prove a broker's account-specific invoice. Keep estimates clearly labelled and actual accounting fail-closed until the relevant source-backed policy/evidence is reviewed.


## GST policy resolver hardening — 27 October 2026

- Audited existing `backend/app/services/broker_gst_component_policy.py` before changing it. It already provides effective-dated broker/exchange/segment/product selection, source URL/retrieval date/SHA-256 provenance, explicit combined/separate/not-applicable IPFT representation, exact component-set checking and an estimate-only calculation path. Avoid creating a parallel resolver.
- New code commit `eef5eebc1e1abfc37c92b4e50d5c35e9afddcbb4`: policy state `CONFLICT` now exists and any effective conflict for the exact scope/date blocks selection even if an approved policy also matches. This prevents silently preferring one of contradictory public sources.
- New test commit `761637aab1d5f36ed5bfc02ffb66ce8b31ab7820`: regression tests for a conflicting source blocking an approved candidate and for rejecting sub-paise component inputs rather than silently rounding them.
- The policy remains estimate-only. This does not approve any broker component set, does not integrate the statutory Rule 33 engine into actual accounting, and does not reconcile invoice-level GST. No broker policies are promoted to APPROVED by this change.
- Validation status: exact-head CI for these commits is not yet verified. Do not mark this increment green until the branch/PR workflow runs on the exact resulting head and all jobs pass. Next: inspect any CI result, fix failures, then synchronize maintained documents/checkpoint to the latest green head.


## Verified GST resolver hardening CI — 27 October 2026

- Service hardening commit `eef5eebc1e1abfc37c92b4e50d5c35e9afddcbb4` passed Backend CI [#40463452758](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463452758).
- Regression-test commit `761637aab1d5f36ed5bfc02ffb66ce8b31ab7820` passed Backend CI [#40463464076](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463464076). New coverage confirms an effective `CONFLICT` policy blocks selection despite an approved candidate, and sub-paise input is rejected.
- Documentation head `d604be9982dc9c37d3a4985abd89c85635b59106` passed Backend CI [#40463512765](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463512765). A newer checkpoint-only commit is pending its own exact-head CI; do not mark the latest branch head green until that run passes.
- The resolver is still estimate-only. No GST candidate or broker tariff has been promoted to approved actual accounting. PR #6/#7 remain Draft/unmerged, PAPER mandatory, live broker order writes disabled, original Tradepro repository out of scope.


## Confirmed statutory GST precision CI and resume point — 27 October 2026

- The initial code-only run for `58c841cb00f7f0137aece7bcd7c83d5a63ae81f9` failed because an older test still expected silent rounding of `0.025`. This was a test expectation conflict with the new fail-closed behavior, not an unresolved runtime regression in the final increment.
- Regression-test commit `c6e9dfb3e4cae6f93fd51a7f1f1facc86e7b804d` passed Backend CI [#40463868838 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463868838). It replaces the obsolete sub-paise rounding expectation with explicit rejection and a valid paise-precision test.
- Checkpoint commit `74015a285cb844a3735052d88cce9c2a2385e1ce` passed Backend CI [#40463883785 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463883785). This verifies the resulting head including the GST precision change, updated regression test and checkpoint document.
- Intermediate failed run: [#40463856382](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40463856382); it was superseded by the successful regression and checkpoint runs above. Do not erase the failure from history; document the correction.
- Current implementation boundaries: statutory GST primitive applies Section 15 default inclusion and conditional Rule 33 pure-agent exclusion only when all modeled evidence flags are true; broker GST policy resolver remains an estimate-only source-specific path. Neither is yet a unified actual per-fill invoice acceptance path. No broker GST policy is approved here for actual accounting.
- Next Phase 3 task: audit the accounting charge reconciliation/promotion boundary and define a single reviewed path that consumes source-backed invoice line identities, statutory valuation evidence and effective-dated broker policy without letting estimates become actual ledger charges. If source provenance, Rule 33 facts, component identity, or GST invoice lines are missing/conflicting, actual accounting must fail closed. Add tests before integration; do not promote estimates or change live-trading safeguards.
- Safety unchanged: work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is out of scope; PR #6/#7 Draft/unmerged; PAPER mode mandatory; live broker order writes disabled.
