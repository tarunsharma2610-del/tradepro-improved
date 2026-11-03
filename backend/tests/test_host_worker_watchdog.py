import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import subprocess


MODULE_PATH = Path(__file__).resolve().parents[2] / "ops" / "worker_watchdog.py"
SPEC = importlib.util.spec_from_file_location("tradepro_worker_watchdog", MODULE_PATH)
watchdog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(watchdog)


def test_worker_state_reports_running_and_restart_count(monkeypatch):
    calls = [
        SimpleNamespace(returncode=0, stdout="container-123\n"),
        SimpleNamespace(returncode=0, stdout="running 4\n"),
    ]
    monkeypatch.setattr(watchdog.subprocess, "run", Mock(side_effect=calls))

    assert watchdog.worker_state() == (
        "running", "running:1/1:running:4", "worker fleet running=1/1; non_running=0; restart_counts=4"
    )


def test_worker_state_reports_missing_container(monkeypatch):
    monkeypatch.setattr(
        watchdog.subprocess, "run",
        Mock(return_value=SimpleNamespace(returncode=0, stdout="")),
    )
    assert watchdog.worker_state() == (
        "missing", "missing", "worker containers are absent"
    )


def test_worker_state_fails_closed_when_docker_is_unavailable(monkeypatch):
    monkeypatch.setattr(
        watchdog.subprocess, "run",
        Mock(side_effect=FileNotFoundError("docker")),
    )
    assert watchdog.worker_state() == (
        "unknown", "unknown", "Docker Compose inspection unavailable"
    )


def test_main_notifies_only_on_state_or_restart_count_transition(monkeypatch, tmp_path):
    state_file = tmp_path / "state" / "last-state"
    monkeypatch.setattr(watchdog, "STATE_FILE", state_file)
    observe = Mock(side_effect=[
        ("running", "running:1/1:running:0", "worker running"),
        ("running", "running:1/1:running:0", "worker running"),
        ("running", "running:1/1:running:1", "worker restarted once"),
    ])
    notify = Mock(return_value=True)
    monkeypatch.setattr(watchdog, "worker_state", observe)
    monkeypatch.setattr(watchdog, "_notify", notify)

    assert watchdog.main() == 0
    assert state_file.read_text() == "running:1/1:running:0\n"
    assert watchdog.main() == 0
    assert watchdog.main() == 0
    assert state_file.read_text() == "running:1/1:running:1\n"
    assert notify.call_count == 2


def test_main_retries_transition_after_webhook_delivery_failure(monkeypatch, tmp_path):
    state_file = tmp_path / "state" / "last-state"
    monkeypatch.setattr(watchdog, "STATE_FILE", state_file)
    monkeypatch.setattr(watchdog, "WEBHOOK_URL", "https://alerts.example.invalid/hook")
    monkeypatch.setattr(
        watchdog, "worker_state",
        Mock(return_value=("down", "down:0/1:exited:1", "worker fleet down")),
    )
    notify = Mock(side_effect=[False, True])
    monkeypatch.setattr(watchdog, "_notify", notify)

    assert watchdog.main() == 1
    assert not state_file.exists()
    assert watchdog.main() == 1
    assert state_file.read_text() == "down:0/1:exited:1\n"
    assert notify.call_count == 2


def test_notify_returns_false_when_https_webhook_fails(monkeypatch, capsys):
    monkeypatch.setattr(watchdog, "WEBHOOK_URL", "https://alerts.example.invalid/secret-token")
    monkeypatch.setattr(
        watchdog.urllib.request, "urlopen",
        Mock(side_effect=TimeoutError("request timed out")),
    )

    assert watchdog._notify("down", "worker stopped") is False
    captured = capsys.readouterr()
    assert "TimeoutError" in captured.err
    assert "secret-token" not in captured.out + captured.err


def test_notify_treats_journal_as_destination_when_webhook_is_unconfigured(monkeypatch):
    monkeypatch.setattr(watchdog, "WEBHOOK_URL", "")
    assert watchdog._notify("running", "worker healthy") is True


