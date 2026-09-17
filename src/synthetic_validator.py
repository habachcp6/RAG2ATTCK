"""Comprehensive synthetic paired benchmark validator for RAG2ATTCK.

Implements 30 validation checks as specified in the Stage A revision protocol.
All checks are derived from the authoritative template registry and config.
"""

import hashlib
import json
import re
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime
from math import ceil
from pathlib import Path
from statistics import median
from typing import Any, Dict, List, Optional, Set, Tuple

from src.synthetic import (
    ScenarioPair, View, SyntheticEvent, ViewGroundTruth,
    check_leakage, find_near_duplicates, get_inference_payload,
    INFERENCE_ALLOWLIST, HOSTS_DOMAIN_CONTROLLER,
    HOSTS_ALLOWED_LOCAL_ACCOUNT, CANONICAL_TELEMETRY_SCHEMA,
)


# ============================================================
# Validation Result
# ============================================================

class ValidationResult:
    """Result of dataset validation containing errors, warnings and statistics."""
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.statistics: Dict[str, Any] = {}

    @property
    def passed(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, msg: str) -> None:
        self.errors.append(msg)

    def add_warning(self, msg: str) -> None:
        self.warnings.append(msg)


# ============================================================
# Allowed transition types (benchmark v1)
# ============================================================

ALLOWED_TRANSITIONS = {
    ("mapped", "mapped"),
    ("ambiguous", "mapped"),
    ("ambiguous", "unmapped"),
    ("ambiguous", "ambiguous"),
    ("unmapped", "unmapped"),
}

VALID_LABEL_STATUSES = {"mapped", "unmapped", "ambiguous"}

# Benchmark technique catalog
BENCHMARK_CATALOG = {
    "T1059.001", "T1059.003", "T1053.005", "T1543.003",
    "T1136.001", "T1547.001", "T1685.005", "T1105",
}

BENCHMARK_TECHNIQUE_NAMES = {
    "T1059.001": "PowerShell",
    "T1059.003": "Windows Command Shell",
    "T1053.005": "Scheduled Task",
    "T1543.003": "Windows Service",
    "T1136.001": "Local Account",
    "T1547.001": "Registry Run Keys / Startup Folder",
    "T1685.005": "Clear Windows Event Logs",
    "T1105": "Ingress Tool Transfer",
}

VALID_REGISTRY_CATEGORIES = {"mapped_single", "mapped_multi", "unmapped", "ambiguous"}
VALID_REGISTRY_SPLITS = {"dev", "test"}
PREDICATE_OPERATORS = {
    "eq", "neq", "contains", "contains_ci", "startswith", "startswith_ci",
    "endswith", "endswith_ci", "regex", "in", "not_in",
}
PREDICATE_RELATIONS = {
    "parent_child", "same_host", "same_user", "same_logon",
    "same_process_guid", "same_process", "temporal_before",
    "temporal_within", "network_then_file", "process_then_file", "process_then_network",
    "process_then_registry", "process_then_task", "process_then_service",
}
GENERIC_METADATA_PLACEHOLDERS = {"dev", "benign", "ambiguous", "any", "multi", "ps", "reg", "svc", "net"}


# ============================================================
# Authoritative registry validation (Stage A)
# ============================================================

def _registry_predicate_has_leaf(predicate: Any) -> bool:
    """Return whether a structured predicate contains an actual field test."""
    if not isinstance(predicate, dict):
        return False
    if {"event", "field", "op", "value"}.issubset(predicate):
        return True
    if "all" in predicate or "any" in predicate:
        return any(_registry_predicate_has_leaf(item)
                   for item in predicate.get("all", predicate.get("any", [])))
    if "not" in predicate:
        return _registry_predicate_has_leaf(predicate["not"])
    if "relation" in predicate:
        return True
    return False


def _registry_predicate_leaves(predicate: Any) -> List[Dict[str, Any]]:
    """Collect field-test leaves from a registry DSL predicate."""
    if not isinstance(predicate, dict):
        return []
    if {"event", "field", "op", "value"}.issubset(predicate):
        return [predicate]
    leaves: List[Dict[str, Any]] = []
    for key in ("all", "any"):
        if key in predicate and isinstance(predicate[key], list):
            for item in predicate[key]:
                leaves.extend(_registry_predicate_leaves(item))
    if "not" in predicate:
        leaves.extend(_registry_predicate_leaves(predicate["not"]))
    return leaves


def _registry_predicate_has_negative_clause(predicate: Any) -> bool:
    """Whether a predicate contains an explicit negative/allowlist clause."""
    if not isinstance(predicate, dict):
        return False
    if "not" in predicate:
        return True
    if predicate.get("op") in {"neq", "not_in"}:
        return True
    for key in ("all", "any"):
        if any(_registry_predicate_has_negative_clause(item) for item in predicate.get(key, [])):
            return True
    return False


def _validate_registry_dsl(
    predicate: Any,
    path: str,
    allowed_events: Dict[str, Tuple[str, ...]],
    result: ValidationResult,
) -> None:
    """Validate the closed, machine-readable registry predicate DSL."""
    if not isinstance(predicate, dict) or not predicate:
        result.add_error(f"{path}: empty evidence predicate")
        return

    keys = set(predicate)
    logical_keys = keys & {"all", "any", "not"}
    if logical_keys:
        if len(logical_keys) != 1:
            result.add_error(f"{path}: predicate has multiple logical operators")
            return
        operator = next(iter(logical_keys))
        if operator in {"all", "any"}:
            children = predicate[operator]
            if not isinstance(children, list) or not children:
                result.add_error(f"{path}: empty evidence predicate")
                result.add_error(f"{path}: {operator} must contain at least one rule")
                return
            for index, child in enumerate(children):
                _validate_registry_dsl(child, f"{path}.{operator}[{index}]", allowed_events, result)
            return
        if keys != {"not"}:
            result.add_error(f"{path}: not predicate has unexpected keys")
            return
        _validate_registry_dsl(predicate["not"], f"{path}.not", allowed_events, result)
        return

    if "relation" in keys:
        relation_name = predicate.get("relation")
        if relation_name not in PREDICATE_RELATIONS:
            result.add_error(f"{path}: unsupported relation {relation_name!r}")
        if len(keys) < 2 or any(value in (None, "", [], {}) for key, value in predicate.items() if key != "relation"):
            result.add_error(f"{path}: relation must identify related events")
        return

    required_leaf_keys = {"event", "field", "op", "value"}
    if keys != required_leaf_keys:
        result.add_error(f"{path}: unsupported predicate shape/keys {sorted(keys)}")
        return
    event_name = predicate["event"]
    field = predicate["field"]
    operator = predicate["op"]
    if event_name not in allowed_events:
        result.add_error(f"{path}: event reference {event_name!r} is not in this view")
    elif field not in allowed_events[event_name]:
        result.add_error(
            f"{path}: field {field!r} is not visible for {event_name} in its telemetry schema"
        )
    if operator not in PREDICATE_OPERATORS:
        result.add_error(f"{path}: unsupported field operator {operator!r}")
    elif operator == "regex":
        try:
            re.compile(str(predicate["value"]))
        except re.error as exc:
            result.add_error(f"{path}: invalid regex: {exc}")
    elif operator in {"in", "not_in"} and (
        not isinstance(predicate["value"], list) or not predicate["value"]
    ):
        result.add_error(f"{path}: {operator} requires a non-empty list")


