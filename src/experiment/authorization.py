"""Execution authorization and gate enforcement for live experiment execution.

LIVE EXECUTION DEFAULT = DENY.
Real calls must never execute without explicit, validated human authorization
and an immutable, hash-bound scientific protocol approval contract (D1-D7).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.experiment.config import canonical_bytes, digest

if TYPE_CHECKING:
    from src.experiment.config import ValidatedPlan


REPO_ROOT = Path(__file__).resolve().parents[2]

CRITICAL_CODE_PATTERNS: tuple[str, ...] = (
    "src",
    "prompts",
    "config/model.json",
    "config/retrieval.json",
    "pyproject.toml",
    "uv.lock",
    ".python-version",
)


def compute_code_manifest(repo_root: Path) -> dict[str, str]:
    """Compute mapping of relative paths to SHA-256 digests for execution-critical code."""
    manifest: dict[str, str] = {}
    for item in sorted(CRITICAL_CODE_PATTERNS):
        path = repo_root / item
        if path.is_file():
            rel = path.relative_to(repo_root).as_posix()
            manifest[rel] = digest(path.read_bytes())
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if (
                    child.is_file()
                    and not child.name.endswith(".pyc")
                    and "__pycache__" not in child.parts
                    and ".pytest_cache" not in child.parts
                ):
                    rel = child.relative_to(repo_root).as_posix()
                    manifest[rel] = digest(child.read_bytes())
    return manifest


def compute_code_manifest_sha256(repo_root: Path) -> str:
    """Compute SHA-256 digest over the canonical JSON of the critical code manifest."""
    manifest = compute_code_manifest(repo_root)
    return digest(canonical_bytes(manifest))



class LiveExecutionBlockedError(RuntimeError):
    """Raised whenever live execution is blocked by safety or protocol gates."""


class ProtocolNotFrozenError(LiveExecutionBlockedError):
    """Raised when scientific protocol decisions (D1-D7) remain unresolved or invalid."""


class HumanAuthorizationRequiredError(LiveExecutionBlockedError):
    """Raised when explicit human authorization token or approval is absent."""


class LiveBudgetRequiredError(LiveExecutionBlockedError):
    """Raised when finite positive request budget is missing or invalid."""


ALLOWED_PROTOCOL_VALUES: dict[str, set[str]] = {
    "d1_raw_response_policy": {"RECORD_ONLY", "DISCARD", "LOG_SEPARATELY"},
    "d2a_ground_truth_semantics": {"PRIMARY_ONLY", "ANY_MATCH", "ALL_MATCH"},
    "d2b_empty_ground_truth": {"EXCLUDE", "TREAT_AS_NEGATIVE"},
    "d2c_ambiguous_ground_truth": {"EXCLUDE", "DISALLOW_CORRECT"},
    "d2d_macro_f1_universe": {
        "BENCHMARK_PREDICTED_ONLY",
        "FULL_ATTACK_UNIVERSE",
        "FROZEN_BENCHMARK_UNIVERSE",
    },
    "d2e_invalid_id_denominator": {"INCLUDE_IN_DENOMINATOR", "EXCLUDE_FROM_DENOMINATOR"},
    "d2f_api_error_denominator": {"INCLUDE_IN_DENOMINATOR", "EXCLUDE_FROM_DENOMINATOR"},
    "d2g_retired_attack_id": {"ALLOW_HISTORICAL", "FAIL_VALIDATION"},
    "d2h_conditional_retrieval": {"RANK_AT_K", "ANY_RANK_IN_CANDIDATES", "ANY_GT_RETRIEVED"},
    "d2i_failure_precedence": {"API_ERROR_FIRST", "PARSE_STATUS_FIRST", "INDEPENDENT_AXES"},
    "d2j_zero_denominator": {"ZERO", "NAN", "UNDEFINED", "NULL"},
    "d3_model_version_policy": {
        "CAPTURED_SNAPSHOT_OR_FAIL",
        "ALLOW_LATEST_WITH_TIMESTAMP_BINDING",
    },
    "d4_concurrency_policy": {"SEQUENTIAL_ONLY", "BOUNDED_POOL"},
    "d5_budget_policy": {"HARD_CAP_WORST_CASE_ATTEMPTS", "LOGICAL_SAMPLES_CAP"},
    "d6_t15_prerequisite_policy": {
        "NOT_REQUIRED_FOR_SYNTHETIC_BENCHMARK",
        "PREREQUISITE_PILOT_SATISFIED",
    },
    "d7_dataset_scope": {"FULL_BENCHMARK", "DEV_SMOKE", "PAIRED_TEST"},
}


@dataclass(frozen=True)
class ScientificProtocolApproval:
    """Immutable scientific protocol approval contract binding D1-D7 decisions.

    The actual scientific decisions must NOT be chosen by automated agents.
    Only explicit human-approved scientific protocol contracts may authorize execution.
    """

    protocol_version: str
    protocol_sha256: str
    d1_raw_response_policy: str
    d2a_ground_truth_semantics: str
    d2b_empty_ground_truth: str
    d2c_ambiguous_ground_truth: str
    d2d_macro_f1_universe: str
    d2e_invalid_id_denominator: str
    d2f_api_error_denominator: str
    d2g_retired_attack_id: str
    d2h_conditional_retrieval: str
    d2i_failure_precedence: str
    d2j_zero_denominator: str
    d3_model_version_policy: str
    d4_concurrency_policy: str
    d5_budget_policy: str
    d6_t15_prerequisite_policy: str
    d7_dataset_scope: str
    approval_timestamp: str
    approval_reference: str


def protocol_decision_dict(protocol: ScientificProtocolApproval) -> dict[str, Any]:
    """Extract canonical mapping of protocol decisions excluding the self-referential hash."""
    return {
        "protocol_version": protocol.protocol_version,
        "d1_raw_response_policy": protocol.d1_raw_response_policy,
        "d2a_ground_truth_semantics": protocol.d2a_ground_truth_semantics,
        "d2b_empty_ground_truth": protocol.d2b_empty_ground_truth,
        "d2c_ambiguous_ground_truth": protocol.d2c_ambiguous_ground_truth,
        "d2d_macro_f1_universe": protocol.d2d_macro_f1_universe,
        "d2e_invalid_id_denominator": protocol.d2e_invalid_id_denominator,
        "d2f_api_error_denominator": protocol.d2f_api_error_denominator,
        "d2g_retired_attack_id": protocol.d2g_retired_attack_id,
        "d2h_conditional_retrieval": protocol.d2h_conditional_retrieval,
        "d2i_failure_precedence": protocol.d2i_failure_precedence,
        "d2j_zero_denominator": protocol.d2j_zero_denominator,
        "d3_model_version_policy": protocol.d3_model_version_policy,
        "d4_concurrency_policy": protocol.d4_concurrency_policy,
        "d5_budget_policy": protocol.d5_budget_policy,
        "d6_t15_prerequisite_policy": protocol.d6_t15_prerequisite_policy,
        "d7_dataset_scope": protocol.d7_dataset_scope,
        "approval_timestamp": protocol.approval_timestamp,
        "approval_reference": protocol.approval_reference,
    }


def protocol_to_dict(protocol: ScientificProtocolApproval) -> dict[str, Any]:
    """Extract complete canonical mapping of the protocol contract including protocol_sha256."""
    return asdict(protocol)


def compute_protocol_sha256(decisions: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 over canonical JSON of protocol decisions."""
    return digest(canonical_bytes(decisions))


