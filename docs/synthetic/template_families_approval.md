# RAG2ATTCK Synthetic Benchmark — Template Families Approval Package

**Generated**: 2026-09-17 18:59 UTC
**Registry hash (SHA-256)**: `dead71546fc0f158...`
**Total families**: 64 (52 test + 12 dev)
**Total scenario pairs**: 670 (640 test + 30 dev = 670)

---

## 1. Quota Verification

| Category | Test | Dev | Total | Target |
|---|---:|---:|---:|---:|
| Mapped single-label | 400 | 16 | 416 | 416 |
| Mapped multi-label | 40 | 4 | 44 | 44 |
| Unmapped | 150 | 6 | 156 | 156 |
| Ambiguous | 50 | 4 | 54 | 54 |
| **Total** | **640** | **30** | **670** | **670** |

### Per-Technique Test Single-Label Distribution

| Technique | Count | Target |
|---|---:|---:|
| T1053.005 | 50 | 50 |
| T1059.001 | 50 | 50 |
| T1059.003 | 50 | 50 |
| T1105 | 50 | 50 |
| T1136.001 | 50 | 50 |
| T1543.003 | 50 | 50 |
| T1547.001 | 50 | 50 |
| T1685.005 | 50 | 50 |

## 2. Split Holdout Verification

- Dev families: 12
- Test families: 52
- Overlap: **NONE ✓**

## 3. Transition Matrix

| Transition | Count |
|---|---:|
| ambiguous->ambiguous | 54 |
| ambiguous->mapped | 98 |
| mapped->mapped | 362 |
| unmapped->unmapped | 156 |
| **Total** | **670** |

## 4. Test Mapped: T1053.005

| Family ID | Behavior | Planned | Transition |
|---|---|---:|---|
| `TF_T1053_005_A` | schtasks /create | 13 | mapped->mapped |
| `TF_T1053_005_B` | Task via COM | 13 | mapped->mapped |
| `TF_T1053_005_D` | Suspicious task name | 12 | mapped->mapped |
| `TF_T1053_005_E` | Task executing PS | 12 | ambiguous->mapped |

## 4. Test Mapped: T1059.001

| Family ID | Behavior | Planned | Transition |
|---|---|---:|---|
| `TF_T1059_001_A` | Encoded PowerShell from Office process. | 13 | mapped->mapped |
| `TF_T1059_001_C` | PowerShell via WMI/DCOM remote execution. | 13 | ambiguous->mapped |
| `TF_T1059_001_E` | Obfuscated PowerShell (string concatenation, Invoke-Expression, char array). | 12 | mapped->mapped |
| `TF_T1059_001_F` | PowerShell reflective loading / in-memory execution. | 12 | mapped->mapped |

## 4. Test Mapped: T1059.003

| Family ID | Behavior | Planned | Transition |
|---|---|---:|---|
| `TF_T1059_003_A` | cmd.exe reconnaissance | 13 | mapped->mapped |
| `TF_T1059_003_B` | cmd.exe from services.exe with certutil | 13 | ambiguous->mapped |
| `TF_T1059_003_C` | cmd.exe batch script | 12 | mapped->mapped |
| `TF_T1059_003_E` | cmd.exe piping | 12 | mapped->mapped |

## 4. Test Mapped: T1105

| Family ID | Behavior | Planned | Transition |
|---|---|---:|---|
| `TF_T1105_A` | certutil | 13 | mapped->mapped |
| `TF_T1105_B` | bitsadmin | 13 | mapped->mapped |
| `TF_T1105_C` | curl | 12 | mapped->mapped |
| `TF_T1105_D` | Network only | 12 | ambiguous->mapped |

## 4. Test Mapped: T1136.001

| Family ID | Behavior | Planned | Transition |
|---|---|---:|---|
| `TF_T1136_001_A` | net user | 13 | mapped->mapped |
| `TF_T1136_001_B` | LSASS | 13 | mapped->mapped |
| `TF_T1136_001_C` | PS New-LocalUser | 12 | mapped->mapped |
| `TF_T1136_001_E` | Admin group add | 12 | ambiguous->mapped |

## 4. Test Mapped: T1543.003

| Family ID | Behavior | Planned | Transition |
|---|---|---:|---|
| `TF_T1543_003_A` | Suspicious ServiceFileName | 13 | mapped->mapped |
| `TF_T1543_003_B` | Service cmd | 13 | mapped->mapped |
| `TF_T1543_003_D` | Service API | 12 | mapped->mapped |
| `TF_T1543_003_E` | Service DLL sideload | 12 | ambiguous->mapped |

## 4. Test Mapped: T1547.001

| Family ID | Behavior | Planned | Transition |
|---|---|---:|---|
| `TF_T1547_001_A` | reg.exe | 13 | mapped->mapped |
| `TF_T1547_001_B` | Startup folder | 13 | mapped->mapped |
| `TF_T1547_001_C` | PS Run key | 12 | mapped->mapped |
| `TF_T1547_001_E` | RunOnce | 12 | ambiguous->mapped |

