"""Reviewable, deterministic classification rules for inventory methodology v1.

The ordering is deliberate: strong source-boundary evidence takes priority;
then known-but-unverified transpiler needs; then localized mechanical work.
Feature detection is independent so later methodology versions can reclassify a
saved raw inventory without rescanning source.
"""

from __future__ import annotations

from .models import Bucket


def classify(features: dict[str, object]) -> tuple[Bucket, str, list[str], str]:
    """Classify visible evidence without application-specific exceptions."""
    present = {name for name, value in features.items() if value is True}

    boundary = [
        name
        for name in ("generated_source", "third_party", "extern_or_abi_boundary")
        if name in present
    ]
    if boundary:
        return Bucket.BOUNDARY, boundary[0], boundary[1:], "high"

    # These forms require a RustyCpp capability that v1 intentionally does not
    # claim to support. A single ordinary pointer is not in this list.
    transpiler = [
        name
        for name in ("function_pointer", "callback", "union", "variadic", "va_list", "setjmp", "longjmp")
        if name in present
    ]
    if transpiler:
        return Bucket.NEEDS_TRANSPILER, transpiler[0], transpiler[1:], "medium"

    # Macro-generated declarations cannot be localized reliably by this lexical
    # scanner, so v1 declines to make a confident structural classification.
    if "macro_generated_declaration" in present:
        return Bucket.UNKNOWN, "macro_generated_declaration", [], "low"

    refactor = [
        name
        for name in (
            "pointer_arithmetic", "malloc", "calloc", "realloc", "free", "memcpy", "memmove",
            "memset", "flexible_array", "bitfield", "goto", "static_local", "mutable_global",
        )
        if name in present
    ]
    if refactor:
        return Bucket.REFACTOR_THEN_DSL, refactor[0], refactor[1:], "medium"

    # Pointers, arrays, conditionals, and ordinary macros are retained as
    # evidence but do not alone establish a blocker or boundary.
    secondary = sorted(present)
    return Bucket.TRIVIAL, "no_significant_detected_blocker", secondary, "medium"
