# Apache Arrow C++ RustyCpp Feasibility Study

Read-only preflight. No Arrow/RustyCpp conversion, migration patch, generated-code edit, or target-source modification was performed.

## 1. Executive Summary

**Measured:** `cpp/src/arrow` has 1,293 C++ files (745 `.cc`, 548 headers). The stated candidate-production filter (exclude tests, benchmarks, testing/integration helpers, vendored, and generated-named files) yields **966 files / 299,626 nonblank LOC**. Tests/helpers: **261 files / 183,872 LOC**. Benchmarks: **66 / 13,706 LOC**. Vendored: **59 / 33,655 LOC**. Generated-named: **2 / 15,819 LOC**.

**Assessment:** staged hybrid migration is feasible; broad direct inline-DSL migration is not demonstrated. Estimated conservative Rusty-safe ratio is **25–35% of functions/units and 15–25% of LOC**. Estimated practical ratio, including localized refactoring and safe logic around small explicit unsafe cores, is **55–70% of units and 35–50% of LOC**. Meaningful work is HIGH; broad work is VERY_HIGH. Infrastructure impact is VERY_HIGH. Best first target is Buffer/BufferBuilder plus array-view helpers; meaningful evaluation should add ArrayData, types/scalars, IPC, and selected compute kernels.

## 2. C++ Codebase Structure

Representative production measurements (files/LOC, excluding tests/benchmarks): `array` 46/15,790; `compute` 140/64,369; `ipc` 27/11,506; `io` 29/6,201; `filesystem` 31/15,333; `csv` 25/5,805; `json` 22/4,707; `dataset` 36/11,871; `acero` 65/22,680; `util` 188/57,876. Root-level buffer, memory-pool, type, scalar, record-batch, and table code makes up the remaining candidate LOC.

| Subsystem | Purpose / dependencies | Performance | Difficulty |
|---|---|---|---|
| buffers/memory pools | ownership, allocation, alignment, byte storage | extreme | VERY_HIGH |
| arrays/builders/types/scalars | typed views, validity, shared buffers, visitors | extreme | HIGH |
| compute | kernels, dispatch, templates, SIMD, threads | extreme | VERY_HIGH |
| IPC/serialization | zero-copy framing and generated layouts | high | VERY_HIGH |
| IO/filesystem | streams, mmap/OS, cloud/network APIs | high | VERY_HIGH |
| CSV/JSON | parsing, byte/string views, external libraries | medium-high | HIGH |
| dataset | discovery/scanning and filesystem composition | high | VERY_HIGH |
| Acero | execution plan, callbacks, futures, concurrency | extreme | VERY_HIGH |
| utilities | futures, thread pool, traits, codecs, shared primitives | high | HIGH |

## 3. RustyCpp-Relevant Features

**Measured lexical file counts** in non-vendored Arrow source: `std::shared_ptr` 788, `unique_ptr` 341, `weak_ptr` 13, `reinterpret_cast` 223, `const_cast` 28, `memcpy` 106, `memmove` 3, `memset` 78, `malloc` 21, `free` 77, `std::atomic` 77, `std::mutex` 81, `condition_variable` 24, `std::function` 140, `virtual` 172, `std::span` 31, `std::variant` 19, `mmap` 12, socket 8, SIMD marker 42, `__m256` 13, `__m512` 2. The v2 scanner additionally reported 3,346 raw-pointer parameters, 59 raw-pointer returns, 277 pointer-arithmetic declarations, 701 function-pointer declarations, 1,045 C-array signals, 137 memcpy signals, 100 memset signals, 9 unions, and 104 variadic signals. These are evidence signals, not automatic unsafety claims.

| Feature | Likely classification |
|---|---|
| shared/unique ownership and RAII | DIRECT_DSL or REFACTOR_THEN_DSL |
| non-owning slices and views | SAFE_WITH_SMALL_UNSAFE_CORE |
| byte access, casts, alignment, memcpy | small LIKELY_UNSAFE_BOUNDARY; surrounding logic may be safe |
| `Result`/`Status`, `Option`, visitors | REFACTOR_THEN_DSL |
| templates/type traits/iterators | NEEDS_RUSTYCPP_SUPPORT or UNCERTAIN |
| callbacks/function pointers/virtual dispatch | NEEDS_RUSTYCPP_SUPPORT |
| atomics/mutex/futures/thread pool | NEEDS_RUSTYCPP_SUPPORT |
| mmap, filesystem, sockets, compression/C APIs | LIKELY_UNSAFE_BOUNDARY |
| SIMD and generated packing | REMAIN_CPP_UNSAFE or retained C++ backend |

