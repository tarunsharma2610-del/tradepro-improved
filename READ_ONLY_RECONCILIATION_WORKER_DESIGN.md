# Read-only broker reconciliation worker — design and implementation gate

Status: design only, not implemented. Reviewed 2026-10-17. Scope is the separate `tradepro-improved` repository. Live submission and cancellation remain disabled.

## Goal

Add a scheduled/on-demand worker that reads Upstox order and trade observations, validates them, matches them to durable local intents, and persists safe status/fill evidence. It must not place, modify or cancel orders. This worker is not authorization to enable live trading.

## Existing building blocks

- `backend/app/services/live_order_reconciliation.py`: pure order/trade normalizers, strict intent matcher and fill-evidence state resolver.
- `backend/app/repositories/live_order_repository.py`: versioned state persistence, idempotent fill identity persistence, and safe late-linking.
- `live_order_intents`, `live_order_events`, `broker_fill_identities`: durable evidence.
- Latest pre-design test checkpoint: [GitHub Actions run 39056392873](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056392873), 294 passed, 1 warning; SQLite/PostgreSQL 16 migration checks passed.

## Hard safety boundary

1. The worker's broker-client interface must expose only read methods needed for order book, order history/details, and per-order trades. Do not inject the general execution adapter into the worker if it also exposes place/modify/cancel methods.
2. No `POST`, `PUT`, or `DELETE` broker calls. No order submission, modification, cancellation, retry of a submit, or outbox dispatch.
3. Never log or persist access tokens, refresh tokens, client secrets, authorization headers, or raw sensitive HTTP bodies. Log only safe error categories, correlation IDs, status codes and sanitized request identifiers.
4. Every job is scoped to one authenticated user-owned broker connection. Never mix candidates, orders or trades across broker connections.
5. A missing/ambiguous local match is not a reason to submit or re-submit. Keep the broker observation unmatched and visible for later/manual resolution.
6. Never infer a fill from order status alone. Individual broker trade IDs are the source of truth for execution quantity and price.
7. Never automatically overwrite portfolio positions, cash, P&L, `Order` or `Execution` accounting in this worker. That is a separate reviewed phase.
8. Worker failure must not change trading mode or live-submit flags.

## Proposed flow

1. Claim a reconciliation job/lease for one broker connection using a database compare-and-set or equivalent safe lock. Do not hold a database transaction open while waiting on HTTP.
2. Validate that the connection belongs to the requested user, the broker is Upstox, and a usable token is available from the existing credential service. Do not invent a second credential storage path.
3. Call the documented read-only order-book endpoint. Validate HTTP status, content type, JSON envelope, response shape and page/window semantics before processing records.
4. Normalize each order with `normalize_upstox_order()`. Unknown status or malformed/economic fields become safe errors/manual review; they are never guessed into a terminal state.
5. Load candidate intents only for this exact broker connection. Use `match_broker_order_to_intent()`; require an existing broker order ID or one exact correlation tag plus all required economic fields. Ambiguous or mismatched records remain unmatched.
6. For a verified match, fetch per-order trades using the documented read-only trades endpoint. Normalize each with `normalize_upstox_trade()`; call `record_broker_fill()` with the stable broker trade ID. If no safe intent match exists, store the validated fill with no intent only when its connection scope is certain; otherwise quarantine it without linking.
7. Re-read the intent version and persisted fill quantity, then call `apply_reconciliation_transition()` with the normalized observed state and a minimal sanitized observation. Existing persisted fills take precedence over stale active/cancel status through `resolve_order_state_with_fill_evidence()`. Contradictions remain `RECONCILIATION_REQUIRED`.
8. Persist a job summary with counts (read, normalized, matched, unmatched, fills inserted, duplicate fills, conflicts, errors), safe error categories and completion time. Do not include tokens or raw response payloads.
9. Release the lease. If the process crashes, the next run may repeat GET calls safely; unique trade identity and idempotent state transitions must prevent duplicate local records/events.

## API behavior and recovery

- Use official Upstox docs as the contract source: [Order Book](https://upstox.com/developer/api-documentation/get-order-book/), [Order History](https://upstox.com/developer/api-documentation/get-order-history/), [Order Details](https://upstox.com/developer/api-documentation/get-order-details/), [Order Trades](https://upstox.com/developer/api-documentation/get-trades-by-order/), and [Order Status Appendix](https://upstox.com/developer/api-documentation/appendix/order-status/).
- Order book/history can be limited by trading-day availability. Persist every verified local observation and document how prior-day trades are checked through the official history endpoints; do not treat a missing current-day order as proof it never existed.
- 401/expired token: classify and stop the connection job; use only the existing approved credential refresh path if it is documented and testable. Never print token data.
- 403: stop and mark permission/account access error; do not loop.
- 429: bounded exponential backoff with jitter and respect `Retry-After` when valid. Bound requests per connection and per run.
- 5xx/network timeout: retry read-only GETs within a small bounded budget, then mark the job incomplete. Repeating GET is acceptable; this rule must never be reused for a broker submit.
- Malformed JSON/schema, unknown statuses, ambiguous match, reused trade ID with conflicting payload, over-quantity fills, and status/trade contradictions must be recorded as safe conflicts and surfaced for manual review.
- Use bounded pagination/batching. Avoid N+1 per-order trade requests where the API contract supports a safer batch strategy; otherwise cap requests and apply rate-limit handling.
- Avoid treating timestamps as globally ordered event versions. Compare current persisted version and cumulative deduplicated trade quantity, not just response arrival order.

## Implementation sequence

1. Introduce a narrow read-only client protocol and unit-tested adapter wrapper with explicit allowlisted methods. Contract fixtures must be based on current official response examples.
2. Implement a worker service with injected client, repository/session factory, clock and retry policy. No direct global app/session state and no long-lived DB transaction around network calls.
3. Add tests for successful reconciliation, repeated runs, expired token, 403, 429/Retry-After, bounded 5xx retry, malformed responses, duplicate order records, ambiguous tag, duplicate/conflicting trade IDs, out-of-order order/trade observations, partial-fill/cancel races, worker lease contention, and restart after each persistence boundary.
4. Run backend tests plus PostgreSQL 16 concurrency and reversible migrations. Test with mocks/recorded fixtures first. If sandbox credentials become available, run a read-only sandbox check only after explicit approval; do not submit a test order.
5. Update audit, architecture, roadmap and progress with exact commits and green CI. Only then consider the next separate phase: reconciling broker trades into accounting models under its own design and tests.

## Exit criteria

- Worker cannot call broker write methods by construction.
- Every job is single-connection scoped and safe under duplicate runs/concurrent workers.
- Fill IDs are deduplicated; conflicts and unmatched data are visible and recoverable.
- Stale status cannot erase known trade evidence.
- Credentials and raw sensitive bodies never enter logs/audit.
- CI is green and evidence distinguishes mocked tests from any sandbox/staging verification.

No worker, real API read, production migration, accounting update or order action is implemented by this document.