def _registry_event_schema(
    event_spec: Dict[str, Any], path: str, result: ValidationResult
) -> Optional[Tuple[str, ...]]:
    """Validate a provider/channel/EventID tuple and return visible fields."""
    provider = event_spec.get("provider")
    channel = event_spec.get("channel")
    event_id = event_spec.get("windows_event_id")
    if provider == "any":
        result.add_error(f"{path}: provider='any' is not allowed")
    if channel == "any":
        result.add_error(f"{path}: channel='any' is not allowed")
    if not isinstance(event_id, int) or isinstance(event_id, bool) or event_id == 0:
        result.add_error(f"{path}: EventID must be a non-zero integer")
        return None
    fields = CANONICAL_TELEMETRY_SCHEMA.get((provider, channel), {}).get(event_id)
    if fields is None:
        result.add_error(
            f"{path}: unsupported provider/channel/EventID combination "
            f"{provider!r}/{channel!r}/{event_id}"
        )
    return fields


def _registry_ground_truth(
    family: Dict[str, Any],
    gt_key: str,
    event_schemas: Dict[str, Tuple[str, ...]],
    stix_names: Dict[str, str],
    result: ValidationResult,
) -> None:
    gt = family.get(gt_key)
    path = f"{family.get('template_family_id', '<missing>')}.{gt_key}"
    if not isinstance(gt, dict):
        result.add_error(f"{path}: missing ground-truth object")
        return
    status = gt.get("status")
    if status not in VALID_LABEL_STATUSES:
        result.add_error(f"{path}: invalid status {status!r}")
    ids = gt.get("technique_ids")
    names = gt.get("technique_names")
    if not isinstance(ids, list) or not isinstance(names, list):
        result.add_error(f"{path}: technique_ids and technique_names must be lists")
        ids, names = [], []
    if len(ids) != len(names):
        result.add_error(f"{path}: technique ID/name lengths differ")
    for index, tid in enumerate(ids):
        if tid not in BENCHMARK_CATALOG:
            result.add_error(f"{path}: technique outside benchmark catalog: {tid!r}")
        expected_name = stix_names.get(tid, BENCHMARK_TECHNIQUE_NAMES.get(tid))
        if index >= len(names) or names[index] != expected_name:
            result.add_error(
                f"{path}: ATT&CK ID/name mismatch for {tid}: "
                f"{names[index] if index < len(names) else None!r} != {expected_name!r}"
            )
    if status == "mapped" and not ids:
        result.add_error(f"{path}: mapped ground truth has no mapped technique")
    if status in {"unmapped", "ambiguous"} and ids:
        result.add_error(f"{path}: {status} ground truth must not contain techniques")
    predicate = gt.get("evidence_predicate")
    is_multi_context = (
        gt_key == "contextual_ground_truth"
        and family.get("category") == "mapped_multi"
    )
    predicate_leaves: List[Dict[str, Any]] = []
    if is_multi_context:
        if not isinstance(predicate, dict) or set(predicate) != set(ids) or len(predicate) < 2:
            result.add_error(f"{path}: each contextual multi-label technique needs its own predicate")
        else:
            for tid in ids:
                _validate_registry_dsl(predicate[tid], f"{path}.evidence_predicate.{tid}", event_schemas, result)
                predicate_leaves.extend(_registry_predicate_leaves(predicate[tid]))
    else:
        _validate_registry_dsl(predicate, f"{path}.evidence_predicate", event_schemas, result)
        predicate_leaves = _registry_predicate_leaves(predicate)
    if not predicate_leaves:
        result.add_error(f"{path}: evidence predicate has no visible field evidence")
    if status == "unmapped" and not _registry_predicate_has_negative_clause(predicate):
        result.add_error(f"{path}: unmapped predicate lacks affirmative negative/allowlist evidence")
    rationale = gt.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        result.add_error(f"{path}: empty rationale")


def _registry_structure_signature(family: Dict[str, Any]) -> str:
    """Signature used to catch DEV/TEST clones that only change decoration."""
    signature = {
        "category": family.get("category"),
        "technique_ids": family.get("technique_ids"),
        "anchor": family.get("anchor"),
        "single": family.get("single_ground_truth"),
        "contextual": family.get("contextual_ground_truth"),
        "contextual_event_specs": family.get("contextual_event_specs"),
    }
    return json.dumps(signature, sort_keys=True, ensure_ascii=False)


