# RAG2ATTCK Synthetic Benchmark — Semantic Template Registry Approval

This package is generated from `config/synthetic_templates.json`. It is a human semantic-review artifact for Stage A. Stage B generation and final dataset freezing are intentionally not performed.

- Registry SHA-256: `1fbe27edd7b20d0f520c13a409a0faa539e52b6e28afb513dfcd6d35b2da483c`
- Total families: `64` (`test=52`, `dev=12`)
- Planned pairs: `670`
- ATT&CK catalog: pinned Enterprise v19.2; names are checked against the local STIX snapshot.
- Attribution policy: evidence-conditioned closed-world; absence of evidence is ambiguous, not unmapped.

## Planned quota summary

| Split | Category | Families | Planned pairs |
|---|---|---:|---:|
| test | mapped_single | 32 | 400 |
| test | mapped_multi | 4 | 40 |
| test | unmapped | 12 | 150 |
| test | ambiguous | 4 | 50 |
| dev | mapped_single | 8 | 16 |
| dev | mapped_multi | 2 | 4 |
| dev | unmapped | 1 | 6 |
| dev | ambiguous | 1 | 4 |

## Canonical telemetry schema

- `Microsoft-Windows-Security-Auditing` / `Security`: EID 4688, 4697, 4698, 4720.
- `Microsoft-Windows-Eventlog` / `Security`: EID 1102.
- `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational`: EID 1, 3, 11, 13.
- EID 4697 is the Security service-install event; EID 7045 is not used.
- EID 1102 is an audit-log-cleared outcome and is not mechanism evidence by itself.

## Relation DSL signatures

- `same_host`, `same_user`, `same_logon`, `same_process`, `same_process_guid`: `events` list.
- `temporal_before`: `before`, `after` event keys.
- `process_then_file`: `process`, `file`; `process_then_network`: `process`, `network`.
- `process_then_registry`: `process`, `registry`; `process_then_task`: `process`, `task`; `process_then_service`: `process`, `service`.
- `network_then_file`: `network`, `file`; operands are checked against the canonical event classes.

## Family-by-family semantic review

## `TF_T1059_001_A`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Encoded PowerShell launched by an Office document
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: Sysmon process creation where Image is powershell.exe, CommandLine contains -EncodedCommand, and ParentImage is an Office application
- Windows documentation: EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1059.001` (PowerShell)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\powershell.exe"
    },
    {
      "any": [
        {
          "event": "anchor",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": "-EncodedCommand"
        },
        {
          "event": "anchor",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": "-enc "
        }
      ]
    },
    {
      "event": "anchor",
      "field": "ParentImage",
      "op": "endswith_ci",
      "value": "\\winword.exe"
    }
  ]
}
```
- Rationale: Sysmon exposes PowerShell execution, an encoded command, and Office as the parent process in the single view.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1059.001` (PowerShell)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\powershell.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "-EncodedCommand"
    },
    {
      "event": "anchor",
      "field": "ParentImage",
      "op": "endswith_ci",
      "value": "\\winword.exe"
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: The contextual process-tree event confirms the Office-to-PowerShell lineage without adding another technique label.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A Sysmon process-create event for winword.exe is present before the PowerShell anchor."]
- Counter-evidence: A signed enterprise automation tool may use an encoded PowerShell command; signing and an approved parent are counter-evidence.
- Benign near-miss: A help-desk document opening a signed PowerShell bootstrapper with a non-encoded command.
- Allowed variations: ["Use powershell.exe or pwsh.exe with a concrete command-line indicator."]
- Disallowed variations: ["Do not add ATT&CK IDs or ground-truth words to CommandLine."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1059.001",
      "technique_name": "PowerShell",
      "url": "https://attack.mitre.org/techniques/T1059/001"
    }
  ],
  "comparison_technique_ids": [
    "T1059.001"
  ]
}
```
- Planned instances: `13`

## `TF_T1059_001_C`

- Split: `test`
- Category: `mapped_single`
- Behavior description: PowerShell started through WMI with intent resolved by context
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `3`
- Anchor selection rule: Sysmon process creation where PowerShell is a child of WmiPrvSE.exe
- Windows documentation: EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]; EID 3 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-3-network-connection]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\powershell.exe"
    },
    {
      "event": "anchor",
      "field": "ParentImage",
      "op": "endswith_ci",
      "value": "\\WmiPrvSE.exe"
    }
  ]
}
```
- Rationale: WMI-launched PowerShell is observable, but that execution path is dual-use and the single view lacks intent evidence.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1059.001` (PowerShell)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\powershell.exe"
    },
    {
      "event": "anchor",
      "field": "ParentImage",
      "op": "endswith_ci",
      "value": "\\WmiPrvSE.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "-NoProfile"
    },
    {
      "event": "context_1",
      "field": "DestinationPort",
      "op": "eq",
      "value": 135
    },
    {
      "relation": "process_then_network",
      "process": "anchor",
      "network": "context_1"
    }
  ]
}
```
- Rationale: The WMI parent, non-interactive PowerShell invocation, and related RPC connection provide defensible contextual evidence for PowerShell execution.
- Expected transition: `ambiguous->mapped`
- Contextual event descriptions: ["A Sysmon network event to TCP/135 is linked to the WMI process before the PowerShell child."]
- Counter-evidence: Remote administration by an authorized operator using WMI and PowerShell remains a benign near-miss.
- Benign near-miss: A locally launched PowerShell process with a signed maintenance script and no remote lineage.
- Allowed variations: ["Keep the WMI parent visible in the anchor fields."]
- Disallowed variations: ["Do not label WMI alone as malicious."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1059.001",
      "technique_name": "PowerShell",
      "url": "https://attack.mitre.org/techniques/T1059/001"
    }
  ],
  "comparison_technique_ids": [
    "T1059.001"
  ]
}
```
- Planned instances: `13`

## `TF_T1059_001_E`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Obfuscated PowerShell using Invoke-Expression and decoded content
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `3`
- Anchor selection rule: PowerShell process whose command line contains Invoke-Expression and FromBase64String
- Windows documentation: EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]; EID 3 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-3-network-connection]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1059.001` (PowerShell)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\powershell.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "Invoke-Expression"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "FromBase64String"
    }
  ]
}
```
- Rationale: PowerShell execution with explicit dynamic evaluation and decoded content is directly visible in the anchor.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1059.001` (PowerShell)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\powershell.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "Invoke-Expression"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "FromBase64String"
    },
    {
      "relation": "same_process",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: The contextual event is the same process identity and confirms the obfuscated PowerShell command rather than introducing a new label.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A follow-on Sysmon event carries the same ProcessGuid as the obfuscated PowerShell anchor."]
- Counter-evidence: An authorized incident-response script can use dynamic evaluation; a documented runbook and signed script are counter-evidence.
- Benign near-miss: A PowerShell script using ordinary variables and no dynamic evaluation or decoding.
- Allowed variations: ["Preserve both dynamic-evaluation and decoding indicators."]
- Disallowed variations: ["Do not infer a second technique from the network event alone."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1059.001",
      "technique_name": "PowerShell",
      "url": "https://attack.mitre.org/techniques/T1059/001"
    }
  ],
  "comparison_technique_ids": [
    "T1059.001"
  ]
}
```
- Planned instances: `12`

## `TF_T1059_001_F`

- Split: `test`
- Category: `mapped_single`
- Behavior description: PowerShell reflective assembly loading in memory
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: PowerShell command line contains Reflection.Assembly and Assembly.Load
- Windows documentation: EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1059.001` (PowerShell)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\powershell.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "Reflection.Assembly"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "Assembly.Load"
    }
  ]
}
```
- Rationale: The anchor directly records PowerShell performing reflective assembly loading.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1059.001` (PowerShell)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\powershell.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "Assembly.Load"
    },
    {
      "event": "context_1",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\powershell.exe"
    },
    {
      "relation": "same_process",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: The follow-on event shares the process identity and confirms the in-memory PowerShell execution chain.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A same-process Sysmon event follows the reflective load."]
- Counter-evidence: A signed application compatibility shim may load an assembly reflectively; approved publisher and path are counter-evidence.
- Benign near-miss: PowerShell loading a normal module from a trusted module directory.
- Allowed variations: ["Keep Reflection.Assembly and Assembly.Load as visible indicators."]
- Disallowed variations: ["Do not claim a fileless technique from Image alone."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1059.001",
      "technique_name": "PowerShell",
      "url": "https://attack.mitre.org/techniques/T1059/001"
    }
  ],
  "comparison_technique_ids": [
    "T1059.001"
  ]
}
```
- Planned instances: `12`

## `TF_T1059_003_A`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Windows Command Shell running a chained administrative command
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Anchor selection rule: Security 4688 where NewProcessName is cmd.exe and CommandLine contains /c, command chaining, and output redirection
- Windows documentation: EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1059.003` (Windows Command Shell)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "NewProcessName",
      "op": "endswith_ci",
      "value": "\\cmd.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": " /c "
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "&&"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "> C:\\ProgramData\\"
    }
  ]
}
```
- Rationale: The Security process-creation record shows a command-shell interpreter executing a chained command and redirecting output.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1059.003` (Windows Command Shell)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "NewProcessName",
      "op": "endswith_ci",
      "value": "\\cmd.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": " /c "
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "&&"
    },
    {
      "relation": "same_process",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: The same process is confirmed by a later Security process record, preserving the command-shell evidence.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A related child process is recorded under the same command-shell process identity."]
- Counter-evidence: Routine support scripts may use cmd.exe; an approved script path, signed parent, and no suspicious output destination are counter-evidence.
- Benign near-miss: cmd.exe /c ipconfig used interactively by a help-desk operator.
- Allowed variations: ["Use NewProcessName and CommandLine from Security 4688."]
- Disallowed variations: ["Do not map cmd.exe merely because it exists."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1059.003",
      "technique_name": "Windows Command Shell",
      "url": "https://attack.mitre.org/techniques/T1059/003"
    }
  ],
  "comparison_technique_ids": [
    "T1059.003"
  ]
}
```
- Planned instances: `13`

## `TF_T1059_003_B`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Windows Command Shell launched by a service with transfer staging resolved by context
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `11`
- Anchor selection rule: Security 4688 where cmd.exe is a child of services.exe
- Windows documentation: EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]; EID 11 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "NewProcessName",
      "op": "endswith_ci",
      "value": "\\cmd.exe"
    },
    {
      "event": "anchor",
      "field": "ParentProcessName",
      "op": "endswith_ci",
      "value": "\\services.exe"
    }
  ]
}
```
- Rationale: A service-launched command shell is observable, but the single view does not establish whether the action is administration or adversarial.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1059.003` (Windows Command Shell)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "NewProcessName",
      "op": "endswith_ci",
      "value": "\\cmd.exe"
    },
    {
      "event": "anchor",
      "field": "ParentProcessName",
      "op": "endswith_ci",
      "value": "\\services.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "certutil"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "-urlcache"
    },
    {
      "relation": "process_then_file",
      "process": "anchor",
      "file": "context_1"
    }
  ]
}
```
- Rationale: The service parent, explicit command-shell execution of certutil staging, and linked file creation provide the contextual threshold.
- Expected transition: `ambiguous->mapped`
- Contextual event descriptions: ["A Sysmon file-create event is linked to the cmd.exe ProcessId after the certutil command."]
- Counter-evidence: A software deployment service may invoke cmd.exe and certutil for an approved package; publisher and managed destination are counter-evidence.
- Benign near-miss: cmd.exe launched by services.exe to run a fixed vendor maintenance command.
- Allowed variations: ["Require both a shell invocation and a concrete command-line behavior."]
- Disallowed variations: ["Do not treat the services.exe parent as sufficient by itself."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1059.003",
      "technique_name": "Windows Command Shell",
      "url": "https://attack.mitre.org/techniques/T1059/003"
    }
  ],
  "comparison_technique_ids": [
    "T1059.003"
  ]
}
```
- Planned instances: `13`

## `TF_T1059_003_C`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Windows Command Shell executing a batch file from a public staging path
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `11`
- Anchor selection rule: Security 4688 where cmd.exe executes a .bat file with delayed expansion and a public staging path
- Windows documentation: EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]; EID 11 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1059.003` (Windows Command Shell)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "NewProcessName",
      "op": "endswith_ci",
      "value": "\\cmd.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": ".bat"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "C:\\Users\\Public\\"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "/v:on"
    }
  ]
}
```
- Rationale: The anchor identifies cmd.exe and a concrete batch-script execution with shell-specific delayed expansion.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1059.003` (Windows Command Shell)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "NewProcessName",
      "op": "endswith_ci",
      "value": "\\cmd.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": ".bat"
    },
    {
      "event": "context_1",
      "field": "TargetFilename",
      "op": "contains_ci",
      "value": ".bat"
    },
    {
      "relation": "process_then_file",
      "process": "anchor",
      "file": "context_1"
    }
  ]
}
```
- Rationale: A linked batch-file creation event confirms the command shell is executing the staged script.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["The batch file is created immediately before the cmd.exe process record."]
- Counter-evidence: Enterprise deployment systems also run batch files; a signed package and managed software directory are counter-evidence.
- Benign near-miss: cmd.exe executing a batch file from C:\Program Files\Contoso.
- Allowed variations: ["Retain the shell-specific /v:on and batch-file indicators."]
- Disallowed variations: ["Do not use only a filename or PID variation."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1059.003",
      "technique_name": "Windows Command Shell",
      "url": "https://attack.mitre.org/techniques/T1059/003"
    }
  ],
  "comparison_technique_ids": [
    "T1059.003"
  ]
}
```
- Planned instances: `12`

## `TF_T1059_003_E`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Windows Command Shell piping reconnaissance into a staged output file
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `11`
- Anchor selection rule: Security 4688 where cmd.exe uses a pipe, findstr, and output to ProgramData
- Windows documentation: EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]; EID 11 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1059.003` (Windows Command Shell)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "NewProcessName",
      "op": "endswith_ci",
      "value": "\\cmd.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": " | "
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "findstr"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "> C:\\ProgramData\\"
    }
  ]
}
```
- Rationale: The anchor visibly records Windows Command Shell piping and filtering output into a staged file.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1059.003` (Windows Command Shell)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "NewProcessName",
      "op": "endswith_ci",
      "value": "\\cmd.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": " | "
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "findstr"
    },
    {
      "event": "context_1",
      "field": "TargetFilename",
      "op": "startswith_ci",
      "value": "C:\\ProgramData\\"
    },
    {
      "relation": "process_then_file",
      "process": "anchor",
      "file": "context_1"
    }
  ]
}
```
- Rationale: The contextual file event confirms the command-shell pipeline wrote its output to the staged destination.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A Sysmon file-create event follows the command-shell pipeline and uses the same process identity."]
- Counter-evidence: A diagnostic script can pipe output to a managed report file; approved script ownership and destination are counter-evidence.
- Benign near-miss: cmd.exe piping a local diagnostic command to the console without a staged output file.
- Allowed variations: ["Require a visible pipe plus filtering or staged output."]
- Disallowed variations: ["Do not use cmd.exe existence as the predicate."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1059.003",
      "technique_name": "Windows Command Shell",
      "url": "https://attack.mitre.org/techniques/T1059/003"
    }
  ],
  "comparison_technique_ids": [
    "T1059.003"
  ]
}
```
- Planned instances: `12`

