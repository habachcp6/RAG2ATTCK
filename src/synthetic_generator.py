"""Deterministic Stage B generator, bound to the approved registry and seed."""

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import hashlib
import inspect
import json
import random

from src import synthetic as model
from src.synthetic_predicates import evaluate_predicate, walk_predicate
from src.synthetic_recipes import realize_family, SYSTEM

GENERATOR_VERSION = "1.0.0"
SEED = 20260915

BUILDERS = {
    4688: model.build_security_4688, 4697: model.build_security_4697,
    4698: model.build_security_4698, 4720: model.build_security_4720,
    1102: model.build_security_1102, 1: model.build_sysmon_1,
    3: model.build_sysmon_3, 11: model.build_sysmon_11, 13: model.build_sysmon_13,
}
PARAM_FIELDS = {
    "timestamp_utc": "UtcTime", "computer": "Computer", "new_process": "NewProcessName",
    "command_line": "CommandLine", "parent_process": "ParentProcessName",
    "subject_user": "SubjectUserName", "target_user": "TargetUserName",
    "new_process_id": "NewProcessId", "creator_process_id": "ProcessId",
    "logon_id": "LogonId", "task_name": "TaskName", "task_content": "TaskContent",
    "service_name": "ServiceName", "service_file_name": "ServiceFileName",
    "service_type": "ServiceType", "service_start_type": "ServiceStartType",
    "service_account": "ServiceAccount", "subject_domain": "SubjectDomainName",
    "image": "Image", "parent_image": "ParentImage", "parent_command_line": "ParentCommandLine",
    "user": "User", "process_id": "ProcessId", "parent_process_id": "ParentProcessId",
    "process_guid": "ProcessGuid", "parent_process_guid": "ParentProcessGuid",
    "logon_guid": "LogonGuid", "hashes": "Hashes", "source_ip": "SourceIp",
    "source_port": "SourcePort", "destination_ip": "DestinationIp",
    "destination_port": "DestinationPort", "protocol": "Protocol",
    "target_filename": "TargetFilename", "event_type": "EventType",
    "target_object": "TargetObject", "details": "Details",
}


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def guid(text):
    h = digest(text)[:32]
    return "{" + "-".join([h[:8], h[8:12], h[12:16], h[16:20], h[20:]]) + "}"


def parameters(family_id, instance_index, seed):
    material = f"{seed}|{family_id}|{instance_index}"
    rng = random.Random(int(digest(material), 16))
    words = ["cedar", "birch", "maple", "aspen", "willow", "pine", "oak", "elm", "alder", "spruce", "beech", "fir", "ash", "larch", "yew", "holly"]
    resource = "_".join(rng.sample(words, 3)) + "_" + digest(material)[:6]
    return {
        "resource": resource, "user": rng.choice([u for u in model.SAFE_USERS if u not in {"system", "network.service", "local.service"}]),
        "ip": rng.choice(model.SAFE_IPS), "limited_ip": rng.choice(["198.51.100.20", "203.0.113.20"]),
        "host": rng.choice(model.HOSTS_ALLOWED_LOCAL_ACCOUNT),
        "source_ip": rng.choice(model.SAFE_IPS), "port": rng.randrange(49152, 65536),
        "pid": rng.randrange(1000, 20000) * 4,
        "job_number": rng.randrange(1, 65535), "mode": rng.choice(["daily", "weekly", "incremental"]),
        "whoami_flag": rng.choice(["all", "priv", "groups", "user"]),
        "format": rng.choice(["csv", "list", "table"]),
        "base_time": datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=rng.randrange(180 * 86400)),
        "material": material,
    }


