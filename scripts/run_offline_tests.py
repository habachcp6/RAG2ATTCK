"""Run Python checks with inherited egress auditing and no provider credentials.

Example: python scripts/run_offline_tests.py -m pytest -m "not integration" -q
Python CLI subprocesses inherit the guard through PYTHONPATH. This is an
accidental-egress regression guard, not isolation against hostile native code
or a child deliberately disabling Python site initialization.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main(arguments: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if arguments is None else arguments)
    if not args:
        args = ["-m", "pytest", "-m", "not integration", "-q"]
    if args[0] not in {"-m", "-c"}:
        raise SystemExit(
            "Use -m <module> or -c <code>; isolated/no-site Python is forbidden"
        )
    env = {
        key: value
        for key, value in os.environ.items()
        if not any(
            word in key.upper() for word in ("API_KEY", "TOKEN", "SECRET", "PASSWORD")
        )
        and key.upper()
        not in {"GOOGLE_APPLICATION_CREDENTIALS", "AWS_SHARED_CREDENTIALS_FILE"}
    }
    guard = Path(__file__).resolve().parent / "offline_guard"
    env["PYTHONPATH"] = os.pathsep.join(
        str(item) for item in (guard, Path.cwd(), env.get("PYTHONPATH", "")) if item
    )
    env.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    with tempfile.TemporaryDirectory(prefix="rag2attck-offline-") as temporary:
        journal = Path(temporary) / "network-audit.txt"
        env["RAG2ATTCK_OFFLINE_JOURNAL"] = str(journal)
        completed = subprocess.run([sys.executable, *args], env=env, check=False)
        events = (
            journal.read_text(encoding="ascii").splitlines() if journal.exists() else []
        )
        attempts = sum(event.startswith("DENIED ") for event in events)
        started = any(event.startswith("START ") for event in events)
        print(
            f"OFFLINE_GUARD: installed={started} attempted_egress={attempts}",
            flush=True,
        )
        if not started or attempts:
            return 97
        return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
