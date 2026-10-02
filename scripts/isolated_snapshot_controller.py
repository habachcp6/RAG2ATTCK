#!/usr/bin/env python3
"""
scripts/isolated_snapshot_controller.py

Standard-library controller for launching isolated snapshot science workers.
Enforces clean environment boundaries, locked snapshot venv (.venv) isolation,
strict expanded pre/post inventory verification (53 core files, evaluate_rqs f85,
22 baselines, protocol, canonical lock, and clean Git state b69a690),
output path containment, strict worker attestation schema validation,
and child process exit-code fail-closed attestation.

Pure standard-library implementation with zero external dependencies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

EXPECTED_CORE_MANIFEST_SHA256 = "8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4"
EXPECTED_CORE_FILES_COUNT = 53
EXPECTED_SNAPSHOT_GIT_COMMIT = "b69a6909acda4c7588744acc7e1d6c20bfce2612"
EXPECTED_ANALYSIS_SOURCE_SHA256 = "f85d7f7373e825dcc7171ce4491fd15c6fb755955da245041783fe317bc80351"
EXPECTED_BASELINE_FILES_COUNT = 22
EXPECTED_BASELINE_MANIFEST_PATH = "artifacts/orchestration/integration_protected_baseline.json"
EXPECTED_PROTOCOL_JSON_PATH = "config/experiment_protocol_v1.json"
EXPECTED_CANONICAL_LOCK_PATH = "config/canonical_experiment_lock_v1.json"

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
    Find the dedicated virtual environment Python executable in snapshot_root/.venv.
    Verifies that .venv is a dedicated directory and contains pyvenv.cfg.
    Returns the absolute invocation path without dereferencing symlinks,
    preserving dedicated virtual environment identity on Linux/macOS.
    """
    venv_dir = snapshot_root / ".venv"
    if not venv_dir.is_dir():
        raise FileNotFoundError(
            f"Snapshot root '{snapshot_root}' is missing dedicated '.venv' directory! "
            "A locked isolated virtual environment is mandatory."
        )

    pyvenv_cfg = venv_dir / "pyvenv.cfg"
    if not pyvenv_cfg.is_file():
        raise FileNotFoundError(
            f"Snapshot virtual environment at '{venv_dir}' is missing pyvenv.cfg!"
        )

    candidates = [
        venv_dir / "Scripts" / "python.exe",
        venv_dir / "bin" / "python",
    ]
    for c in candidates:
        if c.is_file():
            return c.absolute()

    raise FileNotFoundError(
        f"Could not locate frozen virtual environment python in {venv_dir}. "
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


def compute_expanded_snapshot_inventory(snapshot_root: Path) -> Dict[str, Any]:
    """
    Compute full expanded inventory covering:
    1. 53 core files and canonical manifest SHA256
    2. Actual RQ analysis script (evaluate_rqs.py, f85)
    3. 22 protected baseline files and their inventory manifest
    4. Scientific protocol configuration file
    5. Canonical lock file
    6. Git commit HEAD and clean working tree status

    Fails closed if any required file is missing or has a digest mismatch.
    """
    core_sha, core_inventory = compute_closed_snapshot_inventory(snapshot_root)
    if len(core_inventory) != EXPECTED_CORE_FILES_COUNT:
        raise RuntimeError(
            f"Snapshot core inventory count mismatch: expected {EXPECTED_CORE_FILES_COUNT}, got {len(core_inventory)}"
        )
    if core_sha != EXPECTED_CORE_MANIFEST_SHA256:
        raise RuntimeError(
            f"Snapshot core manifest hash mismatch: expected {EXPECTED_CORE_MANIFEST_SHA256}, got {core_sha}"
        )

    # 1. evaluate_rqs.py (f85)
    rq_file = snapshot_root / "scripts" / "analysis" / "evaluate_rqs.py"
    if not rq_file.is_file():
        raise FileNotFoundError(f"Missing analysis script: {rq_file}")
    rq_sha = hashlib.sha256(rq_file.read_bytes()).hexdigest()
    if rq_sha != EXPECTED_ANALYSIS_SOURCE_SHA256:
        raise RuntimeError(
            f"evaluate_rqs.py SHA mismatch: expected {EXPECTED_ANALYSIS_SOURCE_SHA256}, got {rq_sha}"
        )

    # 2. 22 baselines
    baseline_inv_path = snapshot_root / EXPECTED_BASELINE_MANIFEST_PATH
    if not baseline_inv_path.is_file():
        raise FileNotFoundError(f"Missing baseline inventory: {baseline_inv_path}")
    baseline_inv_sha = hashlib.sha256(baseline_inv_path.read_bytes()).hexdigest()
    baseline_data = json.loads(baseline_inv_path.read_bytes())
    protected_files = baseline_data.get("protected_files", {})
    if len(protected_files) != EXPECTED_BASELINE_FILES_COUNT:
        raise RuntimeError(
            f"Protected baselines count mismatch: expected {EXPECTED_BASELINE_FILES_COUNT}, got {len(protected_files)}"
        )
    baselines_map: Dict[str, str] = {}
    for rel_path, exp_sha in sorted(protected_files.items()):
        bf = snapshot_root / rel_path
        if not bf.is_file():
            raise FileNotFoundError(f"Missing baseline file: {bf}")
        act_sha = hashlib.sha256(bf.read_bytes()).hexdigest()
        if act_sha != exp_sha:
            raise RuntimeError(
                f"Baseline hash mismatch for '{rel_path}': expected {exp_sha}, got {act_sha}"
            )
        baselines_map[rel_path] = act_sha

    # 3. Protocol file
    proto_file = snapshot_root / EXPECTED_PROTOCOL_JSON_PATH
    if not proto_file.is_file():
        raise FileNotFoundError(f"Missing protocol file: {proto_file}")
    proto_sha = hashlib.sha256(proto_file.read_bytes()).hexdigest()

    # 4. Canonical lock file
    lock_file = snapshot_root / EXPECTED_CANONICAL_LOCK_PATH
    if not lock_file.is_file():
        raise FileNotFoundError(f"Missing canonical lock file: {lock_file}")
    lock_sha = hashlib.sha256(lock_file.read_bytes()).hexdigest()

    # 5. Git state
    git_commit = verify_snapshot_git_identity(snapshot_root)

    return {
        "core_manifest_sha256": core_sha,
        "core_files_count": len(core_inventory),
        "core_files_map": core_inventory,
        "evaluate_rqs_sha256": rq_sha,
        "protocol_sha256": proto_sha,
        "canonical_lock_sha256": lock_sha,
        "baseline_inventory_sha256": baseline_inv_sha,
        "protected_baselines_count": len(baselines_map),
        "protected_baselines_map": baselines_map,
        "git_commit": git_commit,
    }


def _evaluate_marker(marker_str: Optional[str], platform_name: Optional[str] = None) -> bool:
    """
    Safely evaluate environment markers using standard library platform/sys attributes.
    """
    if not marker_str:
        return True
    current_platform = platform_name or sys.platform
    plat_system = (
        "Linux"
        if current_platform == "linux"
        else ("Windows" if current_platform == "win32" else "Darwin")
    )
    current_machine = platform.machine()
    if current_platform == "linux" and current_machine in ("AMD64", "x86_64"):
        current_machine = "x86_64"
    elif current_platform == "win32" and current_machine in ("AMD64", "x86_64"):
        current_machine = "AMD64"

    ctx = {
        "sys_platform": current_platform,
        "platform_system": plat_system,
        "platform_machine": current_machine,
        "platform_python_implementation": platform.python_implementation(),
        "implementation_name": sys.implementation.name,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "python_full_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "extra": "",
    }
    try:
        return bool(eval(marker_str, {"__builtins__": {}}, ctx))
    except Exception:
        return False


def extract_required_dependencies_from_uv_lock(
    uv_lock_path: Path, platform_name: Optional[str] = None
) -> Dict[str, str]:
    """
    Extract all required dependencies and locked versions for the current platform
    by traversing from the root virtual package (e.g. rag2attck) in uv.lock,
    evaluating platform environment markers and following edge.extra and package.optional-dependencies.
    """
    if not uv_lock_path.is_file():
        raise FileNotFoundError(f"Missing uv.lock file: {uv_lock_path}")

    with open(uv_lock_path, "rb") as f:
        uv_data = tomllib.load(f)

    all_pkgs = {
        p["name"].lower().replace("_", "-"): p
        for p in uv_data.get("package", [])
        if "name" in p and "version" in p
    }

    root_candidates = [
        p["name"].lower().replace("_", "-")
        for p in uv_data.get("package", [])
        if p.get("source", {}).get("virtual") or p.get("name") == "rag2attck"
    ]
    if not root_candidates:
        root_candidates = ["rag2attck"]

    visited_pkgs: Set[str] = set()
    visited_extras: Set[Tuple[str, str]] = set()

    def _walk(pkg_name: str, extras: Optional[List[str]] = None) -> None:
        if pkg_name not in all_pkgs:
            return
        is_first_visit = (pkg_name not in visited_pkgs)
        visited_pkgs.add(pkg_name)
        pkg_info = all_pkgs[pkg_name]

        if is_first_visit:
            for d in pkg_info.get("dependencies", []):
                if _evaluate_marker(d.get("marker"), platform_name=platform_name):
                    d_name = d["name"].lower().replace("_", "-")
                    d_extras = d.get("extra")
                    _walk(d_name, d_extras)
            for dev_list in pkg_info.get("dev-dependencies", {}).values():
                for d in dev_list:
                    if _evaluate_marker(d.get("marker"), platform_name=platform_name):
                        d_name = d["name"].lower().replace("_", "-")
                        d_extras = d.get("extra")
                        _walk(d_name, d_extras)

        if extras:
            opt_deps = pkg_info.get("optional-dependencies", {})
            for extra in extras:
                key = (pkg_name, extra)
                if key in visited_extras:
                    continue
                visited_extras.add(key)
                for d in opt_deps.get(extra, []):
                    if _evaluate_marker(d.get("marker"), platform_name=platform_name):
                        d_name = d["name"].lower().replace("_", "-")
                        d_extras = d.get("extra")
                        _walk(d_name, d_extras)

    for r in root_candidates:
        _walk(r)

    for r in root_candidates:
        visited_pkgs.discard(r)

    return {pkg: all_pkgs[pkg]["version"] for pkg in visited_pkgs if pkg in all_pkgs}


def verify_snapshot_venv_dependencies(
    snapshot_root: Path,
    worker_attestation: Dict[str, Any],
    platform_name: Optional[str] = None,
) -> None:
    """
    Directly cross-check installed dependency versions attested by child worker
    against the snapshot venv original uv.lock.
    Enforces that:
    1. installed_dependencies is a non-empty dictionary.
    2. All required installed distributions extracted from uv.lock are present (no missing packages,
       no empty map, no small subset).
    3. No unauthorized or unknown packages are installed (fails closed if any package is not in uv.lock).
    4. Every installed package version matches the locked version in uv.lock.
    """
    uv_lock_path = snapshot_root / "uv.lock"
    if not uv_lock_path.is_file():
        raise FileNotFoundError(f"Missing uv.lock in snapshot root: {uv_lock_path}")

    with open(uv_lock_path, "rb") as f:
        uv_data = tomllib.load(f)

    all_locked_packages: Dict[str, str] = {
        p["name"].lower().replace("_", "-"): p["version"]
        for p in uv_data.get("package", [])
        if "name" in p and "version" in p
    }

    installed = worker_attestation.get("installed_dependencies")
    if not isinstance(installed, dict) or not installed:
        raise RuntimeError("Worker runtime attestation has missing or empty installed_dependencies!")

    norm_installed: Dict[str, str] = {
        k.lower().replace("_", "-"): str(v) for k, v in installed.items()
    }

    # 1. Reject unauthorized or unknown packages not in uv.lock
    unknown_packages = set(norm_installed.keys()) - set(all_locked_packages.keys())
    if unknown_packages:
        raise RuntimeError(
            f"Unauthorized or unknown installed package(s) not found in uv.lock: {sorted(unknown_packages)}"
        )

    # 2. Reject version mismatches against uv.lock
    for pkg_name, act_ver in norm_installed.items():
        locked_ver = all_locked_packages[pkg_name]
        if act_ver != locked_ver:
            raise RuntimeError(
                f"Venv dependency version mismatch for '{pkg_name}': "
                f"installed {act_ver} != expected in uv.lock {locked_ver}"
            )

    # 3. Reject missing required packages / small subset / empty map
    required_deps = extract_required_dependencies_from_uv_lock(
        uv_lock_path, platform_name=platform_name
    )
    missing_required = set(required_deps.keys()) - set(norm_installed.keys())
    if missing_required:
        raise RuntimeError(
            f"Venv dependency attestation missing {len(missing_required)} required packages from uv.lock: "
            f"{sorted(missing_required)[:10]} (small subset or incomplete installation rejected)"
        )


def validate_worker_attestation_schema(
    worker_output: Dict[str, Any],
    expected_task: str,
    snapshot_root: Path,
) -> None:
    """
    Strictly validate the worker output schema before accepting status PASS:
    1. Reject minimal PASS payloads missing required fields.
    2. Reject wrong-task payloads.
    3. Verify core manifest hash and file count.
    4. Verify zero attempted egress and installed offline guard.
    5. Verify 22 protected baselines count.
    6. Verify non-empty loaded module origins contained within snapshot root.
    7. Verify worker runtime attestation (sys.prefix, sys.executable, and uv.lock consistency).
    """
    if not isinstance(worker_output, dict):
        raise RuntimeError("Invalid worker output: root must be a JSON dictionary!")

    status = worker_output.get("status")
    if status != "PASS":
        return

    # 1. Task identity check
    reported_task = worker_output.get("task")
    if reported_task != expected_task:
        raise RuntimeError(
            f"Worker attestation schema rejection: task mismatch! "
            f"Expected '{expected_task}', got '{reported_task}'"
        )

    # 2. Core manifest check
    if worker_output.get("code_manifest_sha256") != EXPECTED_CORE_MANIFEST_SHA256:
        raise RuntimeError(
            f"Worker attestation schema rejection: code_manifest_sha256 mismatch! "
            f"Expected {EXPECTED_CORE_MANIFEST_SHA256}, got {worker_output.get('code_manifest_sha256')}"
        )
    if worker_output.get("file_count") != EXPECTED_CORE_FILES_COUNT:
        raise RuntimeError(
            f"Worker attestation schema rejection: file_count mismatch! "
            f"Expected {EXPECTED_CORE_FILES_COUNT}, got {worker_output.get('file_count')}"
        )

    # 3. Guard & Egress check
    if worker_output.get("offline_guard_installed") is not True:
        raise RuntimeError(
            "Worker attestation schema rejection: offline_guard_installed must be True!"
        )
    if worker_output.get("attempted_egress_count", -1) != 0:
        raise RuntimeError(
            f"Worker attestation schema rejection: attempted_egress_count must be 0, "
            f"got {worker_output.get('attempted_egress_count')}"
        )

    # 4. Baselines check (Reject baseline PASS count 0 or missing)
    if worker_output.get("protected_baselines_verified_count") != EXPECTED_BASELINE_FILES_COUNT:
        raise RuntimeError(
            f"Worker attestation schema rejection: protected_baselines_verified_count must be {EXPECTED_BASELINE_FILES_COUNT}, "
            f"got {worker_output.get('protected_baselines_verified_count')}"
        )

    # 5. Loaded origins check
    loaded_origins = worker_output.get("loaded_origins")
    origins_count = worker_output.get("loaded_origins_count")
    if not isinstance(loaded_origins, dict) or len(loaded_origins) == 0:
        raise RuntimeError(
            "Worker attestation schema rejection: loaded_origins must be a non-empty dictionary!"
        )
    if not isinstance(origins_count, int) or origins_count <= 0 or origins_count != len(loaded_origins):
        raise RuntimeError(
            f"Worker attestation schema rejection: loaded_origins_count ({origins_count}) "
            f"mismatch with loaded_origins length ({len(loaded_origins)})!"
        )

    resolved_snap = snapshot_root.resolve()
    for mod_name, origin_path in loaded_origins.items():
        p = Path(origin_path).resolve()
        try:
            p.relative_to(resolved_snap)
        except ValueError:
            raise RuntimeError(
                f"Worker attestation schema rejection: loaded module '{mod_name}' origin '{origin_path}' "
                f"is outside snapshot root '{resolved_snap}'!"
            )

    # 6. Worker runtime attestation check
    runtime_attestation = worker_output.get("worker_runtime_attestation")
    if not isinstance(runtime_attestation, dict):
        raise RuntimeError(
            "Worker attestation schema rejection: worker_runtime_attestation dictionary missing!"
        )

    sys_prefix = runtime_attestation.get("sys_prefix")
    expected_venv = (snapshot_root / ".venv").absolute()
    if not sys_prefix:
        raise RuntimeError("Worker attestation schema rejection: sys_prefix is missing!")
    actual_prefix_path = Path(sys_prefix).absolute()
    if actual_prefix_path != expected_venv and actual_prefix_path.resolve() != expected_venv.resolve():
        raise RuntimeError(
            f"Worker attestation schema rejection: sys_prefix '{sys_prefix}' does not match snapshot venv '{expected_venv}'!"
        )

    sys_exe = runtime_attestation.get("sys_executable")
    expected_python = resolve_snapshot_python(snapshot_root).absolute()
    if not sys_exe:
        raise RuntimeError("Worker attestation schema rejection: sys_executable is missing!")
    actual_exe_path = Path(sys_exe).absolute()
    if actual_exe_path != expected_python and actual_exe_path.resolve() != expected_python.resolve():
        try:
            actual_exe_path.relative_to(expected_venv)
        except ValueError:
            raise RuntimeError(
                f"Worker attestation schema rejection: sys_executable '{sys_exe}' does not match expected snapshot python '{expected_python}'!"
            )

    # 7. Locked dependency versions verification against uv.lock
    verify_snapshot_venv_dependencies(snapshot_root, runtime_attestation)


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
    Enforces pre/post expanded inventory verification, clean environment, output containment,
    strict worker attestation schema verification, and process exit-code fail-closed validation.
    """
    snapshot_root = snapshot_root.resolve()
    if not snapshot_root.is_dir():
        raise FileNotFoundError(f"Snapshot root does not exist: {snapshot_root}")

    # Validate output path containment before touching filesystem
    validate_output_path_containment(output_path, snapshot_root)

    # Validate python interpreter and dedicated .venv
    venv_dir = snapshot_root / ".venv"
    if override_python is not None:
        override_abs = Path(override_python).absolute()
        if venv_dir.is_dir():
            expected_python = resolve_snapshot_python(snapshot_root)
            if override_abs != expected_python.absolute() and override_abs.resolve() != expected_python.resolve():
                raise ValueError(
                    f"REJECTED: Arbitrary override_python '{override_python}' is outside snapshot venv!\n"
                    f"  Snapshot venv python: {expected_python}"
                )
            python_exe = expected_python
        else:
            python_exe = override_abs
    else:
        python_exe = resolve_snapshot_python(snapshot_root)

    worker_script = (Path(__file__).parent / "isolated_snapshot_worker.py").resolve()
    if not worker_script.is_file():
        raise FileNotFoundError(f"Missing worker script: {worker_script}")

    # Compute pre-execution expanded inventory (core 53, f85 analysis, 22 baselines, protocol, lock, git)
    pre_expanded = compute_expanded_snapshot_inventory(snapshot_root)

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

    # Post-execution expanded inventory verification (comprehensive immutability check)
    post_expanded = compute_expanded_snapshot_inventory(snapshot_root)
    immutability_ok = (pre_expanded == post_expanded)
    if not immutability_ok:
        diff_keys = [k for k in pre_expanded if pre_expanded.get(k) != post_expanded.get(k)]
        raise RuntimeError(
            f"CRITICAL: Snapshot immutability violated during task execution! "
            f"Expanded inventory mismatch in keys: {diff_keys}"
        )

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

    # Strict attestation schema validation (rejects minimal PASS, wrong task, missing origins/guard/baselines)
    validate_worker_attestation_schema(worker_output, task, snapshot_root)

    worker_output["controller_attestation"] = {
        "snapshot_root": str(snapshot_root.as_posix()),
        "python_executable": str(python_exe.as_posix()),
        "task": task,
        "pre_fingerprint": pre_expanded["core_manifest_sha256"],
        "post_fingerprint": post_expanded["core_manifest_sha256"],
        "pre_expanded_sha256": hashlib.sha256(json.dumps(pre_expanded, sort_keys=True).encode()).hexdigest(),
        "post_expanded_sha256": hashlib.sha256(json.dumps(post_expanded, sort_keys=True).encode()).hexdigest(),
        "expanded_immutability_verified": immutability_ok,
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
    default_snap = Path(
        os.environ.get(
            "RAG2ATTCK_SNAPSHOT_ROOT",
            "C:/Users/hahoa/.codex/artifacts/rag2attck/finalization_snapshots/b69a690",
        )
    )
    parser.add_argument(
        "--snapshot-root",
        type=Path,
        default=default_snap,
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
