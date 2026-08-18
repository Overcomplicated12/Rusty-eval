"""Coverage and denominator accounting for interpreted V3 inventory records."""

from __future__ import annotations

from collections import Counter

from .schema import FunctionRecord
from .scope import ScopeResult


def denominator_category(record: FunctionRecord) -> str:
    if record.is_template_instantiation:
        return "implicit_template_instantiation"
    if record.is_lambda:
        return "lambda"
    if record.is_explicit_specialization:
        return "explicit_specialization"
    return "primary"


def calculate_coverage(
    *, translation_units_seen: int, translation_units_parsed: int,
    raw_records: list[FunctionRecord], scope_result: ScopeResult,
    deduplicated_records: list[FunctionRecord],
) -> dict[str, object]:
    """Return auditable TU and record-reduction counts."""
    categories = Counter(denominator_category(record) for record in deduplicated_records)
    return {
        "translation_units_seen": translation_units_seen,
        "translation_units_parsed": translation_units_parsed,
        "translation_units_failed": translation_units_seen - translation_units_parsed,
        "raw_observations": len(raw_records),
        "scope_included_observations": len(scope_result.included),
        "scope_excluded_observations": len(scope_result.exclusions),
        "deduplicated_functions": len(deduplicated_records),
        "deduplication_reduction": len(scope_result.included) - len(deduplicated_records),
        "primary_denominator": categories["primary"],
        "implicit_template_instantiations": categories["implicit_template_instantiation"],
        "lambdas": categories["lambda"],
        "explicit_specializations": categories["explicit_specialization"],
    }
