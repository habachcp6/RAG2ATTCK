"""Public interface: read-only preflight only; no live/freeze/force switches."""

import argparse
import json
import sys
from pathlib import Path

from src.experiment.config import load_plan


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate the pre-freeze experiment without execution")
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parents[2] / "config" / "experiment_config.json")
    parser.add_argument("--dry-run", action="store_true", required=True)
    args = parser.parse_args(argv)
    try:
        report = load_plan(args.config).report()
    except (ValueError, TypeError, KeyError, OSError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc), "provider_calls": 0}), file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    # Structural validation is not permission to execute a scientific experiment.
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
