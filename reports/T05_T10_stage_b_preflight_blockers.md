# Stage B semantic preflight: generation stopped

> Historical preflight record. On 2026-09-19 the user explicitly approved the
> listed telemetry/relation corrections and continuation of Stage B. They are
> implemented in the registry and `docs/synthetic/relation_contract.md`.
> The corrected approved registry SHA-256 is
> `8495842d24b6a4635e125a1d21dfad811d776efcc8ba138f5441f88457f3350c`.
> The stop status below describes the pre-approval state, not current execution.

## Verified starting state

- Base main: `827eb8b147efc756146261649399ee9e40a1e634` (clean before Stage B).
- Branch: `task/t05-t10-stage-b-data-freeze`.
- Registry SHA-256: `ce9e3d79b827f59a2975be356f0430ebe6939f8012519b476c191360b36b3b7a`.
- `uv lock --check --offline`: PASS.
- `uv sync --frozen`: PASS.
- `uv pip check`: PASS.
- `uv run python scripts/validate_synthetic_registry.py`: `passed=true`, 64 families, 52 test, 12 dev, 670 planned instances.
- `uv run pytest tests/test_synthetic.py -q`: 116 passed.

The user's Stage B instruction explicitly approves proceeding from Stage A. The
registry's older `awaiting_human_semantic_approval` metadata is not treated as a
new approval blocker. The issues below concern the content of the specification.

No candidate or frozen dataset has been generated. Planned counts are not
generated-dataset evidence. Stage A's current DSL validator checks operand names,
available fields and event classes; it does not execute process-identity or temporal
relations over concrete events. Passing its tests therefore does not resolve these
findings.

## B01: two process-creation events for one process lifetime

**Confirmed telemetry conflict.** Family `TF_T1059_001_F` allocates 12 TEST pairs.

- Anchor: Sysmon Event ID 1, PowerShell with reflective-loading command arguments.
- Context: also Sysmon Event ID 1, with selection rule `Same PowerShell process after the reflective load`.
- Predicate: `same_process(anchor, context_1)`.
- Rationale: a later event shares that process identity and confirms the execution chain.

Sysmon Event ID 1 records a newly created process; ProcessGuid identifies that
process. Event ID 3 records network activity linked by ProcessId/ProcessGuid.
Consequently, a later new process-creation event cannot serve as a follow-on
activity observation of that same process lifetime. PID reuse would identify a
different process; replaying the original creation record would not provide new
post-load evidence. Source: [Microsoft Sysmon event documentation](https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon#event-id-1-process-create).

**Concrete proposed correction, not applied:** keep anchor, labels, split and all
12 instances; replace context_1 with Sysmon Event ID 3 for a follow-on connection
of that PowerShell process, using documentation-safe indicators. Keep same-process
identity correlation. Update its event selection, context description and telemetry
source list to Event ID 3. Reword the rationale to distinguish command-line evidence
of the invocation from corroborating same-process network activity; network activity
alone does not demonstrate a successful reflective load. This changes approved
context telemetry, so it is not an implementation-only default.

## B02: ordered relation contract is inconsistent with execution chronology

**Requires explicit relation semantics before implementing the evaluator.**
`TF_UNMAP_EVTCLR` (12 TEST pairs) contains both:

```json
{"relation":"process_then_task","process":"context_2","task":"context_1"}
{"relation":"temporal_before","before":"context_1","after":"context_2"}
```

Here context_1 is task registration (4698), context_2 is the task-launched
logrotate.exe process (Sysmon 1), and the anchor is the subsequent log-clear
outcome (1102). If `process_then_task` means ordered process-to-task activity,
the two predicates require both t2 < t1 and t1 < t2. No timestamps satisfy that.
If it is intended as an unordered association, that meaning needs to be recorded
explicitly; silently dropping the direction would make a new methodological choice.

The distinction matters because `TF_MULTI_A` uses the same relation for a process
that registers a task, while the following families use it for execution after
registration:

- `TF_T1053_005_A`, `TF_T1053_005_B`, `TF_T1053_005_D`, `TF_T1053_005_E`.
- `TF_MULTI_DEV_B`, `TF_UNMAP_EVTCLR`.

Related direction/identity discrepancies requiring the same bounded review:

| Family | Approved text | Existing relation |
|---|---|---|
| TF_T1059_001_C | WMI network event precedes PowerShell child | process_then_network with PowerShell anchor as process |
| TF_T1059_003_A | cmd.exe creates a child process | same_process, although parent/child identities differ |
| TF_T1059_003_C | Batch file exists before the cmd.exe creation record | process_then_file from cmd.exe to that file |
| TF_T1543_003_B | Service payload starts after installation | process_then_service from payload to installation |
| TF_T1543_003_E | Service-host process starts after installation | process_then_service from payload to installation |
| TF_T1547_001_E | RunOnce payload executes after registry mutation | process_then_registry from payload to mutation |

**Concrete proposed correction, not applied:** preserve the behavior descriptions,
labels, quotas and family splits. Define ordered registration/creation relations
separately from task/service/registry-triggered execution relations, and use
parent_child for an actual parent/child pair. Define exact field correlations and
temporal direction for each relation before implementing it. Make the validator
reject impossible temporal cycles and repeated process creation for a single
process lifetime. Do not implement every `*_then_*` as an unordered same-host test.

## Required decision and resumption

The supplied task's section 49 requires stopping and reporting a genuine frozen
specification defect before modifying methodology. This report supplies that stop
evidence; it does not revise the approved registry.

Approve the bounded telemetry/relation corrections above, then regenerate the
Stage A review package, rerun Stage A gates and lock the new explicitly approved
registry hash. Resume all Stage B work from that hash. Keep ATT&CK v19.2, the eight
techniques, seed 20260915, 670 pairs, 640/30 split, quotas, view-level label policy,
and family holdout unchanged. Historical Windows-APT blockers remain separate.

Status: **STAGE B INCOMPLETE**. No freeze, reproduction, Stage B CI, PR, or Data &
Ground Truth completion is claimed.
