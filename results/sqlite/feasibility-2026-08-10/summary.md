# SQLite C RustyCpp Feasibility Summary

Read-only research preflight. No SQLite, RustyCpp, or rusty-eval source files were modified; no conversion, migration patch, build, or benchmark campaign was performed.

## Revisions

- SQLite: `ab5206d096d6ecc5f9ea2586889c07e52e852c23`
- RustyCpp: `488e422c293cdce3346f1ae3865ba588a74541e3`
- rusty-eval: `00099c1a13b150fadbe66eb8b400dd94782c4c80`
- AI-use record: `AI-2026-014`

SQLite had a pre-existing untracked `.gitignore` in its checkout. It was left untouched.

## Executive assessment

The primary feasibility result is a language-boundary blocker: this checkout contains **315 tracked C files and zero tracked C++ files**, while RustyCpp’s inline DSL is documented for `.cpp` files and C++ parsing. Therefore, the direct RustyCpp inline-DSL safe ratio for the existing SQLite source is **not applicable**, not a meaningful percentage of zero.

SQLite remains a valuable Rust migration research target, but a RustyCpp evaluation would first require one of:

1. a supported C frontend or C-to-C++ compatibility mode;
2. a preparatory C-to-C++ port of selected SQLite modules; or
3. a C ABI wrapper whose implementation is migrated separately.

If SQLite is first made C++-compatible, the semantic estimates below are planning estimates only:

| Hypothetical C-to-C++ bridge | Units | LOC |
|---|---:|---:|
| Conservative safe after port; direct/simple logic | 20–35% | 15–25% |
| Practical safe after port/refactoring and isolated unsafe cores | 45–65% | 30–50% |

The remaining C/C++ or `@unsafe` core would likely be **35–55% of units / 50–70% of LOC**, concentrated in VFS, allocation, mutexes, callbacks, virtual tables, parser/VDBE state, unions, generated code, and platform branches.

## Measured scope

The primary hand-written core boundary is `src/`, excluding source files beginning with `test`, the shell template, and the Tcl binding:

- Core source: **102 files / 189,070 physical LOC**
- Source test files: **47 files / 37,644 LOC**
- Shell/Tcl binding excluded from core: **2 files / 19,325 LOC**
- All `src/` C/header/template files: **151 files / 246,039 LOC**
- Tool C/header/template files: **39 files / 22,016 LOC**
- `mptest` C source: **1 file / 1,474 LOC**
- Benchmark/fuzz C files (`speedtest1.c`, `kvtest.c`, `fuzzcheck.c`): **3 files / 7,390 LOC**
- External extensions are separate; a broad `ext/` C inventory is approximately **118 files / 145,763 LOC**

The new v2 scanner run analyzed all `src/` C/header/template files:

- Declarations: **5,688**
- Scanner declaration-span LOC: **173,956**
- `TRIVIAL`: 4,361 declarations / 80,470 span LOC
- `REFACTOR_THEN_DSL`: 872 / 60,035
- `NEEDS_TRANSPILER`: 447 / 33,443
- `UNKNOWN`: 8 / 8

These scanner buckets are lexical evidence only. They do not overcome the C-language input limitation.

## Core structure

| Subsystem | Files | LOC | Purpose | Difficulty |
|---|---:|---:|---|---|
| SQL compiler/VDBE | 24 | 72,867 | tokenizer, parser support, expression/select planning, bytecode VM | Very High |
| OS/memory/concurrency | 30 | 36,365 | malloc, mutexes, VFS, pager-adjacent OS services | Very High |
| Core support | 37 | 51,045 | main connection state, APIs, utilities, diagnostics | High |
| Storage | 5 | 14,039 | B-tree, pager, WAL, cache/backup paths | Very High |
| Functions/extensions in `src` | 6 | 14,754 | JSON, date, functions, virtual-table helpers | High |

The grouping is filename-based and approximate. SQLite’s internal structures cross these boundaries heavily through `sqlite3Int.h`.

## RustyCpp-relevant evidence

The v2 scanner found these `src/` declaration signals:

