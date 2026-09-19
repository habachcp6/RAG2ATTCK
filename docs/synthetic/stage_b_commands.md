# Synthetic Stage B commands

Run from the repository with the pinned uv environment. No telemetry command is
executed and no model/API call occurs. The historical Windows-APT pipeline remains
independently gated.

```text
uv lock --check --offline
uv sync --frozen
uv pip check
uv run python scripts/validate_synthetic_registry.py
uv run python -m src.data_ground_truth prepare-synthetic
uv run python -m src.data_ground_truth validate-synthetic
uv run python -m src.data_ground_truth freeze-synthetic
uv run python -m src.data_ground_truth verify-synthetic
```

Preparation requires the canonical hash-verified ATT&CK reference and its existing
acquisition manifest, plus the explicit approved registry/config hashes in
`config/synthetic_approval.json`. Candidate files live in `.tmp/synthetic_candidate`.
An existing nonempty candidate is never overwritten. Use a fresh `--output-dir`
for prepare and matching `--candidate-dir` for validate/freeze when reproducing.
The four commands accept `--workspace`; they never change the process CWD.

After prepare, inspect `data/audit/synthetic_manual_spotcheck.md`: raw telemetry,
both actual inference views, and the separate per-view annotations/references.
The deterministic package covers every family, both splits, at least two pairs per
technique, multi-label cases, and at least four cases for each negative category.
Record actual inspection in `data/audit/synthetic_manual_review.json`, bound to
the package, registry and semantic file hashes. There is no CLI option that marks
uninspected samples approved and no force-freeze bypass.

Freeze reruns validation and verifies the review before writing the final directory.
An existing frozen directory can only be accepted if all bytes are identical.
Verify checks every frozen file, reconstructs sidecars from pairs, reruns all
validation/audits, checks source-code provenance, then independently regenerates
the six semantic files from the approved registry and seed. A failure exits nonzero.

Only `inference.jsonl` is the model input interface: each row contains an opaque
view `sample_id` and an `endpoint_evidence` string constructed through
`get_inference_payload`. Do not pass `pairs.jsonl` or annotation records to a model.
These are evaluation/provenance artifacts containing labels and rationales.

Serialization is UTF-8, LF, compact sorted-key JSON, sorted records and a final
newline. No wall-clock value or machine path enters dataset identity. The manifest
contains all frozen artifact hashes except its own (no circular self-hash).
Generator source-file hashes bind the code; the generator commit is the last
commit touching those files, so later documentation/data commits do not invalidate
the original generation provenance.

The benchmark is synthetic and limited to the approved closed-world rubric.
Paths, task/service configuration and command arguments are evidence of recorded
configuration/invocation, not proof that execution succeeded. Vendor names do not
constitute independent cryptographic signing evidence. Corpus/model/retrieval and
experiment execution are outside Stage B.
