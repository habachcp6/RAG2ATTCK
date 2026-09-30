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
    validate_canonical_experiment_lock,
    validate_scientific_protocol,
)
from src.experiment.config import load_plan, parse_json
from src.experiment.path_safety import validate_untrusted_output_path
from src.experiment.runner import run_live_experiment


def _default_config() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "experiment_config.json"


def _default_protocol() -> Path:
    return Path(__file__).resolve().parents[2] / "config" / "experiment_protocol_v1.json"


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


def _handle_preflight(args: argparse.Namespace) -> int:
    repo_root = Path(__file__).resolve().parents[2]

    # 1. Clean source state check (unless allow_dirty is explicitly enabled)
    if not getattr(args, "allow_dirty", False):
        try:
            import subprocess

            res = subprocess.run(
                ["git", "status", "--porcelain", "src", "config", "prompts", "scripts"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.stdout.strip():
                print(
                    json.dumps(
                        {
                            "status": "LIVE_EXECUTION_BLOCKED",
                            "reason": (
                                "Source tree is dirty: git status reports uncommitted changes "
                                f"in tracked directories:\n{res.stdout.strip()}"
                            ),
                            "provider_calls": 0,
                            "prediction_writes": 0,
                        },
                        sort_keys=True,
                        indent=2,
                    ),
                    file=sys.stderr,
                )
                return 1
        except Exception as exc:
            print(
                json.dumps(
                    {
                        "status": "LIVE_EXECUTION_BLOCKED",
                        "reason": f"Failed to check git source cleanliness: {exc}",
                        "provider_calls": 0,
                        "prediction_writes": 0,
                    },
                    sort_keys=True,
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 1

    # 2. Check exact 40-character commit SHA
    try:
        import subprocess

        git_sha_res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        git_sha = git_sha_res.stdout.strip()
        import re

        if len(git_sha) != 40 or not re.fullmatch(r"[0-9a-f]{40}", git_sha):
            print(
                json.dumps(
                    {
                        "status": "LIVE_EXECUTION_BLOCKED",
                        "reason": f"Invalid Git commit SHA: {git_sha}",
                        "provider_calls": 0,
                        "prediction_writes": 0,
                    },
                    sort_keys=True,
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 1
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "reason": f"Git commit SHA check failed: {exc}",
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                sort_keys=True,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    # 3. Protocol file & cryptographic hash validation
    protocol_path = Path(args.protocol_file if args.protocol_file else _default_protocol())
    if not protocol_path.exists():
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "reason": f"Scientific protocol file not found at {protocol_path}",
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                sort_keys=True,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    try:
        proto_dict = parse_json(protocol_path.read_bytes())
        protocol = ScientificProtocolApproval(**proto_dict)
        validate_scientific_protocol(protocol)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "reason": f"Scientific protocol validation failed: {exc}",
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                sort_keys=True,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    # 4. Plan load and artifact hash check
    config_path = Path(args.config if args.config else _default_config())
    try:
        plan = load_plan(config_path)
        validate_scientific_protocol(protocol, plan)
        validate_canonical_experiment_lock(plan, protocol, root=repo_root)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "reason": (
                        "Plan loading, protocol compatibility, or canonical lock check "
                        f"failed: {exc}"
                    ),
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                sort_keys=True,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    # 5. Sequential concurrency check
    if (
        protocol.d4_concurrency_policy != "SEQUENTIAL_ONLY"
        or plan.config.execution.concurrency != 1
    ):
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "reason": (
                        "Concurrency policy must be SEQUENTIAL_ONLY and "
                        "execution concurrency in config must be explicitly 1"
                    ),
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                sort_keys=True,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    # 6. Budget check
    if not plan.config.execution.max_requests or plan.config.execution.max_requests <= 0:
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "reason": (
                        "Execution configuration must define an explicit "
                        "positive max_requests budget"
                    ),
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                sort_keys=True,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    from src.experiment.schemas import CONDITIONS

    worst_case_attempts = (
        len(plan.samples) * len(CONDITIONS) * (plan.config.execution.retries + 1)
    )
    if protocol.d5_budget_policy != "HARD_CAP_WORST_CASE_ATTEMPTS":
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "reason": (
                        f"Budget policy must be HARD_CAP_WORST_CASE_ATTEMPTS, "
                        f"got {protocol.d5_budget_policy}"
                    ),
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                sort_keys=True,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    if args.max_attempts is not None and args.max_attempts < worst_case_attempts:
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "reason": (
                        f"Provided max-attempts ({args.max_attempts}) is less than "
                        f"worst-case attempts ({worst_case_attempts})"
                    ),
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                sort_keys=True,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    # 7. Output directory safety check
    output_dir = getattr(args, "output_dir", None)
    if output_dir is None:
        output_dir = repo_root / "artifacts" / "experiments" / plan.manifest["experiment_id"]
    try:
        validated_output = validate_untrusted_output_path(output_dir)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "reason": f"Output path safety validation failed for {output_dir}: {exc}",
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                sort_keys=True,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    # 8. Evaluator contract validation
    try:
        from src.evaluation.experiment_metrics import validate_evaluator_compatibility

        validate_evaluator_compatibility(protocol, plan)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "reason": f"Evaluator contract compatibility validation failed: {exc}",
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                sort_keys=True,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    # 9. Credentials check (informational; fail-closed if require_credentials is set)
    import os

    has_key = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    if getattr(args, "require_credentials", False) and not has_key:
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "reason": "OPENAI_API_KEY is not configured in environment",
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                sort_keys=True,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    # 10. Scoped test authorization token check (fail closed if provided but empty/whitespace)
    test_token = getattr(args, "test_authorization_token", None)
    if test_token is not None:
        if not isinstance(test_token, str) or not test_token.strip():
            print(
                json.dumps(
                    {
                        "status": "LIVE_EXECUTION_BLOCKED",
                        "reason": "Test authorization token cannot be empty or whitespace",
                        "provider_calls": 0,
                        "prediction_writes": 0,
                    },
                    sort_keys=True,
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 1

    # 11. Success: All preflight gates satisfied; strictly 0 provider calls, 0 prediction writes
    is_test_split = plan.manifest.get("split") == "test"
    test_auth_status = (
        "AUTHORIZED"
        if test_token and test_token.strip()
        else ("UNAUTHORIZED_PRE_EXPERIMENT" if is_test_split else "NOT_APPLICABLE_DEV")
    )

    report = {
        "status": "EXPERIMENT_PREFLIGHT_READY",
        "protocol_version": protocol.protocol_version,
        "protocol_sha256": protocol.protocol_sha256,
        "git_commit_sha": git_sha,
        "experiment_id": plan.manifest["experiment_id"],
        "split": plan.manifest["split"],
        "sample_count": len(plan.samples),
        "condition_count": len(CONDITIONS),
        "expected_requests": len(plan.samples) * len(CONDITIONS),
        "worst_case_attempts": worst_case_attempts,
        "concurrency": plan.config.execution.concurrency,
        "provider_calls_during_preflight": 0,
        "has_openai_key": has_key,
        "evaluator_contract_valid": True,
        "output_path_safe": True,
        "output_directory": str(validated_output),
        "test_split_protection": (
            "BLOCKED_WITHOUT_HUMAN_AUTHORIZATION" if is_test_split else "DEV_ONLY"
        ),
        "test_authorization_status": test_auth_status,
        "canonical_test_provider_calls": 0,
        "provider_calls": 0,
        "prediction_writes": 0,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def _handle_evaluate(args: argparse.Namespace) -> int:
    try:
        from src.evaluation.experiment_metrics import (
            CONDITIONS,
            evaluate_experiment,
            load_evaluation_inputs,
        )

        protocol_path = Path(args.protocol_file if args.protocol_file else _default_protocol())
        proto_dict = parse_json(protocol_path.read_bytes())
        protocol = ScientificProtocolApproval(**proto_dict)

        manifest_path = Path(args.manifest).resolve()
        manifest_dir = manifest_path.parent
        prediction_paths = {c: manifest_dir / f"{c}_predictions.jsonl" for c in CONDITIONS}

        repo_root = (
            Path(args.repository_root).resolve()
            if args.repository_root
            else Path(__file__).resolve().parents[2]
        )

        inputs = load_evaluation_inputs(
            manifest_path,
            prediction_paths,
            repository_root=repo_root,
        )

        results = evaluate_experiment(
            inputs,
            protocol,
            output_dir=args.output_dir,
            expected_experiment_id=args.expected_experiment_id,
        )

        print(json.dumps(results["overall"], indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "EVALUATION_FAILED",
                    "error": str(exc),
                },
                sort_keys=True,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1


def _handle_live(args: argparse.Namespace, *, provider_factory=None) -> int:
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
            provider_factory=provider_factory,
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


def _handle_resume(args: argparse.Namespace, *, provider_factory=None) -> int:
    try:
        output_dir = validate_untrusted_output_path(args.output_dir)
    except ValueError as exc:
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "reason": str(exc),
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

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

    if not args.auth_token:
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "reason": "--auth-token is required to resume live execution; "
                    "re-authorization cannot be implicitly inherited from disk",
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    if not args.allow_live_dispatch:
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "reason": "--allow-live-dispatch is required to resume live execution",
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
        proto_sha = manifest.get("protocol_sha256")
        if not proto_data or not proto_sha:
            print(
                json.dumps(
                    {
                        "status": "HUMAN_DECISION_REQUIRED",
                        "reason": "Manifest lacks approved scientific protocol",
                        "provider_calls": 0,
                        "prediction_writes": 0,
                    },
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
            return 1

        if "protocol_sha256" not in proto_data:
            proto_data = {**proto_data, "protocol_sha256": proto_sha}

        protocol = ScientificProtocolApproval(**proto_data)

        if args.protocol_file:
            verify_proto = ScientificProtocolApproval(
                **parse_json(Path(args.protocol_file).read_bytes())
            )
            if verify_proto.protocol_sha256 != protocol.protocol_sha256:
                print(
                    json.dumps(
                        {
                            "status": "LIVE_EXECUTION_BLOCKED",
                            "reason": (
                                "Provided --protocol-file does not match manifest protocol SHA-256"
                            ),
                            "provider_calls": 0,
                            "prediction_writes": 0,
                        },
                        sort_keys=True,
                    ),
                    file=sys.stderr,
                )
                return 1

        max_attempts = (
            args.max_attempts
            if args.max_attempts is not None
            else manifest.get("authorized_max_provider_attempts")
        )

        auth = ExecutionAuthorization(
            human_approval_token=args.auth_token,
            approved_protocol_sha256=protocol.protocol_sha256,
            authorized_max_provider_attempts=max_attempts,
            allow_live_dispatch=args.allow_live_dispatch,
        )

        plan = load_plan(args.config)

        gate_check = check_live_execution_gates(plan, auth, protocol=protocol)
        if not gate_check["live_execution_permitted"]:
            print(
                json.dumps(
                    {
                        "status": "LIVE_EXECUTION_BLOCKED",
                        "reason": gate_check.get("reason", "Live execution gates failed on resume"),
                        "provider_calls": 0,
                        "prediction_writes": 0,
                    },
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
            return 1

        summary = run_live_experiment(
            plan=plan,
            directory=output_dir,
            authorization=auth,
            protocol=protocol,
            provider_factory=provider_factory,
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


def main(argv=None, *, provider_factory=None) -> int:
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
        "--auth-token", type=str, help="Human authorization approval token required to resume"
    )
    resume_parser.add_argument(
        "--allow-live-dispatch",
        action="store_true",
        help="Explicit live dispatch permission",
    )
    resume_parser.add_argument(
        "--max-attempts", type=int, help="Authorized max provider attempts"
    )
    resume_parser.add_argument(
        "--protocol-file", type=Path, help="Optional path to verify frozen D1-D7 protocol"
    )
    resume_parser.add_argument(
        "--stop-after", type=int, help="Optional stop-after limit for staged execution"
    )

    # preflight subcommand
    preflight_parser = subparsers.add_parser(
        "preflight", help="Validate frozen protocol, git cleanliness, and plan readiness"
    )
    preflight_parser.add_argument(
        "--config",
        type=Path,
        default=_default_config(),
        help="Path to experiment_config.json",
    )
    preflight_parser.add_argument(
        "--protocol-file",
        type=Path,
        default=_default_protocol(),
        help="Path to frozen experiment_protocol_v1.json",
    )
    preflight_parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow uncommitted git status in tracked directories (test-only)",
    )
    preflight_parser.add_argument(
        "--require-credentials",
        action="store_true",
        help="Enforce OPENAI_API_KEY presence during preflight",
    )
    preflight_parser.add_argument(
        "--max-attempts",
        type=int,
        help="Authorized max provider attempts to verify against worst-case policy",
    )
    preflight_parser.add_argument(
        "--output-dir",
        type=Path,
        help="Optional candidate output directory to validate path safety",
    )
    preflight_parser.add_argument(
        "--test-authorization-token",
        type=str,
        help="Human authorization token for canonical TEST split execution",
    )

    # evaluate subcommand
    eval_parser = subparsers.add_parser(
        "evaluate", help="Execute canonical evaluation on completed run directory"
    )
    eval_parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="Path to run manifest.json",
    )
    eval_parser.add_argument(
        "--protocol-file",
        type=Path,
        default=_default_protocol(),
        help="Path to frozen experiment_protocol_v1.json",
    )
    eval_parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory to write canonical evaluation JSON artifacts",
    )
    eval_parser.add_argument(
        "--expected-experiment-id",
        type=str,
        help="Optional experiment ID to verify fail-closed against provenance",
    )
    eval_parser.add_argument(
        "--repository-root",
        type=Path,
        help="Repository root for artifact validation",
    )

    args = parser.parse_args(argv)

    if args.subcommand == "preflight":
        return _handle_preflight(args)
    if args.subcommand == "evaluate":
        return _handle_evaluate(args)
    if args.subcommand == "dry-run" or args.dry_run:
        return _handle_dry_run(args)
    if args.subcommand == "live":
        return _handle_live(args, provider_factory=provider_factory)
    if args.subcommand == "resume":
        return _handle_resume(args, provider_factory=provider_factory)

    parser.error(
        "a valid subcommand (preflight, evaluate, dry-run, live, resume) or --dry-run is required"
    )


if __name__ == "__main__":
    raise SystemExit(main())
