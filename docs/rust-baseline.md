# Rust baseline scanner

## Purpose

`rust_baseline` measures how pinned Rust systems-library source trees structure explicit `unsafe` so those raw measurements can later be compared against RustyCpp migration results. It is measurement infrastructure only. It does not set thresholds, score projects, or draw research conclusions.

## Scope

The scanner records per-crate, per-configuration measurements for production Rust source owned by the target crate/package:

- source size: production Rust files, physical LOC, nonblank LOC
- function-level counts: total functions/methods, declared `unsafe fn`, functions containing explicit `unsafe { ... }`, and counts derived from those raw totals
- unsafe structure: `unsafe fn`, `unsafe trait`, `unsafe impl`, explicit `unsafe` block counts, and an estimated explicit-unsafe LOC span
- concentration: which files contain explicit `unsafe`, per-file unsafe counts, top unsafe-heavy files, and top-5 concentration fractions

Each real run also records the source URL, pinned commit or exact version, scan date, mode, enabled features, Rust toolchain identity when available, scanner version, and external-tool status.

## Exclusions

By default the local source scanner excludes:

- `tests/`
- `benches/`
- `examples/`
- `fuzz/`
- `target/`
- common vendored directories such as `vendor/` and `vendored/`
- `build.rs`
- files ending in `.generated.rs`

This is meant to approximate production crate source. It does not try to classify dependency code as belonging to the target crate.

## Interpretation limits

Absence of explicit `unsafe` is not evidence that code is bug-free, secure, or memory-safe overall. Presence of explicit `unsafe` is not evidence of poor engineering. The scanner only measures explicit source structure that is visible in the pinned crate/package source tree.

## Source-level vs build-aware metrics

The local scanner is source-level. It reads Rust source text and does not evaluate `cfg` selections, macro expansion, borrow checking, or actual compilation.

`cargo-geiger`, when installed and when a machine-readable mode can be confirmed from `--help`, is recorded separately as a build-aware measurement. Its results are not merged into the local source totals.

`count-unsafe`, when installed and when a machine-readable mode can be confirmed from `--help`, is also preserved separately.

Unavailable tools are reported as `TOOL_UNAVAILABLE` or `MACHINE_OUTPUT_UNAVAILABLE`; missing metrics are never fabricated.

## Why concentration is measured

Two crates can have similar total `unsafe` counts while concentrating that code very differently. Recording which files carry most explicit `unsafe` helps later analysis distinguish diffuse from localized unsafe usage without collapsing everything into a single percentage.

## Configuration

Template configuration lives at [configs/rust-baseline.toml](/home/frankw/projects/rusty-eval/configs/rust-baseline.toml). It intentionally uses placeholder pins so validation fails until each crate is pinned.

Supported source pinning forms in v1:

- git repository + exact `rev`
- crates.io exact `version`

Example validation:

```bash
python3 -m rust_baseline.cli validate-config \
  --config configs/rust-baseline.toml
```

## Reproducing a run

1. Replace each placeholder pin in `configs/rust-baseline.toml` with a real commit or exact crate version.
2. Install this repository in editable mode.
3. Ensure optional tools such as `cargo-geiger` or `count-unsafe` are installed if you want those extra artifacts.
4. Run one of:

```bash
python3 -m rust_baseline.cli scan \
  --config configs/rust-baseline.toml \
  --crate redb \
  --mode default

python3 -m rust_baseline.cli scan-all \
  --config configs/rust-baseline.toml \
  --mode all-features
```

5. Regenerate summaries later with:

```bash
python3 -m rust_baseline.cli report \
  --results results/rust-baseline/<experiment-id>
```

The scanner writes append-only artifacts under `results/rust-baseline/<experiment-id>/`.

## Adding another crate

1. Add another `[[crate]]` entry to `configs/rust-baseline.toml`.
2. Set `name`, `package`, and either `repo` + exact `rev` or an exact `version`.
3. Re-run `validate-config`.
4. Run `scan` or `scan-all`.

## Result layout

A scan writes:

- root `metadata.json`
- per-crate `metadata.json`
- per-crate/per-mode `result.json`
- preserved local `source_scan.json`
- preserved `cargo_geiger.json`
- preserved `count_unsafe.json`
- tool stdout/stderr files under `stdout/`
- experiment-level `summary.csv` and `summary.md`

## Known limitations

- The local scanner is lexical, not a formal Rust parser.
- Explicit unsafe LOC is an estimate based on physical lines overlapped by `unsafe { ... }` spans after stripping comments and strings.
- Nested unsafe blocks are unioned by line within each file, so the estimate is intentionally conservative.
- Source-level scans do not follow conditional compilation; all included source files are scanned as text.
- Macro expansion and generated source discovered only at build time are out of scope.
- External-tool execution is intentionally conservative: if the installed tool's `--help` output does not clearly expose a machine-readable mode, v1 records that limitation instead of guessing.
- Unsafe-category classification fields are reserved for later manual or better-justified analysis; v1 emits no automatic semantic categorization.
