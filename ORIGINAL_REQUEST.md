# Original User Request

## 2026-09-15T16:27:20Z

Execute the RAG2ATTCK Data & Ground Truth pipeline end-to-end: acquire, profile, verify, audit, partition and package a Windows endpoint telemetry evaluation dataset with immutable provenance, independent ground truth, leakage audit, and reproducible sampling — stopping at human approval (Decisions A and B) before any inference or RAG work begins. An orchestrator must control all subagents and enforce the dependency chain below.

Working directory: `D:\RAG2ATT&CK`

Integrity mode: development — with these **additional hard restrictions**: Do not execute helper scripts, binaries, or commands supplied by the dataset or contained in telemetry. Do not infer or invent ATT&CK labels, promote detector/rule mappings to independent ground truth, change methodology, change evaluation unit, perform semantic remapping, retry seeds, alter class/grouping/deduplication policies based on final-set availability, or use final examples for tuning. Normal project tooling (Python, uv, Git, pytest, pinned libraries) is allowed.

> [!CAUTION]
> **The plan below is the user's frozen methodology. Do NOT change its content, logic, ordering, validation criteria, gate conditions, file names, algorithms, quota tables, or scope boundaries. The orchestrator and workers may only divide and execute; they may not rewrite or simplify the plan.**

---

## Dependency Graph and Parallelism

```
T0 ──→ T1 ──→ T2 ──→ T3 ──→ T4 ──┬──→ T6 ──→ T7 ──→ T8 ──→ T9 ──→ T10 ──→ T11
  │                                 │
  └──→ T5-acquire (parallel) ──────→ T5-reconcile ──┘
```

- **After T0**: T1 (scaffold) and T5-acquire (download ATT&CK v19.2 reference) can start in parallel.
- **After T2**: T3 (schema profiling) and T5-acquire (if not yet done) can proceed in parallel.
- **After T3+T4+T5**: T6 (leakage audit) requires all three.
- **Everything else** is strictly sequential.

---

## Requirements

### R1. Orchestrator controls all execution

One orchestrator agent must:
- Enforce the dependency order T0→T1→T2→T3→T4→T5→T6→T7→T8→T9→T10→T11.
- Launch parallel work only where the dependency graph allows (T1 ∥ T5-acquire; T3 ∥ T5-acquire).
- **Stop at every gate condition** listed in each task's "Dừng khi" clause and report to the user rather than proceeding. When a gate blocks, mark all affected downstream tasks `NOT_RUN` and produce a blocker report; early termination is compliant.
- Never allow a downstream task to start before its dependencies produce validated outputs.
- Track and report task status after each task completes.
- **Single-writer rule:** Parallel workers may only write to explicitly disjoint paths. No worker may modify another worker's artifacts, Git state, shared configuration, manifests, or dependency lockfiles. The orchestrator alone integrates validated worker outputs. T5-acquire may run in parallel only if its writes are strictly isolated to its designated ATT&CK acquisition/reference paths (`attack/raw/enterprise-v19.2/` and related ATT&CK metadata). Any shared-state mutation (Git commits, lockfile updates, config changes) is serialized through the orchestrator.
- **Final-holdout blindness:** After Task 9 creates the final partition, no worker, QA agent, or orchestrator may semantically inspect final sample contents. Post-holdout work is limited to predeclared mechanical/invariant checks: hashes, schema checks, aggregate statistics, leakage assertions, and reproducibility comparisons. Final examples must not be manually opened, summarized, reviewed, or used to revise any policy, class selection, grouping, or sanitization rule.

### R2. Task 0 — Preflight: workspace, paths and capacity

**Objective:** Confirm pre-acquisition conditions.

**Inputs:** Current workspace, metadata package, canonical context and live disk capacity.

**Actions:**
- Check instructions and existing files; preserve already-saved source documents.
- Revalidate Doc/Sheet and write source metadata.
- Resolve all paths (raw, environment, cache, temporary, processed, reproduction outputs); all must be within the workspace, including through junction/symlink.
- Estimate downloads, staging, extraction, ATT&CK reference, environment, derived outputs and one reproduction run.
- Require free space ≥ estimate + 1 GiB, and never below 5 GiB.
- Re-run this check at execution time; do not reuse stale capacity data.

**Windows path safety:**
- Prefer `pathlib`, native filesystem APIs and `subprocess.run([...], shell=False, cwd=...)`.
- In PowerShell, use quoted literal paths, e.g.: `Set-Location -LiteralPath 'D:\RAG2ATT&CK'`
- Never concatenate paths containing `&` into unquoted shell commands.
- Never use `Invoke-Expression` or execute command strings built from data.

**Outputs:** `preflight.json`, source-context record; blocker report if needed.

**Validation:** Paths valid, capacity calculation clear, sufficient free space.

**Dependencies:** None.

**Stop when:** Insufficient capacity or invalid path. Do not delete data, change drives or reduce snapshots to pass the gate.

### R3. Task 1 — Scaffold and reproducible environment

