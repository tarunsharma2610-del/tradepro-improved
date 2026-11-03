# Phase 4 — PAPER operational alerting

Date: 3 November 2026
Repository: `tarunsharma2610-del/tradepro-improved`
Implementation branch: `phase4/operational-alerting`
PR: #12 — Draft/unmerged

## Scope

A worker-side monitor polls the shared Redis market-data fleet metrics. Alerts are aggregate-only, PAPER-labelled, best-effort side effects and are not part of order execution, risk checks, or accounting.

## Implemented alert conditions

- Any positive delta in dropped unique market-data observations.
- Any positive delta in exhausted dispatch retries.
- Five or more handler failures during a monitoring interval.
- Twenty-five or more rejected observations during a monitoring interval.
- No active metrics-exporter heartbeat sustained for at least 60 seconds.
- Shared Redis market-data metrics unavailable.
- Recovery notification when a previously absent metrics-exporter heartbeat returns.

The monitor polls every 30 seconds by default. Repeated alert fingerprints are deduplicated across healthy Redis-connected replicas for a 300-second cooldown. If Redis is unavailable, a process-local cooldown prevents repeated log/notification spam; this fallback does not promise cross-replica deduplication during a Redis outage.

## Delivery configuration

An administrator must configure both values through Settings → Platform:

- `telegram_bot_token`
- `ops_alert_telegram_chat_id`

The new chat-ID key is allowlisted in `KNOWN_PLATFORM_SETTING_KEYS`; both values use the existing encrypted platform-settings storage and masked API response. The chat ID is validated as a numeric Telegram destination before sending. No token, chat ID, user ID, or instrument key is included in alert text.

If credentials or destination are missing/invalid, the monitor logs that delivery is unavailable; it does not fail worker execution. Telegram delivery failures are handled without raising into the trading path. Telegram request details are not written to logs.

## Runtime integration

`backend/app/worker.py` starts the monitor as an independent asyncio task and cancels it during orderly worker shutdown. It runs alongside Redis quote consumption, dispatch workers, and durable PAPER stop-event recovery. Notification errors cannot roll back a fill or stop event.

## Tests

`backend/tests/test_operational_alert_service.py` covers metric deltas/thresholds, aggregate-only alert text, Telegram delivery and deduplication, invalid destination handling, and the 60-second missing-worker threshold.

## Verification boundary

The heartbeat signal counts metrics-exporter processes, not quote-dispatch workers independently. Because this monitor runs inside the worker container, it cannot report a complete crash of that same container; an external uptime/health watchdog is still required to detect total worker-process loss. This is implementation and automated-test coverage, not proof of live Telegram delivery or deployed operational readiness. After exact-head CI passes, configure a dedicated operations Telegram chat and perform a credentialed smoke test. Verify alerts and recovery on the deployed worker fleet, including Redis outage and multiple-replica behavior. Do not claim delivery is active until that smoke test succeeds.

## Remaining operational work

- Add a credentialed Telegram smoke test in the intended deployment.
- Verify Redis dedupe and fallback behavior with multiple worker replicas under fault injection.
- Run sustained-load and restart/recovery tests on PostgreSQL 16 + Redis with measured queue latency, drops, retries, worker restarts, and stop-event recovery.
- Define an on-call owner and escalation/acknowledgement process; Telegram delivery alone is not an incident-management system.
- Keep deployment secrets, Telegram bot token, and destination chat ID out of repository files and CI logs.

## Safety

PAPER mode remains mandatory. Live broker `place_order`, `modify_order`, and `cancel_order` writes remain disabled. This monitor does not call broker order-write APIs. Original `tarunsharma2610-del/Tradepro` is out of scope and untouched. PR #12 remains Draft/unmerged.


## Additional hardening from follow-up review

A code review identified a retryability issue: when Telegram credentials or the destination were missing, the alert's Redis cooldown key could remain for five minutes and suppress immediate delivery after an administrator corrected configuration. The monitor now releases that key when configuration is missing/invalid, allowing the next monitoring pass to retry.

Two additional tests cover:
- Two independent monitor instances sharing one Redis fake observe the same fleet delta but only one Telegram notification is sent (Redis NX deduplication).
- Missing Telegram configuration does not consume the cooldown; after settings are corrected, the same alert can be delivered immediately.

These tests are included in the latest backend CI run. Earlier green CI on commit `fb1d235a0bbbb2f44aca130130f6ea8704908c89` does not verify these follow-up changes. Current code head at the time of this document update: `4f7829a8019758b9eb0fc770dcae80d9cbb1c428`; exact-head CI must pass before this is a verified checkpoint.


