## Current verified Phase 4 checkpoint — 3 November 2026

- Repository: `tarunsharma2610-del/tradepro-improved` only; implementation branch: `phase4/operational-alerting`.
- Verified implementation commit: `e4910f3c93d556bf2c7c7d71df4a6b9f045a1f36`.
- Backend CI [#41669605371 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41669605371): **1,650 passed, 8 warnings**; broker-write boundary guard passed; SQLite and PostgreSQL 16 migration round-trips passed; synthetic PostgreSQL/document-volume restore drill passed.
- Security analysis [#41669605381 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41669605381): CodeQL and Python dependency audit passed.
- Durable PAPER stop-event process recovery remains verified by `test_sigkilled_execution_worker_recovers_paper_stop_without_redis`: a separate worker process is killed after the production claim commit; PostgreSQL-only recovery completes the event, rejects the stale token, and leaves one filled PAPER order/execution, a flat position and one cash mutation.
- Host watchdog now enumerates all Compose worker containers with `docker compose ps --all -q worker`, inspects each container, and reports `running`, `degraded`, `down`, or `unknown` fleet state. Tests cover mixed running/stopped replicas, all-stopped replicas, incomplete inspection, and restart-count transitions. These are unit tests with mocked Docker responses; a real Docker Compose multi-container fault drill and Oracle VM installation remain pending.
- PR #12 remains **OPEN, Draft, and unmerged**. No merge or live broker order-write enablement is authorized.
- Safety remains mandatory: PAPER-only; live broker `place_order`, `modify_order`, and `cancel_order` writes disabled; original `tarunsharma2610-del/Tradepro` untouched.
- Remaining Phase 4 gates: real multi-container/replica failure injection; realistic sustained load using full database handler work (not just dispatcher throughput); Oracle VM watchdog installation and failure drill; independent cloud/VM monitoring; final independent security/penetration review. CI is not production-scale performance certification or deployment sign-off.

Historical checkpoint notes below are retained as history; this section supersedes older "next step", test-count, commit, and PR-number summaries.
# Phase 4 — external worker watchdog

Date: 3 November 2026
Repository: `tarunsharma2610-del/tradepro-improved`
Branch: `phase4/operational-alerting`
PR #12 remains Draft/unmerged.

## Why this is separate

The Telegram operational alert monitor runs inside the worker container. It cannot report the complete loss of that same container. The host-side watchdog runs independently under systemd and inspects Docker Compose state from the host.

## Files

- `ops/worker_watchdog.py`: standard-library-only host checker.
- `ops/systemd/tradepro-worker-watchdog.service`: hardened oneshot systemd service.
- `ops/systemd/tradepro-worker-watchdog.timer`: runs after boot and every minute.
- `ops/worker-watchdog.env.example`: optional HTTPS webhook configuration.
- `backend/tests/test_host_worker_watchdog.py`: tests running/missing/unavailable Docker states, transition deduplication, restart-count changes and HTTPS-only webhook enforcement.

## Behavior

- Checks the Compose `worker` service using the configured Compose file.
- Reports missing, stopped, uninspectable and running states.
- Tracks Docker restart count as part of its transition fingerprint. A worker restart is therefore reported even if Docker has already restarted it and it is running again at the next timer tick.
- Emits transition-only messages to stdout, captured by the systemd journal.
- Optionally posts a minimal JSON message to an administrator-configured HTTPS webhook. It never prints webhook URLs or exception details.
- Returns nonzero when the worker is not confirmed running. Docker's existing `restart: unless-stopped` policy remains responsible for restart; this watchdog does not restart or mutate containers.

## Installation on the deployment host

The following assumes the repository is deployed at `/opt/tradepro-improved`. Adjust the paths if the actual deployment directory differs.

1. Copy `ops/worker_watchdog.py` to `/opt/tradepro-improved/ops/worker_watchdog.py`.
2. Copy the service and timer units to `/etc/systemd/system/`.
3. Optionally copy `ops/worker-watchdog.env.example` to `/etc/tradepro/worker-watchdog.env`, set an HTTPS incident webhook, and restrict it to root (`chown root:root`, `chmod 600`). Do not store a Telegram bot token in this file.
4. Ensure the service's `TRADEPRO_COMPOSE_FILE` points to the deployed Compose file and the state directory `/var/lib/tradepro-watchdog` is writable by root.
5. Run `systemctl daemon-reload`, `systemctl enable --now tradepro-worker-watchdog.timer`, then `systemctl start tradepro-worker-watchdog.service`.
6. Inspect `systemctl status tradepro-worker-watchdog.timer` and `journalctl -u tradepro-worker-watchdog.service`.
7. In an isolated maintenance window, stop the worker container and verify a DOWN transition is emitted; start it again and verify a RUNNING/restart transition. Restore the worker immediately after the test.

## Important limits

- This is host-level Docker-state monitoring, not an external cloud monitor. If the VM, Docker daemon, host network, or systemd timer fails, it cannot send an alert. Use the cloud provider's VM/instance health monitoring and an independent notification destination for host-level failure.
- Without an HTTPS webhook, messages are only in the host journal; they are not automatically forwarded to Telegram or another operator.
- A one-minute timer can miss very short failures that begin and recover between checks; restart-count changes help detect Docker restarts that occurred between checks.
- A successful test suite does not mean this watchdog has been installed or exercised on the Oracle VM. Deployment smoke test remains required.
- The watchdog uses root to access Docker. Restrict access to the script, service, timer, environment file and host. Docker access is effectively host-root access.
- No broker API or order path is called.

## Safety

PAPER mode remains mandatory. Live broker `place_order`, `modify_order`, and `cancel_order` writes remain disabled. This watchdog only observes container state. Original `tarunsharma2610-del/Tradepro` is out of scope and untouched.


## Verified Docker Compose worker-fleet fault drill — 3 November 2026

Supersedes earlier statements that the real multi-container watchdog drill was pending.

- Exact implementation/test commit: `ff0a4b42a9a6aab021dffa10835b29d6228a93e4`.
- Backend workflow [#41671768895 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41671768895): **1,651 passed, 8 warnings, zero skipped**; broker-write boundary guard, SQLite/PostgreSQL 16 migration round-trips, and synthetic PostgreSQL/document-volume restore drill passed.
- Security workflow [#41671768838 — SUCCESS](https://github.com/tarunsharma2610-del/tradepro-improved/actions/runs/41671768838): CodeQL and Python dependency vulnerability audit passed.
- Zero skipped tests confirms `test_real_compose_worker_replica_kill_and_recovery` ran in hosted CI rather than taking its Docker-unavailable skip path.
- The test used two disposable BusyBox Compose workers: RUNNING (2/2), kill one → DEGRADED (1/2), kill second → DOWN (0/2), recreate both → RUNNING (2/2). Cleanup uses Compose down.
- This closes the hosted-CI multi-container watchdog test gap. It does not prove Oracle VM installation, host-level alert delivery, independent cloud monitoring, or production availability.

## Current state and next gate

- PR #12 remains OPEN, Draft, and unmerged. No merge or ready-for-review transition without explicit user approval.
- Only `tarunsharma2610-del/tradepro-improved` is in scope; original `tarunsharma2610-del/Tradepro` remains untouched.
- PAPER-only remains mandatory; live broker `place_order`, `modify_order`, and `cancel_order` writes remain disabled.
- Remaining gates: install/exercise the external watchdog on Oracle VM; verify an independent notification destination and cloud/instance health monitoring; run sustained load with full database-backed handler work and measure latency/recovery; complete independent security/penetration review.
- Do not duplicate the passing Docker Compose fault test or PostgreSQL SIGKILL stop-event recovery test. Inspect existing coverage before adding reliability work.
- The follow-up documentation commit requires its own exact-head Backend and Security CI before becoming a verified documentation checkpoint.
