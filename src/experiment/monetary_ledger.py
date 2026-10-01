"""Study-wide durable USD monetary runtime guard and ledger for RAG2ATTCK."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from pathlib import Path
from typing import Any, Iterator, Optional

from src.experiment.authorization import REPO_ROOT, LiveExecutionBlockedError
from src.experiment.path_safety import (
    is_symlink_or_junction,
    validate_untrusted_output_path,
)

# Canonical rounding quantizers
MONEY_QUANT = Decimal("0.00000001")


def round_cost_up(val: Decimal) -> Decimal:
    """Round costs, deductions, and retained charges UP towards infinity."""
    return val.quantize(MONEY_QUANT, rounding=ROUND_CEILING)


def round_credit_down(val: Decimal) -> Decimal:
    """Round available balance and refunds DOWN towards zero."""
    return val.quantize(MONEY_QUANT, rounding=ROUND_FLOOR)


def validate_finite_nonnegative_money(val: Any, name: str = "money") -> Decimal:
    """Validate that value is a finite, non-negative monetary Decimal."""
    if isinstance(val, bool) or not isinstance(val, (int, str, Decimal)):
        raise ValueError(
            f"Monetary value {name} must be Decimal, int, or str, got {type(val).__name__}"
        )
    try:
        d = Decimal(str(val))
    except Exception as exc:
        raise ValueError(f"Invalid monetary value for {name}: {val}") from exc

    if not d.is_finite() or d < Decimal("0.0"):
        raise ValueError(f"Monetary value {name} must be finite and non-negative, got {d}")
    return d


def validate_token_count(val: Any, name: str) -> Optional[int]:
    """Validate that token count is None or a non-negative exact int (not bool/float/str)."""
    if val is None:
        return None
    if type(val) is not int or isinstance(val, bool):
        raise ValueError(
            f"Token count {name} must be exact int (no bool/float/str), "
            f"got {type(val).__name__}: {val}"
        )
    if val < 0:
        raise ValueError(f"Token count {name} cannot be negative: {val}")
    return val


def canonical_json_bytes(obj: Any) -> bytes:
    """Serialize dictionary or structure to deterministic canonical JSON bytes."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _strict_json_loads(data: bytes | str) -> dict[str, Any]:
    """Parse JSON strictly rejecting non-standard constants (NaN, Inf) and duplicate keys."""

    def _reject_constant(c: str) -> None:
        raise ValueError(f"Non-standard JSON constant rejected: {c}")

    def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        d: dict[str, Any] = {}
        for k, v in pairs:
            if k in d:
                raise ValueError(f"Duplicate JSON key rejected: {k}")
            d[k] = v
        return d

    text = data.decode("utf-8") if isinstance(data, bytes) else data
    return json.loads(
        text, object_pairs_hook=_reject_duplicate_keys, parse_constant=_reject_constant
    )


def compute_pricing_contract_sha256(pricing_dict: dict[str, Any]) -> str:
    """Compute SHA-256 digest of frozen pricing configuration."""
    return hashlib.sha256(canonical_json_bytes(pricing_dict)).hexdigest()


def resolve_study_root(start_path: Optional[Path] = None) -> Path:
    """Resolve the stable study repository root across worktrees and main repo."""
    p = (start_path or Path(__file__).resolve().parents[2]).resolve()
    git_entry = p / ".git"
    if git_entry.is_file():
        try:
            txt = git_entry.read_text("utf-8").strip()
            if txt.startswith("gitdir:"):
                target = Path(txt.split(":", 1)[1].strip()).resolve()
                # target is <main_repo>/.git/worktrees/<name>
                if "worktrees" in target.parts:
                    idx = target.parts.index("worktrees")
                    return Path(*target.parts[: idx - 1]).resolve()
                return target.parents[1].resolve()
        except OSError:
            pass
    elif git_entry.is_dir():
        return p
    return p


def get_canonical_study_ledger_path(study_root: Optional[Path] = None) -> Path:
    """Get the stable study-wide ledger path anchored to repository root."""
    root = study_root or resolve_study_root()
    return root / "artifacts" / "study_budget" / "study_ledger.json"


def validate_safe_ledger_path(ledger_path: Path | str) -> Path:
    """Validate ledger path safety against symlinks, directory junctions, and hardlinks.

    Reuses validate_untrusted_output_path for raw and resolved ancestor checks,
    and unconditionally rejects hardlinked files (st_nlink > 1) on both the target path
    and any associated .tmp file.
    """
    if isinstance(ledger_path, str) and not ledger_path.strip():
        raise ValueError("ledger path must not be empty")

    raw_p = Path(ledger_path)

    # 1. Reuse existing validate_untrusted_output_path on parent directory
    safe_parent = validate_untrusted_output_path(raw_p.parent)

    # 2. Raw path checks before resolution
    if is_symlink_or_junction(raw_p):
        raise ValueError(f"symlink ledger path rejected: {raw_p}")

    if raw_p.exists():
        if raw_p.is_dir():
            raise ValueError(f"ledger path must be a file, not a directory: {raw_p}")
        st = raw_p.stat()
        if st.st_nlink > 1:
            raise ValueError(f"hardlinked ledger file rejected: {raw_p} (st_nlink={st.st_nlink})")

    # 3. Check associated .tmp file if present
    tmp_p = raw_p.with_suffix(".tmp")
    if is_symlink_or_junction(tmp_p):
        raise ValueError(f"symlink temporary file rejected: {tmp_p}")
    if tmp_p.exists():
        if tmp_p.is_dir():
            raise ValueError(f"temporary file must be a file, not a directory: {tmp_p}")
        st_tmp = tmp_p.stat()
        if st_tmp.st_nlink > 1:
            raise ValueError(
                f"hardlinked temporary file rejected: {tmp_p} (st_nlink={st_tmp.st_nlink})"
            )

    # 4. Resolved path checks
    resolved_p = (safe_parent / raw_p.name).resolve()
    if is_symlink_or_junction(resolved_p):
        raise ValueError(f"symlink ledger path rejected: {resolved_p}")
    if resolved_p.exists():
        if resolved_p.is_dir():
            raise ValueError(f"ledger path must be a file, not a directory: {resolved_p}")
        st_res = resolved_p.stat()
        if st_res.st_nlink > 1:
            raise ValueError(
                f"hardlinked ledger file rejected: {resolved_p} (st_nlink={st_res.st_nlink})"
            )

    resolved_tmp = resolved_p.with_suffix(".tmp")
    if is_symlink_or_junction(resolved_tmp):
        raise ValueError(f"symlink temporary file rejected: {resolved_tmp}")
    if resolved_tmp.exists():
        if resolved_tmp.is_dir():
            raise ValueError(f"temporary file must be a file, not a directory: {resolved_tmp}")
        st_res_tmp = resolved_tmp.stat()
        if st_res_tmp.st_nlink > 1:
            raise ValueError(
                f"hardlinked temporary file rejected: {resolved_tmp} "
                f"(st_nlink={st_res_tmp.st_nlink})"
            )

    return resolved_p


