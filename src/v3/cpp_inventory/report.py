"""Writers for the stable, V3-only result artifact layout."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path

from .config import InventoryConfig
from .schema import FunctionRecord, RawFunctionRecord
from .scope import ScopeExclusion


def output_dir(repository_root: Path, project: str, run_id: str) -> Path:
    """Return the only permitted result location for a V3 inventory run."""
    return repository_root / "results" / "v3" / "cpp-inventory" / project / run_id


def write_placeholder_reports(
    output: Path, config: InventoryConfig, records: list[FunctionRecord], run_id: str
) -> None:
    """Write empty-compatible artifacts until parser integration exists."""
    output.mkdir(parents=True, exist_ok=False)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest = {
        "schema_version": 3,
        "status": "placeholder",
        "project": config.project,
        "run_id": run_id,
        "generated_at": generated_at,
        "config_path": str(config.config_path),
        "repo_path": str(config.repo_path),
        "compile_commands_path": str(config.compile_commands_path),
        "scope": {"include": list(config.scope_include), "exclude": list(config.scope_exclude)},
    }
    coverage = {"status": "placeholder", "translation_units_seen": 0, "translation_units_parsed": 0}
    summary = {"status": "placeholder", "function_count": len(records), "parse_failure_count": 0}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (output / "coverage.json").write_text(json.dumps(coverage, indent=2, sort_keys=True) + "\n")
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    (output / "functions.jsonl").write_text(
        "".join(json.dumps(asdict(record), sort_keys=True) + "\n" for record in records)
    )
    (output / "parse_failures.jsonl").write_text("")
    (output / "report.md").write_text(
        "# V3 C++ inventory placeholder\n\n"
        f"Project: `{config.project}`\n\n"
        "No Clang AST parsing, production scope filtering, deduplication, or "
        "migration classification has been implemented yet.\n"
    )


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in records), encoding="utf-8")


def write_inventory_reports(
    output: Path,
    config: InventoryConfig,
    run_id: str,
    *,
    scan_directory: Path | None,
    raw_records: list[RawFunctionRecord],
    functions: list[FunctionRecord],
    exclusions: list[ScopeExclusion],
    coverage: dict[str, object],
    failures: tuple[dict[str, object], ...],
) -> None:
    """Write interpreted inventory artifacts alongside raw observations and failures."""
    output.mkdir(parents=True, exist_ok=False)
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest = {
        "schema_version": 3,
        "status": "interpreted",
        "project": config.project,
        "run_id": run_id,
        "generated_at": generated_at,
        "config_path": str(config.config_path),
        "repo_path": str(config.repo_path),
        "compile_commands_path": str(config.compile_commands_path),
        "scan_directory": str(scan_directory) if scan_directory else None,
        "scope": {"include": list(config.scope_include), "exclude": list(config.scope_exclude)},
    }
    summary = {
        "function_count": len(functions),
        "parse_failure_count": len(failures),
        "primary_denominator": coverage["primary_denominator"],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (output / "coverage.json").write_text(json.dumps(coverage, indent=2, sort_keys=True) + "\n")
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    _write_jsonl(output / "raw_functions.jsonl", [record.to_dict() for record in raw_records])
    _write_jsonl(output / "functions.jsonl", [record.to_dict() for record in functions])
    _write_jsonl(output / "exclusions.jsonl", [
        {"record": exclusion.record.to_dict(), "reason": exclusion.reason, "pattern": exclusion.pattern}
        for exclusion in exclusions
    ])
    _write_jsonl(output / "parse_failures.jsonl", list(failures))
    (output / "report.md").write_text(
        "# V3 C++ inventory\n\n"
        f"Project: `{config.project}`\n\n"
        f"Translation units selected: {coverage['translation_units_seen']}\n\n"
        f"Translation units parsed: {coverage['translation_units_parsed']}\n\n"
        f"Scanner failures: {len(failures)}\n",
        encoding="utf-8",
    )
