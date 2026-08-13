"""Configuration loading and validation for Rust baseline scans."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any

from .models import BaselineConfig, CrateSpec, ToolCommands


class ConfigError(ValueError):
    """Raised when a baseline scan configuration is absent or malformed."""


_EXACT_VERSION = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z._-]+)?$")
_PLACEHOLDER_PINS = {"", "<PINNED COMMIT>", "<PIN EXACT VERSION>", "REQUIRED", "TODO", "TBD"}


def _required_string(table: dict[str, Any], key: str, label: str) -> str:
    value = table.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{label}.{key} must be a non-empty string")
    return value.strip()


def _string_list(value: Any, label: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        raise ConfigError(f"{label} must be an array of non-empty strings")
    return [item.strip() for item in value]


def _is_placeholder_pin(value: str | None) -> bool:
    return value is None or value.strip() in _PLACEHOLDER_PINS


def _load_crate(entry: Any, index: int) -> CrateSpec:
    if not isinstance(entry, dict):
        raise ConfigError(f"crate[{index}] must be a table")
    name = _required_string(entry, "name", f"crate[{index}]")
    package = _required_string(entry, "package", f"crate[{index}]")
    repo = entry.get("repo")
    rev = entry.get("rev")
    version = entry.get("version")
    if repo is not None and (not isinstance(repo, str) or not repo.strip()):
        raise ConfigError(f"crate[{index}].repo must be a non-empty string when present")
    if rev is not None and (not isinstance(rev, str) or not rev.strip()):
        raise ConfigError(f"crate[{index}].rev must be a non-empty string when present")
    if version is not None and (not isinstance(version, str) or not version.strip()):
        raise ConfigError(f"crate[{index}].version must be a non-empty string when present")
    if repo and version:
        raise ConfigError(f"crate[{index}] may not set both repo/rev and version")
    if repo and _is_placeholder_pin(rev):
        raise ConfigError(f"crate[{index}] must set a pinned rev for repo-based scans")
    if not repo and _is_placeholder_pin(version):
        raise ConfigError(f"crate[{index}] must set an exact version when repo is omitted")
    if not repo and version and not _EXACT_VERSION.match(version.strip()):
        raise ConfigError(f"crate[{index}].version must be an exact version, not a range")
    features = _string_list(entry.get("features"), f"crate[{index}].features")
    return CrateSpec(
        name=name,
        package=package,
        repo=repo.strip() if isinstance(repo, str) else None,
        rev=rev.strip() if isinstance(rev, str) else None,
        version=version.strip() if isinstance(version, str) else None,
        features=features,
    )


def load_config(path: str | Path) -> BaselineConfig:
    config_path = Path(path)
    try:
        raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ConfigError(f"configuration not found: {config_path}") from error
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"invalid TOML in {config_path}: {error}") from error
    workspace_root = raw.get("workspace_root", ".rust-baseline-work")
    results_root = raw.get("results_root", "results/rust-baseline")
    if not isinstance(workspace_root, str) or not workspace_root.strip():
        raise ConfigError("workspace_root must be a non-empty string")
    if not isinstance(results_root, str) or not results_root.strip():
        raise ConfigError("results_root must be a non-empty string")
    crate_entries = raw.get("crate")
    if not isinstance(crate_entries, list) or not crate_entries:
        raise ConfigError("at least one [[crate]] entry is required")
    crates = [_load_crate(entry, index) for index, entry in enumerate(crate_entries)]
    names = [crate.name for crate in crates]
    if len(names) != len(set(names)):
        raise ConfigError("crate names must be unique")
    tools_raw = raw.get("tools", {})
    if not isinstance(tools_raw, dict):
        raise ConfigError("tools must be a table when present")
    tools = ToolCommands(
        cargo=str(tools_raw.get("cargo", "cargo")),
        git=str(tools_raw.get("git", "git")),
        rustc=str(tools_raw.get("rustc", "rustc")),
    )
    base_dir = config_path.parent
    return BaselineConfig(
        workspace_root=(base_dir / workspace_root).resolve(),
        results_root=(base_dir / results_root).resolve(),
        crates=crates,
        tools=tools,
    )


def find_crate(config: BaselineConfig, crate_name: str) -> CrateSpec:
    for crate in config.crates:
        if crate.name == crate_name:
            return crate
    raise ConfigError(f"crate not found in config: {crate_name}")