- Raw-pointer parameters: **4,403**
- Raw-pointer returns: **485**
- `void*`: **1,068**
- Pointer-to-pointer: **681**
- C arrays: **1,235**
- Function pointers: **349**
- `memset`: **327**
- `memcpy`: **260**
- Pointer arithmetic: **192**
- `goto`: **177**
- Bitfields: **128**
- Mutable globals: **118**
- Unions: **60**
- Variadic declarations: **37**
- `va_list`: **44**
- Syscall/platform signals: **11**

Important manual classifications:

| Feature | Classification for a hypothetical C++ port |
|---|---|
| SQL token/state-machine helpers | REFACTOR_THEN_DSL |
| Pure expression and utility logic | DIRECT_DSL or REFACTOR_THEN_DSL |
| `sqlite3_malloc`/`sqlite3_free`/realloc | SAFE_WITH_SMALL_UNSAFE_CORE |
| B-tree, pager, WAL, and cache state | REFACTOR_THEN_DSL / NEEDS_RUSTYCPP_SUPPORT |
| `sqlite3_vfs` and OS methods | LIKELY_UNSAFE_BOUNDARY |
| Virtual-table modules and callbacks | NEEDS_RUSTYCPP_SUPPORT / LIKELY_UNSAFE_BOUNDARY |
| `sqlite3_api_routines` extension function table | LIKELY_UNSAFE_BOUNDARY |
| unions, bitfields, flexible arrays, packed layouts | NEEDS_RUSTYCPP_SUPPORT / UNCERTAIN |
| `goto`-based cleanup and error paths | REFACTOR_THEN_DSL |
| generated parser/opcode/amalgamation outputs | EXCLUDE or retain C |
| Tcl, shell, loadable-extension and OS integrations | LIKELY_UNSAFE_BOUNDARY |

SQLite has explicit manual allocation, mutex, VFS, callback, and function-table contracts. `sqlite3.h.in` exposes `sqlite3_vfs` method pointers; `sqlite3ext.h` exposes a large `sqlite3_api_routines` function-pointer table; `sqlite3Int.h` contains extensive internal pointer-rich state. These are not automatically unsafe, but they are strong boundary and lifetime signals.

## Ownership and lifetime analysis

SQLite does not use a single Arena model. Its key lifetime systems are:

1. Connection and statement objects (`sqlite3`, `Vdbe`) own or reference parser, schema, pager, and cache state.
2. SQLite’s configurable memory subsystem owns allocations through `sqlite3_malloc`, `sqlite3_realloc`, and `sqlite3_free`, often under mutex protection.
3. VFS and file objects use manually maintained method tables and platform handles.
4. Virtual tables and SQL functions use application-provided callbacks and destructor contracts.
5. B-tree, pager, WAL, and cache layers couple object lifetimes to transactions, locks, and file state.

The strongest safety opportunity would be explicit ownership wrappers for connection/statement state, allocator results, VFS handles, and callback registrations. The likely unavoidable unsafe boundary includes the C ABI, function-pointer tables, OS file handles, custom allocators, mutex implementations, and extension loading.

## Representative deterministic sample

Seed: `6423`. The sample below excludes source test files, `shell.c.in`, and `tclsqlite.c`; declarations were manually checked against C source patterns.

| Group | Representative declarations |
|---|---|
| Easy | `vdbesort.c:731 vdbePmaReaderInit`; `pager.c:1248 pager_pagehash`; `sqlite.h.in:298 sqlite_uint64`; `os_unix.c:4590 unixShm`; `vdbesort.c:2637 vdbeSorterMergeTreeBuild`; `build.c:1100 sqlite3TableColumnToIndex`; `os_unix.c:2492 dotlockLock`; `dbpage.c:463 dbpageRollbackTo`; `sqlite.h.in:308 sqlite3_uint64`; `main.c:4030 sqlite3CantopenError` |
| Medium | `global.c:338 sqlite3NProfileCnt`; `select.c:516 sqlite3ProcessJoin`; `where.c:208 whereOrInsert`; `dbpage.c:340 dbpageUpdate`; `whereInt.h:149 anonymous_struct_149`; `alter.c:2176 dropColumnFunc`; `global.c:367 sqlite3WhereTrace`; `vdbeInt.h:458 Vdbe`; `dbstat.c:156 statConnect`; `select.c:6668 aggregateConvertIndexedExprRefToColumn` |
| Hard | `vtab.c:559 vtabCallConstructor`; `mem2.c:301 sqlite3MemFree`; `pragma.c:72 getSafetyLevel`; `malloc.c:72 sqlite3_memory_alarm`; `bitvec.c:103 anonymous_union_103`; `vtab.c:123 sqlite3_create_module_v2`; `vdbeaux.c:2508 sqlite3VdbePrintSql`; `sqliteInt.h:3064 anonymous_union_3064`; `threads.c:51 sqlite3ThreadCreate`; `pragma.c:2927 pragmaVtabOpen` |
| Random | `sqliteInt.h:3511 anonymous_union_3511`; `select.c:4792 constInsert`; `window.c:735 WindowRewrite`; `sqliteInt.h:3884 Parse`; `mem2.c:343 sqlite3MemRealloc`; `sqliteInt.h:1987 anonymous_union_1987`; `func.c:3131 percentFinal`; `date.c:306 computeFloor`; `pager.c:724 sqlite3_pager_readdb_count`; `wherecode.c:1085 codeCursorHintIsOrFunction` |

