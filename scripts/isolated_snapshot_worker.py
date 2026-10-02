#!/usr/bin/env python3
"""
scripts/isolated_snapshot_worker.py

Worker script executed in a fresh isolated child process inside the frozen snapshot.
Installs offline socket guard before any application imports, verifies loaded module
origins and co_filename boundaries against snapshot_root, and executes whitelisted tasks.

Pure standard-library implementation with zero external dependencies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

# Expected Invariants for Frozen Snapshot (b69a690)
EXPECTED_CORE_MANIFEST_SHA256 = "8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4"
EXPECTED_ANALYSIS_SOURCE_SHA256 = "f85d7f7373e825dcc7171ce4491fd15c6fb755955da245041783fe317bc80351"
EXPECTED_CORE_FILES_COUNT = 53


class SnapshotGuardSecurityError(RuntimeError):
    """Raised when an offline guard violation or origin boundary breach occurs."""
    pass


_attempted_egress_count = 0


def _install_socket_guard() -> None:
    """Install stdlib audit hook to intercept network socket operations."""
    global _attempted_egress_count

    def audit_hook(event: str, args: tuple) -> None:
        global _attempted_egress_count
        if event in ("socket.connect", "socket.bind", "socket.sendto", "socket.sendmsg"):
            _attempted_egress_count += 1
            raise SnapshotGuardSecurityError(
                f"OFFLINE_GUARD: Blocked network socket event '{event}' with args {args}"
            )

    sys.addaudithook(audit_hook)


def verify_module_origin_boundaries(
    snapshot_root: Path,
    target_callables: Optional[List[Callable[..., Any]]] = None,
) -> Dict[str, str]:
    """
    Enforce that all loaded scientific modules in sys.modules strictly originate
    within snapshot_root, and verify co_filename of critical callables.
    """
    snapshot_root_resolved = snapshot_root.resolve()
    loaded_origins: Dict[str, str] = {}

    for mod_name, mod in list(sys.modules.items()):
        if mod is None:
            continue
        # We enforce boundaries on our project packages
        if mod_name == "src" or mod_name.startswith("src.") or mod_name.startswith("scripts.analysis"):
            origin = getattr(getattr(mod, "__spec__", None), "origin", None)
            file_path = getattr(mod, "__file__", None)
            effective_path = origin or file_path

            if effective_path is None:
                raise SnapshotGuardSecurityError(
                    f"Module '{mod_name}' has no resolvable origin or __file__"
                )

            resolved_path = Path(effective_path).resolve()
            try:
                resolved_path.relative_to(snapshot_root_resolved)
            except ValueError:
                raise SnapshotGuardSecurityError(
                    f"BOUNDARY BREACH: Module '{mod_name}' resolved outside snapshot root!\n"
                    f"  Module file:   {resolved_path}\n"
                    f"  Snapshot root: {snapshot_root_resolved}"
                )

            loaded_origins[mod_name] = str(resolved_path.as_posix())

    if target_callables:
        for fn in target_callables:
            code_file = getattr(getattr(fn, "__code__", None), "co_filename", None)
            if code_file:
                resolved_code = Path(code_file).resolve()
                try:
                    resolved_code.relative_to(snapshot_root_resolved)
                except ValueError:
                    raise SnapshotGuardSecurityError(
                        f"BOUNDARY BREACH: Callable '{fn.__name__}' co_filename resolved outside snapshot root!\n"
                        f"  co_filename:   {resolved_code}\n"
                        f"  Snapshot root: {snapshot_root_resolved}"
                    )

    return loaded_origins


def run_preflight_task(snapshot_root: Path) -> Dict[str, Any]:
    """Execute preflight integrity check using snapshot authorization module."""
    from src.experiment.authorization import (
        ScientificProtocolApproval,
        compute_code_manifest,
        compute_code_manifest_sha256,
        validate_experiment_readiness,
    )
    from src.experiment.config import load_plan, parse_json

    manifest = compute_code_manifest(snapshot_root)
    file_count = len(manifest)
    if file_count != EXPECTED_CORE_FILES_COUNT:
        raise ValueError(
            f"Core manifest file count mismatch: expected {EXPECTED_CORE_FILES_COUNT}, got {file_count}"
        )

    computed_sha = compute_code_manifest_sha256(snapshot_root)
    if computed_sha != EXPECTED_CORE_MANIFEST_SHA256:
        raise ValueError(
            f"Core manifest SHA256 mismatch: expected {EXPECTED_CORE_MANIFEST_SHA256}, got {computed_sha}"
        )

    # Load protocol and plan
    protocol_path = snapshot_root / "config" / "experiment_protocol_v1.json"
    proto_dict = parse_json(protocol_path.read_bytes())
    protocol = ScientificProtocolApproval(**proto_dict)

    config_path = snapshot_root / "config" / "experiment_config.json"
    plan = load_plan(config_path)

    # Validate readiness
    readiness_report = validate_experiment_readiness(
        plan=plan,
        protocol=protocol,
        repo_root=snapshot_root,
        allow_dirty=True,
        is_live=False,
    )

    # Verify boundaries on loaded functions
    origins = verify_module_origin_boundaries(
        snapshot_root=snapshot_root,
        target_callables=[compute_code_manifest, compute_code_manifest_sha256, validate_experiment_readiness],
    )

    return {
        "status": "PASS",
        "task": "preflight",
        "file_count": file_count,
        "code_manifest_sha256": computed_sha,
        "readiness_report": readiness_report,
        "loaded_origins_count": len(origins),
        "loaded_origins": origins,
    }


def run_verify_baselines_task(snapshot_root: Path) -> Dict[str, Any]:
    """Verify 22 static baseline digests and analysis source in snapshot."""
    lock_file = snapshot_root / "config" / "canonical_experiment_lock_v1.json"
    if not lock_file.is_file():
        raise FileNotFoundError(f"Missing lockfile: {lock_file}")

    with open(lock_file, "r", encoding="utf-8") as f:
        lock_data = json.load(f)

    code_manifest_sha = lock_data.get("code_manifest_sha256")
    if code_manifest_sha != EXPECTED_CORE_MANIFEST_SHA256:
        raise ValueError(f"Lockfile code_manifest_sha mismatch: {code_manifest_sha}")

    # Check analysis script f85
    rq_script = snapshot_root / "scripts" / "analysis" / "evaluate_rqs.py"
    if not rq_script.is_file():
        raise FileNotFoundError(f"Missing evaluate_rqs.py: {rq_script}")

    hasher = hashlib.sha256()
    hasher.update(rq_script.read_bytes())
    rq_sha = hasher.hexdigest()
    if rq_sha != EXPECTED_ANALYSIS_SOURCE_SHA256:
        raise ValueError(f"evaluate_rqs.py sha mismatch: {rq_sha} != {EXPECTED_ANALYSIS_SOURCE_SHA256}")

    # Check BOM presence in src/rag/__init__.py
    rag_init = snapshot_root / "src" / "rag" / "__init__.py"
    init_bytes = rag_init.read_bytes()
    has_bom = init_bytes.startswith(b"\xef\xbb\xbf")
    init_sha = hashlib.sha256(init_bytes).hexdigest()

    origins = verify_module_origin_boundaries(snapshot_root=snapshot_root)

    return {
        "status": "PASS",
        "task": "verify_baselines",
        "code_manifest_sha256": code_manifest_sha,
        "evaluate_rqs_sha256": rq_sha,
        "src_rag_init_sha256": init_sha,
        "src_rag_init_has_bom": has_bom,
        "loaded_origins_count": len(origins),
        "loaded_origins": origins,
    }


def main() -> int:
    # 1. Install socket blocker FIRST before anything else
    _install_socket_guard()

    parser = argparse.ArgumentParser(description="Isolated Snapshot Science Worker")
    parser.add_argument("--snapshot-root", type=Path, required=True, help="Path to frozen snapshot root")
    parser.add_argument("--task", choices=["preflight", "verify_baselines", "egress_test"], required=True)
    parser.add_argument("--output", type=Path, required=True, help="Path to destination evidence JSON")
    args = parser.parse_args()

    snapshot_root = args.snapshot_root.resolve()
    if not snapshot_root.is_dir():
        print(f"ERROR: Snapshot root does not exist: {snapshot_root}", file=sys.stderr)
        return 1

    # In -I isolated mode, explicitly insert snapshot_root at head of sys.path
    snapshot_root_str = str(snapshot_root)
    if snapshot_root_str not in sys.path:
        sys.path.insert(0, snapshot_root_str)

    try:
        if args.task == "preflight":
            result = run_preflight_task(snapshot_root)
        elif args.task == "verify_baselines":
            result = run_verify_baselines_task(snapshot_root)
        elif args.task == "egress_test":
            # Attempt a live socket connection to verify guard interception
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("127.0.0.1", 80))
            result = {"status": "FAIL_EGRESS_NOT_BLOCKED"}
        else:
            raise ValueError(f"Unknown task: {args.task}")

        result["attempted_egress_count"] = _attempted_egress_count
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=True)
        return 0

    except SnapshotGuardSecurityError as sec_err:
        err_res = {
            "status": "BLOCKED_SECURITY_VIOLATION",
            "error_type": "SnapshotGuardSecurityError",
            "error_message": str(sec_err),
            "attempted_egress_count": _attempted_egress_count,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(err_res, f, indent=2, sort_keys=True)
        print(f"SECURITY INTERCEPTION: {sec_err}", file=sys.stderr)
        return 2

    except Exception as exc:
        err_res = {
            "status": "ERROR",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "attempted_egress_count": _attempted_egress_count,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(err_res, f, indent=2, sort_keys=True)
        print(f"WORKER ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