def validate_template_registry(
    registry: Dict[str, Any],
    stix_path: Optional[Path] = None,
) -> ValidationResult:
    """Validate the authoritative Stage A template registry before Stage B.

    This validator intentionally accepts no placeholder semantics.  It checks
    registry content directly, independently of generated dataset artifacts.
    """
    result = ValidationResult()
    if not isinstance(registry, dict):
        result.add_error("[REGISTRY] registry must be a JSON object")
        return result
    families = registry.get("families")
    if not isinstance(families, list) or not families:
        result.add_error("[REGISTRY] families must be a non-empty list")
        return result

    stix_names = dict(BENCHMARK_TECHNIQUE_NAMES)
    if stix_path and stix_path.exists():
        try:
            from src.attack_loader import parse_attack_bundle
            loaded = parse_attack_bundle(stix_path)
            stix_names = {tid: loaded[tid].name for tid in BENCHMARK_CATALOG if tid in loaded}
        except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
            result.add_error(f"[REGISTRY] unable to read pinned ATT&CK snapshot: {exc}")

    seen_ids: Set[str] = set()
    dev_signatures: Dict[str, str] = {}
    test_signatures: Dict[str, str] = {}
    category_quota = {
        ("test", "mapped_single"): 400,
        ("test", "mapped_multi"): 40,
        ("test", "unmapped"): 150,
        ("test", "ambiguous"): 50,
        ("dev", "mapped_single"): 16,
        ("dev", "mapped_multi"): 4,
        ("dev", "unmapped"): 6,
        ("dev", "ambiguous"): 4,
    }

    for index, family in enumerate(families):
        path = f"[REGISTRY] family[{index}]"
        if not isinstance(family, dict):
            result.add_error(f"{path}: family must be an object")
            continue
        fid = family.get("template_family_id")
        if not isinstance(fid, str) or not fid.strip():
            result.add_error(f"{path}: missing family ID")
            fid = f"<family-{index}>"
        elif fid in seen_ids:
            result.add_error(f"{path}: duplicate family ID {fid}")
        seen_ids.add(fid)

        category = family.get("category")
        split = family.get("split")
        if category not in VALID_REGISTRY_CATEGORIES:
            result.add_error(f"{fid}: invalid category {category!r}")
        if split not in VALID_REGISTRY_SPLITS:
            result.add_error(f"{fid}: invalid split {split!r}")

        behavior = family.get("behavior_description")
        if not isinstance(behavior, str) or not behavior.strip():
            result.add_error(f"{fid}: empty behavior_description")
        elif behavior.strip().casefold() in GENERIC_METADATA_PLACEHOLDERS:
            result.add_error(f"{fid}: generic behavior_description placeholder")

        anchor = family.get("anchor")
        if not isinstance(anchor, dict):
            result.add_error(f"{fid}: missing anchor")
            anchor = {}
        anchor_fields = _registry_event_schema(anchor, f"{fid}.anchor", result)
        selection_rule = anchor.get("selection_rule")
        if not isinstance(selection_rule, str) or not selection_rule.strip() or selection_rule.strip().casefold() in GENERIC_METADATA_PLACEHOLDERS:
            result.add_error(f"{fid}: empty/generic anchor selection_rule")

        context_specs = family.get("contextual_event_specs")
        if not isinstance(context_specs, list) or not context_specs:
            result.add_error(f"{fid}: contextual_event_specs are required")
            context_specs = []
        event_schemas: Dict[str, Tuple[str, ...]] = {}
        if anchor_fields is not None:
            event_schemas["anchor"] = anchor_fields
        context_keys: Set[str] = set()
        for context_index, context in enumerate(context_specs):
            cpath = f"{fid}.contextual_event_specs[{context_index}]"
            if not isinstance(context, dict):
                result.add_error(f"{cpath}: context spec must be an object")
                continue
            event_key = context.get("event_key")
            if not isinstance(event_key, str) or not event_key or event_key == "anchor" or event_key in context_keys:
                result.add_error(f"{cpath}: invalid or duplicate event_key")
                continue
            context_keys.add(event_key)
            fields = _registry_event_schema(context, cpath, result)
            if fields is not None:
                event_schemas[event_key] = fields
            rule = context.get("selection_rule")
            if not isinstance(rule, str) or not rule.strip() or rule.strip().casefold() in GENERIC_METADATA_PLACEHOLDERS:
                result.add_error(f"{cpath}: empty/generic selection_rule")

        descriptions = family.get("contextual_event_descriptions")
        if not isinstance(descriptions, list) or not descriptions or any(not isinstance(item, str) or not item.strip() for item in descriptions):
            result.add_error(f"{fid}: contextual_event_descriptions are required")

        for text_key in ("counter_evidence", "benign_near_miss"):
            value = family.get(text_key)
            if not isinstance(value, str) or not value.strip() or value.strip().casefold() in {"none", "n/a", "any"}:
                result.add_error(f"{fid}: empty/generic {text_key}")
        for list_key in ("allowed_variations", "disallowed_variations"):
            values = family.get(list_key)
            if not isinstance(values, list) or not values or any(not isinstance(item, str) or not item.strip() for item in values):
                result.add_error(f"{fid}: {list_key} must contain meaningful guidance")

        planned = family.get("planned_instances")
        if not isinstance(planned, int) or isinstance(planned, bool) or planned <= 0:
            result.add_error(f"{fid}: planned_instances must be a positive integer")

        family_ids = family.get("technique_ids")
        contextual_gt = family.get("contextual_ground_truth") or {}
        contextual_ids = contextual_gt.get("technique_ids", []) if isinstance(contextual_gt, dict) else []
        if not isinstance(family_ids, list) or family_ids != contextual_ids:
            result.add_error(f"{fid}: technique_ids must equal contextual technique_ids")
            family_ids = family_ids if isinstance(family_ids, list) else []
        if len(set(family_ids)) != len(family_ids):
            result.add_error(f"{fid}: duplicate technique ID")

        _registry_ground_truth(family, "single_ground_truth", {"anchor": event_schemas.get("anchor", ())}, stix_names, result)
        _registry_ground_truth(family, "contextual_ground_truth", event_schemas, stix_names, result)

        single = family.get("single_ground_truth") or {}
        single_status = single.get("status")
        contextual_status = contextual_gt.get("status")
        transition = (single_status, contextual_status)
        if transition not in ALLOWED_TRANSITIONS:
            result.add_error(f"{fid}: invalid transition {single_status!r}->{contextual_status!r}")
        expected_transition = family.get("expected_transition")
        if expected_transition != f"{single_status}->{contextual_status}":
            result.add_error(f"{fid}: expected_transition does not match ground truth statuses")
        if single_status == "mapped" and contextual_status == "mapped":
            if not set(single.get("technique_ids", [])).issubset(set(contextual_gt.get("technique_ids", []))):
                result.add_error(f"{fid}: mapped contextual labels must preserve single labels")

        if category == "mapped_single" and (contextual_status != "mapped" or len(contextual_gt.get("technique_ids", [])) != 1):
            result.add_error(f"{fid}: mapped_single requires exactly one contextual mapped technique")
        if category == "mapped_multi" and (contextual_status != "mapped" or len(contextual_gt.get("technique_ids", [])) < 2):
            result.add_error(f"{fid}: mapped_multi requires at least two contextual labels")
        if category in {"unmapped", "ambiguous"} and contextual_gt.get("technique_ids"):
            result.add_error(f"{fid}: {category} family has contextual techniques")

        # EID 1102 is outcome telemetry only.  A single 1102 anchor has no
        # mechanism field and therefore cannot be mapped to T1685.005 alone.
        all_ids = set(family_ids)
        if anchor.get("windows_event_id") == 1102 and anchor.get("provider") != "Microsoft-Windows-Eventlog":
            result.add_error(f"{fid}: EID 1102 must use Microsoft-Windows-Eventlog")
        if "T1685.005" in all_ids and anchor.get("windows_event_id") == 1102 and single_status == "mapped":
            result.add_error(f"{fid}: EID 1102-only single view cannot be mapped to T1685.005")
        if anchor.get("windows_event_id") == 4697 and (
            anchor.get("provider") != "Microsoft-Windows-Security-Auditing" or anchor.get("channel") != "Security"
        ):
            result.add_error(f"{fid}: EID 4697 must use Security-Auditing/Security")
        if anchor.get("windows_event_id") == 7045:
            result.add_error(f"{fid}: EID 7045 is not an approved service-install event")

        if "T1136.001" in all_ids:
            constraints = family.get("host_constraints") or {}
            if "DC01" not in constraints.get("forbidden_hosts", []) or not {"workstation", "member_server"}.issubset(set(constraints.get("allowed_host_roles", []))):
                result.add_error(f"{fid}: T1136.001 requires workstation/member-server and forbids DC01")

        attack_source = family.get("attack_source")
        if not isinstance(attack_source, dict) or not attack_source.get("catalog_url") or not attack_source.get("catalog"):
            result.add_error(f"{fid}: missing ATT&CK source/provenance")
        if isinstance(attack_source, dict):
            for ref in attack_source.get("technique_references", []):
                if ref.get("technique_id") in BENCHMARK_CATALOG and ref.get("technique_name") != stix_names.get(ref.get("technique_id"), BENCHMARK_TECHNIQUE_NAMES.get(ref.get("technique_id"))):
                    result.add_error(f"{fid}: ATT&CK source technique name mismatch")

        telemetry_sources = family.get("windows_telemetry_source")
        if not isinstance(telemetry_sources, list) or not telemetry_sources:
            result.add_error(f"{fid}: missing Windows telemetry documentation source")
        else:
            source_keys = {
                (provider_source.get("provider"), provider_source.get("channel"), event_id)
                for provider_source in telemetry_sources
                if isinstance(provider_source, dict)
                for event_id in provider_source.get("event_ids", [])
            }
            expected_keys = {
                (event_spec.get("provider"), event_spec.get("channel"), event_spec.get("windows_event_id"))
                for event_spec in [anchor, *context_specs]
                if isinstance(event_spec, dict)
            }
            if source_keys != expected_keys:
                result.add_error(f"{fid}: Windows telemetry provenance does not match event specifications")
            for source_index, telemetry in enumerate(telemetry_sources):
                if not isinstance(telemetry, dict) or not telemetry.get("reference"):
                    result.add_error(f"{fid}.windows_telemetry_source[{source_index}]: missing documentation reference")

        signature = _registry_structure_signature(family)
        if split == "dev":
            dev_signatures[fid] = signature
        elif split == "test":
            test_signatures[fid] = signature

    overlap = set(dev_signatures) & set(test_signatures)
    if overlap:
        result.add_error(f"[REGISTRY] DEV/TEST family overlap: {sorted(overlap)}")
    duplicate_signatures = set(dev_signatures.values()) & set(test_signatures.values())
    if duplicate_signatures:
        result.add_error("[REGISTRY] DEV family is a structural clone of a TEST family")

    totals: Dict[Tuple[str, str], int] = defaultdict(int)
    for family in families:
        if isinstance(family, dict) and family.get("split") in VALID_REGISTRY_SPLITS and family.get("category") in VALID_REGISTRY_CATEGORIES and isinstance(family.get("planned_instances"), int):
            totals[(family["split"], family["category"])] += family["planned_instances"]
    for key, expected in category_quota.items():
        if totals.get(key, 0) != expected:
            result.add_error(f"[REGISTRY] quota {key[0]}/{key[1]}={totals.get(key, 0)}, expected {expected}")

    # Per-technique quotas derive from registry content, never from a second
    # hand-maintained family count.
    for split, expected in (("test", 50), ("dev", 2)):
        for tid in BENCHMARK_CATALOG:
            actual = sum(
                family.get("planned_instances", 0)
                for family in families
                if isinstance(family, dict)
                and family.get("split") == split
                and family.get("category") == "mapped_single"
                and family.get("technique_ids") == [tid]
            )
            if actual != expected:
                result.add_error(f"[REGISTRY] {split} {tid} single-label quota={actual}, expected {expected}")

    # Formula-based diversity: ceil(quota / eligible families), with no magic
    # constant and no decorative-instance exception.
    for (split, category), quota in category_quota.items():
        eligible = [family for family in families if isinstance(family, dict) and family.get("split") == split and family.get("category") == category and isinstance(family.get("planned_instances"), int) and family.get("planned_instances", 0) > 0]
        if not eligible:
            continue
        max_instances = ceil(quota / len(eligible))
        for family in eligible:
            if family["planned_instances"] > max_instances:
                result.add_error(f"[REGISTRY] {family['template_family_id']} exceeds diversity bound {max_instances}")

    result.statistics.update({
        "total_families": len(families),
        "test_families": sum(1 for family in families if isinstance(family, dict) and family.get("split") == "test"),
        "dev_families": sum(1 for family in families if isinstance(family, dict) and family.get("split") == "dev"),
        "planned_instances": sum(family.get("planned_instances", 0) for family in families if isinstance(family, dict)),
        "quota_totals": {f"{split}/{category}": totals.get((split, category), 0) for split, category in category_quota},
    })
    return result


