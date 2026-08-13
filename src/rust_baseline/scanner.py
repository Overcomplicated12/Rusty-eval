"""End-to-end orchestration for Rust baseline scans."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from . import RUST_BASELINE_SCANNER_VERSION, RUST_BASELINE_SCHEMA_VERSION
from .cargo import checkout_crate, probe_cargo_geiger, probe_count_unsafe, resolve_package_library_target, tool_versions
from .config import find_crate, load_config
from .models import BaselineResult, CheckoutMetadata, ScanMode, ScanStatus, SourceScanStatus, ToolStatus
from .report import BaselineReporter, create_experiment_id, write_summary_files
from .source_scan import scan_source_tree


AI_USE_IDS = ["AI-2026-017", "AI-2026-018"]


def validate_config(config_path: str | Path) -> dict[str, Any]:
    config = load_config(config_path)
    return {
        "config": str(Path(config_path).resolve()),
        "crate_count": len(config.crates),
        "crates": [crate.to_dict() for crate in config.crates],
    }


def run_scan(
    config_path: str | Path,
    crate_name: str,
    mode: ScanMode,
    experiment_id: str | None = None,
) -> Path:
    config = load_config(config_path)
    crate = find_crate(config, crate_name)
    experiment_id = experiment_id or create_experiment_id()
    reporter = BaselineReporter(config.results_root, experiment_id)
    reporter.create()
    root_metadata = _root_metadata(config_path, experiment_id, mode)
    reporter.write_root_metadata(root_metadata)
    _scan_one(reporter, config, crate, mode, datetime.now().astimezone().isoformat(timespec="seconds"))
    write_summary_files(reporter.root, root_metadata)
    return reporter.root


def run_scan_all(config_path: str | Path, mode: ScanMode, experiment_id: str | None = None) -> Path:
    config = load_config(config_path)
    experiment_id = experiment_id or create_experiment_id()
    reporter = BaselineReporter(config.results_root, experiment_id)
    reporter.create()
    root_metadata = _root_metadata(config_path, experiment_id, mode)
    reporter.write_root_metadata(root_metadata)
    scan_date = datetime.now().astimezone().isoformat(timespec="seconds")
    for crate in config.crates:
        _scan_one(reporter, config, crate, mode, scan_date)
    write_summary_files(reporter.root, root_metadata)
    return reporter.root


def regenerate_report(results_root: str | Path) -> Path:
    root = Path(results_root)
    metadata_path = root / "metadata.json"
    metadata = {}
    if metadata_path.exists():
        import json

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    else:
        metadata = {
            "experiment_id": root.name,
            "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "mode": "mixed",
        }
    write_summary_files(root, metadata)
    return root


def _scan_one(reporter: BaselineReporter, config: Any, crate: Any, mode: ScanMode, scan_date: str) -> None:
    stdout_dir = reporter.ensure_stdout_dir(crate.name, mode)
    rust_versions = tool_versions(config.tools)
    failures: list[str] = []
    source_scan: dict[str, Any] | None = None
    geiger_record = None
    count_unsafe_record = None
    checkout_metadata = None
    source_scan_status = SourceScanStatus.OK
    scan_status = ScanStatus.OK
    try:
        checkout_root = checkout_crate(crate, config.workspace_root, config.tools)
        resolution = resolve_package_library_target(checkout_root, crate.package, config.tools)
        manifest_path = resolution.manifest_path
        package_root = resolution.package_root
        checkout_metadata = CheckoutMetadata(
            source_kind=crate.source_kind,
            source_url=crate.source_url,
            pinned_reference=crate.pinned_reference,
            checkout_root=str(checkout_root),
            repository_root=str(resolution.repository_root),
            workspace_root=str(resolution.workspace_root),
            package_root=str(package_root),
            manifest_path=str(manifest_path),
            package_name=resolution.package_name,
            library_target_source=str(resolution.library_target_source),
            production_source_roots=[str(path) for path in resolution.production_source_roots],
        )
        reporter.write_crate_metadata(crate, checkout_metadata.to_dict())
        source_scan = scan_source_tree(package_root, resolution.production_source_roots)
        reporter.write_mode_artifact(crate.name, mode, "source_scan.json", source_scan)
        geiger_record = probe_cargo_geiger(manifest_path, mode, crate, config.tools, stdout_dir)
        reporter.write_mode_artifact(crate.name, mode, "cargo_geiger.json", geiger_record.to_dict())
        count_unsafe_record = probe_count_unsafe(package_root, stdout_dir)
        reporter.write_mode_artifact(crate.name, mode, "count_unsafe.json", count_unsafe_record.to_dict())
    except Exception as error:
        failures.append(str(error))
        source_scan_status = SourceScanStatus.FAILED
        scan_status = ScanStatus.FAILED
    summary = _summary_row(crate, mode, source_scan, geiger_record, count_unsafe_record, scan_status)
    result = BaselineResult(
        experiment_id=reporter.root.name,
        crate_name=crate.name,
        package=crate.package,
        revision=crate.pinned_reference,
        mode=mode,
        scan_date=scan_date,
        enabled_features=list(crate.features),
        default_features_enabled=mode is ScanMode.DEFAULT,
        all_features_enabled=mode is ScanMode.ALL_FEATURES,
        source_checkout=checkout_metadata,
        rust_toolchain=rust_versions,
        source_scan_status=source_scan_status,
        scan_status=scan_status,
        summary=summary,
        failures=failures,
    )
    reporter.write_mode_artifact(crate.name, mode, "result.json", result.to_dict())
    if geiger_record is None and not reporter.artifact_exists(crate.name, mode, "cargo_geiger.json"):
        reporter.write_mode_artifact(crate.name, mode, "cargo_geiger.json", {"tool": "cargo-geiger", "status": ToolStatus.SKIPPED.value, "notes": failures})
    if count_unsafe_record is None and not reporter.artifact_exists(crate.name, mode, "count_unsafe.json"):
        reporter.write_mode_artifact(crate.name, mode, "count_unsafe.json", {"tool": "count-unsafe", "status": ToolStatus.SKIPPED.value, "notes": failures})
    if source_scan is None and not reporter.artifact_exists(crate.name, mode, "source_scan.json"):
        reporter.write_mode_artifact(crate.name, mode, "source_scan.json", {"status": SourceScanStatus.FAILED.value, "failures": failures})


def _root_metadata(config_path: str | Path, experiment_id: str, mode: ScanMode) -> dict[str, Any]:
    return {
        "schema_version": RUST_BASELINE_SCHEMA_VERSION,
        "scanner_version": RUST_BASELINE_SCANNER_VERSION,
        "experiment_id": experiment_id,
        "config_path": str(Path(config_path).resolve()),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "mode": mode.value,
        "ai_use_ids": AI_USE_IDS,
    }


def _summary_row(
    crate: Any,
    mode: ScanMode,
    source_scan: dict[str, Any] | None,
    geiger_record: Any,
    count_unsafe_record: Any,
    scan_status: ScanStatus,
) -> dict[str, Any]:
    metrics = source_scan.get("metrics", {}) if source_scan else {}
    return {
        "crate": crate.name,
        "revision": crate.pinned_reference,
        "mode": mode.value,
        "production_files": metrics.get("production_files", ""),
        "physical_loc": metrics.get("physical_loc", ""),
        "nonblank_loc": metrics.get("nonblank_loc", ""),
        "functions_total": metrics.get("functions_total", ""),
        "functions_safe": metrics.get("functions_safe", ""),
        "functions_unsafe_declared": metrics.get("functions_unsafe_declared", ""),
        "functions_with_unsafe": metrics.get("functions_with_unsafe", ""),
        "functions_unsafe_any": metrics.get("functions_unsafe_any", ""),
        "safe_function_pct": metrics.get("safe_function_pct", ""),
        "functions_without_explicit_unsafe_pct": metrics.get("functions_without_explicit_unsafe_pct", ""),
        "unsafe_blocks": metrics.get("unsafe_block_count", ""),
        "unsafe_loc_estimate": metrics.get("unsafe_loc_estimate", ""),
        "unsafe_loc_pct_estimate": metrics.get("unsafe_loc_pct_estimate", ""),
        "files_with_unsafe": metrics.get("files_with_unsafe", ""),
        "unsafe_file_pct": metrics.get("unsafe_file_pct", ""),
        "top5_unsafe_block_concentration_pct": metrics.get("top5_unsafe_block_concentration_pct", ""),
        "top5_unsafe_concentration_pct": metrics.get("top5_unsafe_loc_concentration_pct_estimate", ""),
        "geiger_status": getattr(geiger_record, "status", ToolStatus.SKIPPED).value,
        "count_unsafe_status": getattr(count_unsafe_record, "status", ToolStatus.SKIPPED).value,
        "scan_status": scan_status.value,
    }