**Objective:** Create minimal infrastructure for Data & Ground Truth.

**Inputs:** Task 0 passed.

**Actions:**
- Initialize local Git if not present; do not create remotes or publish.
- Use existing Python 3.13, record exact patch version, create `.venv` in workspace.
- Pin dependencies via `pyproject.toml`, `uv.lock`, `.python-version`.
- Prefer stdlib; add dependencies only for acquisition, processing and testing.
- Place cache/temp under `.cache`/`.tmp`; create `.gitignore` before acquisition.
- Create staged CLI, check prerequisite artifacts and hashes.
- Separate network-dependent acquisition from offline processing/validation.

**Outputs:** Scaffold, environment lock, config, README and CLI.

**Validation:** No API credentials needed; paths safe; no inference/retrieval dependencies.

**Dependencies:** Task 0.

**Exception:** Resolve environment errors with technical changes that do not affect methodology.

### R4. Task 2 — Acquisition and immutable provenance

**Objective:** Obtain a version-identified, verifiable snapshot.

**Inputs:** Official Windows-APT 2025 v3 metadata and documentation.

**Actions:**
- Pin dataset ID `b8fmtzvpy8`, version `3`, publication DOI and dataset DOI.
- Verify small pre-saved source files before reuse.
- Read README/scenario/validation metadata first; write complete inventory.
- Download via official source; check size/hash in staging before moving to raw.
- Record filename, provider ID, version-specific source, size, SHA-256, publication/update date if available, and acquisition UTC.
- Raw bytes are immutable; format fixes only on derived data.
- Period CSVs are ingest collections; `combined.csv` is for reconciliation, not added to observations.
- Compare record multisets and explain all discrepancies.
- Do not execute downloaded helper scripts or telemetry commands.

**Outputs:** Raw snapshot, `dataset_manifest.json`, acquisition/reconciliation logs.

**Validation:** Version, completeness, hashes and file roles correct; no double-counting.

**Dependencies:** Tasks 0–1.

**Stop when:** Wrong checksum, unverifiable license/version, or unresolved representation discrepancy. Do not substitute dataset/version.

### R5. Task 3 — Profile schemas, values and observation units

**Objective:** Determine structure and meaning of actual records.

**Inputs:** Verified raw snapshot.

**Actions:**
- Streaming CSV with support for quoted delimiters/multiline fields.
- Keep field names verbatim; aliases for typos must be documented.
- Distinguish logical records, physical lines and headers.
- Profile each file/nested path: types, missing/null/empty, malformed records, duplicate rates and candidate labels.
- Check EventID/provider, host/agent, timestamp, scenario/run/attack-step keys.
- Inspect representative values by file, event type, candidate label and error form.
- Determine whether a row is an event, alert, repeated alert or aggregate.
- Parse nested telemetry; do not assume `Full-log` is safe evidence.
- Create stable opaque record IDs from source-file hash and logical record ordinal.
- Cross-check actual counts against publication; document discrepancies, do not fix raw to match.

**Outputs:** `schema_profile.json`, field inventory, record index, parse-error ledger.

**Validation:** Parsed/rejected accounting complete; IDs deterministic; counts reconcile.

**Dependencies:** Task 2.

**Exception:** Do not auto-split aggregates into multiple evaluation samples or guess run boundaries.

### R6. Task 4 — Verify independent event-level ground truth

**Objective:** Prove authoritative exact target for each observation.

**Inputs:** Fields, original labels, dataset documentation and execution/annotation artifacts.

**Actions:**
- Record labeler/tool, assignment procedure, scope and independent evidential origin.
- Determine event-to-label joins using actual keys and documented boundaries.
- Check overlapping runs, timestamp precision/time zones, one-to-many joins and competing labels.
- Each eligible event must have: authoritative target, independent linkage, sufficient behavioral evidence, and no unresolved competing target.
- Preserve original label sets and conflict sources.
- Characterize singleton, missing, multi-label, malformed, conflicting and scope-ambiguous records.
- Do not treat rule mapping, scenario-wide list, successful operation or temporal proximity alone as event-level GT.
- Do not infer missing labels from event text; do not equate tagged with malicious or unlabelled with benign.

**Outputs:** Ground-truth provenance report/register, dispositions and join diagnostics.

**Validation:** Every GT-eligible event has a traceable evidence chain with no circular corroboration.

**Dependencies:** Task 3.

**Stop when:** Missing independent lineage, reannotation needed, or evaluation unit change needed.

If event windows might help, propose only host/run keys, timing, overlap, label semantics and count impacts; wait for approval before applying. Descriptive diagnostics may be completed to explain the blocker.

### R7. Task 5 — Source-era labels and ATT&CK v19.2 reconciliation

**Objective:** Preserve historical ground truth and check compatibility separately.

**Inputs:** Original labels, source provenance and official ATT&CK reference.

