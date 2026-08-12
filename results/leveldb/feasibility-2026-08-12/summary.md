# LevelDB C++ RustyCpp Feasibility Summary

Read-only feasibility preflight. No LevelDB or RustyCpp files were modified; no conversion, migration patch, build, test, or benchmark campaign was performed. This is technical evidence and estimates, not a research conclusion.

## Revisions and method

- LevelDB: `7ee830d02b623e8ffe0b95d59a74db1e58da04c5`
- RustyCpp: `488e422c293cdce3346f1ae3865ba588a74541e3`
- rusty-eval: `72c34af85ed43ecc8d8d92b3ada885cff44d7b60`
- AI-use record: `AI-2026-016`
- Inventory: frozen lexical methodology v2, deterministic seed `6423`

The production scope follows the `leveldb` CMake target: `db/`, `table/`, `util/`, `port/`, `helpers/memenv/`, and `include/leveldb/`, excluding `*_test.*`, benchmarks, test utilities, `leveldbutil`, and third-party code. The scanner staging copy and output were written only beneath `/tmp`.

```text
python3 -m src.inventory.inventory_v2 --root /tmp/leveldb-runtime-scope-20260812 --source-dir . --application leveldb-runtime --application-commit 7ee830d02b623e8ffe0b95d59a74db1e58da04c5 --output /tmp/leveldb-inventory-runtime --sample-seed 6423
```

## Executive summary

**MEASURED:** the scoped runtime is **95 files / 17,320 physical LOC**. Tests matching the repository's C++ `*_test.*` convention total **8,247 LOC**; `benchmarks/` totals **2,487 LOC**. The runtime inventory contains **372 declarations / 3,275 declaration-span LOC**.

**ESTIMATED:** LevelDB is a strong staged RustyCpp target because its safety-critical ownership and concurrency protocols are tangible and well-localized: Arena-backed memtables, lock-free reader access to skiplist nodes, cache-handle reference counts, DB version lifetimes, background compaction, and OS file/thread APIs. The hard code sits on core storage paths, however, so this is not a low-risk mechanical conversion.

| Estimate | Migration units | Physical runtime LOC |
|---|---:|---:|
| Conservative Rusty-safe ratio; DIRECT_DSL only | 25–40% | 20–30% |
| Practical ratio; refactoring plus isolated unsafe cores | 50–65% | 40–55% |
| Remain C++ / `@unsafe` / uncertain boundary | 35–55% | 45–60% |

The v2 scanner reports 331/372 declarations as `TRIVIAL` (84.1% declaration-span LOC). This is **not** a safe-ratio estimate: short helpers inherit the lifetimes, synchronization rules, and allocation protocols of `DBImpl`, `VersionSet`, `MemTable`, `SkipList`, cache entries, and environment objects. The estimates deliberately discount this lexical bucket.

Overall doability is **YES as a staged hybrid migration**. Broad all-safe migration remains **UNCERTAIN** until RustyCpp can preserve LevelDB’s intrusive reference protocols, virtual interfaces, function-pointer callbacks, atomics, and C++ API/ABI compatibility.

## Runtime structure

| Subsystem | Approx. LOC | Purpose | Difficulty |
|---|---:|---|---|
| DB coordination / recovery / compaction | ~4,800 | writes, snapshots, recovery, manifest updates, background compaction | Very High |
| Versions and table cache | ~2,300 | immutable version graph, file metadata, compaction selection, cached tables | Very High |
| Memtable / Arena / SkipList | ~750 | append-only allocation and lock-free read structure | Very High |
| Table and block format | ~2,200 | blocks, filters, table construction, iteration, checksums | High |
| Cache / iterator / batch utilities | ~1,500 | LRU handles, iterator cleanups, write batches, coding | High |
| Environment and platform layer | ~2,100 | files, mmap, locks, scheduling, threads, logging | Very High |
| Public API / portability / in-memory environment | ~3,700 | DB, Env, Slice, Options, C API, mutex/condvar wrappers, MemEnv | High |

These are approximate filename-based groups and are not additive source ownership boundaries.

## RustyCpp-relevant feature evidence

**MEASURED:** inventory signals include 158 raw-pointer parameters, 24 `void *` cases, eight pointer-to-pointer cases, 17 function-pointer cases, 15 C arrays, one `memcpy`, two `memset`, two pointer-arithmetic cases, three frees, two syscalls, four static locals, and 144 conditional-compilation signals. Thirteen macro-generated thread-annotation declarations are `UNKNOWN` with low confidence; they are scanner ambiguity, not an assessment that the annotated code is unknown.

**MANUALLY VERIFIED:**

