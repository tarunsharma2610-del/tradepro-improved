# Phase 4 Sustained Dispatch Benchmark — 3 November 2026

## Verified checkpoint

- Repository: `tarunsharma2610-del/tradepro-improved` only.
- PR #10: OPEN, Draft, unmerged.
- Exact verified head: `edec040c5bb43ea572419345c5ecd50b76ab1c86`.
- Backend CI #41645265983: SUCCESS on the exact head.
- Security CI #41645266170: SUCCESS on the exact head; CodeQL and dependency audit passed.
- Backend pytest: 1,632 passed, 8 warnings.
- Broker-write boundary guard passed.

## Concurrent dispatcher smoke benchmark

The retained `dispatch-benchmark-results.json` artifact reports:

| Measurement | Result |
|---|---:|
| Observations processed | 5,000 |
| Concurrent workers | 8 |
| Bounded queue capacity | 512 |
| Elapsed time | 0.044279 seconds |
| Synthetic throughput | 112,920.26 observations/second |
| p50 enqueue-to-handler latency | 3.2393 ms |
| p95 enqueue-to-handler latency | 4.3143 ms |
| p99 enqueue-to-handler latency | 4.4683 ms |
| Backpressure retries/rejections | 21 / 21 |

All 5,000 observations were eventually accepted and processed; queue and in-flight state returned to zero. Backpressure retries are expected behavior under a bounded queue and are not equivalent to permanently lost accepted observations.

## Interpretation and limitations

This is a short, synthetic in-process dispatcher/worker smoke benchmark on a GitHub-hosted runner. It is useful as a regression baseline for this test shape only. It does NOT measure Upstox network ingestion, PostgreSQL persistence, scanner-to-execution end-to-end latency, long-duration memory behavior, production throughput, or Oracle VM capacity. Do not use the throughput figure as a production SLA or capacity claim.

A production-relevant benchmark still needs longer steady-state runs, realistic producer rates, realistic handler/database work, multiple user/instrument distributions, queue pressure/recovery, CPU/memory measurements and p50/p95/p99 end-to-end latency.

## Operational alerting status

The inspected deployment compose stack contains PostgreSQL, Redis, backend, worker, frontend and Nginx; it does not currently define Prometheus, Alertmanager or an independent notification service. The application exposes admin-only Redis-aggregated PAPER dispatch counters and a 60-second active-worker heartbeat window, but no independently delivered operational alerts are verified.

Initial alert design candidates (not production-approved thresholds): missing worker heartbeat >60 seconds; Redis unavailable for three consecutive probes; handler failure streak >=5; queue occupancy >80% for 60 seconds; stale quote beyond its configured freshness limit. Alert delivery must be independent of the worker being monitored and must have retry/persistent-failure handling.

## Remaining Phase 4 work

1. Implement and test independent alert delivery and alert failure recovery.
2. Complete endpoint-by-endpoint authorization/IDOR and cross-user isolation audit.
3. Continue multi-replica crash-window and sustained-load testing with realistic handler work.
4. Synchronize maintained project documentation and verify the exact documentation head with Backend and Security CI.
5. Complete the final Phase 4 audit. Do not claim LIVE readiness or production security certification.

## Safety

PAPER remains mandatory. Live broker `place_order`, `modify_order`, and `cancel_order` writes remain disabled. PR #9 and PR #10 remain Draft/unmerged. Original `tarunsharma2610-del/Tradepro` is out of scope and untouched.