def test_webhook_rejects_non_https_url(monkeypatch, capsys):
    monkeypatch.setattr(watchdog, "WEBHOOK_URL", "http://example.invalid/hook")
    urlopen = Mock()
    monkeypatch.setattr(watchdog.urllib.request, "urlopen", urlopen)

    watchdog._notify("down", "worker container stopped")

    urlopen.assert_not_called()
    assert "must use HTTPS" in capsys.readouterr().err


def test_worker_state_checks_every_compose_replica_including_stopped(monkeypatch):
    calls = [
        SimpleNamespace(returncode=0, stdout="worker-a\nworker-b\n"),
        SimpleNamespace(returncode=0, stdout="running 2\nexited 5\n"),
    ]
    run = Mock(side_effect=calls)
    monkeypatch.setattr(watchdog.subprocess, "run", run)

    assert watchdog.worker_state() == (
        "degraded",
        "degraded:1/2:exited:5,running:2",
        "worker fleet running=1/2; non_running=1; restart_counts=2,5",
    )
    assert run.call_args_list[0].args[0][5:7] == ["--all", "-q"]
    assert run.call_args_list[1].args[0][-2:] == ["worker-a", "worker-b"]


def test_worker_state_reports_down_when_all_replicas_are_stopped(monkeypatch):
    calls = [
        SimpleNamespace(returncode=0, stdout="worker-a\nworker-b\n"),
        SimpleNamespace(returncode=0, stdout="exited 1\ncreated 0\n"),
    ]
    monkeypatch.setattr(watchdog.subprocess, "run", Mock(side_effect=calls))

    state, fingerprint, detail = watchdog.worker_state()
    assert state == "down"
    assert fingerprint.startswith("down:0/2:")
    assert "running=0/2" in detail


def test_worker_state_fails_closed_when_inspect_omits_a_replica(monkeypatch):
    calls = [
        SimpleNamespace(returncode=0, stdout="worker-a\nworker-b\n"),
        SimpleNamespace(returncode=0, stdout="running 0\n"),
    ]
    monkeypatch.setattr(watchdog.subprocess, "run", Mock(side_effect=calls))

    assert watchdog.worker_state() == (
        "unknown", "unknown", "Docker returned an invalid worker fleet state"
    )


def _docker_compose_available():
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def test_real_compose_worker_replica_kill_and_recovery(monkeypatch, tmp_path):
    """Exercise the host watchdog against two real Compose containers."""
    import os
    import time
    import uuid

    import pytest

    if not _docker_compose_available():
        pytest.skip("Docker Compose is unavailable in this environment")

    compose_file = tmp_path / "watchdog-compose.yml"
    compose_file.write_text(
        """
services:
  worker:
    image: busybox:1.36
    command: ["sh", "-c", "while true; do sleep 1; done"]
    restart: "no"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    project_name = f"watchdog-test-{uuid.uuid4().hex[:12]}"
    monkeypatch.setenv("COMPOSE_PROJECT_NAME", project_name)
    monkeypatch.setattr(watchdog, "COMPOSE_FILE", compose_file)

    def compose(*args):
        result = subprocess.run(
            ["docker", "compose", "-f", str(compose_file), *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            env=os.environ.copy(),
        )
        assert result.returncode == 0, result.stderr
        return result

    def wait_for_state(expected):
        deadline = time.monotonic() + 20
        last = None
        while time.monotonic() < deadline:
            last = watchdog.worker_state()
            if last[0] == expected:
                return last
            time.sleep(0.2)
        pytest.fail(f"watchdog did not report {expected}; last state={last}")

    try:
        compose("up", "-d", "--scale", "worker=2")
        running = wait_for_state("running")
        assert "running=2/2" in running[2]

        worker_ids = compose("ps", "-q", "worker").stdout.splitlines()
        assert len(worker_ids) == 2

        killed = subprocess.run(
            ["docker", "kill", worker_ids[0]],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert killed.returncode == 0, killed.stderr
        degraded = wait_for_state("degraded")
        assert "running=1/2" in degraded[2]

        killed = subprocess.run(
            ["docker", "kill", worker_ids[1]],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert killed.returncode == 0, killed.stderr
        down = wait_for_state("down")
        assert "running=0/2" in down[2]

        compose("up", "-d", "--scale", "worker=2")
        recovered = wait_for_state("running")
        assert "running=2/2" in recovered[2]
    finally:
        compose("down", "--volumes", "--remove-orphans")
