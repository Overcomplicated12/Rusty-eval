# AGENTS.md

## Project purpose

`rusty-eval` is the evaluation and automation repository for RustyCpp application migrations. It measures migratability, automatic conversion success, correctness, performance overhead, token usage, agent wall-clock time, build and test attempts, human interventions and their time, and converted LOC.

Target applications such as SQLite, Mako, and Masstree live in separate repositories. Do not vendor or silently modify them from this repository.

## Repository responsibilities

- `inventory/`: static inventory and migration-feasibility analysis.
- `harness/`: automated conversion, build, test, and repair orchestration.
- `configs/`: per-application experiment definitions.
- `results/`: machine-generated experiment results.
- `tests/`: tests for `rusty-eval` itself.
- `docs/`: methodology and experiment definitions.

## Core research rules

1. Reproducibility is more important than convenience.
2. Every application evaluation must record the exact source commit.
3. Record the RustyCpp/transpiler commit used for every experiment.
4. Never silently change methodology between applications.
5. Preserve failed conversion attempts and failure reasons.
6. Measure token usage and human intervention rather than estimating them.
7. Do not claim code is unmigratable merely because a heuristic identifies a difficult construct.
8. Separate directly convertible, reshape/refactor required, blocked by a transpiler capability, intentional unsafe/ABI boundary, and unknown code.
9. Classify difficult code by reason, not merely by file.
10. Inventory work must not modify a target application's source.

## Target repositories

Expected sibling layout:

```text
~/projects/rusty-eval
~/projects/sqlite
~/projects/mako
~/projects/rusty-cpp
~/projects/masstree
```

Do not assume all targets exist. Detect and report missing repositories.

## Inventory rules

The inventory scanner must be deterministic. Prefer Clang AST information for declarations and types, using textual analysis only where appropriate.

Standard buckets are `TRIVIAL`, `REFACTOR_THEN_DSL`, `NEEDS_TRANSPILER`, `BOUNDARY`, and `UNKNOWN`. Each classification must contain a bucket, primary reason, secondary reasons, and confidence. Prefer `UNKNOWN` to an unsupported confident classification.

Do not equate raw pointers, `goto`, unions, callbacks, macros, or other individual constructs with automatic impossibility.

## Target-source safety

During inventory, do not modify target source, run automatic migrations, or commit inside target repositories. During later conversion experiments, use explicit experiment branches or worktrees, preserve the pinned baseline, and make all mutations attributable to a recorded run.

## Generated results

Per-application results belong in `results/<application>/<run-or-inventory-id>/`. Prefer JSON or CSV for machine-readable data and Markdown for human-readable summaries. Never manually alter generated results to make an experiment look better.

## Git discipline

- Keep commits small and descriptive.
- Do not commit build directories, credentials, or API tokens.
- Do not force-push unless explicitly instructed.
- Do not modify unrelated repositories or automatically merge PRs.
- Before committing, inspect `git diff` and `git status`.

## Secrets

Never place GitHub tokens, API keys, authentication cookies, private SSH keys, or model-provider credentials in this repository. Use existing authenticated CLIs or environment configuration.

## Agent behavior

Before significant implementation:

1. Inspect relevant files.
2. Summarize the proposed change.
3. Identify methodological implications.
4. Implement the smallest coherent change.
5. Run relevant tests.
6. Inspect the diff.
7. Report results accurately.

Do not begin a large-scale application conversion unless explicitly instructed.
