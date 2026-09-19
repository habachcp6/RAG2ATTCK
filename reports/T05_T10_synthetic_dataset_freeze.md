# T05-T10 Synthetic Dataset Freeze

## Provenance

- Base main: `827eb8b147efc756146261649399ee9e40a1e634`.
- Branch: `task/t05-t10-stage-b-data-freeze`.
- Corrected approved registry SHA-256: `0f4db1c62ab3bc59a6da6647bf91f65428d3fe2d86881530d36497544084b8b2`.
- Generator: `1.0.1`, commit `3dec6925b2a9b2c91e7e9381230207f27d0615b1`; source-file hashes are frozen in generation_metadata.json.
- Seed: `20260915`; ATT&CK Enterprise `19.2`.
- ATT&CK source SHA-256: `dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4`.
- The user approved Stage B and the bounded Stage A telemetry/relation corrections recorded in the preflight report. After independent audits of the original PR head, the orchestrator authorized evidence-bounded fixes for parent-command lineage, the unmapped vendor-name shortcut, and unsupported execution/signer wording. ATT&CK catalog, labels, quotas, split assignments, and seed remain unchanged.

## Generated dataset counts

670 scenario pairs; 1340 views; 1434 unique events. TEST=640 pairs, DEV=30 pairs. Contextual windows contain 2-3 events (allowed 2-6); single views contain the identical anchor only.

| Category | TEST | DEV | Total |
|---|---:|---:|---:|
| mapped_single | 400 | 16 | 416 |
| mapped_multi | 40 | 4 | 44 |
| unmapped | 150 | 6 | 156 |
| ambiguous | 50 | 4 | 54 |

| Technique | TEST mapped-single | DEV mapped-single | All contextual labels | All single labels |
|---|---:|---:|---:|---:|
| T1053.005 | 50 | 2 | 64 | 29 |
| T1059.001 | 50 | 2 | 64 | 49 |
| T1059.003 | 50 | 2 | 62 | 49 |
| T1105 | 50 | 2 | 74 | 40 |
| T1136.001 | 50 | 2 | 62 | 37 |
| T1543.003 | 50 | 2 | 64 | 50 |
| T1547.001 | 50 | 2 | 64 | 42 |
| T1685.005 | 50 | 2 | 62 | 0 |

Multi-label annotations contribute to more than one technique in the last two columns; those totals are not independent scenario counts.

## Holdout and transitions

52 TEST families and 12 DEV families; family overlap = 0. All 64 approved family allocations are realized exactly. No family was repartitioned, no sample dropped, and no quota was repaired after observing generated counts.

| Transition | Pairs |
|---|---:|
| ambiguous→ambiguous | 54 |
| ambiguous→mapped | 164 |
| ambiguous→unmapped | 49 |
| mapped→mapped(expanded) | 44 |
| mapped→mapped(same) | 252 |
| unmapped→unmapped | 107 |

## Quality gates

Validation errors=0; warnings=0; leakage findings=0; invalid catalog IDs=0; name mismatches=0; disallowed transitions=0; family overlap=0; local-account host violations=0; unsafe indicator violations=0; unacceptable near-duplicates=0; artifact hash mismatches=0; reproduction hash mismatches=0.

Near-duplicates use character 5-gram Jaccard >=0.95. All logon IDs, process IDs/GUIDs, hostnames and timestamps are excluded by normalization; no duplicate exceptions were granted. XML task namespace URIs are schema identifiers rather than network indicators; actual XML values and command URLs remain checked.

## Independent audit corrections

- Sysmon 1 `ParentCommandLine` now matches the visible parent process command line when that parent event is present. This corrected all 13 `TF_T1059_001_A` pairs and is enforced by a regression check.
- Removed the fixed `Contoso` and `Maintenance` strings from model-facing synthetic telemetry. The original `Contoso` token appeared in 105/156 contextual unmapped views and in no mapped or ambiguous views. The corrected inference payload contains neither token; `ProgramData` remains present across mapped, ambiguous, and unmapped views.
- Updated rationale and template wording so service installation, task configuration, process creation, and command invocation do not claim successful service/DLL/payload execution, scheduler causality, signer authenticity, or authorization without evidence.
- Preserved all 670 pair IDs, per-view labels, family allocations, split assignments, quotas, and technique counts. Re-reviewed the 34 selected spot-check cases whose semantic content changed; the complete 66-case package remains bound to the current registry and artifact hashes.
- `sample_id` can be reversed with the public seed and registry to recover family metadata, but the current production batch path uses it only as record metadata; prompts receive `endpoint_evidence`. The serialized inference file contains only `sample_id` and `endpoint_evidence`.
- Independent structure and leakage reviews found no missing/orphan references, family overlap, or model-visible ground-truth fields. The original documentation count mismatch is corrected below from actual test runs.

## Manual deterministic inspection

Inspected 66 cases spanning all 64 families, both DEV/TEST splits, all eight techniques, multi-label cases and both negative categories. The package contains raw telemetry, actual whitelist inference payloads, per-view ground truth, transition and concrete field references. After the independent audit fixes, all 34 affected selected cases were re-inspected and documented. Case-specific notes are in data/audit/synthetic_manual_review.json, bound to the registry, package and semantic hashes.