**Actions:**
- Find source-era version/semantics via documentation, scenario/annotation/configuration references and actual release/commit.
- Do not infer ATT&CK version from collection timing alone.
- If version cannot be verified, record `unknown`, evidence and search scope.
- Preserve original ID, name, label set and granularity.
- Pin Enterprise ATT&CK v19.2 via immutable revision/hash; create validation lookup only.
- Check syntax, existence, canonical name, hierarchy, platforms, revoked/deprecated and transition relationships.
- Separate:
  - Historical GT authority.
  - Source-era semantic certainty.
  - v19.2 identity/status.
  - Experiment compatibility.
- Mechanical normalization must not change target.
- Deprecated/revoked/renamed/absent in v19.2 does not automatically invalidate historical GT.
- Do not auto-apply successor relationships to remap.

**Outputs:** `attack_manifest.json`, `label_inventory.csv`, source-era provenance and transition audit.

**Validation:** Original labels preserved; parent/sub-technique not collapsed/expanded; status does not directly determine GT authority.

**Dependencies:** Tasks 2–4; reference acquisition can be independent.

**Stop when:** Semantic remapping or unapproved compatibility decision needed. Keep observations in audit; do not drop solely because "deprecated".

### R8. Task 6 — Leakage audit and input policy

**Objective:** Separate raw behavior from answer-bearing metadata.

**Inputs:** Actual fields/values and GT/reference provenance.

**Actions:**
- Classify each candidate path: `SAFE`, `UNSAFE / LABEL LEAKAGE`, `REQUIRES REVIEW`.
- Record value examples/locators, usefulness, rationale, transform and review provenance.
- Check direct labels, tactics, `rule.mitre`, rule descriptions, generated alerts, compliance metadata, scenario/annotation fields.
- Check values in nested messages, filenames, scripts and command paths.
- Derive allowlist from actual audit; do not apply an illustrative pre-built whitelist.
- Preserve legitimate command/path/registry/network evidence.
- Remove annotation substrings only with deterministic rules that do not alter behavioral meaning; if impossible, quarantine.
- Specify missing values, types, serialization and unknown-field handling.
- Complete semantic inspection and policy decisions before holdout.

**Outputs:** `leakage_audit.csv`, `field_policy.json`, sanitizer and inspection ledger.

**Validation:** Fixtures check nested/value leakage, legitimate evidence, missing fields and schema drift.

**Dependencies:** Tasks 3–5.

**Stop when:** Unresolved leakage or sanitization destroys needed evidence. Regex scan does not substitute semantic audit.

### R9. Task 7 — Sanitization, deduplication and grouping

**Objective:** Create eligible candidates and group-level statistics before class selection.

**Inputs:** GT-eligible records, label decisions, frozen input policy.

**Actions:**
- Store inputs, labels and audit provenance separately.
- Distinguish source IDs, exact evidence fingerprints and dependence groups.
- Collapse exact repeated evidence with same target deterministically, keep aliases.
- Quarantine identical evidence with conflicting targets; no majority-vote.
- Use audited comparison representation for near-duplicates, do not drop behavioral fields arbitrarily.
- Keep lexical method versioned; default candidate threshold is character 5-gram Jaccard ≥ 0.95 within compatible event-type blocks.
- Inspect candidate matches before treating as confirmed duplicate families.
- Freeze comparison normalization/blocking before holdout.
- Build connected components from verified scenario identity through repeated executions, run boundaries and duplicate relationships.
- Report giant/mixed-class components, independent-group counts and concentration.
- Do not use broad APT group names or filename/date as substitute for verified run/scenario identity.

**Outputs:** Sanitized candidates, GT sidecars, duplicate/group metadata and quality statistics.

**Validation:** Deterministic groups; full traceability; conflicting labels not hidden.

**Dependencies:** Tasks 4–6.

**Stop when:** Grouping unreliable or loosening grouping/deduplication needed to reach counts.

### R10. Task 8 — Class selection and quota before holdout

**Objective:** Fix benchmark composition and numerical targets before partition.

**Inputs:** Full eligible dataset and overall/group-level statistics from Task 7.

**Actions:**

1. Compute count waterfall before holdout.
2. Apply GT, evidence quality, ambiguity, leakage and compatibility gates.
3. Assess overall usable counts, usable proportion, independent groups, duplicate burden and concentration.
4. Rank eligible classes by:
   - Usable proportion descending.
   - Independent-group count descending.
   - Duplicate burden ascending.
   - Overall usable count descending.
   - Canonical ID as tie-breaker.
5. Select 8–10 classes per ranking and overall feasibility; do not use partition/final counts.
6. After selecting class count `n`, compute the single quota:

```
quota_per_class = {8: 50, 9: 45, 10: 40}[n]
planned_total = n × quota_per_class
```

7. Write `provisional_class_set.json` before partition, including:
   - Ordered class list and target semantics.
   - `class_count`.
   - `planned_final_samples_per_class`.
   - `planned_final_total`.
   - Rationale/caveats.
   - Source, eligible-statistics, grouping and selection-policy hashes.
   - Status `PROVISIONAL_FROZEN_BEFORE_HOLDOUT`.

**Outputs:** Overall class distribution, proposed/rejected candidates and class/quota freeze artifact.

