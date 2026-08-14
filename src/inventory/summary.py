"""Clone (optionally), pin, and summarize an arbitrary C/C++ repository."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from .inventory_v2 import scan
from .inventory import write_outputs
from .models import INVENTORY_METHODOLOGY_VERSION_V2


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, check=True, text=True,
                            capture_output=True)
    return result.stdout.strip()


def materialize_repo(url: str, checkout: Path, ref: str | None = None) -> tuple[Path, str]:
    """Create/update a shallow checkout and return its immutable evaluated commit."""
    checkout = checkout.resolve()
    if (checkout / ".git").exists():
        origin = _git(checkout, "config", "--get", "remote.origin.url")
        if origin != url:
            raise ValueError(f"checkout {checkout} belongs to {origin!r}, not {url!r}")
        _git(checkout, "fetch", "--depth", "1", "origin", ref or "HEAD")
    else:
        checkout.parent.mkdir(parents=True, exist_ok=True)
        command = ["clone", "--depth", "1"]
        if ref:
            command += ["--branch", ref]
        command += [url, str(checkout)]
        subprocess.run(["git", *command], check=True)
    if ref:
        _git(checkout, "checkout", "--detach", ref)
    return checkout, _git(checkout, "rev-parse", "HEAD")


def detect_source_dir(repo: Path, requested: str | None) -> str:
    if requested:
        candidate = repo / requested
        if not candidate.is_dir():
            raise ValueError(f"source directory does not exist: {candidate}")
        return requested
    candidates = [
        path for path in repo.rglob("*")
        if path.is_dir() and path.name.lower() in {"src", "source", "sources"}
        and ".git" not in path.parts and "test" not in {part.lower() for part in path.parts}
    ]
    scores = []
    suffixes = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx"}
    for root in candidates:
        count = sum(1 for p in root.rglob("*") if p.is_file() and p.suffix in suffixes)
        if count:
            scores.append((count, root.relative_to(repo).as_posix()))
    if not scores:
        raise ValueError(f"could not find C/C++ source under {repo}")
    if len(scores) != 1:
        options = ", ".join(name for _, name in sorted(scores, reverse=True))
        raise ValueError(f"ambiguous C/C++ source roots; pass --source-dir explicitly ({options})")
    return scores[0][1]


def run(args: argparse.Namespace) -> Path:
    repo = args.root.resolve() if args.root else None
    if args.url:
        repo, commit = materialize_repo(args.url, args.checkout, args.ref)
    else:
        if repo is None or not (repo / ".git").exists():
            raise ValueError("use --url/--checkout or provide an existing git --root")
        commit = _git(repo, "rev-parse", "HEAD")
    source_dir = detect_source_dir(repo, args.source_dir)
    output = args.output.resolve()
    records = scan(repo, source_dir, args.application, commit)
    write_outputs(records, output, application=args.application, application_commit=commit,
                  seed=args.sample_seed, methodology_version=INVENTORY_METHODOLOGY_VERSION_V2)
    functions = [record for record in records if record.kind == "function"]
    counts = {}
    for record in functions:
        counts[record.bucket.value] = counts.get(record.bucket.value, 0) + 1
    total = len(functions)
    migratable = sum(counts.get(bucket, 0) for bucket in ("TRIVIAL", "REFACTOR_THEN_DSL"))
    function_summary = {
        "application": args.application,
        "application_commit": commit,
        "inventory_methodology_version": INVENTORY_METHODOLOGY_VERSION_V2,
        "functions_total": total,
        "functions_migratable_envelope": migratable,
        "functions_migratable_envelope_pct": 100 * migratable / total if total else 0,
        "bucket_counts": counts,
        "quota_threshold_pct": 80,
        "meets_80_percent_quota": (100 * migratable / total >= 80) if total else False,
    }
    (output / "function-summary.json").write_text(
        json.dumps(function_summary, indent=2, sort_keys=True) + "\n"
    )
    (output / "function-summary.md").write_text(
        "# Function migration summary\n\n"
        "The quota is measured by detected functions, not LOC. The migratable envelope "
        "includes `TRIVIAL` and `REFACTOR_THEN_DSL`; this is an inventory estimate, not a conversion guarantee.\n\n"
        f"- Functions: **{total}**\n"
        f"- Migratable envelope: **{migratable} ({function_summary['functions_migratable_envelope_pct']:.2f}%)**\n"
        f"- Meets 80% quota: **{'yes' if function_summary['meets_80_percent_quota'] else 'no'}**\n"
    )
    metadata = {"repository_url": args.url, "repository_root": str(repo),
                "source_dir": source_dir, "application_commit": commit,
                "inventory_methodology_version": INVENTORY_METHODOLOGY_VERSION_V2}
    (output / "run-metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--root", type=Path)
    source.add_argument("--url")
    parser.add_argument("--checkout", type=Path, help="persistent clone path used with --url")
    parser.add_argument("--ref", help="branch, tag, or commit to evaluate")
    parser.add_argument("--source-dir")
    parser.add_argument("--application", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--sample-seed", type=int, default=6423)
    args = parser.parse_args()
    if args.url and not args.checkout:
        parser.error("--checkout is required with --url")
    print(run(args))


if __name__ == "__main__":
    main()
