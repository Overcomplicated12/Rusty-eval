"""Raw and normalized V3 Clang function-record schemas."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from typing import Any, Mapping


def _string(record: Mapping[str, object], field: str) -> str:
    value = record.get(field, "")
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def _integer(record: Mapping[str, object], field: str) -> int:
    value = record.get(field, 0)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{field} must be an integer")
    return value


def _boolean(record: Mapping[str, object], field: str) -> bool:
    value = record.get(field, False)
    if not isinstance(value, bool):
        raise ValueError(f"{field} must be a boolean")
    return value


@dataclass(frozen=True)
class RawFunctionRecord:
    """One unfiltered function observation emitted by ``clang_inventory``."""

    usr: str
    translation_unit: str
    name: str
    qualified_name: str
    kind: str
    file: str
    start_line: int
    start_column: int
    start_offset: int
    end_line: int
    end_column: int
    end_offset: int
    is_definition: bool
    is_implicit: bool
    is_template: bool
    is_template_instantiation: bool
    is_explicit_specialization: bool
    is_lambda: bool
    is_macro_expansion: bool
    is_virtual: bool
    is_static_method: bool
    parent_type: str
    is_variadic: bool
    is_constexpr: bool
    is_inline: bool

    @classmethod
    def from_mapping(cls, record: Mapping[str, object]) -> RawFunctionRecord:
        return cls(
            usr=_string(record, "usr"), translation_unit=_string(record, "translation_unit"),
            name=_string(record, "name"), qualified_name=_string(record, "qualified_name"),
            kind=_string(record, "kind"), file=_string(record, "file"),
            start_line=_integer(record, "start_line"), start_column=_integer(record, "start_column"),
            start_offset=_integer(record, "start_offset"), end_line=_integer(record, "end_line"),
            end_column=_integer(record, "end_column"), end_offset=_integer(record, "end_offset"),
            is_definition=_boolean(record, "is_definition"), is_implicit=_boolean(record, "is_implicit"),
            is_template=_boolean(record, "is_template"),
            is_template_instantiation=_boolean(record, "is_template_instantiation"),
            is_explicit_specialization=_boolean(record, "is_explicit_specialization"),
            is_lambda=_boolean(record, "is_lambda"),
            is_macro_expansion=_boolean(record, "is_macro_expansion"),
            is_virtual=_boolean(record, "is_virtual"),
            is_static_method=_boolean(record, "is_static_method"), parent_type=_string(record, "parent_type"),
            is_variadic=_boolean(record, "is_variadic"), is_constexpr=_boolean(record, "is_constexpr"),
            is_inline=_boolean(record, "is_inline"),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FunctionRecord(RawFunctionRecord):
    """A normalized, deduplicated function record with observation provenance."""

    raw_file: str = ""
    raw_translation_unit: str = ""
    identity: str = ""
    observation_count: int = 1
    translation_units: tuple[str, ...] = ()

    def with_observations(self, *, observation_count: int, translation_units: tuple[str, ...]) -> FunctionRecord:
        return replace(self, observation_count=observation_count, translation_units=translation_units)

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, Any] = asdict(self)
        payload["translation_units"] = list(self.translation_units)
        return payload