**Validation:**
- No dev/final assignments created yet.
- Selection function does not receive final-pool information.
- Quota matches table exactly: 8→50, 9→45, 10→40.
- Class list, quota and provenance hashed before partition.
- Final examples or final counts not used to select classes.

**Dependencies:** Task 7 and necessary methodological decisions.

**Stop when:** Not enough defensible classes or overall feasibility does not support design. Report shortfall, do not lower standards.

Provisional freeze is a pre-holdout commitment; not yet final human approval.

### R11. Task 9 — Partition and sample manifests with immutable quota

**Objective:** Create samples for exactly the declared classes/quota.

**Inputs:** Frozen class/quota artifact, groups and seed `20260915`.

**Actions:**
- Partition may run only when freeze artifact is valid.
- Hash seed and stable group ID with SHA-256 using deterministic serialization:
  - Hash integer modulo 5 = 0 → dev.
  - Remainder → final.
- Entire component in same partition; this is approximately 20% groups, not guaranteed 20% records.
- All unused dev-group observations still excluded from final.
- Samples non-returnable; at most one representative per confirmed near-duplicate family.
- Seeded ordering and round-robin across groups to reduce run dominance.
- Target real dev: 30 samples; 20–29 triggers warning; below 20 blocks proposed dev design.
- Missing dev class coverage reported, not backfilled from final.
- For each final class:

```
available < predeclared_quota
    → report deficit = predeclared_quota − available
```

- Do not rewrite quota to actual count.
- Do not change classes, seed, grouping or deduplication policy based on availability.
- Do not open final examples to resolve shortfalls.
- Clearly distinguish planned, available, sampled and shortfall.

**Outputs:** Dev/provisional-final inputs and separate labels; partition/sampling manifests; shortfall report.

**Validation:** Class/quota hash unchanged; pools/groups/duplicate families disjoint; IDs unique; reruns identical; shortfall does not trigger reselection.

**Dependencies:** Task 8.

**Stop when:** Protocol change or design shortfall acceptance needed. Report aggregate evidence and wait for methodological decision.

Synthetic smoke-test samples from later phases must not be used to fill evaluation gaps.

### R12. Task 10 — Validation and clean reproduction

**Objective:** Verify artifacts without tuning into holdout.

**Inputs:** Raw snapshot, locked environment/code, policies and manifests.

**Actions:**
- Run automated checks from the Validation section below.
- Reproduce offline in a new output directory under `.tmp`.
- Compare classes, quotas, partitions, IDs, evidence bytes, labels and dispositions.
- Do not include run timestamps/runtime diagnostics in substantive comparisons.
- Rehash raw/reference files.
- After holdout, read only mechanical-check results and aggregate outputs.
- Errors requiring protocol change must invalidate and report impact; do not manually fix the final sample list.

**Outputs:** Validation results, reproduction comparison and integrity report.

**Validation:** Reproduction matches; raw unchanged; manifests/reports consistent.

**Dependencies:** Tasks 1–9.

**Exception:** Upstream blocker makes downstream `NOT_RUN`; do not treat empty outputs as PASS.

### R13. Task 11 — Audit package and human approval

**Objective:** Produce a reviewable recommendation and stop at scope boundary.

**Inputs:** All evidence, artifacts, checks and unresolved issues.

**Actions:** Report in full:
- Dataset/version and suitability.
- Raw/parsed/GT-eligible/usable/deduplicated/selected counts.
- Independent GT source and event linkage.
- Source-era semantics separate from v19.2 status/transition.
- Leakage policy, grouping and limitations.
- Overall class ranking.
- Class/quota freeze before holdout.
- Seed, partitions, actual counts and shortfalls.
- Validation/reproduction results.
- Reproduction commands and artifact references.

Request two separate decisions:
- **Decision A:** Dataset/version and GT basis accepted as primary dataset or not.
- **Decision B:** Classes and sample design accepted/officially frozen or not.

Event windows or semantic remapping require separate approval before applying.

**Outputs:** Full audit, concise approval checklist, pending approval record.

**Validation:** Pending decisions not recorded as approved; report matches artifacts.

**Dependencies:** Task 10 or completed diagnostic tasks when blocked.

**Stop:** Do not begin RAG, retrieval, embeddings, inference or experiments.

---

## Interfaces and boundaries

```
select_classes(overall_statistics, selection_policy)
    → selected_classes

freeze_classes_and_quota(selected_classes)
    → provisional_class_set.json

partition_groups(groups, frozen_class_set, seed)
    → partition_manifest.json

sample_partitions(partitions, frozen_class_set, sampling_policy)
    → sampling_manifest.json + shortfalls
```

- Class selection does not receive final-pool information.
- Quota depends only on the number of selected classes.
- Partition/sampling must not modify the freeze artifact.
- Future model payload accessor returns sanitized evidence only.
- GT authority and v19.2 status are two separate attributes.

## Expected files in workspace

