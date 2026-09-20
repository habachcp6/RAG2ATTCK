# Repository Branch Hygiene Audit

## Overview
Audit of all legacy, fix, and task branches in `habachcp6/RAG2ATTCK` against canonical
`main` at `5d12ee1` (current HEAD after coordinator corrections pass, 2026-09-20).

No branches were deleted, merged, or force-pushed during this audit.

---

## 1. Branch Classification

### A. Fully Merged / Superseded (branch tips are ancestors of `main`)
These branches have been formally merged into `main` via PRs or fast-forward merges:

- `ci/github-actions` — Fully merged into `main` via PR #1.
- `fix/ci-portable-tests` — Fully merged into `main` via PR #2.
- `fix/quality-gates` — Fully merged into `main` via PR #9.
- `fix/t18-t19-hardening` — Fully merged into `main` via PR #3.
- `fix/t18-t19-main-integration` — Fully merged into `main` via PR #5.
- `fix/t15-exception-boundary` — Fully merged into `main` (commit `52d1ea3`).
- `fix/t20-validation-hardening` — Fully merged into `main` (commit `2cf63a6`).
- `docs/research-state-sync` — Fully merged into `main` (commit `1616b2d`).
- `analysis/t20-retrieval-failure` — Fully merged into `main` (commit `8dc043d`).

### B. Diverged — Content Superseded by `main`
These branches contain development work whose features and bug fixes are fully present
in `main` via formal integration paths:

- `baseline-infra` — Early No-RAG baseline; superseded by `main`.
- `task/t16-attack-pin` — ATT&CK v19.2 pinning; superseded by `main`.
- `task/t17-attack-corpus` — Windows corpus builder; superseded by `main`.
- `task/t18-faiss-retriever` — FAISS retriever; superseded by `main`.
- `task/t19-rag-pipeline` — RAG pipeline; superseded by `main`.
- `task/t20-retrieval-diagnostics` — Initial diagnostics; superseded by `main`.
- `task/t15-no-rag-pilot` — Initial T15 pilot; merged via PR #7; superseded by `main`.
- `fix/t15-pilot-hardening` — Earlier T15 hardening pass; content incorporated into
  `task/t15-no-rag-pilot` and later `fix/t15-exception-boundary`. `main` is ahead.
- `fix/t15-exception-hardening` — Alternative T15 exception hardening attempt;
  content incorporated into `fix/t15-exception-boundary`. `main` is ahead.
- `fix/t20-diagnostics-correctness` — Earlier diagnostics correctness pass; content
  incorporated into multi-label metric fixes merged into `main`. `main` is ahead.
- `fix/t20-per-technique-absence` — Per-technique absence metric fix; content
  incorporated into `main` via the correctness chain. `main` is ahead.
- `codex/fix-t15-exception-hardening` — Parallel codex T15 hardening; content
  merged via `fix/t15-exception-boundary`. `main` is ahead.
- `codex/fix-t20-top10-absence` — Parallel codex T20 fix; content merged via
  `fix/t20-diagnostics-correctness` chain. `main` is ahead.
- `task/t05-t10-stage-b-data-freeze` — Stage B data freeze stash; superseded.

### C. Contains Unique Unmerged Work — Requires Manual Review
These branches contain content NOT present on canonical `main`:

- `docs/t33-related-work` (`702b689`) — Contains `reports/T33_related_work.md`
  (initial related work draft with comparator metadata).
- `fix/t33-evidence-hardening` (`4f38f9a`) — Contains `reports/T33_related_work.md`
  with hardened comparator evidence citations (superset of `docs/t33-related-work`).

**Recommendation for T33:** Neither branch should be merged during this hardening
cycle. A dedicated coordinator gate and formal PR should review T33 once related work
evidence is independently verified. `fix/t33-evidence-hardening` is the more
complete branch and should be the merge candidate when T33 is formally approved.

---

## 2. Summary Table

| Branch | Head | Classification | Unique Unmerged Files |
|---|---|---|---|
| `ci/github-actions` | `17a768c` | Fully merged | None |
| `fix/ci-portable-tests` | `cf0aa36` | Fully merged | None |
| `fix/quality-gates` | `b96d614` | Fully merged | None |
| `fix/t18-t19-hardening` | `c8a1257` | Fully merged | None |
| `fix/t18-t19-main-integration` | `9410480` | Fully merged | None |
| `fix/t15-exception-boundary` | `52d1ea3` | Fully merged | None |
| `fix/t20-validation-hardening` | `2cf63a6` | Fully merged | None |
| `docs/research-state-sync` | `1616b2d` | Fully merged | None |
| `analysis/t20-retrieval-failure` | `8dc043d` | Fully merged | None |
| `baseline-infra` | `a1cae3a` | Diverged / Superseded | None |
| `task/t16-attack-pin` | `97c56dc` | Diverged / Superseded | None |
| `task/t17-attack-corpus` | `8b84677` | Diverged / Superseded | None |
| `task/t18-faiss-retriever` | `1f94bdf` | Diverged / Superseded | None |
| `task/t19-rag-pipeline` | `dbe2d57` | Diverged / Superseded | None |
| `task/t20-retrieval-diagnostics` | `5ce34cd` | Diverged / Superseded | None |
| `task/t15-no-rag-pilot` | `dca8c1e` | Diverged / Superseded | None |
| `fix/t15-pilot-hardening` | `d90eb76` | Diverged / Superseded | None |
| `fix/t15-exception-hardening` | `522ecc6` | Diverged / Superseded | None |
| `fix/t20-diagnostics-correctness` | `29fa523` | Diverged / Superseded | None |
| `fix/t20-per-technique-absence` | `c03d8f2` | Diverged / Superseded | None |
| `codex/fix-t15-exception-hardening` | `78fcd6c` | Diverged / Superseded | None |
| `codex/fix-t20-top10-absence` | `4b06bfc` | Diverged / Superseded | None |
| `task/t05-t10-stage-b-data-freeze` | `0b419b9` | Diverged / Superseded | None |
| `docs/t33-related-work` | `702b689` | **Unique unmerged** | `reports/T33_related_work.md` |
| `fix/t33-evidence-hardening` | `4f38f9a` | **Unique unmerged** | `reports/T33_related_work.md` |

---

## 3. T33 Status

T33 branches (`docs/t33-related-work`, `fix/t33-evidence-hardening`) contain related
work literature survey materials. These are not methodology changes and do not modify
any scientific artifacts, ground truth, or retrieval pipeline.

**Decision:** Do not merge T33 in this hardening cycle. Defer to a dedicated
coordinator gate after independent verification of the evidence citations in
`fix/t33-evidence-hardening`.

---

*Audit conducted during coordinator hardening pass; no branch mutations performed.*
