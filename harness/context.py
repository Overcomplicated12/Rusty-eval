"""Deterministic source-window context generation, without AST interpretation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import MigrationUnit


@dataclass(frozen=True)
class SourceContext:
    unit_id: str
    file: str
    start_line: int
    end_line: int
    target_start_line: int
    target_end_line: int
    text: str
    metadata: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return self.__dict__.copy()


def build_context(workspace: str | Path, unit: MigrationUnit, surrounding_lines: int = 20) -> SourceContext:
    if surrounding_lines < 0:
        raise ValueError("surrounding_lines must not be negative")
    source = Path(workspace) / unit.file
    lines = source.read_text(encoding="utf-8").splitlines(keepends=True)
    start = max(1, unit.start_line - surrounding_lines)
    end = min(len(lines), unit.end_line + surrounding_lines)
    rendered = "".join(f"{line_number:>6}: {lines[line_number - 1]}" for line_number in range(start, end + 1))
    return SourceContext(unit.id, unit.file, start, end, unit.start_line, unit.end_line, rendered, dict(unit.metadata))
