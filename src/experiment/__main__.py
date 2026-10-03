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
    LiveBudgetRequiredError,
    LiveExecutionBlockedError,
    ProtocolNotFrozenError,
    ScientificProtocolApproval,
    validate_experiment_readiness,
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

    # Protocol file check
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

    # Plan load
    config_path = Path(args.config if args.config else _default_config())
    try:
        plan = load_plan(config_path)
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

    # Shared preflight readiness validation (BLOCKER-2)
    try:
        report = validate_experiment_readiness(
            plan=plan,
            protocol=protocol,
            repo_root=repo_root,
            output_dir=getattr(args, "output_dir", None),
            max_attempts=getattr(args, "max_attempts", None),
            allow_dirty=getattr(args, "allow_dirty", False),
            is_live=False,
        )
    except (
        LiveExecutionBlockedError,
        ProtocolNotFrozenError,
        LiveBudgetRequiredError,
        ValueError,
    ) as exc:
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "reason": str(exc),
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

    # 10. Scoped test authorization token check (fail closed if provided but not a valid contract)
    test_token = getattr(args, "test_authorization_token", None)
    is_test_split = plan.manifest.get("split") == "test"
    test_auth_status = "UNAUTHORIZED_PRE_EXPERIMENT" if is_test_split else "NOT_APPLICABLE_DEV"
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

        contract_data = None
        token_path = Path(test_token.strip())
        if token_path.is_file():
            try:
                contract_data = json.loads(token_path.read_bytes())
            except Exception as exc:
                print(
                    json.dumps(
                        {
                            "status": "LIVE_EXECUTION_BLOCKED",
                            "reason": f"Failed to parse test authorization contract file: {exc}",
                            "provider_calls": 0,
                            "prediction_writes": 0,
                        },
                        sort_keys=True,
                        indent=2,
                    ),
                    file=sys.stderr,
                )
                return 1
        else:
            try:
                contract_data = json.loads(test_token)
            except Exception:
                contract_data = None

        if not isinstance(contract_data, dict):
            print(
                json.dumps(
                    {
                        "status": "LIVE_EXECUTION_BLOCKED",
                        "reason": (
                            "Scoped test authorization token must be a valid JSON contract "
                            "or path to an authorization contract file"
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

        try:
            from src.experiment.authorization import (
                ExecutionAuthorization,
                validate_live_authorization,
            )

            auth_contract = ExecutionAuthorization(
                human_approval_token=contract_data.get("human_approval_token", ""),
                approved_protocol_sha256=contract_data.get("approved_protocol_sha256"),
                authorized_max_provider_attempts=contract_data.get(
                    "authorized_max_provider_attempts",
                    contract_data.get("authorized_max_requests"),
                ),
                allow_live_dispatch=bool(contract_data.get("allow_live_dispatch", False)),
            )
            validate_live_authorization(auth_contract, plan, protocol)
            test_auth_status = "AUTHORIZED"
        except Exception as exc:
            print(
                json.dumps(
                    {
                        "status": "LIVE_EXECUTION_BLOCKED",
                        "reason": f"Scoped test authorization contract validation failed: {exc}",
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
    report["has_openai_key"] = has_key
    report["test_authorization_status"] = test_auth_status
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


def _inspect_historical_counts(output_dir: Path | str | None) -> tuple[int, int]:
    """Inspect output directory journal to extract historical provider calls and writes.

    Returns (provider_calls, prediction_writes).
    """
    if output_dir is None:
        return 0, 0
    calls = 0
    writes = 0
    try:
        journal_path = Path(output_dir) / "request_journal.jsonl"
        if journal_path.is_file():
            for line in journal_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                    if ev.get("event") == "attempt":
                        calls += 1
                    elif ev.get("event") == "complete":
                        writes += 1
                except Exception:
                    pass
    except Exception:
        pass
    return calls, writes


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
        ledger_path_str = (
            str(args.study_ledger_path) if getattr(args, "study_ledger_path", None) else None
        )
        auth = ExecutionAuthorization(
            human_approval_token=args.auth_token,
            approved_protocol_sha256=protocol.protocol_sha256 if protocol else None,
            authorized_max_provider_attempts=args.max_attempts,
            allow_live_dispatch=args.allow_live_dispatch,
            use_money_guard=getattr(args, "use_money_guard", False),
            study_ledger_path=ledger_path_str,
        )

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

    # Mandatory readiness validation before provider construction (BLOCKER-2)
    is_test_split = plan.manifest.get("split") == "test"
    try:
        validate_experiment_readiness(
            plan=plan,
            protocol=protocol,
            authorization=auth,
            output_dir=args.output_dir,
            max_attempts=args.max_attempts,
            allow_dirty=False if is_test_split else getattr(args, "allow_dirty", False),
            is_live=True,
        )
    except (
        LiveExecutionBlockedError,
        ProtocolNotFrozenError,
        LiveBudgetRequiredError,
        ValueError,
    ) as exc:
        status = "HUMAN_DECISION_REQUIRED" if protocol is None else "LIVE_EXECUTION_BLOCKED"
        print(
            json.dumps(
                {
                    "status": status,
                    "reason": str(exc),
                    "provider_calls": 0,
                    "prediction_writes": 0,
                },
                indent=2,
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
    except Exception as exc:
        calls, writes = _inspect_historical_counts(args.output_dir)
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "error": str(exc),
                    "provider_calls": calls,
                    "prediction_writes": writes,
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

        ledger_path_str = (
            str(args.study_ledger_path) if getattr(args, "study_ledger_path", None) else None
        )
        auth = ExecutionAuthorization(
            human_approval_token=args.auth_token,
            approved_protocol_sha256=protocol.protocol_sha256,
            authorized_max_provider_attempts=max_attempts,
            allow_live_dispatch=args.allow_live_dispatch,
            use_money_guard=getattr(args, "use_money_guard", False),
            study_ledger_path=ledger_path_str,
        )

        plan = load_plan(args.config)

        # Mandatory readiness validation on resume (BLOCKER-2)
        is_test_split = plan.manifest.get("split") == "test"
        try:
            validate_experiment_readiness(
                plan=plan,
                protocol=protocol,
                authorization=auth,
                output_dir=output_dir,
                max_attempts=max_attempts,
                allow_dirty=False if is_test_split else getattr(args, "allow_dirty", False),
                is_live=True,
                is_resume=True,
            )
        except (
            LiveExecutionBlockedError,
            ProtocolNotFrozenError,
            LiveBudgetRequiredError,
            ValueError,
        ) as exc:
            print(
                json.dumps(
                    {
                        "status": "LIVE_EXECUTION_BLOCKED",
                        "reason": str(exc),
                        "provider_calls": 0,
                        "prediction_writes": 0,
                    },
                    sort_keys=True,
                    indent=2,
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
        calls, writes = _inspect_historical_counts(args.output_dir)
        print(
            json.dumps(
                {
                    "status": "LIVE_EXECUTION_BLOCKED",
                    "error": str(exc),
                    "provider_calls": calls,
                    "prediction_writes": writes,
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
    live_parser.add_argument("--max-attempts", type=int, help="Authorized max provider attempts")
    live_parser.add_argument(
        "--allow-live-dispatch",
        action="store_true",
        help="Explicit live dispatch permission",
    )
    live_parser.add_argument(
        "--stop-after", type=int, help="Optional stop-after limit for staged execution"
    )
    live_parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help=(
            "Allow uncommitted git status in tracked directories "
            "(test-only, rejected for canonical TEST)"
        ),
    )
    live_parser.add_argument(
        "--use-money-guard",
        action="store_true",
        help="Enable $20 monetary guard for live execution",
    )
    live_parser.add_argument(
        "--study-ledger-path",
        type=Path,
        help="Optional path to study-wide budget ledger file (test-only)",
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
    resume_parser.add_argument("--max-attempts", type=int, help="Authorized max provider attempts")
    resume_parser.add_argument(
        "--protocol-file", type=Path, help="Optional path to verify frozen D1-D7 protocol"
    )
    resume_parser.add_argument(
        "--stop-after", type=int, help="Optional stop-after limit for staged execution"
    )
    resume_parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help=(
            "Allow uncommitted git status in tracked directories "
            "(test-only, rejected for canonical TEST)"
        ),
    )
    resume_parser.add_argument(
        "--use-money-guard",
        action="store_true",
        help="Enable $20 monetary guard for live execution",
    )
    resume_parser.add_argument(
        "--study-ledger-path",
        type=Path,
        help="Optional path to study-wide budget ledger file (test-only)",
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
