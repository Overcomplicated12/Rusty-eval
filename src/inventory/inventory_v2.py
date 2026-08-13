"""Read-only lexical inventory scanner for frozen methodology version 2.

V2 keeps v1's output contract while sanitizing comments/strings and scoping
preprocessor evidence to each declaration. It remains a lexical scanner, not a
complete C/C++ parser.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from .inventory import (
    FUNCTION_RE,
    GLOBAL_RE,
    SOURCE_SUFFIXES,
    TYPE_RE,
    TYPEDEF_RE,
    _brace_depth_before,
    _line_number,
    _matching_brace,
    detect_features,
    write_outputs,
)
from .models import INVENTORY_METHODOLOGY_VERSION_V2, Declaration
from .rules_v2 import classify


def sanitize_source(text: str) -> str:
    """Blank comments and quoted strings while preserving offsets and newlines."""
    out = list(text)
    index = 0
    quote: str | None = None
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if quote:
            if char == "\\":
                if index + 1 < len(text) and out[index + 1] != "\n":
                    out[index + 1] = " "
                out[index] = " "
                index += 2
                continue
            if char == quote:
                out[index] = " "
                quote = None
            elif char != "\n":
                out[index] = " "
        elif char in {"'", '"'}:
            out[index] = " "
            quote = char
        elif char == "/" and next_char == "/":
            end = text.find("\n", index)
            end = len(text) if end == -1 else end
            for position in range(index, end):
                out[position] = " "
            index = end
            continue
        elif char == "/" and next_char == "*":
            end = text.find("*/", index + 2)
            end = len(text) if end == -1 else end + 2
            for position in range(index, end):
                if out[position] != "\n":
                    out[position] = " "
            index = end
            continue
        index += 1
    return "".join(out)


def _conditional_depths(clean: str) -> list[int]:
    depth, result = 0, []
    for line in clean.splitlines():
        directive = re.match(r"\s*#\s*(\w+)", line)
        if directive and directive.group(1) in {"if", "ifdef", "ifndef"}:
            depth += 1
        result.append(depth)
        if directive and directive.group(1) == "endif":
            depth = max(0, depth - 1)
    return result


def _base_features(path: Path) -> dict[str, object]:
    parts = {part.lower() for part in path.parts}
    return {
        "conditional_compilation": False,
        "macro_use": False,
        "macro_density": 0.0,
        "generated_source": any("generated" in part or part == "gen" for part in parts),
        "third_party": any(part in {"third_party", "vendor", "external", "deps"} for part in parts),
        "platform_specific": any(part in {"win", "windows", "unix", "linux", "darwin", "platform"} for part in parts),
    }


def _features(clean_snippet: str, params: str, kind: str, line: int, depths: list[int], *, generated: bool = False,
              path: Path) -> dict[str, object]:
    features = detect_features(clean_snippet, params, base=_base_features(path))
    features["conditional_compilation"] = bool(depths[line - 1]) if line <= len(depths) else False
    features["macro_use"] = bool(re.search(r"\b[A-Z][A-Z0-9_]{2,}\s*\(", clean_snippet))
    features["macro_density"] = round(
        sum(1 for value in clean_snippet.splitlines() if value.lstrip().startswith("#")) / max(1, clean_snippet.count("\n") + 1), 6
    )
    features["static_local"] = bool(re.search(r"(?m)^\s*static\s+[^;{}()]+\s+[A-Za-z_]\w*\s*(?:=|;)", clean_snippet)) if kind == "function" else False
    features["flexible_array"] = bool(re.search(r"\b[A-Za-z_]\w*\s*\[\s*\]\s*;", clean_snippet)) if kind in {"struct", "union"} else False
    features["extern_declaration"] = bool(re.search(r"\bextern\b", clean_snippet))
    features["explicit_abi_boundary"] = bool(re.search(r"\bextern\s+\"[A-Za-z+]+\"|__declspec\s*\(", clean_snippet))
    features["extern_or_abi_boundary"] = features["explicit_abi_boundary"]
    features["macro_generated_declaration"] = generated
    features["lexical_ambiguity"] = generated
    return features


def scan(root: Path, source_dir: str, application: str, application_commit: str) -> list[Declaration]:
    """Return deterministic v2 records without modifying the target tree."""
    root, records = root.resolve(), []
    for path in sorted(item for item in (root / source_dir).rglob("*") if item.is_file() and item.suffix in SOURCE_SUFFIXES):
        original = path.read_text(encoding="utf-8", errors="replace")
        clean = sanitize_source(original)
        depths = _conditional_depths(clean)
        raw: list[tuple[str, int, int, str, dict[str, object]]] = []
        function_spans: list[tuple[int, int]] = []
        for match in FUNCTION_RE.finditer(clean):
            end = _matching_brace(clean, match.end() - 1)
            if end is None:
                continue
            function_spans.append((match.start(), end))
            line, end_line = _line_number(clean, match.start()), _line_number(clean, end)
            opening = clean.find("{", match.start(), end + 1)
            body = clean[opening + 1:end] if opening != -1 else ""
            features = _features(clean[match.start():end + 1], match.group("params"), "function", line, depths, path=path)
            features["static_local"] = bool(re.search(r"(?m)^\s*static\s+[^;{}()]+\s+[A-Za-z_]\w*\s*(?:=|;)", body))
            raw.append((match.group("name"), line, end_line, "function", features))
        for regex, default_kind in ((TYPE_RE, None), (TYPEDEF_RE, "typedef"), (GLOBAL_RE, "global")):
            for match in regex.finditer(clean):
                if any(start <= match.start() <= end for start, end in function_spans):
                    continue
                kind = default_kind or match.group("kind")
                if kind == "global" and (_brace_depth_before(clean, match.start()) != 0 or match.group("type").startswith("typedef")):
                    continue
                end = _matching_brace(clean, match.end() - 1) if kind in {"struct", "union", "enum"} else match.end()
                end = match.end() if end is None else end
                line, end_line = _line_number(clean, match.start()), _line_number(clean, end)
                name = match.groupdict().get("name") or f"anonymous_{kind}_{line}"
                features = _features(clean[match.start():end + 1], "", kind, line, depths, path=path)
                if kind == "global":
                    features["mutable_global"] = "const" not in match.group("type") and "extern" not in match.group("type")
                raw.append((name, line, end_line, kind, features))
        occupied = function_spans + [(match.start(), match.end()) for match in TYPE_RE.finditer(clean)]
        for match in re.finditer(r"(?m)^(?!\s*#)\s*(?P<macro>[A-Z][A-Z0-9_]{2,})\s*\(", clean):
            if _brace_depth_before(clean, match.start()) == 0 and not any(start <= match.start() <= end for start, end in occupied):
                line = _line_number(clean, match.start())
                raw.append((f"macro_{match.group('macro')}_{line}", line, line, "macro_generated_declaration", _features(clean[match.start():match.end()], "", "macro_generated_declaration", line, depths, generated=True, path=path)))
        for name, line, end_line, kind, features in sorted(raw, key=lambda item: (item[1], item[3], item[0])):
            bucket, primary, secondary, confidence = classify(features)
            records.append(Declaration(application, application_commit, str(path.relative_to(root)), line, end_line, kind, name, max(1, end_line - line + 1), features, bucket, primary, secondary, confidence))
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--source-dir", default="src")
    parser.add_argument("--application", required=True)
    parser.add_argument("--application-commit", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--sample-seed", type=int, default=6423)
    args = parser.parse_args()
    write_outputs(scan(args.root, args.source_dir, args.application, args.application_commit), args.output, application=args.application, application_commit=args.application_commit, seed=args.sample_seed, methodology_version=INVENTORY_METHODOLOGY_VERSION_V2)


if __name__ == "__main__":
    main()