def get_canonical_study_anchor_path(study_root: Optional[Path] = None) -> Path:
    """Get the stable study-wide anchor path outside deletable artifact/output tree."""
    root = study_root or resolve_study_root()
    return root / ".study_anchor.json"


def resolve_study_anchor_path(
    ledger_path: Path,
    study_root: Path,
    explicit_anchor_path: Optional[Path | str] = None,
) -> Path:
    """Resolve study anchor path ensuring it resides outside deletable per-run/output paths."""
    if explicit_anchor_path is not None:
        return Path(explicit_anchor_path)
    try:
        ledger_path.resolve().relative_to(study_root.resolve())
        return get_canonical_study_anchor_path(study_root)
    except ValueError:
        p = ledger_path.resolve().parent
        if p.name in ("study_budget", "artifacts", "experiments", "output", "live-output"):
            return p.parent / ".study_anchor.json"
        return p / ".study_anchor.json"


def validate_safe_anchor_path(anchor_path: Path | str) -> Path:
    """Validate anchor path safety against symlinks, directory junctions, and hardlinks.

    Reuses validate_untrusted_output_path for raw and resolved ancestor checks,
    and unconditionally rejects hardlinked files (st_nlink > 1) on both the target path
    and any associated .tmp file.
    """
    if isinstance(anchor_path, str) and not anchor_path.strip():
        raise ValueError("anchor path must not be empty")

    raw_p = Path(anchor_path)

    # 1. Reuse existing validate_untrusted_output_path on parent directory
    safe_parent = validate_untrusted_output_path(raw_p.parent)

    # 2. Raw path checks before resolution
    if is_symlink_or_junction(raw_p):
        raise ValueError(f"symlink anchor path rejected: {raw_p}")

    if raw_p.exists():
        if raw_p.is_dir():
            raise ValueError(f"anchor path must be a file, not a directory: {raw_p}")
        st = raw_p.stat()
        if st.st_nlink > 1:
            raise ValueError(f"hardlinked anchor file rejected: {raw_p} (st_nlink={st.st_nlink})")

    # 3. Check associated .tmp file if present
    tmp_p = raw_p.with_suffix(".tmp")
    if is_symlink_or_junction(tmp_p):
        raise ValueError(f"symlink temporary file rejected: {tmp_p}")
    if tmp_p.exists():
        if tmp_p.is_dir():
            raise ValueError(f"temporary file must be a file, not a directory: {tmp_p}")
        st_tmp = tmp_p.stat()
        if st_tmp.st_nlink > 1:
            raise ValueError(
                f"hardlinked temporary file rejected: {tmp_p} (st_nlink={st_tmp.st_nlink})"
            )

    # 4. Resolved path checks
    resolved_p = (safe_parent / raw_p.name).resolve()
    if is_symlink_or_junction(resolved_p):
        raise ValueError(f"symlink anchor path rejected: {resolved_p}")
    if resolved_p.exists():
        if resolved_p.is_dir():
            raise ValueError(f"anchor path must be a file, not a directory: {resolved_p}")
        st_res = resolved_p.stat()
        if st_res.st_nlink > 1:
            raise ValueError(
                f"hardlinked anchor file rejected: {resolved_p} (st_nlink={st_res.st_nlink})"
            )

    resolved_tmp = resolved_p.with_suffix(".tmp")
    if is_symlink_or_junction(resolved_tmp):
        raise ValueError(f"symlink temporary file rejected: {resolved_tmp}")
    if resolved_tmp.exists():
        if resolved_tmp.is_dir():
            raise ValueError(f"temporary file must be a file, not a directory: {resolved_tmp}")
        st_res_tmp = resolved_tmp.stat()
        if st_res_tmp.st_nlink > 1:
            raise ValueError(
                f"hardlinked temporary file rejected: {resolved_tmp} "
                f"(st_nlink={st_res_tmp.st_nlink})"
            )

    return resolved_p


def load_pricing_config(
    pricing_file: Optional[Path] = None,
    repo_root: Optional[Path] = None,
) -> tuple[dict[str, Any], str]:
    """Load and validate the frozen pricing contract from the candidate execution code tree."""
    if pricing_file is None:
        root = (repo_root or REPO_ROOT).resolve()
        candidate = root / "config" / "pricing_v1.json"
        if not candidate.exists() and (REPO_ROOT / "config" / "pricing_v1.json").exists():
            pricing_file = REPO_ROOT / "config" / "pricing_v1.json"
        else:
            pricing_file = candidate

    raw_p = Path(pricing_file)
    safe_parent = validate_untrusted_output_path(raw_p.parent)
    if is_symlink_or_junction(raw_p):
        raise ValueError(f"symlink pricing path rejected: {raw_p}")
    resolved_p = (safe_parent / raw_p.name).resolve()
    if is_symlink_or_junction(resolved_p):
        raise ValueError(f"symlink pricing path rejected: {resolved_p}")
    if not resolved_p.exists():
        raise FileNotFoundError(f"Pricing configuration file not found at {resolved_p}")
    if resolved_p.is_dir():
        raise ValueError(f"pricing path must be a file, not a directory: {resolved_p}")

    data = _strict_json_loads(resolved_p.read_bytes())
    digest = compute_pricing_contract_sha256(data)
    return data, digest