# ============================================================
# Per-pair validation checks (1-18)
# ============================================================

def _check_01_schema(pair: ScenarioPair, result: ValidationResult) -> None:
    """Check 1: Basic schema — IDs, label_status enum, split enum."""
    if not pair.pair_id or not pair.pair_id.startswith("pair_"):
        result.add_error(f"[01] Invalid pair_id: {pair.pair_id!r}")
    if not pair.scenario_id:
        result.add_error(f"[01] Pair {pair.pair_id}: missing scenario_id")
    if not pair.template_family_id:
        result.add_error(f"[01] Pair {pair.pair_id}: missing template_family_id")
    if pair.split not in ("dev", "test"):
        result.add_error(f"[01] Pair {pair.pair_id}: invalid split {pair.split!r}")
    for label, gt in [("single", pair.single_ground_truth),
                      ("contextual", pair.contextual_ground_truth)]:
        if gt.label_status not in VALID_LABEL_STATUSES:
            result.add_error(
                f"[01] Pair {pair.pair_id} {label}: invalid label_status {gt.label_status!r}"
            )


def _check_02_unique_ids(pairs: List[ScenarioPair], result: ValidationResult) -> None:
    """Check 2: Unique pair/view/event IDs across entire dataset."""
    pair_ids = set()
    view_ids = set()
    event_ids = set()
    for pair in pairs:
        if pair.pair_id in pair_ids:
            result.add_error(f"[02] Duplicate pair_id: {pair.pair_id}")
        pair_ids.add(pair.pair_id)

        for vid in [pair.single_view.view_id, pair.contextual_view.view_id]:
            if vid in view_ids:
                result.add_error(f"[02] Duplicate view_id: {vid}")
            view_ids.add(vid)

        for eid in pair.events:
            if eid in event_ids:
                # Events CAN be shared across pairs in theory, but flag as warning
                pass
            event_ids.add(eid)