def create_test_protocol_approval(
    *,
    protocol_version: str = "test-protocol-v1",
    d1_raw_response_policy: str = "RECORD_ONLY",
    d2a_ground_truth_semantics: str = "PRIMARY_ONLY",
    d2b_empty_ground_truth: str = "EXCLUDE",
    d2c_ambiguous_ground_truth: str = "EXCLUDE",
    d2d_macro_f1_universe: str = "BENCHMARK_PREDICTED_ONLY",
    d2e_invalid_id_denominator: str = "INCLUDE_IN_DENOMINATOR",
    d2f_api_error_denominator: str = "INCLUDE_IN_DENOMINATOR",
    d2g_retired_attack_id: str = "ALLOW_HISTORICAL",
    d2h_conditional_retrieval: str = "RANK_AT_K",
    d2i_failure_precedence: str = "API_ERROR_FIRST",
    d2j_zero_denominator: str = "ZERO",
    d3_model_version_policy: str = "ALLOW_LATEST_WITH_TIMESTAMP_BINDING",
    d4_concurrency_policy: str = "SEQUENTIAL_ONLY",
    d5_budget_policy: str = "LOGICAL_SAMPLES_CAP",
    d6_t15_prerequisite_policy: str = "NOT_REQUIRED_FOR_SYNTHETIC_BENCHMARK",
    d7_dataset_scope: str = "PAIRED_TEST",
    approval_timestamp: str = "2026-09-30T00:00:00+00:00",
    approval_reference: str = "TEST_PROTOCOL_APPROVAL_REF",
    tamper_hash: bool = False,
) -> ScientificProtocolApproval:
    """Construct an explicit TEST-ONLY scientific protocol approval object for unit tests.

    DOES NOT APPROVE SCIENTIFIC PRODUCTION PROTOCOL.
    """
    decisions = {
        "protocol_version": protocol_version,
        "d1_raw_response_policy": d1_raw_response_policy,
        "d2a_ground_truth_semantics": d2a_ground_truth_semantics,
        "d2b_empty_ground_truth": d2b_empty_ground_truth,
        "d2c_ambiguous_ground_truth": d2c_ambiguous_ground_truth,
        "d2d_macro_f1_universe": d2d_macro_f1_universe,
        "d2e_invalid_id_denominator": d2e_invalid_id_denominator,
        "d2f_api_error_denominator": d2f_api_error_denominator,
        "d2g_retired_attack_id": d2g_retired_attack_id,
        "d2h_conditional_retrieval": d2h_conditional_retrieval,
        "d2i_failure_precedence": d2i_failure_precedence,
        "d2j_zero_denominator": d2j_zero_denominator,
        "d3_model_version_policy": d3_model_version_policy,
        "d4_concurrency_policy": d4_concurrency_policy,
        "d5_budget_policy": d5_budget_policy,
        "d6_t15_prerequisite_policy": d6_t15_prerequisite_policy,
        "d7_dataset_scope": d7_dataset_scope,
        "approval_timestamp": approval_timestamp,
        "approval_reference": approval_reference,
    }
    computed_hash = compute_protocol_sha256(decisions)
    return ScientificProtocolApproval(
        protocol_version=protocol_version,
        protocol_sha256="00" * 32 if tamper_hash else computed_hash,
        d1_raw_response_policy=d1_raw_response_policy,
        d2a_ground_truth_semantics=d2a_ground_truth_semantics,
        d2b_empty_ground_truth=d2b_empty_ground_truth,
        d2c_ambiguous_ground_truth=d2c_ambiguous_ground_truth,
        d2d_macro_f1_universe=d2d_macro_f1_universe,
        d2e_invalid_id_denominator=d2e_invalid_id_denominator,
        d2f_api_error_denominator=d2f_api_error_denominator,
        d2g_retired_attack_id=d2g_retired_attack_id,
        d2h_conditional_retrieval=d2h_conditional_retrieval,
        d2i_failure_precedence=d2i_failure_precedence,
        d2j_zero_denominator=d2j_zero_denominator,
        d3_model_version_policy=d3_model_version_policy,
        d4_concurrency_policy=d4_concurrency_policy,
        d5_budget_policy=d5_budget_policy,
        d6_t15_prerequisite_policy=d6_t15_prerequisite_policy,
        d7_dataset_scope=d7_dataset_scope,
        approval_timestamp=approval_timestamp,
        approval_reference=approval_reference,
    )