@contextlib.contextmanager
def study_ledger_lock(lock_path: Path) -> Iterator[None]:
    """Single-writer lock for study-wide budget ledger operations.

    Raises:
        ValueError: If another process currently holds the lock, lock is hardlinked,
            or lock creation fails.
    """
    safe_parent = validate_untrusted_output_path(lock_path.parent)
    if is_symlink_or_junction(lock_path):
        raise ValueError(f"symlink lock path rejected: {lock_path}")
    safe_parent.mkdir(parents=True, exist_ok=True)

    if lock_path.exists():
        if lock_path.is_dir():
            raise ValueError(f"lock path must be a file, not a directory: {lock_path}")
        st = lock_path.stat()
        if st.st_nlink > 1:
            raise ValueError(f"hardlinked lock file rejected: {lock_path} (st_nlink={st.st_nlink})")

    try:
        stream = lock_path.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise ValueError(
            "Study budget ledger is locked by another process "
            f"(single-writer lock active at {lock_path})"
        ) from exc
    except OSError as exc:
        raise ValueError(
            f"Failed to acquire single-writer study ledger lock at {lock_path}: {exc}"
        ) from exc

    try:
        stream.write(f"pid={os.getpid()}\n")
        stream.flush()
        yield
    finally:
        stream.close()
        try:
            lock_path.unlink()
        except OSError:
            pass


@contextlib.contextmanager
def study_ledger_and_anchor_lock(ledger_lock: Path, anchor_lock: Path) -> Iterator[None]:
    """Acquire single-writer locks for ledger and anchor in deterministic sorted order."""
    if ledger_lock.resolve() == anchor_lock.resolve():
        with study_ledger_lock(ledger_lock):
            yield
    else:
        locks = sorted([ledger_lock, anchor_lock], key=lambda p: str(p.resolve()))
        with study_ledger_lock(locks[0]):
            with study_ledger_lock(locks[1]):
                yield


