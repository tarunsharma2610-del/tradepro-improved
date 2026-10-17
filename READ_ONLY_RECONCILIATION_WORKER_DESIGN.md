# Read-only broker reconciliation worker — design and implementation gate

Status: worker implementation exists and is mocked-CI-tested; operational invocation and any real broker read remain gated. Reviewed 2026-10-17. Scope is the separate `tradepro-improved` repository. Live submission and cancellation remain disabled.

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

1. [x] Introduced `backend/app/brokers/upstox/reconciliation_client.py`, a fixed-path GET-only client for order book, details, history and per-order trades. Mocked contract tests verify endpoint paths, query parameters, sanitized failures and absence of order-write methods. [Run 39056868434](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39056868434) passed 309 tests, 1 warning. No network call to Upstox occurred.
2. [x] Implemented `backend/app/services/live_order_reconciliation_worker.py` with an injected read-only client, SQLAlchemy session, token provider override for tests, bounded retry policy and durable per-connection lease. No long-lived DB transaction is intentionally held across the two initial network reads.
3. [x] Added worker tests for successful reconciliation, repeated-run fill deduplication, expired/missing token, 403 without retry, 429/Retry-After, bounded 5xx retry, malformed response envelopes/data, cross-user rejection, lease contention, unmatched trades, and recovery from UNKNOWN when later trade evidence appears. Existing normalizer/repository tests cover ambiguous tags, duplicate/conflicting trade IDs, out-of-order status and partial-fill/cancel races. Remaining: broaden duplicate order record and crash-boundary coverage.
4. Run backend tests plus PostgreSQL 16 concurrency and reversible migrations. Test with mocks/recorded fixtures first. If sandbox credentials become available, run a read-only sandbox check only after explicit approval; do not submit a test order.
5. [ ] Continue updating audit, architecture, roadmap and progress with exact commits and green CI. The worker is not automatically scheduled or exposed through an API route. Next verify pagination/session-day semantics against current official docs and decide how to persist and expose run summaries/manual-review items. Accounting integration remains a separate reviewed phase.

## Exit criteria

- Worker cannot call broker write methods by construction.
- Every job is single-connection scoped and safe under duplicate runs/concurrent workers.
- Fill IDs are deduplicated; conflicts and unmatched data are visible and recoverable.
- Stale status cannot erase known trade evidence.
- Credentials and raw sensitive bodies never enter logs/audit.
- CI is green and evidence distinguishes mocked tests from any sandbox/staging verification.

The worker implementation is in `backend/app/services/live_order_reconciliation_worker.py`. It has only the read-only client injected and does not expose broker write operations. Tests use mocks: no real API read, production migration, accounting update or order action has occurred.


## Lease foundation checkpoint — 2026-10-17
`LiveReconciliationLease` and `LiveReconciliationLeaseRepository` are now implemented with Alembic revision `202610170003`. Claims are atomic and owner-scoped; expiry allows reclaim; renewal requires the current unexpired token; completion is token-guarded. [Run 39057273255](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39057273255) passed 318 tests, 1 warning, and SQLite/PostgreSQL 16 migration checks. The worker still does not exist or call the lease.


## Implementation checkpoint — 2026-10-17
- Worker commit: [`4ee8427`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/4ee8427f890f7c31021e30f7b36177e2f3f227c3).
- Latest test commit: [`bffeefc`](https://github.com/tarunsharma2610-del/tradepro-improved/commit/bffeefc7921fd96c8fbeab1b201eb3088e87f497); [run 39058734080](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39058734080) passed 338 tests, 1 warning, plus SQLite/PostgreSQL 16 reversible migration checks.
- The worker currently reads the order book and daily trades, not historical windows; it is not scheduled or wired to an endpoint. It writes fill identities and reconciliation state only, never local portfolio positions, cash, P&L or Order/Execution accounting.


## Durable run summaries implemented — 2026-10-17
`LiveReconciliationRun` + `LiveReconciliationRunRepository` persist a `RUNNING` row after lease acquisition and terminal status, start/completion times, safe error code and seven approved integer counters after the pass. The worker exposes `run_id` in its in-memory result. Raw broker records, tokens, headers and exception strings are never placed in the summary. Migration `202610170004` passed SQLite/PostgreSQL 16 upgrade/downgrade/re-upgrade in [run 39059271937](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059271937), which passed 340 tests, 1 warning. Remaining: durable manual-review issues, stale RUNNING recovery and crash/restart boundary tests.


## Manual-review issue persistence implemented — 2026-10-17
`LiveReconciliationIssue` and `LiveReconciliationIssueRepository` now persist a deduplicated issue row for malformed broker records, unmatched/ambiguous order matches, fill persistence/link failures and status-transition conflicts. Records are scoped to the connection owner and use allowlisted types, safe reason codes, normalized IDs, a fingerprint, occurrence counter and first/last-seen timestamps. They do not include raw broker rows, token data or exception text. Migration `202610170005` passed CI with 342 tests in [run 39059749652](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39059749652). This is not yet operator-facing: no API/UI or resolution endpoint exists. Next add a read-only issue listing and stale-run recovery only after API authorization design and tests.


## Read-only review listing endpoints — 2026-10-17
Added authenticated `GET /api/v1/reconciliation/runs` and `GET /api/v1/reconciliation/issues`. Queries are scoped to the authenticated user, filters are bounded and response schemas expose only safe summary/issue fields. No endpoint triggers the worker or changes issue status. Tests for authentication, cross-user isolation and filter validation passed in [run 39060230705](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/39060230705): 345 passed, 1 warning. Frontend review UI, issue-resolution workflow and stale-run recovery remain separate next steps.


## Review UI checkpoint — 2026-10-17
Added a dashboard-linked `/reconciliation` page that displays recent run summaries and manual-review issues through the authenticated read-only API. It filters issue status and allows refreshing, but cannot trigger a run or resolve issues. Commit `e4343dcb225c1f332b6c89399694d0a29a5df739` passed frontend TypeScript/Next.js checks and backend CI (345 passed, 1 warning). Next: stale-run recovery and crash-boundary tests, then historical trade API pagination/session-window work.