def validate_scientific_protocol(
    protocol: ScientificProtocolApproval | None,
    plan: ValidatedPlan | None = None,
) -> None:
    """Validate all D1-D7 protocol decisions and verify cryptographic hash binding."""
    if protocol is None:
        raise ProtocolNotFrozenError(
            "LIVE_EXECUTION_BLOCKED: scientific protocol decisions (D1-D7) remain "
            "HUMAN_DECISION_REQUIRED and are not frozen"
        )

    if not isinstance(protocol, ScientificProtocolApproval):
        raise ProtocolNotFrozenError(
            f"Expected ScientificProtocolApproval instance, got {type(protocol).__name__}"
        )

    if not protocol.protocol_version or not protocol.protocol_version.strip():
        raise ProtocolNotFrozenError("LIVE_EXECUTION_BLOCKED: protocol_version must not be empty")

    # Validate all required decision policies
    for decision_field, allowed_values in ALLOWED_PROTOCOL_VALUES.items():
        val = getattr(protocol, decision_field, None)
        if not val or not isinstance(val, str) or val.strip() == "":
            raise ProtocolNotFrozenError(
                f"LIVE_EXECUTION_BLOCKED: {decision_field} must be approved and non-empty"
            )
        if val not in allowed_values:
            options = sorted(allowed_values)
            raise ProtocolNotFrozenError(
                f"LIVE_EXECUTION_BLOCKED: {decision_field} must be in {options}, got '{val}'"
            )

    # Validate approval reference and timestamp
    if not protocol.approval_reference or not protocol.approval_reference.strip():
        raise ProtocolNotFrozenError("LIVE_EXECUTION_BLOCKED: approval_reference must not be empty")
    if not protocol.approval_timestamp or not protocol.approval_timestamp.strip():
        raise ProtocolNotFrozenError("LIVE_EXECUTION_BLOCKED: approval_timestamp must not be empty")

    # Verify cryptographic hash binding
    decisions = protocol_decision_dict(protocol)
    expected_sha256 = compute_protocol_sha256(decisions)
    if protocol.protocol_sha256 != expected_sha256:
        raise ProtocolNotFrozenError(
            f"LIVE_EXECUTION_BLOCKED: protocol SHA-256 hash mismatch: expected {expected_sha256}, "
            f"got {protocol.protocol_sha256}"
        )

    # If plan is provided, check compatibility
    if plan is not None:
        # D1: Raw Response Policy
        if protocol.d1_raw_response_policy == "LOG_SEPARATELY":
            raise ProtocolNotFrozenError(
                "LIVE_EXECUTION_BLOCKED: LOG_SEPARATELY raw-response storage is not implemented"
            )

        # D3: Model Version Policy
        if protocol.d3_model_version_policy == "CAPTURED_SNAPSHOT_OR_FAIL":
            model_ver = plan.manifest.get("model_version") or plan.config.generation.model_version
            if not model_ver or not str(model_ver).strip():
                raise ProtocolNotFrozenError(
                    "LIVE_EXECUTION_BLOCKED: d3_model_version_policy CAPTURED_SNAPSHOT_OR_FAIL "
                    "requires non-empty model_version in plan"
                )
        elif protocol.d3_model_version_policy == "ALLOW_LATEST_WITH_TIMESTAMP_BINDING":
            pass

        # D4: Concurrency Policy
        if protocol.d4_concurrency_policy == "SEQUENTIAL_ONLY":
            if plan.config.execution.concurrency not in (None, 1):
                raise ProtocolNotFrozenError(
                    "LIVE_EXECUTION_BLOCKED: plan concurrency contradicts SEQUENTIAL_ONLY"
                )
        elif protocol.d4_concurrency_policy == "BOUNDED_POOL":
            raise ProtocolNotFrozenError(
                "LIVE_EXECUTION_BLOCKED: BOUNDED_POOL concurrency is not implemented; "
                "runner supports SEQUENTIAL_ONLY"
            )

        # D6: T15 Prerequisite Policy
        if protocol.d6_t15_prerequisite_policy == "PREREQUISITE_PILOT_SATISFIED":
            raise ProtocolNotFrozenError(
                "LIVE_EXECUTION_BLOCKED: T15 prerequisite pilot proof is not available"
            )

        # D7: Dataset Scope Policy
        plan_split = plan.manifest.get("split") or plan.config.dataset.split
        if protocol.d7_dataset_scope == "PAIRED_TEST":
            if plan_split != "test":
                raise ProtocolNotFrozenError(
                    f"LIVE_EXECUTION_BLOCKED: d7_dataset_scope PAIRED_TEST requires 'test' split, "
                    f"got '{plan_split}'"
                )
        elif protocol.d7_dataset_scope == "DEV_SMOKE":
            if plan_split != "dev":
                raise ProtocolNotFrozenError(
                    f"LIVE_EXECUTION_BLOCKED: d7_dataset_scope DEV_SMOKE requires 'dev' split, "
                    f"got '{plan_split}'"
                )


