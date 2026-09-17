"""Validate the Stage A semantic registry against the pinned ATT&CK snapshot."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "synthetic_templates.json"
STIX = ROOT / "attack" / "raw" / "enterprise-v19.2" / "enterprise-attack-19.2.json"

sys.path.insert(0, str(ROOT))

from src.synthetic_validator import validate_template_registry


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    result = validate_template_registry(registry, STIX)
    print(json.dumps({"passed": result.passed, "statistics": result.statistics}, indent=2))
    if result.errors:
        print("Errors:")
        print("\n".join(result.errors))
    if result.warnings:
        print("Warnings:")
        print("\n".join(result.warnings))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
