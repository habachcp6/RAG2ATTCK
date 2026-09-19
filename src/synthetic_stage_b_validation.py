"""Strict generated-data gates, in addition to the existing thirty checks."""

from collections import Counter
import ipaddress
import re
from urllib.parse import urlparse
from xml.etree import ElementTree

from src.synthetic import CANONICAL_TELEMETRY_SCHEMA, generate_deterministic_id, get_inference_payload, check_leakage
from src.synthetic_generator import SEED, GENERATOR_VERSION
from src.synthetic_generator import evidence_refs
from src.synthetic_predicates import evaluate_predicate
from src.synthetic_validator import validate_synthetic_dataset


def audit_pair(pair, family, registry_hash):
    errors = []
    def need(condition, message):
        if not condition: errors.append(f"{pair.pair_id}: {message}")
    fid = family["template_family_id"]
    index = pair.generation_provenance.get("instance_index")
    need(type(index) is int and 0 <= index < family["planned_instances"], "invalid instance index")
    need(pair.generation_seed == SEED, "seed mismatch")
    need(pair.split == family["split"], "family split differs from registry")
    need(pair.generation_provenance.get("registry_sha256") == registry_hash, "registry provenance mismatch")
    need(pair.generation_provenance.get("generator_version") == GENERATOR_VERSION, "generator version mismatch")
    for field, prefix in [("pair_id", "pair"), ("scenario_id", "scen")]:
        need(getattr(pair, field) == generate_deterministic_id(prefix, SEED, fid, str(index)), "deterministic " + field + " mismatch")
    keys = pair.generation_provenance.get("event_keys", {})
    specs = {"anchor": family["anchor"], **{s["event_key"]: s for s in family["contextual_event_specs"]}}
    need(set(keys) == set(specs), "event key set differs from registry")
    need(len(set(keys.values())) == len(keys) and set(keys.values()) == set(pair.events), "event key mapping is not bijective")
    events = {k: pair.events[eid] for k, eid in keys.items() if eid in pair.events}
    visible_processes = {
        event.fields.get("ProcessGuid"): event
        for event in pair.events.values()
        if event.windows_event_id == 1 and event.fields.get("ProcessGuid")
    }
    for event in pair.events.values():
        if event.windows_event_id == 1:
            parent = visible_processes.get(event.fields.get("ParentProcessGuid"))
            if parent:
                need(
                    event.fields.get("ParentCommandLine") == parent.fields.get("CommandLine"),
                    "ParentCommandLine disagrees with visible parent process",
                )
    for key, event in events.items():
        need(event.event_id == generate_deterministic_id("evt", SEED, fid, str(index), key), "deterministic event_id mismatch")
        if key not in specs: continue
        spec = specs[key]
        need((event.provider, event.channel, event.windows_event_id) == (spec["provider"], spec["channel"], spec["windows_event_id"]), "event specification mismatch")
        schema = CANONICAL_TELEMETRY_SCHEMA.get((event.provider, event.channel), {}).get(event.windows_event_id, ())
        need(set(event.fields) == set(schema), "canonical telemetry field set mismatch")
        need(event.fields.get("EventID") == event.windows_event_id, "EventID mismatch")
        need(event.fields.get("Computer") == event.computer, "Computer mismatch")
        need(event.fields.get("UtcTime", event.fields.get("TimeCreated")) == event.timestamp_utc, "timestamp mismatch")
        need(bool(get_inference_payload(event)), "empty inference payload")
        for leak in check_leakage(get_inference_payload(event)): need(False, "leakage: " + leak)
        if event.windows_event_id == 4720:
            need(not event.computer.upper().startswith("DC"), "local account on domain controller")
            need(0 < len(event.fields.get("TargetUserName", "")) <= 20, "local account name exceeds Windows limit")
        for field, value in event.fields.items():
            indicator_text = str(value)
            if field == "TaskContent":
                try:
                    task = ElementTree.fromstring(value)
                    need(task.tag == "{http://schemas.microsoft.com/windows/2004/02/mit/task}Task", "invalid scheduled-task XML namespace")
                    # A namespace URI is an identifier, not a contacted host.
                    # Still inspect every XML text/attribute value as telemetry.
                    indicator_text = " ".join((node.text or "") + " " + " ".join(node.attrib.values()) for node in task.iter())
                except ElementTree.ParseError:
                    need(False, "invalid scheduled-task XML")
            for candidate in re.findall(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])", str(value)):
                try:
                    address = ipaddress.ip_address(candidate)
                    safe = any(address in ipaddress.ip_network(net) for net in ("192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24"))
                except ValueError: safe = False
                need(safe, f"unsafe IP indicator in {field}: {candidate}")
            for url in re.findall(r"https?://[^\s\"'<>]+", indicator_text):
                host = urlparse(url).hostname or ""
                need(host.endswith((".example", ".invalid")), f"unsafe domain indicator in {field}: {host}")
    for kind in ["single", "contextual"]:
        view = getattr(pair, kind + "_view")
        gt = getattr(pair, kind + "_ground_truth")
        approved = family[kind + "_ground_truth"]
        need(view.view_id == generate_deterministic_id("view", SEED, fid, str(index), kind), "deterministic view_id mismatch")
        need(view.pair_id == pair.pair_id and gt.view_id == view.view_id, "view/ground-truth linkage mismatch")
        expected_ids = [keys.get("anchor")] if kind == "single" else list(keys.values())
        need(len(set(view.event_ids)) == len(view.event_ids) and set(view.event_ids) == set(expected_ids), "view event set mismatch")
        need(gt.label_status == approved["status"] and list(gt.technique_ids) == approved["technique_ids"] and list(gt.technique_names) == approved["technique_names"], "ground truth differs from approved registry")
        need(gt.rationale == approved["rationale"], "rationale differs from approved registry")
        need(gt.approval_reference == f"registry-sha256:{registry_hash}#{fid}/{kind}", "approval reference mismatch")
        selected = {k: event for k, event in events.items() if event.event_id in view.event_ids}
        try:
            need(evaluate_predicate(approved["evidence_predicate"], selected), "approved evidence predicate not satisfied for " + kind)
        except (KeyError, TypeError, ValueError):
            need(False, "malformed evidence predicate input for " + kind)
        need(set(gt.evidence_refs) == (set(gt.technique_ids) or {"decision"}), "evidence reference label set mismatch")
        try:
            expected_refs = {
                tid: evidence_refs(approved["evidence_predicate"].get(tid, approved["evidence_predicate"]), selected)
                for tid in approved["technique_ids"]
            } if approved["technique_ids"] else {"decision": evidence_refs(approved["evidence_predicate"], selected)}
            need(gt.evidence_refs == expected_refs, "evidence references differ from approved predicate dependencies")
        except (KeyError, TypeError, ValueError):
            need(False, "cannot resolve evidence reference dependencies")
        for label, refs in gt.evidence_refs.items():
            need(bool(refs), "missing evidence references for " + label)
            for ref in refs:
                eid = ref.get("event_id")
                fields = ref.get("fields", [])
                need(eid in view.event_ids and bool(fields), "evidence reference is not view-local or empty")
                if eid in pair.events:
                    need(set(fields).issubset(pair.events[eid].fields), "evidence reference field missing")
    return errors


