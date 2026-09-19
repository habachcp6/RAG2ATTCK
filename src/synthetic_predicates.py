"""Executable, view-local registry predicates and explicit telemetry relations.

Labels come from the registry, never from evaluating inference text. Predicates
are used only to check whether generated telemetry realizes the approved evidence.
"""

from datetime import datetime
from pathlib import PureWindowsPath
import re

from src.synthetic import SyntheticEvent


ORDERED_RELATIONS = {
    "parent_child": ("parent", "child"),
    "process_then_file": ("process", "file"),
    "process_then_network": ("process", "network"),
    "process_then_registry": ("process", "registry"),
    "process_then_task": ("process", "task"),
    "process_then_service": ("process", "service"),
    "network_then_file": ("network", "file"),
    "task_then_process": ("task", "process"),
    "service_then_process": ("service", "process"),
    "registry_then_process": ("registry", "process"),
    "file_then_process": ("file", "process"),
    "parent_network_before_child": ("network", "child"),
    "temporal_before": ("before", "after"),
    "temporal_within": ("before", "after"),
}


def walk_predicate(predicate):
    if isinstance(predicate, dict):
        if "event" in predicate or "relation" in predicate:
            yield predicate
        else:
            for value in predicate.values():
                yield from walk_predicate(value)
    elif isinstance(predicate, list):
        for value in predicate:
            yield from walk_predicate(value)


def event_time(event):
    return datetime.fromisoformat(event.timestamp_utc.replace("Z", "+00:00"))


def process_id(event):
    value = event.fields.get("NewProcessId" if event.windows_event_id == 4688 else "ProcessId")
    if value is None:
        return None
    return int(value, 16) if isinstance(value, str) and value.startswith("0x") else int(value)


def same_process(a, b):
    if a.computer != b.computer:
        return False
    ga, gb = a.fields.get("ProcessGuid"), b.fields.get("ProcessGuid")
    if ga and gb:
        return ga == gb
    return process_id(a) is not None and process_id(a) == process_id(b)


def image(event):
    return event.fields.get("Image", event.fields.get("NewProcessName", ""))


def actor(event):
    return event.fields.get("SubjectUserName", event.fields.get("User", ""))


def _relation(rule, events):
    name = rule["relation"]
    if name.startswith("same_"):
        selected = [events[k] for k in rule["events"]]
        a = selected[0]
        if name in {"same_process", "same_process_guid"}:
            if name == "same_process_guid" and not all(e.fields.get("ProcessGuid") for e in selected):
                return False
            return all(same_process(a, b) for b in selected[1:])
        if name == "same_host":
            values = [e.computer for e in selected]
        elif name == "same_user":
            values = [actor(e).casefold() for e in selected]
        elif name == "same_logon":
            values = [e.fields.get("SubjectLogonId", e.fields.get("LogonId")) for e in selected]
        else:
            raise ValueError(f"Unknown relation: {name}")
        return bool(values[0]) and len(set(values)) == 1
    left, right = ORDERED_RELATIONS[name]
    a, b = events[rule[left]], events[rule[right]]
    if not (a.computer == b.computer and event_time(a) < event_time(b)):
        return False
    if name == "temporal_before":
        return True
    if name == "temporal_within":
        return (event_time(b) - event_time(a)).total_seconds() <= rule["within_seconds"]
    if name == "parent_child":
        if b.fields.get("ParentProcessGuid") and a.fields.get("ProcessGuid"):
            return b.fields["ParentProcessGuid"] == a.fields["ProcessGuid"]
        parent = b.fields.get("ProcessId" if b.windows_event_id == 4688 else "ParentProcessId")
        parent = int(parent, 16) if isinstance(parent, str) and parent.startswith("0x") else int(parent)
        return parent == process_id(a)
    if name == "parent_network_before_child":
        return bool(a.fields.get("ProcessGuid")) and a.fields["ProcessGuid"] == b.fields.get("ParentProcessGuid")
    if name in {"process_then_network", "process_then_registry", "network_then_file"}:
        return same_process(a, b)
    if name == "process_then_file":
        # A shell may delegate the write to curl/certutil. Require the exact
        # destination in the invoking command and same host/user, or direct GUID.
        path = b.fields["TargetFilename"].casefold()
        return same_process(a, b) or (actor(a) == actor(b) and path in a.fields.get("CommandLine", "").casefold())
    if name == "file_then_process":
        return a.fields["TargetFilename"].casefold() in b.fields.get("CommandLine", "").casefold()
    if name in {"task_then_process", "service_then_process", "registry_then_process"}:
        field = {"task_then_process": "TaskContent", "service_then_process": "ServiceFileName", "registry_then_process": "Details"}[name]
        # Task XML may use an executable basename; service/RunOnce paths are full.
        executable = PureWindowsPath(image(b)).name.casefold()
        return bool(executable) and executable in a.fields[field].casefold()
    if name in {"process_then_task", "process_then_service"}:
        return bool(actor(a)) and actor(a) == actor(b)
    raise ValueError(f"Unknown relation: {name}")


