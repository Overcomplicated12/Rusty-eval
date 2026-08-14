"""Placeholder production-scope filtering for V3 parser results."""

from __future__ import annotations

from collections.abc import Iterable

from .config import InventoryConfig
from .schema import FunctionRecord


def apply_scope(records: Iterable[FunctionRecord], config: InventoryConfig) -> list[FunctionRecord]:
    """Return records unchanged until V3 scope semantics are implemented."""
    del config
    return list(records)
