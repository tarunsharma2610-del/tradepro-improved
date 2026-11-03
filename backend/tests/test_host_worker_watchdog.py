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
        "running", "running:4", "worker container running; restart_count=4"
    )


def test_worker_state_reports_missing_container(monkeypatch):
    monkeypatch.setattr(
        watchdog.subprocess, "run",
        Mock(return_value=SimpleNamespace(returncode=0, stdout="")),
    )
    assert watchdog.worker_state() == (
        "missing", "missing", "worker container is absent"
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
        ("running", "running:0", "worker running"),
        ("running", "running:0", "worker running"),
        ("running", "running:1", "worker restarted once"),
    ])
    notify = Mock()
    monkeypatch.setattr(watchdog, "worker_state", observe)
    monkeypatch.setattr(watchdog, "_notify", notify)

    assert watchdog.main() == 0
    assert state_file.read_text() == "running:0\n"
    assert watchdog.main() == 0
    assert watchdog.main() == 0
    assert state_file.read_text() == "running:1\n"
    assert notify.call_count == 2


def test_webhook_rejects_non_https_url(monkeypatch, capsys):
    monkeypatch.setattr(watchdog, "WEBHOOK_URL", "http://example.invalid/hook")
    urlopen = Mock()
    monkeypatch.setattr(watchdog.urllib.request, "urlopen", urlopen)

    watchdog._notify("down", "worker container stopped")

    urlopen.assert_not_called()
    assert "must use HTTPS" in capsys.readouterr().err