## `TF_T1053_005_A`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Scheduled task creation with hidden PowerShell payload
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4698`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: Security 4698 where TaskContent contains a hidden PowerShell encoded command and a public payload path
- Windows documentation: EID 4698 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4698]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1053.005` (Scheduled Task)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TaskName",
      "op": "contains_ci",
      "value": "\\Windows\\UpdateCheck"
    },
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "powershell.exe"
    },
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "-EncodedCommand"
    },
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "C:\\Users\\Public\\"
    }
  ]
}
```
- Rationale: The task-created event contains the task object, hidden PowerShell payload, and suspicious payload location in one visible record.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1053.005` (Scheduled Task)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TaskName",
      "op": "contains_ci",
      "value": "\\Windows\\UpdateCheck"
    },
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "-EncodedCommand"
    },
    {
      "event": "context_1",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\powershell.exe"
    },
    {
      "relation": "process_then_task",
      "process": "context_1",
      "task": "anchor"
    }
  ]
}
```
- Rationale: The contextual PowerShell execution is linked back to the created task and confirms execution of the scheduled task payload.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A Sysmon PowerShell process event executes the task content after task creation."]
- Counter-evidence: A centrally managed software updater may create a hidden task; signed content, an approved task owner, and a Program Files path are counter-evidence.
- Benign near-miss: A visible Microsoft maintenance task running cleanmgr.exe from System32.
- Allowed variations: ["Use TaskName and TaskContent as separate observable fields."]
- Disallowed variations: ["Do not map every EID 4698 event."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1053.005",
      "technique_name": "Scheduled Task",
      "url": "https://attack.mitre.org/techniques/T1053/005"
    }
  ],
  "comparison_technique_ids": [
    "T1053.005"
  ]
}
```
- Planned instances: `13`

## `TF_T1053_005_B`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Scheduled task created through COM with suspicious executable execution resolved by context
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4698`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: Security 4698 for a COM-created task whose content points to ProgramData
- Windows documentation: EID 4698 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4698]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TaskName",
      "op": "contains_ci",
      "value": "\\CacheRefresh"
    },
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "C:\\ProgramData\\"
    }
  ]
}
```
- Rationale: A COM-created task and an unknown ProgramData executable are dual-use; intent is not established in the single view.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1053.005` (Scheduled Task)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TaskName",
      "op": "contains_ci",
      "value": "\\CacheRefresh"
    },
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "C:\\ProgramData\\"
    },
    {
      "event": "context_1",
      "field": "Image",
      "op": "contains_ci",
      "value": "C:\\ProgramData\\"
    },
    {
      "relation": "process_then_task",
      "process": "context_1",
      "task": "anchor"
    }
  ]
}
```
- Rationale: The contextual process execution is linked to the task object and establishes scheduled execution of the suspicious payload.
- Expected transition: `ambiguous->mapped`
- Contextual event descriptions: ["A process-create event runs the executable named in TaskContent after registration."]
- Counter-evidence: A vendor cache task may use ProgramData; a signed publisher and an approved maintenance window are counter-evidence.
- Benign near-miss: A task registered for a known Microsoft component with a System32 executable.
- Allowed variations: ["Keep the task content and follow-on process linked."]
- Disallowed variations: ["Do not infer adversarial intent from COM registration alone."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1053.005",
      "technique_name": "Scheduled Task",
      "url": "https://attack.mitre.org/techniques/T1053/005"
    }
  ],
  "comparison_technique_ids": [
    "T1053.005"
  ]
}
```
- Planned instances: `13`

## `TF_T1053_005_D`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Scheduled task with hidden boot trigger and public DLL payload
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4698`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: Security 4698 where TaskName is a misleading update name and TaskContent has a hidden boot trigger and rundll32 public DLL
- Windows documentation: EID 4698 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4698]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1053.005` (Scheduled Task)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TaskName",
      "op": "contains_ci",
      "value": "\\OneDriveUpdate"
    },
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "Hidden"
    },
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "rundll32.exe"
    },
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "C:\\Users\\Public\\"
    }
  ]
}
```
- Rationale: The scheduled-task record exposes a misleading name, hidden trigger, and public DLL execution payload.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1053.005` (Scheduled Task)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TaskName",
      "op": "contains_ci",
      "value": "\\OneDriveUpdate"
    },
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "rundll32.exe"
    },
    {
      "event": "context_1",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\rundll32.exe"
    },
    {
      "relation": "process_then_task",
      "process": "context_1",
      "task": "anchor"
    }
  ]
}
```
- Rationale: The contextual rundll32 process is linked to the task content and confirms task-based execution.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A rundll32 process is created from the task content after registration."]
- Counter-evidence: A legitimate product may use a hidden boot task, but a signed DLL in a vendor directory is required for the benign interpretation.
- Benign near-miss: A Microsoft task with a canonical name and a System32 executable.
- Allowed variations: ["Require both task metadata and a concrete payload indicator."]
- Disallowed variations: ["Do not use a suspicious-looking name alone."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1053.005",
      "technique_name": "Scheduled Task",
      "url": "https://attack.mitre.org/techniques/T1053/005"
    }
  ],
  "comparison_technique_ids": [
    "T1053.005"
  ]
}
```
- Planned instances: `12`

## `TF_T1053_005_E`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Scheduled task invokes PowerShell with intent resolved by a file and network chain
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4698`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`; `context_2` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `3`
- Anchor selection rule: Security 4698 where TaskContent invokes PowerShell from an unknown path
- Windows documentation: EID 4698 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4698]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]; EID 3 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-3-network-connection]
- Telemetry combinations covered: `3` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "powershell.exe"
    },
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "-File"
    }
  ]
}
```
- Rationale: PowerShell in a task is observable, but the single view does not establish whether the task is authorized or adversarial.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1053.005` (Scheduled Task)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "powershell.exe"
    },
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "-File"
    },
    {
      "event": "context_1",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\powershell.exe"
    },
    {
      "event": "context_2",
      "field": "DestinationPort",
      "op": "eq",
      "value": 443
    },
    {
      "relation": "process_then_task",
      "process": "context_1",
      "task": "anchor"
    },
    {
      "relation": "process_then_network",
      "process": "context_1",
      "network": "context_2"
    }
  ]
}
```
- Rationale: The contextual PowerShell execution and outbound connection are both linked to the task, resolving the task mechanism.
- Expected transition: `ambiguous->mapped`
- Contextual event descriptions: ["PowerShell executes the task script and opens a related outbound connection."]
- Counter-evidence: A scheduled compliance job may invoke PowerShell and contact an approved update endpoint; signed script and allowlisted destination are counter-evidence.
- Benign near-miss: A task running a documented PowerShell compliance script without network activity.
- Allowed variations: ["Keep the task content and process relationship explicit."]
- Disallowed variations: ["Do not label task creation as mapped without payload evidence."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1053.005",
      "technique_name": "Scheduled Task",
      "url": "https://attack.mitre.org/techniques/T1053/005"
    }
  ],
  "comparison_technique_ids": [
    "T1053.005"
  ]
}
```
- Planned instances: `12`

## `TF_T1543_003_A`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Windows service installed from a user-writable public executable
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4697`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: Security 4697 where ServiceFileName is a public executable, service starts automatically, and runs as LocalSystem
- Windows documentation: EID 4697 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4697]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1543.003` (Windows Service)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "C:\\Users\\Public\\"
    },
    {
      "event": "anchor",
      "field": "ServiceStartType",
      "op": "eq",
      "value": "2"
    },
    {
      "event": "anchor",
      "field": "ServiceAccount",
      "op": "contains_ci",
      "value": "LocalSystem"
    }
  ]
}
```
- Rationale: Security 4697 directly records a service installation with a user-writable binary, automatic start, and a high-privilege service account.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1543.003` (Windows Service)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "C:\\Users\\Public\\"
    },
    {
      "event": "anchor",
      "field": "ServiceName",
      "op": "contains_ci",
      "value": "Update"
    },
    {
      "event": "context_1",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\services.exe"
    },
    {
      "relation": "process_then_service",
      "process": "context_1",
      "service": "anchor"
    }
  ]
}
```
- Rationale: The service manager process is linked to the 4697 installation and confirms the service creation path.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A services.exe process event is linked to the service installation event."]
- Counter-evidence: A portable enterprise agent may be installed from a controlled staging directory; signer, ACL, and deployment ticket are counter-evidence.
- Benign near-miss: A signed service installed under C:\Program Files\Contoso with a managed start type.
- Allowed variations: ["Use ServiceFileName, ServiceStartType, and ServiceAccount."]
- Disallowed variations: ["Do not map the mere existence of a service."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1543.003",
      "technique_name": "Windows Service",
      "url": "https://attack.mitre.org/techniques/T1543/003"
    }
  ],
  "comparison_technique_ids": [
    "T1543.003"
  ]
}
```
- Planned instances: `13`

## `TF_T1543_003_B`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Windows service installed to launch a command shell payload
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4697`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: Security 4697 where ServiceFileName contains cmd.exe and a ProgramData payload
- Windows documentation: EID 4697 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4697]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1543.003` (Windows Service)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "\\cmd.exe"
    },
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "C:\\ProgramData\\"
    },
    {
      "event": "anchor",
      "field": "ServiceStartType",
      "op": "eq",
      "value": "2"
    }
  ]
}
```
- Rationale: The 4697 record shows service installation whose image launches a command-shell payload from ProgramData.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1543.003` (Windows Service)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "\\cmd.exe"
    },
    {
      "event": "anchor",
      "field": "ServiceName",
      "op": "contains_ci",
      "value": "Update"
    },
    {
      "event": "context_1",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\cmd.exe"
    },
    {
      "relation": "process_then_service",
      "process": "context_1",
      "service": "anchor"
    }
  ]
}
```
- Rationale: A linked cmd.exe process confirms that the installed service executes its command-shell image.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A cmd.exe process is created by the service manager after installation."]
- Counter-evidence: An installer may register a command-shell wrapper; signed wrapper, Program Files path, and installer provenance are counter-evidence.
- Benign near-miss: A service installed by an MSI under Program Files with a vendor executable.
- Allowed variations: ["Require service metadata plus an executable path indicator."]
- Disallowed variations: ["Do not use ServiceName alone."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1543.003",
      "technique_name": "Windows Service",
      "url": "https://attack.mitre.org/techniques/T1543/003"
    }
  ],
  "comparison_technique_ids": [
    "T1543.003"
  ]
}
```
- Planned instances: `13`

## `TF_T1543_003_D`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Windows service installed with a DLL entry point and LocalSystem account
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4697`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `11`
- Anchor selection rule: Security 4697 where ServiceFileName uses svchost -k with an unusual DLL path and LocalSystem
- Windows documentation: EID 4697 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4697]; EID 11 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1543.003` (Windows Service)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "svchost.exe"
    },
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "C:\\Users\\Public\\"
    },
    {
      "event": "anchor",
      "field": "ServiceAccount",
      "op": "contains_ci",
      "value": "LocalSystem"
    }
  ]
}
```
- Rationale: The service-install event records a service-hosted DLL path in a user-writable location under LocalSystem.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1543.003` (Windows Service)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "svchost.exe"
    },
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "C:\\Users\\Public\\"
    },
    {
      "event": "context_1",
      "field": "TargetFilename",
      "op": "contains_ci",
      "value": ".dll"
    },
    {
      "relation": "same_host",
      "events": [
        "context_1",
        "anchor"
      ]
    }
  ]
}
```
- Rationale: The related DLL file event corroborates the installed service image and service-hosted execution.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A DLL file is created at the service image path before the service starts."]
- Counter-evidence: A vendor service may use svchost hosting, but the DLL must be signed and installed in a protected vendor directory.
- Benign near-miss: A signed Windows service DLL under System32 with a Microsoft service name.
- Allowed variations: ["Preserve ServiceFileName, ServiceAccount, and the linked DLL path."]
- Disallowed variations: ["Do not infer maliciousness from svchost.exe alone."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1543.003",
      "technique_name": "Windows Service",
      "url": "https://attack.mitre.org/techniques/T1543/003"
    }
  ],
  "comparison_technique_ids": [
    "T1543.003"
  ]
}
```
- Planned instances: `12`

## `TF_T1543_003_E`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Windows service DLL sideload with execution resolved by context
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4697`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `11`; `context_2` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: Security 4697 where a service loads an unsigned-looking DLL from ProgramData
- Windows documentation: EID 4697 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4697]; EID 11 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `3` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "svchost.exe"
    },
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "C:\\ProgramData\\"
    }
  ]
}
```
- Rationale: A service-hosted DLL under ProgramData is suspicious but the single service-install record does not prove abuse.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1543.003` (Windows Service)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "svchost.exe"
    },
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "C:\\ProgramData\\"
    },
    {
      "event": "context_1",
      "field": "TargetFilename",
      "op": "contains_ci",
      "value": ".dll"
    },
    {
      "event": "context_2",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\svchost.exe"
    },
    {
      "relation": "process_then_service",
      "process": "context_2",
      "service": "anchor"
    }
  ]
}
```
- Rationale: The DLL creation and subsequent service-host process together establish service-based execution of the staged image.
- Expected transition: `ambiguous->mapped`
- Contextual event descriptions: ["A DLL is created at the service path and svchost.exe later starts the service."]
- Counter-evidence: A signed vendor service can use ProgramData; signature and an approved deployment record are required for the benign interpretation.
- Benign near-miss: A service installation with no follow-on file creation or service start evidence.
- Allowed variations: ["Retain the service image path and both contextual corroborators."]
- Disallowed variations: ["Do not map a service install solely from its name."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1543.003",
      "technique_name": "Windows Service",
      "url": "https://attack.mitre.org/techniques/T1543/003"
    }
  ],
  "comparison_technique_ids": [
    "T1543.003"
  ]
}
```
- Planned instances: `12`

## `TF_T1136_001_A`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Local account created through net user with a service-like name
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4720`
- Anchor selection rule: Security 4688 where cmd.exe runs net user /add for a never-expiring service-like account
- Windows documentation: EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]; EID 4720 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4720]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1136.001` (Local Account)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "NewProcessName",
      "op": "endswith_ci",
      "value": "\\cmd.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "net user"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "/add"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "/expires:never"
    }
  ]
}
```
- Rationale: The process event visibly records creation of a local account through net user with persistence-oriented account parameters.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1136.001` (Local Account)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "NewProcessName",
      "op": "endswith_ci",
      "value": "\\cmd.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "net user"
    },
    {
      "event": "context_1",
      "field": "TargetUserName",
      "op": "endswith_ci",
      "value": "$"
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: The contextual account-created event links the net user command to the created local account.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["Security 4720 confirms the account named by the command line was created on the same host."]
- Counter-evidence: A service account created through an approved provisioning runbook is a benign alternative; ticket, owner, and managed naming are counter-evidence.
- Benign near-miss: A help-desk operator creates a named employee account during onboarding.
- Allowed variations: ["Generate only on a workstation or member server."]
- Disallowed variations: ["Never use DC01 for this family."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1136.001",
      "technique_name": "Local Account",
      "url": "https://attack.mitre.org/techniques/T1136/001"
    }
  ],
  "comparison_technique_ids": [
    "T1136.001"
  ]
}
```
- Planned instances: `13`
- Host constraints:
```json
{
  "allowed_host_roles": [
    "workstation",
    "member_server"
  ],
  "forbidden_hosts": [
    "DC01"
  ]
}
```

## `TF_T1136_001_B`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Local account creation followed by suspicious credential-use context
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4720`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Anchor selection rule: Security 4720 where TargetUserName is a service-like name and SubjectUserName is an unexpected creator
- Windows documentation: EID 4720 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4720]; EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TargetUserName",
      "op": "contains_ci",
      "value": "svc_"
    },
    {
      "event": "anchor",
      "field": "SubjectUserName",
      "op": "neq",
      "value": "Administrator"
    }
  ]
}
```
- Rationale: EID 4720 proves account creation but the account name and creator alone do not establish adversarial intent.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1136.001` (Local Account)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TargetUserName",
      "op": "contains_ci",
      "value": "svc_"
    },
    {
      "event": "anchor",
      "field": "SubjectUserName",
      "op": "neq",
      "value": "Administrator"
    },
    {
      "event": "context_1",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "net localgroup administrators"
    },
    {
      "relation": "same_user",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: The account creation is linked to immediate privileged-group use by the same creator session, providing contextual evidence for local-account abuse.
- Expected transition: `ambiguous->mapped`
- Contextual event descriptions: ["A related process adds the new account to the local Administrators group under the same logon."]
- Counter-evidence: Automated workstation provisioning may create a service account and add it to a group; approved image-building provenance is counter-evidence.
- Benign near-miss: A normal employee account created by an administrator without group escalation.
- Allowed variations: ["Use workstation or member-server host roles only."]
- Disallowed variations: ["Do not treat EID 4720 alone as mapped."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1136.001",
      "technique_name": "Local Account",
      "url": "https://attack.mitre.org/techniques/T1136/001"
    }
  ],
  "comparison_technique_ids": [
    "T1136.001"
  ]
}
```
- Planned instances: `13`
- Host constraints:
```json
{
  "allowed_host_roles": [
    "workstation",
    "member_server"
  ],
  "forbidden_hosts": [
    "DC01"
  ]
}
```

## `TF_T1136_001_C`

- Split: `test`
- Category: `mapped_single`
- Behavior description: PowerShell New-LocalUser provisioning with non-expiring account options
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4720`
- Anchor selection rule: Sysmon process creation where pwsh.exe invokes New-LocalUser with AccountNeverExpires
- Windows documentation: EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]; EID 4720 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4720]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1136.001` (Local Account)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\pwsh.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "New-LocalUser"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "AccountNeverExpires"
    }
  ]
}
```
- Rationale: The PowerShell process command line explicitly invokes New-LocalUser with a persistence-oriented option.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1136.001` (Local Account)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\pwsh.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "New-LocalUser"
    },
    {
      "event": "context_1",
      "field": "TargetUserName",
      "op": "contains_ci",
      "value": "svc_"
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: The contextual 4720 record links the PowerShell provisioning command to the created local account.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["Security 4720 records creation of the service-like account after the PowerShell command."]
- Counter-evidence: Golden-image provisioning may use New-LocalUser; approved image build identity and protected script location are counter-evidence.
- Benign near-miss: New-LocalUser used for a time-bounded test account with expiration configured.
- Allowed variations: ["Use FILESVR01, APPSVR01, or a workstation; never DC01."]
- Disallowed variations: ["Do not map ordinary PowerShell without New-LocalUser evidence."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1136.001",
      "technique_name": "Local Account",
      "url": "https://attack.mitre.org/techniques/T1136/001"
    }
  ],
  "comparison_technique_ids": [
    "T1136.001"
  ]
}
```
- Planned instances: `12`
- Host constraints:
```json
{
  "allowed_host_roles": [
    "workstation",
    "member_server"
  ],
  "forbidden_hosts": [
    "DC01"
  ]
}
```