| Group | Files and purpose |
|---|---|
| Project | `README.md`, `.gitignore`, `pyproject.toml`, `uv.lock`, `.python-version` |
| Plan/context | `docs/data_ground_truth_execution_plan.md`, `docs/context/` |
| Policies | `config/data_ground_truth.json`, `field_policy.json`, `grouping_policy.json`, `class_selection_policy.json` |
| Source | `src/dataset.py`, `labels.py`, `attack_loader.py`, `sanitizer.py`, `sampling.py`, `data_ground_truth.py`, `__init__.py` |
| Tests | `tests/test_dataset.py`, `test_labels.py`, `test_sanitizer.py`, `test_sampling.py`, `test_pipeline.py`, `fixtures/` |
| Immutable inputs | `data/raw/windows_apt_2025/v3/`, `attack/raw/enterprise-v19.2/` |
| Source/profile metadata | `data/metadata/preflight.json`, `dataset_manifest.json`, `attack_manifest.json`, `schema_profile.json` |
| Label/leakage metadata | `label_inventory.csv`, `attack_transition_audit.csv`, `leakage_audit.csv` in `data/metadata/` |
| Selection metadata | `class_distribution.csv`, `proposed_subset.csv`, `rejected_candidates.csv`, `provisional_class_set.json` in `data/metadata/` |
| Sampling metadata | `partition_manifest.json`, `sampling_manifest.json`, `sampling_shortfalls.csv` in `data/metadata/` |
| Validation/approval | `validation_results.json`, `approval_record.json` in `data/metadata/` |
| Per-record stores | `data/audit/`, `data/ground_truth/`, `data/processed/` |
| Reports | `reports/ground_truth_provenance.md`, `data_ground_truth_audit.md`, `approval_checklist.md` |
| Runtime | `.venv/`, `.cache/`, `.tmp/` |

Preserve and verify existing source-research files. Do not modify canonical Drive Doc/Sheet. Raw/reference bytes are immutable; large/per-record artifacts are reproducible via manifests/checksums rather than committed to Git.

---

## Acceptance Criteria

### Pipeline integrity
- [ ] Every task that runs respects dependency order; no task starts before its predecessors' validated outputs exist. When a declared gate blocks execution, all affected downstream tasks are marked `NOT_RUN` and the orchestrator produces a user-facing report explaining the blocker, its origin task, and which downstream tasks were skipped. Early termination at a gate is **compliant behavior**, not a pipeline failure.
- [ ] Every gate condition ("Dừng khi" / "Stop when") causes an immediate halt and user-facing report rather than silent continuation or attempted workaround.
- [ ] Workspace path containing `&` works via native/pathlib APIs and quoted PowerShell throughout.
- [ ] Free disk space ≥ estimate + 1 GiB and ≥ 5 GiB at execution-time check.

### Single-writer isolation
- [ ] Parallel workers write only to their designated, disjoint path sets; no worker modifies another worker's artifacts, manifests, or outputs.
- [ ] All Git commits, dependency lockfile updates, and shared config mutations are serialized through the orchestrator — never performed directly by parallel workers.
- [ ] T5-acquire writes are strictly confined to `attack/raw/enterprise-v19.2/` and ATT&CK-specific metadata paths; it does not touch scaffold, dataset, or environment files.
- [ ] The orchestrator integrates worker outputs only after per-task validation passes.

### Final-holdout blindness
- [ ] After Task 9 creates the final partition, no agent (worker, QA, or orchestrator) semantically inspects, opens, summarizes, or reviews individual final sample contents.
- [ ] Post-holdout checks (Task 10) are limited to predeclared mechanical/invariant operations: hash comparison, schema validation, aggregate statistics, leakage assertions, and reproducibility comparison.
- [ ] No policy, class selection, grouping rule, sanitization rule, or quota is revised based on final sample content.
- [ ] Dev-set samples may be inspected freely; the blindness constraint applies exclusively to the final evaluation partition.

### Data provenance
- [ ] Raw snapshot is pinned to Windows-APT 2025 v3 (dataset ID `b8fmtzvpy8`); SHA-256 hashes match; raw bytes never modified after acquisition.
- [ ] ATT&CK Enterprise v19.2 pinned via immutable revision/hash.
- [ ] `dataset_manifest.json` records filename, provider ID, version-specific source, size, SHA-256, and acquisition UTC for every file.
- [ ] Period CSVs and `combined.csv` reconciled without double-counting.

### Ground truth
- [ ] Every GT-eligible event has an independent, traceable evidence chain (not circular corroboration, rule mapping, or scenario-wide list alone).
- [ ] Original label IDs/sets/granularity preserved verbatim; no silent remapping, collapsing, or expanding.
- [ ] Historical deprecated/revoked ATT&CK status does not auto-invalidate GT authority.
- [ ] Source-era semantics and v19.2 identity/status are tracked as separate attributes.

