# Repository Branch Hygiene Audit (Subagent E)

## Overview
Read-only audit of all legacy, fix, and task branches in `habachcp6/RAG2ATTCK` against canonical `main` (`dca8c1e`).

No branches were deleted, merged, or force-pushed during this audit.

---

## 1. Branch Classification

### A. Fully Merged / Superseded (0 commits ahead of main)
These branches have identical heads or their tips are direct ancestors of `main`:
- `ci/github-actions` (`17a768cf`) — Fully merged into `main` via PR #1.
- `fix/ci-portable-tests` (`cf0aa36f`) — Fully merged into `main` via PR #2.
- `fix/quality-gates` (`b96d6141`) — Fully merged into `main`.
- `fix/t18-t19-hardening` (`c8a1257c`) — Fully merged into `main` via PR #3.
- `fix/t18-t19-main-integration` (`94104804`) — Fully merged into `main` via PR #5.

### B. Diverged but Content Already Superseded by `main`
These branches contain early development commits from prior tasks whose features and bug fixes were subsequently integrated into `main` via formal PRs and hardened further:
- `baseline-infra` (`a1cae3ae`) — Early No-RAG baseline development; superseded by `main`.
- `task/t16-attack-pin` (`97c56dc0`) — Pinned ATT&CK v19.2; superseded by `main`.
- `task/t17-attack-corpus` (`8b84677a`) — Windows corpus builder; superseded by `main`.
- `task/t18-faiss-retriever` (`1f94bdf7`) — FAISS retriever implementation; superseded by `main`.
- `task/t19-rag-pipeline` (`dbe2d579`) — RAG pipeline with controlled invariants; superseded by `main`.
- `task/t20-retrieval-diagnostics` (`5ce34cd8`) — Initial diagnostic runner; superseded by `main`.
- `fix/t15-pilot-hardening` (`d90eb76d`) — **Specific check completed:** All content from this branch was incorporated into `task/t15-no-rag-pilot` and merged via PR #7 (`dca8c1e`), followed by operational exception narrowing in the current hardening round. `main` is strictly ahead of this branch.
- `fix/t20-diagnostics-correctness` (`29fa523a`) — **Specific check completed:** `main` already incorporates the multi-label diagnostic fixes, per-technique absence calculations, and deterministic tests from this branch. `main` is strictly ahead of this branch.

### C. Contains Unique Unmerged Work (Requires Manual Review)
These branches contain work that is NOT present on canonical `main`:
- `docs/t33-related-work` (`702b689a`) — Contains `reports/T33_related_work.md` (initial related work draft).
- `fix/t33-evidence-hardening` (`4f38f9a9`) — Contains `reports/T33_related_work.md` with hardened comparator metadata and evidence citations.
  - *Recommendation:* Neither branch should be merged during this hardening cycle (per Section 5, C7). A separate coordinator gate and dedicated PR should review T33 once its related work evidence is formally verified.

---

## 2. Summary Table

| Branch Name | Head Commit | Merge Base | Classification | Unique Unmerged Files |
|---|---|---|---|---|
| `ci/github-actions` | `17a768c` | `17a768c` | Fully merged | None |
| `fix/ci-portable-tests` | `cf0aa36` | `cf0aa36` | Fully merged | None |
| `fix/quality-gates` | `b96d614` | `b96d614` | Fully merged | None |
| `fix/t18-t19-hardening` | `c8a1257` | `c8a1257` | Fully merged | None |
| `fix/t18-t19-main-integration` | `9410480` | `9410480` | Fully merged | None |
| `baseline-infra` | `a1cae3a` | `e3c6856` | Diverged / Superseded | None (superseded by main) |
| `task/t16-attack-pin` | `97c56dc` | `e3c6856` | Diverged / Superseded | None (superseded by main) |
| `task/t17-attack-corpus` | `8b84677` | `e3c6856` | Diverged / Superseded | None (superseded by main) |
| `task/t18-faiss-retriever` | `1f94bdf` | `e3c6856` | Diverged / Superseded | None (superseded by main) |
| `task/t19-rag-pipeline` | `dbe2d57` | `e3c6856` | Diverged / Superseded | None (superseded by main) |
| `task/t20-retrieval-diagnostics`| `5ce34cd` | `79e9bbe` | Diverged / Superseded | None (superseded by main) |
| `fix/t15-pilot-hardening` | `d90eb76` | `79e9bbe` | Diverged / Superseded | None (superseded by main) |
| `fix/t20-diagnostics-correctness`|`29fa523` | `79e9bbe` | Diverged / Superseded | None (superseded by main) |
| `docs/t33-related-work` | `702b689` | `79e9bbe` | Unique unmerged work | `reports/T33_related_work.md` |
| `fix/t33-evidence-hardening` | `4f38f9a` | `79e9bbe` | Unique unmerged work | `reports/T33_related_work.md` |
