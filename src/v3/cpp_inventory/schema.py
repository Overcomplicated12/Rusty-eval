"""Minimal data shapes for future parser-backed function discovery."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FunctionRecord:
    """One future Clang-discovered function declaration or definition."""

    id: str
    usr: str
    qualified_name: str
    kind: str
    file: str
    start_line: int
    end_line: int
    is_definition: bool
    is_implicit: bool
    is_template: bool
    is_template_instantiation: bool
    is_lambda: bool
