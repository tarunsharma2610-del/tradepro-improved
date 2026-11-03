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


def worker_state() -> tuple[str, str]:
    result = subprocess.run(
        ["docker", "compose", "-f", str(COMPOSE_FILE), "ps", "-q", "worker"],
        check=False, capture_output=True, text=True, timeout=10,
    )
    container_id = result.stdout.strip().splitlines()
    if result.returncode != 0:
        return "unknown", "Docker Compose inspection failed"
    if not container_id:
        return "missing", "worker container is absent"
    inspected = subprocess.run(
        ["docker", "inspect", "--format", "{{.State.Status}} {{.RestartCount}}", container_id[0]],
        check=False, capture_output=True, text=True, timeout=10,
    )
    if inspected.returncode != 0:
        return "unknown", "Docker inspection failed"
    fields = inspected.stdout.strip().split()
    if len(fields) != 2:
        return "unknown", "Docker returned an invalid worker state"
    status, restart_count = fields
    if status != "running":
        return "down", f"worker container state is {status}"
    return "running", f"worker container running; restart_count={restart_count}"


def _notify(state: str, detail: str) -> None:
    message = f"Tradepro Improved host watchdog: worker {state}. {detail}"
    print(message, flush=True)
    if not WEBHOOK_URL:
        return
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
    except Exception as exc:
        # Never print the URL or exception text; URLs may contain credentials.
        print(f"Watchdog webhook delivery failed ({type(exc).__name__}).", file=sys.stderr)


def main() -> int:
    state, detail = worker_state()
    try:
        previous = STATE_FILE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        previous = ""
    except OSError:
        previous = ""
    if state != previous:
        _notify(state, detail)
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            temporary = STATE_FILE.with_suffix(".tmp")
            temporary.write_text(state + "\n", encoding="utf-8")
            temporary.replace(STATE_FILE)
        except OSError:
            print("Watchdog could not persist transition state.", file=sys.stderr)
    return 0 if state == "running" else 1


if __name__ == "__main__":
    raise SystemExit(main())