| Area | Evidence | Classification |
|---|---|---|
| `Arena` | raw blocks, bump pointer, vector of owned allocations; only `memory_usage_` is atomic | SAFE_WITH_SMALL_UNSAFE_CORE / REFACTOR_THEN_DSL |
| `SkipList` | nodes use flexible trailing atomic links, placement construction in Arena, release-store publication and lock-free reads | NEEDS_RUSTYCPP_SUPPORT with an unsafe allocation core |
| `DBImpl` | mutex-guarded persistent state, atomics for shutdown/immutable memtable visibility, writer queue, snapshots and background compaction | REFACTOR_THEN_DSL / SAFE_WITH_SMALL_UNSAFE_CORE |
| `VersionSet` / `Version` | intrusive `Ref`/`Unref`, linked version graph, raw metadata and iterator ownership | REFACTOR_THEN_DSL |
| LRU cache | raw malloc/free entry layout, `void *` value/deleter callback, intrusive doubly linked lists under mutex | SAFE_WITH_SMALL_UNSAFE_CORE / LIKELY_UNSAFE_BOUNDARY |
| Table / block / log code | byte encodings, `Slice` borrowing, checksums, iterators and buffer ownership | REFACTOR_THEN_DSL |
| `Env` POSIX/Windows | virtual file interfaces, mmap, fds/handles, detached threads and function-pointer scheduling | LIKELY_UNSAFE_BOUNDARY |
| C API | opaque handles, callback filters/deleters and allocation through `leveldb_free` | LIKELY_UNSAFE_BOUNDARY |

**UNCERTAIN:** pinned RustyCpp evidence supports ownership types, slices, `Option`, `Result`, closures, iterators, templates/generics, RAII, explicit safe/unsafe blocks, and pointer provenance. It does not demonstrate end-to-end compatibility for LevelDB’s flexible atomic node layout, placement construction, intrusive refcounting, virtual `Env` graph, detached callback threads, or C ABI. These are uncertain rather than declared unsupported.

## Ownership and concurrency analysis

LevelDB has several interacting lifetime models:

```text
Arena ─owns blocks/nodes─> MemTable ─refcounted─> DBImpl / iterators
SkipList ─borrows Arena─> nodes published with release/acquire atomics
VersionSet ─owns/refcounts─> Version / FileMetaData / Compaction state
LRUCache ─owns entry layout─> callback-managed user value
DBImpl ─coordinates─> memtable rotation, snapshots, writer queue, background compaction
Env ─boundary─> files, mmap, locks, scheduling and detached threads
```

`Arena` and `SkipList` are especially relevant to RustyCpp. The source explicitly requires the Arena to outlive the skiplist and guarantees nodes are not deleted until destruction; readers use acquire loads and writers publish initialized nodes with release stores. A safe lifetime layer could make the Arena/skiplist relationship explicit, but flexible allocation and atomic link publication should remain narrow C++/`@unsafe` code initially.

`DBImpl` has a more distributed protocol: mutex-protected `mem_`, `imm_`, writer queue, snapshots, pending outputs, versions, and background-compaction state interact with atomics used for shutdown and immutable-memtable visibility. RustyCpp could improve the ownership and state structure, but migration must preserve liveness and lock-release boundaries during I/O.

## Representative manual validation sample

Seed `6423` was used for the scanner sample. The following source units were manually checked, including apparently easy helpers and central hard paths.

| Group | Declaration / area | Classification | Reason |
|---|---|---|---|
| Easy | `db/version_edit.h:63 AddFile` | DIRECT_DSL | metadata append policy |
| Easy | `table/iterator_wrapper.h:71 SeekToLast` | DIRECT_DSL | iterator forwarding |
| Easy | `util/random.h:26 Next` | DIRECT_DSL | local arithmetic state |
| Easy | `util/hash.cc:22 Hash` | DIRECT_DSL | bounded byte hashing after slice representation is available |
| Medium | `util/cache.cc:123 Resize` | REFACTOR_THEN_DSL | intrusive hash-table resizing |
| Medium | `util/crc32c.cc:276 Extend` | REFACTOR_THEN_DSL | optimized checksum path and feature detection |
| Medium | `helpers/memenv/memenv.cc:108 Append` | REFACTOR_THEN_DSL | file-state mutation and shared ownership |
| Medium | `db/db_impl.cc:90 ClipToRange` | DIRECT_DSL | range policy helper |
| Hard | `util/arena.h:37 Allocate` | SAFE_WITH_SMALL_UNSAFE_CORE | bump allocation and raw block lifetime |
| Hard | `db/skiplist.h:95 Node` / `NewNode` | NEEDS_RUSTYCPP_SUPPORT | flexible atomic links and placement construction |
| Hard | `util/cache.cc:239 Insert` | SAFE_WITH_SMALL_UNSAFE_CORE | malloc layout, deleter callback, intrusive refcount/list protocol |
| Hard | `db/db_impl.h:29 DBImpl` | REFACTOR_THEN_DSL | state graph across mutexes, atomics, refs and background work |
| Hard | `db/version_set.cc:569 VersionSet::Builder` | REFACTOR_THEN_DSL | version graph and file-metadata lifetime |
| Hard | `util/env_posix.cc:518 PosixEnv` | LIKELY_UNSAFE_BOUNDARY | POSIX files, mmap, locks and detached threads |
| Hard | `db/c.cc` callback/opaque-handle APIs | LIKELY_UNSAFE_BOUNDARY | C ABI and function-pointer ownership contracts |

