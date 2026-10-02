#!/usr/bin/env python3
"""
scripts/isolated_snapshot_worker.py

Worker script executed in a fresh isolated child process inside the frozen snapshot.
Installs offline socket and DNS guard before any application imports, verifies loaded module
origins, spec bindings, byte hashes, co_filename boundaries against snapshot_root,
attests dedicated virtual environment identity and locked dependencies, and executes
strictly attested tasks.

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
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# Expected Invariants for Frozen Snapshot (b69a690)
EXPECTED_CORE_MANIFEST_SHA256 = "8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4"
EXPECTED_ANALYSIS_SOURCE_SHA256 = "f85d7f7373e825dcc7171ce4491fd15c6fb755955da245041783fe317bc80351"
EXPECTED_CORE_FILES_COUNT = 53
EXPECTED_BASELINE_FILES_COUNT = 22
EXPECTED_BASELINE_MANIFEST_PATH = "artifacts/orchestration/integration_protected_baseline.json"
EXPECTED_SNAPSHOT_GIT_COMMIT = "b69a6909acda4c7588744acc7e1d6c20bfce2612"

BLOCKED_SOCKET_EVENTS = {
    "socket.connect",
    "socket.bind",
    "socket.sendto",
    "socket.sendmsg",
    "socket.getaddrinfo",
    "socket.gethostbyname",
    "socket.gethostbyaddr",
    "socket.getnameinfo",
}


class SnapshotGuardSecurityError(RuntimeError):
    """Raised when an offline guard violation or origin boundary breach occurs."""
    pass


_attempted_egress_count = 0
_offline_guard_installed = False


def _install_socket_guard() -> None:
    """
    Install comprehensive audit hook and monkey-patch socket methods to intercept
    network socket operations, address resolution, and DNS queries.
    """
    global _attempted_egress_count, _offline_guard_installed

    def audit_hook(event: str, args: tuple) -> None:
        global _attempted_egress_count
        if event in BLOCKED_SOCKET_EVENTS:
            _attempted_egress_count += 1
            raise SnapshotGuardSecurityError(
                f"OFFLINE_GUARD: Blocked network socket event '{event}' with args {args}"
            )

    sys.addaudithook(audit_hook)

    try:
        import socket

        def _guarded_call(name: str):
            def _fn(*args, **kwargs):
                global _attempted_egress_count
                _attempted_egress_count += 1
                raise SnapshotGuardSecurityError(f"OFFLINE_GUARD: Blocked socket function '{name}'")
            return _fn

        for fn_name in ("getaddrinfo", "gethostbyname", "gethostbyaddr", "getnameinfo", "create_connection"):
            if hasattr(socket, fn_name):
                setattr(socket, fn_name, _guarded_call(fn_name))
    except Exception:
        pass

    _offline_guard_installed = True


def compute_closed_snapshot_inventory(snapshot_root: Path) -> Tuple[str, Dict[str, str]]:
    """Compute exact 53-file mapping and canonical SHA-256 digest."""
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


def verify_snapshot_git_identity(snapshot_root: Path) -> str:
    """Verify clean Git state and exact commit b69a690."""
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


def verify_protected_baselines(snapshot_root: Path) -> int:
    """
    Mandatory verification of 22 protected baseline files defined in
    artifacts/orchestration/integration_protected_baseline.json.
    Fails closed if the inventory file is missing, count is not 22, or any file hash mismatches.
    """
    inv_file = snapshot_root / EXPECTED_BASELINE_MANIFEST_PATH
    if not inv_file.is_file():
        raise FileNotFoundError(f"Missing protected baseline inventory: {inv_file}")

    inv_data = json.loads(inv_file.read_bytes())
    protected_files = inv_data.get("protected_files", {})
    baseline_count = len(protected_files)
    if baseline_count != EXPECTED_BASELINE_FILES_COUNT:
        raise ValueError(
            f"Protected baselines count mismatch: expected {EXPECTED_BASELINE_FILES_COUNT}, got {baseline_count}"
        )

    for rel_path, exp_sha in protected_files.items():
        bf = snapshot_root / rel_path
        if not bf.is_file():
            raise FileNotFoundError(f"Missing protected baseline file: {rel_path}")
        actual_bsha = hashlib.sha256(bf.read_bytes()).hexdigest()
        if actual_bsha != exp_sha:
            raise ValueError(
                f"Protected baseline hash mismatch for '{rel_path}': expected {exp_sha}, got {actual_bsha}"
            )

    return baseline_count


def gather_worker_runtime_attestation(snapshot_root: Path) -> Dict[str, Any]:
    """
    Attest sys.executable, sys.prefix, and actual installed dependencies within the dedicated venv.
    Fails closed if sys.prefix or sys.executable is outside the snapshot .venv.
    """
    expected_venv = (snapshot_root / ".venv").resolve()
    if not expected_venv.is_dir():
        raise SnapshotGuardSecurityError(
            f"Snapshot .venv directory missing or invalid: {expected_venv}"
        )

    actual_prefix = Path(sys.prefix).resolve()
    if actual_prefix != expected_venv:
        raise SnapshotGuardSecurityError(
            f"Venv boundary breach: sys.prefix '{actual_prefix}' != expected snapshot venv '{expected_venv}'"
        )

    actual_exe = Path(sys.executable).resolve()
    try:
        actual_exe.relative_to(expected_venv)
    except ValueError:
        raise SnapshotGuardSecurityError(
            f"Python executable breach: sys.executable '{actual_exe}' is outside snapshot venv '{expected_venv}'"
        )

    import importlib.metadata

    installed_dependencies: Dict[str, str] = {}
    for dist in importlib.metadata.distributions():
        name = dist.metadata.get("Name")
        if name:
            norm_name = name.lower().replace("_", "-")
            installed_dependencies[norm_name] = dist.version

    return {
        "sys_executable": str(actual_exe.as_posix()),
        "sys_prefix": str(actual_prefix.as_posix()),
        "installed_dependencies": installed_dependencies,
    }


def verify_module_origin_boundaries(
    snapshot_root: Path,
    expected_closed_inventory: Optional[Dict[str, str]] = None,
    target_callables: Optional[List[Callable[..., Any]]] = None,
    target_modules: Optional[Set[str]] = None,
) -> Dict[str, str]:
    """
    Enforce that all loaded scientific modules in sys.modules strictly originate
    within snapshot_root, verify BOTH __spec__.origin and __file__, check byte hashes
    against closed inventory, and inspect co_filename of callables (unwrapping decorators).
    """
    snapshot_root_resolved = snapshot_root.resolve()
    base_prefix_resolved = Path(sys.base_prefix).resolve()
    prefix_resolved = Path(sys.prefix).resolve()

    loaded_origins: Dict[str, str] = {}

    for mod_name, mod in list(sys.modules.items()):
        if mod is None:
            continue
        if target_modules is not None and mod_name not in target_modules:
            continue
        # Enforce boundaries on our project packages
        if mod_name == "src" or mod_name.startswith("src.") or mod_name.startswith("scripts.analysis"):
            spec = getattr(mod, "__spec__", None)
            origin = getattr(spec, "origin", None) if spec else None
            file_path = getattr(mod, "__file__", None)

            if file_path is None and origin is None:
                raise SnapshotGuardSecurityError(
                    f"Module '{mod_name}' has no resolvable origin or __file__"
                )

            resolved_file: Optional[Path] = None
            if file_path is not None:
                resolved_file = Path(file_path).resolve()
                try:
                    resolved_file.relative_to(snapshot_root_resolved)
                except ValueError:
                    raise SnapshotGuardSecurityError(
                        f"BOUNDARY BREACH: Module '{mod_name}' __file__ resolved outside snapshot root!\n"
                        f"  __file__:      {resolved_file}\n"
                        f"  Snapshot root: {snapshot_root_resolved}"
                    )

            resolved_origin: Optional[Path] = None
            if origin is not None:
                resolved_origin = Path(origin).resolve()
                try:
                    resolved_origin.relative_to(snapshot_root_resolved)
                except ValueError:
                    raise SnapshotGuardSecurityError(
                        f"BOUNDARY BREACH: Module '{mod_name}' __spec__.origin resolved outside snapshot root!\n"
                        f"  origin:        {resolved_origin}\n"
                        f"  Snapshot root: {snapshot_root_resolved}"
                    )

            if resolved_file is not None and resolved_origin is not None:
                if resolved_file != resolved_origin:
                    raise SnapshotGuardSecurityError(
                        f"BOUNDARY BREACH: Module '{mod_name}' has mismatched __file__ and __spec__.origin!\n"
                        f"  __file__: {resolved_file}\n"
                        f"  origin:   {resolved_origin}"
                    )

            effective_path = resolved_file or resolved_origin
            if effective_path is None:
                raise SnapshotGuardSecurityError(f"Module '{mod_name}' has no resolvable path")

            if expected_closed_inventory is not None:
                rel_posix = effective_path.relative_to(snapshot_root_resolved).as_posix()
                if rel_posix not in expected_closed_inventory:
                    raise SnapshotGuardSecurityError(
                        f"BOUNDARY BREACH: Module '{mod_name}' file '{rel_posix}' is not in closed 53-file inventory!"
                    )
                actual_sha = hashlib.sha256(effective_path.read_bytes()).hexdigest()
                if actual_sha != expected_closed_inventory[rel_posix]:
                    raise SnapshotGuardSecurityError(
                        f"BOUNDARY BREACH: Module '{mod_name}' file '{rel_posix}' byte hash mismatch! "
                        f"Expected {expected_closed_inventory[rel_posix]}, got {actual_sha}"
                    )

            # Inspect callables/functions inside the module's dictionary
            for attr_name, attr_val in list(getattr(mod, "__dict__", {}).items()):
                target_fn = attr_val
                # Unwrap decorator chains (e.g., @contextmanager, @wraps)
                while hasattr(target_fn, "__wrapped__"):
                    target_fn = getattr(target_fn, "__wrapped__")

                code_obj = getattr(target_fn, "__code__", None)
                if code_obj is not None:
                    code_file = getattr(code_obj, "co_filename", None)
                    if code_file:
                        code_path = Path(code_file).resolve()
                        fn_mod = getattr(target_fn, "__module__", None)

                        # If callable was defined in this project module, its co_filename MUST be in snapshot_root
                        if fn_mod == mod_name:
                            try:
                                code_path.relative_to(snapshot_root_resolved)
                            except ValueError:
                                raise SnapshotGuardSecurityError(
                                    f"BOUNDARY BREACH: Module '{mod_name}' attribute '{attr_name}' "
                                    f"co_filename resolved outside snapshot root!\n"
                                    f"  co_filename:   {code_path}\n"
                                    f"  Snapshot root: {snapshot_root_resolved}"
                                )
                        else:
                            # For foreign/imported callables, verify they reside in snapshot_root, stdlib, or venv
                            in_snapshot = False
                            try:
                                code_path.relative_to(snapshot_root_resolved)
                                in_snapshot = True
                            except ValueError:
                                pass

                            in_stdlib = False
                            try:
                                code_path.relative_to(base_prefix_resolved)
                                in_stdlib = True
                            except ValueError:
                                pass

                            in_venv = False
                            try:
                                code_path.relative_to(prefix_resolved)
                                in_venv = True
                            except ValueError:
                                pass

                            if not (in_snapshot or in_stdlib or in_venv):
                                raise SnapshotGuardSecurityError(
                                    f"BOUNDARY BREACH: Module '{mod_name}' attribute '{attr_name}' "
                                    f"co_filename resolved in foreign untrusted location!\n"
                                    f"  co_filename: {code_path}"
                                )

            loaded_origins[mod_name] = str(effective_path.as_posix())

    if target_callables:
        for fn in target_callables:
            target_fn = fn
            while hasattr(target_fn, "__wrapped__"):
                target_fn = getattr(target_fn, "__wrapped__")
            code_file = getattr(getattr(target_fn, "__code__", None), "co_filename", None)
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
    # Verify closed 53-file inventory first
    manifest_sha, inventory = compute_closed_snapshot_inventory(snapshot_root)
    if len(inventory) != EXPECTED_CORE_FILES_COUNT:
        raise ValueError(
            f"Core manifest file count mismatch: expected {EXPECTED_CORE_FILES_COUNT}, got {len(inventory)}"
        )
    if manifest_sha != EXPECTED_CORE_MANIFEST_SHA256:
        raise ValueError(
            f"Core manifest SHA256 mismatch: expected {EXPECTED_CORE_MANIFEST_SHA256}, got {manifest_sha}"
        )

    # Mandatory clean Git state
    actual_git_commit = verify_snapshot_git_identity(snapshot_root)

    # Mandatory 22 baselines verification
    baseline_count = verify_protected_baselines(snapshot_root)

    # Mandatory venv and locked dependencies attestation
    runtime_attestation = gather_worker_runtime_attestation(snapshot_root)

    from src.experiment.authorization import (
        ScientificProtocolApproval,
        compute_code_manifest,
        compute_code_manifest_sha256,
        validate_experiment_readiness,
    )
    from src.experiment.config import load_plan, parse_json

    protocol_path = snapshot_root / "config" / "experiment_protocol_v1.json"
    proto_dict = parse_json(protocol_path.read_bytes())
    protocol = ScientificProtocolApproval(**proto_dict)

    config_path = snapshot_root / "config" / "experiment_config.json"
    plan = load_plan(config_path)

    # Strictly disallow dirty checkouts
    readiness_report = validate_experiment_readiness(
        plan=plan,
        protocol=protocol,
        repo_root=snapshot_root,
        allow_dirty=False,
        is_live=False,
    )

    origins = verify_module_origin_boundaries(
        snapshot_root=snapshot_root,
        expected_closed_inventory=inventory,
        target_callables=[compute_code_manifest, compute_code_manifest_sha256, validate_experiment_readiness],
    )

    return {
        "status": "PASS",
        "task": "preflight",
        "file_count": len(inventory),
        "code_manifest_sha256": manifest_sha,
        "git_commit": actual_git_commit,
        "offline_guard_installed": _offline_guard_installed,
        "attempted_egress_count": _attempted_egress_count,
        "protected_baselines_verified_count": baseline_count,
        "readiness_report": readiness_report,
        "loaded_origins_count": len(origins),
        "loaded_origins": origins,
        "worker_runtime_attestation": runtime_attestation,
    }


def run_verify_baselines_task(snapshot_root: Path) -> Dict[str, Any]:
    """
    Verify 53 closed core files, 22 static baseline digests, f85 analysis source,
    and actual module import origins in snapshot.
    """
    manifest_sha, inventory = compute_closed_snapshot_inventory(snapshot_root)
    if len(inventory) != EXPECTED_CORE_FILES_COUNT:
        raise ValueError(
            f"Core inventory count mismatch: expected {EXPECTED_CORE_FILES_COUNT}, got {len(inventory)}"
        )
    if manifest_sha != EXPECTED_CORE_MANIFEST_SHA256:
        raise ValueError(f"Core manifest SHA256 mismatch: {manifest_sha}")

    # Mandatory clean Git state
    actual_git_commit = verify_snapshot_git_identity(snapshot_root)

    # Check analysis script f85
    rq_script = snapshot_root / "scripts" / "analysis" / "evaluate_rqs.py"
    if not rq_script.is_file():
        raise FileNotFoundError(f"Missing evaluate_rqs.py: {rq_script}")

    rq_sha = hashlib.sha256(rq_script.read_bytes()).hexdigest()
    if rq_sha != EXPECTED_ANALYSIS_SOURCE_SHA256:
        raise ValueError(f"evaluate_rqs.py sha mismatch: {rq_sha} != {EXPECTED_ANALYSIS_SOURCE_SHA256}")

    # Check BOM presence in src/rag/__init__.py
    rag_init = snapshot_root / "src" / "rag" / "__init__.py"
    init_bytes = rag_init.read_bytes()
    has_bom = init_bytes.startswith(b"\xef\xbb\xbf")
    init_sha = hashlib.sha256(init_bytes).hexdigest()

    # Mandatory 22 baselines verification
    baseline_count = verify_protected_baselines(snapshot_root)

    # Mandatory venv and locked dependencies attestation
    runtime_attestation = gather_worker_runtime_attestation(snapshot_root)

    # Explicitly import scientific modules to verify real module origin boundaries
    import src.experiment.authorization  # noqa: F401
    import src.experiment.config  # noqa: F401
    import src.rag  # noqa: F401
    import src.retrieval  # noqa: F401

    origins = verify_module_origin_boundaries(
        snapshot_root=snapshot_root,
        expected_closed_inventory=inventory,
    )

    return {
        "status": "PASS",
        "task": "verify_baselines",
        "file_count": len(inventory),
        "code_manifest_sha256": manifest_sha,
        "git_commit": actual_git_commit,
        "offline_guard_installed": _offline_guard_installed,
        "attempted_egress_count": _attempted_egress_count,
        "evaluate_rqs_sha256": rq_sha,
        "src_rag_init_sha256": init_sha,
        "src_rag_init_has_bom": has_bom,
        "protected_baselines_verified_count": baseline_count,
        "loaded_origins_count": len(origins),
        "loaded_origins": origins,
        "worker_runtime_attestation": runtime_attestation,
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
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("127.0.0.1", 80))
            result = {"status": "FAIL_EGRESS_NOT_BLOCKED"}
        else:
            raise ValueError(f"Unknown task: {args.task}")

        if _attempted_egress_count > 0:
            raise SnapshotGuardSecurityError(
                f"Egress was attempted during execution ({_attempted_egress_count} events)!"
            )

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