### Leakage and sanitization
- [ ] No forbidden metadata (ATT&CK labels, tactics, `rule.mitre`, rule descriptions, answer-bearing annotations) reaches model/retriever input.
- [ ] Legitimate behavioral evidence (commands, paths, registry, network) is preserved.
- [ ] Allowlist derived from actual audit, not from an illustrative pre-built whitelist.
- [ ] Sanitizer has fixtures checking nested/value leakage, legitimate evidence, missing fields and schema drift.

### Grouping and deduplication
- [ ] Exact duplicate collapse is deterministic; conflicting-target duplicates are quarantined (no majority-vote).
- [ ] Near-duplicate threshold is character 5-gram Jaccard ≥ 0.95 within compatible event-type blocks.
- [ ] Connected components use verified scenario identity, not broad APT group names or filename/date.
- [ ] Groups do not cross partitions.

### Class selection and quota
- [ ] Class selection uses only pre-holdout statistics; no final-pool information.
- [ ] Quota matches the table exactly: 8 classes→50/class/400 total; 9→45/405; 10→40/400.
- [ ] `provisional_class_set.json` written and hashed before any partition runs.
- [ ] Partition code refuses to run without a valid freeze artifact.

### Partition and sampling
- [ ] Seed `20260915`; SHA-256 hash of (seed + stable group ID); mod 5 = 0 → dev, else → final.
- [ ] Entire connected component stays in one partition.
- [ ] At most one representative per confirmed near-duplicate family.
- [ ] Shortfalls reported as `deficit = predeclared_quota − available`; quota never rewritten.
- [ ] Classes, seed, grouping, and deduplication policy never changed based on final availability.

### Reproduction
- [ ] Clean offline reproduction in a new `.tmp` directory produces identical classes, quotas, partitions, IDs, evidence bytes, labels and dispositions (excluding run timestamps).
- [ ] Raw/reference file hashes unchanged after full pipeline run.
- [ ] Reruns are deterministic: same inputs → same outputs.
- [ ] Reproduction comparisons on final-partition outputs are mechanical only (hash, schema, aggregate identity), consistent with the final-holdout blindness rule.

### Audit and stop
- [ ] Full audit report and concise approval checklist produced.
- [ ] Pipeline stops at Decisions A and B; no inference, retrieval, embeddings, FAISS, RAG/No-RAG, or experiment code.
- [ ] Pending decisions not recorded as approved.

### Verification mechanism
- [ ] `pytest` test suite covers: path safety, hash verification, parse accounting, GT independence, label preservation, leakage fixtures, deterministic grouping, quota table correctness, partition disjointness, and reproduction identity.
- [ ] Orchestrator runs `pytest` after each task group and reports pass/fail before proceeding.

---

## Hard scope boundary (do NOT cross)

No OpenAI/GPT inference, prompt benchmarking, model comparison, embeddings, FAISS/vector index, RAG/No-RAG inference implementation, retrieval, experiments, RQ result calculation, fine-tuning, SIEM integration, dashboards, application-level AI agent implementation, or frontend/backend development. This restriction does not prohibit Antigravity orchestration workers/subagents used solely to execute this frozen plan.

---
*Expecting this to run as a full team project with orchestrator, parallel workers, and QA review — given the 12-task dependency chain with strict methodology gates.*

## 2026-09-17T06:50:24Z

Execute 8 final merge-readiness corrections on the `baseline-infra` branch of the RAG2ATTCK research project. This is a correction pass on existing infrastructure code — all changes are well-specified. Commit and push to `origin/baseline-infra` when done. **Do NOT merge into main.**

Working directory: d:\RAG2ATT&CK-baseline-infra
Integrity mode: development

## Reference Material

- Repository: https://github.com/habachcp6/RAG2ATTCK
- Branch: `baseline-infra` at HEAD `6505bdea71156159ab07c5f2e4c11709aa34ac34`
- Main HEAD: `e3c68566ca21ec10a6c089bf6c2020002082b70a`
- Git worktree of `d:\RAG2ATT&CK` on branch `baseline-infra`
- Package manager: `uv`
- Python: >=3.13.0
- Test framework: pytest
- The implementation plan is at: `C:\Users\hahoa\.gemini\antigravity\brain\2041db39-b675-401e-92b8-b5cbe4a10771\implementation_plan.md`

### Critical Constraints
- Do NOT merge baseline-infra into main
- Do NOT modify: README.md, Data/GT production files (`src/acquisition.py`, `src/artifacts.py`, `src/attack_loader.py`, `src/data_ground_truth.py`, `src/dataset.py`, `src/ground_truth.py`, `src/profiler.py`, `src/reconcile.py`), `config/data_ground_truth.json`, T02 literature docs
- Do NOT add `sk-` prefixed strings to any file (not even test fixtures)
- ZERO live OpenAI API calls allowed during implementation and testing

## Requirements

### R1. Fix Responses API Status and Refusal Handling

Rewrite `_extract_response_content_and_status()` in `src/llm/client.py` to handle real OpenAI Responses API object shapes:

**Status classification — full coverage:**

