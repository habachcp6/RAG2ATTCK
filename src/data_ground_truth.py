"""
RAG2ATTCK Staged CLI Entrypoint for Data & Ground Truth Pipeline
Provides command-line commands for executing pipeline tasks cleanly and deterministically.
"""

import argparse
from pathlib import Path
import sys

# Ensure workspace root is on sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.dataset import run_preflight_check, get_default_workspace_root, PreflightGateBlocked


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
        print(f"[+] Artifact generated: data/metadata/preflight.json")
        return 0
    except PreflightGateBlocked as e:
        print(f"[-] Preflight GATE BLOCKED: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(description="RAG2ATTCK Data & Ground Truth Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", help="Pipeline task command")

    # Preflight
    p_preflight = subparsers.add_parser("preflight", help="Execute Task 0 Preflight check")
    p_preflight.add_argument("--workspace", "-w", type=str, default=None, help="Workspace root path")
    p_preflight.add_argument("--recheck", action="store_true", help="Recheck dynamic capacity at runtime")
    p_preflight.set_defaults(func=cmd_preflight)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