Inspection corrected generator defects before freezing: excessive local-account name length; wrong Explorer path; SYSTEM service-process identity; task XML WorkingDirectory; task DEV structure; process/parent identity correlation; and overly broad evidence references. The final package and annotations were rechecked after correction. No review findings remain unresolved under the approved rubric.

## Validation commands

```text
uv lock --check --offline                         PASS
uv sync --frozen                                  PASS
uv pip check                                      PASS
uv run python scripts/validate_synthetic_registry.py  passed=true; 64 families; 670 planned instances
uv run pytest tests/test_synthetic.py -q            116 passed
uv run pytest tests/test_synthetic_generation.py -q 24 passed
uv run pytest tests/test_synthetic_freeze.py -q      15 passed (39 combined Stage B tests passed)
uv run python -m src.data_ground_truth prepare-synthetic   PASS; 670 pairs / 1340 views
uv run python -m src.data_ground_truth validate-synthetic  PASS; 0 errors
uv run python -m src.data_ground_truth freeze-synthetic    PASS
uv run python -m src.data_ground_truth verify-synthetic    PASS; 0 hash/reproduction mismatches
uv run pytest -m "not integration" -q              468 passed / 4 deselected
git diff --check                                  PASS
```

## Reproduction

Run A is data/ground_truth/synthetic. Run B was independently prepared, validated, and frozen into `.tmp/synthetic_independent_frozen` using the same committed source, registry, seed, and ATT&CK bytes. All 14 frozen files, including the manifest and audit documents, were byte-identical. Exact run A/run B hashes are recorded in data/audit/synthetic_reproducibility.json. `verify-synthetic` also independently regenerates the six semantic files on every invocation.

## Frozen artifact hashes

| File | SHA-256 | Records / contents |
|---|---|---|
| dataset_manifest.json | `4576b793360d02b60d619d199fd34d4555ace33215303ee847715c162a50dcc2` | 1 document |
| duplicate_audit.json | `1b0411170ffa38a64c8a5f1530a0a7408fe9c26f26deba60a3f74e33d11b8c18` | 1 document |
| events.jsonl | `84e5a7be3cd251f3932448ec535d4df0d3da1351f0e7cdbe86747bbf2a4e76c0` | 1434 |
| generation_metadata.json | `680f991ec96efe66af1eb93df19abc067d242802e387552d821593e060fcbd2c` | 1 document |
| ground_truth.jsonl | `8f3d73bac7e81336a3e90bfa5a5d0850a51ac5588385ee53ad940bcbc3612608` | 1340 |
| inference.jsonl | `90d5f59e64f669f95d5ddccd86f1f047e10ee3dc46e4b67a8cd13d1ddf2cd4b8` | 1340 |
| leakage_audit.json | `0a0a5d5c4141233313355da146549df794766f3782d750712c341111af4ee220` | 1 document |
| manual_review.json | `a0c6b5c489e9a64825a28baeecbfcdd29dc5626dc50dd50c5f1eb36afb37de64` | 66 inspected cases |
| manual_spotcheck.md | `dece58ffef2cfb98c031d3ea001e4df922f770875442ccd1e47831b212928e6d` | 66 inspected cases |
| pairs.jsonl | `079e57a441b18d127739f610e7f62c263d943eefa19ca4ea5c6eab8b8a07665d` | 670 |
| split_manifest.json | `37fce63ccaa6db8e13604b7e3783997a10635f58995881b5e41913e6f550f43f` | 670 split assignments |
| statistics.json | `9145c1e612e25e5bd5c1162ab652569e83a488decf9a53425ae02e1f957067ac` | 1 document |
| validation_report.json | `11e5728b79f2360b8bb22017fcd71834c215a68a600442fc68024f21fe7597b1` | 1 document |
| views.jsonl | `1e6b0d3bd525b8fe9f97ba9e5656905597a3939e47c130a9e6f74535e2cd421d` | 1340 |

## Research boundaries and limitations

- Same GPT-5.6 Luna, xhigh reasoning, baseline prompt, output schema, API client and retrieval depths 1/3/5/10 remain untouched. No model requests, retrieval diagnostics or T20 experiments were run.
- Synthetic paired reference annotations are evidence-conditioned and closed-world; they are not independent real-world event labels. Family holdout reduces template overlap but cannot establish generalization to real incidents.
- Recorded command/configuration evidence does not establish successful execution. Existing approved DLL-service strings express synthetic configuration/invocation; they are not a verified runtime svchost loading trace. Vendor paths/names are not cryptographic signer proof.
- Safe synthetic indicators and placeholder credentials are not live infrastructure or real secrets. No telemetry command was executed.
- Only inference.jsonl is intended for model input. pairs.jsonl includes ground truth and must remain evaluation-only.
- Historical Windows-APT artifacts and unresolved reconciliation/lineage gates are retained; synthetic completion does not resolve them.

## Data task evidence

| Task | Evidence |
|---|---|
| T05 | Pinned ATT&CK bytes/hash and approved registry binding |
| T06 | Approved semantic corrections, canonical telemetry and all family predicates validated |
| T07 | Whitelist inference export, deterministic realization and duplicate audit |
| T08 | Exact predeclared quotas and unchanged family split assignments |
| T09 | Zero leakage plus actual deterministic 66-case inspection and committed audit package |
| T10 | Frozen manifests, 670 pairs, same-seed byte reproduction and verify-synthetic |
