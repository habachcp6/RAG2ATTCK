# Stage B relation contract

The user explicitly approved the corrections in
`reports/T05_T10_stage_b_preflight_blockers.md` on 2026-09-19, including the
Sysmon 1 to Sysmon 3 context correction and explicit direction/identity relations.
All label statuses, technique sets, quotas, splits and the seed remain unchanged.

All ordered relations require the same host and strict chronological order.
`process_then_task/service` describes registration by an actor process, with the
same actor identity. `task_then_process/service_then_process/registry_then_process`
describes subsequent activation and requires the executable to appear in the
task content, service image or Run value respectively. An actor registering a
service need not be the service account subsequently running the payload.

`same_process` uses ProcessGuid when both events have it, otherwise the canonical
PID: NewProcessId for 4688, ProcessId for Sysmon. In 4688, ProcessId is the creator
PID and must not be mistaken for the newly created process. A parent-child edge
matches the child's parent GUID or creator PID to its parent. A parent network
event preceding a child matches ProcessGuid to ParentProcessGuid.

`process_then_network/registry` and `network_then_file` require same process
identity. `process_then_file` requires either direct same-process identity or a
same-host, same-actor invocation containing the exact destination filename (for
a shell that delegates writing to a utility). This latter relation is resource
correlation, not proof of an unobserved child-process GUID. `file_then_process`
requires the pre-existing filename in the later process command line.

`same_user` means the actor: SubjectUserName for Security and User for Sysmon,
never TargetUserName (the new account). `same_logon` compares SubjectLogonId or
LogonId. `same_host` compares Computer. Ground truth is copied from the approved
registry per view; predicate execution validates evidence and never predicts labels.
