# T05-T10 Synthetic Dataset Freeze

## Provenance

- Base main: `827eb8b147efc756146261649399ee9e40a1e634`.
- Branch: `task/t05-t10-stage-b-data-freeze`.
- Approved Stage A registry SHA-256: `8495842d24b6a4635e125a1d21dfad811d776efcc8ba138f5441f88457f3350c`.
- Generator: `1.0.0`, commit `11fdc3cdcee49e5d4777feb734d85b007225b275`; source-file hashes are frozen in generation_metadata.json.
- Seed: `20260915`; ATT&CK Enterprise `19.2`.
- ATT&CK source SHA-256: `dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4`.
- User explicitly approved the bounded Stage A telemetry/relation corrections recorded in the preflight report. Labels, quotas, catalog and family splits were preserved byte-for-byte at the relevant JSON value level.

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

## Manual deterministic inspection

Inspected 66 cases spanning all 64 families, both DEV/TEST splits, all eight techniques, multi-label cases and both negative categories. The package contains raw telemetry, actual whitelist inference payloads, per-view ground truth, transition and concrete field references. Case-specific notes are in data/audit/synthetic_manual_review.json, bound to the registry, package and semantic hashes.

Inspection corrected generator defects before freezing: excessive local-account name length; wrong Explorer path; SYSTEM service-process identity; task XML WorkingDirectory; task DEV structure; process/parent identity correlation; and overly broad evidence references. The final package and annotations were rechecked after correction. No review findings remain unresolved under the approved rubric.

## Validation commands

```text
uv lock --check --offline                         PASS
uv sync --frozen                                  PASS
uv pip check                                      PASS
uv run python scripts/validate_synthetic_registry.py  passed=true; 64 families; 670 planned instances
uv run pytest tests/test_synthetic.py -q            116 passed
uv run pytest tests/test_synthetic_generation.py -q 22 passed
uv run pytest tests/test_synthetic_freeze.py -q      14 passed (36 combined Stage B tests passed)
uv run python -m src.data_ground_truth prepare-synthetic   PASS; 670 pairs / 1340 views
uv run python -m src.data_ground_truth validate-synthetic  PASS; 0 errors
uv run python -m src.data_ground_truth freeze-synthetic    PASS
uv run python -m src.data_ground_truth verify-synthetic    PASS; 0 hash/reproduction mismatches
uv run pytest -m "not integration" -q              465 passed / 4 deselected
git diff --check                                  PASS
```

## Reproduction

Run A is data/ground_truth/synthetic. Run B was regenerated independently into .tmp/synthetic_reproduction with the same registry, seed, source code and ATT&CK bytes. All 14 frozen files, including dataset_manifest.json and audit documents, were byte-identical. The reproduction candidate was then deleted and regenerated again; the existing frozen output accepts only identical bytes. Exact run A/run B hashes are recorded in data/audit/synthetic_reproducibility.json. verify-synthetic also independently regenerates the six semantic files on every invocation.

## Frozen artifact hashes

| File | SHA-256 | Records / contents |
|---|---|---|
| dataset_manifest.json | `44541c1a459974de775b3c9b6c59c30fe13d1a794330799ea025e26f865990ed` | 1 document |
| duplicate_audit.json | `1b0411170ffa38a64c8a5f1530a0a7408fe9c26f26deba60a3f74e33d11b8c18` | 1 document |
| events.jsonl | `d0599c0da4f8b412785ad2a7873c121dff7c25aa093cbffc3404bc1a4688dfa9` | 1434 |
| generation_metadata.json | `94016a56d3b663a78d52cdbc92de9f3538b3c6db31302a8ce73ee32807f4a4c1` | 1 document |
| ground_truth.jsonl | `04653ce42fd7e3ea14e60ad959dbf018da50c0b8236884930211e0b4d6b88f0a` | 1340 |
| inference.jsonl | `f32f301cf8309115bdc4bd20becdd85df427fc59bb81a9251836eb46cd7123c8` | 1340 |
| leakage_audit.json | `0a0a5d5c4141233313355da146549df794766f3782d750712c341111af4ee220` | 1 document |
| manual_review.json | `2b4b0ca028d9180f7762040fd84d89f47be7fb24e5eeb49c36de53b03cd972f6` | 66 inspected cases |
| manual_spotcheck.md | `ae9daf39d88a16b66586daecabc8f68db735aecc0a1e7dd9c18f0f9c1c9b0801` | 66 inspected cases |
| pairs.jsonl | `a171788b061d83db70ae3d974baf0c91765bd503361ccb89c83dd679db131b20` | 670 |
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
