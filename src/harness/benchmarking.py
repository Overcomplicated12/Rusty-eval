"""Benchmark command interface; the dry-run state machine never invokes it."""

from __future__ import annotations

from pathlib import Path

from .build import run_build
from .models import BenchmarkResult


def run_benchmark(command: list[str], workspace: str | Path, *, label: str, baseline: bool = False) -> BenchmarkResult:
    return BenchmarkResult(run_build(command, workspace), label, baseline)
