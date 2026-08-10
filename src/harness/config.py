"""Configuration loading and early validation for reproducible experiments."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when an experiment configuration is absent or malformed."""


def _required(table: dict[str, Any], key: str, label: str) -> Any:
    value = table.get(key)
    if value in (None, "", []):
        raise ConfigError(f"{label}.{key} is required")
    return value


def _text(table: dict[str, Any], key: str, label: str) -> str:
    value = _required(table, key, label)
    if not isinstance(value, str):
        raise ConfigError(f"{label}.{key} must be a non-empty string")
    return value


def _command(value: Any, label: str, *, required: bool = False) -> list[str] | None:
    if value is None:
        if required:
            raise ConfigError(f"{label} is required")
        return None
    if not isinstance(value, list) or not value or not all(isinstance(part, str) and part for part in value):
        raise ConfigError(f"{label} must be a non-empty array of command arguments")
    return list(value)


@dataclass(frozen=True)
class AttemptBudgets:
    max_total_attempts: int = 7
    transpiler_repairs: int = 2
    compile_repairs: int = 2
    test_repairs: int = 2

    @classmethod
    def from_dict(cls, value: dict[str, Any] | None) -> "AttemptBudgets":
        value = value or {}
        if not isinstance(value, dict):
            raise ConfigError("attempt_budgets must be a table")
        unknown = set(value) - set(cls.__dataclass_fields__)
        if unknown:
            raise ConfigError(f"unknown attempt budget fields: {', '.join(sorted(unknown))}")
        result = cls(**{key: value.get(key, getattr(cls(), key)) for key in cls.__dataclass_fields__})
        if any(not isinstance(item, int) or item < 0 for item in result.__dict__.values()):
            raise ConfigError("attempt budgets must be non-negative integers")
        if result.max_total_attempts < 1:
            raise ConfigError("attempt_budgets.max_total_attempts must be at least one")
        return result


@dataclass(frozen=True)
class EditPolicy:
    allowed_files: list[str]
    forbidden_patterns: list[str] = field(default_factory=lambda: [
        "tests/**", "**/tests/**", "benchmark/**", "benchmarks/**",
        "CMakeLists.txt", "**/CMakeLists.txt", "Makefile", "**/Makefile",
        "meson.build", "**/meson.build", "generated/**", "**/generated/**", "*.generated.*",
    ])


@dataclass(frozen=True)
class HarnessConfig:
    application_name: str
    application_repo: Path
    application_commit: str
    source_roots: list[str]
    rustycpp_repo: Path
    rustycpp_commit: str
    rustycpp_command: list[str]
    build_command: list[str]
    targeted_test_command: list[str] | None
    full_test_command: list[str] | None
    benchmark_command: list[str] | None
    workspace_root: Path
    attempt_budgets: AttemptBudgets
    edit_policy: EditPolicy

    def to_dict(self) -> dict[str, Any]:
        return {
            "application": {"name": self.application_name, "repo": str(self.application_repo), "commit": self.application_commit,
                            "source_roots": self.source_roots},
            "rustycpp": {"repo": str(self.rustycpp_repo), "commit": self.rustycpp_commit, "command": self.rustycpp_command},
            "commands": {"build": self.build_command, "targeted_test": self.targeted_test_command,
                         "full_test": self.full_test_command, "benchmark": self.benchmark_command},
            "workspace_root": str(self.workspace_root), "attempt_budgets": self.attempt_budgets.__dict__,
            "edit_policy": {"allowed_files": self.edit_policy.allowed_files, "forbidden_patterns": self.edit_policy.forbidden_patterns},
        }


def load_config(path: str | Path) -> HarnessConfig:
    """Load a TOML config without touching a target repository."""
    config_path = Path(path)
    try:
        raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ConfigError(f"configuration not found: {config_path}") from error
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"invalid TOML in {config_path}: {error}") from error
    for table_name in ("application", "rustycpp", "commands", "edit_policy"):
        if not isinstance(raw.get(table_name), dict):
            raise ConfigError(f"{table_name} must be a table")
    application, rustycpp, commands, policy = (raw[name] for name in ("application", "rustycpp", "commands", "edit_policy"))
    roots = _required(application, "source_roots", "application")
    allowed = _required(policy, "allowed_files", "edit_policy")
    if not isinstance(roots, list) or not all(isinstance(item, str) and item for item in roots):
        raise ConfigError("application.source_roots must be a non-empty string array")
    if not isinstance(allowed, list) or not all(isinstance(item, str) and item for item in allowed):
        raise ConfigError("edit_policy.allowed_files must be a non-empty string array")
    forbidden = policy.get("forbidden_patterns", EditPolicy([]).forbidden_patterns)
    if not isinstance(forbidden, list) or not all(isinstance(item, str) and item for item in forbidden):
        raise ConfigError("edit_policy.forbidden_patterns must be a string array")
    workspace_root = raw.get("workspace_root")
    if not isinstance(workspace_root, str) or not workspace_root:
        raise ConfigError("workspace_root is required")
    return HarnessConfig(
        application_name=_text(application, "name", "application"),
        application_repo=Path(_text(application, "repo", "application")),
        application_commit=_text(application, "commit", "application"),
        source_roots=list(roots),
        rustycpp_repo=Path(_text(rustycpp, "repo", "rustycpp")),
        rustycpp_commit=_text(rustycpp, "commit", "rustycpp"),
        rustycpp_command=_command(rustycpp.get("command"), "rustycpp.command", required=True) or [],
        build_command=_command(commands.get("build"), "commands.build", required=True) or [],
        targeted_test_command=_command(commands.get("targeted_test"), "commands.targeted_test"),
        full_test_command=_command(commands.get("full_test"), "commands.full_test"),
        benchmark_command=_command(commands.get("benchmark"), "commands.benchmark"),
        workspace_root=Path(workspace_root),
        attempt_budgets=AttemptBudgets.from_dict(raw.get("attempt_budgets")),
        edit_policy=EditPolicy(list(allowed), list(forbidden)),
    )
