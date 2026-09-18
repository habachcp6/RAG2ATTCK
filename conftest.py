r"""
conftest.py - Root pytest configuration.

ENVIRONMENT GUARD: Aborts immediately if pytest is not running inside
the project's .venv virtual environment. This prevents accidental test
runs against the wrong Python interpreter (e.g., user-level or system Python).

Correct usage:
    uv run pytest               (recommended)
    .venv\Scripts\activate && pytest  (Windows manual)
    source .venv/bin/activate && pytest  (Unix manual)
"""

import os
import sys
import pytest
from pathlib import Path

# ---------------------------------------------------------------------------
# Derive repo root from this file's location — never from cwd.
# This is safe regardless of which subdirectory pytest is invoked from.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent

if sys.platform == "win32":
    _expected = _REPO_ROOT / ".venv" / "Scripts" / "python.exe"
else:
    _expected = _REPO_ROOT / ".venv" / "bin" / "python"

_current  = Path(sys.executable).resolve()
_expected = _expected.resolve()

# --- 1. venv must exist -------------------------------------------------------
if not _expected.exists():
    raise pytest.UsageError(
        f"\nENVIRONMENT ERROR\n"
        f"Project virtual environment not found:\n"
        f"  {_expected}\n\n"
        f"Create it with:\n"
        f"  uv sync\n"
    )

# --- 2. Must be running inside that exact venv --------------------------------
try:
    _same_python = os.path.samefile(_current, _expected)
except OSError:
    # Fallback if one of the paths doesn't exist or is a broken symlink
    _same_python = _current == _expected

if not _same_python:
    raise pytest.UsageError(
        f"\nENVIRONMENT ERROR\n"
        f"pytest is running with the wrong Python interpreter.\n\n"
        f"  Running : {_current}\n"
        f"  Expected: {_expected}\n\n"
        f"Run tests with:\n"
        f"  uv run pytest                       (recommended)\n"
        f"  .\\scripts\\dev.ps1 test             (Windows helper)\n"
    )
