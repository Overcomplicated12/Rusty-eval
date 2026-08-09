# Evaluation methodology

The intended evaluation pipeline is:

```text
pinned target source
        ↓
inventory
        ↓
migratability report
        ↓
automated conversion harness
        ↓
build / test / repair loop
        ↓
correctness evaluation
        ↓
performance evaluation
        ↓
effort accounting
        ↓
results
```

Before comparing multiple applications, freeze the methodology: identical definitions, collection procedures, and stopping rules give each target comparable treatment. Each run records its target commit, RustyCpp commit, harness commit, environment, failures, and any human intervention.

Inventory is read-only and provides evidence for feasibility; it does not itself establish that code is impossible to migrate. Conversion experiments must use explicit worktrees or branches and preserve the pinned baseline.

## Inventory methodology version 1

Version 1 inventories functions (the primary unit), structs, unions, enums,
typedefs, and relevant global/static declarations. It is a dependency-free,
deterministic lexical scanner: Clang AST information remains preferred when a
reproducible integration is added, but v1 does not claim to parse all C/C++.

The scanner preserves visible features separately from classification. It
measures source location, LOC, parameter/pointer counts, branch/call proxies,
and visible patterns such as memory operations, arrays, control-flow escapes,
callbacks, unions, macros, compilation conditions, and boundary-path evidence.
It does not make LLM calls.

The authoritative bucket definitions and ordered rules are in
`inventory/rules.py`:

- `TRIVIAL`: no significant detected blocker; ordinary pointers, arrays, and
  macros alone remain evidence rather than a blocker.
- `REFACTOR_THEN_DSL`: visible localized mechanical restructuring, such as raw
  byte operations, allocation, pointer arithmetic, `goto`, or mutable state.
- `NEEDS_TRANSPILER`: conceptually migratable but dependent on an unverified
  capability, including function pointers/callbacks, unions, varargs, or jumps.
- `BOUNDARY`: generated, third-party, or explicit ABI/extern source-boundary
  evidence.
- `UNKNOWN`: insufficiently localizable evidence, currently including a
  macro-generated declaration. It is preferred to speculative certainty.

Confidence is `high` for direct boundary evidence, `medium` for explicit
feature-based rules, and `low` for macro-generated ambiguity. No individual
pointer, union, callback, or `goto` feature automatically means impossibility.

Validation sampling uses a fixed seed and a separate pseudo-random stream per
bucket. Default requested counts are 10 each for `TRIVIAL`,
`REFACTOR_THEN_DSL`, `NEEDS_TRANSPILER`, and `BOUNDARY`, and 20 for `UNKNOWN`.
When fewer declarations exist, all are selected and the actual count is
recorded. Human review fields are intentionally blank.

A material change to these rules, parser semantics, output schema, or sampling
procedure requires a new methodology version. Inventory classification is an
estimate of structural migratability, not proof that a declaration will or will
not successfully migrate through RustyCpp.
