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

## Generative AI Use and Research Provenance

This repository is part of a research project that may be submitted to Regeneron STS, ISEF, or related research competitions. Generative-AI assistance must therefore be traceable and accurately disclosed. This is the project's implementation of Society for Science guidance supplied by the researcher; it is not official legal guidance.

### AI-use logging requirement

Significant human-authored prompts that contribute to research methodology, software design, implementation, debugging, experiment design, analysis tooling, or statistical/tool-selection decisions must be preserved in the project's AI-use log.

AI-use records live in `docs/ai-use/`, with the machine-readable index at `data/ai-use-index.csv`. Start a significant new AI-assisted task with `python3 scripts/new_ai_log.py`.

### Required provenance

For significant AI-assisted work, preserve when available the AI-use ID (`AI-YYYY-NNN`), date and time, system/tool, model/version, exact human-authored prompt, purpose, output disposition, affected files/functions/artifacts, resulting commit or PR, presence of AI-generated code, researcher review/manual changes, and disclosure/citation status.

Never fabricate or reconstruct an exact prompt that was not preserved. Explicitly record when the original prompt is unavailable.

### AI-generated code

AI may be used for permitted brainstorming and idea development, methodological discussion, code generation, debugging assistance, tooling recommendations, statistical-test/software-tool identification, and later language refinement where allowed. When AI-generated code is accepted, identify its affected files/functions/regions and AI-use entry. The researcher must review generated code before accepting it.

### Student-authored scientific work

Do not use an AI agent to author the student's initial research plan, abstract, research paper, poster text, scientific conclusions, interpretation of experimental results, future-work conclusions, or starter bibliography. Do not fabricate citations. AI-generated references are not verified sources; scientific claims must be supported by sources actually examined by the researcher.

The student researcher remains responsible for experimental decisions, verification, data interpretation, conclusions, and final scientific claims. AI may not substitute for the student's scientific reasoning.

### Compliance records vs. experimental telemetry

Keep these concepts separate. AI-use provenance documents how the researcher used generative AI. Experimental telemetry measures the performance/cost of AI, including input/output/total tokens, agent wall-clock time, conversion/build/test/repair attempts, human interventions, and human intervention time.

An experiment may reference `ai_use_ids`, but compliance logs and experimental measurements must not be conflated.

### Research integrity

- Never modify historical prompt records to make an experiment look cleaner.
- Preserve failed and rejected AI attempts when relevant to the measured research process.
- Never fabricate token counts, human effort, prompts, test results, or experimental outcomes.
- Clearly distinguish measured values from estimates.

### Secrets

Never record or commit API keys, GitHub tokens, authentication cookies, passwords, private SSH keys, or model-provider credentials. Redact secrets before storing prompt records.

## Agent behavior

Before significant implementation:

1. Determine whether the task requires an AI-use entry; create or identify the appropriate record when it does.
2. Inspect relevant files and summarize the proposed change and methodological implications.
3. Implement the smallest coherent change.
4. Run relevant tests and inspect the diff.
5. Record which AI-generated output was retained and associate the final commit or PR with the AI-use record when practical.
6. Report results accurately.

Do not begin a large-scale application conversion unless explicitly instructed.
