# GST Cross-Exchange Coverage Matrix

Updated: 27 October 2026

## Design decision

NSE, BSE and MCX use one statutory GST valuation/tax-split engine. The engine
does not own exchange tariff rates. An upstream, effective-dated tariff/source
layer must determine each actual fee, the component's applicability, its basis,
and whether that amount belongs in the GST taxable value. Never reuse one
exchange's transaction-charge or IPFT rate as another exchange's rate.

The statutory engine uses the Section 15 default valuation, allows a Rule 33
pure-agent exclusion only when all required evidence flags are satisfied, and
splits IGST versus CGST+SGST from explicit supplier and place-of-supply state
codes. The output is a calculation result, not evidence that the source inputs
or a broker invoice were correct.

## Automated shared-engine coverage

`backend/tests/test_cross_exchange_gst_engine.py` exercises the same GST
engine across these synthetic product scopes and both intra-state/inter-state
tax modes:

| Exchange | Segments/products in test matrix |
|---|---|
| NSE | Equity delivery, equity intraday, equity F&O futures, equity F&O options |
| BSE | Equity delivery, equity intraday, equity F&O futures, equity F&O options |
| MCX | Commodity futures, commodity options |

The amounts in this test are deliberately synthetic. They prove that the same
tax engine and tax split work across product contexts; they are not exchange
tariff fixtures and do not prove tariff completeness. Rule 33 evidence behavior
is also tested independently of exchange.

## Official source register to maintain

- CBIC Sectoral FAQs, stock-broking questions 77–78: Section 15 treatment of
  statutory recoveries and brokerage GST: https://cbic-gst.gov.in/sectoral-faq.html
- CBIC Valuation Rules, Rule 33 pure-agent conditions:
  https://cbic-gst.gov.in/valuation-rules.html
- NSE equity/cash and equity-derivatives transaction charges and IPFT from
  1 March 2026: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf
- NSE commodity-derivatives transaction charges effective 1 April 2024:
  https://nsearchives.nseindia.com/content/circulars/FA61380.pdf
- BSE equity-derivatives notice 20240927-37 (effective 1 October 2024):
  https://www.bseindia.com/markets/MarketInfo/DispNewNoticesCirculars.aspx?page=20240927-37
- BSE equity segment master circular (29 April 2025):
  https://www.bseindia.com/markets/MarketInfo/DownloadAttach.aspx?attachedId=8a7fec3a-95bc-4bd2-82de-76e2a84e2915&id=20250429-51

## Still separately required before tariff-level acceptance

1. Build/review effective-dated charge rules for every enabled exchange × segment
   × product × side × charge component; do not assume the synthetic matrix proves
   these rates are populated.
2. Capture source document hash, effective dates, scope and independent approval
   for each active tariff rule. A missing or overlapping rule must fail closed.
3. Keep broker estimate, aggregate post-trade API output, and invoice-backed
   booked charge evidence as separate evidence classes.
4. Add source-backed golden invoice fixtures per exchange/broker as genuine notes
   become available. Do not invent per-fill charges or infer IPFT zero from an
   absent line item.

## Safety

This change does not enable live orders or live broker writes. PAPER mode remains
mandatory; PR #7 remains Draft/unmerged; only
`tarunsharma2610-del/tradepro-improved` is in scope.


## API-first GST/IPFT resolution decision — 27 October 2026

### Decision

Use Upstox's official APIs as the primary source for **current estimates**, and retain effective-dated exchange rules as an independent validation/fallback layer. Do not rebuild an unneeded parallel tariff engine when the broker calculator returns the breakdown. Do not treat any estimate API as proof of booked charges.

- Official calculator: `GET /v2/charges/brokerage` — estimate for the supplied instrument, quantity, product, BUY/SELL side and price. The documented response includes total, brokerage, GST, STT, stamp duty, transaction, clearing, IPFT and SEBI turnover fields. Evidence class: `ESTIMATE`.
- Official post-trade endpoint: `GET /v2/trade/profit-loss/charges` — period/segment financial-year charges breakdown, including GST, STT, stamp duty, transaction, clearing, IPFT, SEBI turnover and demat transaction fields. Evidence class: `AGGREGATE_SUMMARY`, never per-fill actual. Null/missing/invalid fields stay unresolved, not zero.
- Contract note / per-fill broker evidence remains the acceptance source for booked charge reconciliation. API aggregate summaries can be used as a control total, not allocated to fills unless the source and deterministic allocation policy explicitly support that use.

