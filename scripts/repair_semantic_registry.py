"""One-time Stage A migration for the synthetic template registry.

The resulting JSON is the authoritative semantic registry.  This script is
kept deliberately data-oriented so every family has explicit telemetry,
predicates, provenance, and counter-evidence before the approval report is
regenerated.  It never creates events, views, pairs, or a frozen dataset.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "config" / "synthetic_templates.json"

NAMES = {
    "T1059.001": "PowerShell",
    "T1059.003": "Windows Command Shell",
    "T1053.005": "Scheduled Task",
    "T1543.003": "Windows Service",
    "T1136.001": "Local Account",
    "T1547.001": "Registry Run Keys / Startup Folder",
    "T1685.005": "Clear Windows Event Logs",
    "T1105": "Ingress Tool Transfer",
}

ATTACK_URLS = {
    tid: f"https://attack.mitre.org/techniques/{tid.split('.')[0]}/{tid.split('.')[1]}"
    if "." in tid else f"https://attack.mitre.org/techniques/{tid}"
    for tid in NAMES
}

SECURITY = "Microsoft-Windows-Security-Auditing"
EVENTLOG = "Microsoft-Windows-Eventlog"
SYSMON = "Microsoft-Windows-Sysmon"
SECURITY_CHANNEL = "Security"
SYSMON_CHANNEL = "Microsoft-Windows-Sysmon/Operational"

EVENT_DOCS = {
    4688: "https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688",
    4697: "https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4697",
    4698: "https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4698",
    4720: "https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4720",
    1102: "https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-1102",
    1: "https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create",
    3: "https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-3-network-connection",
    11: "https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create",
    13: "https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-13-registry-event",
}


def leaf(event: str, field: str, op: str, value: Any) -> dict[str, Any]:
    return {"event": event, "field": field, "op": op, "value": value}


def all_of(*items: dict[str, Any]) -> dict[str, Any]:
    return {"all": list(items)}


def any_of(*items: dict[str, Any]) -> dict[str, Any]:
    return {"any": list(items)}


def not_(item: dict[str, Any]) -> dict[str, Any]:
    return {"not": item}


def relation(kind: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    if args:
        if len(args) % 2:
            raise ValueError(f"relation {kind} requires key/value pairs")
        kwargs.update(dict(zip(args[::2], args[1::2])))
    return {"relation": kind, **kwargs}


def source(ids: list[str], comparisons: list[str] | None = None) -> dict[str, Any]:
    refs = [
        {"technique_id": tid, "technique_name": NAMES[tid], "url": ATTACK_URLS[tid]}
        for tid in ids
    ]
    return {
        "catalog": "MITRE ATT&CK Enterprise v19.2",
        "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
        "technique_references": refs,
        "comparison_technique_ids": comparisons or ids,
    }


def telemetry_source(specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str, int]] = set()
    result = []
    for spec in specs:
        key = (spec["provider"], spec["channel"], spec["windows_event_id"])
        if key in seen:
            continue
        seen.add(key)
        result.append({
            "provider": spec["provider"],
            "channel": spec["channel"],
            "event_ids": [spec["windows_event_id"]],
            "reference": EVENT_DOCS[spec["windows_event_id"]],
        })
    return result


def gt(status: str, ids: list[str], predicate: Any, rationale: str) -> dict[str, Any]:
    return {
        "status": status,
        "technique_ids": ids,
        "technique_names": [NAMES[tid] for tid in ids],
        "evidence_predicate": predicate,
        "rationale": rationale,
    }


def spec(
    fid: str,
    category: str,
    split: str,
    behavior: str,
    anchor: dict[str, Any],
    single: dict[str, Any],
    contextual: dict[str, Any],
    context_descriptions: list[str],
    context_specs: list[dict[str, Any]],
    counter: str,
    near_miss: str,
    allowed: list[str],
    disallowed: list[str],
    original: dict[str, Any],
    comparison_ids: list[str] | None = None,
    host_constraints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    all_telemetry = [anchor, *context_specs]
    result = {
        "template_family_id": fid,
        "category": category,
        "split": split,
        "technique_ids": contextual["technique_ids"],
        "behavior_description": behavior,
        "anchor": anchor,
        "single_ground_truth": single,
        "contextual_ground_truth": contextual,
        "expected_transition": f"{single['status']}->{contextual['status']}",
        "contextual_event_descriptions": context_descriptions,
        "contextual_event_specs": context_specs,
        "counter_evidence": counter,
        "benign_near_miss": near_miss,
        "allowed_variations": allowed,
        "disallowed_variations": disallowed,
        "attack_source": source(
            contextual["technique_ids"],
            comparisons=comparison_ids,
        ),
        "windows_telemetry_source": telemetry_source(all_telemetry),
        "planned_instances": original["planned_instances"],
    }
    if host_constraints:
        result["host_constraints"] = host_constraints
    return result


def a(provider: str, channel: str, eid: int, rule: str) -> dict[str, Any]:
    return {
        "provider": provider,
        "channel": channel,
        "windows_event_id": eid,
        "selection_rule": rule,
    }


def ctx(key: str, provider: str, channel: str, eid: int, rule: str) -> dict[str, Any]:
    return {
        "event_key": key,
        "provider": provider,
        "channel": channel,
        "windows_event_id": eid,
        "selection_rule": rule,
    }


def build() -> dict[str, Any]:
    original = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    old = {item["template_family_id"]: item for item in original["families"]}
    families: list[dict[str, Any]] = []

    # PowerShell: one strong single-view family, one context-resolved family,
    # and two distinct script-content families.
    families += [
        spec("TF_T1059_001_A", "mapped_single", "test", "Encoded PowerShell launched by an Office document",
             a(SYSMON, SYSMON_CHANNEL, 1, "Sysmon process creation where Image is powershell.exe, CommandLine contains -EncodedCommand, and ParentImage is an Office application"),
             gt("mapped", ["T1059.001"], all_of(leaf("anchor", "Image", "endswith_ci", "\\powershell.exe"), any_of(leaf("anchor", "CommandLine", "contains_ci", "-EncodedCommand"), leaf("anchor", "CommandLine", "contains_ci", "-enc ")), leaf("anchor", "ParentImage", "endswith_ci", "\\winword.exe")), "Sysmon exposes PowerShell execution, an encoded command, and Office as the parent process in the single view."),
             gt("mapped", ["T1059.001"], all_of(leaf("anchor", "Image", "endswith_ci", "\\powershell.exe"), leaf("anchor", "CommandLine", "contains_ci", "-EncodedCommand"), leaf("anchor", "ParentImage", "endswith_ci", "\\winword.exe"), relation("same_host", "events", ["anchor", "context_1"])), "The contextual process-tree event confirms the Office-to-PowerShell lineage without adding another technique label."),
             ["A Sysmon process-create event for winword.exe is present before the PowerShell anchor."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "Office parent process for the PowerShell child")],
             "A signed enterprise automation tool may use an encoded PowerShell command; signing and an approved parent are counter-evidence.",
             "A help-desk document opening a signed PowerShell bootstrapper with a non-encoded command.",
             ["Use powershell.exe or pwsh.exe with a concrete command-line indicator."], ["Do not add ATT&CK IDs or ground-truth words to CommandLine."], old["TF_T1059_001_A"]),
        spec("TF_T1059_001_C", "mapped_single", "test", "PowerShell started through WMI with intent resolved by context",
             a(SYSMON, SYSMON_CHANNEL, 1, "Sysmon process creation where PowerShell is a child of WmiPrvSE.exe"),
             gt("ambiguous", [], all_of(leaf("anchor", "Image", "endswith_ci", "\\powershell.exe"), leaf("anchor", "ParentImage", "endswith_ci", "\\WmiPrvSE.exe")), "WMI-launched PowerShell is observable, but that execution path is dual-use and the single view lacks intent evidence."),
             gt("mapped", ["T1059.001"], all_of(leaf("anchor", "Image", "endswith_ci", "\\powershell.exe"), leaf("anchor", "ParentImage", "endswith_ci", "\\WmiPrvSE.exe"), leaf("anchor", "CommandLine", "contains_ci", "-NoProfile"), leaf("context_1", "DestinationPort", "eq", 135), relation("process_then_network", "process", "anchor", "network", "context_1")), "The WMI parent, non-interactive PowerShell invocation, and related RPC connection provide defensible contextual evidence for PowerShell execution."),
             ["A Sysmon network event to TCP/135 is linked to the WMI process before the PowerShell child."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 3, "RPC connection associated with the WMI-launched process")],
             "Remote administration by an authorized operator using WMI and PowerShell remains a benign near-miss.",
             "A locally launched PowerShell process with a signed maintenance script and no remote lineage.",
             ["Keep the WMI parent visible in the anchor fields."], ["Do not label WMI alone as malicious."], old["TF_T1059_001_C"]),
        spec("TF_T1059_001_E", "mapped_single", "test", "Obfuscated PowerShell using Invoke-Expression and decoded content",
             a(SYSMON, SYSMON_CHANNEL, 1, "PowerShell process whose command line contains Invoke-Expression and FromBase64String"),
             gt("mapped", ["T1059.001"], all_of(leaf("anchor", "Image", "endswith_ci", "\\powershell.exe"), leaf("anchor", "CommandLine", "contains_ci", "Invoke-Expression"), leaf("anchor", "CommandLine", "contains_ci", "FromBase64String")), "PowerShell execution with explicit dynamic evaluation and decoded content is directly visible in the anchor."),
             gt("mapped", ["T1059.001"], all_of(leaf("anchor", "Image", "endswith_ci", "\\powershell.exe"), leaf("anchor", "CommandLine", "contains_ci", "Invoke-Expression"), leaf("anchor", "CommandLine", "contains_ci", "FromBase64String"), relation("same_process", "events", ["anchor", "context_1"])), "The contextual event is the same process identity and confirms the obfuscated PowerShell command rather than introducing a new label."),
             ["A follow-on Sysmon event carries the same ProcessGuid as the obfuscated PowerShell anchor."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 3, "Network activity from the same PowerShell process")],
             "An authorized incident-response script can use dynamic evaluation; a documented runbook and signed script are counter-evidence.",
             "A PowerShell script using ordinary variables and no dynamic evaluation or decoding.",
             ["Preserve both dynamic-evaluation and decoding indicators."], ["Do not infer a second technique from the network event alone."], old["TF_T1059_001_E"]),
        spec("TF_T1059_001_F", "mapped_single", "test", "PowerShell reflective assembly loading in memory",
             a(SYSMON, SYSMON_CHANNEL, 1, "PowerShell command line contains Reflection.Assembly and Assembly.Load"),
             gt("mapped", ["T1059.001"], all_of(leaf("anchor", "Image", "endswith_ci", "\\powershell.exe"), leaf("anchor", "CommandLine", "contains_ci", "Reflection.Assembly"), leaf("anchor", "CommandLine", "contains_ci", "Assembly.Load")), "The anchor directly records PowerShell performing reflective assembly loading."),
             gt("mapped", ["T1059.001"], all_of(leaf("anchor", "Image", "endswith_ci", "\\powershell.exe"), leaf("anchor", "CommandLine", "contains_ci", "Assembly.Load"), leaf("context_1", "Image", "endswith_ci", "\\powershell.exe"), relation("same_process", "events", ["anchor", "context_1"])), "The follow-on event shares the process identity and confirms the in-memory PowerShell execution chain."),
             ["A same-process Sysmon event follows the reflective load."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "Same PowerShell process after the reflective load")],
             "A signed application compatibility shim may load an assembly reflectively; approved publisher and path are counter-evidence.",
             "PowerShell loading a normal module from a trusted module directory.",
             ["Keep Reflection.Assembly and Assembly.Load as visible indicators."], ["Do not claim a fileless technique from Image alone."], old["TF_T1059_001_F"]),
    ]

    families += [
        spec("TF_T1059_003_A", "mapped_single", "test", "Windows Command Shell running a chained administrative command",
             a(SECURITY, SECURITY_CHANNEL, 4688, "Security 4688 where NewProcessName is cmd.exe and CommandLine contains /c, command chaining, and output redirection"),
             gt("mapped", ["T1059.003"], all_of(leaf("anchor", "NewProcessName", "endswith_ci", "\\cmd.exe"), leaf("anchor", "CommandLine", "contains_ci", " /c "), leaf("anchor", "CommandLine", "contains_ci", "&&"), leaf("anchor", "CommandLine", "contains_ci", "> C:\\ProgramData\\")), "The Security process-creation record shows a command-shell interpreter executing a chained command and redirecting output."),
             gt("mapped", ["T1059.003"], all_of(leaf("anchor", "NewProcessName", "endswith_ci", "\\cmd.exe"), leaf("anchor", "CommandLine", "contains_ci", " /c "), leaf("anchor", "CommandLine", "contains_ci", "&&"), relation("same_process", "events", ["anchor", "context_1"])), "The same process is confirmed by a later Security process record, preserving the command-shell evidence."),
             ["A related child process is recorded under the same command-shell process identity."],
             [ctx("context_1", SECURITY, SECURITY_CHANNEL, 4688, "Child process created by cmd.exe")],
             "Routine support scripts may use cmd.exe; an approved script path, signed parent, and no suspicious output destination are counter-evidence.",
             "cmd.exe /c ipconfig used interactively by a help-desk operator.",
             ["Use NewProcessName and CommandLine from Security 4688."], ["Do not map cmd.exe merely because it exists."], old["TF_T1059_003_A"]),
        spec("TF_T1059_003_B", "mapped_single", "test", "Windows Command Shell launched by a service with transfer staging resolved by context",
             a(SECURITY, SECURITY_CHANNEL, 4688, "Security 4688 where cmd.exe is a child of services.exe"),
             gt("ambiguous", [], all_of(leaf("anchor", "NewProcessName", "endswith_ci", "\\cmd.exe"), leaf("anchor", "ParentProcessName", "endswith_ci", "\\services.exe")), "A service-launched command shell is observable, but the single view does not establish whether the action is administration or adversarial."),
             gt("mapped", ["T1059.003"], all_of(leaf("anchor", "NewProcessName", "endswith_ci", "\\cmd.exe"), leaf("anchor", "ParentProcessName", "endswith_ci", "\\services.exe"), leaf("anchor", "CommandLine", "contains_ci", "certutil"), leaf("anchor", "CommandLine", "contains_ci", "-urlcache"), relation("process_then_file", "process", "anchor", "file", "context_1")), "The service parent, explicit command-shell execution of certutil staging, and linked file creation provide the contextual threshold."),
             ["A Sysmon file-create event is linked to the cmd.exe ProcessId after the certutil command."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 11, "Payload file created by the service-launched command shell")],
             "A software deployment service may invoke cmd.exe and certutil for an approved package; publisher and managed destination are counter-evidence.",
             "cmd.exe launched by services.exe to run a fixed vendor maintenance command.",
             ["Require both a shell invocation and a concrete command-line behavior."], ["Do not treat the services.exe parent as sufficient by itself."], old["TF_T1059_003_B"]),
        spec("TF_T1059_003_C", "mapped_single", "test", "Windows Command Shell executing a batch file from a public staging path",
             a(SECURITY, SECURITY_CHANNEL, 4688, "Security 4688 where cmd.exe executes a .bat file with delayed expansion and a public staging path"),
             gt("mapped", ["T1059.003"], all_of(leaf("anchor", "NewProcessName", "endswith_ci", "\\cmd.exe"), leaf("anchor", "CommandLine", "contains_ci", ".bat"), leaf("anchor", "CommandLine", "contains_ci", "C:\\Users\\Public\\"), leaf("anchor", "CommandLine", "contains_ci", "/v:on")), "The anchor identifies cmd.exe and a concrete batch-script execution with shell-specific delayed expansion."),
             gt("mapped", ["T1059.003"], all_of(leaf("anchor", "NewProcessName", "endswith_ci", "\\cmd.exe"), leaf("anchor", "CommandLine", "contains_ci", ".bat"), leaf("context_1", "TargetFilename", "contains_ci", ".bat"), relation("process_then_file", "process", "anchor", "file", "context_1")), "A linked batch-file creation event confirms the command shell is executing the staged script."),
             ["The batch file is created immediately before the cmd.exe process record."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 11, "Batch file written to the staging path")],
             "Enterprise deployment systems also run batch files; a signed package and managed software directory are counter-evidence.",
             "cmd.exe executing a batch file from C:\\Program Files\\Contoso.",
             ["Retain the shell-specific /v:on and batch-file indicators."], ["Do not use only a filename or PID variation."], old["TF_T1059_003_C"]),
        spec("TF_T1059_003_E", "mapped_single", "test", "Windows Command Shell piping reconnaissance into a staged output file",
             a(SECURITY, SECURITY_CHANNEL, 4688, "Security 4688 where cmd.exe uses a pipe, findstr, and output to ProgramData"),
             gt("mapped", ["T1059.003"], all_of(leaf("anchor", "NewProcessName", "endswith_ci", "\\cmd.exe"), leaf("anchor", "CommandLine", "contains_ci", " | "), leaf("anchor", "CommandLine", "contains_ci", "findstr"), leaf("anchor", "CommandLine", "contains_ci", "> C:\\ProgramData\\")), "The anchor visibly records Windows Command Shell piping and filtering output into a staged file."),
             gt("mapped", ["T1059.003"], all_of(leaf("anchor", "NewProcessName", "endswith_ci", "\\cmd.exe"), leaf("anchor", "CommandLine", "contains_ci", " | "), leaf("anchor", "CommandLine", "contains_ci", "findstr"), leaf("context_1", "TargetFilename", "startswith_ci", "C:\\ProgramData\\"), relation("process_then_file", "process", "anchor", "file", "context_1")), "The contextual file event confirms the command-shell pipeline wrote its output to the staged destination."),
             ["A Sysmon file-create event follows the command-shell pipeline and uses the same process identity."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 11, "Reconnaissance output file created by cmd.exe")],
             "A diagnostic script can pipe output to a managed report file; approved script ownership and destination are counter-evidence.",
             "cmd.exe piping a local diagnostic command to the console without a staged output file.",
             ["Require a visible pipe plus filtering or staged output."], ["Do not use cmd.exe existence as the predicate."], old["TF_T1059_003_E"]),
    ]

    families += [
        spec("TF_T1053_005_A", "mapped_single", "test", "Scheduled task creation with hidden PowerShell payload",
             a(SECURITY, SECURITY_CHANNEL, 4698, "Security 4698 where TaskContent contains a hidden PowerShell encoded command and a public payload path"),
             gt("mapped", ["T1053.005"], all_of(leaf("anchor", "TaskName", "contains_ci", "\\Windows\\UpdateCheck"), leaf("anchor", "TaskContent", "contains_ci", "powershell.exe"), leaf("anchor", "TaskContent", "contains_ci", "-EncodedCommand"), leaf("anchor", "TaskContent", "contains_ci", "C:\\Users\\Public\\")), "The task-created event contains the task object, hidden PowerShell payload, and suspicious payload location in one visible record."),
             gt("mapped", ["T1053.005"], all_of(leaf("anchor", "TaskName", "contains_ci", "\\Windows\\UpdateCheck"), leaf("anchor", "TaskContent", "contains_ci", "-EncodedCommand"), leaf("context_1", "Image", "endswith_ci", "\\powershell.exe"), relation("process_then_task", "process", "context_1", "task", "anchor")), "The contextual PowerShell execution is linked back to the created task and confirms execution of the scheduled task payload."),
             ["A Sysmon PowerShell process event executes the task content after task creation."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "PowerShell process started by the scheduled task")],
             "A centrally managed software updater may create a hidden task; signed content, an approved task owner, and a Program Files path are counter-evidence.",
             "A visible Microsoft maintenance task running cleanmgr.exe from System32.",
             ["Use TaskName and TaskContent as separate observable fields."], ["Do not map every EID 4698 event."], old["TF_T1053_005_A"]),
        spec("TF_T1053_005_B", "mapped_single", "test", "Scheduled task created through COM with suspicious executable execution resolved by context",
             a(SECURITY, SECURITY_CHANNEL, 4698, "Security 4698 for a COM-created task whose content points to ProgramData"),
             gt("ambiguous", [], all_of(leaf("anchor", "TaskName", "contains_ci", "\\CacheRefresh"), leaf("anchor", "TaskContent", "contains_ci", "C:\\ProgramData\\")), "A COM-created task and an unknown ProgramData executable are dual-use; intent is not established in the single view."),
             gt("mapped", ["T1053.005"], all_of(leaf("anchor", "TaskName", "contains_ci", "\\CacheRefresh"), leaf("anchor", "TaskContent", "contains_ci", "C:\\ProgramData\\"), leaf("context_1", "Image", "contains_ci", "C:\\ProgramData\\"), relation("process_then_task", "process", "context_1", "task", "anchor")), "The contextual process execution is linked to the task object and establishes scheduled execution of the suspicious payload."),
             ["A process-create event runs the executable named in TaskContent after registration."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "Executable launched from the scheduled task content")],
             "A vendor cache task may use ProgramData; a signed publisher and an approved maintenance window are counter-evidence.",
             "A task registered for a known Microsoft component with a System32 executable.",
             ["Keep the task content and follow-on process linked."], ["Do not infer adversarial intent from COM registration alone."], old["TF_T1053_005_B"]),
        spec("TF_T1053_005_D", "mapped_single", "test", "Scheduled task with hidden boot trigger and public DLL payload",
             a(SECURITY, SECURITY_CHANNEL, 4698, "Security 4698 where TaskName is a misleading update name and TaskContent has a hidden boot trigger and rundll32 public DLL"),
             gt("mapped", ["T1053.005"], all_of(leaf("anchor", "TaskName", "contains_ci", "\\OneDriveUpdate"), leaf("anchor", "TaskContent", "contains_ci", "Hidden"), leaf("anchor", "TaskContent", "contains_ci", "rundll32.exe"), leaf("anchor", "TaskContent", "contains_ci", "C:\\Users\\Public\\")), "The scheduled-task record exposes a misleading name, hidden trigger, and public DLL execution payload."),
             gt("mapped", ["T1053.005"], all_of(leaf("anchor", "TaskName", "contains_ci", "\\OneDriveUpdate"), leaf("anchor", "TaskContent", "contains_ci", "rundll32.exe"), leaf("context_1", "Image", "endswith_ci", "\\rundll32.exe"), relation("process_then_task", "process", "context_1", "task", "anchor")), "The contextual rundll32 process is linked to the task content and confirms task-based execution."),
             ["A rundll32 process is created from the task content after registration."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "rundll32.exe launched by the task")],
             "A legitimate product may use a hidden boot task, but a signed DLL in a vendor directory is required for the benign interpretation.",
             "A Microsoft task with a canonical name and a System32 executable.",
             ["Require both task metadata and a concrete payload indicator."], ["Do not use a suspicious-looking name alone."], old["TF_T1053_005_D"]),
        spec("TF_T1053_005_E", "mapped_single", "test", "Scheduled task invokes PowerShell with intent resolved by a file and network chain",
             a(SECURITY, SECURITY_CHANNEL, 4698, "Security 4698 where TaskContent invokes PowerShell from an unknown path"),
             gt("ambiguous", [], all_of(leaf("anchor", "TaskContent", "contains_ci", "powershell.exe"), leaf("anchor", "TaskContent", "contains_ci", "-File")), "PowerShell in a task is observable, but the single view does not establish whether the task is authorized or adversarial."),
             gt("mapped", ["T1053.005"], all_of(leaf("anchor", "TaskContent", "contains_ci", "powershell.exe"), leaf("anchor", "TaskContent", "contains_ci", "-File"), leaf("context_1", "Image", "endswith_ci", "\\powershell.exe"), leaf("context_2", "DestinationPort", "eq", 443), relation("process_then_task", "process", "context_1", "task", "anchor"), relation("process_then_network", "process", "context_1", "network", "context_2")), "The contextual PowerShell execution and outbound connection are both linked to the task, resolving the task mechanism."),
             ["PowerShell executes the task script and opens a related outbound connection."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "PowerShell process started by task"), ctx("context_2", SYSMON, SYSMON_CHANNEL, 3, "Network connection from task-launched PowerShell")],
             "A scheduled compliance job may invoke PowerShell and contact an approved update endpoint; signed script and allowlisted destination are counter-evidence.",
             "A task running a documented PowerShell compliance script without network activity.",
             ["Keep the task content and process relationship explicit."], ["Do not label task creation as mapped without payload evidence."], old["TF_T1053_005_E"]),
    ]

    families += [
        spec("TF_T1543_003_A", "mapped_single", "test", "Windows service installed from a user-writable public executable",
             a(SECURITY, SECURITY_CHANNEL, 4697, "Security 4697 where ServiceFileName is a public executable, service starts automatically, and runs as LocalSystem"),
             gt("mapped", ["T1543.003"], all_of(leaf("anchor", "ServiceFileName", "contains_ci", "C:\\Users\\Public\\"), leaf("anchor", "ServiceStartType", "eq", "2"), leaf("anchor", "ServiceAccount", "contains_ci", "LocalSystem")), "Security 4697 directly records a service installation with a user-writable binary, automatic start, and a high-privilege service account."),
             gt("mapped", ["T1543.003"], all_of(leaf("anchor", "ServiceFileName", "contains_ci", "C:\\Users\\Public\\"), leaf("anchor", "ServiceName", "contains_ci", "Update"), leaf("context_1", "Image", "endswith_ci", "\\services.exe"), relation("process_then_service", "process", "context_1", "service", "anchor")), "The service manager process is linked to the 4697 installation and confirms the service creation path."),
             ["A services.exe process event is linked to the service installation event."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "Service manager process associated with installation")],
             "A portable enterprise agent may be installed from a controlled staging directory; signer, ACL, and deployment ticket are counter-evidence.",
             "A signed service installed under C:\\Program Files\\Contoso with a managed start type.",
             ["Use ServiceFileName, ServiceStartType, and ServiceAccount."], ["Do not map the mere existence of a service."], old["TF_T1543_003_A"]),
        spec("TF_T1543_003_B", "mapped_single", "test", "Windows service installed to launch a command shell payload",
             a(SECURITY, SECURITY_CHANNEL, 4697, "Security 4697 where ServiceFileName contains cmd.exe and a ProgramData payload"),
             gt("mapped", ["T1543.003"], all_of(leaf("anchor", "ServiceFileName", "contains_ci", "\\cmd.exe"), leaf("anchor", "ServiceFileName", "contains_ci", "C:\\ProgramData\\"), leaf("anchor", "ServiceStartType", "eq", "2")), "The 4697 record shows service installation whose image launches a command-shell payload from ProgramData."),
             gt("mapped", ["T1543.003"], all_of(leaf("anchor", "ServiceFileName", "contains_ci", "\\cmd.exe"), leaf("anchor", "ServiceName", "contains_ci", "Update"), leaf("context_1", "Image", "endswith_ci", "\\cmd.exe"), relation("process_then_service", "process", "context_1", "service", "anchor")), "A linked cmd.exe process confirms that the installed service executes its command-shell image."),
             ["A cmd.exe process is created by the service manager after installation."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "Command shell launched by installed service")],
             "An installer may register a command-shell wrapper; signed wrapper, Program Files path, and installer provenance are counter-evidence.",
             "A service installed by an MSI under Program Files with a vendor executable.",
             ["Require service metadata plus an executable path indicator."], ["Do not use ServiceName alone."], old["TF_T1543_003_B"]),
        spec("TF_T1543_003_D", "mapped_single", "test", "Windows service installed with a DLL entry point and LocalSystem account",
             a(SECURITY, SECURITY_CHANNEL, 4697, "Security 4697 where ServiceFileName uses svchost -k with an unusual DLL path and LocalSystem"),
             gt("mapped", ["T1543.003"], all_of(leaf("anchor", "ServiceFileName", "contains_ci", "svchost.exe"), leaf("anchor", "ServiceFileName", "contains_ci", "C:\\Users\\Public\\"), leaf("anchor", "ServiceAccount", "contains_ci", "LocalSystem")), "The service-install event records a service-hosted DLL path in a user-writable location under LocalSystem."),
             gt("mapped", ["T1543.003"], all_of(leaf("anchor", "ServiceFileName", "contains_ci", "svchost.exe"), leaf("anchor", "ServiceFileName", "contains_ci", "C:\\Users\\Public\\"), leaf("context_1", "TargetFilename", "contains_ci", ".dll"), relation("same_host", "events", ["context_1", "anchor"])), "The related DLL file event corroborates the installed service image and service-hosted execution."),
             ["A DLL file is created at the service image path before the service starts."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 11, "DLL written for the installed service")],
             "A vendor service may use svchost hosting, but the DLL must be signed and installed in a protected vendor directory.",
             "A signed Windows service DLL under System32 with a Microsoft service name.",
             ["Preserve ServiceFileName, ServiceAccount, and the linked DLL path."], ["Do not infer maliciousness from svchost.exe alone."], old["TF_T1543_003_D"]),
        spec("TF_T1543_003_E", "mapped_single", "test", "Windows service DLL sideload with execution resolved by context",
             a(SECURITY, SECURITY_CHANNEL, 4697, "Security 4697 where a service loads an unsigned-looking DLL from ProgramData"),
             gt("ambiguous", [], all_of(leaf("anchor", "ServiceFileName", "contains_ci", "svchost.exe"), leaf("anchor", "ServiceFileName", "contains_ci", "C:\\ProgramData\\")), "A service-hosted DLL under ProgramData is suspicious but the single service-install record does not prove abuse."),
             gt("mapped", ["T1543.003"], all_of(leaf("anchor", "ServiceFileName", "contains_ci", "svchost.exe"), leaf("anchor", "ServiceFileName", "contains_ci", "C:\\ProgramData\\"), leaf("context_1", "TargetFilename", "contains_ci", ".dll"), leaf("context_2", "Image", "endswith_ci", "\\svchost.exe"), relation("process_then_service", "process", "context_2", "service", "anchor")), "The DLL creation and subsequent service-host process together establish service-based execution of the staged image."),
             ["A DLL is created at the service path and svchost.exe later starts the service."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 11, "DLL created at service path"), ctx("context_2", SYSMON, SYSMON_CHANNEL, 1, "Service-host process after installation")],
             "A signed vendor service can use ProgramData; signature and an approved deployment record are required for the benign interpretation.",
             "A service installation with no follow-on file creation or service start evidence.",
             ["Retain the service image path and both contextual corroborators."], ["Do not map a service install solely from its name."], old["TF_T1543_003_E"]),
    ]

    local_hosts = {"allowed_host_roles": ["workstation", "member_server"], "forbidden_hosts": ["DC01"]}
    families += [
        spec("TF_T1136_001_A", "mapped_single", "test", "Local account created through net user with a service-like name",
             a(SECURITY, SECURITY_CHANNEL, 4688, "Security 4688 where cmd.exe runs net user /add for a never-expiring service-like account"),
             gt("mapped", ["T1136.001"], all_of(leaf("anchor", "NewProcessName", "endswith_ci", "\\cmd.exe"), leaf("anchor", "CommandLine", "contains_ci", "net user"), leaf("anchor", "CommandLine", "contains_ci", "/add"), leaf("anchor", "CommandLine", "contains_ci", "/expires:never")), "The process event visibly records creation of a local account through net user with persistence-oriented account parameters."),
             gt("mapped", ["T1136.001"], all_of(leaf("anchor", "NewProcessName", "endswith_ci", "\\cmd.exe"), leaf("anchor", "CommandLine", "contains_ci", "net user"), leaf("context_1", "TargetUserName", "endswith_ci", "$"), relation("same_host", "events", ["anchor", "context_1"])), "The contextual account-created event links the net user command to the created local account."),
             ["Security 4720 confirms the account named by the command line was created on the same host."],
             [ctx("context_1", SECURITY, SECURITY_CHANNEL, 4720, "Local account creation corresponding to net user command")],
             "A service account created through an approved provisioning runbook is a benign alternative; ticket, owner, and managed naming are counter-evidence.",
             "A help-desk operator creates a named employee account during onboarding.",
             ["Generate only on a workstation or member server."], ["Never use DC01 for this family."], old["TF_T1136_001_A"], host_constraints=local_hosts),
        spec("TF_T1136_001_B", "mapped_single", "test", "Local account creation followed by suspicious credential-use context",
             a(SECURITY, SECURITY_CHANNEL, 4720, "Security 4720 where TargetUserName is a service-like name and SubjectUserName is an unexpected creator"),
             gt("ambiguous", [], all_of(leaf("anchor", "TargetUserName", "contains_ci", "svc_"), leaf("anchor", "SubjectUserName", "neq", "Administrator")), "EID 4720 proves account creation but the account name and creator alone do not establish adversarial intent."),
             gt("mapped", ["T1136.001"], all_of(leaf("anchor", "TargetUserName", "contains_ci", "svc_"), leaf("anchor", "SubjectUserName", "neq", "Administrator"), leaf("context_1", "CommandLine", "contains_ci", "net localgroup administrators"), relation("same_user", "events", ["anchor", "context_1"])), "The account creation is linked to immediate privileged-group use by the same creator session, providing contextual evidence for local-account abuse."),
             ["A related process adds the new account to the local Administrators group under the same logon."],
             [ctx("context_1", SECURITY, SECURITY_CHANNEL, 4688, "Privileged group membership command from the account creator session")],
             "Automated workstation provisioning may create a service account and add it to a group; approved image-building provenance is counter-evidence.",
             "A normal employee account created by an administrator without group escalation.",
             ["Use workstation or member-server host roles only."], ["Do not treat EID 4720 alone as mapped."], old["TF_T1136_001_B"], host_constraints=local_hosts),
        spec("TF_T1136_001_C", "mapped_single", "test", "PowerShell New-LocalUser provisioning with non-expiring account options",
             a(SYSMON, SYSMON_CHANNEL, 1, "Sysmon process creation where pwsh.exe invokes New-LocalUser with AccountNeverExpires"),
             gt("mapped", ["T1136.001"], all_of(leaf("anchor", "Image", "endswith_ci", "\\pwsh.exe"), leaf("anchor", "CommandLine", "contains_ci", "New-LocalUser"), leaf("anchor", "CommandLine", "contains_ci", "AccountNeverExpires")), "The PowerShell process command line explicitly invokes New-LocalUser with a persistence-oriented option."),
             gt("mapped", ["T1136.001"], all_of(leaf("anchor", "Image", "endswith_ci", "\\pwsh.exe"), leaf("anchor", "CommandLine", "contains_ci", "New-LocalUser"), leaf("context_1", "TargetUserName", "contains_ci", "svc_"), relation("same_host", "events", ["anchor", "context_1"])), "The contextual 4720 record links the PowerShell provisioning command to the created local account."),
             ["Security 4720 records creation of the service-like account after the PowerShell command."],
             [ctx("context_1", SECURITY, SECURITY_CHANNEL, 4720, "Account created by New-LocalUser")],
             "Golden-image provisioning may use New-LocalUser; approved image build identity and protected script location are counter-evidence.",
             "New-LocalUser used for a time-bounded test account with expiration configured.",
             ["Use FILESVR01, APPSVR01, or a workstation; never DC01."], ["Do not map ordinary PowerShell without New-LocalUser evidence."], old["TF_T1136_001_C"], host_constraints=local_hosts),
        spec("TF_T1136_001_E", "mapped_single", "test", "Local account with administrative group use resolved by context",
             a(SECURITY, SECURITY_CHANNEL, 4720, "Security 4720 where a newly created local account has a generic name and ordinary creator context"),
             gt("ambiguous", [], all_of(leaf("anchor", "TargetUserName", "contains_ci", "backup"), leaf("anchor", "SubjectUserName", "contains_ci", "helpdesk")), "The account event is compatible with both authorized backup provisioning and abuse, so the single view is ambiguous."),
             gt("mapped", ["T1136.001"], all_of(leaf("anchor", "TargetUserName", "contains_ci", "backup"), leaf("context_1", "CommandLine", "contains_ci", "net localgroup administrators"), leaf("context_1", "CommandLine", "contains_ci", " /add"), relation("same_logon", "events", ["anchor", "context_1"])), "Immediate administrator-group addition under the account-creation logon resolves the local-account abuse interpretation."),
             ["A same-logon process adds the new account to the local Administrators group."],
             [ctx("context_1", SECURITY, SECURITY_CHANNEL, 4688, "Administrative group addition after account creation")],
             "A backup service account may legitimately be added to a local group; approved change control and least-privilege group are counter-evidence.",
             "A local backup account created and left in the Users group only.",
             ["Constrain hosts to workstation/member server."], ["Do not use DC01 or infer intent from account creation alone."], old["TF_T1136_001_E"], host_constraints=local_hosts),
    ]

    families += [
        spec("TF_T1547_001_A", "mapped_single", "test", "Run key set to execute a user-writable executable",
             a(SYSMON, SYSMON_CHANNEL, 13, "Sysmon 13 where TargetObject is a Run key and Details points to Users/Public executable"),
             gt("mapped", ["T1547.001"], all_of(leaf("anchor", "TargetObject", "contains_ci", "\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\"), leaf("anchor", "Details", "contains_ci", "C:\\Users\\Public\\"), leaf("anchor", "Details", "endswith_ci", ".exe")), "The registry event directly records a Run-key persistence value pointing to a user-writable executable."),
             gt("mapped", ["T1547.001"], all_of(leaf("anchor", "TargetObject", "contains_ci", "\\CurrentVersion\\Run\\"), leaf("anchor", "Details", "contains_ci", "C:\\Users\\Public\\"), leaf("context_1", "Image", "endswith_ci", "\\reg.exe"), relation("process_then_registry", "process", "context_1", "registry", "anchor")), "The reg.exe writer event confirms the Run-key mutation and its persistence target."),
             ["A reg.exe process event writes the Run value immediately before the Sysmon registry event."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "reg.exe process that writes the Run key")],
             "A legitimate auto-start helper may use a Run key; signed binary and Program Files path are counter-evidence.",
             "A signed updater registered under HKCU Run with a protected vendor path.",
             ["Use TargetObject and Details together."], ["Do not map any registry write without a startup location and payload."], old["TF_T1547_001_A"]),
        spec("TF_T1547_001_B", "mapped_single", "test", "Startup-folder shortcut created for a public executable",
             a(SYSMON, SYSMON_CHANNEL, 11, "Sysmon 11 where TargetFilename is a Startup-folder shortcut and Image is explorer.exe"),
             gt("mapped", ["T1547.001"], all_of(leaf("anchor", "TargetFilename", "contains_ci", "\\Start Menu\\Programs\\Startup\\"), leaf("anchor", "TargetFilename", "endswith_ci", ".lnk"), leaf("anchor", "Image", "endswith_ci", "\\explorer.exe")), "The file-create event records a shortcut placed in the per-user Startup folder, a direct persistence location."),
             gt("mapped", ["T1547.001"], all_of(leaf("anchor", "TargetFilename", "contains_ci", "\\Startup\\"), leaf("anchor", "TargetFilename", "endswith_ci", ".lnk"), leaf("context_1", "Image", "endswith_ci", "\\explorer.exe"), relation("same_user", "events", ["anchor", "context_1"])), "A related explorer.exe event for the same user confirms the Startup-folder artifact is in the user startup path."),
             ["Explorer processes the Startup-folder shortcut at the next logon."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "Explorer process after Startup-folder shortcut creation")],
             "Enterprise login software may install a signed Startup shortcut; publisher and protected target path are counter-evidence.",
             "A shortcut created in Downloads or Desktop rather than the Startup folder.",
             ["Require the Startup-folder path and shortcut/file evidence."], ["Do not use only a .lnk extension."], old["TF_T1547_001_B"]),
        spec("TF_T1547_001_C", "mapped_single", "test", "PowerShell writes a RunOnce value to a public script",
             a(SYSMON, SYSMON_CHANNEL, 13, "Sysmon 13 where PowerShell writes a RunOnce value pointing to a public script"),
             gt("mapped", ["T1547.001"], all_of(leaf("anchor", "Image", "endswith_ci", "\\powershell.exe"), leaf("anchor", "TargetObject", "contains_ci", "\\RunOnce\\"), leaf("anchor", "Details", "contains_ci", "C:\\Users\\Public\\"), leaf("anchor", "Details", "endswith_ci", ".ps1")), "The registry event records PowerShell creating a RunOnce persistence value with a user-writable script target."),
             gt("mapped", ["T1547.001"], all_of(leaf("anchor", "TargetObject", "contains_ci", "\\RunOnce\\"), leaf("anchor", "Details", "contains_ci", "C:\\Users\\Public\\"), leaf("context_1", "TargetFilename", "endswith_ci", ".ps1"), relation("same_process", "events", ["anchor", "context_1"])), "The file event corroborates the script target used by the RunOnce value."),
             ["The referenced PowerShell script is created before the RunOnce registry write."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 11, "PowerShell script written for RunOnce execution")],
             "A software installer can use RunOnce for a one-time setup; signed script and managed installer parent are counter-evidence.",
             "A PowerShell script in a protected installer directory with no Run/RunOnce mutation.",
             ["Keep Image, TargetObject, and Details in the predicate."], ["Do not infer persistence from PowerShell alone."], old["TF_T1547_001_C"]),
        spec("TF_T1547_001_E", "mapped_single", "test", "RunOnce mutation with persistence intent resolved by follow-on execution",
             a(SYSMON, SYSMON_CHANNEL, 13, "Sysmon 13 where an unknown user process writes RunOnce to an AppData executable"),
             gt("ambiguous", [], all_of(leaf("anchor", "TargetObject", "contains_ci", "\\RunOnce\\"), leaf("anchor", "Details", "contains_ci", "AppData"), leaf("anchor", "Details", "endswith_ci", ".exe")), "RunOnce plus an AppData executable is dual-use; the single event lacks enough context to distinguish software setup from persistence abuse."),
             gt("mapped", ["T1547.001"], all_of(leaf("anchor", "TargetObject", "contains_ci", "\\RunOnce\\"), leaf("anchor", "Details", "contains_ci", "AppData"), leaf("context_1", "TargetFilename", "contains_ci", "AppData"), leaf("context_2", "Image", "endswith_ci", ".exe"), relation("process_then_registry", "process", "context_2", "registry", "anchor")), "File creation at the target path followed by execution of the RunOnce payload establishes startup persistence in context."),
             ["The AppData executable is created and then executed after the RunOnce registry mutation."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 11, "RunOnce payload file creation"), ctx("context_2", SYSMON, SYSMON_CHANNEL, 1, "RunOnce payload execution")],
             "A signed per-user updater may use RunOnce; verified signer and an installer parent are counter-evidence.",
             "A RunOnce value whose target is a signed executable under Program Files.",
             ["Keep both file and process corroboration in contextual evidence."], ["Do not map RunOnce from the registry path alone."], old["TF_T1547_001_E"]),
    ]

    eventlog_anchor = a(EVENTLOG, SECURITY_CHANNEL, 1102, "Security-channel Windows Eventlog EID 1102 with a non-empty subject user")
    families += [
        spec("TF_T1685_005_A", "mapped_single", "test", "Security audit log cleared by wevtutil, resolved only with process context",
             eventlog_anchor,
             gt("ambiguous", [], all_of(leaf("anchor", "EventID", "eq", 1102), leaf("anchor", "SubjectUserName", "neq", "")), "EID 1102 establishes that the Security audit log was cleared, but does not identify wevtutil or adversarial intent."),
             gt("mapped", ["T1685.005"], all_of(leaf("anchor", "EventID", "eq", 1102), leaf("context_1", "NewProcessName", "endswith_ci", "\\wevtutil.exe"), leaf("context_1", "CommandLine", "contains_ci", " cl Security"), relation("temporal_before", "before", "context_1", "after", "anchor"), relation("same_logon", "events", ["context_1", "anchor"])), "The linked wevtutil process explicitly clears the Security log and supplies the mechanism missing from EID 1102."),
             ["A Security 4688 process event for wevtutil.exe precedes EID 1102 in the same logon."],
             [ctx("context_1", SECURITY, SECURITY_CHANNEL, 4688, "wevtutil.exe process that clears the Security log")],
             "Authorized log maintenance may use wevtutil; a scheduled maintenance identity and approved change window are counter-evidence.",
             "EID 1102 generated by a documented log-retention maintenance job with no suspicious process chain.",
             ["Keep the EID 1102 anchor provider as Microsoft-Windows-Eventlog."], ["Do not infer wevtutil from EID 1102 alone."], old["TF_T1685_005_A"], comparison_ids=["T1685.005"]),
        spec("TF_T1685_005_B", "mapped_single", "test", "Security audit log cleared by PowerShell Clear-EventLog",
             a(EVENTLOG, SECURITY_CHANNEL, 1102, "Security-channel Windows Eventlog EID 1102 for a non-empty subject user"),
             gt("ambiguous", [], all_of(leaf("anchor", "EventID", "eq", 1102), leaf("anchor", "SubjectLogonId", "neq", "")), "The audit-log-cleared event is genuine telemetry but cannot identify a PowerShell mechanism from the anchor alone."),
             gt("mapped", ["T1685.005"], all_of(leaf("anchor", "EventID", "eq", 1102), leaf("context_1", "Image", "endswith_ci", "\\powershell.exe"), any_of(leaf("context_1", "CommandLine", "contains_ci", "Clear-EventLog"), leaf("context_1", "CommandLine", "contains_ci", "wevtutil")), relation("temporal_before", "before", "context_1", "after", "anchor"), relation("same_logon", "events", ["context_1", "anchor"])), "PowerShell Clear-EventLog or equivalent log-clear syntax is visible in the linked process event, so T1685.005 is supported."),
             ["PowerShell executes Clear-EventLog under the same subject logon before EID 1102."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "PowerShell log-clear command")],
             "A compliance script may clear a test log during rotation; maintenance identity and an approved rotation record are counter-evidence.",
             "EID 1102 with no process event capable of identifying the mechanism.",
             ["Use Eventlog provider, Security channel, and EID 1102 for the anchor."], ["Never claim PowerShell from EID 1102 alone."], old["TF_T1685_005_B"], comparison_ids=["T1685.005"]),
        spec("TF_T1685_005_C", "mapped_single", "test", "Security audit log cleared through an event-log API call",
             a(EVENTLOG, SECURITY_CHANNEL, 1102, "Security-channel Windows Eventlog EID 1102 with populated subject metadata"),
             gt("ambiguous", [], all_of(leaf("anchor", "EventID", "eq", 1102), leaf("anchor", "SubjectUserName", "neq", "")), "The anchor only reports the result of log clearing; an API mechanism is not visible in EID 1102."),
             gt("mapped", ["T1685.005"], all_of(leaf("anchor", "EventID", "eq", 1102), leaf("context_1", "CommandLine", "contains_ci", "EvtClearLog"), leaf("context_1", "NewProcessName", "endswith_ci", ".exe"), relation("temporal_before", "before", "context_1", "after", "anchor"), relation("same_logon", "events", ["context_1", "anchor"])), "The linked process command explicitly calls the event-log clear API and is temporally related to EID 1102."),
             ["A process invoking EvtClearLog or an equivalent event-log API precedes EID 1102."],
             [ctx("context_1", SECURITY, SECURITY_CHANNEL, 4688, "Process invoking event-log clear API")],
             "A monitoring or test harness may call the API during approved maintenance; account, signer, and change record are counter-evidence.",
             "EID 1102 with only the subject account and no mechanism evidence.",
             ["Require an explicit process/API indicator in contextual evidence."], ["Do not map API clear from EventID 1102 alone."], old["TF_T1685_005_C"], comparison_ids=["T1685.005"]),
        spec("TF_T1685_005_E", "mapped_single", "test", "Security audit log clearing after suspicious remote session activity",
             a(EVENTLOG, SECURITY_CHANNEL, 1102, "Security-channel Windows Eventlog EID 1102 with a populated logon identity"),
             gt("ambiguous", [], all_of(leaf("anchor", "EventID", "eq", 1102), leaf("anchor", "SubjectLogonId", "neq", "")), "EID 1102 confirms clearing but is insufficient to attribute a mechanism or adversarial context."),
             gt("mapped", ["T1685.005"], all_of(leaf("anchor", "EventID", "eq", 1102), leaf("context_1", "DestinationPort", "eq", 445), leaf("context_2", "NewProcessName", "endswith_ci", "\\wevtutil.exe"), leaf("context_2", "CommandLine", "contains_ci", " cl Security"), relation("temporal_before", "before", "context_1", "after", "anchor"), relation("temporal_before", "before", "context_2", "after", "anchor"), relation("same_logon", "events", ["context_2", "anchor"])), "Remote-session evidence plus an explicit wevtutil clear command supplies both contextual mechanism and suspicious sequence."),
             ["A remote SMB session is followed by wevtutil clearing the Security log on the same host."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 3, "Remote session connection"), ctx("context_2", SECURITY, SECURITY_CHANNEL, 4688, "wevtutil clear process after remote session")],
             "Remote administration for approved incident response may clear a log; operator authorization and maintenance record are counter-evidence.",
             "An isolated EID 1102 event from a scheduled rotation job.",
             ["Keep mechanism and remote-session evidence separate."], ["Do not infer lateral movement or wevtutil from EID 1102 alone."], old["TF_T1685_005_E"], comparison_ids=["T1685.005"]),
    ]

    families += [
        spec("TF_T1105_A", "mapped_single", "test", "Certutil downloads a payload to ProgramData",
             a(SYSMON, SYSMON_CHANNEL, 1, "Sysmon process creation where certutil uses -urlcache -split -f with an external URL and output path"),
             gt("mapped", ["T1105"], all_of(leaf("anchor", "Image", "endswith_ci", "\\certutil.exe"), leaf("anchor", "CommandLine", "contains_ci", "-urlcache"), leaf("anchor", "CommandLine", "contains_ci", "-split"), leaf("anchor", "CommandLine", "contains_ci", "https://files.example.invalid/"), leaf("anchor", "CommandLine", "contains_ci", "C:\\ProgramData\\")), "The process command line contains concrete certutil download syntax, source URL, and destination path."),
             gt("mapped", ["T1105"], all_of(leaf("anchor", "Image", "endswith_ci", "\\certutil.exe"), leaf("anchor", "CommandLine", "contains_ci", "-urlcache"), leaf("context_1", "TargetFilename", "startswith_ci", "C:\\ProgramData\\"), relation("process_then_file", "process", "anchor", "file", "context_1")), "The linked file-create event confirms the downloaded artifact was written to the declared destination."),
             ["A Sysmon file-create event follows certutil and uses the same process identity."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 11, "Downloaded file created by certutil")],
             "A certificate-management job may fetch a CRL; a trusted endpoint, expected filename, and managed signer are counter-evidence.",
             "certutil inspecting a local certificate store without a URL or output path.",
             ["Require tool syntax, source, and destination evidence."], ["Do not map certutil or a network connection alone."], old["TF_T1105_A"]),
        spec("TF_T1105_B", "mapped_single", "test", "BITSAdmin transfers a remote file to a local staging path",
             a(SYSMON, SYSMON_CHANNEL, 1, "Sysmon process creation where bitsadmin /transfer contains an external URL and local output path"),
             gt("mapped", ["T1105"], all_of(leaf("anchor", "Image", "endswith_ci", "\\bitsadmin.exe"), leaf("anchor", "CommandLine", "contains_ci", "/transfer"), leaf("anchor", "CommandLine", "contains_ci", "https://files.example.invalid/"), leaf("anchor", "CommandLine", "contains_ci", "C:\\ProgramData\\")), "The BITSAdmin command visibly specifies a transfer job, remote source, and local destination."),
             gt("mapped", ["T1105"], all_of(leaf("anchor", "Image", "endswith_ci", "\\bitsadmin.exe"), leaf("anchor", "CommandLine", "contains_ci", "/transfer"), leaf("context_1", "TargetFilename", "startswith_ci", "C:\\ProgramData\\"), relation("process_then_file", "process", "anchor", "file", "context_1")), "The resulting file event establishes that the BITS transfer produced a local file."),
             ["A file is created at the BITS output path after the transfer process."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 11, "BITS output file created")],
             "Enterprise software distribution may use BITS; an approved update URL, signed installer, and managed destination are counter-evidence.",
             "BITSAdmin listing jobs or querying status without a transfer source and destination.",
             ["Keep /transfer, URL, and output path visible."], ["Do not infer transfer from bitsadmin presence alone."], old["TF_T1105_B"]),
        spec("TF_T1105_C", "mapped_single", "test", "Curl downloads a remote executable to a local path",
             a(SYSMON, SYSMON_CHANNEL, 1, "Sysmon process creation where curl uses a URL and -o output path"),
             gt("mapped", ["T1105"], all_of(leaf("anchor", "Image", "endswith_ci", "\\curl.exe"), leaf("anchor", "CommandLine", "contains_ci", "https://files.example.invalid/"), leaf("anchor", "CommandLine", "contains_ci", " -o "), leaf("anchor", "CommandLine", "contains_ci", "C:\\ProgramData\\")), "The curl command explicitly carries source and destination arguments for a transfer."),
             gt("mapped", ["T1105"], all_of(leaf("anchor", "Image", "endswith_ci", "\\curl.exe"), leaf("anchor", "CommandLine", "contains_ci", " -o "), leaf("context_1", "TargetFilename", "startswith_ci", "C:\\ProgramData\\"), relation("process_then_file", "process", "anchor", "file", "context_1")), "The file-create event corroborates the local artifact produced by curl."),
             ["The output file is created after the curl process connects to the external URL."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 11, "Curl output file")],
             "A documented update agent may use curl; allowlisted endpoint and signed output are counter-evidence.",
             "curl querying an internal health endpoint without an output path or file creation.",
             ["Require URL plus explicit output path or file linkage."], ["Do not map network-only evidence."], old["TF_T1105_C"]),
        spec("TF_T1105_D", "mapped_single", "test", "Network-only connection resolved to an actual transfer by context",
             a(SYSMON, SYSMON_CHANNEL, 3, "Sysmon EID 3 from a process to TCP/443 at an example.invalid address"),
             gt("ambiguous", [], all_of(leaf("anchor", "DestinationPort", "eq", 443), leaf("anchor", "DestinationIp", "in", ["198.51.100.20", "203.0.113.20"])), "Network-only Sysmon EID 3 shows a connection but not whether bytes were a tool transfer."),
             gt("mapped", ["T1105"], all_of(leaf("anchor", "DestinationPort", "eq", 443), leaf("context_1", "CommandLine", "contains_ci", "https://files.example.invalid/"), leaf("context_1", "CommandLine", "contains_ci", " -o "), leaf("context_2", "TargetFilename", "startswith_ci", "C:\\ProgramData\\"), relation("process_then_network", "process", "context_1", "network", "anchor"), relation("network_then_file", "network", "anchor", "file", "context_2")), "The contextual process command exposes download syntax and the linked file event confirms the transfer result."),
             ["A process-create event with source and destination is followed by file creation at the destination."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "Process command that initiates the transfer"), ctx("context_2", SYSMON, SYSMON_CHANNEL, 11, "File created after the network connection")],
             "An authorized browser or updater can make the connection and download a file; signed process and allowlisted endpoint are counter-evidence.",
             "A TCP connection with no process command or file artifact.",
             ["Keep network-only single view ambiguous."], ["Do not map EID 3 without transfer evidence."], old["TF_T1105_D"]),
    ]

    # Test multi-label families: contextual evidence is a mapping per
    # technique, not one global predicate shared by all labels.
    families += [
        spec("TF_MULTI_A", "mapped_multi", "test", "PowerShell download followed by scheduled-task registration",
             a(SYSMON, SYSMON_CHANNEL, 1, "PowerShell process uses a download URL and writes a task-registration command"),
             gt("mapped", ["T1059.001"], all_of(leaf("anchor", "Image", "endswith_ci", "\\powershell.exe"), leaf("anchor", "CommandLine", "contains_ci", "Invoke-WebRequest")), "The single view independently supports PowerShell execution; the download and task behaviors are contextual."),
             gt("mapped", ["T1059.001", "T1105", "T1053.005"], {
                 "T1059.001": all_of(leaf("anchor", "Image", "endswith_ci", "\\powershell.exe"), leaf("anchor", "CommandLine", "contains_ci", "Invoke-WebRequest")),
                 "T1105": all_of(leaf("anchor", "CommandLine", "contains_ci", "https://files.example.invalid/"), leaf("context_1", "TargetFilename", "startswith_ci", "C:\\ProgramData\\"), relation("process_then_file", "process", "anchor", "file", "context_1")),
                 "T1053.005": all_of(leaf("context_2", "TaskName", "contains_ci", "\\CacheRefresh"), leaf("context_2", "TaskContent", "contains_ci", "C:\\ProgramData\\"), relation("process_then_task", "process", "anchor", "task", "context_2")),
             }, "Each contextual label has separate evidence: PowerShell syntax, a downloaded file, and a scheduled-task object."),
             ["The same PowerShell process downloads a file and registers a task that uses the downloaded path."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 11, "Downloaded file"), ctx("context_2", SECURITY, SECURITY_CHANNEL, 4698, "Scheduled task registered by PowerShell")],
             "An enterprise deployment orchestrator can perform all three actions; signed script, managed endpoint, and approved change are counter-evidence.",
             "PowerShell downloads a file without creating a task.", ["Keep per-technique contextual predicates independent."], ["Do not use one predicate for all labels."], old["TF_MULTI_A"]),
        spec("TF_MULTI_B", "mapped_multi", "test", "Suspicious service installation followed by explicit audit-log clearing",
             a(SECURITY, SECURITY_CHANNEL, 4697, "Security 4697 installs a public-path service with a high-privilege account"),
             gt("mapped", ["T1543.003"], all_of(leaf("anchor", "ServiceFileName", "contains_ci", "C:\\Users\\Public\\"), leaf("anchor", "ServiceAccount", "contains_ci", "LocalSystem")), "The single service-install event independently supports Windows Service."),
             gt("mapped", ["T1543.003", "T1685.005"], {
                 "T1543.003": all_of(leaf("anchor", "ServiceFileName", "contains_ci", "C:\\Users\\Public\\"), leaf("anchor", "ServiceAccount", "contains_ci", "LocalSystem"), relation("process_then_service", "process", "context_1", "service", "anchor")),
                 "T1685.005": all_of(leaf("context_2", "EventID", "eq", 1102), leaf("context_1", "CommandLine", "contains_ci", "wevtutil"), leaf("context_1", "CommandLine", "contains_ci", " cl Security"), relation("temporal_before", "before", "context_1", "after", "context_2"), relation("same_logon", "events", ["context_1", "context_2"])),
             }, "Service evidence and log-clear evidence are independently visible in the contextual view."),
             ["A service process is followed by wevtutil clearing the Security log."],
             [ctx("context_1", SECURITY, SECURITY_CHANNEL, 4688, "Service installation or wevtutil process"), ctx("context_2", EVENTLOG, SECURITY_CHANNEL, 1102, "Security audit log cleared")],
             "A managed installer and log-retention job may create a service and rotate logs; signer, schedule, and ticket are counter-evidence.",
             "A service install with no EID 1102 or clear command.", ["Use Eventlog provider for contextual EID 1102."], ["Do not let the service predicate justify log clearing."], old["TF_MULTI_B"]),
        spec("TF_MULTI_C", "mapped_multi", "test", "Local account creation followed by Run-key persistence",
             a(SECURITY, SECURITY_CHANNEL, 4720, "Security 4720 creates a service-like local account on an allowed host"),
             gt("mapped", ["T1136.001"], all_of(leaf("anchor", "TargetUserName", "contains_ci", "svc_"), leaf("anchor", "SubjectUserName", "neq", "")), "The single view supports local-account creation but does not yet show the persistence behavior."),
             gt("mapped", ["T1136.001", "T1547.001"], {
                 "T1136.001": all_of(leaf("anchor", "TargetUserName", "contains_ci", "svc_"), leaf("anchor", "SubjectUserName", "neq", ""), relation("same_user", "events", ["anchor", "context_1"])),
                 "T1547.001": all_of(leaf("context_1", "TargetObject", "contains_ci", "\\CurrentVersion\\Run\\"), leaf("context_1", "Details", "contains_ci", "svc_"), relation("temporal_before", "before", "anchor", "after", "context_1"), relation("same_user", "events", ["anchor", "context_1"])),
             }, "The account event and Run-key mutation have separate predicates, supporting the two contextual techniques."),
             ["The newly created local account is used as the Run-key payload identity."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 13, "Run-key value referencing the created account payload")],
             "Workstation provisioning may create an account and startup helper; image-build provenance and signed software are counter-evidence.",
             "An account creation event without a startup persistence mutation.", ["Use allowed local-account hosts only."], ["Do not use one account predicate for registry persistence."], old["TF_MULTI_C"], host_constraints=local_hosts),
        spec("TF_MULTI_D", "mapped_multi", "test", "Command shell downloads a file and executes it",
             a(SECURITY, SECURITY_CHANNEL, 4688, "Security 4688 where cmd.exe invokes curl with URL and output path"),
             gt("mapped", ["T1059.003"], all_of(leaf("anchor", "NewProcessName", "endswith_ci", "\\cmd.exe"), leaf("anchor", "CommandLine", "contains_ci", " /c ")), "The single view independently supports Windows Command Shell execution."),
             gt("mapped", ["T1059.003", "T1105"], {
                 "T1059.003": all_of(leaf("anchor", "NewProcessName", "endswith_ci", "\\cmd.exe"), leaf("anchor", "CommandLine", "contains_ci", " /c "), leaf("anchor", "CommandLine", "contains_ci", "curl")),
                 "T1105": all_of(leaf("anchor", "CommandLine", "contains_ci", "https://files.example.invalid/"), leaf("anchor", "CommandLine", "contains_ci", " -o "), leaf("context_1", "TargetFilename", "startswith_ci", "C:\\ProgramData\\"), relation("process_then_file", "process", "anchor", "file", "context_1")),
             }, "Command-shell execution and the concrete curl transfer each have separate evidence in the contextual view."),
             ["A Sysmon file event confirms the curl output path after the cmd.exe process."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 11, "Curl output file")],
             "A deployment wrapper can use cmd.exe and curl for an approved package; signed wrapper and allowlisted URL are counter-evidence.",
             "cmd.exe executes curl against an internal endpoint without a file output.", ["Keep transfer evidence separate from shell evidence."], ["Do not use network-only evidence for T1105."], old["TF_MULTI_D"]),
    ]

    benign_specs = [
        ("TF_UNMAP_A", "Routine signed PowerShell maintenance", SYSMON, SYSMON_CHANNEL, 1, "PowerShell -NoProfile -File C:\\Program Files\\Contoso\\maintenance.ps1", ["PowerShell", "-NoProfile", "maintenance.ps1"], "The signed maintenance script is under Program Files and has no encoded, download, persistence, or account-creation indicator."),
        ("TF_UNMAP_B", "Normal cmd-based DNS administration", SECURITY, SECURITY_CHANNEL, 4688, "cmd.exe /c ipconfig /flushdns", ["cmd.exe", "ipconfig", "/flushdns"], "The command is a routine local diagnostic action with no staged payload, persistence, transfer, or account mutation."),
        ("TF_UNMAP_C", "Standard scheduled disk-maintenance task", SECURITY, SECURITY_CHANNEL, 4698, "\\Microsoft\\Windows\\DiskCleanup with cleanmgr.exe", ["DiskCleanup", "cleanmgr.exe", "System32"], "The task name and System32 cleanmgr.exe content identify routine Windows maintenance."),
        ("TF_UNMAP_D", "Legitimate signed service deployment", SECURITY, SECURITY_CHANNEL, 4697, "ContosoAgent.exe from C:\\Program Files\\Contoso", ["ContosoAgent.exe", "Program Files", "LocalSystem"], "The service binary is in a protected vendor directory and its deployment is a normal managed installation."),
        ("TF_UNMAP_E", "Expected employee local-account provisioning", SECURITY, SECURITY_CHANNEL, 4720, "TargetUserName=jdoe created by helpdesk", ["jdoe", "helpdesk", "employee"], "The account name and help-desk creator match ordinary onboarding and show no persistence or privilege escalation."),
        ("TF_UNMAP_PS", "Routine PowerShell service inventory", SYSMON, SYSMON_CHANNEL, 1, "powershell.exe -Command Get-Service", ["Get-Service", "NoProfile", "powershell.exe"], "PowerShell inventory is ordinary administration with no obfuscation, transfer, or persistence evidence."),
        ("TF_UNMAP_CMD", "Routine cmd directory listing", SECURITY, SECURITY_CHANNEL, 4688, "cmd.exe /c dir C:\\Program Files\\Contoso", ["cmd.exe", "dir", "Program Files"], "The command shell lists a managed software directory and does not stage or execute a payload."),
        ("TF_UNMAP_SCHTASK", "Scheduled Windows update maintenance", SECURITY, SECURITY_CHANNEL, 4698, "\\Contoso\\UpdateMaintenance runs signed updater.exe", ["UpdateMaintenance", "updater.exe", "Program Files"], "The task content is a signed vendor updater in a protected path and is tied to maintenance context."),
        ("TF_UNMAP_SVC", "Signed service restart after patching", SECURITY, SECURITY_CHANNEL, 4697, "ContosoPatch service from Program Files", ["ContosoPatch", "Program Files", "LocalService"], "The service is a signed patching component in a protected location and has no public-path payload."),
        ("TF_UNMAP_ACCT", "Normal local backup-account provisioning", SECURITY, SECURITY_CHANNEL, 4720, "backupsvc created by Administrator", ["backupsvc", "Administrator", "backup"], "The service account is created by the approved administrator provisioning identity without immediate group escalation."),
        ("TF_UNMAP_REG", "Legitimate startup application registration", SYSMON, SYSMON_CHANNEL, 13, "OneDrive Run value under Program Files", ["CurrentVersion\\Run", "Program Files", "OneDrive"], "A signed startup application under Program Files is an affirmative benign startup scenario."),
        ("TF_UNMAP_EVTCLR", "Authorized log-retention maintenance", EVENTLOG, SECURITY_CHANNEL, 1102, "Security log rotation by SYSTEM", ["SYSTEM", "maintenance", "rotation"], "EID 1102 is paired with a SYSTEM maintenance process and an approved log-rotation context."),
    ]
    benign_predicates = {
        "TF_UNMAP_A": all_of(
            leaf("anchor", "Image", "endswith_ci", "\\powershell.exe"),
            leaf("anchor", "CommandLine", "contains_ci", "-NoProfile -File"),
            leaf("anchor", "CommandLine", "contains_ci", "C:\\Program Files\\Contoso\\maintenance.ps1"),
            leaf("anchor", "ParentImage", "endswith_ci", "\\taskeng.exe"),
        ),
        "TF_UNMAP_B": all_of(
            leaf("anchor", "NewProcessName", "endswith_ci", "\\cmd.exe"),
            leaf("anchor", "CommandLine", "contains_ci", "ipconfig /flushdns"),
            leaf("anchor", "ParentProcessName", "endswith_ci", "\\explorer.exe"),
            leaf("anchor", "SubjectUserName", "contains_ci", "helpdesk"),
        ),
        "TF_UNMAP_C": all_of(
            leaf("anchor", "TaskName", "contains_ci", "\\Microsoft\\Windows\\DiskCleanup"),
            leaf("anchor", "TaskContent", "contains_ci", "cleanmgr.exe"),
            leaf("anchor", "TaskContent", "contains_ci", "C:\\Windows\\System32\\"),
            leaf("anchor", "SubjectUserName", "contains_ci", "SYSTEM"),
        ),
        "TF_UNMAP_D": all_of(
            leaf("anchor", "ServiceFileName", "contains_ci", "C:\\Program Files\\Contoso\\ContosoAgent.exe"),
            leaf("anchor", "ServiceAccount", "contains_ci", "LocalSystem"),
            leaf("anchor", "ServiceStartType", "eq", "2"),
            leaf("anchor", "SubjectUserName", "contains_ci", "Administrator"),
        ),
        "TF_UNMAP_E": all_of(
            leaf("anchor", "TargetUserName", "eq", "jdoe"),
            leaf("anchor", "SubjectUserName", "eq", "helpdesk"),
            leaf("anchor", "SubjectLogonId", "neq", ""),
        ),
        "TF_UNMAP_PS": all_of(
            leaf("anchor", "Image", "endswith_ci", "\\powershell.exe"),
            leaf("anchor", "CommandLine", "contains_ci", "Get-Service"),
            leaf("anchor", "ParentImage", "endswith_ci", "\\taskeng.exe"),
        ),
        "TF_UNMAP_CMD": all_of(
            leaf("anchor", "NewProcessName", "endswith_ci", "\\cmd.exe"),
            leaf("anchor", "CommandLine", "contains_ci", "dir C:\\Program Files\\Contoso"),
            leaf("anchor", "ParentProcessName", "endswith_ci", "\\explorer.exe"),
        ),
        "TF_UNMAP_SCHTASK": all_of(
            leaf("anchor", "TaskName", "contains_ci", "\\Contoso\\UpdateMaintenance"),
            leaf("anchor", "TaskContent", "contains_ci", "C:\\Program Files\\Contoso\\updater.exe"),
            leaf("anchor", "SubjectUserName", "contains_ci", "SYSTEM"),
        ),
        "TF_UNMAP_SVC": all_of(
            leaf("anchor", "ServiceName", "contains_ci", "ContosoPatch"),
            leaf("anchor", "ServiceFileName", "contains_ci", "C:\\Program Files\\Contoso\\"),
            leaf("anchor", "ServiceAccount", "contains_ci", "LocalService"),
        ),
        "TF_UNMAP_ACCT": all_of(
            leaf("anchor", "TargetUserName", "eq", "backupsvc"),
            leaf("anchor", "SubjectUserName", "eq", "Administrator"),
            leaf("anchor", "SubjectLogonId", "neq", ""),
        ),
        "TF_UNMAP_REG": all_of(
            leaf("anchor", "TargetObject", "contains_ci", "\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"),
            leaf("anchor", "Details", "contains_ci", "C:\\Program Files\\OneDrive\\"),
            leaf("anchor", "Image", "endswith_ci", "\\OneDrive.exe"),
        ),
        "TF_UNMAP_EVTCLR": all_of(
            leaf("anchor", "EventID", "eq", 1102),
            leaf("anchor", "SubjectUserName", "neq", ""),
        ),
    }
    benign_context_specs = {
        "TF_UNMAP_A": [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "taskeng.exe launches the approved maintenance script")],
        "TF_UNMAP_B": [ctx("context_1", SECURITY, SECURITY_CHANNEL, 4688, "ipconfig.exe child of the interactive cmd session")],
        "TF_UNMAP_C": [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "cleanmgr.exe launched by the maintenance task")],
        "TF_UNMAP_D": [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "ContosoAgent.exe started after managed installation")],
        "TF_UNMAP_E": [ctx("context_1", SECURITY, SECURITY_CHANNEL, 4688, "helpdesk net user command for employee onboarding")],
        "TF_UNMAP_PS": [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "taskeng.exe maintenance process")],
        "TF_UNMAP_CMD": [ctx("context_1", SECURITY, SECURITY_CHANNEL, 4688, "interactive explorer.exe process")],
        "TF_UNMAP_SCHTASK": [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "signed updater.exe launched by taskeng.exe")],
        "TF_UNMAP_SVC": [ctx("context_1", SECURITY, SECURITY_CHANNEL, 4688, "MSI service deployment process")],
        "TF_UNMAP_ACCT": [ctx("context_1", SECURITY, SECURITY_CHANNEL, 4688, "Contoso account-provisioner process under the approved management agent")],
        "TF_UNMAP_REG": [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "OneDrive startup application process")],
    }
    benign_context_predicates = {
        "TF_UNMAP_A": all_of(leaf("context_1", "Image", "endswith_ci", "\\taskeng.exe"), leaf("context_1", "ParentImage", "endswith_ci", "\\svchost.exe")),
        "TF_UNMAP_B": all_of(leaf("context_1", "NewProcessName", "endswith_ci", "\\ipconfig.exe"), leaf("context_1", "ParentProcessName", "endswith_ci", "\\cmd.exe"), leaf("context_1", "SubjectUserName", "contains_ci", "helpdesk")),
        "TF_UNMAP_C": all_of(leaf("context_1", "Image", "endswith_ci", "\\cleanmgr.exe"), leaf("context_1", "User", "contains_ci", "SYSTEM")),
        "TF_UNMAP_D": all_of(leaf("context_1", "Image", "endswith_ci", "\\ContosoAgent.exe"), leaf("context_1", "User", "contains_ci", "SYSTEM")),
        "TF_UNMAP_E": all_of(leaf("context_1", "NewProcessName", "endswith_ci", "\\net.exe"), leaf("context_1", "CommandLine", "contains_ci", "net user jdoe /add"), leaf("context_1", "SubjectUserName", "eq", "helpdesk")),
        "TF_UNMAP_PS": all_of(leaf("context_1", "Image", "endswith_ci", "\\taskeng.exe"), leaf("context_1", "ParentImage", "endswith_ci", "\\svchost.exe")),
        "TF_UNMAP_CMD": all_of(leaf("context_1", "NewProcessName", "endswith_ci", "\\explorer.exe"), leaf("context_1", "SubjectUserName", "contains_ci", "helpdesk")),
        "TF_UNMAP_SCHTASK": all_of(leaf("context_1", "Image", "endswith_ci", "\\updater.exe"), leaf("context_1", "ParentImage", "endswith_ci", "\\taskeng.exe")),
        "TF_UNMAP_SVC": all_of(leaf("context_1", "NewProcessName", "endswith_ci", "\\msiexec.exe"), leaf("context_1", "SubjectUserName", "contains_ci", "Administrator")),
        "TF_UNMAP_ACCT": all_of(leaf("context_1", "NewProcessName", "endswith_ci", "\\account-provisioner.exe"), leaf("context_1", "CommandLine", "contains_ci", "--create backupsvc --role backup"), leaf("context_1", "ParentProcessName", "endswith_ci", "\\management-agent.exe"), leaf("context_1", "SubjectUserName", "eq", "Administrator")),
        "TF_UNMAP_REG": all_of(leaf("context_1", "Image", "endswith_ci", "\\OneDrive.exe"), leaf("context_1", "ParentImage", "endswith_ci", "\\explorer.exe")),
    }
    for fid, behavior, provider, channel, eid, rule, indicators, rationale in benign_specs:
        anchor = a(provider, channel, eid, f"{rule}; select the concrete provider fields that contain {', '.join(indicators)}")
        event = ctx("context_1", provider, channel, eid, f"Related authorized maintenance event for {fid}")
        context_specs = benign_context_specs.get(fid, [event])
        benign_pred = benign_predicates[fid]
        if fid == "TF_UNMAP_EVTCLR":
            context_specs = [
                ctx("context_1", SECURITY, SECURITY_CHANNEL, 4698, "Approved synthetic Security log-retention scheduled task"),
                ctx("context_2", SYSMON, SYSMON_CHANNEL, 1, "Contoso logrotate.exe launched by taskeng.exe"),
            ]
            single = gt("ambiguous", [], benign_pred, "EID 1102 and subject metadata show a log clear, but the single view does not establish authorization or mechanism.")
            contextual = gt("unmapped", [], all_of(
                leaf("anchor", "EventID", "eq", 1102),
                leaf("context_1", "TaskName", "contains_ci", "\\Contoso\\SecurityLogRetention"),
                leaf("context_1", "TaskContent", "contains_ci", "C:\\Program Files\\Contoso\\LogMaintenance\\logrotate.exe"),
                leaf("context_2", "Image", "endswith_ci", "\\logrotate.exe"),
                leaf("context_2", "ParentImage", "endswith_ci", "\\taskeng.exe"),
                leaf("context_2", "CommandLine", "contains_ci", "--clear Security"),
                relation("process_then_task", "process", "context_2", "task", "context_1"),
                relation("temporal_before", "before", "context_1", "after", "context_2"),
                relation("temporal_before", "before", "context_2", "after", "anchor"),
                relation("same_host", "events", ["context_1", "context_2", "anchor"]),
                relation("same_logon", "events", ["context_1", "context_2", "anchor"]),
            ), "The approved synthetic SecurityLogRetention task, protected logrotate.exe path, taskeng parent, ordering, host, and logon jointly establish a benign maintenance workflow.")
        elif fid == "TF_UNMAP_ACCT":
            single = gt("ambiguous", [], benign_pred, "EID 4720 identifies the account and creator but does not prove that provisioning was authorized in the single view.")
            contextual = gt("unmapped", [], all_of(
                benign_pred,
                benign_context_predicates[fid],
                relation("temporal_before", "before", "context_1", "after", "anchor"),
                relation("same_host", "events", ["context_1", "anchor"]),
                relation("same_logon", "events", ["context_1", "anchor"]),
            ), "The linked Contoso account-provisioner process, approved management parent, explicit role, ordering, host, and logon establish an affirmative synthetic provisioning workflow.")
        else:
            single = gt("unmapped", [], benign_pred, rationale)
            contextual = gt("unmapped", [], all_of(benign_pred, benign_context_predicates[fid], relation("same_host", "events", ["anchor", "context_1"])), f"Context confirms the same benign {behavior.lower()} workflow with an explicit maintenance process or actor.")
        families.append(spec(fid, "unmapped", "test", behavior, anchor, single, contextual,
                             [f"A related event confirms the approved workflow for {behavior.lower()} with affirmative benign telemetry."], context_specs,
                             "A payload path, encoded interpreter command, suspicious persistence location, or unauthorized creator would change this interpretation.",
                             f"The same primitive with an untrusted path or suspicious command would be ambiguous or mapped: {behavior.lower()}.",
                             ["Keep the provider-specific benign fields visible."], ["Do not reduce the family to label_status only or use unrelated negative text."], old[fid], comparison_ids=["T1059.001"] if "PowerShell" in behavior else None))

    ambiguous_specs = [
        ("TF_AMBIG_A", "Unknown PowerShell script execution", SYSMON, SYSMON_CHANNEL, 1, "powershell.exe -File C:\\Users\\Public\\unknown.ps1", "unknown.ps1"),
        ("TF_AMBIG_B", "Dual-use cmd reconnaissance", SECURITY, SECURITY_CHANNEL, 4688, "cmd.exe /c whoami", "whoami"),
        ("TF_AMBIG_C", "Unknown scheduled task payload", SECURITY, SECURITY_CHANNEL, 4698, "\\CacheRefresh runs C:\\ProgramData\\cache.exe", "cache.exe"),
        ("TF_AMBIG_D", "Dual-use RunOnce mutation", SYSMON, SYSMON_CHANNEL, 13, "RunOnce points to AppData helper.exe", "AppData"),
    ]
    for fid, behavior, provider, channel, eid, rule, indicator in ambiguous_specs:
        anchor = a(provider, channel, eid, f"{rule}; select the {indicator} field")
        event = ctx("context_1", provider, channel, eid, f"Related event with the same dual-use primitive for {fid}")
        field = "CommandLine" if eid in (1, 4688) else "TaskContent" if eid == 4698 else "Details"
        pred = all_of(leaf("anchor", "EventID", "eq", eid), leaf("anchor", field, "contains_ci", indicator))
        families.append(spec(fid, "ambiguous", "test", behavior, anchor,
                             gt("ambiguous", [], pred, "The event is observable and dual-use, but the single view lacks enough intent or authorization evidence."),
                             gt("ambiguous", [], all_of(pred, relation("same_host", "events", ["anchor", "context_1"])), "Context repeats the dual-use behavior without independently establishing mapped or affirmative benign evidence."),
                             ["A related event confirms the same behavior but still lacks intent, authorization, or a mapped payload chain."], [event],
                             "A signed approved workflow would support unmapped; a linked malicious payload or persistence chain would support mapped.",
                             "The same primitive with no event fields or invalid telemetry would be a registry error, not a valid ambiguous case.",
                             ["Keep the dual-use indicator and same-host relationship."], ["Do not use an empty predicate to represent uncertainty."], old[fid], comparison_ids=["T1059.001"] if "PowerShell" in behavior else None))

    # DEV mapped-single families use different event shapes and behaviors from
    # TEST while retaining two instances per primary technique.
    dev_specs = [
        ("TF_T1059_001_DEV", "PowerShell Core launched by wscript with encoded arguments", "T1059.001", a(SYSMON, SYSMON_CHANNEL, 1, "pwsh.exe child of wscript.exe with -EncodedCommand"), all_of(leaf("anchor", "Image", "endswith_ci", "\\pwsh.exe"), leaf("anchor", "ParentImage", "endswith_ci", "\\wscript.exe"), leaf("anchor", "CommandLine", "contains_ci", "-EncodedCommand")), [ctx("context_1", SYSMON, SYSMON_CHANNEL, 3, "Network activity from the pwsh process")]),
        ("TF_T1059_003_DEV", "Command Shell delayed expansion launched by mshta", "T1059.003", a(SECURITY, SECURITY_CHANNEL, 4688, "cmd.exe child of mshta.exe uses delayed expansion and call"), all_of(leaf("anchor", "NewProcessName", "endswith_ci", "\\cmd.exe"), leaf("anchor", "ParentProcessName", "endswith_ci", "\\mshta.exe"), leaf("anchor", "CommandLine", "contains_ci", "/v:on"), leaf("anchor", "CommandLine", "contains_ci", "call ")), [ctx("context_1", SECURITY, SECURITY_CHANNEL, 4688, "Batch child of the mshta-launched shell")]),
        ("TF_T1053_005_DEV", "Hidden scheduled task launching rundll32 DLL entry point", "T1053.005", a(SECURITY, SECURITY_CHANNEL, 4698, "TaskContent has a hidden trigger and rundll32.exe DLL entry point"), all_of(leaf("anchor", "TaskContent", "contains_ci", "Hidden"), leaf("anchor", "TaskContent", "contains_ci", "rundll32.exe"), leaf("anchor", "TaskContent", "contains_ci", ".dll")), [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "rundll32.exe launched by the hidden task")]),
        ("TF_T1543_003_DEV", "Windows service DLL hosted by svchost under LocalService", "T1543.003", a(SECURITY, SECURITY_CHANNEL, 4697, "ServiceFileName uses svchost -k and a protected service DLL under LocalService"), all_of(leaf("anchor", "ServiceFileName", "contains_ci", "svchost.exe -k"), leaf("anchor", "ServiceFileName", "contains_ci", "ServiceDll"), leaf("anchor", "ServiceAccount", "contains_ci", "LocalService")), [ctx("context_1", SYSMON, SYSMON_CHANNEL, 11, "Service DLL written before installation")]),
        ("TF_T1136_001_DEV", "PowerShell Core creates a local service account during member-server provisioning", "T1136.001", a(SYSMON, SYSMON_CHANNEL, 1, "pwsh.exe invokes New-LocalUser with AccountNeverExpires on a member server"), all_of(leaf("anchor", "Image", "endswith_ci", "\\pwsh.exe"), leaf("anchor", "CommandLine", "contains_ci", "New-LocalUser"), leaf("anchor", "CommandLine", "contains_ci", "-AccountNeverExpires")), [ctx("context_1", SECURITY, SECURITY_CHANNEL, 4720, "Local account created by provisioning command")]),
        ("TF_T1547_001_DEV", "Startup-folder URL shortcut created by a login helper", "T1547.001", a(SYSMON, SYSMON_CHANNEL, 11, "Startup folder receives a .url file with a file-create event"), all_of(leaf("anchor", "TargetFilename", "contains_ci", "\\Startup\\"), leaf("anchor", "TargetFilename", "endswith_ci", ".url"), leaf("anchor", "Image", "endswith_ci", "\\loginhelper.exe")), [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "Login helper associated with startup shortcut")]),
        ("TF_T1685_005_DEV", "Security audit log clear after a remote PowerShell maintenance session", "T1685.005", a(EVENTLOG, SECURITY_CHANNEL, 1102, "Windows Eventlog EID 1102 with a populated SubjectLogonId"), all_of(leaf("anchor", "EventID", "eq", 1102), leaf("anchor", "SubjectLogonId", "neq", "")), [ctx("context_1", SECURITY, SECURITY_CHANNEL, 4688, "Remote PowerShell process invoking Clear-EventLog")]),
        ("TF_T1105_DEV", "MSI transfer initiated by msiexec with a remote package URL", "T1105", a(SYSMON, SYSMON_CHANNEL, 1, "msiexec.exe command line contains an external MSI URL and passive install option"), all_of(leaf("anchor", "Image", "endswith_ci", "\\msiexec.exe"), leaf("anchor", "CommandLine", "contains_ci", "https://files.example.invalid/"), leaf("anchor", "CommandLine", "contains_ci", ".msi")), [ctx("context_1", SYSMON, SYSMON_CHANNEL, 11, "MSI package written to the installer cache")]),
    ]
    for fid, behavior, tid, anchor, pred, context_specs in dev_specs:
        contextual_pred = all_of(pred, relation("same_host", "events", ["anchor", "context_1"]))
        if tid == "T1685.005":
            single = gt("ambiguous", [], pred, "EID 1102 establishes a cleared Security audit log but does not identify the PowerShell mechanism in the single view.")
            contextual_pred = all_of(leaf("anchor", "EventID", "eq", 1102), leaf("context_1", "CommandLine", "contains_ci", "Clear-EventLog"), relation("temporal_before", "before", "context_1", "after", "anchor"), relation("same_logon", "events", ["context_1", "anchor"]))
            contextual = gt("mapped", [tid], contextual_pred, "A linked PowerShell Clear-EventLog process supplies the mechanism evidence for T1685.005.")
        else:
            single = gt("mapped", [tid], pred, f"The DEV-only {behavior.lower()} has concrete technique-specific evidence in its anchor event.")
            contextual = gt("mapped", [tid], contextual_pred, f"Context confirms the DEV-only {behavior.lower()} behavior through a related telemetry event.")
        families.append(spec(fid, "mapped_single", "dev", behavior, anchor, single, contextual,
                             [f"A structurally distinct DEV context event corroborates {behavior.lower()}."], context_specs,
                             "An approved signed tool or managed provisioning workflow would be benign counter-evidence.",
                             f"A routine counterpart of {behavior.lower()} with protected paths and approved ownership.",
                             ["Keep this family structurally distinct from TEST families."], ["Do not vary only IDs, timestamps, or hosts."], old[fid], comparison_ids=[tid],
                             host_constraints=local_hosts if tid == "T1136.001" else None))

    # DEV multi families deliberately use 2 and 3 contextual labels.
    families += [
        spec("TF_MULTI_DEV_A", "mapped_multi", "dev", "Run-key startup persistence followed by service installation",
             a(SYSMON, SYSMON_CHANNEL, 13, "Run key points to a protected DEV payload and is followed by a service install"),
             gt("mapped", ["T1547.001"], all_of(leaf("anchor", "TargetObject", "contains_ci", "\\Run\\"), leaf("anchor", "Details", "contains_ci", "DEV\\agent.exe")), "The DEV single view independently supports a Run-key persistence artifact."),
             gt("mapped", ["T1547.001", "T1543.003"], {
                 "T1547.001": all_of(leaf("anchor", "TargetObject", "contains_ci", "\\Run\\"), leaf("anchor", "Details", "contains_ci", "DEV\\agent.exe")),
                 "T1543.003": all_of(leaf("context_1", "ServiceFileName", "contains_ci", "DEV\\agent.exe"), leaf("context_1", "ServiceAccount", "contains_ci", "LocalService"), relation("same_host", "events", ["anchor", "context_1"])),
             }, "The DEV contextual view supplies separate Run-key and service-install evidence."),
             ["The DEV payload is registered for startup and then installed as a service under a separate service event."],
             [ctx("context_1", SECURITY, SECURITY_CHANNEL, 4697, "DEV service installation")],
             "A managed agent may use both startup and service registration during deployment; signed payload and change record are counter-evidence.",
             "A single Run-key update with no service installation.", ["Keep two independent contextual predicates."], ["Do not collapse the labels into one global rule."], old["TF_MULTI_DEV_A"]),
        spec("TF_MULTI_DEV_B", "mapped_multi", "dev", "Scheduled task launches PowerShell which downloads a package",
             a(SECURITY, SECURITY_CHANNEL, 4698, "DEV task content invokes pwsh.exe and references a remote package"),
             gt("mapped", ["T1053.005"], all_of(leaf("anchor", "TaskName", "contains_ci", "\\DEV\\PackageRefresh"), leaf("anchor", "TaskContent", "contains_ci", "pwsh.exe")), "The DEV single view independently supports scheduled-task creation."),
             gt("mapped", ["T1053.005", "T1059.001", "T1105"], {
                 "T1053.005": all_of(leaf("anchor", "TaskName", "contains_ci", "\\DEV\\PackageRefresh"), leaf("anchor", "TaskContent", "contains_ci", "pwsh.exe")),
                 "T1059.001": all_of(leaf("context_1", "Image", "endswith_ci", "\\pwsh.exe"), leaf("context_1", "CommandLine", "contains_ci", "-File"), relation("process_then_task", "process", "context_1", "task", "anchor")),
                 "T1105": all_of(leaf("context_1", "CommandLine", "contains_ci", "https://files.example.invalid/"), leaf("context_2", "TargetFilename", "contains_ci", "DEV\\cache"), relation("process_then_file", "process", "context_1", "file", "context_2")),
             }, "The DEV contextual view independently supports the task object, PowerShell execution, and transfer artifact."),
             ["The DEV task starts pwsh.exe, which downloads a package and writes the cache file."],
             [ctx("context_1", SYSMON, SYSMON_CHANNEL, 1, "DEV pwsh execution"), ctx("context_2", SYSMON, SYSMON_CHANNEL, 11, "DEV downloaded package cache")],
             "A managed software updater may use this chain; signed script, trusted endpoint, and deployment ticket are counter-evidence.",
             "A scheduled task with a local signed script and no transfer behavior.", ["Use three independent contextual predicates."], ["Do not rely on cardinality alone."], old["TF_MULTI_DEV_B"]),
    ]

    # DEV negative/uncertain families are real telemetry scenarios, not labels
    # attached to placeholders.
    families += [
        spec("TF_UNMAP_DEV", "unmapped", "dev", "Signed vendor updater writes an ordinary cache file",
             a(SYSMON, SYSMON_CHANNEL, 3, "Sysmon EID 3 from a signed updater to an allowlisted update endpoint"),
             gt("unmapped", [], all_of(leaf("anchor", "Image", "endswith_ci", "\\ContosoUpdater.exe"), leaf("anchor", "DestinationIp", "in", ["198.51.100.20", "203.0.113.20"]), not_(leaf("anchor", "Image", "contains_ci", "\\Users\\Public\\"))), "The network event is paired with a signed vendor updater and an allowlisted endpoint, supporting a benign update workflow."),
             gt("unmapped", [], all_of(leaf("anchor", "Image", "endswith_ci", "\\ContosoUpdater.exe"), leaf("context_1", "TargetFilename", "contains_ci", "\\Contoso\\Cache\\"), not_(leaf("context_1", "TargetFilename", "contains_ci", "\\Users\\Public\\")), relation("network_then_file", "network", "anchor", "file", "context_1")), "The contextual cache file confirms ordinary updater activity without suspicious payload or persistence evidence."),
             ["The signed updater creates a cache file under its protected vendor directory."], [ctx("context_1", SYSMON, SYSMON_CHANNEL, 11, "Updater cache file")],
             "An untrusted process, non-allowlisted endpoint, or executable written to a user-writable path would change the interpretation.",
             "A network-only event without signer, endpoint, or cache-path evidence would be ambiguous.", ["Keep signer/path/endpoint evidence."], ["Do not reduce the family to label_status only."], old["TF_UNMAP_DEV"]),
        spec("TF_AMBIG_DEV", "ambiguous", "dev", "Unknown signedness service registration with no execution context",
             a(SECURITY, SECURITY_CHANNEL, 4697, "Security 4697 registers a service from an unknown ProgramData path"),
             gt("ambiguous", [], all_of(leaf("anchor", "ServiceFileName", "contains_ci", "C:\\ProgramData\\"), leaf("anchor", "ServiceStartType", "eq", "3")), "A ProgramData service with demand start is observable but lacks signer, creator, and execution context needed for attribution."),
             gt("ambiguous", [], all_of(leaf("anchor", "ServiceFileName", "contains_ci", "C:\\ProgramData\\"), leaf("context_1", "ServiceName", "contains_ci", "Telemetry"), relation("same_host", "events", ["anchor", "context_1"])), "The related service metadata remains dual-use and does not resolve to mapped or affirmative benign evidence."),
             ["A related service record confirms the same dual-use installation but adds no signer or creator evidence."], [ctx("context_1", SECURITY, SECURITY_CHANNEL, 4697, "Related service metadata")],
             "A signed vendor binary and deployment record would make this unmapped; a suspicious creator and execution chain would make it mapped.",
             "A missing or unsupported service event would be invalid registry data, not ambiguity.", ["Keep the valid 4697 schema and the explicit uncertainty rationale."], ["Do not use provider any or EventID zero."], old["TF_AMBIG_DEV"]),
    ]

    if len(families) != len(old):
        raise ValueError(f"migration produced {len(families)} families, expected {len(old)}")
    if {f["template_family_id"] for f in families} != set(old):
        raise ValueError("migration changed the family ID set")
    return {
        "schema_version": "2.0.0",
        "registry_status": "awaiting_human_semantic_approval",
        "benchmark_catalog": {
            "attack_version": "19.2",
            "snapshot_commit": "6cda5ad8462c79e14fbb872f4e09059b18e0cfc4",
            "technique_ids": list(NAMES),
        },
        "families": families,
    }


def main() -> None:
    registry = build()
    REGISTRY_PATH.write_bytes((json.dumps(registry, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(f"wrote {len(registry['families'])} semantic families to {REGISTRY_PATH}")


if __name__ == "__main__":
    main()
