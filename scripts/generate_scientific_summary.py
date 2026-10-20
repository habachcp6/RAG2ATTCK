"""Extract programmatically generated scientific summary table from canonical_metric_bundle_v2.json."""

from __future__ import annotations

import json
from pathlib import Path


def generate_scientific_summary(bundle_path: Path) -> dict[str, any]:
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    conds = bundle["conditions"]
    cohort = bundle["cohort_breakdown"]

    summary_rows = []
    condition_names = ["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]

    for name in condition_names:
        c = conds[name]
        rq1 = c["rq1_attribution"]
        delta_info = rq1.get("delta_vs_baseline")

        if delta_info is not None:
            mcnemar = delta_info.get("mcnemar_test", {})
            mcnemar_p = mcnemar.get("p_value_exact")
            p_str = mcnemar.get(
                "display_p_exact", f"{mcnemar_p:.3f}" if mcnemar_p is not None else "N/A"
            )
            delta_ci = delta_info.get("delta_accuracy_ci_95_display_pp", "N/A")
            delta_acc_pp = delta_info.get("delta_accuracy_display_pp", "N/A")
            rel_gain_acc = delta_info.get("relative_gain_accuracy_pct")
            rel_gain_f1 = delta_info.get("relative_gain_macro_f1_pct")
            contingency = mcnemar.get("contingency_table", {})
        else:
            mcnemar_p = None
            p_str = "N/A (baseline)"
            delta_ci = "N/A (baseline)"
            delta_acc_pp = "0.000 pp (baseline)"
            rel_gain_acc = 0.0
            rel_gain_f1 = 0.0
            contingency = {}

        row = {
            "condition": name,
            "retrieval_k": c.get("retrieval_k", 0),
            "accuracy_display": rq1["accuracy_display"],
            "accuracy_e2e": rq1["accuracy_end_to_end"],
            "ci_95_display": rq1["accuracy_e2e_ci_95_display"],
            "ci_95": rq1["accuracy_e2e_ci_95"],
            "correct_count": rq1["correct_count"],
            "scorable_count": rq1["scorable_sample_count"],
            "correct_ratio": f"{rq1['correct_count']} / {rq1['scorable_sample_count']}",
            "macro_f1_display": rq1["macro_f1_display"],
            "macro_f1": rq1["macro_f1"],
            "delta_accuracy_display_pp": delta_acc_pp,
            "delta_ci_95_display_pp": delta_ci,
            "mcnemar_exact_p": mcnemar_p,
            "mcnemar_p_display": p_str,
            "relative_gain_accuracy_pct": rel_gain_acc,
            "relative_gain_macro_f1_pct": rel_gain_f1,
            "contingency_table": contingency,
        }
        summary_rows.append(row)

    md_table = [
        "| Condition | Retrieval k | Accuracy (95% CI) | Correct / Total | Macro F1 | Delta vs No-RAG (95% CI) | McNemar Exact p |",
        "| :--- | :---: | :--- | :---: | :---: | :--- | :---: |",
    ]
    for r in summary_rows:
        md_table.append(
            f"| `{r['condition']}` | {r['retrieval_k']} | **{r['accuracy_display']}** {r['ci_95_display']} | "
            f"{r['correct_ratio']} | {r['macro_f1_display']} | {r['delta_ci_95_display_pp']} | {r['mcnemar_p_display']} |"
        )

    return {
        "cohort": cohort,
        "candidate_base_git_sha": bundle.get("candidate_base_git_sha"),
        "bundle_build_timestamp_utc": bundle.get("bundle_build_timestamp_utc"),
        "rows": summary_rows,
        "markdown_table": "\n".join(md_table),
    }


if __name__ == "__main__":
    repo_root = Path(__file__).resolve().parents[1]
    bundle_file = repo_root / "artifacts/results/canonical_metric_bundle_v2.json"
    result = generate_scientific_summary(bundle_file)
    print("PROGRAMMATIC SCIENTIFIC SUMMARY (canonical_metric_bundle_v2.json):")
    print(result["markdown_table"])

    out_json = repo_root / "reports/evidence/r8_scientific_summary.json"
    out_json.write_text(json.dumps(result, indent=2), encoding="utf-8")
    out_md = repo_root / "reports/evidence/r8_scientific_summary.md"
    out_md.write_text(result["markdown_table"] + "\n", encoding="utf-8")
    print(f"\nWritten to {out_json} and {out_md}")
