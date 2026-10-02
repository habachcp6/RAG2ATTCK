"""Scientific Report Populator from Diagnostic Evaluation & Analysis Fixtures.

Safely consumes canonical evaluation JSON fixtures and Specialist B's rq_analysis.json,
formats metrics strictly adhering to Scientific Protocol v1.1 and s2_report_population_plan.md,
and populates placeholders in scientific report templates.

SAFETY & INTEGRITY BOUNDARY:
- Strictly operates on mock fixture outputs (fixture_only: true).
- Strictly zero live prediction reads (never touches predictions_*.jsonl).
- Strictly zero provider/network calls (offline socket compliant).
- All generated documents carry prominent private labeling:
  "fixture_only: true" / "DIAGNOSTIC TEST FIXTURE ONLY - NOT CANONICAL NUMERICAL RESULTS".
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluation.experiment_metrics import CONDITIONS  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DISCLAIMER_TEXT = "DIAGNOSTIC TEST FIXTURE ONLY - NOT CANONICAL NUMERICAL RESULTS"
DEFAULT_FIXTURE_DIR = REPO_ROOT / ".tmp" / "s1-offline-reproduction" / "fixture_diagnostics"
FALLBACK_FIXTURE_DIR = REPO_ROOT / "outputs" / "reproduction" / "fixture_diagnostics"
DEFAULT_TEMPLATE_PATH = REPO_ROOT / "docs" / "report" / "scientific_report.md"
DEFAULT_OUTPUT_MD = REPO_ROOT / "reports" / "evidence" / "fixture_populated_report.md"
DEFAULT_AUDIT_JSON = REPO_ROOT / "reports" / "evidence" / "populated_report_slots_fixture.json"


def compute_file_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file on disk."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found on disk: {filepath}")
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def assert_fixture_safety(
    fixture_dir: Path,
    analysis_data: dict[str, Any] | None = None,
    provenance_data: dict[str, Any] | None = None,
) -> None:
    """Fail closed if target is not certified as mock fixture data.

    Prevents accidental population using unverified or live data.
    Strictly zero live prediction reads, zero provider calls.
    """
    is_fixture = False

    # Check companion metadata file if present
    meta_file = fixture_dir / "_fixture_metadata.json"
    if meta_file.is_file():
        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            if meta.get("fixture_only") is True:
                is_fixture = True
        except Exception:
            pass

    if analysis_data:
        if analysis_data.get("fixture_only") is True:
            is_fixture = True
        if analysis_data.get("provenance_status") == "diagnostic_fixture":
            is_fixture = True

    if provenance_data:
        if provenance_data.get("execution_mode") == "mock_fixture":
            is_fixture = True

    prov_file = fixture_dir / "run_provenance.json"
    if not is_fixture and prov_file.is_file():
        try:
            prov = json.loads(prov_file.read_text(encoding="utf-8"))
            if prov.get("execution_mode") == "mock_fixture":
                is_fixture = True
        except Exception:
            pass

    if not is_fixture:
        raise RuntimeError(
            f"[FAIL_CLOSED] populate_report is strictly restricted to diagnostic fixtures "
            f"with fixture_only=True. Refusing to operate on uncertified data at: {fixture_dir}"
        )


def load_fixture_data(fixture_dir: Path, analysis_file: Path | None = None) -> dict[str, Any]:
    """Load canonical evaluation JSON fixtures and Specialist B's rq_analysis.json."""
    if not fixture_dir.is_dir():
        raise FileNotFoundError(f"Fixture directory not found: {fixture_dir}")

    # Native evaluator files
    per_cond_path = fixture_dir / "per_condition_metrics.json"
    failure_decomp_path = fixture_dir / "failure_decomposition.json"
    retrieval_cond_path = fixture_dir / "retrieval_conditional_metrics.json"
    overall_path = fixture_dir / "overall_metrics.json"
    provenance_path = fixture_dir / "run_provenance.json"

    analysis_p = analysis_file or (fixture_dir / "rq_analysis.json")

    per_condition: dict[str, Any] = {}
    if per_cond_path.is_file():
        per_condition = json.loads(per_cond_path.read_text(encoding="utf-8"))

    failure_decomp: dict[str, Any] = {}
    if failure_decomp_path.is_file():
        failure_decomp = json.loads(failure_decomp_path.read_text(encoding="utf-8"))

    retrieval_cond: dict[str, Any] = {}
    if retrieval_cond_path.is_file():
        retrieval_cond = json.loads(retrieval_cond_path.read_text(encoding="utf-8"))

    overall: dict[str, Any] = {}
    if overall_path.is_file():
        overall = json.loads(overall_path.read_text(encoding="utf-8"))

    provenance: dict[str, Any] = {}
    if provenance_path.is_file():
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))

    analysis: dict[str, Any] = {}
    if analysis_p.is_file():
        analysis = json.loads(analysis_p.read_text(encoding="utf-8"))

    assert_fixture_safety(fixture_dir, analysis_data=analysis, provenance_data=provenance)

    return {
        "fixture_dir": fixture_dir,
        "per_condition_metrics": per_condition,
        "failure_decomposition": failure_decomp,
        "retrieval_conditional_metrics": retrieval_cond,
        "overall_metrics": overall,
        "run_provenance": provenance,
        "rq_analysis": analysis,
    }