class StudyBudgetLedger:
    """Persistent shared study-wide budget ledger with single-writer lock.

    Preserves total study spend, pilot hold, active reservations, and settled costs
    across multiple runs and output directories.
    """

    def __init__(
        self,
        ledger_path: Optional[Path | str] = None,
        *,
        pricing_config: Optional[dict[str, Any]] = None,
        study_root: Optional[Path] = None,
        code_root: Optional[Path] = None,
        anchor_path: Optional[Path | str] = None,
        output_directory: Optional[Path | str] = None,
        experiment_id: Optional[str] = None,
    ) -> None:
        self.study_root = study_root or resolve_study_root()
        ledger_file = (
            Path(ledger_path) if ledger_path else get_canonical_study_ledger_path(self.study_root)
        )
        self.ledger_path = validate_safe_ledger_path(ledger_file)
        self.lock_path = self.ledger_path.with_suffix(".lock")

        resolved_anchor_file = resolve_study_anchor_path(
            self.ledger_path, self.study_root, explicit_anchor_path=anchor_path
        )
        self.anchor_path = validate_safe_anchor_path(resolved_anchor_file)
        self.anchor_lock_path = self.anchor_path.with_suffix(".lock")

        self.output_directory = Path(output_directory).resolve() if output_directory else None
        self.experiment_id = experiment_id

        if pricing_config is not None:
            self.pricing_config = pricing_config
            self.pricing_sha256 = compute_pricing_contract_sha256(pricing_config)
        else:
            self.pricing_config, self.pricing_sha256 = load_pricing_config(repo_root=code_root)

        study_budget = self.pricing_config.get("study_budget", {})
        self.total_budget = validate_finite_nonnegative_money(
            self.pricing_config.get("total_study_budget_usd")
            or study_budget.get("total_budget_usd", "19.99000000"),
            "total_budget_usd",
        )
        self.prior_pilot_hold = validate_finite_nonnegative_money(
            self.pricing_config.get("prior_pilot_provisional_hold_usd")
            or study_budget.get("prior_pilot_provisional_hold_usd", "0.05264010"),
            "prior_pilot_provisional_hold_usd",
        )

        bounds = self.pricing_config.get("reservation_bounds", {})
        self.attempt_worst_usd = validate_finite_nonnegative_money(
            bounds.get("default_attempt_worst_usd", "0.53974560"), "default_attempt_worst_usd"
        )
        self.logical_worst_usd = validate_finite_nonnegative_money(
            bounds.get("default_logical_worst_usd", "2.15898240"), "default_logical_worst_usd"
        )

        self._data: dict[str, Any] = {}
        self.is_already_initialized = False
        with study_ledger_and_anchor_lock(self.lock_path, self.anchor_lock_path):
            self._load_or_initialize_unlocked()

    def _load_or_initialize_unlocked(self) -> None:
        """Load existing ledger or initialize fresh study-wide ledger with anchor protection."""
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.anchor_path.parent.mkdir(parents=True, exist_ok=True)

        anchor_exists = self.anchor_path.exists()
        ledger_exists = self.ledger_path.exists()

        if anchor_exists and not ledger_exists:
            raise LiveExecutionBlockedError(
                f"LIVE_EXECUTION_BLOCKED: Study initialization anchor exists at "
                f"{self.anchor_path}, but study ledger at {self.ledger_path} is missing. "
                f"Refusing silent re-initialization of fresh budget."
            )

        if not anchor_exists and ledger_exists:
            raise LiveExecutionBlockedError(
                f"LIVE_EXECUTION_BLOCKED: Study ledger exists at {self.ledger_path}, "
                f"but study initialization anchor at {self.anchor_path} is missing. "
                f"Refusing unanchored ledger."
            )

        if not anchor_exists and not ledger_exists:
            self.is_already_initialized = False
            initial_available = round_credit_down(self.total_budget - self.prior_pilot_hold)
            anchor_payload: dict[str, Any] = {
                "schema_version": "1.0.0",
                "study_id": "rag2attack-study-wide",
                "pricing_contract_sha256": self.pricing_sha256,
                "total_budget_usd": str(self.total_budget),
                "prior_pilot_provisional_hold_usd": str(self.prior_pilot_hold),
                "initial_available_usd": str(initial_available),
                "ledger_path": str(self.ledger_path.resolve()),
            }
            if self.output_directory is not None:
                anchor_payload["output_directory"] = str(self.output_directory)
            if self.experiment_id is not None:
                anchor_payload["experiment_id"] = str(self.experiment_id)

            self._write_anchor_atomically_unlocked(anchor_payload)

            self._data = {
                "schema_version": "1.0.0",
                "study_id": "rag2attack-study-wide",
                "pricing_contract_sha256": self.pricing_sha256,
                "service_tier": "default",
                "total_budget_usd": str(self.total_budget),
                "prior_pilot_provisional_hold_usd": str(self.prior_pilot_hold),
                "cumulative_settled_cost_usd": "0.00000000",
                "active_reservations_usd": "0.00000000",
                "uncommitted_available_balance_usd": str(initial_available),
                "settlement_records_count": 0,
                "active_reservations": {},
                "settled_records": {},
            }
            self._write_atomically_unlocked()
        else:
            anchor_raw = _strict_json_loads(self.anchor_path.read_bytes())
            if anchor_raw.get("pricing_contract_sha256") != self.pricing_sha256:
                raise ValueError(
                    f"Pricing contract mismatch in study anchor: "
                    f"{anchor_raw.get('pricing_contract_sha256')} != {self.pricing_sha256}"
                )
            anchor_total = validate_finite_nonnegative_money(
                anchor_raw.get("total_budget_usd"), "total_budget_usd"
            )
            if anchor_total != self.total_budget:
                raise ValueError(
                    f"Total study budget mismatch in anchor: "
                    f"existing anchor has {anchor_total}, expected {self.total_budget}"
                )
            anchor_pilot = validate_finite_nonnegative_money(
                anchor_raw.get("prior_pilot_provisional_hold_usd"),
                "prior_pilot_provisional_hold_usd",
            )
            if anchor_pilot != self.prior_pilot_hold:
                raise ValueError(
                    f"Prior pilot hold mismatch in anchor: "
                    f"existing anchor has {anchor_pilot}, expected {self.prior_pilot_hold}"
                )

            rec_out = anchor_raw.get("output_directory")
            if rec_out is None and self.output_directory is not None:
                # First time an output directory is bound to this study
                anchor_raw["output_directory"] = str(self.output_directory)
                if self.experiment_id is not None:
                    anchor_raw["experiment_id"] = str(self.experiment_id)
                self._write_anchor_atomically_unlocked(anchor_raw)
                self.is_already_initialized = False
            elif rec_out is not None:
                self.is_already_initialized = True
                if (
                    self.output_directory is not None
                    and Path(rec_out).resolve() != self.output_directory
                ):
                    self.output_dir_mismatch = True
                else:
                    self.output_dir_mismatch = False
            else:
                self.is_already_initialized = False
                self.output_dir_mismatch = False

            ledger_raw = _strict_json_loads(self.ledger_path.read_bytes())
            if ledger_raw.get("pricing_contract_sha256") != self.pricing_sha256:
                raise ValueError(
                    f"Pricing contract mismatch in study ledger: "
                    f"{ledger_raw.get('pricing_contract_sha256')} != {self.pricing_sha256}"
                )
            existing_total = validate_finite_nonnegative_money(
                ledger_raw.get("total_budget_usd"), "total_budget_usd"
            )
            if existing_total != self.total_budget:
                raise ValueError(
                    f"Total study budget mismatch: existing ledger has {existing_total}, "
                    f"expected {self.total_budget}"
                )
            existing_pilot = validate_finite_nonnegative_money(
                ledger_raw.get("prior_pilot_provisional_hold_usd"),
                "prior_pilot_provisional_hold_usd",
            )
            if existing_pilot != self.prior_pilot_hold:
                raise ValueError(
                    f"Prior pilot hold mismatch: existing ledger has {existing_pilot}, "
                    f"expected {self.prior_pilot_hold}"
                )

            self._data = ledger_raw
            self._verify_balance_invariant_unlocked()

    def _verify_balance_invariant_unlocked(self) -> None:
        """Deeply validate that ledger aggregates match all hold and settled records exactly."""
        total = validate_finite_nonnegative_money(
            self._data.get("total_budget_usd"), "total_budget_usd"
        )
        if total != self.total_budget:
            raise ValueError(
                f"Total budget drift: recorded {total} != configured {self.total_budget}"
            )

        pilot = validate_finite_nonnegative_money(
            self._data.get("prior_pilot_provisional_hold_usd"), "prior_pilot_provisional_hold_usd"
        )
        if pilot != self.prior_pilot_hold:
            raise ValueError(
                f"Pilot hold drift: recorded {pilot} != configured {self.prior_pilot_hold}"
            )

        settled = validate_finite_nonnegative_money(
            self._data.get("cumulative_settled_cost_usd"), "cumulative_settled_cost_usd"
        )
        reserved = validate_finite_nonnegative_money(
            self._data.get("active_reservations_usd"), "active_reservations_usd"
        )
        available = validate_finite_nonnegative_money(
            self._data.get("uncommitted_available_balance_usd"), "uncommitted_available_balance_usd"
        )

        rec_count = self._data.get("settlement_records_count")
        if type(rec_count) is not int or isinstance(rec_count, bool) or rec_count < 0:
            raise ValueError(
                f"settlement_records_count must be non-negative int, "
                f"got {type(rec_count).__name__}"
            )

        active_reservations = self._data.get("active_reservations")
        if not isinstance(active_reservations, dict):
            raise ValueError(
                f"active_reservations must be dict, got {type(active_reservations).__name__}"
            )

        sum_reserved = Decimal("0.0")
        for k, v in active_reservations.items():
            if not isinstance(k, str):
                raise ValueError(f"active_reservation key must be string, got {type(k).__name__}")
            hold_amount = validate_finite_nonnegative_money(v, f"active_reservations[{k}]")
            if hold_amount <= Decimal("0.0"):
                raise ValueError(
                    f"active_reservation[{k}] must be strictly positive: {hold_amount}"
                )
            if round_cost_up(hold_amount) != hold_amount:
                raise ValueError(
                    f"active_reservation[{k}] has unquantized precision: {hold_amount}"
                )
            sum_reserved += hold_amount

        sum_reserved_rounded = round_cost_up(sum_reserved)
        if reserved != sum_reserved_rounded:
            raise ValueError(
                f"Active reservations aggregate mismatch: recorded {reserved} "
                f"!= sum of items {sum_reserved_rounded}"
            )

        settled_records = self._data.get("settled_records")
        if not isinstance(settled_records, dict):
            raise ValueError(f"settled_records must be dict, got {type(settled_records).__name__}")

        if len(settled_records) != rec_count:
            raise ValueError(
                f"Settled records count mismatch: recorded {rec_count} "
                f"!= actual {len(settled_records)}"
            )

        sum_settled = Decimal("0.0")
        for k, item in settled_records.items():
            if not isinstance(k, str) or not isinstance(item, dict):
                raise ValueError(f"settled_records[{k}] must be a dict")
            c = validate_finite_nonnegative_money(
                item.get("cost_usd"), f"settled_records[{k}].cost_usd"
            )
            if round_cost_up(c) != c:
                raise ValueError(f"settled_records[{k}].cost_usd has unquantized precision: {c}")
            r = validate_finite_nonnegative_money(
                item.get("refund_usd"), f"settled_records[{k}].refund_usd"
            )
            if round_credit_down(r) != r:
                raise ValueError(f"settled_records[{k}].refund_usd has unquantized precision: {r}")
            sha = item.get("record_sha256")
            is_valid_sha = (
                isinstance(sha, str)
                and len(sha) == 64
                and all(ch in "0123456789abcdef" for ch in sha.lower())
            )
            if not is_valid_sha:
                raise ValueError(f"Invalid record_sha256 in settled_records[{k}]: {sha}")
            sum_settled += c

        sum_settled_rounded = round_cost_up(sum_settled)
        if settled != sum_settled_rounded:
            raise ValueError(
                f"Cumulative settled cost mismatch: recorded {settled} "
                f"!= sum of items {sum_settled_rounded}"
            )

        # Disjoint keys invariant
        overlap = set(active_reservations.keys()) & set(settled_records.keys())
        if overlap:
            raise ValueError(
                f"Integrity violation: keys {overlap} present in both active and settled sets"
            )

        # Conservation of funds invariant
        expected_available = round_credit_down(total - pilot - settled - reserved)
        if available != expected_available:
            raise ValueError(
                f"Study budget ledger integrity violation: available {available} "
                f"!= expected {expected_available}"
            )

        if "has_breach" in self._data and not isinstance(self._data["has_breach"], bool):
            raise ValueError(
                f"has_breach must be bool, got {type(self._data['has_breach']).__name__}"
            )
        if "breached_records" in self._data and not isinstance(
            self._data["breached_records"], dict
        ):
            raise ValueError(
                f"breached_records must be dict, "
                f"got {type(self._data['breached_records']).__name__}"
            )

    def _write_anchor_atomically_unlocked(self, data: dict[str, Any]) -> None:
        """Write study anchor to disk with fsync under atomic rename pattern.

        Safely creates known tmp file with exclusive open ('xb') to fail closed
        against hijacking or pre-existing hardlinks.
        """
        payload = canonical_json_bytes(data)
        tmp_file = self.anchor_path.with_suffix(".tmp")
        validate_safe_anchor_path(tmp_file)

        if tmp_file.exists():
            st = tmp_file.stat()
            if st.st_nlink > 1:
                raise ValueError(
                    f"hardlinked temporary file rejected: {tmp_file} (st_nlink={st.st_nlink})"
                )
            tmp_file.unlink()

        with tmp_file.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())

        tmp_file.replace(self.anchor_path)

    def _write_atomically_unlocked(self) -> None:
        """Write ledger to disk with fsync under atomic rename pattern.

        Safely creates known tmp file with exclusive open ('xb') to fail closed
        against hijacking or pre-existing hardlinks.
        """
        self._verify_balance_invariant_unlocked()
        payload = canonical_json_bytes(self._data)
        tmp_file = self.ledger_path.with_suffix(".tmp")
        validate_safe_ledger_path(tmp_file)

        if tmp_file.exists():
            st = tmp_file.stat()
            if st.st_nlink > 1:
                raise ValueError(
                    f"hardlinked temporary file rejected: {tmp_file} (st_nlink={st.st_nlink})"
                )
            tmp_file.unlink()

        with tmp_file.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())

        tmp_file.replace(self.ledger_path)

    @property
    def uncommitted_available_balance_usd(self) -> Decimal:
        return Decimal(str(self._data["uncommitted_available_balance_usd"]))

    @property
    def cumulative_settled_cost_usd(self) -> Decimal:
        return Decimal(str(self._data["cumulative_settled_cost_usd"]))

    @property
    def active_reservations_usd(self) -> Decimal:
        return Decimal(str(self._data["active_reservations_usd"]))

    @property
    def has_breach(self) -> bool:
        return bool(self._data.get("has_breach", False))

    @property
    def settled_records(self) -> dict[str, Any]:
        return dict(self._data.get("settled_records", {}))

    def reserve(self, key_str: str, amount_usd: Decimal) -> None:
        """Reserve funds before request dispatch under single-writer lock.

        Raises:
            LiveExecutionBlockedError: If available budget is insufficient or prior breach exists.
            ValueError: If duplicate active reservation or invalid amount.
        """
        amount_valid = validate_finite_nonnegative_money(amount_usd, "amount_usd")
        amount_round = round_cost_up(amount_valid)

        with study_ledger_and_anchor_lock(self.lock_path, self.anchor_lock_path):
            self._load_or_initialize_unlocked()
            if self.has_breach:
                raise LiveExecutionBlockedError(
                    "LIVE_EXECUTION_BLOCKED: Study ledger has prior breach; "
                    "dispatch permanently blocked"
                )
            available = self.uncommitted_available_balance_usd

            if available < amount_round:
                raise LiveExecutionBlockedError(
                    f"LIVE_EXECUTION_BLOCKED: Insufficient study budget. Available credit "
                    f"${available} USD is less than required worst-case reservation "
                    f"${amount_round} USD."
                )

            active_reservations = self._data.setdefault("active_reservations", {})
            if key_str in active_reservations:
                raise ValueError(
                    f"Request {key_str} already has an active reservation in study ledger"
                )

            active_reservations[key_str] = str(amount_round)
            new_reserved = sum(
                (Decimal(str(v)) for v in active_reservations.values()), Decimal("0.0")
            )
            new_available = round_credit_down(
                self.total_budget
                - self.prior_pilot_hold
                - self.cumulative_settled_cost_usd
                - new_reserved
            )

            self._data["active_reservations_usd"] = str(round_cost_up(new_reserved))
            self._data["uncommitted_available_balance_usd"] = str(new_available)
            self._write_atomically_unlocked()

    def settle(
        self,
        key_str: str,
        cost_usd: Decimal,
        reserved_amount_usd: Decimal,
        record_sha256: str,
        breach: bool = False,
        breach_reason: str | None = None,
    ) -> Decimal:
        """Settle a completed request, debiting settled cost and refunding delta.

        Requires exact existing active hold and amount. Recomputes sums from scratch.
        Idempotent if called repeatedly with identical record hash and cost.

        Returns:
            refund_usd: The delta credited back to available balance.
        """
        cost_valid = validate_finite_nonnegative_money(cost_usd, "cost_usd")
        reserved_valid = validate_finite_nonnegative_money(
            reserved_amount_usd, "reserved_amount_usd"
        )
        cost_round = round_cost_up(cost_valid)
        reserved_round = round_cost_up(reserved_valid)

        if cost_round > reserved_round:
            raise ValueError(
                f"Settled cost ${cost_round} cannot exceed reserved amount ${reserved_round}"
            )

        with study_ledger_and_anchor_lock(self.lock_path, self.anchor_lock_path):
            self._load_or_initialize_unlocked()
            settled_history = self._data.setdefault("settled_records", {})

            # Idempotency check
            if key_str in settled_history:
                prior = settled_history[key_str]
                is_match = (
                    prior.get("record_sha256") == record_sha256
                    and Decimal(str(prior.get("cost_usd"))) == cost_round
                )
                if is_match:
                    return Decimal(str(prior.get("refund_usd")))
                raise ValueError(f"Conflicting duplicate settlement attempted for {key_str}")

            active_reservations = self._data.setdefault("active_reservations", {})
            if key_str not in active_reservations:
                raise ValueError(
                    f"No active reservation found for {key_str}; cannot settle unreserved request"
                )

            existing_hold = Decimal(str(active_reservations[key_str]))
            if existing_hold != reserved_round:
                raise ValueError(
                    f"Reservation amount mismatch for {key_str}: "
                    f"expected {existing_hold}, got {reserved_round}"
                )

            # Delete hold and calculate refund
            del active_reservations[key_str]
            refund_round = round_credit_down(reserved_round - cost_round)

            settled_entry: dict[str, Any] = {
                "record_sha256": record_sha256,
                "cost_usd": str(cost_round),
                "refund_usd": str(refund_round),
            }
            if breach:
                settled_entry["breach"] = True
                if breach_reason:
                    settled_entry["breach_reason"] = breach_reason
                self._data["has_breach"] = True
                breached = self._data.setdefault("breached_records", {})
                breached[key_str] = {
                    "cost_usd": str(cost_round),
                    "reason": breach_reason,
                }
            settled_history[key_str] = settled_entry

            # Recompute all sums from scratch (never max(0) or pop(None))
            new_reserved = sum(
                (Decimal(str(v)) for v in active_reservations.values()), Decimal("0.0")
            )
            new_settled = sum(
                (Decimal(str(e["cost_usd"])) for e in settled_history.values()), Decimal("0.0")
            )
            new_available = round_credit_down(
                self.total_budget - self.prior_pilot_hold - new_settled - new_reserved
            )

            self._data["active_reservations_usd"] = str(round_cost_up(new_reserved))
            self._data["cumulative_settled_cost_usd"] = str(round_cost_up(new_settled))
            self._data["uncommitted_available_balance_usd"] = str(new_available)
            self._data["settlement_records_count"] = len(settled_history)
            self._write_atomically_unlocked()
            return refund_round

    def cancel_orphan_hold(self, key_str: str, amount_usd: Decimal) -> None:
        """Cancel an orphan hold (e.g. crash or safe abandonment) and credit funds back.

        Requires exact existing active hold and amount. Recomputes sums from scratch.
        """
        amount_valid = validate_finite_nonnegative_money(amount_usd, "amount_usd")
        amount_round = round_cost_up(amount_valid)

        with study_ledger_and_anchor_lock(self.lock_path, self.anchor_lock_path):
            self._load_or_initialize_unlocked()
            active_reservations = self._data.setdefault("active_reservations", {})
            if key_str not in active_reservations:
                raise ValueError(f"No active reservation found for {key_str}; cannot cancel hold")

            existing_hold = Decimal(str(active_reservations[key_str]))
            if existing_hold != amount_round:
                raise ValueError(
                    f"Hold amount mismatch for {key_str}: "
                    f"expected {existing_hold}, got {amount_round}"
                )

            del active_reservations[key_str]

            settled_history = self._data.setdefault("settled_records", {})
            new_reserved = sum(
                (Decimal(str(v)) for v in active_reservations.values()), Decimal("0.0")
            )
            new_settled = sum(
                (Decimal(str(e["cost_usd"])) for e in settled_history.values()), Decimal("0.0")
            )
            new_available = round_credit_down(
                self.total_budget - self.prior_pilot_hold - new_settled - new_reserved
            )

            self._data["active_reservations_usd"] = str(round_cost_up(new_reserved))
            self._data["uncommitted_available_balance_usd"] = str(new_available)
            self._write_atomically_unlocked()

    def get_summary(self) -> dict[str, Any]:
        """Return immutable summary copy for run_summary.json integration."""
        return {
            "pricing_contract_sha256": self.pricing_sha256,
            "service_tier": "default",
            "total_budget_usd": str(self.total_budget),
            "prior_pilot_provisional_hold_usd": str(self.prior_pilot_hold),
            "cumulative_settled_cost_usd": str(self.cumulative_settled_cost_usd),
            "active_reservations_usd": str(self.active_reservations_usd),
            "uncommitted_available_balance_usd": str(self.uncommitted_available_balance_usd),
            "settlement_records_count": self._data.get("settlement_records_count", 0),
            "has_breach": self.has_breach,
            "breached_records_count": len(self._data.get("breached_records", {})),
        }