## `TF_T1136_001_E`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Local account with administrative group use resolved by context
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4720`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Anchor selection rule: Security 4720 where a newly created local account has a generic name and ordinary creator context
- Windows documentation: EID 4720 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4720]; EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TargetUserName",
      "op": "contains_ci",
      "value": "backup"
    },
    {
      "event": "anchor",
      "field": "SubjectUserName",
      "op": "contains_ci",
      "value": "helpdesk"
    }
  ]
}
```
- Rationale: The account event is compatible with both authorized backup provisioning and abuse, so the single view is ambiguous.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1136.001` (Local Account)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TargetUserName",
      "op": "contains_ci",
      "value": "backup"
    },
    {
      "event": "context_1",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "net localgroup administrators"
    },
    {
      "event": "context_1",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": " /add"
    },
    {
      "relation": "same_logon",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Immediate administrator-group addition under the account-creation logon resolves the local-account abuse interpretation.
- Expected transition: `ambiguous->mapped`
- Contextual event descriptions: ["A same-logon process adds the new account to the local Administrators group."]
- Counter-evidence: A backup service account may legitimately be added to a local group; approved change control and least-privilege group are counter-evidence.
- Benign near-miss: A local backup account created and left in the Users group only.
- Allowed variations: ["Constrain hosts to workstation/member server."]
- Disallowed variations: ["Do not use DC01 or infer intent from account creation alone."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1136.001",
      "technique_name": "Local Account",
      "url": "https://attack.mitre.org/techniques/T1136/001"
    }
  ],
  "comparison_technique_ids": [
    "T1136.001"
  ]
}
```
- Planned instances: `12`
- Host constraints:
```json
{
  "allowed_host_roles": [
    "workstation",
    "member_server"
  ],
  "forbidden_hosts": [
    "DC01"
  ]
}
```

## `TF_T1547_001_A`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Run key set to execute a user-writable executable
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `13`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: Sysmon 13 where TargetObject is a Run key and Details points to Users/Public executable
- Windows documentation: EID 13 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-13-registry-event]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1547.001` (Registry Run Keys / Startup Folder)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TargetObject",
      "op": "contains_ci",
      "value": "\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\"
    },
    {
      "event": "anchor",
      "field": "Details",
      "op": "contains_ci",
      "value": "C:\\Users\\Public\\"
    },
    {
      "event": "anchor",
      "field": "Details",
      "op": "endswith_ci",
      "value": ".exe"
    }
  ]
}
```
- Rationale: The registry event directly records a Run-key persistence value pointing to a user-writable executable.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1547.001` (Registry Run Keys / Startup Folder)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TargetObject",
      "op": "contains_ci",
      "value": "\\CurrentVersion\\Run\\"
    },
    {
      "event": "anchor",
      "field": "Details",
      "op": "contains_ci",
      "value": "C:\\Users\\Public\\"
    },
    {
      "event": "context_1",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\reg.exe"
    },
    {
      "relation": "process_then_registry",
      "process": "context_1",
      "registry": "anchor"
    }
  ]
}
```
- Rationale: The reg.exe writer event confirms the Run-key mutation and its persistence target.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A reg.exe process event writes the Run value immediately before the Sysmon registry event."]
- Counter-evidence: A legitimate auto-start helper may use a Run key; signed binary and Program Files path are counter-evidence.
- Benign near-miss: A signed updater registered under HKCU Run with a protected vendor path.
- Allowed variations: ["Use TargetObject and Details together."]
- Disallowed variations: ["Do not map any registry write without a startup location and payload."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1547.001",
      "technique_name": "Registry Run Keys / Startup Folder",
      "url": "https://attack.mitre.org/techniques/T1547/001"
    }
  ],
  "comparison_technique_ids": [
    "T1547.001"
  ]
}
```
- Planned instances: `13`

## `TF_T1547_001_B`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Startup-folder shortcut created for a public executable
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `11`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: Sysmon 11 where TargetFilename is a Startup-folder shortcut and Image is explorer.exe
- Windows documentation: EID 11 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1547.001` (Registry Run Keys / Startup Folder)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TargetFilename",
      "op": "contains_ci",
      "value": "\\Start Menu\\Programs\\Startup\\"
    },
    {
      "event": "anchor",
      "field": "TargetFilename",
      "op": "endswith_ci",
      "value": ".lnk"
    },
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\explorer.exe"
    }
  ]
}
```
- Rationale: The file-create event records a shortcut placed in the per-user Startup folder, a direct persistence location.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1547.001` (Registry Run Keys / Startup Folder)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TargetFilename",
      "op": "contains_ci",
      "value": "\\Startup\\"
    },
    {
      "event": "anchor",
      "field": "TargetFilename",
      "op": "endswith_ci",
      "value": ".lnk"
    },
    {
      "event": "context_1",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\explorer.exe"
    },
    {
      "relation": "same_user",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: A related explorer.exe event for the same user confirms the Startup-folder artifact is in the user startup path.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["Explorer processes the Startup-folder shortcut at the next logon."]
- Counter-evidence: Enterprise login software may install a signed Startup shortcut; publisher and protected target path are counter-evidence.
- Benign near-miss: A shortcut created in Downloads or Desktop rather than the Startup folder.
- Allowed variations: ["Require the Startup-folder path and shortcut/file evidence."]
- Disallowed variations: ["Do not use only a .lnk extension."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1547.001",
      "technique_name": "Registry Run Keys / Startup Folder",
      "url": "https://attack.mitre.org/techniques/T1547/001"
    }
  ],
  "comparison_technique_ids": [
    "T1547.001"
  ]
}
```
- Planned instances: `13`

## `TF_T1547_001_C`

- Split: `test`
- Category: `mapped_single`
- Behavior description: PowerShell writes a RunOnce value to a public script
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `13`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `11`
- Anchor selection rule: Sysmon 13 where PowerShell writes a RunOnce value pointing to a public script
- Windows documentation: EID 13 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-13-registry-event]; EID 11 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1547.001` (Registry Run Keys / Startup Folder)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\powershell.exe"
    },
    {
      "event": "anchor",
      "field": "TargetObject",
      "op": "contains_ci",
      "value": "\\RunOnce\\"
    },
    {
      "event": "anchor",
      "field": "Details",
      "op": "contains_ci",
      "value": "C:\\Users\\Public\\"
    },
    {
      "event": "anchor",
      "field": "Details",
      "op": "endswith_ci",
      "value": ".ps1"
    }
  ]
}
```
- Rationale: The registry event records PowerShell creating a RunOnce persistence value with a user-writable script target.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1547.001` (Registry Run Keys / Startup Folder)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TargetObject",
      "op": "contains_ci",
      "value": "\\RunOnce\\"
    },
    {
      "event": "anchor",
      "field": "Details",
      "op": "contains_ci",
      "value": "C:\\Users\\Public\\"
    },
    {
      "event": "context_1",
      "field": "TargetFilename",
      "op": "endswith_ci",
      "value": ".ps1"
    },
    {
      "relation": "same_process",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: The file event corroborates the script target used by the RunOnce value.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["The referenced PowerShell script is created before the RunOnce registry write."]
- Counter-evidence: A software installer can use RunOnce for a one-time setup; signed script and managed installer parent are counter-evidence.
- Benign near-miss: A PowerShell script in a protected installer directory with no Run/RunOnce mutation.
- Allowed variations: ["Keep Image, TargetObject, and Details in the predicate."]
- Disallowed variations: ["Do not infer persistence from PowerShell alone."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1547.001",
      "technique_name": "Registry Run Keys / Startup Folder",
      "url": "https://attack.mitre.org/techniques/T1547/001"
    }
  ],
  "comparison_technique_ids": [
    "T1547.001"
  ]
}
```
- Planned instances: `12`

## `TF_T1547_001_E`

- Split: `test`
- Category: `mapped_single`
- Behavior description: RunOnce mutation with persistence intent resolved by follow-on execution
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `13`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `11`; `context_2` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: Sysmon 13 where an unknown user process writes RunOnce to an AppData executable
- Windows documentation: EID 13 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-13-registry-event]; EID 11 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `3` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TargetObject",
      "op": "contains_ci",
      "value": "\\RunOnce\\"
    },
    {
      "event": "anchor",
      "field": "Details",
      "op": "contains_ci",
      "value": "AppData"
    },
    {
      "event": "anchor",
      "field": "Details",
      "op": "endswith_ci",
      "value": ".exe"
    }
  ]
}
```
- Rationale: RunOnce plus an AppData executable is dual-use; the single event lacks enough context to distinguish software setup from persistence abuse.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1547.001` (Registry Run Keys / Startup Folder)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TargetObject",
      "op": "contains_ci",
      "value": "\\RunOnce\\"
    },
    {
      "event": "anchor",
      "field": "Details",
      "op": "contains_ci",
      "value": "AppData"
    },
    {
      "event": "context_1",
      "field": "TargetFilename",
      "op": "contains_ci",
      "value": "AppData"
    },
    {
      "event": "context_2",
      "field": "Image",
      "op": "endswith_ci",
      "value": ".exe"
    },
    {
      "relation": "process_then_registry",
      "process": "context_2",
      "registry": "anchor"
    }
  ]
}
```
- Rationale: File creation at the target path followed by execution of the RunOnce payload establishes startup persistence in context.
- Expected transition: `ambiguous->mapped`
- Contextual event descriptions: ["The AppData executable is created and then executed after the RunOnce registry mutation."]
- Counter-evidence: A signed per-user updater may use RunOnce; verified signer and an installer parent are counter-evidence.
- Benign near-miss: A RunOnce value whose target is a signed executable under Program Files.
- Allowed variations: ["Keep both file and process corroboration in contextual evidence."]
- Disallowed variations: ["Do not map RunOnce from the registry path alone."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1547.001",
      "technique_name": "Registry Run Keys / Startup Folder",
      "url": "https://attack.mitre.org/techniques/T1547/001"
    }
  ],
  "comparison_technique_ids": [
    "T1547.001"
  ]
}
```
- Planned instances: `12`

## `TF_T1685_005_A`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Security audit log cleared by wevtutil, resolved only with process context
- Anchor telemetry: `Microsoft-Windows-Eventlog` / `Security` / EID `1102`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Anchor selection rule: Security-channel Windows Eventlog EID 1102 with a non-empty subject user
- Windows documentation: EID 1102 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-1102]; EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "EventID",
      "op": "eq",
      "value": 1102
    },
    {
      "event": "anchor",
      "field": "SubjectUserName",
      "op": "neq",
      "value": ""
    }
  ]
}
```
- Rationale: EID 1102 establishes that the Security audit log was cleared, but does not identify wevtutil or adversarial intent.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1685.005` (Clear Windows Event Logs)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "EventID",
      "op": "eq",
      "value": 1102
    },
    {
      "event": "context_1",
      "field": "NewProcessName",
      "op": "endswith_ci",
      "value": "\\wevtutil.exe"
    },
    {
      "event": "context_1",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": " cl Security"
    },
    {
      "relation": "temporal_before",
      "before": "context_1",
      "after": "anchor"
    },
    {
      "relation": "same_logon",
      "events": [
        "context_1",
        "anchor"
      ]
    }
  ]
}
```
- Rationale: The linked wevtutil process explicitly clears the Security log and supplies the mechanism missing from EID 1102.
- Expected transition: `ambiguous->mapped`
- Contextual event descriptions: ["A Security 4688 process event for wevtutil.exe precedes EID 1102 in the same logon."]
- Counter-evidence: Authorized log maintenance may use wevtutil; a scheduled maintenance identity and approved change window are counter-evidence.
- Benign near-miss: EID 1102 generated by a documented log-retention maintenance job with no suspicious process chain.
- Allowed variations: ["Keep the EID 1102 anchor provider as Microsoft-Windows-Eventlog."]
- Disallowed variations: ["Do not infer wevtutil from EID 1102 alone."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1685.005",
      "technique_name": "Clear Windows Event Logs",
      "url": "https://attack.mitre.org/techniques/T1685/005"
    }
  ],
  "comparison_technique_ids": [
    "T1685.005"
  ]
}
```
- Planned instances: `13`

## `TF_T1685_005_B`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Security audit log cleared by PowerShell Clear-EventLog
- Anchor telemetry: `Microsoft-Windows-Eventlog` / `Security` / EID `1102`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: Security-channel Windows Eventlog EID 1102 for a non-empty subject user
- Windows documentation: EID 1102 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-1102]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "EventID",
      "op": "eq",
      "value": 1102
    },
    {
      "event": "anchor",
      "field": "SubjectLogonId",
      "op": "neq",
      "value": ""
    }
  ]
}
```
- Rationale: The audit-log-cleared event is genuine telemetry but cannot identify a PowerShell mechanism from the anchor alone.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1685.005` (Clear Windows Event Logs)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "EventID",
      "op": "eq",
      "value": 1102
    },
    {
      "event": "context_1",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\powershell.exe"
    },
    {
      "any": [
        {
          "event": "context_1",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": "Clear-EventLog"
        },
        {
          "event": "context_1",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": "wevtutil"
        }
      ]
    },
    {
      "relation": "temporal_before",
      "before": "context_1",
      "after": "anchor"
    },
    {
      "relation": "same_logon",
      "events": [
        "context_1",
        "anchor"
      ]
    }
  ]
}
```
- Rationale: PowerShell Clear-EventLog or equivalent log-clear syntax is visible in the linked process event, so T1685.005 is supported.
- Expected transition: `ambiguous->mapped`
- Contextual event descriptions: ["PowerShell executes Clear-EventLog under the same subject logon before EID 1102."]
- Counter-evidence: A compliance script may clear a test log during rotation; maintenance identity and an approved rotation record are counter-evidence.
- Benign near-miss: EID 1102 with no process event capable of identifying the mechanism.
- Allowed variations: ["Use Eventlog provider, Security channel, and EID 1102 for the anchor."]
- Disallowed variations: ["Never claim PowerShell from EID 1102 alone."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1685.005",
      "technique_name": "Clear Windows Event Logs",
      "url": "https://attack.mitre.org/techniques/T1685/005"
    }
  ],
  "comparison_technique_ids": [
    "T1685.005"
  ]
}
```
- Planned instances: `13`

## `TF_T1685_005_C`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Security audit log cleared through an event-log API call
- Anchor telemetry: `Microsoft-Windows-Eventlog` / `Security` / EID `1102`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Anchor selection rule: Security-channel Windows Eventlog EID 1102 with populated subject metadata
- Windows documentation: EID 1102 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-1102]; EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "EventID",
      "op": "eq",
      "value": 1102
    },
    {
      "event": "anchor",
      "field": "SubjectUserName",
      "op": "neq",
      "value": ""
    }
  ]
}
```
- Rationale: The anchor only reports the result of log clearing; an API mechanism is not visible in EID 1102.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1685.005` (Clear Windows Event Logs)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "EventID",
      "op": "eq",
      "value": 1102
    },
    {
      "event": "context_1",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "EvtClearLog"
    },
    {
      "event": "context_1",
      "field": "NewProcessName",
      "op": "endswith_ci",
      "value": ".exe"
    },
    {
      "relation": "temporal_before",
      "before": "context_1",
      "after": "anchor"
    },
    {
      "relation": "same_logon",
      "events": [
        "context_1",
        "anchor"
      ]
    }
  ]
}
```
- Rationale: The linked process command explicitly calls the event-log clear API and is temporally related to EID 1102.
- Expected transition: `ambiguous->mapped`
- Contextual event descriptions: ["A process invoking EvtClearLog or an equivalent event-log API precedes EID 1102."]
- Counter-evidence: A monitoring or test harness may call the API during approved maintenance; account, signer, and change record are counter-evidence.
- Benign near-miss: EID 1102 with only the subject account and no mechanism evidence.
- Allowed variations: ["Require an explicit process/API indicator in contextual evidence."]
- Disallowed variations: ["Do not map API clear from EventID 1102 alone."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1685.005",
      "technique_name": "Clear Windows Event Logs",
      "url": "https://attack.mitre.org/techniques/T1685/005"
    }
  ],
  "comparison_technique_ids": [
    "T1685.005"
  ]
}
```
- Planned instances: `12`

## `TF_T1685_005_E`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Security audit log clearing after suspicious remote session activity
- Anchor telemetry: `Microsoft-Windows-Eventlog` / `Security` / EID `1102`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `3`; `context_2` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Anchor selection rule: Security-channel Windows Eventlog EID 1102 with a populated logon identity
- Windows documentation: EID 1102 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-1102]; EID 3 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-3-network-connection]; EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]
- Telemetry combinations covered: `3` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "EventID",
      "op": "eq",
      "value": 1102
    },
    {
      "event": "anchor",
      "field": "SubjectLogonId",
      "op": "neq",
      "value": ""
    }
  ]
}
```
- Rationale: EID 1102 confirms clearing but is insufficient to attribute a mechanism or adversarial context.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1685.005` (Clear Windows Event Logs)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "EventID",
      "op": "eq",
      "value": 1102
    },
    {
      "event": "context_1",
      "field": "DestinationPort",
      "op": "eq",
      "value": 445
    },
    {
      "event": "context_2",
      "field": "NewProcessName",
      "op": "endswith_ci",
      "value": "\\wevtutil.exe"
    },
    {
      "event": "context_2",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": " cl Security"
    },
    {
      "relation": "temporal_before",
      "before": "context_1",
      "after": "anchor"
    },
    {
      "relation": "temporal_before",
      "before": "context_2",
      "after": "anchor"
    },
    {
      "relation": "same_logon",
      "events": [
        "context_2",
        "anchor"
      ]
    }
  ]
}
```
- Rationale: Remote-session evidence plus an explicit wevtutil clear command supplies both contextual mechanism and suspicious sequence.
- Expected transition: `ambiguous->mapped`
- Contextual event descriptions: ["A remote SMB session is followed by wevtutil clearing the Security log on the same host."]
- Counter-evidence: Remote administration for approved incident response may clear a log; operator authorization and maintenance record are counter-evidence.
- Benign near-miss: An isolated EID 1102 event from a scheduled rotation job.
- Allowed variations: ["Keep mechanism and remote-session evidence separate."]
- Disallowed variations: ["Do not infer lateral movement or wevtutil from EID 1102 alone."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1685.005",
      "technique_name": "Clear Windows Event Logs",
      "url": "https://attack.mitre.org/techniques/T1685/005"
    }
  ],
  "comparison_technique_ids": [
    "T1685.005"
  ]
}
```
- Planned instances: `12`

## `TF_T1105_A`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Certutil downloads a payload to ProgramData
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `11`
- Anchor selection rule: Sysmon process creation where certutil uses -urlcache -split -f with an external URL and output path
- Windows documentation: EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]; EID 11 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1105` (Ingress Tool Transfer)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\certutil.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "-urlcache"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "-split"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "https://files.example.invalid/"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "C:\\ProgramData\\"
    }
  ]
}
```
- Rationale: The process command line contains concrete certutil download syntax, source URL, and destination path.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1105` (Ingress Tool Transfer)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\certutil.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "-urlcache"
    },
    {
      "event": "context_1",
      "field": "TargetFilename",
      "op": "startswith_ci",
      "value": "C:\\ProgramData\\"
    },
    {
      "relation": "process_then_file",
      "process": "anchor",
      "file": "context_1"
    }
  ]
}
```
- Rationale: The linked file-create event confirms the downloaded artifact was written to the declared destination.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A Sysmon file-create event follows certutil and uses the same process identity."]
- Counter-evidence: A certificate-management job may fetch a CRL; a trusted endpoint, expected filename, and managed signer are counter-evidence.
- Benign near-miss: certutil inspecting a local certificate store without a URL or output path.
- Allowed variations: ["Require tool syntax, source, and destination evidence."]
- Disallowed variations: ["Do not map certutil or a network connection alone."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1105",
      "technique_name": "Ingress Tool Transfer",
      "url": "https://attack.mitre.org/techniques/T1105"
    }
  ],
  "comparison_technique_ids": [
    "T1105"
  ]
}
```
- Planned instances: `13`