def validate_stage_b(pairs, root, stix, registry, registry_path, registry_hash):
    result = validate_synthetic_dataset(pairs, root, stix, registry, registry_path, registry_hash)
    families = {f["template_family_id"]: f for f in registry["families"]}
    counts = Counter(p.template_family_id for p in pairs)
    for fid, family in families.items():
        if counts[fid] != family["planned_instances"]:
            result.add_error(f"Family {fid}: generated={counts[fid]} approved={family['planned_instances']}")
    all_ids = []
    indices = []
    for pair in pairs:
        if pair.template_family_id not in families:
            result.add_error(f"Unknown family {pair.template_family_id}")
            continue
        result.errors.extend(audit_pair(pair, families[pair.template_family_id], registry_hash))
        indices.append((pair.template_family_id, pair.generation_provenance.get("instance_index")))
        all_ids += [pair.pair_id, pair.scenario_id, pair.single_view.view_id, pair.contextual_view.view_id, *pair.events]
    if len(all_ids) != len(set(all_ids)): result.add_error("Duplicate scenario/pair/view/event identifiers")
    if len(indices) != len(set(indices)): result.add_error("Duplicate family instance indices")
    splits = {}
    for split in ["dev", "test"]:
        subset = [p for p in pairs if p.split == split]
        categories, techniques = Counter(), Counter()
        for p in subset:
            gt = p.contextual_ground_truth
            category = ("mapped_single" if len(gt.technique_ids) == 1 else "mapped_multi") if gt.label_status == "mapped" else gt.label_status
            categories[category] += 1
            if category == "mapped_single": techniques.update(gt.technique_ids)
        splits[split] = {"pairs": len(subset), "categories": dict(sorted(categories.items())), "mapped_single_per_technique": dict(sorted(techniques.items()))}
        quota = 2 if split == "dev" else 50
        if set(techniques.values()) != {quota} or set(techniques) != set(registry["benchmark_catalog"]["technique_ids"]):
            result.add_error(f"{split}: per-technique generated quota mismatch")
    result.statistics.update(total_pairs=len(pairs), views=2 * len(pairs), splits=splits)
    return result
