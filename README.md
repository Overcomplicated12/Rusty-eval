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

The scanner and harness are intentionally placeholders while the evaluation methodology is established. Validate the local Python package with:

```bash
python3 -m pytest
```

See [the methodology](docs/methodology.md) before adding an application evaluation.