Official docs: https://upstox.com/developer/api-documentation/get-brokerage/ and https://upstox.com/developer/api-documentation/get-trade-charges/.

### GST method

1. Preserve the broker API's reported GST as a separately sourced estimate field; do not overwrite it with our own calculation.
2. Independently compute a statutory cross-check using explicit valuation lines, supplier state and recipient state recorded by the broker. Standard rate is 18% on the applicable taxable value; round using paise-level policy.
3. Apply the CBIC Section 15 default valuation. Exclude STT, stamp duty or another third-party recovery only when the complete CGST Rule 33 pure-agent conditions are supported by evidence. Charge labels alone do not prove pure-agent status.
4. Store `api_reported_gst`, `engine_estimated_gst`, their bases, source/provenance, and any variance separately. Do not silently force equality. A variance becomes a review/reconciliation item.
5. The post-trade aggregate endpoint may provide a GST control total but does not establish which individual fill carries the GST amount.

Official tax reference: https://cbic-gst.gov.in/sectoral-faq.html (stock-broking FAQ 77–78) and https://cbic-gst.gov.in/valuation-rules.html.

### IPFT historical/current method

NSE circular FA73061 dated 27 February 2026 says that from 1 March 2026 the NSE IPFT contribution was rolled back to Rs 0.01 per crore per side for cash market and equity futures, and Rs 0.01 per crore of equity-options premium per side. The corresponding transaction-charge rates became Rs 306.99/crore cash, Rs 182.99/crore equity futures and Rs 3,552/crore options premium, keeping combined outflow at Rs 307, Rs 183 and Rs 3,553 respectively. Earlier dates must use the historical effective-dated rule; do not apply the March 2026 rates retroactively. Source: https://nsearchives.nseindia.com/content/circulars/FA73061.pdf.

This NSE schedule must not be reused for BSE or MCX. For those exchanges, use the broker calculator's returned estimate for supported instruments and retain source-backed exchange schedules as independent validation. If the API omits/nulls IPFT, do not infer zero; leave it unresolved or use a verified, effective-dated rule for an explicitly supported scope.

### Existing implementation safeguards

The repository already contains exact approved API field mapping and value resolution services. They keep missing/null/invalid/zero distinct, preserve mapping provenance, reject stale/overlapping mappings, and prevent the Upstox brokerage calculator and aggregate post-trade endpoint from being relabelled as per-fill actual evidence. Keep these restrictions. The cross-exchange synthetic GST matrix validates shared tax-engine behavior only; it does not claim real tariff rates for every scope.

### Acceptance tests to require

- API calculator sample: retain all returned component values as estimate evidence, including null-vs-zero IPFT distinction.
- GST cross-check: API-reported GST and independently calculated GST are separate values; variance is visible and not auto-approved.
- Historical NSE IPFT: boundary tests before/after 1 March 2026, with the published transaction/IPFT split and unchanged combined rate.
- Scope guards: NSE rules never satisfy BSE/MCX; estimate and aggregate responses cannot be promoted to per-fill actuals.
- Existing broker-write boundary, migration and restore checks remain mandatory; PAPER mode remains mandatory.


## Implementation increment: broker GST estimate comparison

Added `backend/app/services/broker_gst_reconciliation.py` and `backend/tests/test_broker_gst_reconciliation.py`. The comparison takes a broker GST field as estimate evidence and independently computes the statutory GST estimate from explicit Section 15 / Rule 33 valuation lines and supplier/place-of-supply state inputs. It returns separate API GST, engine GST, taxable base, tax type, variance and review status.

- Exact match is reported as `MATCH_EXACT`.
- Any non-zero variance is retained and requires review (`ROUNDING_VARIANCE_REQUIRES_REVIEW` for within-tolerance differences; `VARIANCE_REQUIRES_REVIEW` otherwise). Tolerance never auto-approves a difference.
- Missing, null and invalid API values remain unavailable/reviewable; numeric zero is preserved and compared as zero, never converted to missing or a fabricated charge.
- Sub-paise GST values are invalid for INR currency comparison.
- This service is estimate comparison only. It does not mark API data as booked actuals or promote any per-fill accounting allocation.

