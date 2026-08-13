"""Append-only result writing and summary reporting for Rust baseline scans."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import CrateSpec, ScanMode


class ReportError(RuntimeError):
    """Raised when a result directory would be overwritten."""


SUMMARY_COLUMNS = [
    "crate",
    "revision",
    "mode",
    "production_files",
    "physical_loc",
    "nonblank_loc",
    "functions_total",
    "functions_safe",
    "functions_unsafe_declared",
    "functions_with_unsafe",
    "safe_function_pct",
    "functions_without_explicit_unsafe_pct",
    "unsafe_blocks",
    "unsafe_loc_estimate",
    "unsafe_loc_pct_estimate",
    "files_with_unsafe",
    "unsafe_file_pct",
    "top5_unsafe_block_concentration_pct",
    "top5_unsafe_concentration_pct",
    "geiger_status",
    "count_unsafe_status",
    "scan_status",
]


class BaselineReporter:
    def __init__(self, results_root: Path, experiment_id: str) -> None:
        self.root = results_root / experiment_id

    def create(self) -> Path:
        if self.root.exists():
            raise ReportError(f"refusing to overwrite an existing experiment: {self.root}")
        self.root.mkdir(parents=True, exist_ok=False)
        return self.root

    def write_root_metadata(self, metadata: dict[str, Any]) -> Path:
        return self._write_json(self.root / "metadata.json", metadata)

    def write_crate_metadata(self, crate: CrateSpec, checkout: dict[str, Any]) -> Path:
        return self._write_json(
            self.root / crate.name / "metadata.json",
            {
                "crate": crate.to_dict(),
                "checkout": checkout,
            },
        )

    def write_mode_artifact(self, crate_name: str, mode: ScanMode, name: str, data: dict[str, Any]) -> Path:
        return self._write_json(self.root / crate_name / mode.value / name, data)

    def ensure_stdout_dir(self, crate_name: str, mode: ScanMode) -> Path:
        directory = self.root / crate_name / mode.value / "stdout"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def artifact_exists(self, crate_name: str, mode: ScanMode, name: str) -> bool:
        return (self.root / crate_name / mode.value / name).exists()

    def _write_json(self, path: Path, data: dict[str, Any]) -> Path:
        if path.exists():
            raise ReportError(f"refusing to overwrite artifact: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path


def create_experiment_id(now: datetime | None = None) -> str:
    now = now or datetime.now().astimezone()
    return now.strftime("baseline-%Y-%m-%dT%H%M%S%z")


def collect_results(results_root: Path) -> list[dict[str, Any]]:
    result_files = sorted(results_root.glob("*/*/result.json"))
    rows: list[dict[str, Any]] = []
    for result_file in result_files:
        data = json.loads(result_file.read_text(encoding="utf-8"))
        row = {column: data.get("summary", {}).get(column, "") for column in SUMMARY_COLUMNS}
        row["crate"] = data.get("crate_name", row["crate"])
        row["revision"] = data.get("revision", row["revision"])
        row["mode"] = data.get("mode", row["mode"])
        rows.append(row)
    return rows


def write_summary_files(results_root: Path, root_metadata: dict[str, Any]) -> None:
    rows = collect_results(results_root)
    summary_csv = results_root / "summary.csv"
    summary_md = results_root / "summary.md"
    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Rust Baseline Summary",
        "",
        f"- Experiment ID: `{root_metadata['experiment_id']}`",
        f"- Generated at: `{root_metadata['generated_at']}`",
        f"- Mode: `{root_metadata['mode']}`",
        "",
        "| " + " | ".join(SUMMARY_COLUMNS) + " |",
        "| " + " | ".join("---" for _ in SUMMARY_COLUMNS) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in SUMMARY_COLUMNS) + " |")
    summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
