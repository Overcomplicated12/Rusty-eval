# rusty-eval

Research tooling for evaluating RustyCpp migrations across applications. It is not RustyCpp itself.

This repository keeps reusable inventory analysis, conversion-harness infrastructure, experiment definitions, and generated evaluation results in one place. Target applications remain separate sibling repositories, such as `~/projects/sqlite`, `~/projects/mako`, and `~/projects/masstree`; they are never vendored here.

The current phase is inventory and migration-feasibility analysis. Later phases will automate conversion and measure correctness, performance, token use, and human effort.

## Layout

- `inventory/` — deterministic static inventory and feasibility analysis.
- `harness/` — future conversion/build/test/repair orchestration.
- `configs/` — per-application experiment definitions.
- `results/` — versionable summaries and generated run data.
- `docs/` — methodology and experiment schema.
- `tests/` — tests for this repository.

## Basic usage

Inventory methodology version 1 is frozen with its recorded SQLite results.
Methodology version 2 is a deterministic, read-only lexical scanner candidate
that corrects known v1 lexical false positives; it must be approved before use
for a new cross-application comparison.
It measures declaration structure and visible migration evidence; it does not
prove that a declaration will or will not successfully migrate through RustyCpp.
Run it only against an explicitly pinned source tree:

```bash
python3 -m inventory.inventory_v2 \
  --root /path/to/application \
  --source-dir src \
  --application sqlite \
  --application-commit <sha> \
  --output results/sqlite/<run-id> \
  --sample-seed 6423
```

See [the methodology](docs/methodology.md) before adding an application evaluation.
