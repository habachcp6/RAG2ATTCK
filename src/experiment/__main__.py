"""Public CLI interface: subcommands for dry-run preflight, live dispatch, and resume.

Default invocation NEVER executes live.
Live execution requires explicit subcommands, validated protocol approval,
and runtime execution authorization.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.experiment.authorization import (
    ExecutionAuthorization,
    LiveExecutionBlockedError,
    ProtocolNotFrozenError,
    ScientificProtocolApproval,
    check_live_execution_gates,
)
from src.experiment.config import load_plan, parse_json
from src.experiment.runner import run_live_experiment


def _default_config() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "experiment_config.json"


def _handle_dry_run(args: argparse.Namespace) -> int:
    try:
        report = load_plan(args.config).report()
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(
            json.dumps(
                {"status": "BLOCKED", "error": str(exc), "provider_calls": 0},
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    # Structural validation is not permission to execute a scientific experiment.
    return 2


def _handle_live(args: argparse.Namespace) -> int:
    try:
        plan = load_plan(args.config)
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "error": str(exc),
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    # Load protocol if provided
    protocol = None
    if args.protocol_file:
        try:
            proto_dict = parse_json(Path(args.protocol_file).read_bytes())
            protocol = ScientificProtocolApproval(**proto_dict)
        except Exception as exc:
            print(
                json.dumps(
                    {
                        "status": "HUMAN_DECISION_REQUIRED",
                        "error": f"Invalid protocol file: {exc}",
                        "provider_calls": 0,
                        "prediction_writes": 0,
                    },
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
            return 1

    # Construct authorization
    auth = None
    if args.auth_token:
        auth = ExecutionAuthorization(
            human_approval_token=args.auth_token,
            approved_protocol_sha256=protocol.protocol_sha256 if protocol else None,
            authorized_max_provider_attempts=args.max_attempts,
            allow_live_dispatch=args.allow_live_dispatch,
        )

    # Check live execution gates
    gate_check = check_live_execution_gates(plan, auth, protocol=protocol)
    if not gate_check["live_execution_permitted"]:
        status = "HUMAN_DECISION_REQUIRED" if protocol is None else "LIVE_EXECUTION_BLOCKED"
        print(
            json.dumps(
                {
                    "status": status,
                    "reason": gate_check.get("reason", "Live execution gates failed"),
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                indent=2,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    if not args.output_dir:
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "reason": "--output-dir is required for live execution",
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    try:
        summary = run_live_experiment(
            plan=plan,
            directory=args.output_dir,
            authorization=auth,
            protocol=protocol,
            stop_after=args.stop_after,
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    except (LiveExecutionBlockedError, ProtocolNotFrozenError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "error": str(exc),
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1


def _handle_resume(args: argparse.Namespace) -> int:
    output_dir = Path(args.output_dir).resolve()
    manifest_path = output_dir / "manifest.json"
    if not manifest_path.exists():
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "reason": f"Manifest not found in {output_dir}",
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    try:
        manifest = parse_json(manifest_path.read_bytes())
        proto_data = manifest.get("protocol")
        if not proto_data or not manifest.get("protocol_sha256"):
            print(
                json.dumps(
                    {
                        "status": "HUMAN_DECISION_REQUIRED",
                        "reason": "Manifest lacks approved scientific protocol",
                        "provider_calls": 0,
                        "prediction_writes": 0,
                    },
                    sort_keys=True,
                )
            )
            return 1
        protocol = ScientificProtocolApproval(**proto_data)
        token = manifest.get("human_authorization_token", "")
        max_attempts = manifest.get("authorized_max_provider_attempts")
        auth = ExecutionAuthorization(
            human_approval_token=token,
            approved_protocol_sha256=protocol.protocol_sha256,
            authorized_max_provider_attempts=max_attempts,
            allow_live_dispatch=True,
        )
        plan = load_plan(args.config)
        summary = run_live_experiment(
            plan=plan,
            directory=output_dir,
            authorization=auth,
            protocol=protocol,
            resume=True,
            stop_after=args.stop_after,
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "error": str(exc),
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="RAG2ATT&CK Experiment CLI (dry-run preflight, live dispatch, resume)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=_default_config(),
        help="Path to experiment_config.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Legacy flag: validate pre-freeze plan without execution",
    )

    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # dry-run subcommand
    dry_parser = subparsers.add_parser("dry-run", help="Validate plan without execution")
    dry_parser.add_argument(
        "--config",
        type=Path,
        default=_default_config(),
        help="Path to experiment_config.json",
    )

    # live subcommand
    live_parser = subparsers.add_parser(
        "live", help="Execute live experiment (requires authorization)"
    )
    live_parser.add_argument(
        "--config",
        type=Path,
        default=_default_config(),
        help="Path to experiment_config.json",
    )
    live_parser.add_argument("--output-dir", type=Path, help="Directory to store live results")
    live_parser.add_argument(
        "--protocol-file", type=Path, help="Path to JSON file with frozen D1-D7 protocol"
    )
    live_parser.add_argument("--auth-token", type=str, help="Human authorization approval token")
    live_parser.add_argument(
        "--max-attempts", type=int, help="Authorized max provider attempts"
    )
    live_parser.add_argument(
        "--allow-live-dispatch",
        action="store_true",
        help="Explicit live dispatch permission",
    )
    live_parser.add_argument(
        "--stop-after", type=int, help="Optional stop-after limit for staged execution"
    )

    # resume subcommand
    resume_parser = subparsers.add_parser("resume", help="Resume interrupted live experiment")
    resume_parser.add_argument(
        "--config",
        type=Path,
        default=_default_config(),
        help="Path to experiment_config.json",
    )
    resume_parser.add_argument(
        "--output-dir", type=Path, required=True, help="Run directory to resume"
    )
    resume_parser.add_argument(
        "--stop-after", type=int, help="Optional stop-after limit for staged execution"
    )

    args = parser.parse_args(argv)

    if args.subcommand == "dry-run" or args.dry_run:
        return _handle_dry_run(args)
    if args.subcommand == "live":
        return _handle_live(args)
    if args.subcommand == "resume":
        return _handle_resume(args)

    parser.error("a valid subcommand (dry-run, live, resume) or --dry-run is required")


if __name__ == "__main__":
    raise SystemExit(main())
