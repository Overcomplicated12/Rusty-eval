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
