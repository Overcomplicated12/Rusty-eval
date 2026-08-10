#!/usr/bin/env python3
"""Summarize existing result.json files without modifying generated artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-root", default="results")
    args = parser.parse_args()
    records = []
    for path in sorted(Path(args.results_root).glob("*/*/result.json")):
        records.append(json.loads(path.read_text(encoding="utf-8")))
    by_outcome: dict[str, int] = {}
    for record in records:
        outcome = str(record.get("outcome", "UNKNOWN"))
        by_outcome[outcome] = by_outcome.get(outcome, 0) + 1
    print(json.dumps({"experiment_count": len(records), "outcomes": by_outcome}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