def calculate_attempt_token_cost(
    prompt_tokens: Optional[int],
    completion_tokens: Optional[int],
    pricing_config: dict[str, Any],
    *,
    cached_tokens: Optional[int] = None,
    tier: str = "default",
) -> Decimal:
    """Calculate actual dollar cost for a single attempt receipt.

    Invariants:
    - Never fallback unknown tier to default; reject unknown tier immediately.
    - Validate prompt, completion, and cached token types strictly.
    - Never clamp invalid cached_tokens > prompt_tokens; raise ValueError on ceiling or breach.
    - If cache usage fields are absent/null, charges cache-write tariff for ALL prompt tokens.
    - If prompt_tokens or completion_tokens are None/missing: returns full worst attempt charge.
    """
    tariffs = pricing_config.get("tariffs", {})
    if tier not in tariffs:
        raise ValueError(f"Unknown service tier '{tier}'; no fallback permitted")

    bounds = pricing_config.get("reservation_bounds", {})
    worst_charge = Decimal(str(bounds.get("default_attempt_worst_usd", "0.53974560")))

    if prompt_tokens is None or completion_tokens is None:
        return worst_charge

    # Strict type validation (reject bool, float, str, negative)
    p_tok = validate_token_count(prompt_tokens, "prompt_tokens")
    c_tok = validate_token_count(completion_tokens, "completion_tokens")
    ca_tok = validate_token_count(cached_tokens, "cached_tokens")

    ceilings = pricing_config.get("ceilings", {})
    max_in = ceilings.get("max_input_tokens", 1050000)
    max_out = ceilings.get("max_output_tokens", 8192)
    short_limit = ceilings.get("short_context_limit", 272000)

    if p_tok is None or c_tok is None or p_tok > max_in or c_tok > max_out:
        raise ValueError(
            f"Token counts (input={p_tok}, output={c_tok}) exceeded context ceilings "
            f"(max_in={max_in}, max_out={max_out})"
        )

    # Never clamp invalid cached_tokens to prompt
    if ca_tok is not None and ca_tok > p_tok:
        raise ValueError(
            f"Invalid cache usage: cached_tokens ({ca_tok}) cannot exceed prompt_tokens ({p_tok})"
        )

    rate_table = tariffs[tier].get("long" if p_tok > short_limit else "short", {})
    scale = Decimal("1000000")
    p_cache_read = Decimal(str(rate_table.get("cache_read_per_million", "0.02"))) / scale
    p_cache_write = Decimal(str(rate_table.get("cache_write_per_million", "0.25"))) / scale
    p_out = Decimal(str(rate_table.get("output_per_million", "1.20"))) / scale

    # If cache usage is unspecified or 0, use cache-write price for all input tokens
    if ca_tok is not None and ca_tok > 0:
        read_tok = ca_tok
        write_tok = p_tok - read_tok
        cost_in = (Decimal(read_tok) * p_cache_read) + (Decimal(write_tok) * p_cache_write)
    else:
        cost_in = Decimal(p_tok) * p_cache_write

    cost_out = Decimal(c_tok) * p_out
    return round_cost_up(cost_in + cost_out)


