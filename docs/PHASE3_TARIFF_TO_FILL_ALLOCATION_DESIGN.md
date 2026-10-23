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