## `TF_T1105_B`

- Split: `test`
- Category: `mapped_single`
- Behavior description: BITSAdmin transfers a remote file to a local staging path
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `11`
- Anchor selection rule: Sysmon process creation where bitsadmin /transfer contains an external URL and local output path
- Windows documentation: EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]; EID 11 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1105` (Ingress Tool Transfer)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\bitsadmin.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "/transfer"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "https://files.example.invalid/"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "C:\\ProgramData\\"
    }
  ]
}
```
- Rationale: The BITSAdmin command visibly specifies a transfer job, remote source, and local destination.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1105` (Ingress Tool Transfer)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\bitsadmin.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "/transfer"
    },
    {
      "event": "context_1",
      "field": "TargetFilename",
      "op": "startswith_ci",
      "value": "C:\\ProgramData\\"
    },
    {
      "relation": "process_then_file",
      "process": "anchor",
      "file": "context_1"
    }
  ]
}
```
- Rationale: The resulting file event establishes that the BITS transfer produced a local file.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A file is created at the BITS output path after the transfer process."]
- Counter-evidence: Enterprise software distribution may use BITS; an approved update URL, signed installer, and managed destination are counter-evidence.
- Benign near-miss: BITSAdmin listing jobs or querying status without a transfer source and destination.
- Allowed variations: ["Keep /transfer, URL, and output path visible."]
- Disallowed variations: ["Do not infer transfer from bitsadmin presence alone."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1105",
      "technique_name": "Ingress Tool Transfer",
      "url": "https://attack.mitre.org/techniques/T1105"
    }
  ],
  "comparison_technique_ids": [
    "T1105"
  ]
}
```
- Planned instances: `13`

## `TF_T1105_C`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Curl downloads a remote executable to a local path
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `11`
- Anchor selection rule: Sysmon process creation where curl uses a URL and -o output path
- Windows documentation: EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]; EID 11 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1105` (Ingress Tool Transfer)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\curl.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "https://files.example.invalid/"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": " -o "
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "C:\\ProgramData\\"
    }
  ]
}
```
- Rationale: The curl command explicitly carries source and destination arguments for a transfer.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1105` (Ingress Tool Transfer)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\curl.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": " -o "
    },
    {
      "event": "context_1",
      "field": "TargetFilename",
      "op": "startswith_ci",
      "value": "C:\\ProgramData\\"
    },
    {
      "relation": "process_then_file",
      "process": "anchor",
      "file": "context_1"
    }
  ]
}
```
- Rationale: The file-create event corroborates the local artifact produced by curl.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["The output file is created after the curl process connects to the external URL."]
- Counter-evidence: A documented update agent may use curl; allowlisted endpoint and signed output are counter-evidence.
- Benign near-miss: curl querying an internal health endpoint without an output path or file creation.
- Allowed variations: ["Require URL plus explicit output path or file linkage."]
- Disallowed variations: ["Do not map network-only evidence."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1105",
      "technique_name": "Ingress Tool Transfer",
      "url": "https://attack.mitre.org/techniques/T1105"
    }
  ],
  "comparison_technique_ids": [
    "T1105"
  ]
}
```
- Planned instances: `12`

## `TF_T1105_D`

- Split: `test`
- Category: `mapped_single`
- Behavior description: Network-only connection resolved to an actual transfer by context
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `3`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`; `context_2` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `11`
- Anchor selection rule: Sysmon EID 3 from a process to TCP/443 at an example.invalid address
- Windows documentation: EID 3 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-3-network-connection]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]; EID 11 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create]
- Telemetry combinations covered: `3` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "DestinationPort",
      "op": "eq",
      "value": 443
    },
    {
      "event": "anchor",
      "field": "DestinationIp",
      "op": "in",
      "value": [
        "198.51.100.20",
        "203.0.113.20"
      ]
    }
  ]
}
```
- Rationale: Network-only Sysmon EID 3 shows a connection but not whether bytes were a tool transfer.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1105` (Ingress Tool Transfer)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "DestinationPort",
      "op": "eq",
      "value": 443
    },
    {
      "event": "context_1",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "https://files.example.invalid/"
    },
    {
      "event": "context_1",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": " -o "
    },
    {
      "event": "context_2",
      "field": "TargetFilename",
      "op": "startswith_ci",
      "value": "C:\\ProgramData\\"
    },
    {
      "relation": "process_then_network",
      "process": "context_1",
      "network": "anchor"
    },
    {
      "relation": "network_then_file",
      "network": "anchor",
      "file": "context_2"
    }
  ]
}
```
- Rationale: The contextual process command exposes download syntax and the linked file event confirms the transfer result.
- Expected transition: `ambiguous->mapped`
- Contextual event descriptions: ["A process-create event with source and destination is followed by file creation at the destination."]
- Counter-evidence: An authorized browser or updater can make the connection and download a file; signed process and allowlisted endpoint are counter-evidence.
- Benign near-miss: A TCP connection with no process command or file artifact.
- Allowed variations: ["Keep network-only single view ambiguous."]
- Disallowed variations: ["Do not map EID 3 without transfer evidence."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1105",
      "technique_name": "Ingress Tool Transfer",
      "url": "https://attack.mitre.org/techniques/T1105"
    }
  ],
  "comparison_technique_ids": [
    "T1105"
  ]
}
```
- Planned instances: `12`

## `TF_MULTI_A`

- Split: `test`
- Category: `mapped_multi`
- Behavior description: PowerShell download followed by scheduled-task registration
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `11`; `context_2` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4698`
- Anchor selection rule: PowerShell process uses a download URL and writes a task-registration command
- Windows documentation: EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]; EID 11 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create]; EID 4698 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4698]
- Telemetry combinations covered: `3` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1059.001` (PowerShell)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\powershell.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "Invoke-WebRequest"
    }
  ]
}
```
- Rationale: The single view independently supports PowerShell execution; the download and task behaviors are contextual.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1059.001` (PowerShell), `T1105` (Ingress Tool Transfer), `T1053.005` (Scheduled Task)
- Evidence predicate:
```json
{
  "T1059.001": {
    "all": [
      {
        "event": "anchor",
        "field": "Image",
        "op": "endswith_ci",
        "value": "\\powershell.exe"
      },
      {
        "event": "anchor",
        "field": "CommandLine",
        "op": "contains_ci",
        "value": "Invoke-WebRequest"
      }
    ]
  },
  "T1105": {
    "all": [
      {
        "event": "anchor",
        "field": "CommandLine",
        "op": "contains_ci",
        "value": "https://files.example.invalid/"
      },
      {
        "event": "context_1",
        "field": "TargetFilename",
        "op": "startswith_ci",
        "value": "C:\\ProgramData\\"
      },
      {
        "relation": "process_then_file",
        "process": "anchor",
        "file": "context_1"
      }
    ]
  },
  "T1053.005": {
    "all": [
      {
        "event": "context_2",
        "field": "TaskName",
        "op": "contains_ci",
        "value": "\\CacheRefresh"
      },
      {
        "event": "context_2",
        "field": "TaskContent",
        "op": "contains_ci",
        "value": "C:\\ProgramData\\"
      },
      {
        "relation": "process_then_task",
        "process": "anchor",
        "task": "context_2"
      }
    ]
  }
}
```
- Rationale: Each contextual label has separate evidence: PowerShell syntax, a downloaded file, and a scheduled-task object.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["The same PowerShell process downloads a file and registers a task that uses the downloaded path."]
- Counter-evidence: An enterprise deployment orchestrator can perform all three actions; signed script, managed endpoint, and approved change are counter-evidence.
- Benign near-miss: PowerShell downloads a file without creating a task.
- Allowed variations: ["Keep per-technique contextual predicates independent."]
- Disallowed variations: ["Do not use one predicate for all labels."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1059.001",
      "technique_name": "PowerShell",
      "url": "https://attack.mitre.org/techniques/T1059/001"
    },
    {
      "technique_id": "T1105",
      "technique_name": "Ingress Tool Transfer",
      "url": "https://attack.mitre.org/techniques/T1105"
    },
    {
      "technique_id": "T1053.005",
      "technique_name": "Scheduled Task",
      "url": "https://attack.mitre.org/techniques/T1053/005"
    }
  ],
  "comparison_technique_ids": [
    "T1059.001",
    "T1105",
    "T1053.005"
  ]
}
```
- Planned instances: `10`

## `TF_MULTI_B`

- Split: `test`
- Category: `mapped_multi`
- Behavior description: Suspicious service installation followed by explicit audit-log clearing
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4697`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`; `context_2` = `Microsoft-Windows-Eventlog` / `Security` / EID `1102`
- Anchor selection rule: Security 4697 installs a public-path service with a high-privilege account
- Windows documentation: EID 4697 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4697]; EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]; EID 1102 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-1102]
- Telemetry combinations covered: `3` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1543.003` (Windows Service)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "C:\\Users\\Public\\"
    },
    {
      "event": "anchor",
      "field": "ServiceAccount",
      "op": "contains_ci",
      "value": "LocalSystem"
    }
  ]
}
```
- Rationale: The single service-install event independently supports Windows Service.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1543.003` (Windows Service), `T1685.005` (Clear Windows Event Logs)
- Evidence predicate:
```json
{
  "T1543.003": {
    "all": [
      {
        "event": "anchor",
        "field": "ServiceFileName",
        "op": "contains_ci",
        "value": "C:\\Users\\Public\\"
      },
      {
        "event": "anchor",
        "field": "ServiceAccount",
        "op": "contains_ci",
        "value": "LocalSystem"
      },
      {
        "relation": "process_then_service",
        "process": "context_1",
        "service": "anchor"
      }
    ]
  },
  "T1685.005": {
    "all": [
      {
        "event": "context_2",
        "field": "EventID",
        "op": "eq",
        "value": 1102
      },
      {
        "event": "context_1",
        "field": "CommandLine",
        "op": "contains_ci",
        "value": "wevtutil"
      },
      {
        "event": "context_1",
        "field": "CommandLine",
        "op": "contains_ci",
        "value": " cl Security"
      },
      {
        "relation": "temporal_before",
        "before": "context_1",
        "after": "context_2"
      },
      {
        "relation": "same_logon",
        "events": [
          "context_1",
          "context_2"
        ]
      }
    ]
  }
}
```
- Rationale: Service evidence and log-clear evidence are independently visible in the contextual view.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A service process is followed by wevtutil clearing the Security log."]
- Counter-evidence: A managed installer and log-retention job may create a service and rotate logs; signer, schedule, and ticket are counter-evidence.
- Benign near-miss: A service install with no EID 1102 or clear command.
- Allowed variations: ["Use Eventlog provider for contextual EID 1102."]
- Disallowed variations: ["Do not let the service predicate justify log clearing."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1543.003",
      "technique_name": "Windows Service",
      "url": "https://attack.mitre.org/techniques/T1543/003"
    },
    {
      "technique_id": "T1685.005",
      "technique_name": "Clear Windows Event Logs",
      "url": "https://attack.mitre.org/techniques/T1685/005"
    }
  ],
  "comparison_technique_ids": [
    "T1543.003",
    "T1685.005"
  ]
}
```
- Planned instances: `10`

