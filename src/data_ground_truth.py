"""
RAG2ATTCK Staged CLI Entrypoint for Data & Ground Truth Pipeline
Provides command-line commands for executing pipeline tasks cleanly and deterministically.
"""

import argparse
import sys
from pathlib import Path

# Direct-file execution bootstrap: ensure repository root is in sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.acquisition import acquire_windows_apt_dataset  # noqa: E402
from src.artifacts import ArtifactValidationError, validate_stage_prerequisites  # noqa: E402
from src.attack_loader import (  # noqa: E402
    download_attack_reference,
    generate_attack_manifest,
    parse_attack_bundle,
)
from src.dataset import (  # noqa: E402
    PreflightGateBlocked,
    get_default_workspace_root,
    run_preflight_check,
)
from src.ground_truth import verify_ground_truth_provenance  # noqa: E402
from src.profiler import profile_dataset_schemas  # noqa: E402
from src.reconcile import run_multiset_reconciliation  # noqa: E402


def _validate_or_exit(ws: Path, stage_name: str) -> None:
    try:
        validate_stage_prerequisites(ws, stage_name)
    except ArtifactValidationError as e:
        print(f"[-] Gate validation failed for '{stage_name}': {e}")
        sys.exit(1)


def cmd_preflight(args):
    ws = Path(args.workspace) if args.workspace else get_default_workspace_root()
    print(f"[*] Executing Task 0 Preflight check on workspace: {ws}")
    try:
        res = run_preflight_check(ws, recheck=args.recheck)
        print(f"[+] Task 0 Preflight Status: {res['gate_result']['status']}")
        print(f"[+] Free Disk Space: {res['capacity_assessment']['live_free_gib']} GiB")
        print(f"[+] Gate Floor: {res['capacity_assessment']['effective_required_free_gib']} GiB")
        print(f"[+] Headroom: +{res['capacity_assessment']['headroom_gib']} GiB")
        print(f"[+] Paths Contained: {res['path_validation']['all_paths_contained']}")
        print("[+] Artifact generated: data/metadata/preflight.json")
        return 0
    except PreflightGateBlocked as e:
        print(f"[-] Preflight GATE BLOCKED: {e}")
        return 1


def cmd_acquire_attack(args):
    ws = Path(args.workspace) if args.workspace else get_default_workspace_root()
    _validate_or_exit(ws, "acquire-attack")
    print(f"[*] Executing Task 5-acquire ATT&CK v19.2 reference on workspace: {ws}")
    try:
        stix_file, sha256_hash, file_size = download_attack_reference(ws)
        print(f"[+] Downloaded/Verified STIX file: {stix_file} ({file_size} bytes)")
        print(f"[+] STIX SHA-256: {sha256_hash}")
        techniques = parse_attack_bundle(stix_file)
        manifest_file = generate_attack_manifest(ws, stix_file, sha256_hash, file_size, techniques)
        print(f"[+] Manifest generated: {manifest_file}")
        return 0
    except Exception as e:
        print(f"[-] acquire-attack failed: {e}")
        return 1


def cmd_acquire_dataset(args):
    ws = Path(args.workspace) if args.workspace else get_default_workspace_root()
    _validate_or_exit(ws, "acquire-dataset")
    print(f"[*] Executing Task 2 Dataset Acquisition on workspace: {ws}")
    try:
        manifest = acquire_windows_apt_dataset(ws)
        print(
            f"[+] Dataset acquisition complete. Files: {manifest['total_files']}, "
            f"Total bytes: {manifest['total_bytes']}"
        )
        print("[+] Manifest generated: data/metadata/dataset_manifest.json")
        return 0
    except Exception as e:
        print(f"[-] acquire-dataset failed: {e}")
        return 1


def cmd_reconcile(args):
    ws = Path(args.workspace) if args.workspace else get_default_workspace_root()
    _validate_or_exit(ws, "reconcile")
    print(f"[*] Executing Task 2 Multiset Reconciliation on workspace: {ws}")
    try:
        res = run_multiset_reconciliation(ws)
        print(f"[+] Reconciliation status: {res['multiset_equality_status']}")
        print(f"[+] Period row count: {res['row_count_accounting']['total_period_rows']}")
        print(f"[+] Combined row count: {res['row_count_accounting']['total_combined_rows']}")
        print(
            "[+] Reconciled artifacts: data/metadata/reconciliation_log.json, "
            "data/audit/reconciliation_report.md"
        )
        return 0
    except Exception as e:
        print(f"[-] reconcile failed: {e}")
        return 1


def cmd_profile(args):
    ws = Path(args.workspace) if args.workspace else get_default_workspace_root()
    _validate_or_exit(ws, "profile")
    print(f"[*] Executing Task 3 Schema Profiling & Record Indexing on workspace: {ws}")
    try:
        res = profile_dataset_schemas(ws)
        print(
            f"[+] Profiling complete. Logical rows: {res['source_logical_rows']}, "
            f"Parsed: {res['successfully_parsed_records']}, "
            f"Malformed: {res['rejected_malformed_records']}"
        )
        print(f"[+] Distinct fields: {res['unique_field_count']}")
        print(
            "[+] Artifacts: data/metadata/schema_profile.json, data/metadata/record_index.csv, "
            "data/metadata/parse_error_ledger.json"
        )
        return 0
    except Exception as e:
        print(f"[-] profile failed: {e}")
        return 1


