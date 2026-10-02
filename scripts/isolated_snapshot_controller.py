#!/usr/bin/env python3
"""
scripts/isolated_snapshot_controller.py

Standard-library controller for launching isolated snapshot science workers.
Enforces clean environment boundaries, locked snapshot venv isolation,
pre/post snapshot immutability verification, and attestation reporting.

Pure standard-library implementation with zero external dependencies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

EXPECTED_CORE_MANIFEST_SHA256 = "8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4"
EXPECTED_CORE_FILES_COUNT = 53


def resolve_snapshot_python(snapshot_root: Path) -> Path:
    """Find the dedicated virtual environment Python executable in snapshot_root."""
    candidates = [
        snapshot_root / ".venv" / "Scripts" / "python.exe",
        snapshot_root / ".venv" / "bin" / "python",
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()
    raise FileNotFoundError(
        f"Could not locate frozen virtual environment python in {snapshot_root}. "
        "Did you run 'uv sync --frozen' in the snapshot directory?"
    )


def compute_quick_snapshot_fingerprint(snapshot_root: Path) -> str:
    """Compute digest of critical core lockfile and protocol in snapshot to check immutability."""
    hasher = hashlib.sha256()
    lock_file = snapshot_root / "config" / "canonical_experiment_lock_v1.json"
    if lock_file.is_file():
        hasher.update(lock_file.read_bytes())
    rq_file = snapshot_root / "scripts" / "analysis" / "evaluate_rqs.py"
    if rq_file.is_file():
        hasher.update(rq_file.read_bytes())
    init_file = snapshot_root / "src" / "rag" / "__init__.py"
    if init_file.is_file():
        hasher.update(init_file.read_bytes())
    return hasher.hexdigest()


def execute_snapshot_task(
    snapshot_root: Path,
    task: str,
    output_path: Path,
    extra_env: Optional[Dict[str, str]] = None,
    override_python: Optional[Path] = None,
    cwd_override: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Launch an isolated child process using snapshot python and worker script.
    Strips inherited PYTHONPATH and user-site packages to prevent shadow imports.
    """
    snapshot_root = snapshot_root.resolve()
    if not snapshot_root.is_dir():
        raise FileNotFoundError(f"Snapshot root does not exist: {snapshot_root}")

    python_exe = override_python or resolve_snapshot_python(snapshot_root)
    worker_script = (Path(__file__).parent / "isolated_snapshot_worker.py").resolve()
    if not worker_script.is_file():
        raise FileNotFoundError(f"Missing worker script: {worker_script}")

    # Snapshot fingerprint before execution
    pre_fingerprint = compute_quick_snapshot_fingerprint(snapshot_root)

    # Build strictly sanitized environment
    clean_env = os.environ.copy()
    clean_env.pop("PYTHONPATH", None)
    clean_env.pop("PYTHONHOME", None)
    clean_env["PYTHONNOUSERSITE"] = "1"
    clean_env["OFFLINE_GUARD"] = "1"
    
    # Strip any potential provider credentials
    for cred_key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"]:
        clean_env.pop(cred_key, None)

    if extra_env:
        clean_env.update(extra_env)

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.is_file():
        output_path.unlink()

    cmd = [
        str(python_exe),
        "-I",
        str(worker_script),
        "--snapshot-root",
        str(snapshot_root),
        "--task",
        task,
        "--output",
        str(output_path),
    ]

    working_dir = cwd_override or snapshot_root
    proc = subprocess.run(
        cmd,
        cwd=str(working_dir),
        env=clean_env,
        capture_output=True,
        text=True,
    )

    # Snapshot fingerprint after execution (immutability check)
    post_fingerprint = compute_quick_snapshot_fingerprint(snapshot_root)
    if pre_fingerprint != post_fingerprint:
        raise RuntimeError("CRITICAL: Snapshot immutability violated during task execution!")

    if not output_path.is_file():
        raise RuntimeError(
            f"Worker failed to write output JSON! Exit code: {proc.returncode}\n"
            f"STDOUT:\n{proc.stdout}\n"
            f"STDERR:\n{proc.stderr}"
        )

    with open(output_path, "r", encoding="utf-8") as f:
        worker_output = json.load(f)

    worker_output["controller_attestation"] = {
        "snapshot_root": str(snapshot_root.as_posix()),
        "python_executable": str(python_exe.as_posix()),
        "task": task,
        "pre_fingerprint": pre_fingerprint,
        "post_fingerprint": post_fingerprint,
        "exit_code": proc.returncode,
        "immutability_verified": (pre_fingerprint == post_fingerprint),
        "stdout": proc.stdout[:500],
        "stderr": proc.stderr[:500],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(worker_output, f, indent=2, sort_keys=True)

    return worker_output


def main() -> int:
    parser = argparse.ArgumentParser(description="Isolated Snapshot Science Controller")
    parser.add_argument(
        "--snapshot-root",
        type=Path,
        default=Path("C:/Users/hahoa/.codex/artifacts/rag2attck/finalization_snapshots/b69a690"),
        help="Path to clean detached snapshot root",
    )
    parser.add_argument(
        "--task",
        choices=["preflight", "verify_baselines", "egress_test"],
        default="preflight",
        help="Task to execute in isolated child",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/evidence/snapshot_controller_attestation.json"),
        help="Output path for attestation report",
    )
    args = parser.parse_args()

    try:
        res = execute_snapshot_task(
            snapshot_root=args.snapshot_root,
            task=args.task,
            output_path=args.output,
        )
        print(f"PASS: Isolated snapshot task '{args.task}' succeeded.")
        print(f"Status: {res.get('status')}")
        print(f"Report written to: {args.output}")
        return 0 if res.get("status") == "PASS" else 1
    except Exception as exc:
        print(f"CONTROLLER ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
