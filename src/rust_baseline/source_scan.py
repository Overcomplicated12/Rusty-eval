"""Local lexical scanning for auditable Rust source metrics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import FileSummary, SourceMetrics

_EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "target",
    "tests",
    "benches",
    "examples",
    "example",
    "fuzz",
    "fuzzers",
    "vendor",
    "vendors",
    "vendored",
}

_EXCLUDED_FILE_NAMES = {"build.rs"}
_EXCLUDED_SUFFIXES = (".generated.rs",)


@dataclass(frozen=True)
class Token:
    text: str
    line: int
    kind: str
    offset: int


@dataclass(frozen=True)
class FunctionContext:
    brace_depth: int
    has_unsafe_block: bool = False


def is_production_rust_file(path: Path) -> bool:
    if path.suffix != ".rs":
        return False
    if path.name in _EXCLUDED_FILE_NAMES:
        return False
    if path.name.endswith(_EXCLUDED_SUFFIXES):
        return False
    if any(part in _EXCLUDED_DIRS for part in path.parts):
        return False
    return True


def iter_production_rust_files(root: Path, source_roots: list[Path] | None = None) -> list[Path]:
    roots = source_roots or [root]
    files = {
        path
        for source_root in roots
        for path in source_root.rglob("*.rs")
        if is_production_rust_file(path.relative_to(root))
    }
    return sorted(files)


def scan_source_tree(root: Path, source_roots: list[Path] | None = None) -> dict[str, object]:
    files = iter_production_rust_files(root, source_roots)
    file_summaries = [scan_rust_file(root, path) for path in files]
    result = build_source_scan(root, file_summaries)
    result["production_source_roots"] = [str(path) for path in (source_roots or [root])]
    return result


def build_source_scan(root: Path, file_summaries: list[FileSummary]) -> dict[str, object]:
    production_files = len(file_summaries)
    physical_loc = sum(item.physical_loc for item in file_summaries)
    nonblank_loc = sum(item.nonblank_loc for item in file_summaries)
    functions_total = sum(item.functions_total for item in file_summaries)
    functions_safe = sum(item.functions_safe for item in file_summaries)
    functions_unsafe_declared = sum(item.functions_unsafe_declared for item in file_summaries)
    functions_with_unsafe = sum(item.functions_with_unsafe for item in file_summaries)
    functions_unsafe_any = sum(item.functions_unsafe_any for item in file_summaries)
    functions_with_any_explicit_unsafe = sum(item.functions_with_any_explicit_unsafe for item in file_summaries)
    functions_without_explicit_unsafe = sum(item.functions_without_explicit_unsafe for item in file_summaries)
    unsafe_trait_count = sum(item.unsafe_traits for item in file_summaries)
    unsafe_impl_count = sum(item.unsafe_impls for item in file_summaries)
    unsafe_block_count = sum(item.unsafe_blocks for item in file_summaries)
    unsafe_loc_estimate = sum(item.unsafe_loc_estimate for item in file_summaries)
    files_with_unsafe = sum(1 for item in file_summaries if _file_has_unsafe(item))
    sorted_unsafe = sorted(
        file_summaries,
        key=lambda item: (
            item.unsafe_blocks + item.functions_unsafe_declared + item.unsafe_traits + item.unsafe_impls,
            item.unsafe_loc_estimate,
            item.path,
        ),
        reverse=True,
    )
    top10 = [item.to_dict() for item in sorted_unsafe[:10] if _file_has_unsafe(item)]
    top5 = sorted_unsafe[:5]
    metrics = SourceMetrics(
        production_files=production_files,
        physical_loc=physical_loc,
        nonblank_loc=nonblank_loc,
        functions_total=functions_total,
        functions_safe=functions_safe,
        functions_unsafe_declared=functions_unsafe_declared,
        functions_with_unsafe=functions_with_unsafe,
        functions_unsafe_any=functions_unsafe_any,
        functions_with_any_explicit_unsafe=functions_unsafe_any,
        functions_without_explicit_unsafe=functions_without_explicit_unsafe,
        safe_function_pct=_pct(functions_safe, functions_total),
        functions_without_explicit_unsafe_pct=_pct(functions_without_explicit_unsafe, functions_total),
        unsafe_fn_count=functions_unsafe_declared,
        unsafe_trait_count=unsafe_trait_count,
        unsafe_impl_count=unsafe_impl_count,
        unsafe_block_count=unsafe_block_count,
        unsafe_loc_estimate=unsafe_loc_estimate,
        unsafe_loc_pct_estimate=_pct(unsafe_loc_estimate, physical_loc),
        files_with_unsafe=files_with_unsafe,
        unsafe_file_pct=_pct(files_with_unsafe, production_files),
        top5_unsafe_block_concentration_pct=_pct(sum(item.unsafe_blocks for item in top5), unsafe_block_count),
        top5_unsafe_loc_concentration_pct_estimate=_pct(
            sum(item.unsafe_loc_estimate for item in top5),
            unsafe_loc_estimate,
        ),
    )
    return {
        "root": str(root),
        "metrics": metrics.to_dict(),
        "files": [item.to_dict() for item in file_summaries],
        "unsafe_counts_per_file": {
            item.path: {
                "unsafe_fn_count": item.functions_unsafe_declared,
                "unsafe_trait_count": item.unsafe_traits,
                "unsafe_impl_count": item.unsafe_impls,
                "unsafe_block_count": item.unsafe_blocks,
                "unsafe_loc_estimate": item.unsafe_loc_estimate,
            }
            for item in file_summaries
            if _file_has_unsafe(item)
        },
        "top_unsafe_files": top10,
        "unsafe_loc_estimate_basis": "physical source lines overlapped by explicit unsafe blocks after comment/string stripping",
        "excluded_path_components": sorted(_EXCLUDED_DIRS),
        "excluded_file_names": sorted(_EXCLUDED_FILE_NAMES),
        "excluded_suffixes": list(_EXCLUDED_SUFFIXES),
    }


def scan_rust_file(root: Path, path: Path) -> FileSummary:
    text = path.read_text(encoding="utf-8")
    sanitized = strip_non_code(text)
    tokens = tokenize(sanitized)
    brace_map = build_brace_map(tokens)
    excluded_token_indexes = _test_only_token_indexes(tokens, brace_map)
    excluded_lines = {tokens[index].line for index in excluded_token_indexes}
    physical_loc = sum(1 for line_number, _ in enumerate(text.splitlines(), start=1) if line_number not in excluded_lines)
    nonblank_loc = sum(
        1
        for line_number, line in enumerate(text.splitlines(), start=1)
        if line.strip() and line_number not in excluded_lines
    )

    functions_total = 0
    functions_unsafe_declared = 0
    functions_with_unsafe = 0
    functions_declared_unsafe_with_block = 0
    unsafe_trait_count = 0
    unsafe_impl_count = 0
    unsafe_blocks = 0
    unsafe_lines: set[int] = set()
    unsafe_block_openings: list[int] = []

    pending_function: dict[str, int | bool] | None = None
    function_stack: list[dict[str, int | bool]] = []
    brace_depth = 0

    for index, token in enumerate(tokens):
        if index in excluded_token_indexes:
            continue
        if token.text == "fn" and pending_function is None and _is_function_declaration(tokens, index):
            functions_total += 1
            unsafe_declared = _has_prior_unsafe(tokens, index)
            if unsafe_declared:
                functions_unsafe_declared += 1
            pending_function = {
                "unsafe_declared": unsafe_declared,
                "has_unsafe_block": False,
            }
        elif token.text == "trait" and _has_prior_unsafe(tokens, index):
            unsafe_trait_count += 1
        elif token.text == "impl" and _has_prior_unsafe(tokens, index):
            unsafe_impl_count += 1
        elif token.text == "unsafe":
            next_index = _next_significant(tokens, index)
            if next_index is not None and tokens[next_index].text == "{":
                unsafe_blocks += 1
                unsafe_block_openings.append(next_index)
                if function_stack:
                    function_stack[-1]["has_unsafe_block"] = True
                close_index = brace_map.get(next_index)
                if close_index is not None:
                    start_line = tokens[next_index].line
                    end_line = tokens[close_index].line
                    unsafe_lines.update(range(start_line, end_line + 1))
        if token.text == "{":
            brace_depth += 1
            if pending_function is not None:
                context = {
                    "brace_depth": brace_depth,
                    "body_start": index,
                    "body_end": brace_map.get(index, index),
                    "unsafe_declared": bool(pending_function["unsafe_declared"]),
                    "has_unsafe_block": bool(pending_function["has_unsafe_block"]),
                }
                function_stack.append(context)
                pending_function = None
        elif token.text == ";":
            pending_function = None
        elif token.text == "}":
            if function_stack and function_stack[-1]["brace_depth"] == brace_depth:
                context = function_stack.pop()
                if context["has_unsafe_block"]:
                    functions_with_unsafe += 1
                    if context.get("unsafe_declared"):
                        functions_declared_unsafe_with_block += 1
            brace_depth = max(brace_depth - 1, 0)

    function_contexts = _function_body_contexts(tokens, excluded_token_indexes, brace_map)
    functions_with_blocks = {
        id(context)
        for block_opening in unsafe_block_openings
        for context in function_contexts
        if int(context["body_start"]) < block_opening < int(context["body_end"])
    }
    functions_with_unsafe = len(functions_with_blocks)
    functions_declared_unsafe_with_block = sum(
        1 for context in function_contexts if id(context) in functions_with_blocks and context["unsafe_declared"]
    )
    functions_unsafe_any = functions_unsafe_declared + functions_with_unsafe - functions_declared_unsafe_with_block
    functions_safe = functions_total - functions_unsafe_any
    functions_without_explicit_unsafe = functions_total - functions_unsafe_any
    relative_path = path.relative_to(root).as_posix()
    return FileSummary(
        path=relative_path,
        physical_loc=physical_loc,
        nonblank_loc=nonblank_loc,
        functions_total=functions_total,
        functions_safe=functions_safe,
        functions_unsafe_declared=functions_unsafe_declared,
        functions_with_unsafe=functions_with_unsafe,
        functions_unsafe_any=functions_unsafe_any,
        functions_with_any_explicit_unsafe=functions_unsafe_any,
        functions_without_explicit_unsafe=functions_without_explicit_unsafe,
        unsafe_traits=unsafe_trait_count,
        unsafe_impls=unsafe_impl_count,
        unsafe_blocks=unsafe_blocks,
        unsafe_loc_estimate=len(unsafe_lines),
        unsafe_lines_estimate=sorted(unsafe_lines),
    )


def strip_non_code(text: str) -> str:
    result: list[str] = []
    index = 0
    length = len(text)
    block_depth = 0
    state = "normal"
    raw_hashes = 0
    while index < length:
        char = text[index]
        nxt = text[index + 1] if index + 1 < length else ""
        if state == "normal":
            raw_match = _raw_string_start(text, index)
            if char == "/" and nxt == "/":
                result.extend([" ", " "])
                index += 2
                state = "line_comment"
                continue
            if char == "/" and nxt == "*":
                result.extend([" ", " "])
                index += 2
                block_depth = 1
                state = "block_comment"
                continue
            if raw_match is not None:
                prefix_len, raw_hashes = raw_match
                result.extend(" " * prefix_len)
                index += prefix_len
                state = "raw_string"
                continue
            if char in {"b", "c"} and nxt == '"':
                result.extend([" ", " "])
                index += 2
                state = "string"
                continue
            if char == '"':
                result.append(" ")
                index += 1
                state = "string"
                continue
            if _is_char_literal_start(text, index):
                result.append(" ")
                index += 1
                state = "char"
                continue
            result.append(char)
            index += 1
            continue
        if state == "line_comment":
            if char == "\n":
                result.append("\n")
                index += 1
                state = "normal"
            else:
                result.append(" ")
                index += 1
            continue
        if state == "block_comment":
            if char == "/" and nxt == "*":
                result.extend([" ", " "])
                block_depth += 1
                index += 2
            elif char == "*" and nxt == "/":
                result.extend([" ", " "])
                block_depth -= 1
                index += 2
                if block_depth == 0:
                    state = "normal"
            else:
                result.append("\n" if char == "\n" else " ")
                index += 1
            continue
        if state == "string":
            if char == "\\" and index + 1 < length:
                result.extend([" ", " "])
                index += 2
            elif char == '"':
                result.append(" ")
                index += 1
                state = "normal"
            else:
                result.append("\n" if char == "\n" else " ")
                index += 1
            continue
        if state == "raw_string":
            if char == '"' and text[index + 1:index + 1 + raw_hashes] == ("#" * raw_hashes):
                result.append(" ")
                result.extend(" " * raw_hashes)
                index += 1 + raw_hashes
                state = "normal"
            else:
                result.append("\n" if char == "\n" else " ")
                index += 1
            continue
        if state == "char":
            if char == "\\" and index + 1 < length:
                result.extend([" ", " "])
                index += 2
            elif char == "'":
                result.append(" ")
                index += 1
                state = "normal"
            else:
                result.append("\n" if char == "\n" else " ")
                index += 1
    return "".join(result)


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    line = 1
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if char == "\n":
            line += 1
            index += 1
            continue
        if char.isspace():
            index += 1
            continue
        if char.isalpha() or char == "_":
            start = index
            while index < length and (text[index].isalnum() or text[index] == "_"):
                index += 1
            tokens.append(Token(text[start:index], line, "word", start))
            continue
        tokens.append(Token(char, line, "symbol", index))
        index += 1
    return tokens


def build_brace_map(tokens: list[Token]) -> dict[int, int]:
    stack: list[int] = []
    brace_map: dict[int, int] = {}
    for index, token in enumerate(tokens):
        if token.text == "{":
            stack.append(index)
        elif token.text == "}" and stack:
            start = stack.pop()
            brace_map[start] = index
    return brace_map


def _is_char_literal_start(text: str, index: int) -> bool:
    if text[index] != "'":
        return False
    lookahead = text[index + 1:index + 6]
    if "\n" in lookahead:
        lookahead = lookahead.split("\n", 1)[0]
    return "'" in lookahead


def _raw_string_start(text: str, index: int) -> tuple[int, int] | None:
    prefixes = ("r", "br")
    for prefix in prefixes:
        if not text.startswith(prefix, index):
            continue
        cursor = index + len(prefix)
        hashes = 0
        while cursor < len(text) and text[cursor] == "#":
            hashes += 1
            cursor += 1
        if cursor < len(text) and text[cursor] == '"':
            return cursor - index + 1, hashes
    return None


def _next_significant(tokens: list[Token], index: int) -> int | None:
    for candidate in range(index + 1, len(tokens)):
        return candidate
    return None


def _has_prior_unsafe(tokens: list[Token], index: int) -> bool:
    cursor = index - 1
    while cursor >= 0:
        token = tokens[cursor]
        if token.text in {";", "{", "}"}:
            return False
        if token.text == "unsafe":
            return True
        cursor -= 1
    return False


def _is_function_declaration(tokens: list[Token], index: int) -> bool:
    next_index = _next_significant(tokens, index)
    if next_index is None or tokens[next_index].kind != "word":
        return False
    cursor = index - 1
    while cursor >= 0 and tokens[cursor].text in {"unsafe", "async", "const", "extern", "default", "pub"}:
        cursor -= 1
    if cursor >= 0 and tokens[cursor].text == ")":
        opening = _matching_open_paren(tokens, cursor)
        if opening is not None and opening > 0 and tokens[opening - 1].text == "pub":
            cursor = opening - 2
    return cursor < 0 or tokens[cursor].text in {"{", "}", ";", "]"}


def _matching_open_paren(tokens: list[Token], close_index: int) -> int | None:
    depth = 0
    for index in range(close_index, -1, -1):
        if tokens[index].text == ")":
            depth += 1
        elif tokens[index].text == "(":
            depth -= 1
            if depth == 0:
                return index
    return None


def _test_only_token_indexes(tokens: list[Token], brace_map: dict[int, int]) -> set[int]:
    """Return direct `#[cfg(test)]` and `#[test]` item spans.

    This intentionally leaves mixed predicates such as `cfg(any(test, feature))`
    in scope because they can compile in production configurations.
    """
    excluded: set[int] = set()
    index = 0
    while index + 2 < len(tokens):
        if tokens[index].text != "#" or tokens[index + 1].text != "[":
            index += 1
            continue
        close = _attribute_close(tokens, index + 1)
        if close is None or not _is_direct_test_attribute(tokens[index + 2:close]):
            index += 1
            continue
        item_start = close + 1
        while item_start + 1 < len(tokens) and tokens[item_start].text == "#" and tokens[item_start + 1].text == "[":
            nested_close = _attribute_close(tokens, item_start + 1)
            if nested_close is None:
                break
            item_start = nested_close + 1
        item_end = _item_end(tokens, item_start, brace_map)
        if item_end is not None:
            excluded.update(range(index, item_end + 1))
        index = max(item_start, index + 1)
    return excluded


def _attribute_close(tokens: list[Token], opening: int) -> int | None:
    depth = 0
    for index in range(opening, len(tokens)):
        if tokens[index].text == "[":
            depth += 1
        elif tokens[index].text == "]":
            depth -= 1
            if depth == 0:
                return index
    return None


def _is_direct_test_attribute(attribute: list[Token]) -> bool:
    texts = [token.text for token in attribute]
    return texts == ["test"] or texts == ["cfg", "(", "test", ")"]


def _item_end(tokens: list[Token], item_start: int, brace_map: dict[int, int]) -> int | None:
    for index in range(item_start, len(tokens)):
        if tokens[index].text == "{":
            return brace_map.get(index)
        if tokens[index].text == ";":
            return index
    return None


def _function_body_contexts(
    tokens: list[Token], excluded_token_indexes: set[int], brace_map: dict[int, int]
) -> list[dict[str, int | bool]]:
    contexts: list[dict[str, int | bool]] = []
    for index, token in enumerate(tokens):
        if index in excluded_token_indexes or token.text != "fn" or not _is_function_declaration(tokens, index):
            continue
        paren_depth = 0
        bracket_depth = 0
        for body_start in range(index + 1, len(tokens)):
            if body_start in excluded_token_indexes:
                continue
            body_token = tokens[body_start].text
            if body_token == "(":
                paren_depth += 1
            elif body_token == ")":
                paren_depth = max(paren_depth - 1, 0)
            elif body_token == "[":
                bracket_depth += 1
            elif body_token == "]":
                bracket_depth = max(bracket_depth - 1, 0)
            if body_token == ";" and paren_depth == 0 and bracket_depth == 0:
                break
            if body_token == "{":
                body_end = brace_map.get(body_start)
                if body_end is not None:
                    contexts.append(
                        {
                            "body_start": body_start,
                            "body_end": body_end,
                            "unsafe_declared": _has_prior_unsafe(tokens, index),
                        }
                    )
                break
    return contexts


def _file_has_unsafe(file_summary: FileSummary) -> bool:
    return any(
        value > 0
        for value in (
            file_summary.functions_unsafe_declared,
            file_summary.functions_with_unsafe,
            file_summary.unsafe_traits,
            file_summary.unsafe_impls,
            file_summary.unsafe_blocks,
            file_summary.unsafe_loc_estimate,
        )
    )


def _pct(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round((numerator / denominator) * 100.0, 4)
