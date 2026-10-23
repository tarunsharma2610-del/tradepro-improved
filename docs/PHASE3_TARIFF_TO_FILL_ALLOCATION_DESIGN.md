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

- Snapshot schema v3 now captures canonical sorted fill IDs and SHA-256 for single-fill and order-fill-set estimates.
- Persistence stores scope metadata with the immutable snapshot; migration `202610240018` adds scope fields and database scope validation for PostgreSQL and SQLite.
- Variance comparison now requires the actual reviewed component manifest to match the exact estimate fill set, validates all identified fills are present on the same broker connection and same broker order, and requires side/trade-date consistency across the set.
- Variance records retain scope and fill-set digest; replay checks include those fields. Existing variance rows are not mutated during migration; legacy single-fill replay tolerates their absent digest.
- Added builder tests for canonical fill-set ordering, duplicate IDs, empty sets, plus aggregate comparison/replay and mismatched-manifest tests.

Status: implementation is in progress and exact-head CI is pending. Do not claim aggregate variance is accepted until CI, migration downgrade/re-upgrade, and all tests pass. The current design intentionally rejects cross-order fill sets and does not yet implement advanced nonlinear tariff models beyond the existing rule calculator.
