#!/usr/bin/env python3
"""
scripts/provision_snapshot.py

Provision a clean, portable historical snapshot at commit b69a690 outside engineering checkout.
Ensures:
1. Exact Git commit b69a6909acda4c7588744acc7e1d6c20bfce2612 with a clean working tree.
2. Verified ATT&CK reference at attack/raw/enterprise-v19.2/enterprise-attack-19.2.json.
3. Dedicated venv in .venv with pyvenv.cfg and dependencies installed via 'uv sync --frozen'.
4. Full expanded inventory preflight (53 core files, 22 baselines, f85 analysis, protocol, lock).
5. Strict containment checks preventing mutation/deletion of source_repo or its ancestors.
6. Fail-closed policy on existing non-empty directories: verified snapshots are reused,
   corrupt/dirty/foreign directories are rejected without deletion or reset.
7. Verbatim git attributes configuration (* -text -eol, * binary) with independent local clone
   preventing line-ending conversion on Linux/CI runners.

Pure standard-library runner with uv subprocess calls.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

EXPECTED_SNAPSHOT_GIT_COMMIT = "b69a6909acda4c7588744acc7e1d6c20bfce2612"
EXPECTED_ATTACK_SHA256 = "dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4"


def verify_sha256(file_path: Path, expected_sha: str) -> bool:
    if not file_path.is_file():
        return False
    actual_sha = hashlib.sha256(file_path.read_bytes()).hexdigest()
    return actual_sha == expected_sha


def check_containment(target_dir: Path, source_repo: Path) -> None:
    target_resolved = target_dir.resolve()
    source_resolved = source_repo.resolve()
    if (
        target_resolved == source_resolved
        or target_resolved in source_resolved.parents
        or source_resolved in target_resolved.parents
    ):
        raise ValueError(
            f"Target directory {target_resolved} conflicts with source repo {source_resolved} "
            "containment hierarchy."
        )


def _export_github_env(target_dir: Path) -> None:
    gh_env = os.environ.get("GITHUB_ENV")
    if gh_env:
        with open(gh_env, "a", encoding="utf-8") as f:
            f.write(f"RAG2ATTCK_SNAPSHOT_ROOT={target_dir.as_posix()}\n")
        print(f"Exported RAG2ATTCK_SNAPSHOT_ROOT={target_dir.as_posix()} to GITHUB_ENV.")


def _configure_verbatim_attributes(target_dir: Path) -> None:
    """
    Disable all line-ending conversions for historical snapshot checkout.
    Uses * -text -eol and * binary in repository attributes to ensure byte-exact preservation.
    """
    subprocess.run(["git", "-C", str(target_dir), "config", "core.autocrlf", "false"], check=True)
    subprocess.run(["git", "-C", str(target_dir), "config", "core.eol", "lf"], check=True)

    info_dir = target_dir / ".git" / "info"
    info_dir.mkdir(parents=True, exist_ok=True)
    attr_content = "* -text -eol\n* binary\n"
    (info_dir / "attributes").write_text(attr_content, encoding="utf-8")

    temp_attr = Path(tempfile.gettempdir()) / "rag2attck_verbatim_attributes"
    temp_attr.write_text(attr_content, encoding="utf-8")
    subprocess.run(
        [
            "git",
            "-C",
            str(target_dir),
            "config",
            "core.attributesFile",
            temp_attr.as_posix(),
        ],
        check=True,
    )


def _verify_full_snapshot_integrity(snapshot_root: Path, commit: str) -> None:
    """
    Fail-closed comprehensive snapshot integrity gate:
    1. Git identity: commit matches and working tree is clean.
    2. ATT&CK reference JSON hash matches.
    3. Dedicated .venv with pyvenv.cfg exists.
    4. Full expanded inventory (53 core, 22 baselines, f85, protocol, lock).
    5. Locked dependencies closure (104 on Linux, 87 on Windows, 85 on macOS).
    6. Actual child process identity, offline guard, and baselines via execute_snapshot_task.
    """
    from scripts.isolated_snapshot_controller import (
        compute_expanded_snapshot_inventory,
        execute_snapshot_task,
        resolve_snapshot_python,
        verify_snapshot_git_identity,
    )

    verify_snapshot_git_identity(snapshot_root)
    py_bin = resolve_snapshot_python(snapshot_root)
    compute_expanded_snapshot_inventory(snapshot_root)

    # Cross-check child process identity, offline guard, and baselines via isolated controller
    with tempfile.TemporaryDirectory() as tmp_dir:
        receipt_path = Path(tmp_dir) / "provision_verification_receipt.json"
        res = execute_snapshot_task(
            snapshot_root=snapshot_root,
            task="verify_baselines",
            output_path=receipt_path,
        )

        if res.get("status") != "PASS":
            raise RuntimeError(
                f"Snapshot integrity verification failed: worker status is '{res.get('status')}'"
            )

        if res.get("offline_guard_installed") is not True:
            raise RuntimeError(
                "Snapshot integrity verification failed: offline guard is not installed in child!"
            )

        if res.get("attempted_egress_count", -1) != 0:
            raise RuntimeError(
                f"Snapshot integrity verification failed: attempted egress count is "
                f"{res.get('attempted_egress_count')} (expected 0)!"
            )

        ctrl_att = res.get("controller_attestation", {})
        if ctrl_att.get("exit_code") != 0:
            raise RuntimeError(
                f"Snapshot integrity verification failed: "
                f"worker exit code is {ctrl_att.get('exit_code')}"
            )

        runtime_att = res.get("worker_runtime_attestation", {})
        child_prefix = runtime_att.get("sys_prefix")
        expected_venv = (snapshot_root / ".venv").absolute()
        if not child_prefix or Path(child_prefix).absolute() != expected_venv:
            raise RuntimeError(
                f"Snapshot integrity verification failed: child sys.prefix '{child_prefix}' "
                f"does not match expected snapshot venv '{expected_venv}'!"
            )

        child_exe = runtime_att.get("sys_executable")
        expected_python = py_bin.absolute()
        if not child_exe:
            raise RuntimeError(
                "Snapshot integrity verification failed: child sys_executable missing!"
            )
        child_exe_path = Path(child_exe).absolute()
        if child_exe_path != expected_python:
            try:
                child_exe_path.relative_to(expected_venv)
            except ValueError:
                raise RuntimeError(
                    f"Snapshot integrity verification failed: child sys_executable '{child_exe}' "
                    f"is outside snapshot venv '{expected_venv}'!"
                )


def provision_snapshot(
    target_dir: Path,
    source_repo: Path,
    commit: str = EXPECTED_SNAPSHOT_GIT_COMMIT,
) -> Path:
    target_dir = target_dir.resolve()
    source_repo = source_repo.resolve()

    print("=== Provisioning Portable Snapshot ===")
    print(f"  Target directory: {target_dir}")
    print(f"  Source repo:      {source_repo}")
    print(f"  Commit:           {commit}")

    # 1. Containment check
    check_containment(target_dir, source_repo)

    created_by_this_invocation = False

    # 2. Existing directory check
    if target_dir.exists():
        has_entries = False
        try:
            has_entries = any(target_dir.iterdir())
        except Exception:
            pass

        if has_entries:
            # Reusing existing non-empty directory ONLY if verified clean snapshot
            is_valid_git = False
            if (target_dir / ".git").exists():
                p_head = subprocess.run(
                    ["git", "-C", str(target_dir), "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                )
                if p_head.returncode == 0 and p_head.stdout.strip() == commit:
                    p_status = subprocess.run(
                        ["git", "-C", str(target_dir), "status", "--porcelain=v1"],
                        capture_output=True,
                        text=True,
                    )
                    if p_status.returncode == 0 and not p_status.stdout.strip():
                        is_valid_git = True

            raw_attack = (
                target_dir
                / "attack"
                / "raw"
                / "enterprise-v19.2"
                / "enterprise-attack-19.2.json"
            )
            attack_ok = verify_sha256(raw_attack, EXPECTED_ATTACK_SHA256)
            venv_ok = (target_dir / ".venv" / "pyvenv.cfg").is_file()

            if is_valid_git and attack_ok and venv_ok:
                try:
                    _verify_full_snapshot_integrity(target_dir, commit)
                    print(f"Reusing existing valid clean snapshot at {target_dir}.")
                    _export_github_env(target_dir)
                    return target_dir
                except Exception as exc:
                    raise RuntimeError(
                        f"Target directory exists and is dirty/mismatched/foreign. "
                        f"Provisioning will not overwrite or clean existing directories: {exc}"
                    )
            else:
                raise RuntimeError(
                    "Target directory exists and is dirty/mismatched/foreign. "
                    "Provisioning will not overwrite or clean existing directories."
                )
    else:
        target_dir.mkdir(parents=True, exist_ok=True)
        created_by_this_invocation = True

    try:
        # Step 3: Independent local clone with verbatim attributes
        print(f"Cloning local repository into {target_dir}...")
        subprocess.run(
            ["git", "clone", "--no-checkout", "--local", str(source_repo), str(target_dir)],
            check=True,
        )

        _configure_verbatim_attributes(target_dir)
        subprocess.run(["git", "-C", str(target_dir), "checkout", "-f", commit], check=True)

        # Step 4: Populate ATT&CK reference JSON
        raw_dst = target_dir / "attack" / "raw" / "enterprise-v19.2" / "enterprise-attack-19.2.json"
        raw_dst.parent.mkdir(parents=True, exist_ok=True)
        raw_src = (
            source_repo
            / "attack"
            / "raw"
            / "enterprise-v19.2"
            / "enterprise-attack-19.2.json"
        )
        if verify_sha256(raw_src, EXPECTED_ATTACK_SHA256):
            print(f"Copying verified ATT&CK reference from {raw_src}...")
            shutil.copy(raw_src, raw_dst)
        else:
            print("Downloading ATT&CK v19.2 reference directly...")
            from src.attack_loader import download_attack_reference

            download_attack_reference(workspace_root=target_dir)

        if not verify_sha256(raw_dst, EXPECTED_ATTACK_SHA256):
            raise RuntimeError(f"ATT&CK raw reference checksum mismatch at {raw_dst}!")

        # Verify working tree remains completely clean
        p_status = subprocess.run(
            ["git", "-C", str(target_dir), "status", "--porcelain=v1"],
            capture_output=True,
            text=True,
            check=True,
        )
        if p_status.stdout.strip():
            raise RuntimeError(f"Snapshot working tree dirty after checkout:\n{p_status.stdout}")

        # Step 5: Provision dedicated virtual environment with uv sync --frozen
        print(f"Creating dedicated virtual environment in {target_dir}/.venv...")
        subprocess.run(["uv", "sync", "--frozen"], cwd=str(target_dir), check=True)

        pyvenv = target_dir / ".venv" / "pyvenv.cfg"
        if not pyvenv.is_file():
            raise RuntimeError(f"Failed to create virtual environment: missing {pyvenv}")

        # Step 6: Verify full snapshot integrity
        print("Verifying provisioned snapshot integrity...")
        _verify_full_snapshot_integrity(target_dir, commit)
        print("Snapshot integrity verified successfully.")

        _export_github_env(target_dir)
        return target_dir

    except Exception:
        if created_by_this_invocation and target_dir.exists():
            print(
                f"Cleaning up incomplete target directory created by this invocation: {target_dir}"
            )
            shutil.rmtree(target_dir, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Provision portable historical snapshot")
    default_target = os.environ.get("RAG2ATTCK_SNAPSHOT_ROOT")
    if not default_target:
        runner_temp = os.environ.get("RUNNER_TEMP")
        if runner_temp:
            default_target = str(Path(runner_temp) / "rag2attck_snapshot_b69a690")
        else:
            default_target = str(Path.cwd().parent / "rag2attck_snapshot_b69a690")

    parser.add_argument(
        "--target-dir",
        type=Path,
        default=Path(default_target),
        help="Target directory for provisioned snapshot",
    )
    parser.add_argument(
        "--source-repo",
        type=Path,
        default=Path("."),
        help="Source git repository",
    )
    parser.add_argument(
        "--commit",
        type=str,
        default=EXPECTED_SNAPSHOT_GIT_COMMIT,
        help="Target git commit",
    )
    args = parser.parse_args()

    try:
        snap_path = provision_snapshot(
            target_dir=args.target_dir,
            source_repo=args.source_repo,
            commit=args.commit,
        )
        print(f"SUCCESS: Snapshot provisioned at {snap_path}")
        return 0
    except Exception as exc:
        print(f"ERROR provisioning snapshot: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
