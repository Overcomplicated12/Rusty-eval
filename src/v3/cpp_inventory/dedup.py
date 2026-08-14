"""Placeholder declaration/definition deduplication for V3."""

from __future__ import annotations

from collections.abc import Iterable

from .schema import FunctionRecord


def deduplicate_functions(records: Iterable[FunctionRecord]) -> list[FunctionRecord]:
    """Return records unchanged until USR-based deduplication is implemented."""
    return list(records)
