#!/usr/bin/env python3
"""
scripts/isolated_snapshot_controller.py

Standard-library controller for launching isolated snapshot science workers.
Enforces clean environment boundaries, locked snapshot venv isolation,
strict 53-file pre/post closed inventory verification, output path containment,
and child process exit-code fail-closed attestation.

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
EXPECTED_SNAPSHOT_GIT_COMMIT = "b69a6909acda4c7588744acc7e1d6c20bfce2612"
EXPECTED_ANALYSIS_SOURCE_SHA256 = "f85d7f7373e825dcc7171ce4491fd15c6fb755955da245041783fe317bc80351"

SENSITIVE_ENV_SUBSTRINGS = (
    "KEY",
    "TOKEN",
    "SECRET",
    "PASSWORD",
    "AUTH",
    "CREDENTIAL",
    "API",
)

FORBIDDEN_ENV_KEYS = {
    "PYTHONPATH",
    "PYTHONHOME",
    "VIRTUAL_ENV",
}


def resolve_snapshot_python(snapshot_root: Path) -> Path:
    """
    Find the dedicated virtual environment Python executable in snapshot_root.
    Preserves virtualenv invocation path rather than resolving symlinks to system Python.
    """
    candidates = [
        snapshot_root / ".venv" / "Scripts" / "python.exe",
        snapshot_root / ".venv" / "bin" / "python",
    ]
    for c in candidates:
        if c.is_file():
            return c.absolute()
    raise FileNotFoundError(
        f"Could not locate frozen virtual environment python in {snapshot_root}. "
        "Did you run 'uv sync --frozen' in the snapshot directory?"
    )


def compute_closed_snapshot_inventory(snapshot_root: Path) -> Tuple[str, Dict[str, str]]:
    """
    Compute exact closed 53-file path-to-SHA256 mapping and canonical digest using pure standard library.
    Excludes pyc, __pycache__, and .pytest_cache.
    """
    patterns = (
        "src",
        "prompts",
        "config/model.json",
        "config/pricing_v1.json",
        "config/retrieval.json",
        "pyproject.toml",
        "uv.lock",
        ".python-version",
    )
    mapping: Dict[str, str] = {}
    for item in sorted(patterns):
        p = snapshot_root / item
        paths = [p] if p.is_file() else sorted(p.rglob("*")) if p.is_dir() else []
        for q in paths:
            if (
                q.is_file()
                and not q.name.endswith(".pyc")
                and "__pycache__" not in q.parts
                and ".pytest_cache" not in q.parts
            ):
                rel = q.relative_to(snapshot_root).as_posix()
                mapping[rel] = hashlib.sha256(q.read_bytes()).hexdigest()

    canonical_json = json.dumps(
        mapping, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")
    manifest_sha = hashlib.sha256(canonical_json).hexdigest()
    return manifest_sha, mapping


def compute_quick_snapshot_fingerprint(snapshot_root: Path) -> str:
    """Backward compatibility helper: returns canonical 53-file manifest SHA256."""
    sha, _ = compute_closed_snapshot_inventory(snapshot_root)
    return sha


def verify_snapshot_git_identity(snapshot_root: Path) -> str:
    """
    Verify that snapshot_root is a clean git repository at exact expected commit b69a690.
    Fails closed if .git is missing, commit differs, or working directory is dirty.
    """
    git_dir = snapshot_root / ".git"
    if not git_dir.exists():
        raise RuntimeError(f"Snapshot root '{snapshot_root}' is missing .git directory or reference file!")

    cmd_head = ["git", "-C", str(snapshot_root), "rev-parse", "HEAD"]
    p_head = subprocess.run(cmd_head, capture_output=True, text=True)
    if p_head.returncode != 0:
        raise RuntimeError(f"Failed to get git commit for {snapshot_root}: {p_head.stderr.strip()}")
    actual_head = p_head.stdout.strip()
    if actual_head != EXPECTED_SNAPSHOT_GIT_COMMIT:
        raise RuntimeError(
            f"Snapshot Git commit mismatch: expected {EXPECTED_SNAPSHOT_GIT_COMMIT}, got {actual_head}"
        )

    cmd_status = ["git", "-C", str(snapshot_root), "status", "--porcelain=v1"]
    p_status = subprocess.run(cmd_status, capture_output=True, text=True)
    if p_status.returncode != 0:
        raise RuntimeError(f"Failed to check git status for {snapshot_root}: {p_status.stderr.strip()}")
    status_output = p_status.stdout.strip()
    if status_output:
        raise RuntimeError(
            f"Snapshot working directory is dirty! git status:\n{status_output}"
        )
    return actual_head


def validate_output_path_containment(output_path: Path, snapshot_root: Path) -> Path:
    """
    Ensure output_path does NOT reside within snapshot_root or overwrite
    the controller or worker control scripts.
    """
    resolved_out = output_path.resolve()
    resolved_snap = snapshot_root.resolve()
    worker_script = (Path(__file__).parent / "isolated_snapshot_worker.py").resolve()
    controller_script = Path(__file__).resolve()

    try:
        resolved_out.relative_to(resolved_snap)
        raise ValueError(
            f"SECURITY REJECTION: output_path '{resolved_out}' is inside snapshot root '{resolved_snap}'! "
            "Output files must never be written inside the protected snapshot."
        )
    except ValueError as e:
        if "SECURITY REJECTION" in str(e):
            raise

    if resolved_out == controller_script or resolved_out == worker_script:
        raise ValueError(
            f"SECURITY REJECTION: output_path '{resolved_out}' targets control script itself!"
        )

    return resolved_out


def sanitize_environment(extra_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Build strictly sanitized environment.
    Strips PYTHONPATH, PYTHONHOME, and all sensitive variables containing KEY, TOKEN, SECRET,
    PASSWORD, AUTH, CREDENTIAL, or API.
    Filters extra_env through the same strict denial filter before and after merge.
    """
    clean_env = os.environ.copy()

    def _scrub(d: Dict[str, str]) -> None:
        for k in list(d.keys()):
            upper_k = k.upper()
            if k in FORBIDDEN_ENV_KEYS or upper_k in FORBIDDEN_ENV_KEYS:
                d.pop(k, None)
                continue
            for pattern in SENSITIVE_ENV_SUBSTRINGS:
                if pattern in upper_k:
                    d.pop(k, None)
                    break

    _scrub(clean_env)

    if extra_env:
        filtered_extra = dict(extra_env)
        _scrub(filtered_extra)
        clean_env.update(filtered_extra)

    _scrub(clean_env)

    clean_env["PYTHONNOUSERSITE"] = "1"
    clean_env["OFFLINE_GUARD"] = "1"
    return clean_env


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
    Enforces pre/post 53-file closed inventory, clean environment, output containment,
    and process exit-code fail-closed validation.
    """
    snapshot_root = snapshot_root.resolve()
    if not snapshot_root.is_dir():
        raise FileNotFoundError(f"Snapshot root does not exist: {snapshot_root}")

    # Validate output path containment before touching filesystem
    validate_output_path_containment(output_path, snapshot_root)

    # Validate python interpreter
    if override_python is not None:
        override_resolved = Path(override_python).resolve()
        venv_dir = snapshot_root / ".venv"
        if venv_dir.is_dir():
            expected_python = resolve_snapshot_python(snapshot_root)
            if override_resolved != expected_python.resolve():
                raise ValueError(
                    f"REJECTED: Arbitrary override_python '{override_python}' is outside snapshot venv!\n"
                    f"  Snapshot venv python: {expected_python}"
                )
            python_exe = expected_python
        else:
            python_exe = override_resolved
    else:
        python_exe = resolve_snapshot_python(snapshot_root)

    worker_script = (Path(__file__).parent / "isolated_snapshot_worker.py").resolve()
    if not worker_script.is_file():
        raise FileNotFoundError(f"Missing worker script: {worker_script}")

    # Compute closed 53-file inventory before execution
    pre_sha, pre_inventory = compute_closed_snapshot_inventory(snapshot_root)
    if len(pre_inventory) != EXPECTED_CORE_FILES_COUNT:
        raise RuntimeError(
            f"Snapshot core inventory count mismatch: expected {EXPECTED_CORE_FILES_COUNT}, got {len(pre_inventory)}"
        )
    if pre_sha != EXPECTED_CORE_MANIFEST_SHA256:
        raise RuntimeError(
            f"Snapshot core manifest hash mismatch: expected {EXPECTED_CORE_MANIFEST_SHA256}, got {pre_sha}"
        )

    # Check git clean identity if .git is present
    git_dir = snapshot_root / ".git"
    if git_dir.exists():
        verify_snapshot_git_identity(snapshot_root)

    clean_env = sanitize_environment(extra_env)

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

    # Post-execution closed 53-file inventory verification (immutability check)
    post_sha, post_inventory = compute_closed_snapshot_inventory(snapshot_root)
    immutability_ok = (pre_inventory == post_inventory and pre_sha == post_sha)
    if not immutability_ok:
        raise RuntimeError("CRITICAL: Snapshot immutability violated during task execution!")

    if not output_path.is_file():
        raise RuntimeError(
            f"Worker failed to write output JSON! Exit code: {proc.returncode}\n"
            f"STDOUT:\n{proc.stdout}\n"
            f"STDERR:\n{proc.stderr}"
        )

    with open(output_path, "r", encoding="utf-8") as f:
        worker_output = json.load(f)

    # Fail closed on process exit code vs reported status
    if proc.returncode != 0:
        if worker_output.get("status") == "PASS":
            raise RuntimeError(
                f"Worker process exited with non-zero code {proc.returncode} but claimed PASS in JSON payload.\n"
                f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
            )

    # Fail closed on unblocked egress
    if worker_output.get("status") == "PASS":
        if worker_output.get("attempted_egress_count", 0) != 0:
            raise RuntimeError(
                f"Worker reported status PASS but attempted_egress_count is {worker_output.get('attempted_egress_count')}"
            )
        if "code_manifest_sha256" in worker_output and worker_output["code_manifest_sha256"] != EXPECTED_CORE_MANIFEST_SHA256:
            raise RuntimeError(
                f"Worker reported PASS but code manifest SHA mismatch: {worker_output.get('code_manifest_sha256')}"
            )

    worker_output["controller_attestation"] = {
        "snapshot_root": str(snapshot_root.as_posix()),
        "python_executable": str(python_exe.as_posix()),
        "task": task,
        "pre_fingerprint": pre_sha,
        "post_fingerprint": post_sha,
        "exit_code": proc.returncode,
        "immutability_verified": immutability_ok,
        "stdout": proc.stdout[:1000],
        "stderr": proc.stderr[:1000],
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
        if res.get("status") == "PASS" and res.get("controller_attestation", {}).get("exit_code") == 0:
            print(f"PASS: Isolated snapshot task '{args.task}' succeeded.")
            print(f"Status: {res.get('status')}")
            print(f"Report written to: {args.output}")
            return 0
        else:
            print(
                f"FAIL: Isolated snapshot task '{args.task}' returned status {res.get('status')} "
                f"with exit code {res.get('controller_attestation', {}).get('exit_code')}",
                file=sys.stderr,
            )
            return 1
    except Exception as exc:
        print(f"CONTROLLER ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
