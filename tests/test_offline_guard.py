"""Regression for swallowed network errors and inherited Python CLI guards."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

LAUNCHER = Path(__file__).resolve().parents[1] / "scripts" / "run_offline_tests.py"


def launch(code):
    return subprocess.run(
        [sys.executable, str(LAUNCHER), "-c", code],
        capture_output=True,
        text=True,
        check=False,
    )


def test_pure_python_runs_without_network():
    result = launch("assert 2 + 2 == 4")
    assert result.returncode == 0, result.stderr
    assert "installed=True attempted_egress=0" in result.stdout


def test_swallowed_network_attempt_still_fails_check():
    result = launch(
        "import socket\ntry:\n socket.create_connection(('192.0.2.1', 443))"
        "\nexcept Exception:\n pass"
    )
    assert result.returncode == 97
    assert "attempted_egress=1" in result.stdout


@pytest.mark.parametrize(
    "event",
    ["socket.gethostbyname", "socket.gethostbyaddr", "socket.getnameinfo"],
)
def test_swallowed_name_resolution_event_still_fails_check(event):
    # Python emits these distinct audit events for resolver calls. Raise the
    # event directly so a broken guard cannot accidentally issue a DNS query.
    result = launch(
        f"import sys\ntry:\n sys.audit({event!r}, 'localhost')"
        "\nexcept Exception:\n pass"
    )
    assert result.returncode == 97
    assert "attempted_egress=1" in result.stdout


def test_cli_subprocess_inherits_network_guard():
    result = launch(
        "import subprocess,sys\nsubprocess.run([sys.executable,'-c',"
        "\"import socket; socket.socket().connect(('192.0.2.1',443))\"])"
    )
    assert result.returncode == 97
    assert "attempted_egress=1" in result.stdout


def test_provider_credentials_are_not_inherited(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-sentinel")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-only-sentinel")
    result = launch(
        "import os; assert 'OPENAI_API_KEY' not in os.environ;"
        " assert 'ANTHROPIC_API_KEY' not in os.environ"
    )
    assert result.returncode == 0, result.stderr
    assert os.environ["OPENAI_API_KEY"] == "test-only-sentinel"