def extract_slots(data: dict[str, Any]) -> dict[str, Any]:
    """Extract and format all table slots according to canonical schema pointers."""
    per_cond = data["per_condition_metrics"].get("conditions", {})
    failure_by_cond = data["failure_decomposition"].get("by_condition", {})
    retrieval_by_cond = data["retrieval_conditional_metrics"].get("by_condition", {})
    rq_analysis = data["rq_analysis"]
    rq1_by_cond = rq_analysis.get("rq1", {}).get("by_condition", {})
    rq3_tradeoffs = rq_analysis.get("rq3", {}).get("tradeoffs_by_condition", {})
    rq3_views = rq_analysis.get("rq3", {}).get("view_diagnostics", {})
    complexity_by_cond = rq_analysis.get("new_proposed_producer_stratified_gt_complexity", {}).get(
        "by_condition", {}
    )

    slots: dict[str, Any] = {
        "_metadata": {
            "fixture_only": True,
            "disclaimer": DISCLAIMER_TEXT,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "source_fixture_dir": str(data["fixture_dir"]),
        },
        "table_2a": {},
        "table_2b": {},
        "table_3": {},
        "table_4": {},
        "table_5": {},
    }

    # Depth mapping for conditions
    depth_map = {"no_rag": 0, "rag_k1": 1, "rag_k3": 3, "rag_k5": 5, "rag_k10": 10}

    for c in CONDITIONS:
        k = depth_map.get(c, 0)
        c_eval = per_cond.get(c, {})
        c_rq1 = rq1_by_cond.get(c, {})

        # Table 2a: Attribution Performance
        acc_e2e = c_eval.get("accuracy_end_to_end", c_rq1.get("accuracy_end_to_end", 0.0))
        acc_valid = c_eval.get("accuracy_valid_outputs", c_rq1.get("accuracy_valid_outputs", 0.0))
        macro_f1 = c_eval.get("macro_f1", c_rq1.get("macro_f1", 0.0))

        c_complex = complexity_by_cond.get(c, {})
        single_gt_acc = c_complex.get("single_gt_accuracy_e2e")
        multi_gt_acc = c_complex.get("multi_gt_accuracy_e2e")
        complex_delta = c_complex.get("complexity_accuracy_delta")

        slots["table_2a"][c] = {
            "condition": c,
            "k": k,
            "scorable_n": 718,
            "accuracy_end_to_end": f"{acc_e2e * 100:.2f}%",
            "accuracy_valid_outputs": f"{acc_valid * 100:.2f}%",
            "macro_f1": f"{macro_f1 * 100:.2f}%",
            "single_gt_accuracy_e2e": (
                f"{single_gt_acc * 100:.2f}%" if single_gt_acc is not None else None
            ),
            "multi_gt_accuracy_e2e": (
                f"{multi_gt_acc * 100:.2f}%" if multi_gt_acc is not None else None
            ),
            "complexity_accuracy_delta": (
                f"{complex_delta * 100:+.2f} pp" if complex_delta is not None else None
            ),
        }

        # Table 2b: Attribution Diagnostics
        completed = c_eval.get("completed_record_count", 0)
        parse_fail = c_eval.get("parse_failure_count", 0)
        invalid_id = c_eval.get("invalid_id_count", 0)
        invalid_rate = c_eval.get("invalid_id_rate", 0.0)

        slots["table_2b"][c] = {
            "condition": c,
            "scorable_n": 718,
            "completed_outputs": f"{completed:,}",
            "parse_failures": f"{parse_fail:,}",
            "invalid_ids": f"{invalid_id:,}",
            "invalid_id_rate": f"{invalid_rate * 100:.2f}%",
        }

        # Table 3: Representation Stratification
        c_view = rq3_views.get(c, {})
        single_acc = c_view.get("single_view_accuracy_e2e", 0.0)
        context_acc = c_view.get("contextual_view_accuracy_e2e", 0.0)
        single_f1 = c_view.get("single_view_macro_f1", 0.0)
        context_f1 = c_view.get("contextual_view_macro_f1", 0.0)
        delta_acc = c_view.get("view_accuracy_delta", 0.0)

        slots["table_3"][c] = {
            "condition": c,
            "single_acc": f"{single_acc * 100:.2f}%",
            "context_acc": f"{context_acc * 100:.2f}%",
            "single_macro_f1": f"{single_f1 * 100:.2f}%",
            "context_macro_f1": f"{context_f1 * 100:.2f}%",
            "delta_acc": f"{delta_acc * 100:+.2f} pp",
        }

        # Table 4: Decoupled Failure Decomposition
        c_fail = failure_by_cond.get(c, {})
        c_ret = retrieval_by_cond.get(c, {})
        total_scorable = c_fail.get("total_scorable_samples", 718)
        correct_c = c_eval.get("correct_count", 0)
        total_errors = total_scorable - correct_c

        slots["table_4"][c] = {
            "condition": c,
            "total_errors": f"{total_errors:,}",
            "retrieval_miss": (
                "N/A" if c == "no_rag" else f"{c_fail.get('retrieval_miss_count', 0):,}"
            ),
            "downstream_selection_failure": (
                "N/A"
                if c == "no_rag"
                else f"{c_fail.get('valid_but_wrong_classification_count', 0):,}"
            ),
            "parametric_recovery": (
                "N/A" if c == "no_rag" else f"{c_ret.get('retrieval_failure_correct_count', 0):,}"
            ),
            "invalid_attack_id": f"{c_fail.get('invalid_attack_id_count', invalid_id):,}",
            "parse_failure": f"{c_fail.get('parse_failure_count', parse_fail):,}",
            "provider_failure": f"{c_fail.get('provider_failure_count', 0):,}",
        }

        # Table 5: Resource Scaling
        c_trade = rq3_tradeoffs.get(c, {})
        tokens = c_trade.get("tokens", {})
        latency = c_trade.get("latency_ms", {})
        fin = c_trade.get("financial_cost_usd", {})

        mean_prompt_tok = tokens.get("mean_prompt_tokens", 0.0)
        mean_comp_tok = tokens.get("mean_completion_tokens", 0.0)
        sum_prompt_tok = tokens.get("sum_prompt_tokens", int(round(mean_prompt_tok * 1280)))
        sum_comp_tok = tokens.get("sum_completion_tokens", int(round(mean_comp_tok * 1280)))

        mean_lat_s = latency.get("mean", 0.0) / 1000.0
        med_lat_s = latency.get("median", 0.0) / 1000.0
        p95_lat_s = latency.get("p95", 0.0) / 1000.0

        tot_cost = fin.get("total_cost_usd", 0.0)
        cost_per_req = fin.get("cost_per_logical_request_usd", 0.0)

        slots["table_5"][c] = {
            "condition": c,
            "total_input_tokens": f"{sum_prompt_tok:,}",
            "total_output_tokens": f"{sum_comp_tok:,}",
            "mean_output_tokens_req": f"{mean_comp_tok:.1f}",
            "mean_latency_s": f"{mean_lat_s:.2f}s",
            "median_latency_s": f"{med_lat_s:.2f}s",
            "p95_latency_s": f"{p95_lat_s:.2f}s",
            "total_cost_usd": f"USD {tot_cost:.2f}",
            "mean_cost_query_usd": f"USD {cost_per_req:.6f}",
        }

    return slots


