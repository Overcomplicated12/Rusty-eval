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
    scope_include: tuple[str, ...]
    scope_exclude: tuple[str, ...]
    config_path: Path


def _patterns(values: object, *, field: str) -> tuple[str, ...]:
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise ValueError(f"{field} must be an array of strings")
    return tuple(values)


def load_config(path: Path) -> InventoryConfig:
    """Load a V3 TOML config, resolving paths relative to its location."""
    path = path.resolve()
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    project = raw.get("project")
    repo_path = raw.get("repo_path")
    compile_commands_path = raw.get("compile_commands_path")
    scope = raw.get("scope", {})
    if not isinstance(project, str) or not project:
        raise ValueError("project must be a non-empty string")
    if not isinstance(repo_path, str) or not isinstance(compile_commands_path, str):
        raise ValueError("repo_path and compile_commands_path must be strings")
    if not isinstance(scope, dict):
        raise ValueError("scope must be a TOML table")
    base = path.parent
    return InventoryConfig(
        project=project,
        repo_path=(base / repo_path).resolve(),
        compile_commands_path=(base / compile_commands_path).resolve(),
        scope_include=_patterns(scope.get("include", []), field="scope.include"),
        scope_exclude=_patterns(scope.get("exclude", []), field="scope.exclude"),
        config_path=path,
    )
