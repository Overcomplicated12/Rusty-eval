"""Read-only lexical inventory scanner for methodology version 1.

This intentionally dependency-free first implementation extracts common C/C++
declaration forms. It is deterministic but not a complete parser; its output is
evidence for review, not proof of migration success or failure.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

from .models import Bucket, Declaration, INVENTORY_METHODOLOGY_VERSION
from .rules import classify


SOURCE_SUFFIXES = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx", ".in"}
DEFAULT_SAMPLE_COUNTS = {
    Bucket.TRIVIAL: 10,
    Bucket.REFACTOR_THEN_DSL: 10,
    Bucket.NEEDS_TRANSPILER: 10,
    Bucket.BOUNDARY: 10,
    Bucket.UNKNOWN: 20,
}
FUNCTION_RE = re.compile(
    r"(?m)^[ \t]*(?P<prefix>(?:(?:static|extern|inline|const|volatile|unsigned|signed)\s+)*)"
    r"(?P<return>[A-Za-z_][\w\s]*?)\s+(?P<stars>\*+\s*)?(?P<name>[A-Za-z_]\w*)\s*"
    r"\((?P<params>[^{};]*)\)\s*\{"
)
TYPE_RE = re.compile(r"(?m)^[ \t]*(?P<kind>struct|union|enum)\s+(?P<name>[A-Za-z_]\w*)?[^;{]*\{")
TYPEDEF_RE = re.compile(r"(?m)^[ \t]*typedef\b[^;{}]+\s+(?P<name>[A-Za-z_]\w*)\s*;")
GLOBAL_RE = re.compile(
    r"(?m)^[ \t]*(?P<prefix>static\s+)?(?P<type>[A-Za-z_]\w*(?:\s+[A-Za-z_]\w*)*\s*\*?)\s+"
    r"(?P<name>[A-Za-z_]\w*)\s*(?:=[^;]*)?;"
)


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _brace_depth_before(text: str, offset: int) -> int:
    """Return a conservative lexical brace depth for top-level declaration checks."""
    return text[:offset].count("{") - text[:offset].count("}")


def _matching_brace(text: str, opening: int) -> int | None:
    """Find a closing brace while ignoring quoted strings and comments roughly."""
    depth, index = 0, opening
    quote: str | None = None
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if quote:
            if char == "\\":
                index += 2
                continue
            if char == quote:
                quote = None
        elif char in {"'", '"'}:
            quote = char
        elif char == "/" and next_char == "/":
            newline = text.find("\n", index)
            index = len(text) if newline == -1 else newline
            continue
        elif char == "/" and next_char == "*":
            end = text.find("*/", index + 2)
            index = len(text) if end == -1 else end + 2
            continue
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return None


def _base_features(path: Path, text: str) -> dict[str, object]:
    parts = {part.lower() for part in path.parts}
    macro_lines = sum(1 for line in text.splitlines() if line.lstrip().startswith("#"))
    return {
        "conditional_compilation": bool(re.search(r"(?m)^\s*#\s*(if|ifdef|ifndef|elif)\b", text)),
        "macro_use": bool(re.search(r"\b[A-Z][A-Z0-9_]{2,}\s*\(", text)),
        "macro_density": round(macro_lines / max(1, text.count("\n") + 1), 6),
        "generated_source": any("generated" in part or "gen" == part for part in parts),
        "third_party": any(part in {"third_party", "vendor", "external", "deps"} for part in parts),
        "platform_specific": any(part in {"win", "windows", "unix", "linux", "darwin", "platform"} for part in parts),
    }


def detect_features(snippet: str, params: str = "", *, base: dict[str, object] | None = None) -> dict[str, object]:
    """Detect visible lexical evidence; no feature alone proves impossibility."""
    features: dict[str, object] = dict(base or {})
    body = snippet
    parameter_pointers = params.count("*")
    features.update({
        "raw_pointer_parameter": parameter_pointers > 0,
        "raw_pointer_return": bool(re.search(r"^[^{(]*\*\s*[A-Za-z_]\w*\s*\(", body)),
        "pointer_to_pointer": "**" in params or "**" in body,
        "void_pointer": bool(re.search(r"\bvoid\s*\*", body)),
        "pointer_arithmetic": bool(re.search(r"\b\w+\s*(?:\+\+|--|[+\-]=)\s*\d|\*\s*\(\s*\w+\s*[+\-]", body)),
        "c_array": bool(re.search(r"\b[A-Za-z_]\w*\s*\[\s*\d+\s*\]", body)),
        "flexible_array": bool(re.search(r"\b[A-Za-z_]\w*\s*\[\s*\]", body)),
        "malloc": bool(re.search(r"\bmalloc\s*\(", body)),
        "calloc": bool(re.search(r"\bcalloc\s*\(", body)),
        "realloc": bool(re.search(r"\brealloc\s*\(", body)),
        "free": bool(re.search(r"\bfree\s*\(", body)),
        "memcpy": bool(re.search(r"\bmemcpy\s*\(", body)),
        "memmove": bool(re.search(r"\bmemmove\s*\(", body)),
        "memset": bool(re.search(r"\bmemset\s*\(", body)),
        "function_pointer": bool(re.search(r"\(\s*\*\s*[A-Za-z_]\w*\s*\)", body)),
        "callback": bool(re.search(r"\b(?:callback|cb)\w*\b", body, re.IGNORECASE)),
        "union": bool(re.search(r"\bunion\b", body)),
        "bitfield": bool(re.search(r"\b[A-Za-z_]\w*\s*:\s*\d+", body)),
        "variadic": "..." in params,
        "va_list": bool(re.search(r"\bva_(?:list|start|arg|end)\b", body)),
        "goto": bool(re.search(r"\bgoto\s+[A-Za-z_]\w*\s*;", body)),
        "setjmp": bool(re.search(r"\bsetjmp\s*\(", body)),
        "longjmp": bool(re.search(r"\blongjmp\s*\(", body)),
        "static_local": bool(re.search(r"\bstatic\s+[\w\s\*]+\s+[A-Za-z_]\w*", body)),
        "extern_or_abi_boundary": bool(re.search(r"\bextern\b|__declspec|__attribute__", body)),
        "syscall": bool(re.search(r"\b(?:syscall|ioctl|open|close|read|write)\s*\(", body)),
        "macro_generated_declaration": bool(re.match(r"\s*[A-Z][A-Z0-9_]+\s*\(", body)),
        "parameter_count": 0 if not params.strip() or params.strip() == "void" else len(params.split(",")),
        "pointer_count": body.count("*"),
        "branch_complexity_proxy": len(re.findall(r"\b(?:if|for|while|case|&&|\|\|)\b", body)),
        "call_count": len(re.findall(r"\b[A-Za-z_]\w*\s*\(", body)),
        "global_read": False,
        "global_write": False,
        "mutable_global": False,
    })
    return features


def _function_declarations(text: str, path: Path) -> list[tuple[str, int, int, str, str, dict[str, object]]]:
    declarations = []
    base = _base_features(path, text)
    for match in FUNCTION_RE.finditer(text):
        if match.group("name") in {"if", "for", "while", "switch"}:
            continue
        end = _matching_brace(text, match.end() - 1)
        if end is None:
            continue
        start_line, end_line = _line_number(text, match.start()), _line_number(text, end)
        snippet = text[match.start():end + 1]
        declarations.append((match.group("name"), start_line, end_line, "function", snippet,
                             detect_features(snippet, match.group("params"), base=base)))
    return declarations


def _other_declarations(text: str, path: Path, function_spans: list[tuple[int, int]]) -> list[tuple[str, int, int, str, str, dict[str, object]]]:
    declarations = []
    base = _base_features(path, text)
    for regex, kind in ((TYPE_RE, None), (TYPEDEF_RE, "typedef"), (GLOBAL_RE, "global")):
        for match in regex.finditer(text):
            if any(start <= match.start() <= end for start, end in function_spans):
                continue
            actual_kind = kind or match.group("kind")
            if actual_kind == "global" and _brace_depth_before(text, match.start()) != 0:
                continue
            if actual_kind == "global" and match.group("type").startswith("typedef"):
                continue
            name = match.groupdict().get("name") or f"anonymous_{actual_kind}_{_line_number(text, match.start())}"
            end = _matching_brace(text, match.end() - 1) if actual_kind in {"struct", "union", "enum"} else match.end()
            end = end if end is not None else match.end()
            snippet = text[match.start():end + 1]
            features = detect_features(snippet, base=base)
            if actual_kind == "global":
                features["mutable_global"] = "const" not in match.group("type")
            declarations.append((name, _line_number(text, match.start()), _line_number(text, end), actual_kind,
                                 snippet, features))
    return declarations


def scan(root: Path, source_dir: str, application: str, application_commit: str) -> list[Declaration]:
    """Read source files under *root* and return stable declaration records."""
    root = root.resolve()
    source_root = root / source_dir
    records: list[Declaration] = []
    for path in sorted(path for path in source_root.rglob("*") if path.is_file() and path.suffix in SOURCE_SUFFIXES):
        text = path.read_text(encoding="utf-8", errors="replace")
        functions = _function_declarations(text, path)
        spans = []
        for match in FUNCTION_RE.finditer(text):
            end = _matching_brace(text, match.end() - 1)
            if end is not None:
                spans.append((match.start(), end))
        others = _other_declarations(text, path, spans)
        global_names = {name for name, _, _, kind, _, _ in others if kind == "global"}
        for name, _, _, _, snippet, features in functions:
            for global_name in global_names:
                if re.search(rf"\b{re.escape(global_name)}\s*(?:=|\+=|-=|\+\+|--)", snippet):
                    features["global_write"] = True
                if re.search(rf"\b{re.escape(global_name)}\b", snippet):
                    features["global_read"] = True
        raw = functions + others
        for name, line, end_line, kind, snippet, features in sorted(raw, key=lambda item: (item[1], item[3], item[0])):
            bucket, primary, secondary, confidence = classify(features)
            records.append(Declaration(application, application_commit, str(path.relative_to(root)), line, end_line,
                                       kind, name, max(1, end_line - line + 1), features, bucket, primary,
                                       secondary, confidence))
    return records


def sample(records: list[Declaration], seed: int, requested: dict[Bucket, int] | None = None) -> dict[str, object]:
    """Sample each bucket independently using a seed derived from bucket identity."""
    requested = requested or DEFAULT_SAMPLE_COUNTS
    grouped: dict[Bucket, list[Declaration]] = defaultdict(list)
    for record in records:
        grouped[record.bucket].append(record)
    buckets = []
    for bucket in Bucket:
        population = sorted(grouped[bucket], key=lambda item: (item.file, item.line, item.kind, item.name))
        selected = list(population)
        random.Random(f"{seed}:{bucket.value}").shuffle(selected)
        selected = selected[:requested[bucket]]
        buckets.append({
            "bucket": bucket.value, "requested_count": requested[bucket], "actual_count": len(selected),
            "available_count": len(population),
            "declarations": [{
                "file": item.file, "line": item.line, "end_line": item.end_line, "kind": item.kind,
                "name": item.name, "features": item.features, "scanner_bucket": item.bucket.value,
                "primary_reason": item.primary_reason, "confidence": item.confidence,
                "human_bucket": "", "human_notes": "", "agreement": "",
            } for item in selected],
        })
    return {"inventory_methodology_version": INVENTORY_METHODOLOGY_VERSION, "seed": seed, "buckets": buckets}


def _summary(records: list[Declaration], metadata: dict[str, object]) -> str:
    counts, locs = Counter(record.bucket.value for record in records), Counter()
    blockers, reasons = Counter(), Counter(record.primary_reason for record in records)
    for record in records:
        locs[record.bucket.value] += record.loc
        blockers.update(name for name, value in record.features.items() if value is True)
    total_loc = sum(record.loc for record in records)
    lines = ["# Inventory summary", "", "## Run metadata", ""]
    lines.extend(f"- **{key}**: `{value}`" for key, value in metadata.items())
    lines += ["", "## Declaration counts", "", f"- Declarations: {len(records)}", f"- Total analyzed LOC: {total_loc}", "",
              "| Bucket | Declarations | Declaration % | LOC | LOC % |", "| --- | ---: | ---: | ---: | ---: |"]
    for bucket in Bucket:
        count, loc = counts[bucket.value], locs[bucket.value]
        lines.append(f"| {bucket.value} | {count} | {(100 * count / max(1, len(records))):.2f} | {loc} | {(100 * loc / max(1, total_loc)):.2f} |")
    lines += ["", "## Blocker/evidence histogram", ""]
    lines.extend(f"- `{name}`: {count}" for name, count in sorted(blockers.items()))
    lines += ["", "## Primary-reason histogram", ""]
    lines.extend(f"- `{name}`: {count}" for name, count in sorted(reasons.items()))
    lines += ["", "## Low-confidence declarations", ""]
    lines.extend(f"- `{r.file}:{r.line}` `{r.name}` — {r.primary_reason}" for r in records if r.confidence == "low")
    lines += ["", "## UNKNOWN declarations", ""]
    lines.extend(f"- `{r.file}:{r.line}` `{r.name}` — {r.primary_reason}" for r in records if r.bucket == Bucket.UNKNOWN)
    return "\n".join(lines) + "\n"


def write_outputs(records: list[Declaration], output: Path, *, application: str, application_commit: str,
                  seed: int) -> None:
    """Write JSON, CSV, summary Markdown, and a blank human-review sample."""
    output.mkdir(parents=True, exist_ok=True)
    metadata = {"inventory_methodology_version": INVENTORY_METHODOLOGY_VERSION, "application": application,
                "application_commit": application_commit}
    payload = {**metadata, "declarations": [record.to_dict() for record in records]}
    (output / "inventory.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = [record.to_dict() for record in records]
    fields = ["inventory_methodology_version", "application", "application_commit", "file", "line", "end_line", "kind", "name", "loc",
              "features", "bucket", "primary_reason", "secondary_reasons", "confidence"]
    with (output / "inventory.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            row["inventory_methodology_version"] = INVENTORY_METHODOLOGY_VERSION
            row["features"] = json.dumps(row["features"], sort_keys=True)
            row["secondary_reasons"] = json.dumps(row["secondary_reasons"])
            writer.writerow({key: row[key] for key in fields})
    (output / "summary.md").write_text(_summary(records, metadata), encoding="utf-8")
    (output / "manual-validation-sample.json").write_text(
        json.dumps(sample(records, seed), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--source-dir", default="src")
    parser.add_argument("--application", required=True)
    parser.add_argument("--application-commit", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--sample-seed", type=int, default=6423)
    args = parser.parse_args()
    records = scan(args.root, args.source_dir, args.application, args.application_commit)
    write_outputs(records, args.output, application=args.application, application_commit=args.application_commit,
                  seed=args.sample_seed)


if __name__ == "__main__":
    main()
