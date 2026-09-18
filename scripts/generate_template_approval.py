"""Generate the human semantic-review package from the authoritative registry."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "synthetic_templates.json"
OUTPUT = ROOT / "docs" / "synthetic" / "template_families_approval.md"
sys.path.insert(0, str(ROOT))


def compact(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(", ", ": "))


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_lines(family: dict[str, Any]) -> list[str]:
    anchor = family["anchor"]
    contexts = family.get("contextual_event_specs", [])
    event_specs = [anchor, *contexts]
    lines = [
        f"- Anchor telemetry: `{anchor['provider']}` / `{anchor['channel']}` / EID `{anchor['windows_event_id']}`",
        f"- Context telemetry: " + "; ".join(
            f"`{item['event_key']}` = `{item['provider']}` / `{item['channel']}` / EID `{item['windows_event_id']}`"
            for item in contexts
        ),
        f"- Anchor selection rule: {anchor['selection_rule']}",
        "- Windows documentation: " + "; ".join(
            f"EID {', '.join(str(event_id) for event_id in item.get('event_ids', []))} [{item.get('reference', 'missing')}]"
            for item in family.get("windows_telemetry_source", [])
        ),
        f"- Telemetry combinations covered: `{len(event_specs)}` registry event specifications",
    ]
    return lines


def gt_block(title: str, gt: dict[str, Any]) -> list[str]:
    return [
        f"### {title}",
        f"- Status: `{gt['status']}`",
        f"- Technique(s): " + (", ".join(f"`{tid}` ({name})" for tid, name in zip(gt.get("technique_ids", []), gt.get("technique_names", []))) or "none"),
        "- Evidence predicate:",
        "```json",
        json.dumps(gt["evidence_predicate"], ensure_ascii=False, indent=2),
        "```",
        f"- Rationale: {gt['rationale']}",
    ]


def main() -> int:
    registry_bytes = REGISTRY.read_bytes()
    registry = json.loads(registry_bytes.decode("utf-8"))
    families = registry["families"]
    digest = hashlib.sha256(registry_bytes).hexdigest()
    counts = Counter((family["split"], family["category"]) for family in families)
    planned = Counter((family["split"], family["category"]) for family in families for _ in range(family["planned_instances"]))

    lines = [
        "# RAG2ATTCK Synthetic Benchmark — Semantic Template Registry Approval",
        "",
        "This package is generated from `config/synthetic_templates.json`. It is a human semantic-review artifact for Stage A. Stage B generation and final dataset freezing are intentionally not performed.",
        "",
        f"- Registry SHA-256: `{digest}`",
        f"- Total families: `{len(families)}` (`test={sum(v for (s, _), v in counts.items() if s == 'test')}`, `dev={sum(v for (s, _), v in counts.items() if s == 'dev')}`)",
        f"- Planned pairs: `{sum(family['planned_instances'] for family in families)}`",
        "- ATT&CK catalog: pinned Enterprise v19.2; names are checked against the local STIX snapshot.",
        "- Attribution policy: evidence-conditioned closed-world; absence of evidence is ambiguous, not unmapped.",
        "",
        "## Planned quota summary",
        "",
        "| Split | Category | Families | Planned pairs |",
        "|---|---|---:|---:|",
    ]
    for split in ("test", "dev"):
        for category in ("mapped_single", "mapped_multi", "unmapped", "ambiguous"):
            lines.append(f"| {split} | {category} | {counts[(split, category)]} | {planned[(split, category)]} |")
    lines += [
        "",
        "## Canonical telemetry schema",
        "",
        "- `Microsoft-Windows-Security-Auditing` / `Security`: EID 4688, 4697, 4698, 4720.",
        "- `Microsoft-Windows-Eventlog` / `Security`: EID 1102.",
        "- `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational`: EID 1, 3, 11, 13.",
        "- EID 4697 is the Security service-install event; EID 7045 is not used.",
        "- EID 1102 is an audit-log-cleared outcome and is not mechanism evidence by itself.",
        "",
        "## Relation DSL signatures",
        "",
        "- `same_host`, `same_user`, `same_logon`, `same_process`, `same_process_guid`: `events` list.",
        "- `temporal_before`: `before`, `after` event keys.",
        "- `process_then_file`: `process`, `file`; `process_then_network`: `process`, `network`.",
        "- `process_then_registry`: `process`, `registry`; `process_then_task`: `process`, `task`; `process_then_service`: `process`, `service`.",
        "- `network_then_file`: `network`, `file`; operands are checked against the canonical event classes.",
        "- Approved Stage B corrections: `task_then_process`, `service_then_process`, `registry_then_process`, `file_then_process` distinguish activation from registration; `parent_network_before_child` links a parent network event to a subsequently created child.",
        "- Ordered relations require strictly increasing timestamps; process identity and resource correlations are specified in `docs/synthetic/relation_contract.md`.",
        "",
        "## Family-by-family semantic review",
        "",
    ]

    for family in families:
        lines += [
            f"## `{family['template_family_id']}`",
            "",
            f"- Split: `{family['split']}`",
            f"- Category: `{family['category']}`",
            f"- Behavior description: {family['behavior_description']}",
            *source_lines(family),
        ]
        lines += gt_block("Single-view ground truth", family["single_ground_truth"])
        lines += gt_block("Contextual ground truth", family["contextual_ground_truth"])
        lines += [
            f"- Expected transition: `{family['expected_transition']}`",
            f"- Contextual event descriptions: {compact(family['contextual_event_descriptions'])}",
            f"- Counter-evidence: {family['counter_evidence']}",
            f"- Benign near-miss: {family['benign_near_miss']}",
            f"- Allowed variations: {compact(family['allowed_variations'])}",
            f"- Disallowed variations: {compact(family['disallowed_variations'])}",
            "- ATT&CK source:",
            "```json",
            json.dumps(family["attack_source"], ensure_ascii=False, indent=2),
            "```",
            f"- Planned instances: `{family['planned_instances']}`",
        ]
        if "host_constraints" in family:
            lines += [
                "- Host constraints:",
                "```json",
                json.dumps(family["host_constraints"], ensure_ascii=False, indent=2),
                "```",
            ]
        lines.append("")

    OUTPUT.write_bytes(("\n".join(lines).rstrip() + "\n").encode("utf-8"))
    print(f"wrote {OUTPUT}")
    print(f"registry_sha256={digest}")
    print(f"approval_sha256={hash_file(OUTPUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