The sample confirms that SQLite has many small algorithmic functions, but its difficult units are central: VFS, memory, virtual tables, parser/VDBE state, unions, callbacks, and thread handling.

## RustyCpp capability fit

RustyCpp currently documents and tests C++ parsing, `@safe`/`@unsafe`, pointer/lifetime analysis, Rust-shaped ownership types, `Option`, `Result`, `Vec`, slices, closures, iterators, and templates. The inline DSL is documented as operating inside `.cpp` files, with generated C++ fallbacks.

This creates a decisive distinction:

- Directly feeding SQLite’s `.c` files to the current inline DSL: **NOT DEMONSTRATED / effectively blocked**.
- Porting selected modules to C++ first, then applying RustyCpp: **Plausible but high effort**.
- Using RustyCpp only for a new C++ wrapper or replacement subsystem: **Plausible and bounded**.

The RustyCpp checker’s C++ pointer support is relevant after a C++ port, but it does not itself provide C-language parsing or preserve C’s macro/preprocessor and ABI behavior automatically.

## Estimated work

### Direct current-checkout RustyCpp migration

**Blocked by language compatibility.** Expected work is not meaningfully estimable as a conversion until C support or a C-to-C++ preparation plan exists.

### C-to-C++ bridge plus meaningful RustyCpp evaluation

Estimated:

- C-to-C++ compatibility/refactoring: **6–15 person-months**
- RustyCpp/transpiler support and annotations: **4–10**
- Unsafe-boundary isolation: **3–8**
- Build integration: **2–4**
- Correctness validation: **4–10**
- Performance validation: **2–5**

Total: **HIGH to VERY_HIGH; approximately 20–50 person-months** for a meaningful core evaluation, with broad migration substantially beyond that.

## Highest-value areas

| Rank | Area | Bridge-case practical safe ratio | Work | Impact | Recommended |
|---:|---|---:|---|---|---|
| 1 | Pure SQL tokenizer/completion helpers | 60–80% | Medium | Medium | Yes, after C++ proof |
| 2 | Selected expression/utility functions | 45–65% | Medium–High | High | Yes |
| 3 | Memory wrapper policy around allocator core | 30–50% | High | Very High | Yes, staged |
| 4 | VDBE value/record helpers | 25–45% | High | Very High | Later |
| 5 | B-tree/pager policy above file boundary | 20–40% | Very High | Very High | Later |
| 6 | VFS abstraction wrappers | 15–30% | Very High | Very High | Boundary only |
| 7 | JSON/date/function helpers | 45–65% | Medium | Medium–High | Yes |
| 8 | Virtual-table and extension callbacks | 10–30% | Very High | High | Later |

## Migration scopes

### Proof of concept

Do not begin with the unmodified C tree. First port a small, isolated C module such as SQL-completion/token-state logic or a pure utility/codec subset to C++ while preserving the C ABI.

- **20–40 functions / 500–1,500 LOC after C++ preparation**
- Expected bridge-case practical safe ratio: **55–80%**
- Main boundary: C ABI and SQLite error/status conventions
- Difficulty: **High because language preparation dominates**

### Meaningful evaluation

