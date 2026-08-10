"""Write append-only per-experiment artifacts under results/<app>/<id>."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import ExperimentResult, MigrationUnit


class ReportingError(RuntimeError):
    pass


class ExperimentReporter:
    def __init__(self, results_root: str | Path, application: str, experiment_id: str) -> None:
        self.root = Path(results_root) / application / experiment_id

    def create(self) -> Path:
        if self.root.exists():
            raise ReportingError(f"refusing to overwrite an existing experiment: {self.root}")
        for directory in (self.root, self.root / "baseline", self.root / "attempts", self.root / "human", self.root / "final"):
            directory.mkdir(parents=True, exist_ok=True)
        return self.root

    def _write_json(self, relative: str, data: dict[str, Any]) -> Path:
        destination = self.root / relative
        if destination.exists():
            raise ReportingError(f"refusing to overwrite artifact: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return destination

    def write_manifest(self, manifest: dict[str, Any]) -> Path:
        return self._write_json("manifest.json", manifest)

    def write_environment(self, environment: dict[str, Any]) -> Path:
        return self._write_json("environment.json", environment)

    def write_unit(self, unit: MigrationUnit) -> Path:
        return self._write_json("unit.json", unit.to_dict())

    def write_attempt(self, number: int, artifact: dict[str, Any]) -> Path:
        return self._write_json(f"attempts/{number:03d}/attempt.json", artifact)

    def write_result(self, result: ExperimentResult) -> Path:
        return self._write_json("result.json", result.to_dict())
