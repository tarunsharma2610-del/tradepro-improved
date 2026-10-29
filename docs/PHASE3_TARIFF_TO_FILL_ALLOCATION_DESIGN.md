<!-- Phase 3 continuation sync: 27 October 2026. Latest verified code/test head: 31ce2a10bcc789c223608c6566082b24aea7358c; Backend CI #40383076131 SUCCESS. Latest checkpoint-document commit: 61f23e5ce714c37a97f996f5f75c1963cc1136e6; docs-head CI #40383798007 must be checked for final conclusion. DP/demat Execution persistence and central charge-total recomputation are implemented; next gate is focused accounting audit. GST/IPFT implementation is not being restarted. PR #6/#7 stay Draft/unmerged; PAPER mandatory; live broker writes disabled; original Tradepro repository out of scope. -->

## Canonical checkpoint reconciliation — 26 October 2026 (canonical live-fill integration verified)

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. Never modify original `tarunsharma2610-del/Tradepro`.
- **Latest verified implementation head before this documentation sync:** `255fc208eed4bc8b922977717209d27912055377`. Exact-head Backend CI [run #40286205714 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40286205714): **962 passed, 1 warning**. Broker-write boundary guard, SQLite and PostgreSQL 16 migration upgrade/downgrade/re-upgrade, synthetic PostgreSQL/document-volume restore, and restore-evidence retention all passed. Synthetic restore does not prove actual Oracle Cloud recovery.
- **PR #6:** open, draft, unmerged. Do not merge without explicit user approval.
- **Phase 3 integration completed on this head:** `LiveFillAccountingService` now requires exactly six independently verified canonical charge snapshots. It revalidates each canonical ledger and its source hashes/links/mapping version, reviewed fill manifest and weights, INR totals, durable reconciliation references, and the contract-note reference under lock. There is no fallback to raw-only legacy allocation rows. Extra, unmapped, unlinked, or foreign-connection per-fill allocations fail closed.
- **Integration tests:** canonical snapshot creation → independent review → allocation → reconciliation; direct and combined/split transaction/IPFT source lines canonicalize to one exchange-charge component; exact replay, missing/unreconciled/extra allocations, and PostgreSQL live-fill-versus-ledger promotion race. No live broker order writes are enabled.
- **Remaining Phase 3 gates:** (2) independently reviewed effective-dated tariff applicability; (3) approved component-specific per-fill allocation rules; (4) invoice/source-backed GST/IPFT and product-specific component acceptance; (6) final adversarial, migration and recovery review; (7) exact-head documentation/sign-off. Official public tariff snapshots are research evidence, not proof of account-specific actual charges; candidate rates remain DRAFT until the required review is recorded. Synthetic restore is not a real Oracle recovery test.
- **Upstox controls:** no unused SDK runtime dependency; Agent Skill remains development/static-review-only; brokerage calculator is estimate-only; aggregate charge endpoints are not per-fill actual evidence.
- **Safety invariants:** PAPER mode mandatory; live broker order writes, automatic live-fill promotion, and automatic scheduling remain disabled. Keep PR #6 unmerged until explicit approval.
- **Next step:** resume at the remaining Phase 3 tariff/component evidence gates. Do not repeat canonical snapshot integration. Do not begin the separate AI/open-source adaptations until Phase 3 acceptance is complete.
- **Documentation-sync note:** this multi-document commit must pass its own exact-head CI before the next implementation change.

---


---

# Phase 3 tariff-to-fill allocation integration design

Status: design checkpoint; implementation not yet approved for accounting promotion.
Date: 23 October 2026.

## Goal

Connect the fail-closed effective-dated Upstox tariff selector to the existing contract-note source-component and per-fill allocation ledger without confusing an estimate with a broker-confirmed charge.

## Existing boundaries

- `TariffRule` selects exactly one APPROVED rule for an exact component/broker/exchange/segment/product/side/basis/date tuple.
- `calculate_charge_for_trade` calculates an amount from that rule and an explicit base. It does not persist results.
- `BrokerChargeSourceComponent` records a source amount transcribed from a reviewed, hash-verified contract note.
- `BrokerChargeAllocation` stores a source-component total and allocated amount for each fill.
- `verify_component_allocation_ledger` verifies the reviewed source document, independent review, exact fill manifest, weights, method version and total reconciliation. Automatic QUANTITY/NOTIONAL allocation is intentionally blocked until component-specific rules are approved.

## Required design distinction

Keep three records/meanings separate:

1. **Tariff estimate** — calculated from an approved rule and trade data. Must retain the complete rule snapshot/provenance, calculation base and amount. It is not a contract-note source amount.
2. **Broker source charge** — actual amount evidenced by the original contract note or a supported broker API response. Must retain evidence source type, source hash/request metadata, effective date, component and reviewer state.
3. **Per-fill allocation** — allocation of a broker source charge, not a silent replacement of the source amount with an estimate. Allocation must preserve exact total and reviewed fill-set hash.

An estimate may be compared to a source charge for variance analysis, but must not be promoted as a broker-confirmed actual charge.

## Proposed tariff snapshot fields

Before database migration, agree on an immutable snapshot representation containing:
- rule identifier/version and content digest;
- broker, exchange, segment, product, side, component and calculation basis;
- effective-from/effective-to and trade date;
- rate, unit, explicit base and base unit;
- computed estimate, currency and rounding policy;
- source URL, retrieval timestamp/date, source digest and reviewer/approval state.

Prefer a dedicated tariff-rule table if operationally managed rules are required. If the first release uses a static versioned registry, persist the complete canonical snapshot with the estimate rather than relying on a mutable in-memory rule list. Do not persist OAuth credentials.

## Calculation and persistence transaction

1. Resolve the trade and exact tariff scope.
2. Select exactly one approved effective rule; fail closed on no match or overlap.
3. Validate base and unit, calculate in Decimal and round according to the versioned policy.
4. Store estimate plus immutable rule snapshot under a stable idempotency key derived from source/trade identity, component and rule version.
5. On exact replay, return the existing identical result. On same key with different inputs/snapshot, raise a conflict; never overwrite silently.
6. When actual contract-note component arrives, create/review the source component independently.
7. Compare estimate with actual only as a variance record; do not use estimate to fill a missing source charge.
8. Allocate actual source component only under the existing reviewed allocation workflow. Recheck and lock evidence, source component, eligible fills and allocation rows in the transaction that promotes status.

## Component-specific gates

- Brokerage: order-level cap/minimum rules must be applied at the appropriate order scope before any reviewed distribution; do not calculate each fill independently and accidentally multiply a cap.
- GST: approved taxable component set and GST rate/effective date must be explicit; do not assume every charge component is in the taxable base.
- STT/CTT: product, side, tax event, base and statutory effective date must be explicit; exercise/assignment cases need their own applicability.
- Stamp duty: eligible side, product, exchange/segment, transaction-value base and effective rate must be explicit.
- Exchange/IPFT: exchange and segment-specific rate, effective date, base and unit must be explicit.
- SEBI turnover fee: use a normalized INR-per-crore unit where the source defines it that way, not a percentage field.
- DP/depository charges: daily/per-scrip/order charge models need a different basis from turnover percentages and are not covered by the current simple rate units.

## Acceptance tests before integration

- exact approved rule selected on both sides of every effective-date boundary;
- missing/overlapping/unapproved rules reject without writes;
- percent, INR-per-crore and fixed units cannot be confused;
- immutable snapshot digest and canonical serialization are stable;
- exact replay is idempotent; conflicting replay rejects;
- broker actual versus estimate remains distinguishable;
- order-level caps and GST base composition tested at their true scope;
- source component and allocation ledger reconcile exactly to paise;
- concurrent requests cannot create duplicate estimate/allocation rows;
- PostgreSQL and SQLite migration/rollback/re-upgrade pass;
- broker-write boundary tests remain green.

## Safety and release status

No active production tariff rates are supplied by this design. Rules need reviewed source extracts and executable examples before approval. PR #6 remains draft/unmerged until acceptance gates and explicit user approval. Live broker order writes remain disabled. Scope is only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` is out of scope.



## Implementation checkpoint — 2026-10-23

Implemented and verified:
- Durable canonical estimate-only snapshots with digest and idempotency key.
- Database-level append-only protections for direct SQL UPDATE/DELETE on PostgreSQL and SQLite (migration `202610240016`).
- SQLite direct-SQL mutation/deletion tests.
- PostgreSQL concurrency test for simultaneous same-key exact replay and conflicting-payload rejection.
- Code checkpoint `fd0e42917611f3b6c3f826cb2e99971fd3e2cce6` passed CI run 39960409771: 677 tests, broker-write boundary, SQLite/PostgreSQL 16 migration round-trips and synthetic restore drill.

Still not implemented:
- Variance-only estimate-versus-actual record linking a snapshot to reviewed contract-note source components.
- Order-scoped brokerage caps/minimums, conditional lesser-of pricing, full GST taxable-base composition, DP/depository charges and other special tariff bases.
- No live production tariff registry should be activated until each supported rule has reviewed Upstox source evidence and component-specific executable examples.

Safety boundary remains unchanged: an estimate is never an actual broker charge and must not supply a missing source component or enter per-fill actual allocation. PR #6 remains draft/unmerged; live broker order writes remain disabled; original `Tradepro` is out of scope.


## Variance service implementation update — 2026-10-23

A variance-only comparison service and append-only table are now implemented. Snapshot schema v2 optionally stores exact `source_trade_record_id`; comparison fails closed without it and currently requires the reviewed actual source component manifest to contain exactly that one fill. The service validates reviewed contract-note evidence, source bytes/hash, reviewer provenance, broker connection, component and currency. It records estimate, actual, signed variance and percentage only; it does not touch the allocation ledger.

Migration `202610240017` and direct-SQL immutability tests are included. CI run 39961777103 passed 680 tests and the broker-write/migration/restore gates. Multi-fill/order-level aggregate variance remains intentionally unsupported; a per-fill estimate must not be compared to an aggregate source total. Conditional caps/minimums, GST taxable-base composition and special charge models remain open.


## Aggregate estimate-versus-actual variance design proposal — 2026-10-23

Status: proposed design only; not implemented or approved for accounting promotion.

### Scope identity

Do not overload a single-fill snapshot by treating an order-level actual as equivalent. Add an explicit immutable comparison scope with one of:

- `TRADE_FILL`: exactly one stable broker trade/fill ID.
- `ORDER_FILL_SET`: a broker order identity plus a canonical, sorted set of stable fill IDs and a digest of that exact set.

The scope record must retain broker connection identity, exchange/segment/product, trade date, component, currency, rule snapshot digest, calculation basis, source/evidence ID, reviewer identity, and calculation version. A comparison is valid only if the estimate scope and reviewed actual source-component manifest identify the same scope and exact fill set. Missing/ambiguous order IDs, incomplete fill sets, duplicate fill IDs, currency/component mismatch, or changed fill-set digest must fail closed.

### Calculation rule

- Compute order-scoped charges at order scope using the approved rule (for example, a brokerage cap/minimum) before comparing with the contract-note total. Never sum per-fill calculations when the tariff is nonlinear or capped.
- For additive per-fill components, aggregation may sum independently calculated fill estimates only if the approved tariff rule explicitly declares that aggregation method and units.
- Store estimate, actual, signed variance (actual minus estimate), absolute variance, percentage with a documented zero-estimate policy, rounding/version, and the exact member-fill digest in an append-only variance record.
- The variance path is audit-only: it must not mutate source components, allocations, positions, realized P&L, or estimate snapshots, and must never create a missing actual charge.
- A single source component cannot be compared to a partial fill set or to a different set with the same count. Exact member identity—not only quantity/count/total—is required.

### Idempotency and concurrency

Use a stable unique comparison key over estimate snapshot/version, actual source component ID/hash, scope type, and fill-set digest. Exact replay returns the existing identical record. Same key with different payload rejects as a conflict. Lock/recheck the estimate, source component, evidence review/hash state, and current fill manifest within one transaction; insert the variance record atomically. Concurrent retries must produce one record, and any evidence/manifest mismatch must produce no write. Database immutability protections should reject direct UPDATE/DELETE in PostgreSQL and SQLite.

### Required acceptance tests before implementation is considered complete

1. Exact one-fill comparison remains unchanged and backward-compatible.
2. Exact order fill-set matches; reordered input canonicalizes to the same digest.
3. Missing, incomplete, extra, duplicate, or changed fill IDs reject.
4. Same fill count but different members rejects.
5. Order-scoped brokerage cap/minimum is calculated once at order scope, not multiplied per fill.
6. Additive component aggregation only works when the rule explicitly opts in.
7. Component, currency, connection, trade-date, source hash, reviewer, or rule-version mismatch rejects.
8. Exact replay is idempotent; conflicting replay rejects; concurrent same-key calls create one row.
9. Evidence review revoked or manifest changed before transaction recheck causes rollback/no variance write.
10. Failed comparison leaves actual allocations, positions, P&L and estimate snapshots byte-for-byte/logically unchanged.
11. Direct SQL UPDATE/DELETE against variance records fails on PostgreSQL and SQLite.
12. Migration upgrade/downgrade/re-upgrade and broker-write guard remain green.

### Explicit exclusions until separately designed

Do not infer order membership from timestamp/quantity/symbol alone. Do not use aggregate totals from public examples as verified evidence for a real account. Do not allocate an aggregate estimate into per-fill actual accounting. Multi-component GST composition, conditional lesser-of pricing, DP/depository fee bases and other unsupported tariff models remain separately gated; each needs an approved source-backed rule and executable examples.


## Implementation checkpoint: explicit fill-set variance scope — 2026-10-23

Implementation has started on the proposed `TRADE_FILL` / `ORDER_FILL_SET` scope:

- Snapshot schema v4 captures canonical sorted fill IDs and SHA-256 for single-fill and order-fill-set estimates.
- Persistence stores scope metadata with the immutable snapshot; migration `202610240018` adds scope fields and database scope validation for PostgreSQL and SQLite.
- Variance comparison now requires the actual reviewed component manifest to match the exact estimate fill set, validates all identified fills are present on the same broker connection and same broker order, and requires side/trade-date consistency across the set.
- Variance records retain scope and fill-set digest; replay checks include those fields. Existing variance rows are not mutated during migration; legacy single-fill replay tolerates their absent digest.
- Added builder tests for canonical fill-set ordering, duplicate IDs, empty sets, plus aggregate comparison/replay and mismatched-manifest tests.

Status: implementation is in progress and exact-head CI is pending. Do not claim aggregate variance is accepted until CI, migration downgrade/re-upgrade, and all tests pass. The current design intentionally rejects cross-order fill sets and does not yet implement advanced nonlinear tariff models beyond the existing rule calculator.


## Upstox API source-contract review — 2026-10-23

Reviewed official endpoints: [Brokerage Details](https://upstox.com/developer/api-documentation/get-brokerage/), [Trade Charges](https://upstox.com/developer/api-documentation/get-trade-charges/), [Historical Trades](https://upstox.com/developer/api-documentation/get-historical-trades/), and [Brokerage Charges](https://upstox.com/brokerage-charges/). The brokerage endpoint returns a scoped charge estimate, including tax/charge breakdown and DP plan daily per-scrip minimum metadata; the trade charges endpoint returns segment/financial-year range totals; historical trades supplies trade IDs and scope fields. Treat all API-calculated charge breakdowns as reconciliation/reference data unless independently captured under the approved evidence workflow; they do not automatically replace the reviewed contract note/source component. Preserve exact API version, request scope, retrieval time and payload digest for audit, and never persist OAuth tokens. The public charges page includes rows with different effective periods, so no rates are activated from a flattened page parse. DP per-scrip/day minimums, STT/CTT event-specific treatment (including exercised options), conditional lesser-of pricing and other unimplemented charge models remain explicit acceptance gates.

The stamp-duty calculator now rejects non-percentage units; commit `ce0b4bc17eaf1656334e10ca8d6e32a68f50593b` passed CI run [39987357989](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39987357989), including tests, broker-write guard, SQLite/PostgreSQL 16 migration round-trips and synthetic restore drill.


## Generic conditional-charge guard — 2026-10-23
The next audit found that the generic rate calculator could apply plain rate×base arithmetic to STT/CTT and DP/demat components, despite these requiring event- or day/scrip-specific semantics. Commit `ee09183e5b8eeff0311431faa90b807d9b561ce7` adds an explicit fail-closed block for STT, CTT, DP, DP charges and demat/depository transaction charges in the generic calculator, with parameterized regression tests. Exact-head CI run [39988242077](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39988242077) passed. The synchronized documentation commit `b1207def7d828c960e6fffe9c6af8b9ed0177c07` also passed exact-head CI run [39988578238](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39988578238).

Audit note: the implementation constant is `tariff-estimate-snapshot-v4`; older design text saying snapshot v3 is stale and is corrected in the accompanying design-document update. Remaining gated models include STT/CTT event-specific rules, DP daily per-scrip minimums, conditional lesser-of pricing, and reviewed source-backed effective-date rates. No live tariff registry or live broker order writes are enabled.

## Aggregate variance concurrency checkpoint — 2026-10-24
Exact-head CI run `40064129721` passed on `dbff090610028cfb9f5a87585d9c8e697449cd23` (738 passed, 1 warning). Concurrent duplicate comparisons are covered by PostgreSQL integration tests and remain audit-only: one append-only variance record, exact replay, no allocation writes. Next implementation gate is effective-dated, reviewed component-specific tariff applicability and explicit integration with the per-fill ledger. Conditional-charge and unsupported allocation-shape guards remain in force; brokerage calculator estimates and historical aggregate charges are not actual per-fill evidence.

## Read-only Upstox charge endpoints — 2026-10-24
The existing read-only client now exposes brokerage estimate, historical aggregate charges and paginated historical trades; exact-head CI run `40064514873` passed (744 passed, 1 warning). The next integration boundary is immutable estimate-only normalization and provenance. Keep the Brokerage Details response as an estimate; keep Trade Charges as aggregate history and Historical Trades as trade references. The current Upstox tariff page has 2026 effective-date rows, but rates remain research-only until archived, independently corroborated, reviewed and covered by component-specific applicability tests. No API response creates or promotes per-fill allocations.

## Upstox API estimate normalization — 2026-10-24 (CI verified)
Brokerage calculator output normalizes to separate component-level estimate-only snapshots with full canonical response JSON/digest, request parameters, API version/endpoint, retrieval timestamp, total and separate DP-plan minimum metadata. The existing immutable snapshot store is reused. Before variance-only comparison, the service recomputes response integrity and checks quantity, price, side and instrument against the exact reviewed fill set. This does not create actual-charge evidence or allocation rows. Exact-head CI run `40065219626` passed (**754 passed, 1 warning**).

## Flat brokerage estimate shape — 2026-10-24 (CI verified)
Added `ORDER_FIXED`/`INR_FIXED` support to guarded order brokerage calculation and snapshot generation; percentage brokerage with rule-bound caps remains supported. This is calculation-shape support, not tariff activation or fill allocation. Exact-head CI run `40065607232` passed (**756 passed, 1 warning**). Next: archived source-backed effective-dated candidate rules and applicability tests.

## Source-backed tariff candidates — 2026-10-24 (CI verified)
Added a dated normalized source excerpt and 18 effective-dated STT/exchange-charge candidates. All are DRAFT and cannot be selected; no active rate or per-fill automatic calculation was enabled. Exact-head CI run `40065979244` passed (**760 passed, 1 warning**). Remaining: archive original source bytes where possible, resolve IPFT/transaction-charge composition, corroborate stamp duty, and add applicability/date-boundary tests before review.


## 2026-10-24 — Resolver acceptance and CI checkpoint

- Backend workflow `40108183667` succeeded on prior head `8214430f562f6f425cfc1b9b6a6b3b547832b68a`. New resolver tests add exact broker/endpoint/schema/field/scope matching and non-finite-number rejection; newer commits still require CI.
- Mapping identity fixtures use immutable dataclass replacement. Intended-use semantics remain explicit; missing/null/invalid values remain unusable and retain provenance; numeric zero remains distinct.
- Accounting acceptance includes replay/conflict, ledger reconciliation, lock order, rollback, reviewer authority and PostgreSQL verification/promotion race coverage. Re-check exact test and workflow status before claiming complete. CI does not establish production tariff correctness or broker-origin authenticity.
- Safety gates unchanged: PR #6 draft/unmerged; live broker order submission and automatic quantity/notional allocation disabled; production Upstox mappings/tariffs unapproved. Only `tarunsharma2610-del/tradepro-improved` is in scope; original `Tradepro` remains untouched.


## 2026-10-24 — Resolver field-identity guard added; CI pending

- Resolver now verifies that the payload field matches the terminal field in the approved mapping path. Implementation `77aa77aec37dc535c3e427ca3f88c2ccb5e75ed8`; regression test `5c5482c7f7fa623707698f64b6a061351e5e5b87`. CI is pending for these and subsequent documentation commits.
- The field-identity guard is a code correctness safeguard, not approval of production Upstox field semantics or tariffs. Existing live-fill tests cover lock order, replay idempotency and rollback; genuine concurrent verification-versus-promotion coverage still needs confirmation.
- PR #6 remains draft/unmerged. Live order submission and automatic quantity/notional allocation remain disabled. Work only in `tradepro-improved`; original `Tradepro` remains untouched.


## 2026-10-24 — Latest resolver CI and PostgreSQL concurrency suite verified

- Backend workflow [#40109041654](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40109041654) passed on head `ed346e823cbfae8448fae0134c4ff864bfcc60ac`: **872 passed, 1 warning**; broker-write boundary guard passed.
- Dedicated PostgreSQL concurrency tests cover competing fill sets, source verification vs allocation promotion, and live-fill promotion vs ledger verification. The successful test summary has no skipped tests, confirming the collected suite ran in CI's synthetic database environment.
- This is not approval of production Upstox tariff/field mappings. PR #6 remains draft/unmerged; live broker order submission and automatic quantity/notional allocation remain disabled; original `Tradepro` remains out of scope.


## 2026-10-24 — Official tariff/API source audit

- Upstox's `GET /v2/trade/profit-loss/charges` accepts segment, financial year and optional date bounds; documented output is aggregate `charges_breakdown`, not a per-fill schema. Example `charges.ipft` is null. Treat it as aggregate reconciliation evidence only, and never coerce null to zero. https://upstox.com/developer/api-documentation/get-trade-charges/
- NSE circular NSE/FA/73061 dated 27-Feb-2026 applies from 1-Mar-2026: combined member outflow ₹307/crore cash, ₹183/crore equity futures and ₹3,553/crore equity-options premium; included IPFT contribution is ₹0.01/crore each side. Use effective-dated rate versioning and guard against double counting. This circular does not establish Upstox-specific contract-note JSON field semantics. https://nsearchives.nseindia.com/content/circulars/FA73061.pdf
- Upstox's public charges page shows newer effective-date summary values alongside historical tables and lists a STT/CTT change effective 1-Apr-2026. Use the matching date/scope and prefer official exchange/statutory notices for rate authority. https://upstox.com/brokerage-charges/
- Acceptance: aggregate API response, null IPFT, stale tariff, combined-vs-split IPFT and effective-date boundary must fail closed when actual per-fill evidence is required. Production mappings and tariffs remain DRAFT/non-selectable.
- Latest prior implementation head `ee1b2a74d2a9f6141b9afbb6e06562b5cf263a9b` passed workflow #40110597753; rerun CI on the resulting documentation head.
- PR #6 remains draft/unmerged; live order submission and automatic quantity/notional allocation remain disabled; original `Tradepro` remains untouched.


## 2026-10-24 — Aggregate endpoint hard guard added; CI pending

- Upstox `/v2/trade/profit-loss/charges` is now explicitly blocked from `PER_FILL_ACTUAL` resolution regardless of a misleading mapping semantic. Its published schema is aggregate `charges_breakdown`, not per-fill evidence.
- Regression test `test_official_upstox_aggregate_charges_endpoint_cannot_be_promoted_to_per_fill` covers the guard. Implementation `cdc07afdd8cc0c8d0b37d7e4aa8cdf1bf6eac651`; test `8ae749017a8ba0016f2c9adeb77eaff41fb5ae70`. Latest test CI must pass before verification is complete.
- Keep production mappings/tariffs unapproved; null distinct from zero; automatic quantity/notional allocation and live order submission disabled. PR #6 draft/unmerged; original `Tradepro` out of scope.


## 2026-10-24 — Upstox brokerage calculator restricted to estimates; CI pending

- Official Upstox `GET /v2/charges/brokerage` takes proposed instrument, quantity, product, transaction type and price, returning a charge calculation; this is not proof of final booked per-fill charges. https://upstox.com/developer/api-documentation/get-brokerage/
- Resolver now blocks `/v2/charges/brokerage` from `PER_FILL_ACTUAL` and actual `AGGREGATE_SUMMARY` use even if a mapping is misleadingly labelled. Existing guard still blocks `/v2/trade/profit-loss/charges` from per-fill actual use. New regression tests cover both misuse cases.
- Implementation `3486d854dae2451858a858cb627602aca7338969`; tests `6c92101a1890a0f4d761e86ed3db047a269fd10d`. Prior head `6cc8b58f635fcb4f1b1cb3e5997099d074800a28` passed workflow #40111501429. CI for the new commits must be verified.
- Production mappings/tariffs remain unapproved; null is not zero; automatic quantity/notional allocation and live broker order submission remain disabled. PR #6 stays draft/unmerged. Only `tradepro-improved` is in scope; original `Tradepro` remains untouched.


## Canonical latest Phase 3 checkpoint — 26 October 2026

- **Repository:** `tarunsharma2610-del/tradepro-improved` only. **Branch:** `phase3/durable-per-fill-charge-allocation`. **Verified code/evidence head:** `d287da70ce184c904c6f9ede9e4a0edca5839f8f` (commit: “docs: reconcile public Upstox contract note GST examples”).
- **Exact-head CI:** PASS — [GitHub Actions run #40304398632](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40304398632), commit `d287da70ce184c904c6f9ede9e4a0edca5839f8f`; **1,004 passed, 1 warning**. Broker-write boundary guard, SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration round-trip, synthetic PostgreSQL/document-volume restore drill, and restore-evidence retention also passed. This is CI evidence, not proof of a real Oracle recovery or broker-origin authenticity.
- **GST/IPFT research:** Three public third-party historical Upstox note copies were reconciled: 11-Feb-2025 base ₹2.97 / IGST ₹0.53; 21-May-2024 base ₹77.56 / IGST ₹13.96 (IPFT ₹0.11 listed outside that note's printed base); 12-Mar-2025 base ₹2.75 / IGST ₹0.50. Printed-base compositions differ historically. The current official Upstox schedule supports the **estimate-only** base of brokerage + transaction charges + demat where applicable + IPFT, with IPFT represented exactly once because it is combined with transaction charges. Do not add SEBI to this current estimate base without current applicable billing evidence; never calculate GST on trade notional or infer zero from missing/null fields.
- **Tax/accounting approval:** all four GST component candidates remain `DRAFT`. Historical public copies do not prove current actual per-fill billing across products/accounts. Actual-charge promotion stays gated; estimate logic and actual invoice reconciliation are distinct. Follow effective dates and preserve raw API/source evidence.
- **Next action when resuming:** continue Phase 3 from this exact commit and checkpoint. Next gate is component-specific GST acceptance cases for equity delivery, intraday, futures and options, then implementation review and exact-head CI; do not restart from earlier saved checkpoints.
- **Safety / PR:** PAPER mode mandatory; live broker `place_order`/`modify_order`/`cancel_order` and automatic live-fill promotion remain disabled. PR #6 remains open, draft and unmerged. Original `tarunsharma2610-del/Tradepro` is not the work target and must remain untouched.
- This checkpoint supersedes older statements in this document about CI being in progress or requiring verification for the pre-`d287da7` head. Historical notes remain history; this is the canonical resume point.


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


## Authoritative Phase 3 engineering closure — 29 October 2026

This section supersedes older status/next-step notes above; earlier entries remain as historical audit trail.

**Status: Phase 3 engineering acceptance is complete for the agreed PAPER-mode scope.** Verified code checkpoint `3a0c464afcb10261d1590607f8440affd21295a0` passed Backend CI [#40878367369 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/40878367369): **1,207 passed, 1 warning**; broker-write boundary, SQLite/PostgreSQL 16 migrations, synthetic restore and retained restore evidence passed. The new documentation-sync head requires its own CI result.

Completed engineering scope includes deterministic paise-exact per-fill allocation; evidence integrity and reviewer control; source-to-canonical mapping; combined/split transaction/IPFT handling; replay conflict/idempotency, lock and rollback safeguards; explicit DP/demat completeness; statutory GST and GST/API diagnostic primitives; and Upstox API-first PAPER estimates with hardcoded fallback. Estimates carry: “Estimated charges may differ from actual broker charges. For paper trading only; these are not actual booked charges.” Upstox post-trade charges remain aggregate-only and cannot be promoted to per-fill actuals.

Non-blocking release gates: deployed, user-authorized Upstox OAuth/API smoke test; real Oracle/database-plus-document-volume backup/restore; and independent effective-dated tariff approval for any scope intended for actual-charge promotion. Unsupported tariff scopes remain estimate-only/fail-closed; historical contract-note fixtures do not turn API estimates into actuals. These gates do not block PAPER-mode engineering closure.

Safety unchanged: only `tarunsharma2610-del/tradepro-improved`; original `Tradepro` untouched; PR #6/#7 Draft/unmerged; PAPER mandatory; live broker order writes disabled. Phase 4 is the next separate project increment after exact documentation-head CI passes.