Current pinned RustyCpp documentation/tests evidence `Box`, `Rc`, `Arc`, `Cell`, `RefCell`, `Vec`, `Option`, `Result`, slices, closures, iterators, generics/traits, safe/unsafe blocks, pointer provenance, function-pointer wrappers, RAII, lambda capture, partial borrows, and lifetime annotations. Inline DSL v1 is explicitly conservative: local free functions/structs/inherent impls, common control flow, and `Option`/`Result`/`Vec`/`String`; no cross-TU declaration magic. Exception modeling and virtual-call support are known incomplete. Accordingly, unclear cases are marked NEEDS_RUSTYCPP_SUPPORT or UNCERTAIN, not unsupported.

## 4. Subsystem Difficulty

Hard code is not confined to one tiny low-level island. Allocator, byte, OS, SIMD, and ABI code is concentrated, but its lifetime/aliasing contracts propagate through arrays, builders, IPC, compute, and execution. The useful pattern exists in layers: safe control/algorithmic logic surrounds lower-level primitives, but boundary isolation and API refactoring are required.

## 5. Representative Function Sample

The v2 scanner was run with seed 6423. Its validation file contains ten declarations each in TRIVIAL, REFACTOR_THEN_DSL, NEEDS_TRANSPILER, BOUNDARY, and UNKNOWN buckets. Representative manually reviewed entries (scanner span LOC; mostly one-line declarations) were:

| Group | Representative entries | Classification |
|---|---|---|
| easy | `util/decimal.cc:283 RoundedRightShift`; `util/basic_decimal.cc:754 ShiftArrayRight`; `engine/substrait/plan_internal.cc:46 AddExtensionSetToPlan`; `array/builder_base.cc:279 Visit`; `filesystem/localfs_test.cc:88 ConcreteTypedOption`; `acero/asof_join_node_test.cc:302 DoRunInvalidPlanTest`; `c/bridge_test.cc:78 ExportTraits`; `filesystem/hdfs.cc:53 Init`; `compute/kernels/vector_swizzle_test.cc:303 AssertScatterAAA`; `util/decimal.cc:1091 UInt64FromBigEndian` | DIRECT_DSL for arithmetic/control; REFACTOR or small unsafe core for byte/C boundary |
| medium | `util/tdigest.cc:135 TDigestImpl`; `ipc/writer.cc:885 WriteStridedTensorData`; `adapters/orc/util.cc:770 WriteMapBatch`; `util/value_parsing.h:336 Convert`; `c/bridge_test.cc:5508 handler`; `c/bridge_test.cc:4525 orig_allocated_`; `c/bridge_test.cc:5034 mm`; `c/bridge_test.cc:4612 c_stream`; `util/decimal.cc:1091 UInt64FromBigEndian`; `util/task_group_test.cc:221 operator` | REFACTOR_THEN_DSL, NEEDS_SUPPORT, or boundary |
| hard | `filesystem/gcsfs.cc:494 CreateDir`; `pretty_print.cc:195 WritePrimitiveValues`; `csv/converter.cc:485 DurationValueDecoder`; `status.h:245 CapacityError`; `flight/server.cc:300 Next`; `ipc/reader.cc:2847 FuzzIpcFile`; `util/bpacking_scalar_generated_internal.h:34 LoadInt`; `...:5856 ScalarUnpackerForWidth`; `acero/hash_join_node_test.cc:571 GenRandomJoinTables`; `util/bit_block_counter_benchmark.cc:97 BenchBitmapReader` | external/async boundary, template support, or retained generated/SIMD code |
| random seed-6423 draw | `dataset/partition.h:101 Partitioning`; `compute/kernels/scalar_set_lookup.cc:163 UnsignedIntType`; `filesystem/azurefs.cc:551 Validate`; `dataset/file_csv.cc:342 GeneratorFromReader`; `util/compression_zlib.cc:106 GZipDecompressor`; `acero/tpch_node.cc:2349 L_COMMENT`; `compute/api_scalar.cc:260 EnumTraits`; `util/future_test.cc:1230 anonymous_struct_1230`; plus two test/vendored declarations | DIRECT_DSL through UNCERTAIN; confirms mixed concentration |