@dataclass(frozen=True)
class ExecutionAuthorization:
    """Explicit human runtime execution authorization required before live dispatch."""

    human_approval_token: str
    approved_protocol_sha256: str | None = None
    authorized_max_provider_attempts: int | None = None
    allow_live_dispatch: bool = False
    # Backward compatibility fields:
    authorized_max_requests: int | None = None
    scientific_protocol_approved: bool = False
    d1_raw_response_policy_approved: str | None = None
    d7_dataset_scope_approved: str | None = None


def validate_live_authorization(
    authorization: ExecutionAuthorization | None,
    plan: ValidatedPlan,
    protocol: ScientificProtocolApproval | None = None,
) -> None:
    """Validate all gates before any live provider dispatch can occur.

    Default is FAIL-CLOSED (DENY).
    Requires explicit human authorization and hash-bound protocol approval.
    """
    if authorization is None:
        raise LiveExecutionBlockedError(
            "LIVE_EXECUTION_BLOCKED: execution authorization is missing; default is DENY"
        )

    if not isinstance(authorization, ExecutionAuthorization):
        raise LiveExecutionBlockedError(
            f"Expected ExecutionAuthorization instance, got {type(authorization).__name__}"
        )

    # Gate 1: Scientific Protocol Decisions (D1-D7) are MANDATORY for live execution
    if protocol is None:
        raise ProtocolNotFrozenError(
            "LIVE_EXECUTION_BLOCKED: full ScientificProtocolApproval contract is mandatory "
            "for live execution; scientific protocol decisions (D1-D7) remain "
            "HUMAN_DECISION_REQUIRED and are not frozen"
        )

    validate_scientific_protocol(protocol, plan)

    if not authorization.approved_protocol_sha256:
        raise ProtocolNotFrozenError(
            "LIVE_EXECUTION_BLOCKED: explicit approved_protocol_sha256 matching the "
            "frozen scientific protocol is required on execution authorization"
        )

    if authorization.approved_protocol_sha256 != protocol.protocol_sha256:
        raise ProtocolNotFrozenError(
            "LIVE_EXECUTION_BLOCKED: authorized protocol SHA-256 does not match protocol"
        )

    # Gate 2: Explicit non-empty human authorization token
    if (
        not authorization.human_approval_token
        or not authorization.human_approval_token.strip()
    ):
        raise HumanAuthorizationRequiredError(
            "LIVE_EXECUTION_BLOCKED: non-empty human approval token is required"
        )

    # Gate 3: Live dispatch must be explicitly enabled
    if not authorization.allow_live_dispatch:
        raise LiveExecutionBlockedError(
            "LIVE_EXECUTION_BLOCKED: allow_live_dispatch flag must be True"
        )

    # Gate 4: Explicit finite request budget (provider attempts)
    budget_cap = (
        authorization.authorized_max_provider_attempts
        if authorization.authorized_max_provider_attempts is not None
        else authorization.authorized_max_requests
    )

    if budget_cap is None:
        raise LiveBudgetRequiredError(
            "LIVE_EXECUTION_BLOCKED: explicit finite request budget is required"
        )

    if budget_cap < 0:
        raise LiveBudgetRequiredError(
            "LIVE_EXECUTION_BLOCKED: authorized_max_requests cannot be negative"
        )

    if budget_cap == 0:
        raise LiveBudgetRequiredError(
            "LIVE_EXECUTION_BLOCKED: authorized request budget cannot be zero"
        )

    from src.experiment.schemas import CONDITIONS

    if protocol.d5_budget_policy == "HARD_CAP_WORST_CASE_ATTEMPTS":
        worst_case_attempts = (
            len(plan.samples) * len(CONDITIONS) * (plan.config.execution.retries + 1)
        )
        if budget_cap < worst_case_attempts:
            raise LiveBudgetRequiredError(
                f"LIVE_EXECUTION_BLOCKED: authorized budget ({budget_cap}) "
                f"cannot cover worst-case attempts ({worst_case_attempts}) "
                f"required by HARD_CAP_WORST_CASE_ATTEMPTS"
            )
    else:
        required_calls = len(plan.samples) * len(CONDITIONS)
        if budget_cap < required_calls:
            raise LiveBudgetRequiredError(
                f"LIVE_EXECUTION_BLOCKED: authorized budget ({budget_cap}) "
                f"cannot cover the required matrix calls ({required_calls})"
            )

    # Gate 5: Reject external self-signed lock or external plan root on TEST split
    is_test_split = plan.manifest.get("split") == "test"
    is_canonical_scale = len(getattr(plan, "samples", [])) == 1280
    if is_test_split:
        has_external_lock = (
            hasattr(plan, "root")
            and (plan.root / "config" / "canonical_experiment_lock_v1.json").exists()
            and plan.root.resolve() != REPO_ROOT.resolve()
        )
        if has_external_lock:
            raise ProtocolNotFrozenError(
                "LIVE_EXECUTION_BLOCKED: canonical TEST execution must execute from repo root; "
                "external plan root rejected"
            )
        if (
            is_canonical_scale
            and hasattr(plan, "root")
            and plan.root.resolve() != REPO_ROOT.resolve()
        ):
            raise ProtocolNotFrozenError(
                "LIVE_EXECUTION_BLOCKED: canonical TEST execution must execute from repo root; "
                "external plan root rejected"
            )

    # Gate 6: Canonical experiment lock enforcement for canonical TEST execution
    validate_canonical_experiment_lock(plan, protocol)


