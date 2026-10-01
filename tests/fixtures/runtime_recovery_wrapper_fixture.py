"""Portable fixture for runtime recovery atomic replacement retry wrapper.

Contains the archived, non-sensitive retry wrapper extracted from the canonical
resume launcher. Provides portable verification across environments (local and CI)
without depending on machine-specific absolute paths.

Provenance:
- Whole Launcher Canonical SHA-256:
  05b60f050cb456688ed74bddb72f994f3b61a84b56f8e568dda4c17467c4c7aa
- Extracted Wrapper Block SHA-256:
  e4a0115ff2d712bf6a0b896b50d9f4d412b786707d9721f47c74a4ac174e5f68
"""

from __future__ import annotations

import ast
import hashlib
import os
import time
from pathlib import Path
from typing import Any, Callable

CANONICAL_LAUNCHER_SHA256 = (
    "05b60f050cb456688ed74bddb72f994f3b61a84b56f8e568dda4c17467c4c7aa"
)
CANONICAL_WRAPPER_BLOCK_SHA256 = (
    "e4a0115ff2d712bf6a0b896b50d9f4d412b786707d9721f47c74a4ac174e5f68"
)

# Exact lines 47-75 extracted from canonical launcher (29 lines of wrapper definitions)
RAW_WRAPPER_BLOCK = (
    "_orig_write_atomically = StudyBudgetLedger._write_atomically_unlocked\n"
    "def _robust_write_atomically(self):\n"
    "    for attempt in range(12):\n"
    "        try:\n"
    "            return _orig_write_atomically(self)\n"
    "        except (PermissionError, OSError) as exc:\n"
    '            winerror = getattr(exc, "winerror", None)\n'
    "            if winerror in (5, 32) or isinstance(exc, PermissionError):\n"
    "                if attempt == 11:\n"
    "                    raise\n"
    "                time.sleep(0.05 * (1.5 ** attempt))\n"
    "            else:\n"
    "                raise\n"
    "StudyBudgetLedger._write_atomically_unlocked = _robust_write_atomically\n"
    "\n"
    "_orig_anchor_atomically = StudyBudgetLedger._write_anchor_atomically_unlocked\n"
    "def _robust_anchor_atomically(self, data):\n"
    "    for attempt in range(12):\n"
    "        try:\n"
    "            return _orig_anchor_atomically(self, data)\n"
    "        except (PermissionError, OSError) as exc:\n"
    '            winerror = getattr(exc, "winerror", None)\n'
    "            if winerror in (5, 32) or isinstance(exc, PermissionError):\n"
    "                if attempt == 11:\n"
    "                    raise\n"
    "                time.sleep(0.05 * (1.5 ** attempt))\n"
    "            else:\n"
    "                raise\n"
    "StudyBudgetLedger._write_anchor_atomically_unlocked = _robust_anchor_atomically\n"
)


def verify_wrapper_block_digest() -> bool:
    """Verify that the embedded raw wrapper block matches its frozen SHA-256 digest."""
    computed = hashlib.sha256(RAW_WRAPPER_BLOCK.encode("utf-8")).hexdigest()
    return computed == CANONICAL_WRAPPER_BLOCK_SHA256


def verify_local_launcher_if_present(
    launcher_path: Path | str | None = None,
) -> tuple[bool, str]:
    """Optional check: if the local live launcher exists, verify byte/AST equivalence with fixture.

    If not present (e.g. running in GitHub Actions CI), returns (True, "SKIPPED_NOT_PRESENT").
    NEVER imports the live launcher directly.
    """
    target = launcher_path or os.environ.get("RAG2ATTCK_LIVE_LAUNCHER_PATH")
    if not target:
        return True, "SKIPPED_NOT_PRESENT"

    target_path = Path(target)
    if not target_path.is_file():
        return True, "SKIPPED_NOT_PRESENT"

    content = target_path.read_bytes()
    whole_sha = hashlib.sha256(content).hexdigest()
    if whole_sha != CANONICAL_LAUNCHER_SHA256:
        return (
            False,
            f"Launcher SHA mismatch: {whole_sha} != {CANONICAL_LAUNCHER_SHA256}",
        )

    lines = content.decode("utf-8").splitlines()
    extracted_block = "\n".join(lines[46:75]) + "\n"
    block_sha = hashlib.sha256(extracted_block.encode("utf-8")).hexdigest()
    if block_sha != CANONICAL_WRAPPER_BLOCK_SHA256:
        return (
            False,
            f"Extracted block SHA mismatch: {block_sha} != {CANONICAL_WRAPPER_BLOCK_SHA256}",
        )

    ast_fixture = ast.parse(RAW_WRAPPER_BLOCK)
    ast_extracted = ast.parse(extracted_block)
    if ast.dump(ast_fixture) != ast.dump(ast_extracted):
        return False, "AST structure drift between fixture and extracted block"

    return True, "VERIFIED_EQUIVALENT"


def build_robust_methods(
    orig_write: Callable[..., Any],
    orig_anchor: Callable[..., Any],
    sleep_fn: Callable[[float], None] = time.sleep,
) -> tuple[Callable[..., Any], Callable[..., Any]]:
    """Build the robust write and anchor methods by dynamically executing the archived RAW_WRAPPER_BLOCK."""

    class _LedgerProxy:
        _write_atomically_unlocked = orig_write
        _write_anchor_atomically_unlocked = orig_anchor

    class _TimeProxy:
        @staticmethod
        def sleep(seconds: float) -> None:
            sleep_fn(seconds)

    exec_ns: dict[str, Any] = {
        "StudyBudgetLedger": _LedgerProxy,
        "time": _TimeProxy,
        "PermissionError": PermissionError,
        "OSError": OSError,
    }
    exec(compile(RAW_WRAPPER_BLOCK, "<archived_wrapper_block>", "exec"), exec_ns)
    robust_write = exec_ns["StudyBudgetLedger"]._write_atomically_unlocked
    robust_anchor = exec_ns["StudyBudgetLedger"]._write_anchor_atomically_unlocked
    return robust_write, robust_anchor
