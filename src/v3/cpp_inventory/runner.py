"""Translation-unit selection and Clang scanner invocation for V3 inventory."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import tempfile

from .config import InventoryConfig


@dataclass(frozen=True)
class ScanResult:
    """Raw scanner output and per-translation-unit execution failures."""

    translation_units_seen: int
    translation_units_parsed: int
    jsonl: str
    failures: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class TranslationUnit:
    """A source path paired with the compilation directory that defines its command."""

    source_path: Path
    compilation_directory: Path


def select_translation_units(compile_commands_path: Path, directory: Path | None = None) -> list[Path]:
    """Return unique compile-database source files below ``directory`` in database order."""
    return [unit.source_path for unit in _select_translation_units(compile_commands_path, directory)]


def _select_translation_units(
    compile_commands_path: Path, directory: Path | None
) -> list[TranslationUnit]:
    """Return selected source files together with their compile-command directories."""
    with compile_commands_path.open(encoding="utf-8") as handle:
        entries = json.load(handle)
    if not isinstance(entries, list):
        raise ValueError("compile_commands.json must contain an array")

    selected: list[TranslationUnit] = []
    seen: set[Path] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("each compile_commands.json entry must be an object")
        entry_directory = entry.get("directory")
        source_file = entry.get("file")
        if not isinstance(entry_directory, str) or not isinstance(source_file, str):
            raise ValueError(
                "each compile_commands.json entry requires string directory and file fields"
            )
        source_path = Path(source_file)
        if not source_path.is_absolute():
            source_path = Path(entry_directory) / source_path
        source_path = source_path.resolve()
        if directory is not None:
            try:
                source_path.relative_to(directory)
            except ValueError:
                continue
        if source_path not in seen:
            selected.append(
                TranslationUnit(
                    source_path=source_path,
                    compilation_directory=Path(entry_directory).resolve(),
                )
            )
            seen.add(source_path)
    return selected


def scan_directory(
    config: InventoryConfig, *, directory: Path | None, clang_inventory: Path
) -> ScanResult:
    """Run the scanner once per selected TU and retain successful JSONL and failures."""
    if directory is not None:
        directory = directory.resolve()
    if directory is not None and not directory.is_dir():
        raise ValueError(f"scan directory does not exist or is not a directory: {directory}")
    if not config.compile_commands_path.is_file():
        raise ValueError(f"compile_commands.json does not exist: {config.compile_commands_path}")
    if not clang_inventory.is_file():
        raise ValueError(f"clang inventory executable does not exist: {clang_inventory}")

    translation_units = _select_translation_units(config.compile_commands_path, directory)
    successful_jsonl: list[str] = []
    failures: list[dict[str, object]] = []

    with tempfile.TemporaryDirectory(prefix="rusty-eval-v3-clang-") as temporary:
        temporary_path = Path(temporary)
        for index, translation_unit in enumerate(translation_units):
            output_path = temporary_path / f"{index}.jsonl"
            command = [
                str(clang_inventory),
                f"--compilation-database={config.compile_commands_path}",
                f"--output={output_path}",
                f"--source-file={translation_unit.source_path}",
            ]
            try:
                completed = subprocess.run(
                    command,
                    cwd=translation_unit.compilation_directory,
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except OSError as error:
                failures.append(
                    {
                        "translation_unit": str(translation_unit.source_path),
                        "compilation_directory": str(translation_unit.compilation_directory),
                        "error": str(error),
                    }
                )
                continue
            if completed.returncode != 0:
                failures.append(
                    {
                        "translation_unit": str(translation_unit.source_path),
                        "compilation_directory": str(translation_unit.compilation_directory),
                        "returncode": completed.returncode,
                        "stdout": completed.stdout,
                        "stderr": completed.stderr,
                    }
                )
                continue
            if output_path.exists():
                successful_jsonl.append(output_path.read_text(encoding="utf-8"))

    return ScanResult(
        translation_units_seen=len(translation_units),
        translation_units_parsed=len(translation_units) - len(failures),
        jsonl="".join(successful_jsonl),
        failures=tuple(failures),
    )