def validate_canonical_experiment_lock(
    plan: ValidatedPlan,
    protocol: ScientificProtocolApproval,
    *,
    repo_root: Any = None,
    root: Any = None,
) -> None:
    """Enforce that test split or canonical experiment binds strictly to the frozen lock artifact.

    Reject any alternate protocol or config even if internally self-consistent.
    Ensures canonical lock is loaded from repository root, preventing external self-signed bypasses.
    """
    from src.experiment.config import parse_json

    is_test_split = plan.manifest.get("split") == "test"
    is_canonical_scale = len(getattr(plan, "samples", [])) == 1280
    default_repo_root = REPO_ROOT

    # Determine target repository root containing config/
    target_repo_root = Path(repo_root or root) if (repo_root or root) else default_repo_root
    lock_path = target_repo_root / "config" / "canonical_experiment_lock_v1.json"

    plan_in_target = False
    plan_in_repo = False
    try:
        plan_in_target = hasattr(plan, "root") and plan.root.resolve() == target_repo_root.resolve()
        plan_in_repo = hasattr(plan, "root") and plan.root.resolve() == REPO_ROOT.resolve()
    except Exception:
        plan_in_target = False
        plan_in_repo = False

    should_enforce = (
        (is_canonical_scale and is_test_split)
        or (plan_in_repo and is_test_split)
        or (plan_in_target and lock_path.exists())
    )
    if not should_enforce:
        return

    if not lock_path.exists():
        raise ProtocolNotFrozenError(
            "LIVE_EXECUTION_BLOCKED: canonical experiment lock file missing "
            "at config/canonical_experiment_lock_v1.json"
        )
    lock_data = parse_json(lock_path.read_bytes())
    if protocol.protocol_sha256 != lock_data.get("protocol_sha256"):
        raise ProtocolNotFrozenError(
            f"LIVE_EXECUTION_BLOCKED: protocol SHA-256 ({protocol.protocol_sha256}) "
            f"does not match canonical lock ({lock_data.get('protocol_sha256')}); "
            "alternate protocol rejected for canonical TEST execution"
        )
    if plan.manifest.get("config_sha256") != lock_data.get("config_sha256"):
        raise ProtocolNotFrozenError(
            f"LIVE_EXECUTION_BLOCKED: config SHA-256 ({plan.manifest.get('config_sha256')}) "
            f"does not match canonical lock ({lock_data.get('config_sha256')}); "
            "alternate config rejected for canonical TEST execution"
        )
    expected_artifacts = lock_data.get("artifact_hashes", {})
    plan_artifacts = plan.manifest.get("artifacts", {})
    for name, expected_hash in expected_artifacts.items():
        actual_hash = plan_artifacts.get(name, {}).get("sha256")
        if actual_hash != expected_hash:
            raise ProtocolNotFrozenError(
                f"LIVE_EXECUTION_BLOCKED: artifact '{name}' SHA-256 mismatch with canonical lock "
                f"(expected {expected_hash}, got {actual_hash})"
            )

    # Verify executable code manifest digest (BLOCKER-1)
    expected_code_manifest = lock_data.get("code_manifest_sha256")
    if expected_code_manifest:
        actual_code_manifest = compute_code_manifest_sha256(target_repo_root)
        if actual_code_manifest != expected_code_manifest:
            raise ProtocolNotFrozenError(
                f"LIVE_EXECUTION_BLOCKED: code manifest SHA-256 ({actual_code_manifest}) "
                f"does not match canonical lock ({expected_code_manifest}); code drift detected"
            )
    elif is_test_split or is_canonical_scale:
        raise ProtocolNotFrozenError(
            "LIVE_EXECUTION_BLOCKED: canonical lock missing code_manifest_sha256 binding"
        )

    # Verify optional code freeze commit SHA if specified
    expected_commit = lock_data.get("code_freeze_commit_sha")
    if expected_commit:
        try:
            import subprocess

            git_cwd = (
                target_repo_root
                if (target_repo_root / ".git").exists()
                else REPO_ROOT
            )
            commit_res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=git_cwd,
                capture_output=True,
                text=True,
                check=False,
            )
            if commit_res.returncode == 0:
                actual_commit = commit_res.stdout.strip()
                if actual_commit != expected_commit:
                    raise ProtocolNotFrozenError(
                        f"LIVE_EXECUTION_BLOCKED: commit SHA ({actual_commit}) does not match "
                        f"canonical lock freeze commit ({expected_commit})"
                    )
            else:
                raise ProtocolNotFrozenError(
                    "LIVE_EXECUTION_BLOCKED: failed to determine HEAD commit SHA to verify "
                    f"canonical lock freeze commit ({expected_commit})"
                )
        except ProtocolNotFrozenError:
            raise
        except Exception:
            pass


