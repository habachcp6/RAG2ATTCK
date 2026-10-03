"""Alias and wrapper for generate_r9_artifact_inventory.py."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.generate_r9_artifact_inventory import generate_inventory, main

__all__ = ["generate_inventory", "main"]

if __name__ == "__main__":
    sys.exit(main())
