"""Command-line entry point for the isolated V3 C++ inventory scaffold."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import json

from .config import load_config
from .coverage import calculate_coverage
from .dedup import deduplicate_functions
from .normalize import normalize_records
from .report import output_dir, write_inventory_reports
from .runner import scan_directory
from .schema import RawFunctionRecord
from .scope import apply_scope


def run_scan(
    config_path: Path,
    *,
    directory: Path | None = None,
    clang_inventory: Path,
    run_id: str | None = None,
    repository_root: Path | None = None,
) -> Path:
    """Scan compile-database translation units below a directory and return the output path."""
    config = load_config(config_path)
    root = repository_root.resolve() if repository_root else Path.cwd().resolve()
    run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    result = scan_directory(config, directory=directory, clang_inventory=clang_inventory)
    output = output_dir(root, config.project, run_id)
    raw_records = [RawFunctionRecord.from_mapping(json.loads(line)) for line in result.jsonl.splitlines() if line]
    normalized_records = normalize_records(raw_records, config.repo_path)
    scoped = apply_scope(normalized_records, config)
    functions = deduplicate_functions(scoped.included)
    coverage = calculate_coverage(
        translation_units_seen=result.translation_units_seen,
        translation_units_parsed=result.translation_units_parsed,
        raw_records=normalized_records,
        scope_result=scoped,
        deduplicated_records=functions,
    )
    write_inventory_reports(
        output,
        config,
        run_id,
        scan_directory=directory.resolve() if directory else None,
        raw_records=raw_records,
        functions=functions,
        exclusions=scoped.exclusions,
        coverage=coverage,
        failures=result.failures,
    )
    return output


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan = subparsers.add_parser(
        "scan", help="scan a directory with the V3 Clang inventory tool"
    )
    scan.add_argument("--config", required=True, type=Path)
    scan.add_argument("--directory", type=Path)
    scan.add_argument("--clang-inventory", required=True, type=Path)
    scan.add_argument("--run-id")
    args = parser.parse_args(argv)
    if args.command == "scan":
        print(
            run_scan(
                args.config,
                directory=args.directory,
                clang_inventory=args.clang_inventory,
                run_id=args.run_id,
            )
        )


if __name__ == "__main__":
    main()