The sample validates the pattern but is not a successful-conversion sample.

## 6. Estimated Rusty-Safe Ratio

| Category | Units | LOC |
|---|---:|---:|
| DIRECT_DSL | 25–35% | 15–25% |
| REFACTOR_THEN_DSL | 15–25% | 10–18% |
| SAFE_WITH_SMALL_UNSAFE_CORE | 15–25% | 10–18% |
| REMAIN_CPP_UNSAFE | 15–25% | 30–45% |
| UNCERTAIN | 5–10% | 5–12% |

These ranges are ESTIMATED from the candidate LOC boundary, scanner signals, and manual sample. Conservative ratio counts only DIRECT_DSL. Practical ratio counts the first three categories but only safe portions of the third: **55–70% units / 35–50% LOC**. LOC is lower because representation kernels, generated code, and infrastructure types are disproportionately large.

## 7. Estimated Work

Meaningful evaluation: direct conversion 3–8 person-months; C++ preparation 2–6; unsafe isolation 2–5; RustyCpp/transpiler work 3–9; build integration 1–3; correctness 2–6; performance 1–3. Broad migration: roughly 12–30+, 8–24, 8–18, 12–36, 4–12, 10–24, and 6–15 person-months respectively. These are planning estimates, not measured human time.

## 8. Highest-Value Migration Areas

1. Buffer/BufferBuilder — ownership, slices, alignment; practical safe ratio 45–65%; VERY_HIGH work; **YES**.
2. ArrayData/typed arrays — buffer lifetimes and views; 40–60%; HIGH; **YES**.
3. Memory pools — allocator boundary; 25–45%; VERY_HIGH; **YES as boundary study**.
4. IPC reader/writer — zero-copy framing; 35–55%; VERY_HIGH; **YES**.
5. Scalar/type/schema — shared ownership/dispatch; 55–75%; HIGH; **YES**.
6. Selected compute scalar kernels — templates/SIMD; 30–50%; VERY_HIGH; **YES after core**.
7. Futures/thread pool — concurrent lifetimes; 25–45%; VERY_HIGH; **YES for research scope**.
8. Acero — execution concurrency; 20–40%; VERY_HIGH; later.

## 9. Likely Unsafe Boundaries

Allocator internals; raw bytes/alignment and pointer arithmetic; mmap/OS and filesystem/network APIs; compression/parser/C ABI calls; SIMD/intrinsics and generated packing; and concurrency primitives whose contracts are not expressible in current DSL form. Raw pointers elsewhere are often non-owning views or parameters and must be manually classified by lifetime contract.

## 10. Build/Test/Benchmark Feasibility

Arrow uses CMake. A minimal useful configuration is core + IPC + compute, tests and benchmarks enabled, optional compression/cloud/Flight/dataset disabled. Existing per-subsystem GTest targets and Google Benchmark targets are suitable for correctness and performance overhead; likely metrics are buffer slicing/allocation, array construction, IPC round trips, selected kernels, latency, throughput, CPU time, and peak memory.

Commands run (parallel build was not started):

```text
cmake -S cpp -B /tmp/arrow-cpp-feasibility-build -DCMAKE_BUILD_TYPE=Release -DARROW_BUILD_TESTS=ON -DARROW_BUILD_BENCHMARKS=ON -DARROW_BUILD_EXAMPLES=OFF -DARROW_COMPUTE=ON -DARROW_IPC=ON -DARROW_CSV=OFF -DARROW_JSON=OFF -DARROW_DATASET=OFF -DARROW_ACERO=OFF -DARROW_FLIGHT=OFF -DARROW_GANDIVA=OFF -DARROW_PARQUET=OFF -DARROW_WITH_ZLIB=OFF -DARROW_WITH_BROTLI=OFF -DARROW_WITH_LZ4=OFF -DARROW_WITH_SNAPPY=OFF -DARROW_WITH_ZSTD=OFF -DARROW_TESTING=ON
cmake -S cpp -B /tmp/arrow-cpp-feasibility-system -DCMAKE_BUILD_TYPE=Release -DARROW_DEPENDENCY_SOURCE=SYSTEM [same feature switches]
python3 -m inventory.inventory_v2 --root /home/frankw/projects/arrow --source-dir cpp/src/arrow --application arrow --application-commit 42694575d0219f6a3a78b1f344bb071a60df6a4e --output /tmp/arrow-inventory-2026-08-10 --sample-seed 6423
```