## `TF_MULTI_C`

- Split: `test`
- Category: `mapped_multi`
- Behavior description: Local account creation followed by Run-key persistence
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4720`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `13`
- Anchor selection rule: Security 4720 creates a service-like local account on an allowed host
- Windows documentation: EID 4720 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4720]; EID 13 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-13-registry-event]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1136.001` (Local Account)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TargetUserName",
      "op": "contains_ci",
      "value": "svc_"
    },
    {
      "event": "anchor",
      "field": "SubjectUserName",
      "op": "neq",
      "value": ""
    }
  ]
}
```
- Rationale: The single view supports local-account creation but does not yet show the persistence behavior.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1136.001` (Local Account), `T1547.001` (Registry Run Keys / Startup Folder)
- Evidence predicate:
```json
{
  "T1136.001": {
    "all": [
      {
        "event": "anchor",
        "field": "TargetUserName",
        "op": "contains_ci",
        "value": "svc_"
      },
      {
        "event": "anchor",
        "field": "SubjectUserName",
        "op": "neq",
        "value": ""
      },
      {
        "relation": "same_user",
        "events": [
          "anchor",
          "context_1"
        ]
      }
    ]
  },
  "T1547.001": {
    "all": [
      {
        "event": "context_1",
        "field": "TargetObject",
        "op": "contains_ci",
        "value": "\\CurrentVersion\\Run\\"
      },
      {
        "event": "context_1",
        "field": "Details",
        "op": "contains_ci",
        "value": "svc_"
      },
      {
        "relation": "temporal_before",
        "before": "anchor",
        "after": "context_1"
      },
      {
        "relation": "same_user",
        "events": [
          "anchor",
          "context_1"
        ]
      }
    ]
  }
}
```
- Rationale: The account event and Run-key mutation have separate predicates, supporting the two contextual techniques.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["The newly created local account is used as the Run-key payload identity."]
- Counter-evidence: Workstation provisioning may create an account and startup helper; image-build provenance and signed software are counter-evidence.
- Benign near-miss: An account creation event without a startup persistence mutation.
- Allowed variations: ["Use allowed local-account hosts only."]
- Disallowed variations: ["Do not use one account predicate for registry persistence."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1136.001",
      "technique_name": "Local Account",
      "url": "https://attack.mitre.org/techniques/T1136/001"
    },
    {
      "technique_id": "T1547.001",
      "technique_name": "Registry Run Keys / Startup Folder",
      "url": "https://attack.mitre.org/techniques/T1547/001"
    }
  ],
  "comparison_technique_ids": [
    "T1136.001",
    "T1547.001"
  ]
}
```
- Planned instances: `10`
- Host constraints:
```json
{
  "allowed_host_roles": [
    "workstation",
    "member_server"
  ],
  "forbidden_hosts": [
    "DC01"
  ]
}
```

## `TF_MULTI_D`

- Split: `test`
- Category: `mapped_multi`
- Behavior description: Command shell downloads a file and executes it
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `11`
- Anchor selection rule: Security 4688 where cmd.exe invokes curl with URL and output path
- Windows documentation: EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]; EID 11 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1059.003` (Windows Command Shell)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "NewProcessName",
      "op": "endswith_ci",
      "value": "\\cmd.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": " /c "
    }
  ]
}
```
- Rationale: The single view independently supports Windows Command Shell execution.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1059.003` (Windows Command Shell), `T1105` (Ingress Tool Transfer)
- Evidence predicate:
```json
{
  "T1059.003": {
    "all": [
      {
        "event": "anchor",
        "field": "NewProcessName",
        "op": "endswith_ci",
        "value": "\\cmd.exe"
      },
      {
        "event": "anchor",
        "field": "CommandLine",
        "op": "contains_ci",
        "value": " /c "
      },
      {
        "event": "anchor",
        "field": "CommandLine",
        "op": "contains_ci",
        "value": "curl"
      }
    ]
  },
  "T1105": {
    "all": [
      {
        "event": "anchor",
        "field": "CommandLine",
        "op": "contains_ci",
        "value": "https://files.example.invalid/"
      },
      {
        "event": "anchor",
        "field": "CommandLine",
        "op": "contains_ci",
        "value": " -o "
      },
      {
        "event": "context_1",
        "field": "TargetFilename",
        "op": "startswith_ci",
        "value": "C:\\ProgramData\\"
      },
      {
        "relation": "process_then_file",
        "process": "anchor",
        "file": "context_1"
      }
    ]
  }
}
```
- Rationale: Command-shell execution and the concrete curl transfer each have separate evidence in the contextual view.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A Sysmon file event confirms the curl output path after the cmd.exe process."]
- Counter-evidence: A deployment wrapper can use cmd.exe and curl for an approved package; signed wrapper and allowlisted URL are counter-evidence.
- Benign near-miss: cmd.exe executes curl against an internal endpoint without a file output.
- Allowed variations: ["Keep transfer evidence separate from shell evidence."]
- Disallowed variations: ["Do not use network-only evidence for T1105."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1059.003",
      "technique_name": "Windows Command Shell",
      "url": "https://attack.mitre.org/techniques/T1059/003"
    },
    {
      "technique_id": "T1105",
      "technique_name": "Ingress Tool Transfer",
      "url": "https://attack.mitre.org/techniques/T1105"
    }
  ],
  "comparison_technique_ids": [
    "T1059.003",
    "T1105"
  ]
}
```
- Planned instances: `10`

## `TF_UNMAP_A`

- Split: `test`
- Category: `unmapped`
- Behavior description: Routine signed PowerShell maintenance
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: PowerShell -NoProfile -File C:\Program Files\Contoso\maintenance.ps1; select the concrete provider fields that contain PowerShell, -NoProfile, maintenance.ps1
- Windows documentation: EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\powershell.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "-NoProfile -File"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "C:\\Program Files\\Contoso\\maintenance.ps1"
    },
    {
      "event": "anchor",
      "field": "ParentImage",
      "op": "endswith_ci",
      "value": "\\taskeng.exe"
    }
  ]
}
```
- Rationale: The signed maintenance script is under Program Files and has no encoded, download, persistence, or account-creation indicator.
### Contextual ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "Image",
          "op": "endswith_ci",
          "value": "\\powershell.exe"
        },
        {
          "event": "anchor",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": "-NoProfile -File"
        },
        {
          "event": "anchor",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": "C:\\Program Files\\Contoso\\maintenance.ps1"
        },
        {
          "event": "anchor",
          "field": "ParentImage",
          "op": "endswith_ci",
          "value": "\\taskeng.exe"
        }
      ]
    },
    {
      "all": [
        {
          "event": "context_1",
          "field": "Image",
          "op": "endswith_ci",
          "value": "\\taskeng.exe"
        },
        {
          "event": "context_1",
          "field": "ParentImage",
          "op": "endswith_ci",
          "value": "\\svchost.exe"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context confirms the same benign routine signed powershell maintenance workflow with an explicit maintenance process or actor.
- Expected transition: `unmapped->unmapped`
- Contextual event descriptions: ["A related event confirms the approved workflow for routine signed powershell maintenance with affirmative benign telemetry."]
- Counter-evidence: A payload path, encoded interpreter command, suspicious persistence location, or unauthorized creator would change this interpretation.
- Benign near-miss: The same primitive with an untrusted path or suspicious command would be ambiguous or mapped: routine signed powershell maintenance.
- Allowed variations: ["Keep the provider-specific benign fields visible."]
- Disallowed variations: ["Do not reduce the family to label_status only or use unrelated negative text."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [],
  "comparison_technique_ids": [
    "T1059.001"
  ]
}
```
- Planned instances: `13`

## `TF_UNMAP_B`

- Split: `test`
- Category: `unmapped`
- Behavior description: Normal cmd-based DNS administration
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Anchor selection rule: cmd.exe /c ipconfig /flushdns; select the concrete provider fields that contain cmd.exe, ipconfig, /flushdns
- Windows documentation: EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "NewProcessName",
      "op": "endswith_ci",
      "value": "\\cmd.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "ipconfig /flushdns"
    },
    {
      "event": "anchor",
      "field": "ParentProcessName",
      "op": "endswith_ci",
      "value": "\\explorer.exe"
    },
    {
      "event": "anchor",
      "field": "SubjectUserName",
      "op": "contains_ci",
      "value": "helpdesk"
    }
  ]
}
```
- Rationale: The command is a routine local diagnostic action with no staged payload, persistence, transfer, or account mutation.
### Contextual ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "NewProcessName",
          "op": "endswith_ci",
          "value": "\\cmd.exe"
        },
        {
          "event": "anchor",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": "ipconfig /flushdns"
        },
        {
          "event": "anchor",
          "field": "ParentProcessName",
          "op": "endswith_ci",
          "value": "\\explorer.exe"
        },
        {
          "event": "anchor",
          "field": "SubjectUserName",
          "op": "contains_ci",
          "value": "helpdesk"
        }
      ]
    },
    {
      "all": [
        {
          "event": "context_1",
          "field": "NewProcessName",
          "op": "endswith_ci",
          "value": "\\ipconfig.exe"
        },
        {
          "event": "context_1",
          "field": "ParentProcessName",
          "op": "endswith_ci",
          "value": "\\cmd.exe"
        },
        {
          "event": "context_1",
          "field": "SubjectUserName",
          "op": "contains_ci",
          "value": "helpdesk"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context confirms the same benign normal cmd-based dns administration workflow with an explicit maintenance process or actor.
- Expected transition: `unmapped->unmapped`
- Contextual event descriptions: ["A related event confirms the approved workflow for normal cmd-based dns administration with affirmative benign telemetry."]
- Counter-evidence: A payload path, encoded interpreter command, suspicious persistence location, or unauthorized creator would change this interpretation.
- Benign near-miss: The same primitive with an untrusted path or suspicious command would be ambiguous or mapped: normal cmd-based dns administration.
- Allowed variations: ["Keep the provider-specific benign fields visible."]
- Disallowed variations: ["Do not reduce the family to label_status only or use unrelated negative text."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [],
  "comparison_technique_ids": []
}
```
- Planned instances: `13`

## `TF_UNMAP_C`

- Split: `test`
- Category: `unmapped`
- Behavior description: Standard scheduled disk-maintenance task
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4698`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: \Microsoft\Windows\DiskCleanup with cleanmgr.exe; select the concrete provider fields that contain DiskCleanup, cleanmgr.exe, System32
- Windows documentation: EID 4698 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4698]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TaskName",
      "op": "contains_ci",
      "value": "\\Microsoft\\Windows\\DiskCleanup"
    },
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "cleanmgr.exe"
    },
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "C:\\Windows\\System32\\"
    },
    {
      "event": "anchor",
      "field": "SubjectUserName",
      "op": "contains_ci",
      "value": "SYSTEM"
    }
  ]
}
```
- Rationale: The task name and System32 cleanmgr.exe content identify routine Windows maintenance.
### Contextual ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "TaskName",
          "op": "contains_ci",
          "value": "\\Microsoft\\Windows\\DiskCleanup"
        },
        {
          "event": "anchor",
          "field": "TaskContent",
          "op": "contains_ci",
          "value": "cleanmgr.exe"
        },
        {
          "event": "anchor",
          "field": "TaskContent",
          "op": "contains_ci",
          "value": "C:\\Windows\\System32\\"
        },
        {
          "event": "anchor",
          "field": "SubjectUserName",
          "op": "contains_ci",
          "value": "SYSTEM"
        }
      ]
    },
    {
      "all": [
        {
          "event": "context_1",
          "field": "Image",
          "op": "endswith_ci",
          "value": "\\cleanmgr.exe"
        },
        {
          "event": "context_1",
          "field": "User",
          "op": "contains_ci",
          "value": "SYSTEM"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context confirms the same benign standard scheduled disk-maintenance task workflow with an explicit maintenance process or actor.
- Expected transition: `unmapped->unmapped`
- Contextual event descriptions: ["A related event confirms the approved workflow for standard scheduled disk-maintenance task with affirmative benign telemetry."]
- Counter-evidence: A payload path, encoded interpreter command, suspicious persistence location, or unauthorized creator would change this interpretation.
- Benign near-miss: The same primitive with an untrusted path or suspicious command would be ambiguous or mapped: standard scheduled disk-maintenance task.
- Allowed variations: ["Keep the provider-specific benign fields visible."]
- Disallowed variations: ["Do not reduce the family to label_status only or use unrelated negative text."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [],
  "comparison_technique_ids": []
}
```
- Planned instances: `13`

## `TF_UNMAP_D`

- Split: `test`
- Category: `unmapped`
- Behavior description: Legitimate signed service deployment
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4697`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: ContosoAgent.exe from C:\Program Files\Contoso; select the concrete provider fields that contain ContosoAgent.exe, Program Files, LocalSystem
- Windows documentation: EID 4697 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4697]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "C:\\Program Files\\Contoso\\ContosoAgent.exe"
    },
    {
      "event": "anchor",
      "field": "ServiceAccount",
      "op": "contains_ci",
      "value": "LocalSystem"
    },
    {
      "event": "anchor",
      "field": "ServiceStartType",
      "op": "eq",
      "value": "2"
    },
    {
      "event": "anchor",
      "field": "SubjectUserName",
      "op": "contains_ci",
      "value": "Administrator"
    }
  ]
}
```
- Rationale: The service binary is in a protected vendor directory and its deployment is a normal managed installation.
### Contextual ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "ServiceFileName",
          "op": "contains_ci",
          "value": "C:\\Program Files\\Contoso\\ContosoAgent.exe"
        },
        {
          "event": "anchor",
          "field": "ServiceAccount",
          "op": "contains_ci",
          "value": "LocalSystem"
        },
        {
          "event": "anchor",
          "field": "ServiceStartType",
          "op": "eq",
          "value": "2"
        },
        {
          "event": "anchor",
          "field": "SubjectUserName",
          "op": "contains_ci",
          "value": "Administrator"
        }
      ]
    },
    {
      "all": [
        {
          "event": "context_1",
          "field": "Image",
          "op": "endswith_ci",
          "value": "\\ContosoAgent.exe"
        },
        {
          "event": "context_1",
          "field": "User",
          "op": "contains_ci",
          "value": "SYSTEM"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context confirms the same benign legitimate signed service deployment workflow with an explicit maintenance process or actor.
- Expected transition: `unmapped->unmapped`
- Contextual event descriptions: ["A related event confirms the approved workflow for legitimate signed service deployment with affirmative benign telemetry."]
- Counter-evidence: A payload path, encoded interpreter command, suspicious persistence location, or unauthorized creator would change this interpretation.
- Benign near-miss: The same primitive with an untrusted path or suspicious command would be ambiguous or mapped: legitimate signed service deployment.
- Allowed variations: ["Keep the provider-specific benign fields visible."]
- Disallowed variations: ["Do not reduce the family to label_status only or use unrelated negative text."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [],
  "comparison_technique_ids": []
}
```
- Planned instances: `13`

## `TF_UNMAP_E`

- Split: `test`
- Category: `unmapped`
- Behavior description: Expected employee local-account provisioning
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4720`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Anchor selection rule: TargetUserName=jdoe created by helpdesk; select the concrete provider fields that contain jdoe, helpdesk, employee
- Windows documentation: EID 4720 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4720]; EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TargetUserName",
      "op": "eq",
      "value": "jdoe"
    },
    {
      "event": "anchor",
      "field": "SubjectUserName",
      "op": "eq",
      "value": "helpdesk"
    },
    {
      "event": "anchor",
      "field": "SubjectLogonId",
      "op": "neq",
      "value": ""
    }
  ]
}
```
- Rationale: The account name and help-desk creator match ordinary onboarding and show no persistence or privilege escalation.
### Contextual ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "TargetUserName",
          "op": "eq",
          "value": "jdoe"
        },
        {
          "event": "anchor",
          "field": "SubjectUserName",
          "op": "eq",
          "value": "helpdesk"
        },
        {
          "event": "anchor",
          "field": "SubjectLogonId",
          "op": "neq",
          "value": ""
        }
      ]
    },
    {
      "all": [
        {
          "event": "context_1",
          "field": "NewProcessName",
          "op": "endswith_ci",
          "value": "\\net.exe"
        },
        {
          "event": "context_1",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": "net user jdoe /add"
        },
        {
          "event": "context_1",
          "field": "SubjectUserName",
          "op": "eq",
          "value": "helpdesk"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context confirms the same benign expected employee local-account provisioning workflow with an explicit maintenance process or actor.
- Expected transition: `unmapped->unmapped`
- Contextual event descriptions: ["A related event confirms the approved workflow for expected employee local-account provisioning with affirmative benign telemetry."]
- Counter-evidence: A payload path, encoded interpreter command, suspicious persistence location, or unauthorized creator would change this interpretation.
- Benign near-miss: The same primitive with an untrusted path or suspicious command would be ambiguous or mapped: expected employee local-account provisioning.
- Allowed variations: ["Keep the provider-specific benign fields visible."]
- Disallowed variations: ["Do not reduce the family to label_status only or use unrelated negative text."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [],
  "comparison_technique_ids": []
}
```
- Planned instances: `13`