## Work and migration scopes

**ESTIMATED work:** direct DSL conversion 1–3 person-months; C++ ownership/state refactoring 3–6; unsafe-boundary isolation 2–5; RustyCpp/transpiler support 3–8; build integration 1–2; correctness validation 3–6; performance validation 2–4. Broad hybrid migration is **14–28 person-months**.

| Scope | Recommended content | Size | Expected practical safe ratio | Difficulty |
|---|---|---:|---:|---|
| Proof of concept | Slice/coding/hash/status helpers, selected block-format checks, Arena ownership wrapper | 30–60 functions / 800–1,500 LOC | 60–80% | Medium |
| Meaningful evaluation | Arena + MemTable policy, table/block builders and readers, selected cache ownership, focused DB tests | 100–180 functions / 4,000–6,000 LOC | 40–60% | High |
| Broad migration | DB coordination, versions, compaction policy, tables and selected cache code; retain platform/C/atomic cores | ~7,000–9,500 LOC plausibly hybrid-migratable | 40–55% LOC | Very High |

The best first subsystem is **Arena/MemTable ownership policy plus table/block byte-format helpers**. It exercises allocation lifetime, append-only data, serialization, iteration, and relevant tests without first rewriting lock-free node publication or background compaction.

## Build, tests, benchmarks, and impact

**MEASURED:** CMake provides `LEVELDB_BUILD_TESTS` and `LEVELDB_BUILD_BENCHMARKS`; default unit tests use GoogleTest/GoogleMock and cover DB behavior, recovery, corruption, memtables, skiplist, versions, write batches, table/filter blocks, Arena, cache, coding, CRC32C, and environment behavior. Benchmarks build `db_bench` through Google Benchmark, with optional SQLite3 and Kyoto Cabinet comparisons.

No build was run. A later minimal comparison should disable benchmarks initially, build LevelDB and focused tests with at most `-j6`, run tests with at most `-j4`, and later compare put/get throughput, sequential/random reads, write-batch throughput, compaction latency, cache hit behavior, allocations, peak memory, recovery, and checksummed on-disk compatibility.

Infrastructure impact is **HIGH**. `DBImpl`, the table format, versions, cache, and environment lie beneath every normal read/write/compaction path; LevelDB's public C++ and C APIs also magnify compatibility requirements.

## Evidence and uncertainty

- **MEASURED:** revisions; scoped LOC/file counts; inventory results; lexical feature counts; CMake options; test and benchmark inventories.
- **MANUALLY VERIFIED:** Arena, SkipList, LRU cache, DBImpl state, VersionSet usage, POSIX environment and C API patterns.
- **ESTIMATED:** safe ratios, work, subsystem difficulty, migration scope and impact.
- **UNCERTAIN:** RustyCpp support for flexible atomic storage, placement construction, virtual interfaces, callback ABI, detached threads, and public generated/binary compatibility.

Raw pointers, atomics, callbacks, and macros are evidence requiring review—not automatic proof that a unit is unsafe or unmigratable.

## Final summary

LevelDB C++ runtime:

- Relevant production LOC: **17,320**
- Migration units: **372 scanner units / 3,275 declaration-span LOC**
- Conservative Rusty-safe ratio: **25–40% units / 20–30% LOC**
- Practical Rusty-safe ratio: **50–65% units / 40–55% LOC**
- Expected work: **HIGH; 14–28 person-months for broad hybrid migration**
- Infrastructure impact: **HIGH**
- Main unsafe/boundary area: **Arena/SkipList allocation and atomics, intrusive cache/version lifetimes, OS environment, and C callbacks**
- Best first subsystem: **Arena/MemTable ownership policy plus table/block format helpers**
- Recommended meaningful migration size: **100–180 functions / 4,000–6,000 LOC**
- Build/test quality: **broad unit coverage and useful DB benchmarks are available**
- Overall doability: **YES as a staged hybrid; broad all-safe migration remains uncertain**