| `response.status` | → `ParseStatus` |
|---|---|
| `completed` | Continue to output extraction |
| `incomplete` | `INCOMPLETE` |
| `failed` | `API_FAILURE` |
| `cancelled` | `API_FAILURE` |
| `queued` / `in_progress` | `API_FAILURE` (unexpected for synchronous calls) |
| Any unknown value | `API_FAILURE` (defensive) |

**Refusal detection for `completed` responses:**
- Inspect `response.output[*].content[*]` for content parts with `type == "refusal"`
- Extract `part.refusal` as the refusal message → `ParseStatus.REFUSAL`
- For normal output: extract text from `type == "output_text"` parts or fall back to `response.output_text`

**Also update mock objects in `src/baseline/smoke.py` failure pathways:**
- Pathway 7 (REFUSAL): use realistic nested `output[].content[]` structure instead of flat `status="refused"` / `refusal="..."`
- Remove stale `m9.chat.completions.create.side_effect` and `m10.chat.completions.create.side_effect` lines (lines 238, 248)

**Also update mock helper `create_mock_responses_api_obj()` and the test helper `create_mock_responses_api_response()` in test files** to produce realistic nested output structure matching the real API.

### R2. Fix Smoke Report Generator

The `write_smoke_test_report()` function in `src/baseline/smoke.py` (lines 410–570) still emits stale fallback references. Fix:

1. Remove `"Primary Responses API execution with operational fallback to Chat Completions API"` → `"Responses API execution (sole frozen experimental interface, no runtime fallback)"`
2. Remove the `fallback_api_interface` row from the config table (line 448)
3. Replace `"across the entire application lifecycle"` → `"per-process smoke-test live request cap"`
4. Fix the status label: when `live_requests_consumed == 0` use `"Mock-only / unauthenticated test runtime"`, when > 0 use `"Authenticated live runtime"`
5. Do NOT hardcode `$0.00` for cost — make it conditional: `$0.00` only when 0 live requests, otherwise `"See OpenAI dashboard for actual cost"`
6. Label token/latency values as `*(mock telemetry)*` when `live_requests_consumed == 0`
7. **Distinguish live sample count from actual API request count:** Report both `live_samples_dispatched` (samples sent to live API) and `live_api_requests_consumed` (from `LiveBudget.count`, includes retries). These are different numbers because one sample may consume multiple budget units due to retries.

### R3. Validate Condition Enum at Runtime

`condition` parameter currently accepts any string. Invalid values like `"norag"`, `"no-rag"`, `"No-RAG"`, `"baseline"` silently bypass the No-RAG retrieved_context isolation check.

Add runtime validation:
1. In `src/llm/schemas.py`: add `VALID_CONDITIONS = frozenset({"no_rag", "rag"})` and a `validate_condition(condition: str)` function that raises `ValueError` for invalid values
2. In `src/llm/client.py` `predict()`: call `validate_condition()` as the **first** check — before the No-RAG isolation check
3. In `src/baseline/pipeline.py` `run_sample()`: call `validate_condition()` before forwarding to client
4. Tests must prove `ValueError` is raised **before** any API call (`mock.assert_not_called()`)

### R4. Correct T11 Report

In `reports/T11_model_freeze.md`:
1. Line 82: Change `"Deepest reasoning compute tier"` → `"Frozen reasoning effort selected for this study"` (GPT-5.6 Luna supports `max` tier too)
2. Line 49: The claim about `usage.output_tokens_details.reasoning_tokens` implies it's persisted — check `ExecutionRecord` in `src/llm/schemas.py` (it only stores `input_tokens` and `output_tokens`, not reasoning token breakdown). Reword to: `"The Responses API exposes reasoning token counts via usage.output_tokens_details.reasoning_tokens at query time; however, ExecutionRecord does not persist this field — only aggregate input_tokens and output_tokens are recorded."`
3. Line 132: Remove stale mention of `max_completion_tokens`: change `"config/model.json strictly specifies max_output_tokens and max_completion_tokens"` → `"config/model.json specifies only max_output_tokens since the frozen interface is Responses API"`

### R5. Correct LiveBudget Semantics + Mock-by-Default

1. In `src/llm/client.py`: Update `LiveBudget` docstring — replace `"across the application lifecycle"` with `"Per-process smoke-test live request cap. Resets when the process restarts. The external OpenAI/project spend limit is the true cross-process safeguard."`
2. In `src/baseline/smoke.py` `run_smoke_test_pipeline()`: Add `allow_live: bool = False` parameter. When `allow_live=False` (default): **always use mock client**, regardless of whether `OPENAI_API_KEY` exists. When `allow_live=True`: check key, respect ≤5 budget cap. Update `if __name__ == "__main__"` to accept `--live` flag.
3. In `reports/T14_smoke_test_report.md`: Replace `"across the entire application lifecycle"` → `"per-process smoke-test run"` in the committed static report.

### R6. Secret-Scan Cleanliness

Replace all `sk-` prefixed fake test keys with non-secret placeholders:

