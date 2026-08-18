"""Cross-translation-unit function deduplication for V3."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import replace

from .schema import FunctionRecord


def deduplicate_functions(records: Iterable[FunctionRecord]) -> list[FunctionRecord]:
    """Deduplicate by USR, falling back to normalized source location identity."""
    groups: dict[str, list[FunctionRecord]] = defaultdict(list)
    for record in records:
        identity = (
            f"usr:{record.usr}"
            if record.usr
            else f"fallback:{record.file}:{record.start_offset}:{record.qualified_name}:{record.kind}"
        )
        groups[identity].append(record)
    deduplicated: list[FunctionRecord] = []
    for identity, observations in groups.items():
        canonical = observations[0]
        translation_units = tuple(sorted({record.translation_unit for record in observations}))
        deduplicated.append(
            replace(
                canonical,
                identity=identity,
                observation_count=len(observations),
                translation_units=translation_units,
            )
        )
    return deduplicated