def _make_fields(spec, overrides, values, timestamp, pid, pguid, parent_pid, parent_guid, actor):
    eid = spec["windows_event_id"]
    fields = {
        "TimeCreated": timestamp, "UtcTime": timestamp, "Computer": values["host"], "EventID": eid,
        "Image": SYSTEM + r"\helper.exe", "NewProcessName": SYSTEM + r"\helper.exe",
        "CommandLine": SYSTEM + r"\helper.exe", "ParentImage": r"C:\Windows\explorer.exe",
        "ParentProcessName": r"C:\Windows\explorer.exe", "ParentCommandLine": r"C:\Windows\explorer.exe",
        "User": actor, "SubjectUserName": actor, "TargetUserName": actor,
        "SubjectDomainName": values["host"], "SubjectLogonId": hex(values["pid"] + 1),
        "LogonId": hex(values["pid"] + 1), "LogonGuid": guid(values["material"] + "logon"),
        "ProcessId": hex(parent_pid) if eid == 4688 else pid,
        "NewProcessId": hex(pid), "ParentProcessId": parent_pid,
        "ProcessGuid": pguid, "ParentProcessGuid": parent_guid,
        "SourceIp": values["source_ip"], "SourcePort": values["port"],
        "DestinationIp": values["ip"], "DestinationPort": 443, "Protocol": "tcp",
        "Hashes": "", "ServiceName": "Service_" + values["resource"],
        "ServiceFileName": SYSTEM + r"\helper.exe", "ServiceType": "0x10", "ServiceStartType": "2",
        "ServiceAccount": "LocalSystem", "EventType": "SetValue", "TaskName": "", "TaskContent": "",
        "TargetFilename": "", "TargetObject": "", "Details": "",
    }
    overrides = dict(overrides)
    if eid == 4688:
        for a, b in [("Image", "NewProcessName"), ("ParentImage", "ParentProcessName"), ("User", "SubjectUserName")]:
            if a in overrides: overrides[b] = overrides.pop(a)
    fields.update(overrides)
    if eid == 4697 and fields["ServiceFileName"].startswith("C:\\Program Files\\"):
        path, rest = fields["ServiceFileName"].split(".exe", 1)
        fields["ServiceFileName"] = '"' + path + '.exe"' + rest
    if eid == 13 and fields["TargetObject"].startswith("HKCU\\"):
        sid = "S-1-5-21-111111111-222222222-333333333-" + str(1000 + int(digest(actor)[:4], 16))
        fields["TargetObject"] = "HKU\\" + sid + fields["TargetObject"][4:]
    if eid == 1:
        # Stable executable identity, not an instance-specific decorative hash.
        fields["Hashes"] = "SHA256=" + digest(fields["Image"].casefold())
        fields["ParentCommandLine"] = fields["ParentImage"]
    aliases = dict(PARAM_FIELDS)
    if eid >= 1000:
        aliases.update(timestamp_utc="TimeCreated", logon_id="SubjectLogonId")
    builder = BUILDERS[eid]
    kwargs = {name: fields[aliases[name]] for name, p in inspect.signature(builder).parameters.items()
              if p.kind != inspect.Parameter.VAR_KEYWORD}
    result = builder(**kwargs)
    assert set(result) == set(model.CANONICAL_TELEMETRY_SCHEMA[(spec["provider"], spec["channel"])][eid])
    return result


def evidence_refs(predicate, events):
    """References contain only fields actually read by the approved predicate."""
    found = {}
    from src.synthetic_predicates import relation_evidence_fields
    for leaf in walk_predicate(predicate):
        if "event" in leaf:
            found.setdefault(leaf["event"], set()).add(leaf["field"])
        else:
            for key, fields in relation_evidence_fields(leaf, events).items():
                found.setdefault(key, set()).update(fields)
    return [{"event_id": events[key].event_id, "fields": sorted(fields)} for key, fields in sorted(found.items())]