def populate_report_text(template_text: str, slots: dict[str, Any], fixture_dir: Path) -> str:
    """Populate markdown template text with formatted slot values and private labels."""
    lines = template_text.splitlines()
    new_lines: list[str] = []

    # Table regex matchers for rows
    t2a_row_pat = re.compile(r"^\|\s*`([a-z0-9_]+)`\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|.*")
    t2b_row_pat = re.compile(r"^\|\s*`([a-z0-9_]+)`\s*\|\s*(\d+)\s*\|.*")
    t3_row_pat = re.compile(r"^\|\s*`([a-z0-9_]+)`\s*\|.*")
    t4_row_pat = re.compile(r"^\|\s*`([a-z0-9_]+)`\s*\|.*")
    t5_row_pat = re.compile(r"^\|\s*`([a-z0-9_]+)`\s*\|.*")

    in_table: str | None = None

    for line in lines:
        stripped = line.strip()

        # Track which table we are currently scanning
        if "*Table 2a:" in stripped:
            in_table = "table_2a"
            new_lines.append(line)
            continue
        elif "*Table 2b:" in stripped:
            in_table = "table_2b"
            new_lines.append(line)
            continue
        elif "*Table 3:" in stripped:
            in_table = "table_3"
            new_lines.append(line)
            continue
        elif "*Table 4:" in stripped:
            in_table = "table_4"
            new_lines.append(line)
            continue
        elif "*Table 5:" in stripped:
            in_table = "table_5"
            new_lines.append(line)
            continue
        elif stripped.startswith("### ") or (
            stripped.startswith("## ") and not stripped.startswith("## 6.")
        ):
            in_table = None

        # Row replacement logic
        if in_table == "table_2a" and stripped.startswith("| `"):
            m = t2a_row_pat.match(stripped)
            if m:
                c = m.group(1)
                k = m.group(2)
                n = m.group(3)
                if c in slots["table_2a"]:
                    s = slots["table_2a"][c]
                    new_line = (
                        f"| `{c}` | {k} | {n} | {s['accuracy_end_to_end']} | "
                        f"{s['accuracy_valid_outputs']} | {s['macro_f1']} |"
                    )
                    new_lines.append(new_line)
                    continue

        elif in_table == "table_2b" and stripped.startswith("| `"):
            m = t2b_row_pat.match(stripped)
            if m:
                c = m.group(1)
                n = m.group(2)
                if c in slots["table_2b"]:
                    s = slots["table_2b"][c]
                    new_line = (
                        f"| `{c}` | {n} | {s['completed_outputs']} | "
                        f"{s['parse_failures']} | {s['invalid_ids']} | {s['invalid_id_rate']} |"
                    )
                    new_lines.append(new_line)
                    continue

        elif in_table == "table_3" and stripped.startswith("| `"):
            m = t3_row_pat.match(stripped)
            if m:
                c = m.group(1)
                if c in slots["table_3"]:
                    s = slots["table_3"][c]
                    new_line = (
                        f"| `{c}` | {s['single_acc']} | {s['context_acc']} | "
                        f"{s['single_macro_f1']} | {s['context_macro_f1']} | {s['delta_acc']} |"
                    )
                    new_lines.append(new_line)
                    continue

        elif in_table == "table_4" and stripped.startswith("| `"):
            m = t4_row_pat.match(stripped)
            if m:
                c = m.group(1)
                if c in slots["table_4"]:
                    s = slots["table_4"][c]
                    new_line = (
                        f"| `{c}` | {s['total_errors']} | {s['retrieval_miss']} | "
                        f"{s['downstream_selection_failure']} | {s['parametric_recovery']} | "
                        f"{s['invalid_attack_id']} | {s['parse_failure']} | "
                        f"{s['provider_failure']} |"
                    )
                    new_lines.append(new_line)
                    continue

        elif in_table == "table_5" and stripped.startswith("| `"):
            m = t5_row_pat.match(stripped)
            if m:
                c = m.group(1)
                if c in slots["table_5"]:
                    s = slots["table_5"][c]
                    new_line = (
                        f"| `{c}` | {s['total_input_tokens']} | {s['total_output_tokens']} | "
                        f"{s['mean_output_tokens_req']} | {s['mean_latency_s']} | "
                        f"{s['median_latency_s']} | {s['p95_latency_s']} | "
                        f"{s['total_cost_usd']} | {s['mean_cost_query_usd']} |"
                    )
                    new_lines.append(new_line)
                    continue

        new_lines.append(line)

    populated = "\n".join(new_lines)

    # Append Supplementary Execution Provenance table before References (### 8.3)
    # or after Table 6
    supp_marker = "#### Supplementary Execution Provenance (Diagnostic Fixture Mode)"
    if supp_marker not in populated and "### 8.3" in populated:
        fixture_files = [
            ("Diagnostic Overall Metrics", fixture_dir / "overall_metrics.json"),
            (
                "Diagnostic Condition Metrics",
                fixture_dir / "per_condition_metrics.json",
            ),
            (
                "Diagnostic Failure Decomposition",
                fixture_dir / "failure_decomposition.json",
            ),
            ("Diagnostic RQ Analysis", fixture_dir / "rq_analysis.json"),
        ]

        supp_lines = [
            "",
            supp_marker,
            (
                "The following diagnostic fixture files were consumed during this "
                "offline verification run:"
            ),
            "",
            "| Asset Description | File Path | Digest Type | SHA-256 Digest |",
            "| :--- | :--- | :--- | :--- |",
        ]
        for desc, fpath in fixture_files:
            if fpath.is_file():
                f_hash = compute_file_sha256(fpath)
                try:
                    rel_p = str(fpath.relative_to(REPO_ROOT)).replace("\\", "/")
                except ValueError:
                    rel_p = str(fpath).replace("\\", "/")
                supp_lines.append(f"| **{desc}** | `{rel_p}` | File SHA-256 | `{f_hash}` |")

        supp_lines.extend(["", ""])
        populated = populated.replace("### 8.3", "\n".join(supp_lines) + "### 8.3")

    # Add prominent private labeling warning banner at the very top
    banner = [
        "<!-- FIXTURE_ONLY: true -->",
        "> [!WARNING]",
        f"> **{DISCLAIMER_TEXT}**",
        "> This scientific report preview was populated using synthetic offline test fixtures",
        "> for pipeline verification and presentation readiness purposes only.",
        "> It contains **NO** canonical live experimental results or live model predictions.",
        "",
        "---",
        "",
    ]

    return "\n".join(banner) + populated


