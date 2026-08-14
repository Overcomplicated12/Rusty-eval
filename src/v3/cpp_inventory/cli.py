"""Command-line entry point for the isolated V3 C++ inventory scaffold."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from .config import InventoryConfig, load_config
from .dedup import deduplicate_functions
from .report import output_dir, write_placeholder_reports
from .scope import apply_scope
from .schema import FunctionRecord


def discover_functions(config: InventoryConfig) -> list[FunctionRecord]:
    """Placeholder for future JSONL input from the Clang inventory tool."""
    del config
    return []


def run_scan(config_path: Path, *, run_id: str | None = None, repository_root: Path | None = None) -> Path:
    """Create a V3-only placeholder run and return its output directory."""
    config = load_config(config_path)
    root = repository_root.resolve() if repository_root else Path.cwd().resolve()
    run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    records = deduplicate_functions(apply_scope(discover_functions(config), config))
    output = output_dir(root, config.project, run_id)
    write_placeholder_reports(output, config, records, run_id)
    return output


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan = subparsers.add_parser("scan", help="create a placeholder V3 inventory run")
    scan.add_argument("--config", required=True, type=Path)
    scan.add_argument("--run-id")
    args = parser.parse_args(argv)
    if args.command == "scan":
        print(run_scan(args.config, run_id=args.run_id))


if __name__ == "__main__":
    main()