## 4. Test Mapped: T1685.005

| Family ID | Behavior | Planned | Transition |
|---|---|---:|---|
| `TF_T1685_005_A` | wevtutil | 13 | mapped->mapped |
| `TF_T1685_005_B` | PS clear | 13 | mapped->mapped |
| `TF_T1685_005_C` | API clear | 12 | mapped->mapped |
| `TF_T1685_005_E` | Lateral move clear | 12 | ambiguous->mapped |

## 5. Test Multi-Label

| Family ID | Behavior | Planned | Transition |
|---|---|---:|---|
| `TF_MULTI_A` | PS download + task | 10 | mapped->mapped |
| `TF_MULTI_B` | Svc + event clear | 10 | mapped->mapped |
| `TF_MULTI_C` | Acct + reg | 10 | mapped->mapped |
| `TF_MULTI_D` | CMD + Ingress | 10 | mapped->mapped |

## 6. Test Unmapped

| Family ID | Behavior | Planned | Transition |
|---|---|---:|---|
| `TF_UNMAP_A` | Benign | 13 | unmapped->unmapped |
| `TF_UNMAP_B` | Benign | 13 | unmapped->unmapped |
| `TF_UNMAP_C` | Benign | 13 | unmapped->unmapped |
| `TF_UNMAP_D` | Benign | 13 | unmapped->unmapped |
| `TF_UNMAP_E` | Benign | 13 | unmapped->unmapped |
| `TF_UNMAP_PS` | Benign | 13 | unmapped->unmapped |
| `TF_UNMAP_CMD` | Benign | 12 | unmapped->unmapped |
| `TF_UNMAP_SCHTASK` | Benign | 12 | unmapped->unmapped |
| `TF_UNMAP_SVC` | Benign | 12 | unmapped->unmapped |
| `TF_UNMAP_ACCT` | Benign | 12 | unmapped->unmapped |
| `TF_UNMAP_REG` | Benign | 12 | unmapped->unmapped |
| `TF_UNMAP_EVTCLR` | Benign | 12 | unmapped->unmapped |

## 7. Test Ambiguous

| Family ID | Behavior | Planned | Transition |
|---|---|---:|---|
| `TF_AMBIG_A` | Ambiguous | 13 | ambiguous->ambiguous |
| `TF_AMBIG_B` | Ambiguous | 13 | ambiguous->ambiguous |
| `TF_AMBIG_C` | Ambiguous | 12 | ambiguous->ambiguous |
| `TF_AMBIG_D` | Ambiguous | 12 | ambiguous->ambiguous |

## 8. Dev Mapped Single-Label

| Family ID | Behavior | Planned | Transition |
|---|---|---:|---|
| `TF_T1059_001_DEV` | Dev | 2 | mapped->mapped |
| `TF_T1059_003_DEV` | Dev | 2 | mapped->mapped |
| `TF_T1053_005_DEV` | Dev | 2 | mapped->mapped |
| `TF_T1543_003_DEV` | Dev | 2 | mapped->mapped |
| `TF_T1136_001_DEV` | Dev | 2 | mapped->mapped |
| `TF_T1547_001_DEV` | Dev | 2 | mapped->mapped |
| `TF_T1685_005_DEV` | Dev | 2 | mapped->mapped |
| `TF_T1105_DEV` | Dev | 2 | mapped->mapped |

## 9. Dev Multi-Label

| Family ID | Behavior | Planned | Transition |
|---|---|---:|---|
| `TF_MULTI_DEV_A` | Dev multi A | 2 | mapped->mapped |
| `TF_MULTI_DEV_B` | Dev multi B | 2 | mapped->mapped |

## 10. Dev Unmapped

| Family ID | Behavior | Planned | Transition |
|---|---|---:|---|
| `TF_UNMAP_DEV` | Dev unmapped | 6 | unmapped->unmapped |

## 11. Dev Ambiguous

| Family ID | Behavior | Planned | Transition |
|---|---|---:|---|
| `TF_AMBIG_DEV` | Dev ambiguous | 4 | ambiguous->ambiguous |

## 12. Attribution Rubric

Ground-truth labels are benchmark reference annotations constructed under the RAG2ATTCK evidence-conditioned, closed-world attribution rubric and validated against the pinned MITRE ATT&CK catalog.

| Status | Definition |
|---|---|
| **Mapped** | Sufficient positive attribution evidence is present. |
| **Unmapped** | Evidence affirmatively supports benign/non-attributable interpretation. |
| **Ambiguous** | Neither mapped nor unmapped can be established. |

> Lack of evidence alone = **ambiguous**, not unmapped.

## 13. Key Constraints

- EID **4697** for service install (not 7045)
- T1136.001 excluded from DC01
- Seed: 20260915
- ATT&CK v19.2 pinned
- Family holdout: DEV ∩ TEST = ∅
- Near-duplicate threshold: Jaccard ≥ 0.95