def run_pipeline(
    fixture_dir: Path,
    template_path: Path,
    output_path: Path,
    audit_json_path: Path | None = None,
    export_docx: bool = False,
    force_in_place: bool = False,
) -> tuple[Path, dict[str, Any]]:
    """Execute end-to-end report population against test fixtures."""
    # Safety check: prevent overwriting canonical report template unless forced
    if output_path.resolve() == DEFAULT_TEMPLATE_PATH.resolve() and not force_in_place:
        raise ValueError(
            "[SAFETY_GUARD] Refusing to overwrite canonical report template "
            f"({DEFAULT_TEMPLATE_PATH}) with fixture data! Specify a different --output "
            "path or provide --force-in-place if explicitly testing template replacement."
        )

    # 1. Load and validate fixture data
    data = load_fixture_data(fixture_dir)

    # 2. Extract and format slots
    slots = extract_slots(data)

    # 3. Read template
    template_text = template_path.read_text(encoding="utf-8")

    # 4. Populate report markdown
    populated_text = populate_report_text(template_text, slots, fixture_dir)

    # 5. Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(populated_text, encoding="utf-8")
    print(f"[OK] Wrote populated fixture report to: {output_path}")

    # 6. Write audit JSON if requested
    if audit_json_path:
        audit_json_path.parent.mkdir(parents=True, exist_ok=True)
        audit_json_path.write_text(
            json.dumps(slots, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"[OK] Wrote audit slots JSON to: {audit_json_path}")

    # 7. Optional DOCX compilation
    if export_docx:
        from scripts.export_report_docx import (
            build_docx_from_markdown,
        )

        docx_path = output_path.with_suffix(".docx")
        build_docx_from_markdown(output_path, docx_path)
        print(f"[OK] Exported Word document to: {docx_path}")

    return output_path, slots


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Populate scientific report tables from offline test fixtures (fixture_only: true)."
        )
    )
    parser.add_argument(
        "--fixture-dir",
        type=Path,
        default=DEFAULT_FIXTURE_DIR,
        help="Path to directory containing mock fixture evaluation outputs.",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=DEFAULT_TEMPLATE_PATH,
        help="Path to scientific report markdown template.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_MD,
        help="Path to write populated markdown output.",
    )
    parser.add_argument(
        "--audit-json",
        type=Path,
        default=DEFAULT_AUDIT_JSON,
        help="Path to write populated slots audit JSON.",
    )
    parser.add_argument(
        "--export-docx",
        action="store_true",
        help="Also export populated markdown to Word (.docx).",
    )
    parser.add_argument(
        "--force-in-place",
        action="store_true",
        help="Allow overwriting template file in place (USE WITH CAUTION).",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()

    # Determine active fixture dir
    target_fixture_dir = args.fixture_dir
    if not target_fixture_dir.is_dir() and FALLBACK_FIXTURE_DIR.is_dir():
        print(
            f"[INFO] Default fixture dir not found at {target_fixture_dir}, "
            f"falling back to {FALLBACK_FIXTURE_DIR}"
        )
        target_fixture_dir = FALLBACK_FIXTURE_DIR

    try:
        run_pipeline(
            fixture_dir=target_fixture_dir,
            template_path=args.template,
            output_path=args.output,
            audit_json_path=args.audit_json,
            export_docx=args.export_docx,
            force_in_place=args.force_in_place,
        )
    except Exception as exc:
        print(f"[ERROR] Population failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
