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
