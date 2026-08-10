# Phase 2 methodology scaffold (v1)

This document specifies intended collection mechanics, not experimental
results or a conclusion about migratability. Phase 1 inventory selects or
informs explicit `MigrationUnit` records; no automatic sampling is implemented
here.

Each eventual experiment uses a clean detached worktree pinned to the target
commit. The canonical checkout is never reset or cleaned. Before conversion,
the harness records baseline build and test outcomes. Coding agents only
propose a conversion or bounded repair; the harness checks changed-file scope,
runs the configured RustyCpp command, and independently determines the next
state.

The initial conversion plus configured transpiler, compile, and test repair
budgets stop at `AUTOMATION_EXHAUSTED`. Failed attempts and their diagnostics
are append-only artifacts. Token fields are recorded only when provider
reported or transparently locally estimated; absent values remain unavailable.
Benchmarking is an eventual, separately configured step and is not performed
by this scaffold.

## Outcome definitions

Automatic success requires RustyCpp, the configured build, and required tests
to pass with no recorded human intervention. Human-assisted success requires
those same conditions after a recorded migration-specific intervention. A run
fails when its attempt budget is exhausted or an unresolved blocker remains.

Automated effort consists of agent calls, measured or transparently estimated
tokens, agent wall time, and retries. Human effort is only manually timed,
migration-specific work; it remains separate from debugging this harness.
