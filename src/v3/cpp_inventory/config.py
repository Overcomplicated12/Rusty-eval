"""TOML configuration for the isolated V3 C++ inventory command."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class InventoryConfig:
    project: str
    repo_path: Path
    compile_commands_path: Path
    include_paths: tuple[Path, ...]
    exclude_paths: tuple[Path, ...]
    config_path: Path


def _paths(values: object, *, base: Path, field: str) -> tuple[Path, ...]:
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise ValueError(f"{field} must be an array of strings")
    return tuple((base / value).resolve() for value in values)


def load_config(path: Path) -> InventoryConfig:
    """Load a V3 TOML config, resolving paths relative to its location."""
    path = path.resolve()
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    project = raw.get("project")
    repo_path = raw.get("repo_path")
    compile_commands_path = raw.get("compile_commands_path")
    if not isinstance(project, str) or not project:
        raise ValueError("project must be a non-empty string")
    if not isinstance(repo_path, str) or not isinstance(compile_commands_path, str):
        raise ValueError("repo_path and compile_commands_path must be strings")
    base = path.parent
    return InventoryConfig(
        project=project,
        repo_path=(base / repo_path).resolve(),
        compile_commands_path=(base / compile_commands_path).resolve(),
        include_paths=_paths(raw.get("include_paths", []), base=base, field="include_paths"),
        exclude_paths=_paths(raw.get("exclude_paths", []), base=base, field="exclude_paths"),
        config_path=path,
    )
