# Live Broker Order State Machine — Design Before Implementation

**Status:** design only; no live submission is enabled by this document.  
**Scope:** future Upstox live order lifecycle, using the existing Paper Trading code without routing live orders through the paper fill path.

## 1. Current implementation audit

The current repository already has:
- A fail-closed gate in `ExecutionService.place_order`: it rejects LIVE or unknown mode before creating an order.
- OAuth state binding/single-use checks, encrypted broker credentials, access-token expiry checks, and connection verification.
- An equity-only instrument/segment validator and paper order accounting with atomic transactions.
- An `Order` model with a local status, a legacy singular `broker_order_id`, optional idempotency key and broker-status metadata.
- Read-only broker status checks that require a matching returned `order_id` and deliberately do not update local fills, cash or positions.
- An Upstox adapter for V3 place/modify/cancel and read-only V2 order details, order book, order trades and order history. These methods are not wired into execution.

Important gaps: no separate live submission service, no durable parent-to-multiple-broker-order mapping, no trade-ID deduplication for live fills, no local PARTIALLY_FILLED state, no broker-trade reconciliation loop, no unknown-timeout recovery, and no complete live/manual pre-trade exposure control or broker-error circuit breaker.

## 2. Upstox API facts used in this design

- **Place Order V3** uses `POST https://api-hft.upstox.com/v3/order/place`. The response contains `data.order_ids`, an array, and can contain multiple broker order IDs when slicing is used. The request `tag` is limited to 40 characters. Official docs: [Place Order V3](https://upstox.com/developer/api-documentation/v3/place-order/).
- **Modify Order V3** uses `PUT https://api-hft.upstox.com/v3/order/modify`; **Cancel Order V3** uses `DELETE https://api-hft.upstox.com/v3/order/cancel?order_id=...`. Acceptance of either request is not proof that the broker has reached the requested terminal state. Docs: [Modify](https://upstox.com/developer/api-documentation/v3/modify-order/), [Cancel](https://upstox.com/developer/api-documentation/v3/cancel-order/).
- **Order Details** provides a broker order's current status and order ID: [Get Order Details](https://upstox.com/developer/api-documentation/get-order-details/).
- **Order History** supports lookup by broker `order_id` and/or `tag`, allowing recovery after a response is lost: [Get Order History](https://upstox.com/developer/api-documentation/get-order-history/).
- **Order Trades** returns trade-level fills for a broker order, including trade ID, quantity, average price and order ID: [Get Order Trades](https://upstox.com/developer/api-documentation/get-trades-by-order/).

These endpoints are currently only adapter methods and mocked tests. There has been no live order submission.

## 3. Required data model changes

Use additive migrations; do not repurpose or delete existing paper fields.

### `Order` — conceptual user order
Retain the local idempotency key and add a stable broker `tag` (maximum 40 chars) generated before any broker request. Extend the live lifecycle statuses to include at least:
- `SUBMITTING`: local intent committed before the network request.
- `SUBMISSION_UNKNOWN`: request timed out or response was ambiguous; broker may have accepted it.
- `PENDING`: broker confirms an open/unfilled order.
- `PARTIALLY_FILLED`: broker confirms some, but not all, requested quantity executed.
- `CANCEL_REQUESTED` / `MODIFY_REQUESTED`: request sent, broker outcome not yet confirmed.
- Existing terminal `FILLED`, `REJECTED`, `CANCELLED` where supported by confirmed broker data.

Paper statuses and paper accounting must remain unchanged.

### New `BrokerOrder` — one row per broker child order
A conceptual local order can map to multiple broker orders, so do not treat the legacy singular `Order.broker_order_id` field as the only source of truth. Add a child table with:
- FK to local `Order`, broker name, broker order ID (unique per broker), stable tag, broker status.
- Requested quantity, cumulative filled quantity, average fill price, last status-check time, error text and timestamps.
- Constraints/indexes that prevent duplicate child-order IDs and make recovery queries efficient.

Keep `Order.broker_order_id` populated with a primary/first ID only for backward compatibility until all readers are migrated; the child table is authoritative for multi-order reconciliation.

### `Execution` — one confirmed broker trade per row
Add nullable `broker_trade_id` (unique when non-null) and `broker_order_id` so each broker-reported trade is applied at most once. Paper executions keep these fields NULL. A unique trade-ID constraint is the deduplication barrier when reconciliation retries or restarts.

The live reconciliation transaction must insert the trade execution and update the live position/cash ledger atomically. Do not write a fill merely because Place Order returned success or Order Details reports a terminal status; use validated trade records for executed quantity/price.

## 4. Submission lifecycle

1. **Preflight:** confirm explicit user authorization and environment-level live enablement, correct broker connection/token, market session, verified equity instrument, valid tick/quantity, sufficient funds/margin, per-order notional, position/exposure and daily-loss limits. Any missing control blocks submission.
2. **Persist intent first:** create a local order with a stable idempotency key and deterministic tag before network I/O. A tag such as `tp` plus the 32-character hex local UUID is 34 characters and stable across retries. Commit the intent so a restart can recover it.
3. **Submit once:** call V3 Place Order with `slice` behavior explicitly chosen by the live-service policy. Never automatically repeat a POST after a timeout. A timeout is an unknown outcome, not a rejection.
4. **Parse response:** require a successful response and a non-empty list of `data.order_ids`. Persist every returned child order in one transaction. If the response is malformed or ambiguous, mark `SUBMISSION_UNKNOWN` and recover by tag; do not blindly resubmit.
5. **Recover uncertain submission:** query Order History by the stable tag, verify every returned order belongs to the expected instrument/side/quantity where the response provides those fields, and persist discovered child IDs. Only an explicit broker response proving no order exists can permit a carefully bounded retry policy.
6. **Track status:** query Order Details for each known broker order. Require the returned broker order ID to match the requested ID. Status checks update broker metadata, not fills/cash.
7. **Reconcile trades:** fetch Order Trades per child order; validate `order_id`, non-empty `trade_id`, positive quantity, valid price, instrument and side. Deduplicate by broker trade ID. Apply each new trade once, in a DB transaction that includes execution record, position/cash accounting and cumulative fill totals.
8. **Derive parent state:** `FILLED` only when confirmed executed quantity reaches requested quantity; `PARTIALLY_FILLED` while a positive remainder remains; do not erase partial executions when the rest is cancelled or rejected. If all children are terminal with unfilled remainder, preserve the actual filled quantity and expose the terminal outcome clearly.
9. **Modify/cancel:** validate that the order is still modifiable/cancellable, persist a request-in-progress marker, send the V3 request, then poll Order Details/History until confirmed or unresolved. A successful API response alone must not set local status to `CANCELLED` or rewrite quantities/prices.
10. **Restart recovery:** on startup and on a schedule, find `SUBMITTING`, `SUBMISSION_UNKNOWN`, `PENDING`, `PARTIALLY_FILLED`, `CANCEL_REQUESTED` and `MODIFY_REQUESTED` orders. Reconcile by stable tag/order ID and trade ID. Never resubmit an unknown order without resolving its broker state.
11. **Mismatch circuit breaker:** if broker identity, order quantity, trade IDs, positions, holdings or cash cannot be reconciled, stop new live entries for that account and require explicit review. Do not silently “fix” discrepancies with synthetic fills.

## 5. Risk and authorization gates before live submission

The current paper order cap and automated-entry loss limit are not a complete live risk system. Before a live service is wired, implement and test:
- Separate environment-level live enablement plus explicit per-user opt-in/confirmation; no UI/database flag alone may bypass the server gate.
- All-order pre-trade limits for manual and strategy orders: notional, available funds/margin, position size, aggregate exposure, daily loss and order frequency.
- Verified instrument master, tick size, quantity/lot rules and supported segments.
- Account-level emergency stop and broker-error/unknown-order circuit breaker.
- Rate-limit-aware polling and bounded backoff that never blindly repeats an ambiguous order submission.
- Audit logging without secrets, and staging/sandbox tests for the broker integration.

OAuth state/credential encryption currently exist; expired tokens are rejected. Token refresh/reconnection automation and production static-IP/regulatory prerequisites still require verification.

## 6. Test plan and release gates

All tests below must use mocked HTTP or an authorized Upstox sandbox; never place a real order just to test.

- V3 Place Order returns one ID, multiple IDs, malformed response, explicit rejection, network timeout after acceptance and network timeout before acceptance.
- Stable tag recovery finds an existing order after timeout and proves the service does not POST a second time.
- Partial fills across several trade IDs update position/cash/executions exactly once; replaying the same trade does not double-count.
- One local order mapped to several broker child orders aggregates correctly.
- Modify/cancel request accepted but status remains open; eventual cancellation; cancellation after partial fill; broker rejects modification/cancellation.
- Restart with unknown submission, open order, partial fill and pending cancellation.
- Mismatched broker order ID, trade ID/order ID mismatch, duplicate trade ID, malformed price/quantity and broker/local position mismatch all fail closed.
- PAPER mode can never invoke place/modify/cancel; LIVE mode cannot reach the paper fill method.
- Migration upgrade and backfill tested against both a clean DB and a populated staging-like DB.
- Frontend shows broker-confirmed states and unresolved/unknown states distinctly; it never implies that a request was filled/cancelled before confirmation.

## 7. Implementation order

1. Add schema/model support for broker child orders, trade-ID deduplication and partial-fill states, with additive migration and model/migration tests. No execution path uses the new tables yet.
2. Add pure response validation/mapping helpers and tests for V3 place/order-history/order-details/order-trades payloads.
3. Implement a separate, initially unregistered `LiveExecutionService` with explicit gates and mocked tests.
4. Implement a reconciliation worker that recovers unknown submissions, syncs broker statuses and applies deduplicated trades atomically.
5. Add account-wide live risk controls and circuit breakers; test direct API calls and concurrent submissions.
6. Only after independent review and sandbox/staging evidence, consider wiring explicit live UI/API routes. Keep the existing paper `ExecutionService` isolated.
7. Obtain explicit user authorization before enabling any real order path.

**Current release decision: Live Trading is NOT READY. The current adapter methods are foundations only; the PAPER-only execution gate must remain unchanged.**


## Schema foundation status update — 17 October 2026

The first schema-only implementation step is now committed in migration `202610170004_live_broker_order_state.py`: `BrokerOrder` supports multiple broker IDs per local order; `Order.broker_tag` is unique when populated; order status width supports partial/unknown states; and `Execution` has a child-order reference plus per-broker trade-ID uniqueness. The populated migration regression test passed. No execution/reconciliation code uses these fields yet.


## Response validation helper status update — 17 October 2026

Added pure typed parsing helpers in `backend/app/brokers/upstox/response_parsing.py` for Place Order V3 IDs, Order Details, Order History and Order Trades. They are tested but not wired into any live submission or accounting path. The history parser intentionally allows repeated order IDs because the official endpoint can return multiple status events for one order.


## Pre-trade risk audit update — 17 October 2026

The existing risk engine gates automated strategy entries using realized losses; manual orders bypass it and unrealized drawdown is not included. The paper order cap/cash/holding checks are not a live risk system. Live exposure/loss/rate limits, stale-quote/session checks and an account-level circuit breaker remain missing. Upstox Funds & Margin V3 (released 10 April 2026) is now the verified source for available-to-trade funds, via `GET /v3/user/get-funds-and-margin` with `Api-Version: 3.0`; the adapter lacks this method, so the next step is read-only support only.


## Funds & Margin V3 adapter status — 17 October 2026

The adapter now has read-only `get_funds_and_margin` using the official V3 endpoint and `Api-Version: 3.0`. Tests cover the documented response envelope and the daily 00:00–05:30 IST maintenance response (423). This raw response is not yet used by any risk decision. The next step is a pure parser that keeps cash available and pledged margin distinct.


## Funds response parser status — 17 October 2026

The pure `parse_funds_and_margin_v3` parser is implemented and tested. It intentionally separates total available-to-trade from cash and pledge margin; this avoids treating pledged collateral as cash. It is not connected to order approval. Next is read-only instrument-specific margin calculation support, still without live execution wiring.


## Status correction — 18 October 2026 (supersedes stale next-step notes)

The following are now present in the branch: `BrokerAdapter.get_margin_details`, the Upstox `POST /v2/charges/margin` implementation with local request validation, pure `parse_margin_details`, and unit tests for success/error/malformed response shapes. Older notes saying the adapter method or typed parser is still missing are historical snapshots, not current status. The parser is read-only and is not used to authorize orders.

The current blocker is verification: the GitHub integration returned no workflow run and no commit status for the current PR head when checked. Earlier CI results (238 backend tests, one warning, migration/frontend checks green) belong to an older commit and do not verify the margin parser changes. No pass/fail conclusion is possible from the available evidence. Inspect or trigger the configured workflow from GitHub Actions and record actual results before advancing.

`MASTER_ROADMAP.md` is now the current sequencing guide. After this verification gate, the next implementation phase is a separate, initially unregistered `LiveExecutionService` with mocked tests, while preserving the current PAPER-only execution guard. Do not merge the draft PR, place real orders, or enable live trading.


## Broker trade intake validation update — 18 October 2026

The staging-only `BrokerTradeIngestionService` was hardened to resolve the exact broker connection from the mapped child order and verify owner/broker binding. It rejects missing instrument tokens and malformed side values, with regression tests added. It remains separate from `Execution` accounting and is not registered as a live execution path. Current code/test target `264aa4c609d522cd01d07e8213bfee6f14c7a2bf` has no current-head Actions result available; do not proceed to live lifecycle wiring until tests and migration checks are verified.


A further regression test now confirms intake rejects legacy child-order rows with no resolvable broker connection. Code/test target `264aa4c609d522cd01d07e8213bfee6f14c7a2bf`; verification still pending.
