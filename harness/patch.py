"""Independent, conservative changed-file validation for agent proposals."""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import PurePosixPath

from .config import EditPolicy


@dataclass(frozen=True)
class PatchValidation:
    accepted: bool
    changed_files: list[str]
    rejected_files: list[str]
    reason: str | None = None


def validate_changed_files(changed_files: list[str], policy: EditPolicy) -> PatchValidation:
    normalized = sorted({PurePosixPath(path).as_posix() for path in changed_files})
    rejected: list[str] = []
    for filename in normalized:
        path = PurePosixPath(filename)
        malformed = path.is_absolute() or ".." in path.parts
        allowed = any(fnmatch(filename, pattern) for pattern in policy.allowed_files)
        forbidden = any(fnmatch(filename, pattern) for pattern in policy.forbidden_patterns)
        if malformed or not allowed or forbidden:
            rejected.append(filename)
    if rejected:
        return PatchValidation(False, normalized, rejected, "unauthorized changed files")
    return PatchValidation(True, normalized, [])