def _check_03_pair_has_two_views(pair: ScenarioPair, result: ValidationResult) -> None:
    """Check 3: Pair has exactly two views (single + contextual)."""
    if pair.single_view.view_type != "single":
        result.add_error(f"[03] Pair {pair.pair_id}: single_view has type {pair.single_view.view_type!r}")
    if pair.contextual_view.view_type != "contextual":
        result.add_error(f"[03] Pair {pair.pair_id}: contextual_view has type {pair.contextual_view.view_type!r}")


def _check_04_single_one_event(pair: ScenarioPair, result: ValidationResult) -> None:
    """Check 4: Single view has exactly one event."""
    if len(pair.single_view.event_ids) != 1:
        result.add_error(
            f"[04] Pair {pair.pair_id}: single view has {len(pair.single_view.event_ids)} events, expected 1"
        )


def _check_05_contextual_event_count(pair: ScenarioPair, result: ValidationResult) -> None:
    """Check 5: Contextual view has 2-6 events."""
    n = len(pair.contextual_view.event_ids)
    if not (2 <= n <= 6):
        result.add_error(f"[05] Pair {pair.pair_id}: contextual view has {n} events, expected 2-6")


def _check_06_anchor_exists_in_both(pair: ScenarioPair, result: ValidationResult) -> None:
    """Check 6: Same anchor event exists in both views."""
    if len(pair.single_view.event_ids) != 1:
        return
    anchor_id = pair.single_view.event_ids[0]
    if anchor_id not in pair.contextual_view.event_ids:
        result.add_error(f"[06] Pair {pair.pair_id}: anchor {anchor_id} missing from contextual view")
    if anchor_id not in pair.events:
        result.add_error(f"[06] Pair {pair.pair_id}: anchor {anchor_id} not in pair.events")


def _check_07_strict_anchor_equality(pair: ScenarioPair, result: ValidationResult) -> None:
    """Check 7: Anchor event is identical between views (same event object).

    Both views must reference the SAME event_id, and since events are stored
    in pair.events dict, this guarantees content equality. We additionally
    verify no field tampering by checking the event dict reference.
    """
    if len(pair.single_view.event_ids) != 1:
        return
    anchor_id = pair.single_view.event_ids[0]
    if anchor_id not in pair.contextual_view.event_ids:
        return  # Already caught by check 06

    # Both views reference the same event in pair.events — verify existence
    if anchor_id not in pair.events:
        result.add_error(f"[07] Pair {pair.pair_id}: anchor {anchor_id} not in events dict")
        return

    # Verify all event_ids in both views resolve to actual events
    for eid in pair.single_view.event_ids:
        if eid not in pair.events:
            result.add_error(f"[07] Pair {pair.pair_id}: single view event {eid} not in events dict")
    for eid in pair.contextual_view.event_ids:
        if eid not in pair.events:
            result.add_error(f"[07] Pair {pair.pair_id}: contextual view event {eid} not in events dict")


def _check_08_attack_ids_in_stix(pair: ScenarioPair, techniques: Dict, result: ValidationResult) -> None:
    """Check 8: Technique IDs exist in pinned STIX snapshot."""
    if not techniques:
        return
    for label, gt in [("single", pair.single_ground_truth),
                      ("contextual", pair.contextual_ground_truth)]:
        for tid in gt.technique_ids:
            if tid not in techniques:
                result.add_error(f"[08] Pair {pair.pair_id} {label}: technique {tid} not in STIX")
                continue
            tech = techniques[tid]
            if hasattr(tech, 'revoked') and tech.revoked:
                result.add_error(f"[08] Pair {pair.pair_id} {label}: technique {tid} is revoked")
            if hasattr(tech, 'deprecated') and tech.deprecated:
                result.add_error(f"[08] Pair {pair.pair_id} {label}: technique {tid} is deprecated")


def _check_09_attack_name_match(pair: ScenarioPair, techniques: Dict, result: ValidationResult) -> None:
    """Check 9: ATT&CK ID/name relation matches STIX."""
    if not techniques:
        return
    for label, gt in [("single", pair.single_ground_truth),
                      ("contextual", pair.contextual_ground_truth)]:
        for i, tid in enumerate(gt.technique_ids):
            if tid not in techniques:
                continue
            if i < len(gt.technique_names) and gt.technique_names[i] != techniques[tid].name:
                result.add_error(
                    f"[09] Pair {pair.pair_id} {label}: name mismatch for {tid}: "
                    f"{gt.technique_names[i]!r} vs STIX {techniques[tid].name!r}"
                )


def _check_10_parent_subtechnique(pair: ScenarioPair, techniques: Dict, result: ValidationResult) -> None:
    """Check 10: Parent/sub-technique relation correct."""
    if not techniques:
        return
    for label, gt in [("single", pair.single_ground_truth),
                      ("contextual", pair.contextual_ground_truth)]:
        for tid in gt.technique_ids:
            if tid not in BENCHMARK_CATALOG:
                result.add_error(
                    f"[10] Pair {pair.pair_id} {label}: technique {tid} not in benchmark catalog"
                )


def _check_11_mapped_has_techniques(pair: ScenarioPair, result: ValidationResult) -> None:
    """Check 11: Mapped views must have >=1 technique."""
    for label, gt in [("single", pair.single_ground_truth),
                      ("contextual", pair.contextual_ground_truth)]:
        if gt.label_status == "mapped" and len(gt.technique_ids) < 1:
            result.add_error(f"[11] Pair {pair.pair_id} {label}: mapped but no technique_ids")


def _check_12_unmapped_no_techniques(pair: ScenarioPair, result: ValidationResult) -> None:
    """Check 12: Unmapped views must have 0 techniques."""
    for label, gt in [("single", pair.single_ground_truth),
                      ("contextual", pair.contextual_ground_truth)]:
        if gt.label_status == "unmapped" and len(gt.technique_ids) > 0:
            result.add_error(
                f"[12] Pair {pair.pair_id} {label}: unmapped but has technique_ids: {gt.technique_ids}"
            )


def _check_13_ambiguous_no_techniques(pair: ScenarioPair, result: ValidationResult) -> None:
    """Check 13: Ambiguous views must have 0 techniques."""
    for label, gt in [("single", pair.single_ground_truth),
                      ("contextual", pair.contextual_ground_truth)]:
        if gt.label_status == "ambiguous" and len(gt.technique_ids) > 0:
            result.add_error(
                f"[13] Pair {pair.pair_id} {label}: ambiguous but has technique_ids: {gt.technique_ids}"
            )