def cmd_audit_gt(args):
    ws = Path(args.workspace) if args.workspace else get_default_workspace_root()
    _validate_or_exit(ws, "audit-gt")
    print(f"[*] Executing Task 4 Independent Ground Truth Lineage Audit on workspace: {ws}")
    try:
        diagnostics = verify_ground_truth_provenance(ws)
        print(f"[+] Task 4 Gate Status: {diagnostics['gate_status']}")
        print(f"[+] Independent lineage available: {diagnostics['independent_lineage_available']}")
        print(f"[+] Records with Wazuh rule: {diagnostics['records_with_wazuh_rule']}")
        print(f"[+] Records with MITRE mapping: {diagnostics['records_with_mitre_mapping']}")
        print(f"[+] Unlabeled records: {diagnostics['unlabeled_records']}")
        print("[+] Artifacts generated:")
        print("    - data/metadata/join_diagnostics.json")
        print("    - data/metadata/ground_truth_register.json")
        print("    - data/metadata/gate_blocker_task4.json")
        print("    - reports/ground_truth_provenance.md")
        print("    - reports/gate_blocker_task4.md")
        return 0
    except Exception as e:
        print(f"[-] audit-gt failed: {e}")
        return 1


def cmd_synthetic(args):
    import json

    from src.synthetic_pipeline import (
        freeze_synthetic,
        prepare_synthetic,
        validate_synthetic,
        verify_synthetic,
    )

    # Synthetic stages are portable and independent of the historical Windows
    # acquisition workspace. Resolve the default from this module, never CWD.
    ws = Path(args.workspace).resolve() if args.workspace else Path(__file__).resolve().parents[1]
    try:
        if args.command == "prepare-synthetic":
            result = prepare_synthetic(ws, args.output_dir)
        elif args.command == "validate-synthetic":
            result = validate_synthetic(ws, args.candidate_dir)
        elif args.command == "freeze-synthetic":
            result = freeze_synthetic(ws, args.candidate_dir, args.output_dir)
        else:
            result = verify_synthetic(ws, args.output_dir)
        print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"Synthetic gate FAILED: {exc}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="RAG2ATTCK Data & Ground Truth Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", help="Pipeline task command")

    for command in (
        "prepare-synthetic",
        "validate-synthetic",
        "freeze-synthetic",
        "verify-synthetic",
    ):
        sub = subparsers.add_parser(command, help="Independent synthetic Stage B gate")
        sub.add_argument("--workspace", "-w", default=None, help="Workspace root")
        sub.add_argument(
            "--output-dir",
            type=Path,
            default=None,
            help="Candidate/frozen directory for this stage",
        )
        sub.add_argument(
            "--candidate-dir", type=Path, default=None, help="Prepared candidate directory"
        )
        sub.set_defaults(func=cmd_synthetic)

    # Preflight
    p_preflight = subparsers.add_parser("preflight", help="Execute Task 0 Preflight check")
    p_preflight.add_argument(
        "--workspace", "-w", type=str, default=None, help="Workspace root path"
    )
    p_preflight.add_argument(
        "--recheck", action="store_true", help="Recheck dynamic capacity at runtime"
    )
    p_preflight.set_defaults(func=cmd_preflight)

    # Acquire ATT&CK Reference
    p_acquire_attack = subparsers.add_parser(
        "acquire-attack", help="Execute Task 5-acquire ATT&CK reference acquisition"
    )
    p_acquire_attack.add_argument(
        "--workspace", "-w", type=str, default=None, help="Workspace root path"
    )
    p_acquire_attack.set_defaults(func=cmd_acquire_attack)

    # Acquire Dataset
    p_acquire_dataset = subparsers.add_parser(
        "acquire-dataset", help="Execute Task 2 Windows-APT dataset acquisition"
    )
    p_acquire_dataset.add_argument(
        "--workspace", "-w", type=str, default=None, help="Workspace root path"
    )
    p_acquire_dataset.set_defaults(func=cmd_acquire_dataset)

    # Reconcile
    p_reconcile = subparsers.add_parser("reconcile", help="Execute Task 2 Multiset Reconciliation")
    p_reconcile.add_argument(
        "--workspace", "-w", type=str, default=None, help="Workspace root path"
    )
    p_reconcile.set_defaults(func=cmd_reconcile)

    # Profile
    p_profile = subparsers.add_parser(
        "profile", help="Execute Task 3 Schema Profiling & Record Indexing"
    )
    p_profile.add_argument("--workspace", "-w", type=str, default=None, help="Workspace root path")
    p_profile.set_defaults(func=cmd_profile)

    # Audit Ground Truth
    p_audit_gt = subparsers.add_parser(
        "audit-gt", help="Execute Task 4 Independent Ground Truth Lineage Audit"
    )
    p_audit_gt.add_argument("--workspace", "-w", type=str, default=None, help="Workspace root path")
    p_audit_gt.set_defaults(func=cmd_audit_gt)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
