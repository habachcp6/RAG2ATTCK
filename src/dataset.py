"""
RAG2ATTCK - Dataset & Preflight Module (Tasks 0, 1, 2, 3)
Handles path containment, capacity assessment, source context validation,
preflight report generation, and dataset ingestion.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sys
from typing import Any, Dict, List, Optional


class PreflightGateBlocked(RuntimeError):
    """Base exception for all preflight gate failures causing pipeline halt."""
    def __init__(self, message: str, condition_code: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"[{condition_code}] {message}")
        self.condition_code = condition_code
        self.details = details or {}


class PreflightCapacityError(PreflightGateBlocked):
    """Raised when free disk space is below required threshold."""
    def __init__(self, free_bytes: int, required_bytes: int, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            f"Insufficient disk space: {free_bytes / (1024**3):.2f} GiB available, "
            f"{required_bytes / (1024**3):.2f} GiB required.",
            condition_code="GATE-02_03_CAPACITY",
            details={"free_bytes": free_bytes, "required_bytes": required_bytes, **(details or {})}
        )


class PreflightPathSafetyError(PreflightGateBlocked):
    """Raised when path escapes workspace or violates safety rules."""
    def __init__(self, path: str, reason: str):
        super().__init__(
            f"Path safety violation for '{path}': {reason}",
            condition_code="GATE-01_PATH_SAFETY",
            details={"path": path, "reason": reason}
        )


class PreflightSourceContextError(PreflightGateBlocked):
    """Raised when source research files are missing or modified."""
    def __init__(self, filename: str, reason: str):
        super().__init__(
            f"Source document verification failed for '{filename}': {reason}",
            condition_code="GATE-04_05_SOURCE_CONTEXT",
            details={"filename": filename, "reason": reason}
        )


@dataclass(frozen=True)
class PathVerification:
    path: str
    resolved: str
    is_within_workspace: bool
    writable: bool


@dataclass(frozen=True)
class CapacityAssessment:
    drive: str
    live_total_bytes: int
    live_used_bytes: int
    live_free_bytes: int
    live_free_gib: float
    estimates_breakdown_bytes: Dict[str, int]
    total_estimate_bytes: int
    total_estimate_gib: float
    estimate_plus_one_gib_bytes: int
    minimum_floor_bytes: int
    effective_required_free_bytes: int
    effective_required_free_gib: float
    headroom_bytes: int
    headroom_gib: float
    capacity_sufficient: bool


def get_default_workspace_root() -> Path:
    return Path(r"D:\RAG2ATT&CK").resolve()


def resolve_secure_path(workspace_root: Path, target: str | Path) -> Path:
    """
    Resolves a target path and ensures it is strictly within workspace_root.
    Raises PreflightPathSafetyError if resolution escapes workspace_root.
    """
    workspace_root = workspace_root.resolve()
    target_path = Path(target)
    if not target_path.is_absolute():
        resolved = (workspace_root / target_path).resolve()
    else:
        resolved = target_path.resolve()

    if not resolved.is_relative_to(workspace_root):
        raise PreflightPathSafetyError(
            str(target),
            f"Resolved path '{resolved}' escapes workspace root '{workspace_root}'"
        )
    return resolved


def verify_all_workspace_paths(workspace_root: Path) -> Dict[str, PathVerification]:
    """
    Verifies all designated workspace directories for containment, symlinks, and writability.
    """
    workspace_root = workspace_root.resolve()
    designated_paths = {
        "data_raw_windows_apt": "data/raw/windows_apt_2025/v3",
        "attack_raw_enterprise": "attack/raw/enterprise-v19.2",
        "data_metadata": "data/metadata",
        "data_audit": "data/audit",
        "data_ground_truth": "data/ground_truth",
        "data_processed": "data/processed",
        "reports": "reports",
        "docs_context": "docs/context",
        "config": "config",
        "src": "src",
        "tests": "tests",
        "venv": ".venv",
        "cache": ".cache",
        "tmp": ".tmp",
    }

    result = {}
    for name, rel in designated_paths.items():
        resolved = resolve_secure_path(workspace_root, rel)
        resolved.mkdir(parents=True, exist_ok=True)
        writable = os.access(resolved, os.W_OK)
        result[name] = PathVerification(
            path=rel,
            resolved=str(resolved),
            is_within_workspace=resolved.is_relative_to(workspace_root),
            writable=writable
        )
    return result


def assess_disk_capacity(
    workspace_root: Path,
    custom_breakdown: Optional[Dict[str, int]] = None
) -> CapacityAssessment:
    """
    Calculates 5-component budget and checks live free disk space.
    Gate requirement: free_bytes >= max(estimate + 1 GiB, 5.0 GiB).
    """
    workspace_root = workspace_root.resolve()
    total, used, free = shutil.disk_usage(workspace_root)

    breakdown = custom_breakdown or {
        "downloads_and_staging_bytes": 560 * 1024 * 1024,
        "extraction_and_raw_dataset_bytes": 540 * 1024 * 1024,
        "virtual_environment_and_tooling_bytes": 300 * 1024 * 1024,
        "derived_outputs_bytes": 250 * 1024 * 1024,
        "reproduction_run_bytes": 350 * 1024 * 1024,
    }

    total_est_bytes = sum(breakdown.values())
    one_gib_bytes = 1024 * 1024 * 1024
    min_floor_bytes = 5 * 1024 * 1024 * 1024
    effective_required = max(total_est_bytes + one_gib_bytes, min_floor_bytes)

    capacity_sufficient = free >= effective_required
    headroom = free - effective_required

    drive_letter = workspace_root.drive or "D:"

    return CapacityAssessment(
        drive=drive_letter,
        live_total_bytes=total,
        live_used_bytes=used,
        live_free_bytes=free,
        live_free_gib=round(free / (1024**3), 2),
        estimates_breakdown_bytes=breakdown,
        total_estimate_bytes=total_est_bytes,
        total_estimate_gib=round(total_est_bytes / (1024**3), 2),
        estimate_plus_one_gib_bytes=total_est_bytes + one_gib_bytes,
        minimum_floor_bytes=min_floor_bytes,
        effective_required_free_bytes=effective_required,
        effective_required_free_gib=round(effective_required / (1024**3), 2),
        headroom_bytes=headroom,
        headroom_gib=round(headroom / (1024**3), 2),
        capacity_sufficient=capacity_sufficient
    )


def verify_source_context(workspace_root: Path) -> Dict[str, Any]:
    """
    Inspects and revalidates canonical research documents and pre-saved source research assets.
    """
    workspace_root = workspace_root.resolve()
    sr_dir = workspace_root / "data" / "audit" / "source_research"
    expected_sr_files = [
        "article_fulltext.xml",
        "article_sections.txt",
        "checksums.sha256",
        "mendeley_v3_files.json",
        "README.md",
        "scenario_manifest.csv",
        "validation_summary.csv"
    ]

    preserved_files = []
    for fname in sorted(expected_sr_files):
        fpath = sr_dir / fname
        if not fpath.exists():
            raise PreflightSourceContextError(fname, f"File missing in {sr_dir}")
        data = fpath.read_bytes()
        preserved_files.append({
            "filename": fname,
            "size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()
        })

    # Canonical documents lookup: physically revalidate files even if saved metadata exists
    saved_ctx_file = workspace_root / "data" / "metadata" / "source_context.json"
    if saved_ctx_file.exists():
        with open(saved_ctx_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        canonical_docs = saved_data.get("canonical_documents", {})
        if not canonical_docs or "docx" not in canonical_docs or "xlsx" not in canonical_docs:
            raise PreflightSourceContextError("canonical_documents", "Saved metadata missing canonical docx/xlsx entries")

        for doc_type in ["docx", "xlsx"]:
            doc_meta = canonical_docs[doc_type]
            rel_path = doc_meta.get("path")
            if not rel_path:
                raise PreflightSourceContextError(doc_type, f"Saved metadata missing path for {doc_type}")

            # Physical resolution with strict workspace containment check
            resolved_path = resolve_secure_path(workspace_root, rel_path)
            if not resolved_path.exists() or not resolved_path.is_file():
                raise PreflightSourceContextError(doc_type, f"Physical canonical file missing: {resolved_path}")

            file_bytes = resolved_path.read_bytes()
            curr_size = len(file_bytes)
            curr_sha256 = hashlib.sha256(file_bytes).hexdigest()

            expected_size = doc_meta.get("size_bytes")
            expected_sha256 = doc_meta.get("sha256")

            if expected_size is not None and curr_size != expected_size:
                raise PreflightSourceContextError(
                    doc_type,
                    f"Canonical document size mismatch for '{rel_path}': expected {expected_size}, got {curr_size}"
                )
            if expected_sha256 is not None and curr_sha256 != expected_sha256:
                raise PreflightSourceContextError(
                    doc_type,
                    f"Canonical document hash mismatch for '{rel_path}': expected {expected_sha256}, got {curr_sha256}"
                )

            # Re-verify and ensure current attributes are recorded
            doc_meta["size_bytes"] = curr_size
            doc_meta["sha256"] = curr_sha256
    else:
        # First-time initialization: allowed only when canonical files are physically present in workspace
        docx_candidates = [
            workspace_root / "docs" / "context" / "RAG_ATTCK_Research_Plan_Updated.docx",
            workspace_root / "Context" / "RAG2ATTCK-20260915T154859Z-1-001" / "RAG2ATTCK" / "RAG_ATTCK_Research_Plan_Updated.docx",
        ]
        xlsx_candidates = [
            workspace_root / "docs" / "context" / "RAG_ATTCK_Project_Tracker_Updated.xlsx",
            workspace_root / "Context" / "RAG2ATTCK-20260915T154859Z-1-001" / "RAG2ATTCK" / "RAG_ATTCK_Project_Tracker_Updated.xlsx",
        ]
        docx_path = None
        for cand in docx_candidates:
            res_cand = resolve_secure_path(workspace_root, cand)
            if res_cand.exists() and res_cand.is_file():
                docx_path = res_cand
                break

        xlsx_path = None
        for cand in xlsx_candidates:
            res_cand = resolve_secure_path(workspace_root, cand)
            if res_cand.exists() and res_cand.is_file():
                xlsx_path = res_cand
                break

        if not docx_path or not xlsx_path:
            missing = []
            if not docx_path:
                missing.append("Research Plan DOCX")
            if not xlsx_path:
                missing.append("Project Tracker XLSX")
            raise PreflightSourceContextError(", ".join(missing), "Canonical documents missing in workspace for initialization")

        docx_bytes = docx_path.read_bytes()
        xlsx_bytes = xlsx_path.read_bytes()
        canonical_docs = {
            "docx": {
                "path": str(docx_path.relative_to(workspace_root)).replace("\\", "/"),
                "size_bytes": len(docx_bytes),
                "sha256": hashlib.sha256(docx_bytes).hexdigest(),
                "title": "Evaluating MITRE ATT&CK-Grounded RAG for Technique Attribution from Windows Endpoint Logs: A Replication-and-Extension Study",
                "version": "1.1",
                "plan_date": "2026-09-15",
                "author": "Hà Hoàng Bách"
            },
            "xlsx": {
                "path": str(xlsx_path.relative_to(workspace_root)).replace("\\", "/"),
                "size_bytes": len(xlsx_bytes),
                "sha256": hashlib.sha256(xlsx_bytes).hexdigest(),
                "sheets": [
                    "Overview",
                    "Roadmap",
                    "RQ_Experiments",
                    "Resources"
                ]
            }
        }

    return {
        "verification_status": "VERIFIED_CANONICAL_PRESERVED",
        "verification_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "canonical_documents": canonical_docs,
        "official_dataset_reference": {
            "dataset_name": "Windows-APT 2025: A Dataset of Attack Scenarios Inspired by Advanced Persistent Threats on Windows Systems",
            "dataset_id": "b8fmtzvpy8",
            "version": 3,
            "provider": "Mendeley Data",
            "dataset_doi": "10.17632/b8fmtzvpy8.3",
            "publication_doi": "10.1016/j.dib.2026.112569",
            "publication_outlet": "Elsevier Data in Brief",
            "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
            "authors": [
                "Maryam Mozaffari",
                "Abbas Yazdinejad",
                "Ali Dehghantanha"
            ],
            "total_mendeley_files": 21,
            "total_mendeley_bytes": 480856926
        },
        "research_plan_parameters": {
            "evaluation_task": "Windows endpoint log -> LLM -> MITRE ATT&CK Technique/Sub-technique attribution",
            "experimental_conditions": ["No-RAG baseline", "ATT&CK-grounded RAG"],
            "retriever_architecture": "Local FAISS vector store on MITRE ATT&CK Windows techniques corpus",
            "target_class_count": "8 to 10 techniques",
            "target_sample_quota_policy": {
                "8_classes": 50,
                "9_classes": 45,
                "10_classes": 40
            },
            "total_evaluation_samples": 400,
            "partition_seed": 20260915,
            "partition_split_mod": "hash(seed + group_id) % 5 == 0 -> dev, else -> final",
            "hard_restrictions": [
                "No model fine-tuning",
                "No autonomous AI agent implementation",
                "No Wazuh/SIEM/EDR live deployment",
                "No custom SDK implementation",
                "No knowledge graph development",
                "No final-holdout sample inspection"
            ]
        },
        "preserved_source_research_files": preserved_files
    }


def run_preflight_check(
    workspace_root: Optional[Path] = None,
    output_path: Optional[Path] = None,
    recheck: bool = False
) -> Dict[str, Any]:
    """
    Executes full Task 0 Preflight verification.
    Writes data/metadata/preflight.json and data/metadata/source_context.json.
    Raises PreflightGateBlocked if any gate condition fails.
    """
    ws = (workspace_root or get_default_workspace_root()).resolve()
    meta_dir = ws / "data" / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)

    # 1. Path Safety, Containment & Windows Junction Detection
    symlinks = []
    junctions = []
    for p in ws.rglob("*"):
        try:
            if p.is_symlink():
                symlinks.append(p)
            elif hasattr(p, "is_junction") and p.is_junction():
                junctions.append(p)
        except (OSError, PermissionError):
            continue

    symlinks_detected = len(symlinks)
    junctions_detected = len(junctions)
    path_verifications = verify_all_workspace_paths(ws)

    all_contained = (symlinks_detected == 0) and all(
        v.is_within_workspace for v in path_verifications.values()
    )

    # Validate that any junctions stay within the workspace root
    junction_targets_contained = True
    for j in junctions:
        try:
            target = Path(os.readlink(j)).resolve()
            if not target.is_relative_to(ws):
                junction_targets_contained = False
                all_contained = False
        except Exception:
            junction_targets_contained = False
            all_contained = False

    # 2. Capacity Assessment
    cap = assess_disk_capacity(ws)
    if not cap.capacity_sufficient:
        raise PreflightCapacityError(cap.live_free_bytes, cap.effective_required_free_bytes)

    # 3. Source Context
    src_ctx = verify_source_context(ws)

    # 4. Runtime Validation
    py_valid = sys.version_info.major == 3 and sys.version_info.minor == 13

    gate_passed = all_contained and cap.capacity_sufficient and py_valid

    preflight_doc = {
        "meta": {
            "schema_version": "1.0.0",
            "task": "T0_PREFLIGHT",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "hostname": platform.node(),
            "os": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "architecture": platform.machine()
            },
            "python_version": sys.version,
            "python_executable": sys.executable,
            "workspace_root": str(ws)
        },
        "path_validation": {
            "workspace_has_special_chars": "&" in str(ws),
            "special_char_safety_mode": "NATIVE_API_AND_LITERAL_PATHS",
            "symlinks_detected": symlinks_detected,
            "junctions_detected": junctions_detected,
            "junction_detection_implemented": True,
            "junction_targets_contained": junction_targets_contained,
            "all_paths_contained": all_contained,
            "resolved_paths": {k: asdict(v) for k, v in path_verifications.items()}
        },
        "capacity_assessment": asdict(cap),
        "source_context": src_ctx,
        "gate_result": {
            "status": "PASS" if gate_passed else "STOP",
            "passed": gate_passed,
            "gate_conditions": {
                "path_containment_passed": all_contained,
                "disk_capacity_passed": cap.capacity_sufficient,
                "source_documents_preserved": True,
                "python_version_valid": py_valid,
                "junction_validation_passed": junction_targets_contained
            },
            "recheck_required_at_execution": True,
            "blocker_reason": None if gate_passed else "One or more gate conditions failed"
        }
    }

    target_json = output_path or (meta_dir / "preflight.json")
    with open(target_json, "w", encoding="utf-8") as f:
        json.dump(preflight_doc, f, indent=2, ensure_ascii=False)

    source_ctx_file = meta_dir / "source_context.json"
    with open(source_ctx_file, "w", encoding="utf-8") as f:
        json.dump(src_ctx, f, indent=2, ensure_ascii=False)

    if not gate_passed:
        raise PreflightGateBlocked("Preflight gate evaluation failed", "GATE_EVALUATION_FAILED", preflight_doc["gate_result"])

    return preflight_doc
