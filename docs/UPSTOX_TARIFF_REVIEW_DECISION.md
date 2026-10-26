## Authoritative Phase 3 checkpoint — 26 October 2026 (latest verified CI)

- Target repository only: `tarunsharma2610-del/tradepro-improved`; branch `phase3/durable-per-fill-charge-allocation`; implementation/test head `44830ec48b50b4f470ec9ca95dd2d3f4339dd3df`. Do not modify original `Tradepro`.
- Exact-head Backend CI: [run #40294178677 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40294178677), including the test separating NSE/IPFT arithmetic reconciliation from GST taxable-base approval.
- GST estimate helper accepts exactly 18%; tests reject 0%, 5%, 100%, and 100.01%. Rate guard does not approve taxable-base composition; component inclusion needs reviewer and invoice/source evidence.
- ₹307/crore versus ₹306.99/crore transaction charge + ₹0.01/crore IPFT is arithmetic reconciliation only, not GST-base approval.
- Canonical live-fill integration is verified: six independently verified charge snapshots, evidence revalidated under lock, no raw-only fallback; brokerage cap applied once before deterministic paise-exact allocation.
- Remaining Phase 3 gates: effective-dated tariff applicability; component-specific per-fill allocation acceptance; invoice/source-backed GST/IPFT and product/segment evidence; adversarial/migration/recovery review; final exact-head docs/sign-off.
- Upstox public schedules/calculator are estimates; aggregate charges endpoint is not actual per-fill evidence. Null remains unknown, not zero. Synthetic restore is not actual Oracle recovery.
- PAPER mandatory; live broker writes, automatic live-fill promotion and automatic scheduling disabled. PR #6 open/draft/unmerged unless explicitly approved. Defer AI/open-source adaptations until Phase 3 acceptance. Documentation commit needs its own CI.

---

# Upstox public tariff review decision — 26 October 2026

## Decision

**Approve a narrow set of 18 effective-dated rules for public-schedule estimates only. Do not approve them as actual-charge evidence or as account-specific tariff rules.** The underlying candidate registry remains DRAFT; a separate explicit allowlist produces APPROVED copies only when every reviewed identity, source hash, retrieval date and source URL still matches.

## Evidence reviewed

- Official Upstox brokerage/charges page: https://upstox.com/brokerage-charges/
- Official NSE STT schedule: https://www.nseindia.com/static/products-services/equity-derivatives-securities-transaction-tax
- NSE Finance & Accounts Circular NSE/FA/73061 dated 27 February 2026, effective 1 March 2026: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf
- Repository excerpt snapshot: `docs/source_snapshots/UPSTOX_CHARGES_2026-10-24.md`
- Canonical source-payload SHA-256: `c59f7e940fde6b0d94ca1189766f16e5601c117d4a8c2bcd2415da0ecd6db420`

The NSE circular confirms combined outflow of ₹307/crore for cash, ₹183/crore for equity futures and ₹3,553/crore for equity options from 1 March 2026. The revised split is transaction charge plus ₹0.01/crore IPFT; do not add legacy ₹10/₹50-per-crore IPFT rates on top. Upstox's public page records the 1 April 2026 STT changes: futures sell-side 0.05%, options sell-side premium 0.15%, and exercised options 0.15% on intrinsic value on the purchaser side. Earlier effective windows remain separately represented.

## Approved estimate-only scope

The allowlist in `backend/app/services/upstox_public_estimate_rules.py` approves exactly 18 STT and exchange-charge identities, including their effective dates and source hash. `build_upstox_public_schedule_estimate_snapshot` labels outputs `PUBLIC_SCHEDULE_ESTIMATE_ONLY`. Rules use exact scope and effective dates; there are no wildcard fallbacks. The source candidate registry stays DRAFT and changed identities fail closed until review updates the allowlist and tests.

## Explicitly not approved

- Account-specific brokerage plan, API-order discounts or future brokerage changes without a supported effective date.
- GST taxable-base composition by product/invoice, stamp duty, SEBI turnover, DP/demat, clearing/other charges, and charge-component attribution.
- BSE cash scrip-group rates, BSE futures zero-charge assumptions, MCX commodities and currency derivatives.
- Any conversion of a brokerage calculator result or aggregate charge API response into per-fill actual evidence.
- Automatic quantity/notional allocation, guessed zero values, or live-order enablement.

The current public Upstox calculator page can display older STT/transaction values than the current official charges page and the NSE circular. Use it only as an estimate cross-check, not as the effective-dated tariff source of record.

## Actual-charge boundary

Actual per-fill accounting remains exclusively based on a reviewed contract-note evidence record, independently reviewed source components, canonical mapping snapshots, exact fill manifests/weights, and durable reconciled allocations. This estimate registry is not imported by `LiveFillAccountingService` and cannot promote charges.

## Re-review triggers

Re-review if the official pricing page changes, the source payload hash changes, a new product/segment is added, an effective date is revised, a BSE scrip group or MCX/currency rule is proposed, or the account's pricing plan is known to differ from the public schedule.


## Authoritative checkpoint — 26 October 2026 (documentation CI verified)

- Repository: `tarunsharma2610-del/tradepro-improved`; branch: `phase3/durable-per-fill-charge-allocation`.
- Latest implementation commit: `ac7d27f2c9922925483b5b906c484c0d5a4e3f53`; exact-head Backend CI [#40287765745 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40287765745).
- Documentation synchronization commit: `f90573d653c7103bf9cfdb1f867da97b176d3240`; its exact-head Backend CI [#40289107666 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40289107666). Backend tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore/evidence retention passed. Synthetic restore is not proof of actual Oracle Cloud recovery.
- Approved public Upstox STT/exchange rules are estimate-only. Account-specific actual charges, GST taxable-base composition, stamp duty, SEBI/DP/demat/other charges, unsupported exchange/segment mappings, and per-fill actual evidence remain unapproved. Candidate tariff entries remain DRAFT unless separately allowlisted and reviewed.
- Phase 3 remains in progress. Next gates: independently reviewed tariff applicability; component-specific per-fill allocation rules; invoice/source-backed GST/IPFT and product/segment evidence; final adversarial, migration and recovery review; exact-head acceptance sign-off. Do not repeat canonical live-fill integration.
- Safety: PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. PR #6 stays open/draft/unmerged without explicit user approval. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.
- This documentation commit’s CI is green. Continue only from this checkpoint and verify CI for every subsequent implementation/checkpoint commit. Historical entries do not supersede this checkpoint.


## GST/IPFT focused re-review — 26 October 2026

New evidence record: [UPSTOX_GST_IPFT_VERIFICATION_2026-10-26.md](UPSTOX_GST_IPFT_VERIFICATION_2026-10-26.md). Result: keep all four GST component sets DRAFT. Upstox currently publishes 18% and says GST base is brokerage + transaction charges + IPFT (plus demat for delivery); newer NSE combined transaction/IPFT rates effective 1 March 2026 are ₹307/crore cash, ₹183/crore futures, and ₹3,553/crore options premium, including ₹0.01/crore IPFT. Do not add a separate IPFT amount to those combined rates. CBIC confirms stock-broking service brokerage is taxable and pure-agent exclusion for STT/stamp duty recoveries depends on Rule 33 conditions. Public historical contract notes are not authenticated/current enough to resolve present product-specific GST composition. No production GST candidate is approved by this research update. Public estimates remain separate from actual-charge/per-fill accounting.


## Blocking discrepancy discovered in public historical note — 26 October 2026

The public 21 May 2024 Upstox-style contract note reports taxable value ₹77.56 from brokerage ₹0.01 + SEBI ₹0.11 + turnover charges ₹3.44 + demat ₹74.00; IGST ₹13.96; IPFT ₹0.11 is shown separately and excluded from that displayed base. Current Upstox public pricing instead lists IPFT in the GST base and does not list SEBI there. The public copy is unauthenticated and historical, so it does not establish current treatment—but the mismatch blocks approval. Keep all GST component-set candidates DRAFT; do not resolve by guessing. See [evidence review](UPSTOX_GST_IPFT_VERIFICATION_2026-10-26.md).


## CI regression follow-up — 26 October 2026

Backend CI run [#40302129087](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40302129087) failed with 1,002 passed and one failed assertion: the test expected an exact wording variant that was not present in the evidence document. The source text already said the historical note was materially different from the current Upstox public pricing page. The assertion was corrected in `f792627fb0ead15551e2506731b183e9b91482bb`. Wait for and verify CI on the new head; do not record green until confirmed. GST component sets remain DRAFT, and no legal/tax conclusion is inferred from this test-only fix.


## Additional public evidence and GST legal-source nuance — 26 October 2026

Publicly indexed FY 2025–26 Upstox realized-P&L reports list aggregate `INTEGRATED GST` and `IPFT CHG` totals separately but do not provide a GST taxable-value composition. An October–November 2025 F&O report similarly lists GST, IPFT, SEBI, stamp duty and transaction charges as aggregate totals. These third-party copies are not authenticated and cannot establish a per-trade taxable base. A July 2026 Reddit report describing GST on brokerage and charges is anecdotal only. See the evidence review for exact links and limitations.

CBIC FAQ Q7 and Q77 together caution against a simplistic universal exclusion: taxes are generally included in value under Section 15 unless Rule 33 pure-agent conditions apply, and stockbroking recovery exclusion depends on those conditions. The label of a fee alone is not enough to decide GST-base treatment. No new authoritative/current source resolved the Upstox tariff-versus-historical-note discrepancy. All four GST component sets remain DRAFT.


## Follow-up correction to brittle evidence assertion — 26 October 2026

The first wording-only assertion adjustment still failed because the exact phrase in the evidence document is split by Markdown emphasis (`**materially different**`). Updated the regression test to assert the stable semantic phrase `materially different` rather than formatting-sensitive exact markup. This is a test-only wording fix; the evidence finding and all GST candidate DRAFT statuses are unchanged. The current exact-head CI run must pass before the checkpoint is accepted.


## Contract-note examples found by image/PDF search — 26 October 2026

Three indexed Upstox contract-note copies were inspected: 11-Feb-2025 (https://www.scribd.com/document/888335885/pdf), 21-May-2024 (https://www.scribd.com/document/735902961/CW-T-842243-20240521-NSE-35749411), and 12-Mar-2025 (https://www.scribd.com/document/971660843/CW-T-3JCTYG-20250312-NSE-66319975-1). Their displayed GST bases are respectively ₹2.97 = brokerage ₹2.96 + turnover ₹0.01; ₹77.56 = brokerage ₹0.01 + SEBI ₹0.11 + turnover ₹3.44 + demat ₹74; and brokerage ₹2.75 alone. Corresponding GST arithmetic rounds correctly to ₹0.53, ₹13.96, and ₹0.50. The 2024 note lists IPFT ₹0.11 separately outside its printed base. These are historical third-party copies and not authenticated current invoices; absence of a charge line is not proof of zero or universal exclusion.

The current official Upstox tariff explicitly says 18% on brokerage + transaction charges + demat + IPFT and says IPFT is combined with transaction charges. Therefore, for current estimate-only candidate calculations, canonicalize the combined transaction/IPFT amount once and add demat/DP only for delivery where applicable; do not add SEBI turnover fees to that estimate base absent a current applicable billing rule. Keep actual-charge/per-fill GST promotion gated until reviewed current invoice evidence validates current segment/account behavior. This resolves the implementation direction for public estimates without pretending historical notes establish current actual billing.


## Canonical latest Phase 3 checkpoint — 26 October 2026

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **Verified code/evidence head:** `d287da70ce184c904c6f9ede9e4a0edca5839f8f` (commit: “docs: reconcile public Upstox contract note GST examples”).
- **Exact-head CI:** PASS — [GitHub Actions run #40304398632](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40304398632), commit `d287da70ce184c904c6f9ede9e4a0edca5839f8f`; **1,004 passed, 1 warning**. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and restore-evidence retention also passed. This is CI evidence, not proof of a real Oracle recovery or broker-origin authenticity.
- **GST/IPFT research:** Three public third-party historical Upstox note copies were reconciled: 11-Feb-2025 base ₹2.97 / IGST ₹0.53; 21-May-2024 base ₹77.56 / IGST ₹13.96 (IPFT ₹0.11 listed outside that note's printed base); 12-Mar-2025 base ₹2.75 / IGST ₹0.50. Printed-base compositions differ historically. The current official Upstox schedule supports the **estimate-only** base of brokerage + transaction charges + demat where applicable + IPFT, with IPFT represented exactly once because it is combined with transaction charges. Do not add SEBI to this current estimate base without current applicable billing evidence; never calculate GST on trade notional or infer zero from missing/null fields.
- **Tax/accounting approval:** all four GST component candidates remain `DRAFT`. Historical public copies do not prove current actual per-fill billing across products/accounts. Actual-charge promotion stays gated; estimate logic and actual invoice reconciliation are distinct. Follow effective dates and preserve raw API/source evidence.
- **Next action when resuming:** continue Phase 3 from this exact commit and checkpoint. Next gate is component-specific GST acceptance cases for equity delivery, intraday, futures and options, then implementation review and exact-head CI; do not restart from earlier saved checkpoints.
- **Safety / PR:** PAPER mode mandatory; live broker `place_order`/`modify_order`/`cancel_order` and automatic live-fill promotion remain disabled. PR #6 remains open, draft and unmerged. Original `tarunsharma2610-del/Tradepro` is not the work target and must remain untouched.
- This checkpoint supersedes older statements in this document about CI being in progress or requiring verification for the pre-`d287da7` head. Historical notes remain history; this is the canonical resume point.