def calculate_request_cost_from_receipts(
    attempts_consumed: int,
    receipts: list[dict[str, Any]],
    record: Any,
    pricing_config: dict[str, Any],
    *,
    tier: str = "default",
    expected_model: Optional[str] = None,
) -> tuple[Decimal, bool, Optional[str]]:
    """Compute exact request settlement cost from durable per-attempt receipts and committed record.

    Invariants:
    - Strict ordinal and attempt_index uniqueness covering [0..attempts_consumed-1].
    - Zero duplicate receipts; duplicate receipts immediately flag breach.
    - Final attempt receipt binds strictly to committed record (ID, model, tokens, status).
    - Returned service tier must match required tier (missing remains unknown and breaches).
    - No silent min clipping: exceeding logical worst flags breach.

    Returns:
        (total_cost, breach_detected, breach_reason)
    """
    bounds = pricing_config.get("reservation_bounds", {})
    attempt_worst = Decimal(str(bounds.get("default_attempt_worst_usd", "0.53974560")))
    logical_worst = Decimal(str(bounds.get("default_logical_worst_usd", "2.15898240")))
    ceilings = pricing_config.get("ceilings", {})
    max_in = ceilings.get("max_input_tokens", 1050000)
    max_out = ceilings.get("max_output_tokens", 8192)

    breach = False
    breach_reasons: list[str] = []

    # 1. Validate receipt counts and uniqueness
    if len(receipts) != attempts_consumed:
        breach = True
        breach_reasons.append(
            f"Receipt count {len(receipts)} does not match attempts_consumed {attempts_consumed}"
        )

    receipt_by_attempt: dict[int, dict[str, Any]] = {}
    for r in receipts:
        idx = r.get("attempt_index")
        if not isinstance(idx, int) or isinstance(idx, bool):
            breach = True
            breach_reasons.append(f"Invalid non-integer attempt_index {idx}")
            continue
        if idx in receipt_by_attempt:
            breach = True
            breach_reasons.append(f"Duplicate receipt for attempt_index {idx}")
        else:
            receipt_by_attempt[idx] = r

    expected_indices = set(range(attempts_consumed))
    if set(receipt_by_attempt.keys()) != expected_indices:
        breach = True
        breach_reasons.append(
            f"Receipt indices {set(receipt_by_attempt.keys())} "
            f"do not cover expected {expected_indices}"
        )

    # 2. Binding to committed record
    if record is not None:
        rec_attempts = getattr(record, "request_attempt_count", None)
        if rec_attempts is not None and rec_attempts != attempts_consumed:
            breach = True
            breach_reasons.append(
                f"Record attempt count {rec_attempts} does not match "
                f"consumed attempts {attempts_consumed}"
            )

        final_idx = attempts_consumed - 1
        final_receipt = receipt_by_attempt.get(final_idx) if final_idx >= 0 else None
        rec_status = getattr(record, "parse_status", None)

        if final_receipt is not None:
            if rec_status in ("TIMEOUT", "API_FAILURE"):
                if final_receipt.get("status") not in ("TIMEOUT", "API_FAILURE"):
                    breach = True
                    breach_reasons.append(
                        f"Final receipt status '{final_receipt.get('status')}' "
                        f"does not match record failure '{rec_status}'"
                    )
            else:
                # Terminal success or post-hoc validation outcome
                # Verify Response ID binding
                rec_resp_id = getattr(record, "response_id", None)
                recpt_resp_id = final_receipt.get("response_id")
                if rec_resp_id:
                    if not recpt_resp_id:
                        breach = True
                        breach_reasons.append(
                            f"Missing receipt response_id for record '{rec_resp_id}'"
                        )
                    elif rec_resp_id != recpt_resp_id:
                        breach = True
                        breach_reasons.append(
                            f"Response ID mismatch: record '{rec_resp_id}' != "
                            f"receipt '{recpt_resp_id}'"
                        )

                # Verify Token usage binding
                rec_p_tok = getattr(record, "prompt_tokens", None)
                rec_c_tok = getattr(record, "completion_tokens", None)
                recpt_in = final_receipt.get("input_tokens")
                recpt_out = final_receipt.get("output_tokens")
                if rec_p_tok != recpt_in or rec_c_tok != recpt_out:
                    breach = True
                    breach_reasons.append(
                        f"Token count mismatch: record ({rec_p_tok}, {rec_c_tok}) "
                        f"!= receipt ({recpt_in}, {recpt_out})"
                    )

                # Verify Model binding
                rec_model = getattr(record, "model", None)
                recpt_model = final_receipt.get("model")
                if rec_model:
                    if not recpt_model:
                        breach = True
                        breach_reasons.append(
                            f"Missing receipt model for record '{rec_model}'"
                        )
                    elif rec_model != recpt_model:
                        breach = True
                        breach_reasons.append(
                            f"Model mismatch: record '{rec_model}' != receipt '{recpt_model}'"
                        )

    # 3. Compute cost per attempt
    total_cost = Decimal("0.0")

    for i in range(attempts_consumed):
        r = receipt_by_attempt.get(i)
        if r is None:
            total_cost += attempt_worst
            continue

        status = r.get("status")
        if status != "SUCCESS":
            total_cost += attempt_worst
            continue

        # Check returned service tier (no configured-tier substitution permitted)
        r_tier = r.get("service_tier")
        if r_tier != tier:
            breach = True
            breach_reasons.append(
                f"Attempt {i} returned tier '{r_tier}' mismatch with required '{tier}'"
            )
            total_cost += attempt_worst
            continue

        if expected_model:
            r_model = r.get("model")
            if not r_model:
                breach = True
                breach_reasons.append(
                    f"Attempt {i} missing model; expected '{expected_model}'"
                )
                total_cost += attempt_worst
                continue
            elif r_model != expected_model:
                breach = True
                breach_reasons.append(
                    f"Attempt {i} model '{r_model}' != expected '{expected_model}'"
                )
                total_cost += attempt_worst
                continue

        in_tok = r.get("input_tokens")
        out_tok = r.get("output_tokens")
        ca_tok = r.get("cached_tokens")

        if in_tok is not None and (in_tok > max_in or in_tok < 0):
            breach = True
            breach_reasons.append(f"Attempt {i} input tokens {in_tok} exceeded ceiling {max_in}")
            total_cost += attempt_worst
            continue

        if out_tok is not None and (out_tok > max_out or out_tok < 0):
            breach = True
            breach_reasons.append(f"Attempt {i} output tokens {out_tok} exceeded ceiling {max_out}")
            total_cost += attempt_worst
            continue

        if ca_tok is not None and in_tok is not None and (ca_tok > in_tok or ca_tok < 0):
            breach = True
            breach_reasons.append(f"Attempt {i} cached tokens {ca_tok} exceeded input {in_tok}")
            total_cost += attempt_worst
            continue

        try:
            cost = calculate_attempt_token_cost(
                in_tok,
                out_tok,
                pricing_config,
                cached_tokens=ca_tok,
                tier=tier,
            )
            total_cost += cost
        except Exception as exc:
            breach = True
            breach_reasons.append(f"Attempt {i} cost calculation error: {exc}")
            total_cost += attempt_worst

    rounded_cost = round_cost_up(total_cost)

    # 4. Check against logical worst and hold worst on breach
    if breach:
        final_cost = min(logical_worst, round_cost_up(attempt_worst * max(1, attempts_consumed)))
    elif rounded_cost > logical_worst:
        breach = True
        breach_reasons.append(
            f"Calculated total cost ${rounded_cost} exceeds "
            f"logical worst-case reservation ${logical_worst}"
        )
        final_cost = logical_worst
    else:
        final_cost = rounded_cost

    reason_str = "; ".join(breach_reasons) if breach_reasons else None
    return final_cost, breach, reason_str
