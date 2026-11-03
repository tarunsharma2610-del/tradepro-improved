#!/usr/bin/env python3
"""Host-side watchdog for the Docker Compose worker container.

Runs outside the worker container (systemd timer). It observes Docker state
and emits transition-only journal messages. An optional HTTPS webhook can
forward alerts to an external monitoring/incident endpoint.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

COMPOSE_FILE = Path(os.environ.get("TRADEPRO_COMPOSE_FILE", "/opt/tradepro-improved/docker-compose.yml"))
STATE_FILE = Path(os.environ.get("TRADEPRO_WATCHDOG_STATE", "/var/lib/tradepro-watchdog/last-state"))
WEBHOOK_URL = os.environ.get("TRADEPRO_WATCHDOG_WEBHOOK_URL", "").strip()


def worker_state() -> tuple[str, str, str]:
    try:
        result = subprocess.run(
            ["docker", "compose", "-f", str(COMPOSE_FILE), "ps", "--all", "-q", "worker"],
            check=False, capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown", "unknown", "Docker Compose inspection unavailable"
    container_ids = result.stdout.strip().splitlines()
    if result.returncode != 0:
        return "unknown", "unknown", "Docker Compose inspection failed"
    if not container_ids:
        return "missing", "missing", "worker containers are absent"
    try:
        inspected = subprocess.run(
            [
                "docker", "inspect", "--format",
                "{{.State.Status}} {{.RestartCount}}", *container_ids,
            ],
            check=False, capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown", "unknown", "Docker worker inspection unavailable"
    if inspected.returncode != 0:
        return "unknown", "unknown", "Docker inspection failed"

    rows = [line.split() for line in inspected.stdout.splitlines() if line.strip()]
    if len(rows) != len(container_ids) or any(
        len(row) != 2 or not row[1].isdigit() for row in rows
    ):
        return "unknown", "unknown", "Docker returned an invalid worker fleet state"

    states = [(row[0], int(row[1])) for row in rows]
    running_count = sum(status == "running" for status, _ in states)
    total_count = len(states)
    restart_counts = ",".join(str(count) for count in sorted(count for _, count in states))
    if running_count == total_count:
        state = "running"
    elif running_count == 0:
        state = "down"
    else:
        state = "degraded"
    fingerprint_states = ",".join(
        f"{status}:{count}" for status, count in sorted(states)
    )
    fingerprint = f"{state}:{running_count}/{total_count}:{fingerprint_states}"
    detail = (
        f"worker fleet running={running_count}/{total_count}; "
        f"non_running={total_count - running_count}; restart_counts={restart_counts}"
    )
    return state, fingerprint, detail


def _notify(state: str, detail: str) -> bool:
    """Emit to the journal and return whether configured webhook delivery succeeded."""
    message = f"Tradepro Improved host watchdog: worker {state}. {detail}"
    print(message, flush=True)
    if not WEBHOOK_URL:
        return True
    if not WEBHOOK_URL.startswith("https://"):
        print("Watchdog webhook must use HTTPS; notification was not forwarded.", file=sys.stderr)
        return False
    request = urllib.request.Request(
        WEBHOOK_URL,
        data=json.dumps({"text": message, "service": "tradepro-improved-worker", "state": state}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            if not 200 <= response.status < 300:
                print("Watchdog webhook returned a non-success status.", file=sys.stderr)
                return False
            return True
    except Exception as exc:
        # Never print the URL or exception text; URLs may contain credentials.
        print(f"Watchdog webhook delivery failed ({type(exc).__name__}).", file=sys.stderr)
        return False


def main() -> int:
    state, fingerprint, detail = worker_state()
    try:
        previous = STATE_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        previous = ""
    except OSError:
        previous = ""
    if fingerprint != previous:
        delivered = _notify(state, detail)
        if delivered:
            try:
                STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
                temporary = STATE_FILE.with_suffix(".tmp")
                temporary.write_text(fingerprint + "\n", encoding="utf-8")
                temporary.replace(STATE_FILE)
            except OSError:
                print("Watchdog could not persist transition state.", file=sys.stderr)
    return 0 if state == "running" else 1


if __name__ == "__main__":
    raise SystemExit(main())