## `TF_UNMAP_PS`

- Split: `test`
- Category: `unmapped`
- Behavior description: Routine PowerShell service inventory
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: powershell.exe -Command Get-Service; select the concrete provider fields that contain Get-Service, NoProfile, powershell.exe
- Windows documentation: EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\powershell.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "Get-Service"
    },
    {
      "event": "anchor",
      "field": "ParentImage",
      "op": "endswith_ci",
      "value": "\\taskeng.exe"
    }
  ]
}
```
- Rationale: PowerShell inventory is ordinary administration with no obfuscation, transfer, or persistence evidence.
### Contextual ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "Image",
          "op": "endswith_ci",
          "value": "\\powershell.exe"
        },
        {
          "event": "anchor",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": "Get-Service"
        },
        {
          "event": "anchor",
          "field": "ParentImage",
          "op": "endswith_ci",
          "value": "\\taskeng.exe"
        }
      ]
    },
    {
      "all": [
        {
          "event": "context_1",
          "field": "Image",
          "op": "endswith_ci",
          "value": "\\taskeng.exe"
        },
        {
          "event": "context_1",
          "field": "ParentImage",
          "op": "endswith_ci",
          "value": "\\svchost.exe"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context confirms the same benign routine powershell service inventory workflow with an explicit maintenance process or actor.
- Expected transition: `unmapped->unmapped`
- Contextual event descriptions: ["A related event confirms the approved workflow for routine powershell service inventory with affirmative benign telemetry."]
- Counter-evidence: A payload path, encoded interpreter command, suspicious persistence location, or unauthorized creator would change this interpretation.
- Benign near-miss: The same primitive with an untrusted path or suspicious command would be ambiguous or mapped: routine powershell service inventory.
- Allowed variations: ["Keep the provider-specific benign fields visible."]
- Disallowed variations: ["Do not reduce the family to label_status only or use unrelated negative text."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [],
  "comparison_technique_ids": [
    "T1059.001"
  ]
}
```
- Planned instances: `13`

## `TF_UNMAP_CMD`

- Split: `test`
- Category: `unmapped`
- Behavior description: Routine cmd directory listing
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Anchor selection rule: cmd.exe /c dir C:\Program Files\Contoso; select the concrete provider fields that contain cmd.exe, dir, Program Files
- Windows documentation: EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "NewProcessName",
      "op": "endswith_ci",
      "value": "\\cmd.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "dir C:\\Program Files\\Contoso"
    },
    {
      "event": "anchor",
      "field": "ParentProcessName",
      "op": "endswith_ci",
      "value": "\\explorer.exe"
    }
  ]
}
```
- Rationale: The command shell lists a managed software directory and does not stage or execute a payload.
### Contextual ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "NewProcessName",
          "op": "endswith_ci",
          "value": "\\cmd.exe"
        },
        {
          "event": "anchor",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": "dir C:\\Program Files\\Contoso"
        },
        {
          "event": "anchor",
          "field": "ParentProcessName",
          "op": "endswith_ci",
          "value": "\\explorer.exe"
        }
      ]
    },
    {
      "all": [
        {
          "event": "context_1",
          "field": "NewProcessName",
          "op": "endswith_ci",
          "value": "\\explorer.exe"
        },
        {
          "event": "context_1",
          "field": "SubjectUserName",
          "op": "contains_ci",
          "value": "helpdesk"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context confirms the same benign routine cmd directory listing workflow with an explicit maintenance process or actor.
- Expected transition: `unmapped->unmapped`
- Contextual event descriptions: ["A related event confirms the approved workflow for routine cmd directory listing with affirmative benign telemetry."]
- Counter-evidence: A payload path, encoded interpreter command, suspicious persistence location, or unauthorized creator would change this interpretation.
- Benign near-miss: The same primitive with an untrusted path or suspicious command would be ambiguous or mapped: routine cmd directory listing.
- Allowed variations: ["Keep the provider-specific benign fields visible."]
- Disallowed variations: ["Do not reduce the family to label_status only or use unrelated negative text."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [],
  "comparison_technique_ids": []
}
```
- Planned instances: `12`

## `TF_UNMAP_SCHTASK`

- Split: `test`
- Category: `unmapped`
- Behavior description: Scheduled Windows update maintenance
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4698`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: \Contoso\UpdateMaintenance runs signed updater.exe; select the concrete provider fields that contain UpdateMaintenance, updater.exe, Program Files
- Windows documentation: EID 4698 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4698]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TaskName",
      "op": "contains_ci",
      "value": "\\Contoso\\UpdateMaintenance"
    },
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "C:\\Program Files\\Contoso\\updater.exe"
    },
    {
      "event": "anchor",
      "field": "SubjectUserName",
      "op": "contains_ci",
      "value": "SYSTEM"
    }
  ]
}
```
- Rationale: The task content is a signed vendor updater in a protected path and is tied to maintenance context.
### Contextual ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "TaskName",
          "op": "contains_ci",
          "value": "\\Contoso\\UpdateMaintenance"
        },
        {
          "event": "anchor",
          "field": "TaskContent",
          "op": "contains_ci",
          "value": "C:\\Program Files\\Contoso\\updater.exe"
        },
        {
          "event": "anchor",
          "field": "SubjectUserName",
          "op": "contains_ci",
          "value": "SYSTEM"
        }
      ]
    },
    {
      "all": [
        {
          "event": "context_1",
          "field": "Image",
          "op": "endswith_ci",
          "value": "\\updater.exe"
        },
        {
          "event": "context_1",
          "field": "ParentImage",
          "op": "endswith_ci",
          "value": "\\taskeng.exe"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context confirms the same benign scheduled windows update maintenance workflow with an explicit maintenance process or actor.
- Expected transition: `unmapped->unmapped`
- Contextual event descriptions: ["A related event confirms the approved workflow for scheduled windows update maintenance with affirmative benign telemetry."]
- Counter-evidence: A payload path, encoded interpreter command, suspicious persistence location, or unauthorized creator would change this interpretation.
- Benign near-miss: The same primitive with an untrusted path or suspicious command would be ambiguous or mapped: scheduled windows update maintenance.
- Allowed variations: ["Keep the provider-specific benign fields visible."]
- Disallowed variations: ["Do not reduce the family to label_status only or use unrelated negative text."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [],
  "comparison_technique_ids": []
}
```
- Planned instances: `12`

## `TF_UNMAP_SVC`

- Split: `test`
- Category: `unmapped`
- Behavior description: Signed service restart after patching
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4697`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Anchor selection rule: ContosoPatch service from Program Files; select the concrete provider fields that contain ContosoPatch, Program Files, LocalService
- Windows documentation: EID 4697 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4697]; EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "ServiceName",
      "op": "contains_ci",
      "value": "ContosoPatch"
    },
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "C:\\Program Files\\Contoso\\"
    },
    {
      "event": "anchor",
      "field": "ServiceAccount",
      "op": "contains_ci",
      "value": "LocalService"
    }
  ]
}
```
- Rationale: The service is a signed patching component in a protected location and has no public-path payload.
### Contextual ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "ServiceName",
          "op": "contains_ci",
          "value": "ContosoPatch"
        },
        {
          "event": "anchor",
          "field": "ServiceFileName",
          "op": "contains_ci",
          "value": "C:\\Program Files\\Contoso\\"
        },
        {
          "event": "anchor",
          "field": "ServiceAccount",
          "op": "contains_ci",
          "value": "LocalService"
        }
      ]
    },
    {
      "all": [
        {
          "event": "context_1",
          "field": "NewProcessName",
          "op": "endswith_ci",
          "value": "\\msiexec.exe"
        },
        {
          "event": "context_1",
          "field": "SubjectUserName",
          "op": "contains_ci",
          "value": "Administrator"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context confirms the same benign signed service restart after patching workflow with an explicit maintenance process or actor.
- Expected transition: `unmapped->unmapped`
- Contextual event descriptions: ["A related event confirms the approved workflow for signed service restart after patching with affirmative benign telemetry."]
- Counter-evidence: A payload path, encoded interpreter command, suspicious persistence location, or unauthorized creator would change this interpretation.
- Benign near-miss: The same primitive with an untrusted path or suspicious command would be ambiguous or mapped: signed service restart after patching.
- Allowed variations: ["Keep the provider-specific benign fields visible."]
- Disallowed variations: ["Do not reduce the family to label_status only or use unrelated negative text."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [],
  "comparison_technique_ids": []
}
```
- Planned instances: `12`

## `TF_UNMAP_ACCT`

- Split: `test`
- Category: `unmapped`
- Behavior description: Normal local backup-account provisioning
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4720`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Anchor selection rule: backupsvc created by Administrator; select the concrete provider fields that contain backupsvc, Administrator, backup
- Windows documentation: EID 4720 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4720]; EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TargetUserName",
      "op": "eq",
      "value": "backupsvc"
    },
    {
      "event": "anchor",
      "field": "SubjectUserName",
      "op": "eq",
      "value": "Administrator"
    },
    {
      "event": "anchor",
      "field": "SubjectLogonId",
      "op": "neq",
      "value": ""
    }
  ]
}
```
- Rationale: EID 4720 identifies the account and creator but does not prove that provisioning was authorized in the single view.
### Contextual ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "TargetUserName",
          "op": "eq",
          "value": "backupsvc"
        },
        {
          "event": "anchor",
          "field": "SubjectUserName",
          "op": "eq",
          "value": "Administrator"
        },
        {
          "event": "anchor",
          "field": "SubjectLogonId",
          "op": "neq",
          "value": ""
        }
      ]
    },
    {
      "all": [
        {
          "event": "context_1",
          "field": "NewProcessName",
          "op": "endswith_ci",
          "value": "\\account-provisioner.exe"
        },
        {
          "event": "context_1",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": "--create backupsvc --role backup"
        },
        {
          "event": "context_1",
          "field": "ParentProcessName",
          "op": "endswith_ci",
          "value": "\\management-agent.exe"
        },
        {
          "event": "context_1",
          "field": "SubjectUserName",
          "op": "eq",
          "value": "Administrator"
        }
      ]
    },
    {
      "relation": "temporal_before",
      "before": "context_1",
      "after": "anchor"
    },
    {
      "relation": "same_host",
      "events": [
        "context_1",
        "anchor"
      ]
    },
    {
      "relation": "same_logon",
      "events": [
        "context_1",
        "anchor"
      ]
    }
  ]
}
```
- Rationale: The linked Contoso account-provisioner process, approved management parent, explicit role, ordering, host, and logon establish an affirmative synthetic provisioning workflow.
- Expected transition: `ambiguous->unmapped`
- Contextual event descriptions: ["A related event confirms the approved workflow for normal local backup-account provisioning with affirmative benign telemetry."]
- Counter-evidence: A payload path, encoded interpreter command, suspicious persistence location, or unauthorized creator would change this interpretation.
- Benign near-miss: The same primitive with an untrusted path or suspicious command would be ambiguous or mapped: normal local backup-account provisioning.
- Allowed variations: ["Keep the provider-specific benign fields visible."]
- Disallowed variations: ["Do not reduce the family to label_status only or use unrelated negative text."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [],
  "comparison_technique_ids": []
}
```
- Planned instances: `12`

## `TF_UNMAP_REG`

- Split: `test`
- Category: `unmapped`
- Behavior description: Legitimate startup application registration
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `13`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: OneDrive Run value under Program Files; select the concrete provider fields that contain CurrentVersion\Run, Program Files, OneDrive
- Windows documentation: EID 13 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-13-registry-event]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TargetObject",
      "op": "contains_ci",
      "value": "\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
    },
    {
      "event": "anchor",
      "field": "Details",
      "op": "contains_ci",
      "value": "C:\\Program Files\\OneDrive\\"
    },
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\OneDrive.exe"
    }
  ]
}
```
- Rationale: A signed startup application under Program Files is an affirmative benign startup scenario.
### Contextual ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "TargetObject",
          "op": "contains_ci",
          "value": "\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
        },
        {
          "event": "anchor",
          "field": "Details",
          "op": "contains_ci",
          "value": "C:\\Program Files\\OneDrive\\"
        },
        {
          "event": "anchor",
          "field": "Image",
          "op": "endswith_ci",
          "value": "\\OneDrive.exe"
        }
      ]
    },
    {
      "all": [
        {
          "event": "context_1",
          "field": "Image",
          "op": "endswith_ci",
          "value": "\\OneDrive.exe"
        },
        {
          "event": "context_1",
          "field": "ParentImage",
          "op": "endswith_ci",
          "value": "\\explorer.exe"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context confirms the same benign legitimate startup application registration workflow with an explicit maintenance process or actor.
- Expected transition: `unmapped->unmapped`
- Contextual event descriptions: ["A related event confirms the approved workflow for legitimate startup application registration with affirmative benign telemetry."]
- Counter-evidence: A payload path, encoded interpreter command, suspicious persistence location, or unauthorized creator would change this interpretation.
- Benign near-miss: The same primitive with an untrusted path or suspicious command would be ambiguous or mapped: legitimate startup application registration.
- Allowed variations: ["Keep the provider-specific benign fields visible."]
- Disallowed variations: ["Do not reduce the family to label_status only or use unrelated negative text."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [],
  "comparison_technique_ids": []
}
```
- Planned instances: `12`

## `TF_UNMAP_EVTCLR`

