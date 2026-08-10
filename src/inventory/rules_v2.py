"""Ordered, reviewable classification rules for inventory methodology version 2."""

from __future__ import annotations

from .models import Bucket


def classify(features: dict[str, object]) -> tuple[Bucket, str, list[str], str]:
    """Classify v2 evidence without treating linkage alone as a boundary."""
    present = {name for name, value in features.items() if value is True}
    boundary = [name for name in ("generated_source", "third_party", "explicit_abi_boundary") if name in present]
    if boundary:
        return Bucket.BOUNDARY, boundary[0], boundary[1:], "high"
    if "lexical_ambiguity" in present or "macro_generated_declaration" in present:
        reason = "macro_generated_declaration" if "macro_generated_declaration" in present else "lexical_ambiguity"
        return Bucket.UNKNOWN, reason, sorted(present - {reason}), "low"
    transpiler = [name for name in ("function_pointer", "callback", "union", "variadic", "va_list", "setjmp", "longjmp") if name in present]
    if transpiler:
        return Bucket.NEEDS_TRANSPILER, transpiler[0], transpiler[1:], "medium"
    refactor = [name for name in ("pointer_arithmetic", "malloc", "calloc", "realloc", "free", "memcpy", "memmove", "memset", "flexible_array", "bitfield", "goto", "static_local", "mutable_global") if name in present]
    if refactor:
        return Bucket.REFACTOR_THEN_DSL, refactor[0], refactor[1:], "medium"
    return Bucket.TRIVIAL, "no_significant_detected_blocker", sorted(present), "medium"