## External host watchdog follow-up — 3 November 2026

A separate host-side watchdog has now been added because an in-process monitor cannot observe a complete worker-container crash:

- `ops/worker_watchdog.py` checks Docker Compose worker state and restart count.
- A systemd oneshot service and one-minute timer run outside the worker container.
- State transitions and Docker restart-count changes are written to the host journal; an optional HTTPS webhook can forward minimal alerts.
- The watchdog does not restart containers or interact with broker/order paths. Docker's existing restart policy remains responsible for restart.
- Tests are in `backend/tests/test_host_worker_watchdog.py`.

See `PHASE4_EXTERNAL_WATCHDOG.md` for installation and limitations. This is code and test coverage only; it has not been installed on the Oracle VM. VM/Docker daemon/systemd failure still requires cloud-provider instance monitoring and an independent notification route. A one-minute poll may miss brief failures that recover without incrementing Docker restart count.


## Real Redis multi-client alert deduplication — 3 November 2026

Added an integration test in `backend/tests/test_operational_alert_service.py` that uses the CI-provided `REDIS_TEST_URL` service and two independent Redis clients. Both clients concurrently attempt to claim the same unique alert fingerprint through Redis `SET NX EX`; the test requires exactly one successful claim and exactly one Telegram send. The test is skipped only when the dedicated Redis integration URL is absent (local environments without Redis); the backend CI workflow provisions Redis 7 and sets this URL.

This strengthens the previous in-memory fake test but remains a focused atomic-deduplication integration test, not a full multi-process deployment or Telegram network smoke test. Real Telegram delivery and multi-container fault injection remain deployment gates. Exact-head Backend and Security CI are required for this test and the subsequent documentation sync.


## PostgreSQL recovery-sweeper fault-window coverage — 3 November 2026

Added `test_postgres_recovery_sweeper_resumes_expired_executing_worker` to `backend/tests/test_paper_stop_event_claim_postgres_concurrency.py`. It uses the CI PostgreSQL 16 service, persists an EXECUTING stop-event claim with an expired lease (representing loss of the original worker after its transaction closed), invokes the actual `recover_expired_paper_stop_events_once` sweeper without Redis redelivery, verifies the old claim token is replaced, and completes the event using the replacement token. It asserts the durable row is COMPLETED with attempt_count=2. The execution service's broker-facing method is stubbed at the boundary so this recovery test exercises database lifecycle orchestration without any broker or order-write call.

This is a PostgreSQL-backed recovery-sweeper integration test, not an OS-level SIGKILL of a worker process or a full end-to-end fill test. The earlier PostgreSQL concurrency tests continue to cover duplicate execution, indicator-vs-stop exit, concurrent expired-lease reclaim, stale-token fencing, and retry exhaustion. Corrected a stale model docstring that incorrectly said workers did not create stop events.

Exact-head Backend and Security CI are required for this change and the final documentation sync. Do not infer a green result from the previous checkpoint.


Follow-up test-harness correction: the stubbed `execute_claimed` method now uses an instance-method-compatible signature, so the PostgreSQL recovery-sweeper test exercises the handler call shape correctly. This creates a new exact-head CI requirement; previous runs on earlier commits do not verify this final correction.


## PostgreSQL recovery verification update — 3 November 2026

- Backend CI run [#41659743611](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41659743611) and Security analysis [#41659743654](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41659743654) both PASSED on exact commit `319cf01dedd3b8bb861d6d60f010f96b08e9697e`.
- Backend and Security results above validate the lease-timeline harness correction, but do not validate subsequent commits.
- Added an explicit PostgreSQL integration assertion that the original worker's claim token cannot complete the event after recovery and replacement-worker completion. This is committed as `794af153daa6d331d28a5e4aa7b3d3249de1a09e`.
- Exact-head Backend and Security CI for `794af153daa6d331d28a5e4aa7b3d3249de1a09e` and this documentation synchronization are required before declaring a verified checkpoint.
- Scope remains `tarunsharma2610-del/tradepro-improved` only. PAPER-only; live broker order writes disabled; PR #12 OPEN, Draft and unmerged; original `Tradepro` untouched.
- This DB-backed worker-loss simulation is not an OS-level SIGKILL or Oracle VM failure drill. External watchdog installation, real VM failure drill, sustained production-like load, and final security audit remain pending.