| File | Current | Replacement |
|------|---------|-------------|
| `tests/test_llm_client.py:120` | `"sk-test-key-for-unit-tests"` | `"test-key-for-unit-tests"` |
| `tests/test_llm_client.py:129` | `"sk-injected-test-key"` | `"test-injected-key"` |
| `tests/test_baseline_pipeline.py:98` | `"sk-test-pipeline-key"` | `"test-pipeline-key"` |

Do NOT change the secret-scan patterns in `tests/test_model_config.py` (lines 90, 112) — those are scan/assertion logic, not fake keys.

### R7. Remove Out-of-Scope Scripts

Delete both files:
- `scripts/adversarial_challenge_suite.py`
- `scripts/generate_smoke_cases.py`

Justification: `generate_smoke_cases.py` was a one-shot generator (output `smoke_cases.jsonl` already committed). `adversarial_challenge_suite.py` coverage is subsumed by existing test files. Neither is imported by `src/` or `tests/`. Both are outside the T11–T14 approved file whitelist.

If removing these breaks any import or test, fix the breakage.

### R8. Final Verification and Push

1. Sync with current main: `git fetch origin && git merge origin/main` (resolve cleanly)
2. Run `uv sync && uv run pytest -v` — all tests must pass
3. Run secret scan: `Select-String -Pattern "sk-[A-Za-z0-9_\-]{20,}" -Recurse` across src/, tests/, config/, reports/
4. Commit with descriptive message
5. Push to `origin/baseline-infra`
6. **Do NOT merge into main**

## Acceptance Criteria

### Responses API Status Handling
- [ ] `_extract_response_content_and_status()` classifies all 6 documented Responses API statuses (`completed`, `incomplete`, `failed`, `cancelled`, `queued`, `in_progress`) correctly
- [ ] Unknown/unexpected status values produce `API_FAILURE`, not `MALFORMED_RESPONSE`
- [ ] Refusal detection works via realistic nested `response.output[*].content[*]` with `type == "refusal"` — NOT via flat `response.status == "refused"`
- [ ] Each status classification has a dedicated passing test

### Condition Validation
- [ ] `validate_condition()` exists and is called before prompt construction in both `predict()` and `run_sample()`
- [ ] `"norag"`, `"no-rag"`, `"No-RAG"`, `""`, `"baseline"` all raise `ValueError`
- [ ] `"no_rag"` and `"rag"` are the only accepted values
- [ ] Tests prove `ValueError` fires before any mock API call (`assert_not_called()`)

### Report Generator
- [ ] Regenerated T14 report contains ZERO occurrences of: `"Chat Completions"`, `"fallback"`, `"fallback_api_interface"`, `"Authenticated Runtime"` (when no live calls)
- [ ] Regenerated report distinguishes live sample count from actual API request count
- [ ] When 0 live requests: cost shows `$0.00`, metrics labelled as mock telemetry
- [ ] Regression test verifies these invariants programmatically

### Mock-by-Default
- [ ] `run_smoke_test_pipeline()` with default `allow_live=False` performs ZERO live API calls even when `OPENAI_API_KEY` environment variable is set
- [ ] `allow_live=True` + key present → live calls possible (capped at ≤5)
- [ ] Test proves mock-by-default behavior with monkeypatched key

### T11 Report
- [ ] `reasoning_effort` described as `"Frozen reasoning effort selected for this study"`, not `"Deepest reasoning compute tier"`
- [ ] No claim that `config/model.json` contains `max_completion_tokens`
- [ ] Reasoning token telemetry accurately described as "available at query time" but not persisted in `ExecutionRecord`

### LiveBudget Semantics
- [ ] `LiveBudget` docstring says "per-process" not "application lifecycle"
- [ ] T14 committed report says "per-process" not "application lifecycle"

### Secret Scan
- [ ] `Select-String -Pattern "sk-[A-Za-z0-9_\-]{20,}"` returns 0 matches across `src/`, `tests/`, `config/`, `reports/` (excluding scan pattern definitions in test_model_config.py)
- [ ] Test fixture keys use non-`sk-` prefixed placeholders

### Scope
- [ ] `scripts/adversarial_challenge_suite.py` deleted
- [ ] `scripts/generate_smoke_cases.py` deleted
- [ ] No imports or tests broken by deletion

### Final State
- [ ] `uv run pytest -v` — all tests pass, 0 failures
- [ ] baseline-infra is 0 commits behind current `origin/main`
- [ ] Changes pushed to `origin/baseline-infra`
- [ ] Branch is NOT merged into main
- [ ] T15 remains unexecuted
- [ ] 0 live OpenAI API calls during implementation

### Return Report
Produce a 10-item structured report:
1. New HEAD SHA
2. pytest collected/passed/failed/skipped
3. Files changed relative to main (`git diff origin/main --stat`)
4. Refusal-handling verification (which tests, pass/fail)
5. Condition-validation verification (which tests, pass/fail)
6. Regenerated-report verification (which tests, pass/fail)
7. Mock-by-default verification (which tests, pass/fail)
8. Secret-scan result (exact command, match count)
9. Scope decision for the two scripts (deleted/retained + justification)
10. Merge-ready YES/NO

