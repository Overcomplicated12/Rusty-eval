#!/usr/bin/env python3
"""Create a numbered, reviewable generative-AI provenance record."""

from __future__ import annotations

import argparse
import csv
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / "docs" / "ai-use" / "prompts"
INDEX = ROOT / "data" / "ai-use-index.csv"
LOG = ROOT / "docs" / "ai-use" / "log.md"
ID_PATTERN = re.compile(r"^AI-(?P<year>\d{4})-(?P<number>\d{3,})$")
LOG_HEADER = "| ID | Date | Tool | Purpose | Output used | AI-generated code | Commit | Disclosure |\n"
LOG_RULE = "|----|------|------|---------|-------------|-------------------|--------|------------|\n"


def next_id(year: int) -> str:
    """Return the next unused ID for *year*, checking prompt files and the CSV."""
    numbers: list[int] = []
    for path in PROMPTS.glob(f"AI-{year}-*.md"):
        match = ID_PATTERN.match(path.stem)
        if match:
            numbers.append(int(match["number"]))
    if INDEX.exists():
        with INDEX.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                match = ID_PATTERN.match(row.get("id", ""))
                if match and int(match["year"]) == year:
                    numbers.append(int(match["number"]))
    return f"AI-{year}-{max(numbers, default=0) + 1:03d}"


def prompt_text(prompt_file: Path | None) -> str:
    """Read a supplied verbatim prompt, or retain an explicit missing-prompt note."""
    if prompt_file is None:
        return "Exact prompt was not automatically captured. Researcher must insert verbatim prompt."
    return prompt_file.read_text(encoding="utf-8").rstrip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tool", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--researcher", default="")
    parser.add_argument("--prompt-file", type=Path)
    args = parser.parse_args()

    now = datetime.now().astimezone()
    record_id = next_id(now.year)
    PROMPTS.mkdir(parents=True, exist_ok=True)
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    destination = PROMPTS / f"{record_id}.md"
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing AI-use record: {destination}")

    prompt = prompt_text(args.prompt_file)
    destination.write_text(
        f"""# {record_id}\n\n## Metadata\n\nDate: {now.date().isoformat()}\nTime: {now.isoformat(timespec='seconds')}\nTool: {args.tool}\nModel: {args.model}\nResearcher: {args.researcher}\nPurpose: {args.purpose}\n\n## Exact human-authored prompt\n\n{prompt}\n\n## AI output usage\n\nUsed:\n- TBD\n\nDescription:\n\n## Research artifacts affected\n\nFiles:\n\nGit commit:\n\nPull request:\n\n## AI-generated code\n\nAI-generated code present:\n- TBD\n\nFiles / functions / regions:\n\n## Human contribution and review\n\nDescribe:\n\n- what the researcher independently decided\n- what was reviewed\n- what was changed manually\n- what AI suggestions were rejected\n\n## Disclosure status\n\nExplicit citation/disclosure required:\n- TBD\n\nReason:\n\n## Notes\n""",
        encoding="utf-8",
    )

    fields = [
        "id", "date", "time", "tool", "model", "purpose", "prompt_file", "output_used",
        "ai_generated_code", "artifacts", "git_commit", "pull_request", "human_review",
        "disclosure_status", "notes",
    ]
    new_file = not INDEX.exists() or INDEX.stat().st_size == 0
    with INDEX.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if new_file:
            writer.writeheader()
        writer.writerow({
            "id": record_id, "date": now.date().isoformat(), "time": now.isoformat(timespec="seconds"),
            "tool": args.tool, "model": args.model, "purpose": args.purpose,
            "prompt_file": destination.relative_to(ROOT).as_posix(), "output_used": "TBD",
            "ai_generated_code": "TBD", "artifacts": "", "git_commit": "", "pull_request": "",
            "human_review": "", "disclosure_status": "TBD", "notes": "",
        })

    if not LOG.exists():
        LOG.parent.mkdir(parents=True, exist_ok=True)
        LOG.write_text("# Generative AI Use Log\n\n" + LOG_HEADER + LOG_RULE, encoding="utf-8")
    row = f"| [{record_id}](prompts/{record_id}.md) | {now.date().isoformat()} | {args.tool} | {args.purpose} | TBD | TBD |  | TBD |\n"
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(row)
    print(record_id)


if __name__ == "__main__":
    main()