Existing historical NSE IPFT tests already exercise the 31 March/1 April 2023 and 28 February/1 March 2026 boundaries and ensure the new rate is not applied retroactively. The next CI result must be checked on the latest code and documentation head before claiming this increment is green.


## Nested broker response field support — 27 October 2026

The GST estimate comparison now accepts an exact dotted JSON field path, including the documented nested Upstox response shape such as `data.charges.gst`, rather than assuming GST is a top-level key. Intermediate missing/non-object paths fail closed as `MISSING`; explicit null stays `NULL`; numeric zero remains `ZERO`. Regression tests cover nested value, missing, null and malformed field paths. This remains an estimate comparison only and does not promote calculator output to booked per-fill accounting.


## Exact nested API mapping hardening — 27 October 2026

`resolve_charge_api_value` now extracts a value only from the exact approved dotted `field_path`. It no longer reads a top-level leaf-name value when the approved nested path is missing. This matters for Upstox responses such as `data.charges.gst`/`data.charges.ipft`: a similarly named field elsewhere in the payload cannot silently substitute. Tests cover nested extraction and the missing-path/no-leaf-fallback case. Mapping provenance and missing/null/invalid/zero distinctions remain intact.


## Session resume checkpoint — 27 October 2026 (API-first charges decision; supersedes older next-step wording)

- **Resume from this checkpoint only.** Latest verified documentation head before this session sync: `72b03ee5b5c7487bb94815ea8b6fc3aabb6f8352`; exact-head Backend CI [#40553171858 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40553171858). The run completed successfully for backend pytest, broker-write boundary enforcement, SQLite upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL + document-volume restore, and restore-evidence retention. It is newer than the earlier failed CI and supersedes it for the tested commit.
- **User decision:** do not let a tiny GST/IPFT rounding discrepancy (including the discussed ₹0.20 annual aggregate variance / sub-paise arithmetic) block paper trading or the core app. The app does not need to independently recreate every broker billing detail before progressing.
- **Paper-trade approach:** use Upstox Brokerage Details API as an estimate where available; otherwise use the existing GST/brokerage/tax engine as a fallback. A target of roughly 95% practical accuracy is acceptable for paper-trading estimates, provided charges are labelled estimated and used consistently. Historical backtests should disclose that current tariffs may differ from historical tariffs.
- **Actual trades:** broker executes and collects actual charges. Import broker-reported post-trade charges/statements where available. Upstox post-trade Trade Charges API is aggregate evidence and must not be misrepresented as per-fill booked-charge evidence. Keep estimates separate from actuals; preserve reconciliation safeguards for imported records without blocking unrelated app development.
- **Do not reopen GST/IPFT from zero or chase tiny rounding differences as a release blocker.** Retain the existing GST engine, tariff/source evidence, API field-path resolver, reconciliation service and tests. Revisit only a concrete integration defect, material systematic variance, or a scope needing evidence.
- **Actual next technical work:** (1) inspect and wire the GST API-vs-engine comparison into the real charge-data flow using the correct charge lines and supplier/place-of-supply inputs; (2) finish genuinely uncovered component-by-component per-fill accounting acceptance—fill identity, paise totals, source-to-canonical mapping, replay/idempotency, rollback and segment/product applicability; (3) keep unsupported BSE/MCX tariff scopes explicitly estimated/unverified until source-backed; (4) synchronize maintained docs and run exact-head CI.
- **Evidence correction:** user has supplied genuine Upstox/RKSV contract-note evidence for 23, 24, 25, 27 and 30 January 2023. Do not state that no personal contract note exists or ask the user to provide it again. Production Oracle backup/restore acceptance remains deferred until deployment backups exist.
- **Safety invariants:** work only in `tarunsharma2610-del/tradepro-improved`; original `tarunsharma2610-del/Tradepro` is out of scope. PR #6 and PR #7 remain Draft/unmerged. PAPER mode mandatory; live broker order writes remain disabled. Do not merge.
- **First action next session:** verify the latest head and its CI, read this checkpoint's latest section, then continue from the caller-level API/GST integration and remaining accounting acceptance. Do not resume from the earlier failed CI or repeat already completed GST/IPFT research.