def generate_pair(family, seed, instance_index, registry_sha256):
    if type(instance_index) is not int or not 0 <= instance_index < family["planned_instances"]:
        raise ValueError("instance index outside approved family allocation")
    fid = family["template_family_id"]
    v = parameters(fid, instance_index, seed)
    recipes, order = realize_family(fid, v)
    specs = {"anchor": family["anchor"], **{s["event_key"]: s for s in family["contextual_event_specs"]}}
    if set(order) != set(specs) or len(order) != len(specs):
        raise ValueError(f"{fid}: recipe event keys differ from approved specifications")
    actor = recipes["anchor"].get("SubjectUserName", recipes["anchor"].get("User", v["user"]))
    # A union over explicitly same-process relations. Parent/child remains distinct.
    roots = {key: key for key in specs}
    def root(key):
        while roots[key] != key: key = roots[key]
        return key
    rules = list(walk_predicate(family["contextual_ground_truth"]["evidence_predicate"]))
    for r in rules:
        name = r.get("relation")
        keys = None
        if name in {"same_process", "same_process_guid"}: keys = r["events"]
        elif name in {"process_then_network", "process_then_registry", "network_then_file"}:
            keys = [value for key, value in r.items() if key != "relation"]
        elif name == "process_then_file":
            x, y = r["process"], r["file"]
            if recipes[x].get("Image") == recipes[y].get("Image"): keys = [x, y]
        if keys:
            for key in keys[1:]: roots[root(key)] = root(keys[0])
    for key in order:
        if specs[key]["windows_event_id"] not in {3, 11, 13}:
            continue
        for candidate in reversed(order[:order.index(key)]):
            if specs[candidate]["windows_event_id"] in {1, 4688} and recipes[candidate].get("Image") == recipes[key].get("Image"):
                roots[root(key)] = root(candidate)
                break
    pids = {k: v["pid"] + list(specs).index(root(k)) * 4 for k in specs}
    guids = {k: guid(v["material"] + root(k)) for k in specs}
    parents = {}
    for r in rules:
        if r.get("relation") == "parent_child": parents[r["child"]] = r["parent"]
        if r.get("relation") == "parent_network_before_child": parents[r["child"]] = r["network"]
    # Correlate visible process-tree context even if registry only requires host.
    for child in order:
        parent_image = recipes[child].get("ParentImage")
        if parent_image:
            for candidate in order[:order.index(child)]:
                if recipes[candidate].get("Image") == parent_image: parents[child] = candidate
    events = {}
    for ordinal, key in enumerate(order):
        timestamp = (v["base_time"] + timedelta(seconds=ordinal * 3)).isoformat().replace("+00:00", "Z")
        parent = parents.get(key)
        fields = _make_fields(specs[key], recipes[key], v, timestamp, pids[key], guids[key],
                              pids[parent] if parent else v["pid"] - 4,
                              guids[parent] if parent else guid(v["material"] + "external-parent"), actor)
        eid = model.generate_deterministic_id("evt", seed, fid, str(instance_index), key)
        events[key] = model.SyntheticEvent(eid, specs[key]["provider"], specs[key]["channel"],
                                          int(digest(v["material"] + key)[:12], 16), specs[key]["windows_event_id"], v["host"], timestamp, fields)
    pair_id = model.generate_deterministic_id("pair", seed, fid, str(instance_index))
    views, truths = {}, {}
    for kind in ["single", "contextual"]:
        gt = family[kind + "_ground_truth"]
        selected = {"anchor": events["anchor"]} if kind == "single" else events
        if not evaluate_predicate(gt["evidence_predicate"], selected):
            failed = [r for r in walk_predicate(gt["evidence_predicate"]) if not evaluate_predicate(r, selected)]
            raise ValueError(f"{fid}[{instance_index}] {kind}: generated evidence violates approved predicate: {failed}")
        vid = model.generate_deterministic_id("view", seed, fid, str(instance_index), kind)
        views[kind] = model.View(vid, pair_id, kind, tuple(e.event_id for e in selected.values()))
        refs = {}
        for tid in gt["technique_ids"]:
            predicate = gt["evidence_predicate"].get(tid, gt["evidence_predicate"])
            refs[tid] = evidence_refs(predicate, selected)
        if not gt["technique_ids"]:
            refs["decision"] = evidence_refs(gt["evidence_predicate"], selected)
        truths[kind] = model.ViewGroundTruth(vid, gt["status"], tuple(gt["technique_ids"]), tuple(gt["technique_names"]), refs, gt["rationale"], f"registry-sha256:{registry_sha256}#{fid}/{kind}")
    return model.ScenarioPair(pair_id, model.generate_deterministic_id("scen", seed, fid, str(instance_index)),
                              fid, family["split"], views["single"], views["contextual"],
                              {e.event_id: e for e in events.values()}, truths["single"], truths["contextual"], seed,
                              {"generator_version": GENERATOR_VERSION, "registry_sha256": registry_sha256,
                               "instance_index": instance_index, "event_keys": {k: e.event_id for k, e in events.items()}})


def generate_dataset(registry, registry_sha256, seed=SEED):
    """Exact approved allocation; no resampling, quota repair or split changes."""
    if seed != SEED:
        raise ValueError(f"Frozen seed must remain {SEED}")
    return sorted([generate_pair(family, seed, i, registry_sha256)
                   for family in registry["families"] for i in range(family["planned_instances"])], key=lambda p: p.pair_id)