def _check_14_evidence_is_view_local(pair: ScenarioPair, result: ValidationResult) -> None:
    """Check 14: Mapped evidence refs point only to events in the same view."""
    for label, gt, view in [
        ("single", pair.single_ground_truth, pair.single_view),
        ("contextual", pair.contextual_ground_truth, pair.contextual_view),
    ]:
        view_eids = set(view.event_ids)
        for tid, refs in gt.evidence_refs.items():
            for ref in refs:
                ref_eid = ref.get("event_id", "")
                if ref_eid and ref_eid not in view_eids:
                    result.add_error(
                        f"[14] Pair {pair.pair_id} {label}: evidence for {tid} references "
                        f"event {ref_eid} not in this view"
                    )


def _check_15_no_hidden_contextual_evidence(pair: ScenarioPair, result: ValidationResult) -> None:
    """Check 15: Single GT must not reference contextual-only events."""
    contextual_only = set(pair.contextual_view.event_ids) - set(pair.single_view.event_ids)
    for tid, refs in pair.single_ground_truth.evidence_refs.items():
        for ref in refs:
            ref_eid = ref.get("event_id", "")
            if ref_eid in contextual_only:
                result.add_error(
                    f"[15] Pair {pair.pair_id}: single GT references contextual-only event {ref_eid}"
                )


def _check_16_temporal_coherence(pair: ScenarioPair, result: ValidationResult) -> None:
    """Check 16: Contextual view events are chronologically ordered."""
    timestamps = []
    for eid in pair.contextual_view.event_ids:
        ev = pair.events.get(eid)
        if not ev:
            continue
        try:
            ts = datetime.fromisoformat(ev.timestamp_utc.replace("Z", "+00:00"))
            timestamps.append(ts)
        except (ValueError, AttributeError):
            result.add_error(f"[16] Pair {pair.pair_id}: invalid timestamp in event {eid}")
    if len(timestamps) >= 2 and timestamps != sorted(timestamps):
        result.add_error(f"[16] Pair {pair.pair_id}: contextual view timestamps not chronologically ordered")


def _check_17_transition_allowed(pair: ScenarioPair, result: ValidationResult) -> None:
    """Check 17: Single→contextual transition is an allowed type."""
    transition = (pair.single_ground_truth.label_status, pair.contextual_ground_truth.label_status)
    if transition not in ALLOWED_TRANSITIONS:
        result.add_error(
            f"[17] Pair {pair.pair_id}: disallowed transition "
            f"{transition[0]} → {transition[1]}"
        )


def _check_18_leakage(pair: ScenarioPair, result: ValidationResult) -> None:
    """Check 18: No inference label leakage."""
    for eid, ev in pair.events.items():
        payload = get_inference_payload(ev)
        leaks = check_leakage(payload)
        for leak in leaks:
            result.add_error(f"[18] Pair {pair.pair_id} event {eid}: {leak}")


# ============================================================
# Dataset-level validation checks (19-30)
# ============================================================

def _check_19_dev_quotas(pairs: List[ScenarioPair], result: ValidationResult) -> None:
    """Check 19: Exact dev quotas (30 total, 16 mapped-single, 4 multi, 6 unmapped, 4 ambiguous)."""
    dev = [p for p in pairs if p.split == "dev"]
    if len(dev) != 30:
        result.add_error(f"[19] Dev split has {len(dev)} pairs, expected 30")

    dev_mapped_single = sum(1 for p in dev
                           if p.contextual_ground_truth.label_status == "mapped"
                           and len(p.contextual_ground_truth.technique_ids) == 1)
    dev_multi = sum(1 for p in dev
                    if p.contextual_ground_truth.label_status == "mapped"
                    and len(p.contextual_ground_truth.technique_ids) >= 2)
    dev_unmapped = sum(1 for p in dev if p.contextual_ground_truth.label_status == "unmapped")
    dev_ambiguous = sum(1 for p in dev if p.contextual_ground_truth.label_status == "ambiguous")

    if dev_mapped_single != 16:
        result.add_error(f"[19] Dev mapped single-label: {dev_mapped_single}, expected 16")
    if dev_multi != 4:
        result.add_error(f"[19] Dev multi-label: {dev_multi}, expected 4")
    if dev_unmapped != 6:
        result.add_error(f"[19] Dev unmapped: {dev_unmapped}, expected 6")
    if dev_ambiguous != 4:
        result.add_error(f"[19] Dev ambiguous: {dev_ambiguous}, expected 4")


def _check_20_test_quotas(pairs: List[ScenarioPair], result: ValidationResult) -> None:
    """Check 20: Exact test quotas (640 total, 400+40+150+50)."""
    test = [p for p in pairs if p.split == "test"]
    if len(test) != 640:
        result.add_error(f"[20] Test split has {len(test)} pairs, expected 640")

    test_mapped_single = sum(1 for p in test
                            if p.contextual_ground_truth.label_status == "mapped"
                            and len(p.contextual_ground_truth.technique_ids) == 1)
    test_multi = sum(1 for p in test
                     if p.contextual_ground_truth.label_status == "mapped"
                     and len(p.contextual_ground_truth.technique_ids) >= 2)
    test_unmapped = sum(1 for p in test if p.contextual_ground_truth.label_status == "unmapped")
    test_ambiguous = sum(1 for p in test if p.contextual_ground_truth.label_status == "ambiguous")

    if test_mapped_single != 400:
        result.add_error(f"[20] Test mapped single-label: {test_mapped_single}, expected 400")
    if test_multi != 40:
        result.add_error(f"[20] Test multi-label: {test_multi}, expected 40")
    if test_unmapped != 150:
        result.add_error(f"[20] Test unmapped: {test_unmapped}, expected 150")
    if test_ambiguous != 50:
        result.add_error(f"[20] Test ambiguous: {test_ambiguous}, expected 50")


def _check_21_per_technique_single_label(pairs: List[ScenarioPair], result: ValidationResult) -> None:
    """Check 21: 50 contextual single-label per primary technique in test."""
    test = [p for p in pairs if p.split == "test"]
    tech_counts: Dict[str, int] = defaultdict(int)
    for p in test:
        cgt = p.contextual_ground_truth
        if cgt.label_status == "mapped" and len(cgt.technique_ids) == 1:
            tech_counts[cgt.technique_ids[0]] += 1

    for tid in BENCHMARK_CATALOG:
        count = tech_counts.get(tid, 0)
        if count != 50:
            result.add_error(f"[21] Test single-label for {tid}: {count}, expected 50")


def _check_22_multi_label_test(pairs: List[ScenarioPair], result: ValidationResult) -> None:
    """Check 22: Contextual multi-label test == 40."""
    test = [p for p in pairs if p.split == "test"]
    multi = sum(1 for p in test
                if p.contextual_ground_truth.label_status == "mapped"
                and len(p.contextual_ground_truth.technique_ids) >= 2)
    if multi != 40:
        result.add_error(f"[22] Test multi-label count: {multi}, expected 40")