def evaluate_predicate(predicate, events: dict[str, SyntheticEvent]) -> bool:
    if "all" in predicate:
        return all(evaluate_predicate(p, events) for p in predicate["all"])
    if "any" in predicate:
        return any(evaluate_predicate(p, events) for p in predicate["any"])
    if "not" in predicate:
        return not evaluate_predicate(predicate["not"], events)
    if "relation" in predicate:
        keys = predicate.get("events", [v for k, v in predicate.items() if k not in {"relation", "within_seconds"}])
        return all(k in events for k in keys) and _relation(predicate, events)
    if "event" not in predicate:
        return all(evaluate_predicate(p, events) for p in predicate.values())
    if predicate["event"] not in events:
        return False
    fields = events[predicate["event"]].fields
    if predicate["field"] not in fields:
        return False
    actual, expected, op = fields[predicate["field"]], predicate["value"], predicate["op"]
    if op == "eq": return actual == expected
    if op == "neq": return actual != expected
    if op == "in": return actual in expected
    if op == "not_in": return actual not in expected
    if op == "regex": return re.search(expected, str(actual)) is not None
    if op.endswith("_ci"):
        actual, expected, op = str(actual).casefold(), str(expected).casefold(), op[:-3]
    if op == "contains": return expected in actual
    if op == "startswith": return actual.startswith(expected)
    if op == "endswith": return actual.endswith(expected)
    raise ValueError(f"Unknown predicate operator: {op}")


def validate_relation_contract(family):
    """Reject impossible ordered cycles and repeated creation of one process."""
    errors = []
    specs = {"anchor": family["anchor"], **{s["event_key"]: s for s in family["contextual_event_specs"]}}
    rules = list(walk_predicate(family["contextual_ground_truth"]["evidence_predicate"]))
    edges = []
    for rule in rules:
        name = rule.get("relation")
        if name in ORDERED_RELATIONS:
            x, y = ORDERED_RELATIONS[name]
            if x in rule and y in rule:
                edges.append((rule[x], rule[y]))
        if name in {"same_process", "same_process_guid"}:
            creations = [specs[k] for k in rule.get("events", []) if k in specs and specs[k]["windows_event_id"] in {1, 4688}]
            if len(creations) > 1 and len({s["provider"] for s in creations}) < len(creations):
                errors.append("same_process cannot represent two distinct process creations from the same provider")
    def reaches(start, target, seen):
        if start in seen: return False
        return any(b == target or reaches(b, target, seen | {start}) for a, b in edges if a == start)
    if any(reaches(b, a, set()) for a, b in edges):
        errors.append("ordered relation cycle has no valid event chronology")
    return errors


def relation_evidence_fields(rule, events):
    """Return exact field dependencies of a relation, without unrelated telemetry."""
    name = rule["relation"]
    keys = rule.get("events", [v for k, v in rule.items() if k not in {"relation", "within_seconds"}])
    refs = {k: set() for k in keys}
    def add(k, *fields): refs[k].update(fields)
    def user_field(k): return "SubjectUserName" if "SubjectUserName" in events[k].fields else "User"
    def pid_field(k): return "NewProcessId" if events[k].windows_event_id == 4688 else "ProcessId"
    def identity(a, b):
        add(a, "Computer"); add(b, "Computer")
        if events[a].fields.get("ProcessGuid") and events[b].fields.get("ProcessGuid"):
            add(a, "ProcessGuid"); add(b, "ProcessGuid")
        else:
            add(a, pid_field(a)); add(b, pid_field(b))
    if name == "same_host":
        for k in keys: add(k, "Computer")
    elif name == "same_user":
        for k in keys: add(k, user_field(k))
    elif name == "same_logon":
        for k in keys: add(k, "SubjectLogonId" if "SubjectLogonId" in events[k].fields else "LogonId")
    elif name in {"same_process", "same_process_guid"}:
        for k in keys[1:]: identity(keys[0], k)
    else:
        x, y = ORDERED_RELATIONS[name]; a, b = rule[x], rule[y]
        for k in [a, b]: add(k, "Computer", "TimeCreated" if "TimeCreated" in events[k].fields else "UtcTime")
        if name == "parent_child":
            if events[b].fields.get("ParentProcessGuid") and events[a].fields.get("ProcessGuid"):
                add(a,"ProcessGuid"); add(b,"ParentProcessGuid")
            else:
                add(a,pid_field(a)); add(b,"ProcessId" if events[b].windows_event_id==4688 else "ParentProcessId")
        elif name == "parent_network_before_child":
            add(a,"ProcessGuid"); add(b,"ParentProcessGuid")
        elif name in {"process_then_network", "process_then_registry", "network_then_file"}:
            identity(a,b)
        elif name == "process_then_file":
            if same_process(events[a],events[b]): identity(a,b)
            else:
                add(a,user_field(a),"CommandLine"); add(b,user_field(b),"TargetFilename")
        elif name == "file_then_process":
            add(a,"TargetFilename"); add(b,"CommandLine")
        elif name in {"task_then_process", "service_then_process", "registry_then_process"}:
            add(a,{"task_then_process":"TaskContent","service_then_process":"ServiceFileName","registry_then_process":"Details"}[name])
            add(b,"Image" if "Image" in events[b].fields else "NewProcessName")
        elif name in {"process_then_task", "process_then_service"}:
            add(a,user_field(a)); add(b,user_field(b))
    return refs