- Split: `test`
- Category: `unmapped`
- Behavior description: Authorized log-retention maintenance
- Anchor telemetry: `Microsoft-Windows-Eventlog` / `Security` / EID `1102`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4698`; `context_2` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: Security log rotation by SYSTEM; select the concrete provider fields that contain SYSTEM, maintenance, rotation
- Windows documentation: EID 1102 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-1102]; EID 4698 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4698]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `3` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "EventID",
      "op": "eq",
      "value": 1102
    },
    {
      "event": "anchor",
      "field": "SubjectUserName",
      "op": "neq",
      "value": ""
    }
  ]
}
```
- Rationale: EID 1102 and subject metadata show a log clear, but the single view does not establish authorization or mechanism.
### Contextual ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "EventID",
      "op": "eq",
      "value": 1102
    },
    {
      "event": "context_1",
      "field": "TaskName",
      "op": "contains_ci",
      "value": "\\Contoso\\SecurityLogRetention"
    },
    {
      "event": "context_1",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "C:\\Program Files\\Contoso\\LogMaintenance\\logrotate.exe"
    },
    {
      "event": "context_2",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\logrotate.exe"
    },
    {
      "event": "context_2",
      "field": "ParentImage",
      "op": "endswith_ci",
      "value": "\\taskeng.exe"
    },
    {
      "event": "context_2",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "--clear Security"
    },
    {
      "relation": "process_then_task",
      "process": "context_2",
      "task": "context_1"
    },
    {
      "relation": "temporal_before",
      "before": "context_1",
      "after": "context_2"
    },
    {
      "relation": "temporal_before",
      "before": "context_2",
      "after": "anchor"
    },
    {
      "relation": "same_host",
      "events": [
        "context_1",
        "context_2",
        "anchor"
      ]
    },
    {
      "relation": "same_logon",
      "events": [
        "context_1",
        "context_2",
        "anchor"
      ]
    }
  ]
}
```
- Rationale: The approved synthetic SecurityLogRetention task, protected logrotate.exe path, taskeng parent, ordering, host, and logon jointly establish a benign maintenance workflow.
- Expected transition: `ambiguous->unmapped`
- Contextual event descriptions: ["A related event confirms the approved workflow for authorized log-retention maintenance with affirmative benign telemetry."]
- Counter-evidence: A payload path, encoded interpreter command, suspicious persistence location, or unauthorized creator would change this interpretation.
- Benign near-miss: The same primitive with an untrusted path or suspicious command would be ambiguous or mapped: authorized log-retention maintenance.
- Allowed variations: ["Keep the provider-specific benign fields visible."]
- Disallowed variations: ["Do not reduce the family to label_status only or use unrelated negative text."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [],
  "comparison_technique_ids": []
}
```
- Planned instances: `12`

## `TF_AMBIG_A`

- Split: `test`
- Category: `ambiguous`
- Behavior description: Unknown PowerShell script execution
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: powershell.exe -File C:\Users\Public\unknown.ps1; select the unknown.ps1 field
- Windows documentation: EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "EventID",
      "op": "eq",
      "value": 1
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "unknown.ps1"
    }
  ]
}
```
- Rationale: The event is observable and dual-use, but the single view lacks enough intent or authorization evidence.
### Contextual ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "EventID",
          "op": "eq",
          "value": 1
        },
        {
          "event": "anchor",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": "unknown.ps1"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context repeats the dual-use behavior without independently establishing mapped or affirmative benign evidence.
- Expected transition: `ambiguous->ambiguous`
- Contextual event descriptions: ["A related event confirms the same behavior but still lacks intent, authorization, or a mapped payload chain."]
- Counter-evidence: A signed approved workflow would support unmapped; a linked malicious payload or persistence chain would support mapped.
- Benign near-miss: The same primitive with no event fields or invalid telemetry would be a registry error, not a valid ambiguous case.
- Allowed variations: ["Keep the dual-use indicator and same-host relationship."]
- Disallowed variations: ["Do not use an empty predicate to represent uncertainty."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [],
  "comparison_technique_ids": [
    "T1059.001"
  ]
}
```
- Planned instances: `13`

## `TF_AMBIG_B`

- Split: `test`
- Category: `ambiguous`
- Behavior description: Dual-use cmd reconnaissance
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Anchor selection rule: cmd.exe /c whoami; select the whoami field
- Windows documentation: EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "EventID",
      "op": "eq",
      "value": 4688
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "whoami"
    }
  ]
}
```
- Rationale: The event is observable and dual-use, but the single view lacks enough intent or authorization evidence.
### Contextual ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "EventID",
          "op": "eq",
          "value": 4688
        },
        {
          "event": "anchor",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": "whoami"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context repeats the dual-use behavior without independently establishing mapped or affirmative benign evidence.
- Expected transition: `ambiguous->ambiguous`
- Contextual event descriptions: ["A related event confirms the same behavior but still lacks intent, authorization, or a mapped payload chain."]
- Counter-evidence: A signed approved workflow would support unmapped; a linked malicious payload or persistence chain would support mapped.
- Benign near-miss: The same primitive with no event fields or invalid telemetry would be a registry error, not a valid ambiguous case.
- Allowed variations: ["Keep the dual-use indicator and same-host relationship."]
- Disallowed variations: ["Do not use an empty predicate to represent uncertainty."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [],
  "comparison_technique_ids": []
}
```
- Planned instances: `13`

## `TF_AMBIG_C`

- Split: `test`
- Category: `ambiguous`
- Behavior description: Unknown scheduled task payload
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4698`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4698`
- Anchor selection rule: \CacheRefresh runs C:\ProgramData\cache.exe; select the cache.exe field
- Windows documentation: EID 4698 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4698]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "EventID",
      "op": "eq",
      "value": 4698
    },
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "cache.exe"
    }
  ]
}
```
- Rationale: The event is observable and dual-use, but the single view lacks enough intent or authorization evidence.
### Contextual ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "EventID",
          "op": "eq",
          "value": 4698
        },
        {
          "event": "anchor",
          "field": "TaskContent",
          "op": "contains_ci",
          "value": "cache.exe"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context repeats the dual-use behavior without independently establishing mapped or affirmative benign evidence.
- Expected transition: `ambiguous->ambiguous`
- Contextual event descriptions: ["A related event confirms the same behavior but still lacks intent, authorization, or a mapped payload chain."]
- Counter-evidence: A signed approved workflow would support unmapped; a linked malicious payload or persistence chain would support mapped.
- Benign near-miss: The same primitive with no event fields or invalid telemetry would be a registry error, not a valid ambiguous case.
- Allowed variations: ["Keep the dual-use indicator and same-host relationship."]
- Disallowed variations: ["Do not use an empty predicate to represent uncertainty."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [],
  "comparison_technique_ids": []
}
```
- Planned instances: `12`

## `TF_AMBIG_D`

- Split: `test`
- Category: `ambiguous`
- Behavior description: Dual-use RunOnce mutation
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `13`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `13`
- Anchor selection rule: RunOnce points to AppData helper.exe; select the AppData field
- Windows documentation: EID 13 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-13-registry-event]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "EventID",
      "op": "eq",
      "value": 13
    },
    {
      "event": "anchor",
      "field": "Details",
      "op": "contains_ci",
      "value": "AppData"
    }
  ]
}
```
- Rationale: The event is observable and dual-use, but the single view lacks enough intent or authorization evidence.
### Contextual ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "EventID",
          "op": "eq",
          "value": 13
        },
        {
          "event": "anchor",
          "field": "Details",
          "op": "contains_ci",
          "value": "AppData"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context repeats the dual-use behavior without independently establishing mapped or affirmative benign evidence.
- Expected transition: `ambiguous->ambiguous`
- Contextual event descriptions: ["A related event confirms the same behavior but still lacks intent, authorization, or a mapped payload chain."]
- Counter-evidence: A signed approved workflow would support unmapped; a linked malicious payload or persistence chain would support mapped.
- Benign near-miss: The same primitive with no event fields or invalid telemetry would be a registry error, not a valid ambiguous case.
- Allowed variations: ["Keep the dual-use indicator and same-host relationship."]
- Disallowed variations: ["Do not use an empty predicate to represent uncertainty."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [],
  "comparison_technique_ids": []
}
```
- Planned instances: `12`

## `TF_T1059_001_DEV`

- Split: `dev`
- Category: `mapped_single`
- Behavior description: PowerShell Core launched by wscript with encoded arguments
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `3`
- Anchor selection rule: pwsh.exe child of wscript.exe with -EncodedCommand
- Windows documentation: EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]; EID 3 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-3-network-connection]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1059.001` (PowerShell)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\pwsh.exe"
    },
    {
      "event": "anchor",
      "field": "ParentImage",
      "op": "endswith_ci",
      "value": "\\wscript.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "-EncodedCommand"
    }
  ]
}
```
- Rationale: The DEV-only powershell core launched by wscript with encoded arguments has concrete technique-specific evidence in its anchor event.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1059.001` (PowerShell)
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "Image",
          "op": "endswith_ci",
          "value": "\\pwsh.exe"
        },
        {
          "event": "anchor",
          "field": "ParentImage",
          "op": "endswith_ci",
          "value": "\\wscript.exe"
        },
        {
          "event": "anchor",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": "-EncodedCommand"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context confirms the DEV-only powershell core launched by wscript with encoded arguments behavior through a related telemetry event.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A structurally distinct DEV context event corroborates powershell core launched by wscript with encoded arguments."]
- Counter-evidence: An approved signed tool or managed provisioning workflow would be benign counter-evidence.
- Benign near-miss: A routine counterpart of powershell core launched by wscript with encoded arguments with protected paths and approved ownership.
- Allowed variations: ["Keep this family structurally distinct from TEST families."]
- Disallowed variations: ["Do not vary only IDs, timestamps, or hosts."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1059.001",
      "technique_name": "PowerShell",
      "url": "https://attack.mitre.org/techniques/T1059/001"
    }
  ],
  "comparison_technique_ids": [
    "T1059.001"
  ]
}
```
- Planned instances: `2`

## `TF_T1059_003_DEV`

- Split: `dev`
- Category: `mapped_single`
- Behavior description: Command Shell delayed expansion launched by mshta
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Anchor selection rule: cmd.exe child of mshta.exe uses delayed expansion and call
- Windows documentation: EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1059.003` (Windows Command Shell)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "NewProcessName",
      "op": "endswith_ci",
      "value": "\\cmd.exe"
    },
    {
      "event": "anchor",
      "field": "ParentProcessName",
      "op": "endswith_ci",
      "value": "\\mshta.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "/v:on"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "call "
    }
  ]
}
```
- Rationale: The DEV-only command shell delayed expansion launched by mshta has concrete technique-specific evidence in its anchor event.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1059.003` (Windows Command Shell)
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "NewProcessName",
          "op": "endswith_ci",
          "value": "\\cmd.exe"
        },
        {
          "event": "anchor",
          "field": "ParentProcessName",
          "op": "endswith_ci",
          "value": "\\mshta.exe"
        },
        {
          "event": "anchor",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": "/v:on"
        },
        {
          "event": "anchor",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": "call "
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context confirms the DEV-only command shell delayed expansion launched by mshta behavior through a related telemetry event.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A structurally distinct DEV context event corroborates command shell delayed expansion launched by mshta."]
- Counter-evidence: An approved signed tool or managed provisioning workflow would be benign counter-evidence.
- Benign near-miss: A routine counterpart of command shell delayed expansion launched by mshta with protected paths and approved ownership.
- Allowed variations: ["Keep this family structurally distinct from TEST families."]
- Disallowed variations: ["Do not vary only IDs, timestamps, or hosts."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1059.003",
      "technique_name": "Windows Command Shell",
      "url": "https://attack.mitre.org/techniques/T1059/003"
    }
  ],
  "comparison_technique_ids": [
    "T1059.003"
  ]
}
```
- Planned instances: `2`

## `TF_T1053_005_DEV`

- Split: `dev`
- Category: `mapped_single`
- Behavior description: Hidden scheduled task launching rundll32 DLL entry point
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4698`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: TaskContent has a hidden trigger and rundll32.exe DLL entry point
- Windows documentation: EID 4698 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4698]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1053.005` (Scheduled Task)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "Hidden"
    },
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "rundll32.exe"
    },
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": ".dll"
    }
  ]
}
```
- Rationale: The DEV-only hidden scheduled task launching rundll32 dll entry point has concrete technique-specific evidence in its anchor event.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1053.005` (Scheduled Task)
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "TaskContent",
          "op": "contains_ci",
          "value": "Hidden"
        },
        {
          "event": "anchor",
          "field": "TaskContent",
          "op": "contains_ci",
          "value": "rundll32.exe"
        },
        {
          "event": "anchor",
          "field": "TaskContent",
          "op": "contains_ci",
          "value": ".dll"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context confirms the DEV-only hidden scheduled task launching rundll32 dll entry point behavior through a related telemetry event.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A structurally distinct DEV context event corroborates hidden scheduled task launching rundll32 dll entry point."]
- Counter-evidence: An approved signed tool or managed provisioning workflow would be benign counter-evidence.
- Benign near-miss: A routine counterpart of hidden scheduled task launching rundll32 dll entry point with protected paths and approved ownership.
- Allowed variations: ["Keep this family structurally distinct from TEST families."]
- Disallowed variations: ["Do not vary only IDs, timestamps, or hosts."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1053.005",
      "technique_name": "Scheduled Task",
      "url": "https://attack.mitre.org/techniques/T1053/005"
    }
  ],
  "comparison_technique_ids": [
    "T1053.005"
  ]
}
```
- Planned instances: `2`

## `TF_T1543_003_DEV`

- Split: `dev`
- Category: `mapped_single`
- Behavior description: Windows service DLL hosted by svchost under LocalService
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4697`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `11`
- Anchor selection rule: ServiceFileName uses svchost -k and a protected service DLL under LocalService
- Windows documentation: EID 4697 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4697]; EID 11 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1543.003` (Windows Service)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "svchost.exe -k"
    },
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "ServiceDll"
    },
    {
      "event": "anchor",
      "field": "ServiceAccount",
      "op": "contains_ci",
      "value": "LocalService"
    }
  ]
}
```
- Rationale: The DEV-only windows service dll hosted by svchost under localservice has concrete technique-specific evidence in its anchor event.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1543.003` (Windows Service)
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "ServiceFileName",
          "op": "contains_ci",
          "value": "svchost.exe -k"
        },
        {
          "event": "anchor",
          "field": "ServiceFileName",
          "op": "contains_ci",
          "value": "ServiceDll"
        },
        {
          "event": "anchor",
          "field": "ServiceAccount",
          "op": "contains_ci",
          "value": "LocalService"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context confirms the DEV-only windows service dll hosted by svchost under localservice behavior through a related telemetry event.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A structurally distinct DEV context event corroborates windows service dll hosted by svchost under localservice."]
- Counter-evidence: An approved signed tool or managed provisioning workflow would be benign counter-evidence.
- Benign near-miss: A routine counterpart of windows service dll hosted by svchost under localservice with protected paths and approved ownership.
- Allowed variations: ["Keep this family structurally distinct from TEST families."]
- Disallowed variations: ["Do not vary only IDs, timestamps, or hosts."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1543.003",
      "technique_name": "Windows Service",
      "url": "https://attack.mitre.org/techniques/T1543/003"
    }
  ],
  "comparison_technique_ids": [
    "T1543.003"
  ]
}
```
- Planned instances: `2`

## `TF_T1136_001_DEV`

- Split: `dev`
- Category: `mapped_single`
- Behavior description: PowerShell Core creates a local service account during member-server provisioning
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4720`
- Anchor selection rule: pwsh.exe invokes New-LocalUser with AccountNeverExpires on a member server
- Windows documentation: EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]; EID 4720 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4720]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1136.001` (Local Account)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\pwsh.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "New-LocalUser"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "-AccountNeverExpires"
    }
  ]
}
```
- Rationale: The DEV-only powershell core creates a local service account during member-server provisioning has concrete technique-specific evidence in its anchor event.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1136.001` (Local Account)
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "Image",
          "op": "endswith_ci",
          "value": "\\pwsh.exe"
        },
        {
          "event": "anchor",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": "New-LocalUser"
        },
        {
          "event": "anchor",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": "-AccountNeverExpires"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context confirms the DEV-only powershell core creates a local service account during member-server provisioning behavior through a related telemetry event.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A structurally distinct DEV context event corroborates powershell core creates a local service account during member-server provisioning."]