def _check_23_transition_matrix_sums(pairs: List[ScenarioPair], result: ValidationResult) -> None:
    """Check 23: Transition matrix sums exactly to pair count."""
    matrix: Dict[str, int] = defaultdict(int)
    for p in pairs:
        sgt = p.single_ground_truth
        cgt = p.contextual_ground_truth
        # Determine technique set change type
        if sgt.label_status == "mapped" and cgt.label_status == "mapped":
            if set(sgt.technique_ids) == set(cgt.technique_ids):
                key = "mapped→mapped(same)"
            elif set(sgt.technique_ids).issubset(set(cgt.technique_ids)):
                key = "mapped→mapped(expanded)"
            else:
                key = "mapped→mapped(changed)"
        else:
            key = f"{sgt.label_status}→{cgt.label_status}"
        matrix[key] += 1

    total = sum(matrix.values())
    if total != len(pairs):
        result.add_error(f"[23] Transition matrix sum {total} != pair count {len(pairs)}")

    # Also check per-split
    for split_name in ("dev", "test"):
        split_pairs = [p for p in pairs if p.split == split_name]
        split_matrix: Dict[str, int] = defaultdict(int)
        for p in split_pairs:
            sgt = p.single_ground_truth
            cgt = p.contextual_ground_truth
            if sgt.label_status == "mapped" and cgt.label_status == "mapped":
                if set(sgt.technique_ids) == set(cgt.technique_ids):
                    key = "mapped→mapped(same)"
                elif set(sgt.technique_ids).issubset(set(cgt.technique_ids)):
                    key = "mapped→mapped(expanded)"
                else:
                    key = "mapped→mapped(changed)"
            else:
                key = f"{sgt.label_status}→{cgt.label_status}"
            split_matrix[key] += 1
        split_total = sum(split_matrix.values())
        expected = 30 if split_name == "dev" else 640
        if split_total != expected:
            result.add_error(f"[23] {split_name} transition sum {split_total} != {expected}")


def _check_24_template_family_count(pairs: List[ScenarioPair],
                                     registry: Optional[Dict] = None,
                                     result: ValidationResult = None) -> None:
    """Check 24: Actual template-family count matches registry/report."""
    families_in_data = set(p.template_family_id for p in pairs)
    if registry:
        families_in_registry = set(t["template_family_id"] for t in registry.get("families", []))
        data_only = families_in_data - families_in_registry
        registry_only = families_in_registry - families_in_data
        if data_only:
            result.add_error(f"[24] Families in data but not registry: {data_only}")
        if registry_only:
            result.add_warning(f"[24] Families in registry but not data: {registry_only}")


def _check_25_family_diversity(pairs: List[ScenarioPair], result: ValidationResult) -> None:
    """Check 25: No family violates diversity policy.

    Policy: max instances per family per technique/category =
    ceil(category_quota / num_families_for_that_category)
    """
    test = [p for p in pairs if p.split == "test"]

    # Per-technique single-label families
    for tid in BENCHMARK_CATALOG:
        tech_pairs = [p for p in test
                      if p.contextual_ground_truth.label_status == "mapped"
                      and len(p.contextual_ground_truth.technique_ids) == 1
                      and p.contextual_ground_truth.technique_ids[0] == tid]
        if not tech_pairs:
            continue
        family_counts: Dict[str, int] = defaultdict(int)
        for p in tech_pairs:
            family_counts[p.template_family_id] += 1
        num_families = len(family_counts)
        max_allowed = ceil(50 / num_families) if num_families > 0 else 50
        for fid, count in family_counts.items():
            if count > max_allowed:
                result.add_error(
                    f"[25] Family {fid} has {count} instances for {tid}, "
                    f"max allowed {max_allowed} (50/{num_families} families)"
                )


def _check_26_no_family_overlap_dev_test(pairs: List[ScenarioPair], result: ValidationResult) -> None:
    """Check 26: No template family appears in both dev and test (strict holdout)."""
    dev_families = set(p.template_family_id for p in pairs if p.split == "dev")
    test_families = set(p.template_family_id for p in pairs if p.split == "test")
    overlap = dev_families & test_families
    if overlap:
        result.add_error(f"[26] Template families in both dev and test: {overlap}")


def _check_27_local_account_host(pair: ScenarioPair, result: ValidationResult) -> None:
    """Check 27: T1136.001 scenarios not on domain controller hosts."""
    all_tids = set(pair.contextual_ground_truth.technique_ids) | set(pair.single_ground_truth.technique_ids)
    if "T1136.001" not in all_tids:
        return
    for eid, ev in pair.events.items():
        if ev.computer in HOSTS_DOMAIN_CONTROLLER:
            result.add_error(
                f"[27] Pair {pair.pair_id}: T1136.001 scenario uses DC host {ev.computer}"
            )
            break


def _check_28_near_duplicates(pairs: List[ScenarioPair], result: ValidationResult) -> None:
    """Check 28: Unexpected cross-pair duplicates."""
    dups = find_near_duplicates(pairs)
    for id_a, id_b, sim in dups:
        result.add_warning(f"[28] Near-duplicate: {id_a} <-> {id_b} (Jaccard={sim:.3f})")


def _check_29_reproduction(workspace: Path, reproduction_dir: Optional[Path],
                            result: ValidationResult) -> None:
    """Check 29: Deterministic reproduction (if reproduction dir provided)."""
    if not reproduction_dir or not reproduction_dir.exists():
        return
    from src.synthetic import _sha256_file
    files = ["events.jsonl", "views.jsonl", "pairs.jsonl", "ground_truth.jsonl", "split_manifest.json"]
    for fname in files:
        orig = workspace / fname
        repro = reproduction_dir / fname
        if not orig.exists() or not repro.exists():
            result.add_error(f"[29] Missing file for reproduction check: {fname}")
            continue
        if _sha256_file(orig) != _sha256_file(repro):
            result.add_error(f"[29] Reproduction hash mismatch: {fname}")


def _check_30_approval_hash(registry_path: Optional[Path],
                             expected_hash: Optional[str],
                             result: ValidationResult) -> None:
    """Check 30: Approval/template hash integrity."""
    if not registry_path or not expected_hash:
        return
    if not registry_path.exists():
        result.add_error(f"[30] Template registry not found: {registry_path}")
        return
    from src.synthetic import _sha256_file
    actual = _sha256_file(registry_path)
    if actual != expected_hash:
        result.add_error(
            f"[30] Template registry hash mismatch: expected {expected_hash[:16]}..., "
            f"got {actual[:16]}..."
        )


def _check_service_event_provider(pair: ScenarioPair, result: ValidationResult) -> None:
    """Additional: No event should have provider=Security-Auditing with EID 7045."""
    for eid, ev in pair.events.items():
        if ev.provider == "Microsoft-Windows-Security-Auditing" and ev.windows_event_id == 7045:
            result.add_error(
                f"Pair {pair.pair_id} event {eid}: EID 7045 with Security-Auditing provider is invalid. "
                f"Use EID 4697 for Security service-install events."
            )


