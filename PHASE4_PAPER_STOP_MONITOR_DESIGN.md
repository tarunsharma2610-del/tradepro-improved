# Phase 4 — PAPER Quote-Driven Stop Monitor Design Audit

Date: 30 October 2026
Repository: `tarunsharma2610-del/tradepro-improved`
Implementation branch: `phase4/redis-market-data-publisher`
Status: design gate only; no quote-driven order trigger has been enabled.

## Verified baseline

- Exact code/test head: `d6fd555d17faa02beff229a04acd3dfcd4cf86c5`.
- Backend CI #41076913522 passed on that exact SHA: https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41076913522
- PR #9 remains open, Draft and unmerged; target branch `phase4/roadmap-progress-checkpoints`.
- PAPER mode only. Live broker order submission/modification/cancellation remains disabled.
- Scanner observations are held in process memory, keyed by (user_id, instrument_key), and expire after 15 seconds based on local monotonic receive time.
- Redis quote consumer callback currently calls `MarketScanner.process_quote`; it is synchronous and performs no database/order work.
- Strategy worker runs candle-based evaluations every 300 seconds. It fetches 5-minute historical + intraday candles, checks candle freshness, computes indicators, then may use a fresh scanner LTP for a trailing-stop check.
- `ExecutionService.place_order` is the shared PAPER execution/accounting path. MARKET PAPER fills require a separate fresh Full Market Quotes V3 depth snapshot; LTPC WebSocket messages do not contain executable depth.

## Findings that block a safe tick-driven stop monitor

1. **No idempotency key for a stop event.** Repeated quote versions, Redis redelivery, callback retries, or two worker replicas could submit repeated exit orders unless a durable event claim is introduced.
2. **Strategy state is not locked by the current evaluator.** `StrategyExecutionService.evaluate` reads/writes `current_watermark` without a strategy-row lock. Portfolio locking inside order placement does not by itself prove that two stop callbacks cannot both decide to exit.
3. **Multiple strategies can share a portfolio/instrument.** Position quantity is portfolio+instrument scoped, while trailing-stop watermark is strategy scoped. Multiple strategies could each attempt to close the same shared position. The ownership/allocation rule must be explicit before automation.
4. **A quote is a trigger observation, not an execution price.** The LTPC quote must never be used to simulate a fill. A triggered exit must go through existing PAPER order execution, fresh depth, portfolio risk validation, virtual cash/position accounting and transaction-cost handling.
5. **The scanner's 15-second TTL is based on local receipt time.** It does not independently prove that the exchange timestamp is within an allowed age. The monitor must enforce both exchange timestamp and receive-time bounds, reject future/skewed timestamps, and bind epoch/version to a per-subscription lifecycle.
6. **Redis listener isolation and backpressure matter.** Do not perform slow DB or broker calls inside the quote callback. Do not spawn an unbounded async task for every tick. Use a bounded/coalescing queue keyed by user+instrument and explicit overflow metrics/fail-closed behavior.
7. **Reconnect/lease handoff can replay data.** Epoch changes, version resets, duplicate/out-of-order messages and stale consumers must not reuse old stop claims or create duplicate orders.
8. **Existing worker cadence is not real time.** A 300-second candle evaluation cannot be described as tick-by-tick stop monitoring. The new monitor must be an independent worker path and must not redownload candles on each quote.

## Required architecture before implementation

- Keep `MarketScanner.process_quote` as a fast validation/cache callback only.
- Publish accepted observations to a bounded, coalescing dispatcher keyed by (user_id, instrument_key); retain only the newest accepted (epoch, version) per key.
- Resolve active strategies by exact portfolio owner and instrument key; never use a global instrument-only lookup.
- Define one explicit position-exit ownership model for multiple strategies sharing a portfolio/instrument. Until then, fail closed for ambiguous shared-position ownership rather than allowing each strategy to independently liquidate it.
- Introduce durable stop-event idempotency, preferably a persisted event/claim with a unique key covering strategy (or position owner), subscription epoch and quote version. The claim and transition to an exit-in-progress state must be transactionally coordinated.
- Lock the authoritative strategy/position/portfolio rows in a consistent order. PostgreSQL concurrency tests must prove that two replicas cannot create duplicate exit orders for one stop event.
- Trigger only after a fresh, valid quote crosses the configured stop using the strategy's persisted watermark. Update watermark monotonically and transactionally; do not regress it on out-of-order ticks.
- Submit exits only through the existing PAPER `ExecutionService.place_order` path. WebSocket LTP is trigger-only; full-depth quote remains the execution input.
- If full-depth quote, analytics token, risk validation, accounting, or DB transaction fails, retain a recoverable state and do not mark the stop event complete. Define retry policy and alerting before release.
- Ensure no new code path can select LIVE mode or call broker order-write endpoints.

## Test gates (all required)

1. Quote freshness: receive-time TTL, exchange timestamp age, future timestamp/skew, invalid timestamp, missing timestamp, and exact 15-second boundary.
2. Ordering/lifecycle: duplicate version, lower version, epoch rotation, lease handoff, delayed old-epoch quote, reconnect and replay.
3. Isolation: wrong user, wrong instrument, inactive strategy, deleted strategy, portfolio ownership mismatch.
4. Multiple strategies: same user/instrument, same portfolio/instrument, different portfolios, explicit shared-position ownership, and no duplicate aggregate close.
5. Concurrency: simultaneous callbacks across two worker replicas on PostgreSQL 16; exactly one durable claim and at most one exit order.
6. Execution: LTPC never used as fill price; fresh depth required; risk checks, kill switch semantics, PAPER-only mode, fees, GST/IPFT accounting and position/cash ledgers unchanged.
7. Failure recovery: Redis outage, bounded queue overflow, DB outage, token expiry, depth quote failure, process restart after claim, process restart after order creation but before acknowledgement.
8. Regression: existing 5-minute indicator calculations and scheduled strategy evaluation unchanged; no repeated candle downloads per tick.

## Implementation decision

Do **not** implement tick-triggered exits by simply calling `StrategyExecutionService._exit` from the Redis callback. That would lack durable event idempotency, bounded dispatch, shared-position ownership and proven concurrency control. First implement and test the dispatcher/claim state machine and ownership policy; only then connect it to the existing PAPER execution service.

## Current completion state

- Scanner TTL, Redis worker lifecycle and first scanner-to-PAPER trailing-stop evaluation slice: implemented and CI-verified at the baseline above.
- True quote-driven/tick-by-tick PAPER stop monitor: not implemented; design and concurrency gates remain.
- Production deployment, sustained-load testing and credentialed Upstox smoke tests: deferred.