AUTO configure stopped while trying to source Boost; SYSTEM configure stopped because xsimd was unavailable. This is a measured environment limitation, not an Arrow source conclusion. No build/test result is claimed.

## 11. Proof-of-Concept Scope

Buffer/BufferBuilder, memory-pool interface-adjacent helpers, and selected array view/slice functions plus existing tests: **3–8k LOC / 30–80 functions**, estimated practical safe ratio 45–65%. It exercises ownership, zero-copy views, lifetimes, and byte boundaries without immediately taking on OS/network/template complexity.

## 12. Meaningful Evaluation Scope

PoC plus ArrayData/typed-array lifetime paths, scalar/type/schema utilities, IPC reader/writer, and selected compute scalar kernels: **35–60k LOC / 400–900 functions**, about 12–20% of candidate LOC, estimated practical safe ratio 35–55%. Boundaries: bytes/alignment, generated layouts, templates, SIMD, shared ownership.

## 13. Broad Migration Scope

Realistic broad target: **105–150k LOC / 1,500–3,000 units** (35–50% of candidate production LOC), with practical maximum safe ratio 35–50% LOC. Retain allocator/OS/ABI, generated/SIMD, external integrations, and concurrency-heavy cores. Broad work is worthwhile only after RustyCpp cross-TU, template, callback, concurrency, and boundary support matures.

## 14. Infrastructure Impact

**VERY_HIGH.** Arrow is foundational in-memory columnar/interchange infrastructure. Buffers, arrays, schema, IPC, and compute are reused by readers, writers, datasets, execution engines, and language bindings. They are central data/memory paths, so safety improvements would have broad reach; the same centrality makes ABI, layout, compatibility, and performance validation demanding.

## 15. Evidence, Assumptions, and Uncertainty

**MEASURED:** commits, file/LOC counts, lexical counts, v2 scanner output, configure failures. **MANUALLY VERIFIED:** representative Arrow locations, CMake switches, RustyCpp DSL/runtime docs and tests, and sample pattern. **ESTIMATED:** ratios, effort, scope sizes, ratings. **UNCERTAIN:** actual transpilation success for Arrow templates/macros, RustyCpp runtime ABI/layout compatibility, concurrency lowering, and generated-code treatment. The scanner is lexical and broader than the candidate filter; its 86.33% TRIVIAL bucket is not a migration-success percentage.

Pinned commits: Arrow `42694575d0219f6a3a78b1f344bb071a60df6a4e`; RustyCpp `488e422c293cdce3346f1ae3865ba588a74541e3`; rusty-eval `f7fae9732ede9a3569923e4a5984f4edaa9bb236`. AI-use record: `AI-2026-008`.

Apache Arrow C++:
- Relevant production LOC: 299,626 nonblank LOC
- Main subsystems: buffers/memory, arrays/types, compute, IPC, IO/filesystem, CSV/JSON, dataset, Acero, utilities
- Conservative Rusty-safe ratio: 25–35% units; 15–25% LOC
- Practical Rusty-safe ratio: 55–70% units; 35–50% LOC
- Expected work: high meaningful; very high broad
- Infrastructure impact: VERY_HIGH
- Main unsafe/boundary area: byte/allocator/OS/ABI/SIMD/generated/concurrency cores
- Best first subsystem: Buffer + BufferBuilder with array-view helpers
- Recommended meaningful migration size: 35–60k LOC / 400–900 functions
- Build/test quality: strong harnesses; configure blocked by missing Boost/xsimd here
- Overall doability: staged hybrid migration feasible; broad direct migration not demonstrated