def validate_experiment_readiness(
    *,
    plan: ValidatedPlan,
    protocol: ScientificProtocolApproval | None,
    authorization: ExecutionAuthorization | None = None,
    repo_root: Path | None = None,
    output_dir: Path | str | None = None,
    max_attempts: int | None = None,
    allow_dirty: bool = False,
    is_live: bool = False,
    is_resume: bool = False,
) -> dict[str, Any]:
    """Comprehensive shared non-provider readiness validator for preflight, live, and resume.

    Mandatory gate across preflight, live dispatch, and resume.
    Ensures clean source tree, canonical commit SHA, frozen protocol, canonical lock,
    finite budget, sequential concurrency, output safety, and evaluator contract.
    Canonical TEST live strictly prohibits any dirty source bypass.
    Fails closed with strictly 0 provider calls, 0 prediction writes.
    """
    from src.experiment.path_safety import validate_untrusted_output_path
    from src.experiment.schemas import CONDITIONS

    root = Path(repo_root) if repo_root else REPO_ROOT
    target_code_root = getattr(plan, "root", None) or root
    is_test_split = plan.manifest.get("split") == "test"
    is_canonical_scale = len(getattr(plan, "samples", [])) == 1280

    # Gate 1: Scientific protocol validation (mandatory)
    if protocol is None:
        msg = (
            "LIVE_EXECUTION_BLOCKED: full ScientificProtocolApproval contract is mandatory "
            "for live execution; scientific protocol decisions (D1-D7) remain "
            "HUMAN_DECISION_REQUIRED and are not frozen"
            if is_live
            else "LIVE_EXECUTION_BLOCKED: scientific protocol decisions (D1-D7) remain "
            "HUMAN_DECISION_REQUIRED and are not frozen"
        )
        raise ProtocolNotFrozenError(msg)
    validate_scientific_protocol(protocol, plan)

    # Gate 2: Live authorization validation (mandatory when is_live is True)
    if is_live:
        validate_live_authorization(authorization, plan, protocol=protocol)

    # Gate 3: Canonical experiment lock & code manifest validation
    validate_canonical_experiment_lock(plan, protocol, repo_root=target_code_root)

    # Gate 4: Sequential concurrency check
    if (
        protocol.d4_concurrency_policy != "SEQUENTIAL_ONLY"
        or plan.config.execution.concurrency != 1
    ):
        raise LiveExecutionBlockedError(
            "LIVE_EXECUTION_BLOCKED: Concurrency policy must be SEQUENTIAL_ONLY and "
            "execution concurrency in config must be explicitly 1"
        )

    # Gate 5: Explicit finite request budget check
    if not plan.config.execution.max_requests or plan.config.execution.max_requests <= 0:
        raise LiveBudgetRequiredError(
            "LIVE_EXECUTION_BLOCKED: Execution configuration must define an explicit "
            "positive max_requests budget"
        )

    worst_case_attempts = (
        len(plan.samples) * len(CONDITIONS) * (plan.config.execution.retries + 1)
    )
    plan_in_repo = False
    try:
        plan_in_repo = hasattr(plan, "root") and plan.root.resolve() == REPO_ROOT.resolve()
    except Exception:
        plan_in_repo = False
    is_canonical_test = is_test_split and (is_canonical_scale or plan_in_repo)

    if is_canonical_test or protocol.d5_budget_policy == "HARD_CAP_WORST_CASE_ATTEMPTS":
        if protocol.d5_budget_policy != "HARD_CAP_WORST_CASE_ATTEMPTS":
            raise LiveExecutionBlockedError(
                f"LIVE_EXECUTION_BLOCKED: Budget policy must be HARD_CAP_WORST_CASE_ATTEMPTS, "
                f"got {protocol.d5_budget_policy}"
            )
        if max_attempts is not None and max_attempts < worst_case_attempts:
            raise LiveBudgetRequiredError(
                f"LIVE_EXECUTION_BLOCKED: Provided max-attempts ({max_attempts}) is less than "
                f"worst-case attempts ({worst_case_attempts})"
            )
    else:
        required_calls = len(plan.samples) * len(CONDITIONS)
        if max_attempts is not None and max_attempts < required_calls:
            raise LiveBudgetRequiredError(
                f"LIVE_EXECUTION_BLOCKED: Provided max-attempts ({max_attempts}) is less than "
                f"required calls ({required_calls})"
            )

    # Gate 6: Output directory path safety check
    effective_output = output_dir
    if effective_output is None:
        effective_output = root / "artifacts" / "experiments" / plan.manifest["experiment_id"]
    validated_output = validate_untrusted_output_path(effective_output)

    # Gate 7: Evaluator contract compatibility (MAJOR-6)
    from src.evaluation.experiment_metrics import validate_evaluator_compatibility

    evaluator_details = validate_evaluator_compatibility(protocol, plan)

    # Gate 8: Clean source tree check
    is_canonical_test = is_test_split and (is_canonical_scale or plan_in_repo)
    # Canonical TEST live or canonical scale NEVER permits allow_dirty bypass
    effective_allow_dirty = (
        False if (is_live and is_canonical_test) else allow_dirty
    )
    should_check_dirty = not effective_allow_dirty and (
        plan_in_repo or is_canonical_test or getattr(plan, "enforce_clean_git", False)
    )
    git_cwd = root if (root / ".git").exists() else REPO_ROOT
    if should_check_dirty:
        try:
            import subprocess

            res = subprocess.run(
                ["git", "status", "--porcelain", "src", "config", "prompts", "scripts"],
                cwd=git_cwd,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode != 0:
                raise LiveExecutionBlockedError(
                    f"LIVE_EXECUTION_BLOCKED: git status failed: {res.stderr}"
                )
            if res.stdout.strip():
                raise LiveExecutionBlockedError(
                    "LIVE_EXECUTION_BLOCKED: Source tree is dirty: git status reports "
                    f"uncommitted changes in tracked directories:\n{res.stdout.strip()}"
                )
        except LiveExecutionBlockedError:
            raise
        except Exception as exc:
            raise LiveExecutionBlockedError(
                f"LIVE_EXECUTION_BLOCKED: Failed to check git source cleanliness: {exc}"
            ) from exc

    # Gate 9: Exact 40-character Git commit SHA check
    git_sha = None
    try:
        import subprocess

        git_sha_res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=git_cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if git_sha_res.returncode != 0:
            raise LiveExecutionBlockedError(
                f"LIVE_EXECUTION_BLOCKED: git rev-parse HEAD failed: {git_sha_res.stderr}"
            )
        git_sha = git_sha_res.stdout.strip()
        import re

        if len(git_sha) != 40 or not re.fullmatch(r"[0-9a-f]{40}", git_sha):
            raise LiveExecutionBlockedError(
                f"LIVE_EXECUTION_BLOCKED: Invalid Git commit SHA: {git_sha}"
            )
    except LiveExecutionBlockedError:
        raise
    except Exception as exc:
        if is_test_split or is_canonical_scale:
            raise LiveExecutionBlockedError(
                f"LIVE_EXECUTION_BLOCKED: Git commit SHA check failed: {exc}"
            ) from exc

    return {
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
        "evaluator_contract_valid": True,
        "evaluator_contract_details": evaluator_details,
        "output_path_safe": True,
        "output_directory": str(validated_output),
        "test_split_protection": (
            "BLOCKED_WITHOUT_HUMAN_AUTHORIZATION" if is_test_split else "DEV_ONLY"
        ),
        "provider_calls_during_preflight": 0,
        "canonical_test_provider_calls": 0,
        "provider_calls": 0,
        "prediction_writes": 0,
    }


def check_live_execution_gates(
    plan: ValidatedPlan,
    authorization: ExecutionAuthorization | None = None,
    protocol: ScientificProtocolApproval | None = None,
) -> dict[str, Any]:
    """Inspect authorization status and return non-executing gate report."""
    try:
        validate_live_authorization(authorization, plan, protocol=protocol)
        return {
            "status": "AUTHORIZED",
            "provider_calls": 0,
            "prediction_writes": 0,
            "live_execution_permitted": True,
        }
    except (LiveExecutionBlockedError, TypeError, ValueError) as exc:
        return {
            "status": "LIVE_EXECUTION_BLOCKED",
            "reason": str(exc),
            "provider_calls": 0,
            "prediction_writes": 0,
            "live_execution_permitted": False,
        }