Recommended: prepared tokenizer/completion utilities, selected expression/value helpers, memory wrapper policy, and a narrow VDBE or JSON slice, with SQLite’s existing TCL/C test harness retained as the oracle.

- **100–250 functions / 8,000–15,000 LOC after C++ preparation**
- Approximately **4–8% of core physical LOC**
- Expected bridge-case practical safe ratio: **30–55%**
- Major blockers: C-to-C++ conversion, macro-heavy headers, function-pointer APIs, VFS, and internal layout

### Broad migration

Broad migration of the existing SQLite core is not presently practical through the inline DSL alone. A hybrid strategy could migrate selected policy and algorithmic code, while retaining C for the VFS, allocator, ABI, generated parser/opcode pieces, and callback-heavy internals. A plausible long-term migrated share after extensive preparation is **30–50% of core LOC**, not a direct conversion of the current C tree.

## Tests, benchmarks, and build feasibility

SQLite has unusually strong validation infrastructure. The core can be built without Tcl; the full development test workflow uses an enhanced Tcl `testfixture` and `make test`. The repository includes extensive TCL tests, C test programs, fault-injection tests, corruption tests, WAL/pager tests, malloc tests, fuzzers, and platform tests.

Useful later comparisons include:

- `speedtest1` SQL workload timing
- `kvtest` key/value workload timing
- `fuzzcheck` and invariant fuzzing
- Statement prepare/step/finalize throughput
- B-tree read/write and transaction latency
- Pager/WAL throughput and fsync behavior
- Allocation count/bytes and lookaside usage
- Mutex contention and concurrency behavior
- Database size, cache behavior, CPU time, and tail latency

SQLite’s tests are excellent for correctness comparison, but many require generated sources, Tcl, platform features, or a preserved C ABI. The appropriate later oracle is the original C implementation’s test suite, not only unit-level translated-function tests.

No build or test run was performed in this preflight.

## Infrastructure impact

**VERY_HIGH.** SQLite is a widely embedded database engine with a stable public C ABI, a VFS abstraction, extension loading, virtual tables, a SQL compiler, a bytecode VM, and storage/concurrency machinery. Safety improvements in allocator wrappers, statement lifetime, VFS handles, or selected VDBE policy would affect broadly reused infrastructure, but the ABI and platform boundaries are substantial.

## Evidence and uncertainty

- **MEASURED:** revisions, C/C++ suffix counts, physical LOC boundaries, v2 scanner output, test/benchmark counts, and build/test documentation.
- **MANUALLY VERIFIED:** SQLite’s C-only language profile, allocator/mutex/VFS/function-table structures, generated-source notes, representative functions, and RustyCpp’s C++-only inline-DSL documentation.
- **ESTIMATED:** hypothetical C-to-C++ safe ratios, work, migration scopes, and impact.
- **UNCERTAIN:** whether future RustyCpp versions add C input support, how much C can be accepted under a C++ compatibility mode, and the cost of preserving exact SQLite ABI/behavior.
- Raw pointers were treated as evidence requiring review, not automatic proof of unsafety.
- Existing SQLite v1 inventory data is retained as a prior baseline, but this new evaluation uses the current v2 scanner and explicitly corrects for the C/C++ target mismatch.

## Final summary

- Relevant current target LOC: **189,070 C core LOC**
- Migration units: **5,688 v2 scanner declarations; 3,946 filtered core declarations**
- Direct current Rusty-safe ratio: **NOT APPLICABLE / blocked by C-only input**
- Hypothetical post-C++-bridge conservative ratio: **20–35% units / 15–25% LOC**
- Hypothetical post-C++-bridge practical ratio: **45–65% units / 30–50% LOC**
- Expected work: **VERY_HIGH; 20–50 person-months for a meaningful bridge-based evaluation**
- Infrastructure impact: **VERY_HIGH**
- Main boundary: **C language input, stable C ABI, VFS, allocator, callbacks, and generated parser/VDBE interfaces**
- Best first subsystem: **pure tokenizer/completion or utility logic after a small C-to-C++ proof**
- Recommended meaningful migration size: **100–250 functions / 8,000–15,000 prepared LOC**
- Build/test quality: **exceptionally strong, but Tcl/generated-source dependent**
- Overall doability: **NO direct inline-DSL target today; MAYBE as a staged C-to-C++ bridge research program**