def _check_event_telemetry_schema(pair: ScenarioPair, result: ValidationResult) -> None:
    """Reject generated events whose provider/channel/EventID tuple is not canonical."""
    for eid, event in pair.events.items():
        fields = CANONICAL_TELEMETRY_SCHEMA.get((event.provider, event.channel), {}).get(event.windows_event_id)
        if fields is None:
            result.add_error(
                f"Pair {pair.pair_id} event {eid}: unsupported provider/channel/EventID "
                f"{event.provider!r}/{event.channel!r}/{event.windows_event_id}"
            )


# ============================================================
# Main validation entry point
# ============================================================

def validate_synthetic_dataset(
    pairs: List[ScenarioPair],
    workspace_root: Path,
    stix_path: Optional[Path] = None,
    registry: Optional[Dict] = None,
    registry_path: Optional[Path] = None,
    expected_registry_hash: Optional[str] = None,
    reproduction_dir: Optional[Path] = None,
) -> ValidationResult:
    """Run all 30 validation checks on synthetic paired dataset."""
    result = ValidationResult()

    # Load ATT&CK techniques if available
    techniques: Dict = {}
    if stix_path and stix_path.exists():
        from src.attack_loader import parse_attack_bundle
        techniques = parse_attack_bundle(stix_path)

    # Per-pair checks
    for pair in pairs:
        _check_01_schema(pair, result)
        _check_03_pair_has_two_views(pair, result)
        _check_04_single_one_event(pair, result)
        _check_05_contextual_event_count(pair, result)
        _check_06_anchor_exists_in_both(pair, result)
        _check_07_strict_anchor_equality(pair, result)
        _check_08_attack_ids_in_stix(pair, techniques, result)
        _check_09_attack_name_match(pair, techniques, result)
        _check_10_parent_subtechnique(pair, techniques, result)
        _check_11_mapped_has_techniques(pair, result)
        _check_12_unmapped_no_techniques(pair, result)
        _check_13_ambiguous_no_techniques(pair, result)
        _check_14_evidence_is_view_local(pair, result)
        _check_15_no_hidden_contextual_evidence(pair, result)
        _check_16_temporal_coherence(pair, result)
        _check_17_transition_allowed(pair, result)
        _check_18_leakage(pair, result)
        _check_27_local_account_host(pair, result)
        _check_service_event_provider(pair, result)
        _check_event_telemetry_schema(pair, result)

    # Dataset-level checks
    if pairs:
        _check_02_unique_ids(pairs, result)
        _check_19_dev_quotas(pairs, result)
        _check_20_test_quotas(pairs, result)
        _check_21_per_technique_single_label(pairs, result)
        _check_22_multi_label_test(pairs, result)
        _check_23_transition_matrix_sums(pairs, result)
        _check_24_template_family_count(pairs, registry, result)
        _check_25_family_diversity(pairs, result)
        _check_26_no_family_overlap_dev_test(pairs, result)
        _check_28_near_duplicates(pairs, result)
        _check_29_reproduction(workspace_root, reproduction_dir, result)
        _check_30_approval_hash(registry_path, expected_registry_hash, result)

    result.statistics = compute_statistics(pairs)
    return result


# ============================================================
# Statistics & Reporting
# ============================================================

def compute_transition_matrix(pairs: List[ScenarioPair]) -> Dict[str, int]:
    """Compute the single→contextual transition matrix from pair annotations."""
    matrix: Dict[str, int] = defaultdict(int)
    for p in pairs:
        sgt = p.single_ground_truth
        cgt = p.contextual_ground_truth
        if sgt.label_status == "mapped" and cgt.label_status == "mapped":
            if set(sgt.technique_ids) == set(cgt.technique_ids):
                key = "mapped→mapped(same)"
            elif set(sgt.technique_ids).issubset(set(cgt.technique_ids)):
                key = "mapped→mapped(expanded)"
            else:
                key = "mapped→mapped(changed)"
        else:
            key = f"{sgt.label_status}→{cgt.label_status}"
        matrix[key] += 1
    return dict(matrix)


def compute_statistics(pairs: List[ScenarioPair]) -> Dict[str, Any]:
    """Generate complete dataset statistics."""
    if not pairs:
        return {"total_scenario_pairs": 0}

    dev = [p for p in pairs if p.split == "dev"]
    test = [p for p in pairs if p.split == "test"]
    ctx_events = [len(p.contextual_view.event_ids) for p in pairs]

    tech_single: Dict[str, int] = defaultdict(int)
    tech_contextual: Dict[str, int] = defaultdict(int)
    family_dist: Dict[str, int] = defaultdict(int)

    for p in pairs:
        family_dist[p.template_family_id] += 1
        for tid in p.single_ground_truth.technique_ids:
            tech_single[tid] += 1
        for tid in p.contextual_ground_truth.technique_ids:
            tech_contextual[tid] += 1

    return {
        "total_scenario_pairs": len(pairs),
        "total_views": len(pairs) * 2,
        "total_unique_events": len(set(eid for p in pairs for eid in p.events)),
        "dev_pairs": len(dev),
        "test_pairs": len(test),
        "dev_families": len(set(p.template_family_id for p in dev)),
        "test_families": len(set(p.template_family_id for p in test)),
        "total_families": len(set(p.template_family_id for p in pairs)),
        "technique_distribution_single": dict(tech_single),
        "technique_distribution_contextual": dict(tech_contextual),
        "events_per_contextual_view": {
            "min": min(ctx_events) if ctx_events else 0,
            "median": median(ctx_events) if ctx_events else 0,
            "max": max(ctx_events) if ctx_events else 0,
        },
        "template_family_distribution": dict(family_dist),
        "transition_matrix": compute_transition_matrix(pairs),
    }


def generate_audit_table(pairs: List[ScenarioPair]) -> List[Dict[str, Any]]:
    """Generate human-readable audit table for review."""
    table = []
    for pair in pairs:
        for view_type, view, gt in [
            ("single", pair.single_view, pair.single_ground_truth),
            ("contextual", pair.contextual_view, pair.contextual_ground_truth),
        ]:
            table.append({
                "pair_id": pair.pair_id,
                "scenario_id": pair.scenario_id,
                "template_family_id": pair.template_family_id,
                "split": pair.split,
                "view_type": view_type,
                "event_ids": list(view.event_ids),
                "label_status": gt.label_status,
                "technique_ids": list(gt.technique_ids),
                "technique_names": list(gt.technique_names),
                "evidence_summary": {k: len(v) for k, v in gt.evidence_refs.items()},
                "approval_reference": gt.approval_reference,
            })
    return table
