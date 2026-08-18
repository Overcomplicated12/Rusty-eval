"""TOML-pattern scope filtering for normalized V3 records."""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
from collections.abc import Iterable

from .config import InventoryConfig
from .schema import FunctionRecord


@dataclass(frozen=True)
class ScopeExclusion:
    record: FunctionRecord
    reason: str
    pattern: str | None


@dataclass(frozen=True)
class ScopeResult:
    included: list[FunctionRecord]
    exclusions: list[ScopeExclusion]


def apply_scope(records: Iterable[FunctionRecord], config: InventoryConfig) -> ScopeResult:
    """Apply only configured include/exclude patterns to normalized file paths."""
    included: list[FunctionRecord] = []
    exclusions: list[ScopeExclusion] = []
    for record in records:
        include_match = next((pattern for pattern in config.scope_include if fnmatchcase(record.file, pattern)), None)
        exclude_match = next((pattern for pattern in config.scope_exclude if fnmatchcase(record.file, pattern)), None)
        if config.scope_include and include_match is None:
            exclusions.append(ScopeExclusion(record, "not_included", None))
        elif exclude_match is not None:
            exclusions.append(ScopeExclusion(record, "excluded", exclude_match))
        else:
            included.append(record)
    return ScopeResult(included, exclusions)
