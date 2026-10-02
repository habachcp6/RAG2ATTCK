#!/usr/bin/env python3
"""
scripts/provision_snapshot.py

Provision a clean, portable historical snapshot at commit b69a690 outside engineering checkout.
Ensures:
1. Exact Git commit b69a6909acda4c7588744acc7e1d6c20bfce2612 with a clean working tree.
2. Verified ATT&CK reference at attack/raw/enterprise-v19.2/enterprise-attack-19.2.json.
3. Dedicated venv in .venv with pyvenv.cfg and dependencies installed via 'uv sync --frozen'.
4. Full expanded inventory preflight (53 core files, 22 baselines, f85 analysis, protocol, lock).

Pure standard-library runner with uv subprocess calls.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
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

    # Step 1: Check if already provisioned and fully valid
    if (target_dir / ".git").exists() and (target_dir / ".venv" / "pyvenv.cfg").is_file():
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
            raw_attack = (
                target_dir
                / "attack"
                / "raw"
                / "enterprise-v19.2"
                / "enterprise-attack-19.2.json"
            )
            attack_ok = verify_sha256(raw_attack, EXPECTED_ATTACK_SHA256)
            if p_status.returncode == 0 and not p_status.stdout.strip() and attack_ok:
                print(f"Snapshot at {target_dir} is already valid and clean.")
                return target_dir

    # Step 2: Create directory and checkout commit
    target_dir.mkdir(parents=True, exist_ok=True)
    if not (target_dir / ".git").exists():
        # Try worktree add first (fast, shares objects)
        print(f"Creating git worktree at {target_dir} for commit {commit}...")
        res = subprocess.run(
            [
                "git",
                "-C",
                str(source_repo),
                "worktree",
                "add",
                "--detach",
                str(target_dir),
                commit,
            ],
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            print(f"Worktree creation failed ({res.stderr.strip()}), falling back to clone...")
            shutil.rmtree(target_dir, ignore_errors=True)
            subprocess.run(
                ["git", "clone", "--no-checkout", str(source_repo), str(target_dir)],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(target_dir), "checkout", "-f", commit],
                check=True,
            )

    # Ensure clean Git state at exact commit
    subprocess.run(["git", "-C", str(target_dir), "checkout", "-f", commit], check=True)
    subprocess.run(["git", "-C", str(target_dir), "reset", "--hard", "HEAD"], check=True)
    subprocess.run(["git", "-C", str(target_dir), "clean", "-fd"], check=True)

    # Step 3: Populate ATT&CK reference JSON
    raw_dst = target_dir / "attack" / "raw" / "enterprise-v19.2" / "enterprise-attack-19.2.json"
    raw_dst.parent.mkdir(parents=True, exist_ok=True)
    if not verify_sha256(raw_dst, EXPECTED_ATTACK_SHA256):
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

    # Verify working tree remains clean
    p_status = subprocess.run(
        ["git", "-C", str(target_dir), "status", "--porcelain=v1"],
        capture_output=True,
        text=True,
        check=True,
    )
    if p_status.stdout.strip():
        raise RuntimeError(f"Snapshot working tree dirty after checkout:\n{p_status.stdout}")

    # Step 4: Provision dedicated virtual environment with uv sync --frozen
    print(f"Creating dedicated virtual environment in {target_dir}/.venv...")
    subprocess.run(["uv", "sync", "--frozen"], cwd=str(target_dir), check=True)

    pyvenv = target_dir / ".venv" / "pyvenv.cfg"
    if not pyvenv.is_file():
        raise RuntimeError(f"Failed to create virtual environment: missing {pyvenv}")

    # Step 5: Self-verify using controller functions
    print("Verifying provisioned snapshot integrity...")
    from scripts.isolated_snapshot_controller import (
        compute_expanded_snapshot_inventory,
        resolve_snapshot_python,
        verify_snapshot_git_identity,
    )
    verify_snapshot_git_identity(target_dir)
    resolve_snapshot_python(target_dir)
    inventory = compute_expanded_snapshot_inventory(target_dir)
    core_count = inventory["core_files_count"]
    baselines_count = inventory["protected_baselines_count"]
    print(f"Snapshot verified: {core_count} core files, {baselines_count} baselines.")

    # Export to GITHUB_ENV if running in GitHub Actions
    gh_env = os.environ.get("GITHUB_ENV")
    if gh_env:
        with open(gh_env, "a", encoding="utf-8") as f:
            f.write(f"RAG2ATTCK_SNAPSHOT_ROOT={target_dir.as_posix()}\n")
        print(f"Exported RAG2ATTCK_SNAPSHOT_ROOT={target_dir.as_posix()} to GITHUB_ENV.")

    return target_dir


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