- Counter-evidence: An approved signed tool or managed provisioning workflow would be benign counter-evidence.
- Benign near-miss: A routine counterpart of powershell core creates a local service account during member-server provisioning with protected paths and approved ownership.
- Allowed variations: ["Keep this family structurally distinct from TEST families."]
- Disallowed variations: ["Do not vary only IDs, timestamps, or hosts."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1136.001",
      "technique_name": "Local Account",
      "url": "https://attack.mitre.org/techniques/T1136/001"
    }
  ],
  "comparison_technique_ids": [
    "T1136.001"
  ]
}
```
- Planned instances: `2`
- Host constraints:
```json
{
  "allowed_host_roles": [
    "workstation",
    "member_server"
  ],
  "forbidden_hosts": [
    "DC01"
  ]
}
```

## `TF_T1547_001_DEV`

- Split: `dev`
- Category: `mapped_single`
- Behavior description: Startup-folder URL shortcut created by a login helper
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `11`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Anchor selection rule: Startup folder receives a .url file with a file-create event
- Windows documentation: EID 11 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1547.001` (Registry Run Keys / Startup Folder)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TargetFilename",
      "op": "contains_ci",
      "value": "\\Startup\\"
    },
    {
      "event": "anchor",
      "field": "TargetFilename",
      "op": "endswith_ci",
      "value": ".url"
    },
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\loginhelper.exe"
    }
  ]
}
```
- Rationale: The DEV-only startup-folder url shortcut created by a login helper has concrete technique-specific evidence in its anchor event.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1547.001` (Registry Run Keys / Startup Folder)
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "TargetFilename",
          "op": "contains_ci",
          "value": "\\Startup\\"
        },
        {
          "event": "anchor",
          "field": "TargetFilename",
          "op": "endswith_ci",
          "value": ".url"
        },
        {
          "event": "anchor",
          "field": "Image",
          "op": "endswith_ci",
          "value": "\\loginhelper.exe"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context confirms the DEV-only startup-folder url shortcut created by a login helper behavior through a related telemetry event.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A structurally distinct DEV context event corroborates startup-folder url shortcut created by a login helper."]
- Counter-evidence: An approved signed tool or managed provisioning workflow would be benign counter-evidence.
- Benign near-miss: A routine counterpart of startup-folder url shortcut created by a login helper with protected paths and approved ownership.
- Allowed variations: ["Keep this family structurally distinct from TEST families."]
- Disallowed variations: ["Do not vary only IDs, timestamps, or hosts."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1547.001",
      "technique_name": "Registry Run Keys / Startup Folder",
      "url": "https://attack.mitre.org/techniques/T1547/001"
    }
  ],
  "comparison_technique_ids": [
    "T1547.001"
  ]
}
```
- Planned instances: `2`

## `TF_T1685_005_DEV`

- Split: `dev`
- Category: `mapped_single`
- Behavior description: Security audit log clear after a remote PowerShell maintenance session
- Anchor telemetry: `Microsoft-Windows-Eventlog` / `Security` / EID `1102`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4688`
- Anchor selection rule: Windows Eventlog EID 1102 with a populated SubjectLogonId
- Windows documentation: EID 1102 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-1102]; EID 4688 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4688]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "EventID",
      "op": "eq",
      "value": 1102
    },
    {
      "event": "anchor",
      "field": "SubjectLogonId",
      "op": "neq",
      "value": ""
    }
  ]
}
```
- Rationale: EID 1102 establishes a cleared Security audit log but does not identify the PowerShell mechanism in the single view.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1685.005` (Clear Windows Event Logs)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "EventID",
      "op": "eq",
      "value": 1102
    },
    {
      "event": "context_1",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "Clear-EventLog"
    },
    {
      "relation": "temporal_before",
      "before": "context_1",
      "after": "anchor"
    },
    {
      "relation": "same_logon",
      "events": [
        "context_1",
        "anchor"
      ]
    }
  ]
}
```
- Rationale: A linked PowerShell Clear-EventLog process supplies the mechanism evidence for T1685.005.
- Expected transition: `ambiguous->mapped`
- Contextual event descriptions: ["A structurally distinct DEV context event corroborates security audit log clear after a remote powershell maintenance session."]
- Counter-evidence: An approved signed tool or managed provisioning workflow would be benign counter-evidence.
- Benign near-miss: A routine counterpart of security audit log clear after a remote powershell maintenance session with protected paths and approved ownership.
- Allowed variations: ["Keep this family structurally distinct from TEST families."]
- Disallowed variations: ["Do not vary only IDs, timestamps, or hosts."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1685.005",
      "technique_name": "Clear Windows Event Logs",
      "url": "https://attack.mitre.org/techniques/T1685/005"
    }
  ],
  "comparison_technique_ids": [
    "T1685.005"
  ]
}
```
- Planned instances: `2`

## `TF_T1105_DEV`

- Split: `dev`
- Category: `mapped_single`
- Behavior description: MSI transfer initiated by msiexec with a remote package URL
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `11`
- Anchor selection rule: msiexec.exe command line contains an external MSI URL and passive install option
- Windows documentation: EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]; EID 11 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1105` (Ingress Tool Transfer)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\msiexec.exe"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": "https://files.example.invalid/"
    },
    {
      "event": "anchor",
      "field": "CommandLine",
      "op": "contains_ci",
      "value": ".msi"
    }
  ]
}
```
- Rationale: The DEV-only msi transfer initiated by msiexec with a remote package url has concrete technique-specific evidence in its anchor event.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1105` (Ingress Tool Transfer)
- Evidence predicate:
```json
{
  "all": [
    {
      "all": [
        {
          "event": "anchor",
          "field": "Image",
          "op": "endswith_ci",
          "value": "\\msiexec.exe"
        },
        {
          "event": "anchor",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": "https://files.example.invalid/"
        },
        {
          "event": "anchor",
          "field": "CommandLine",
          "op": "contains_ci",
          "value": ".msi"
        }
      ]
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: Context confirms the DEV-only msi transfer initiated by msiexec with a remote package url behavior through a related telemetry event.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["A structurally distinct DEV context event corroborates msi transfer initiated by msiexec with a remote package url."]
- Counter-evidence: An approved signed tool or managed provisioning workflow would be benign counter-evidence.
- Benign near-miss: A routine counterpart of msi transfer initiated by msiexec with a remote package url with protected paths and approved ownership.
- Allowed variations: ["Keep this family structurally distinct from TEST families."]
- Disallowed variations: ["Do not vary only IDs, timestamps, or hosts."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1105",
      "technique_name": "Ingress Tool Transfer",
      "url": "https://attack.mitre.org/techniques/T1105"
    }
  ],
  "comparison_technique_ids": [
    "T1105"
  ]
}
```
- Planned instances: `2`

## `TF_MULTI_DEV_A`

- Split: `dev`
- Category: `mapped_multi`
- Behavior description: Run-key startup persistence followed by service installation
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `13`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4697`
- Anchor selection rule: Run key points to a protected DEV payload and is followed by a service install
- Windows documentation: EID 13 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-13-registry-event]; EID 4697 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4697]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1547.001` (Registry Run Keys / Startup Folder)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TargetObject",
      "op": "contains_ci",
      "value": "\\Run\\"
    },
    {
      "event": "anchor",
      "field": "Details",
      "op": "contains_ci",
      "value": "DEV\\agent.exe"
    }
  ]
}
```
- Rationale: The DEV single view independently supports a Run-key persistence artifact.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1547.001` (Registry Run Keys / Startup Folder), `T1543.003` (Windows Service)
- Evidence predicate:
```json
{
  "T1547.001": {
    "all": [
      {
        "event": "anchor",
        "field": "TargetObject",
        "op": "contains_ci",
        "value": "\\Run\\"
      },
      {
        "event": "anchor",
        "field": "Details",
        "op": "contains_ci",
        "value": "DEV\\agent.exe"
      }
    ]
  },
  "T1543.003": {
    "all": [
      {
        "event": "context_1",
        "field": "ServiceFileName",
        "op": "contains_ci",
        "value": "DEV\\agent.exe"
      },
      {
        "event": "context_1",
        "field": "ServiceAccount",
        "op": "contains_ci",
        "value": "LocalService"
      },
      {
        "relation": "same_host",
        "events": [
          "anchor",
          "context_1"
        ]
      }
    ]
  }
}
```
- Rationale: The DEV contextual view supplies separate Run-key and service-install evidence.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["The DEV payload is registered for startup and then installed as a service under a separate service event."]
- Counter-evidence: A managed agent may use both startup and service registration during deployment; signed payload and change record are counter-evidence.
- Benign near-miss: A single Run-key update with no service installation.
- Allowed variations: ["Keep two independent contextual predicates."]
- Disallowed variations: ["Do not collapse the labels into one global rule."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1547.001",
      "technique_name": "Registry Run Keys / Startup Folder",
      "url": "https://attack.mitre.org/techniques/T1547/001"
    },
    {
      "technique_id": "T1543.003",
      "technique_name": "Windows Service",
      "url": "https://attack.mitre.org/techniques/T1543/003"
    }
  ],
  "comparison_technique_ids": [
    "T1547.001",
    "T1543.003"
  ]
}
```
- Planned instances: `2`

## `TF_MULTI_DEV_B`

- Split: `dev`
- Category: `mapped_multi`
- Behavior description: Scheduled task launches PowerShell which downloads a package
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4698`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `1`; `context_2` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `11`
- Anchor selection rule: DEV task content invokes pwsh.exe and references a remote package
- Windows documentation: EID 4698 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4698]; EID 1 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create]; EID 11 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create]
- Telemetry combinations covered: `3` registry event specifications
### Single-view ground truth
- Status: `mapped`
- Technique(s): `T1053.005` (Scheduled Task)
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "TaskName",
      "op": "contains_ci",
      "value": "\\DEV\\PackageRefresh"
    },
    {
      "event": "anchor",
      "field": "TaskContent",
      "op": "contains_ci",
      "value": "pwsh.exe"
    }
  ]
}
```
- Rationale: The DEV single view independently supports scheduled-task creation.
### Contextual ground truth
- Status: `mapped`
- Technique(s): `T1053.005` (Scheduled Task), `T1059.001` (PowerShell), `T1105` (Ingress Tool Transfer)
- Evidence predicate:
```json
{
  "T1053.005": {
    "all": [
      {
        "event": "anchor",
        "field": "TaskName",
        "op": "contains_ci",
        "value": "\\DEV\\PackageRefresh"
      },
      {
        "event": "anchor",
        "field": "TaskContent",
        "op": "contains_ci",
        "value": "pwsh.exe"
      }
    ]
  },
  "T1059.001": {
    "all": [
      {
        "event": "context_1",
        "field": "Image",
        "op": "endswith_ci",
        "value": "\\pwsh.exe"
      },
      {
        "event": "context_1",
        "field": "CommandLine",
        "op": "contains_ci",
        "value": "-File"
      },
      {
        "relation": "process_then_task",
        "process": "context_1",
        "task": "anchor"
      }
    ]
  },
  "T1105": {
    "all": [
      {
        "event": "context_1",
        "field": "CommandLine",
        "op": "contains_ci",
        "value": "https://files.example.invalid/"
      },
      {
        "event": "context_2",
        "field": "TargetFilename",
        "op": "contains_ci",
        "value": "DEV\\cache"
      },
      {
        "relation": "process_then_file",
        "process": "context_1",
        "file": "context_2"
      }
    ]
  }
}
```
- Rationale: The DEV contextual view independently supports the task object, PowerShell execution, and transfer artifact.
- Expected transition: `mapped->mapped`
- Contextual event descriptions: ["The DEV task starts pwsh.exe, which downloads a package and writes the cache file."]
- Counter-evidence: A managed software updater may use this chain; signed script, trusted endpoint, and deployment ticket are counter-evidence.
- Benign near-miss: A scheduled task with a local signed script and no transfer behavior.
- Allowed variations: ["Use three independent contextual predicates."]
- Disallowed variations: ["Do not rely on cardinality alone."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [
    {
      "technique_id": "T1053.005",
      "technique_name": "Scheduled Task",
      "url": "https://attack.mitre.org/techniques/T1053/005"
    },
    {
      "technique_id": "T1059.001",
      "technique_name": "PowerShell",
      "url": "https://attack.mitre.org/techniques/T1059/001"
    },
    {
      "technique_id": "T1105",
      "technique_name": "Ingress Tool Transfer",
      "url": "https://attack.mitre.org/techniques/T1105"
    }
  ],
  "comparison_technique_ids": [
    "T1053.005",
    "T1059.001",
    "T1105"
  ]
}
```
- Planned instances: `2`

## `TF_UNMAP_DEV`

- Split: `dev`
- Category: `unmapped`
- Behavior description: Signed vendor updater writes an ordinary cache file
- Anchor telemetry: `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `3`
- Context telemetry: `context_1` = `Microsoft-Windows-Sysmon` / `Microsoft-Windows-Sysmon/Operational` / EID `11`
- Anchor selection rule: Sysmon EID 3 from a signed updater to an allowlisted update endpoint
- Windows documentation: EID 3 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-3-network-connection]; EID 11 [https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-11-file-create]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\ContosoUpdater.exe"
    },
    {
      "event": "anchor",
      "field": "DestinationIp",
      "op": "in",
      "value": [
        "198.51.100.20",
        "203.0.113.20"
      ]
    },
    {
      "not": {
        "event": "anchor",
        "field": "Image",
        "op": "contains_ci",
        "value": "\\Users\\Public\\"
      }
    }
  ]
}
```
- Rationale: The network event is paired with a signed vendor updater and an allowlisted endpoint, supporting a benign update workflow.
### Contextual ground truth
- Status: `unmapped`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "Image",
      "op": "endswith_ci",
      "value": "\\ContosoUpdater.exe"
    },
    {
      "event": "context_1",
      "field": "TargetFilename",
      "op": "contains_ci",
      "value": "\\Contoso\\Cache\\"
    },
    {
      "not": {
        "event": "context_1",
        "field": "TargetFilename",
        "op": "contains_ci",
        "value": "\\Users\\Public\\"
      }
    },
    {
      "relation": "network_then_file",
      "network": "anchor",
      "file": "context_1"
    }
  ]
}
```
- Rationale: The contextual cache file confirms ordinary updater activity without suspicious payload or persistence evidence.
- Expected transition: `unmapped->unmapped`
- Contextual event descriptions: ["The signed updater creates a cache file under its protected vendor directory."]
- Counter-evidence: An untrusted process, non-allowlisted endpoint, or executable written to a user-writable path would change the interpretation.
- Benign near-miss: A network-only event without signer, endpoint, or cache-path evidence would be ambiguous.
- Allowed variations: ["Keep signer/path/endpoint evidence."]
- Disallowed variations: ["Do not reduce the family to label_status only."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [],
  "comparison_technique_ids": []
}
```
- Planned instances: `6`

## `TF_AMBIG_DEV`

- Split: `dev`
- Category: `ambiguous`
- Behavior description: Unknown signedness service registration with no execution context
- Anchor telemetry: `Microsoft-Windows-Security-Auditing` / `Security` / EID `4697`
- Context telemetry: `context_1` = `Microsoft-Windows-Security-Auditing` / `Security` / EID `4697`
- Anchor selection rule: Security 4697 registers a service from an unknown ProgramData path
- Windows documentation: EID 4697 [https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/event-4697]
- Telemetry combinations covered: `2` registry event specifications
### Single-view ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "C:\\ProgramData\\"
    },
    {
      "event": "anchor",
      "field": "ServiceStartType",
      "op": "eq",
      "value": "3"
    }
  ]
}
```
- Rationale: A ProgramData service with demand start is observable but lacks signer, creator, and execution context needed for attribution.
### Contextual ground truth
- Status: `ambiguous`
- Technique(s): none
- Evidence predicate:
```json
{
  "all": [
    {
      "event": "anchor",
      "field": "ServiceFileName",
      "op": "contains_ci",
      "value": "C:\\ProgramData\\"
    },
    {
      "event": "context_1",
      "field": "ServiceName",
      "op": "contains_ci",
      "value": "Telemetry"
    },
    {
      "relation": "same_host",
      "events": [
        "anchor",
        "context_1"
      ]
    }
  ]
}
```
- Rationale: The related service metadata remains dual-use and does not resolve to mapped or affirmative benign evidence.
- Expected transition: `ambiguous->ambiguous`
- Contextual event descriptions: ["A related service record confirms the same dual-use installation but adds no signer or creator evidence."]
- Counter-evidence: A signed vendor binary and deployment record would make this unmapped; a suspicious creator and execution chain would make it mapped.
- Benign near-miss: A missing or unsupported service event would be invalid registry data, not ambiguity.
- Allowed variations: ["Keep the valid 4697 schema and the explicit uncertainty rationale."]
- Disallowed variations: ["Do not use provider any or EventID zero."]
- ATT&CK source:
```json
{
  "catalog": "MITRE ATT&CK Enterprise v19.2",
  "catalog_url": "https://attack.mitre.org/versions/v19/techniques/",
  "technique_references": [],
  "comparison_technique_ids": []
}
```
- Planned instances: `4`
