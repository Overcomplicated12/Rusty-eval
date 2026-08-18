"""Path normalization for V3 function observations."""

from __future__ import annotations

from pathlib import Path

from .schema import FunctionRecord, RawFunctionRecord


def normalize_path(path: str, repo_path: Path) -> str:
    """Return a stable repository-relative POSIX path when possible."""
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(repo_path).as_posix()
    except ValueError:
        return resolved.as_posix()


def normalize_record(record: RawFunctionRecord, repo_path: Path) -> FunctionRecord:
    """Normalize paths only; scope filtering and identity selection happen later."""
    file = normalize_path(record.file, repo_path)
    translation_unit = normalize_path(record.translation_unit, repo_path)
    payload = record.to_dict()
    payload.update(
        file=file,
        translation_unit=translation_unit,
        raw_file=record.file,
        raw_translation_unit=record.translation_unit,
        translation_units=(translation_unit,),
    )
    return FunctionRecord(**payload)


def normalize_records(records: list[RawFunctionRecord], repo_path: Path) -> list[FunctionRecord]:
    return [normalize_record(record, repo_path) for record in records]
