"""Explicit migration-unit selection; automatic sampling is intentionally absent."""

from __future__ import annotations

import json
from pathlib import Path

from .models import MigrationUnit


class SelectionError(ValueError):
    pass


def unit_from_dict(value: dict[str, object]) -> MigrationUnit:
    required = ("id", "application", "application_commit", "file", "start_line", "end_line", "allowed_files")
    missing = [key for key in required if key not in value]
    if missing:
        raise SelectionError(f"migration unit missing required fields: {', '.join(missing)}")
    try:
        unit = MigrationUnit(**value)  # type: ignore[arg-type]
    except TypeError as error:
        raise SelectionError(str(error)) from error
    if unit.start_line < 1 or unit.end_line < unit.start_line:
        raise SelectionError("migration unit line range is invalid")
    if not unit.allowed_files:
        raise SelectionError("migration unit must declare allowed_files")
    return unit


def load_selection(path: str | Path) -> list[MigrationUnit]:
    """Load explicitly listed units from JSON; no sampling occurs here."""
    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SelectionError(f"selection not found: {source}") from error
    except json.JSONDecodeError as error:
        raise SelectionError(f"invalid JSON in {source}: {error}") from error
    records = payload.get("units") if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise SelectionError("selection must be a list or an object with a units list")
    units = [unit_from_dict(item) for item in records if isinstance(item, dict)]
    if len(units) != len(records):
        raise SelectionError("every selection entry must be an object")
    ids = [unit.id for unit in units]
    if len(ids) != len(set(ids)):
        raise SelectionError("migration-unit ids must be unique")
    return units


def find_unit(path: str | Path, unit_id: str) -> MigrationUnit:
    for unit in load_selection(path):
        if unit.id == unit_id:
            return unit
    raise SelectionError(f"migration unit not found: {unit_id}")
