"""Stable data model for inventory methodology version 1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum


INVENTORY_METHODOLOGY_VERSION = 1


class Bucket(StrEnum):
    """The only classification buckets used by inventory methodology version 1."""

    TRIVIAL = "TRIVIAL"
    REFACTOR_THEN_DSL = "REFACTOR_THEN_DSL"
    NEEDS_TRANSPILER = "NEEDS_TRANSPILER"
    BOUNDARY = "BOUNDARY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class Declaration:
    """One source declaration and its lexical evidence and classification."""

    application: str
    application_commit: str
    file: str
    line: int
    end_line: int
    kind: str
    name: str
    loc: int
    features: dict[str, object]
    bucket: Bucket
    primary_reason: str
    secondary_reasons: list[str]
    confidence: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        result = asdict(self)
        result["bucket"] = self.bucket.value
        return result
