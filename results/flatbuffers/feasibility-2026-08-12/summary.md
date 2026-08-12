# FlatBuffers C++ RustyCpp Feasibility Summary

Read-only feasibility preflight. No FlatBuffers or RustyCpp files were modified; no conversion, migration patch, build, test, or benchmark campaign was performed. This is technical evidence and estimates, not a research conclusion.

## Revisions and method

- FlatBuffers: `5761d6e67af841d15ee21bc1ce9a78ffa9cf939e`
- RustyCpp: `488e422c293cdce3346f1ae3865ba588a74541e3`
- rusty-eval: `a9fba7cfa55337bdd056dfd3a17c15ee5ec21bde`
- AI-use record: `AI-2026-015`
- Inventory: frozen lexical methodology v2, deterministic seed `6423`

Commands were run read-only against the target (scanner outputs were written only beneath `/tmp`):

```text
python3 -m src.inventory.inventory_v2 --root /tmp/flatbuffers-runtime-scope-20260812 --source-dir src --application flatbuffers-runtime --application-commit 5761d6e67af841d15ee21bc1ce9a78ffa9cf939e --output /tmp/flatbuffers-inventory-runtime --sample-seed 6423
python3 -m src.inventory.inventory_v2 --root /home/frankw/projects/flatbuffers --source-dir src --application flatbuffers-compiler --application-commit 5761d6e67af841d15ee21bc1ce9a78ffa9cf939e --output /tmp/flatbuffers-inventory-src --sample-seed 6423
```

The runtime scanner staging directory contains the 24 non-generated, non-compiler-oriented public headers plus `src/reflection.cpp` and `src/util.cpp`. It excludes `reflection_generated.h`, parser/compiler headers, and `flatc` support. The scanner is lexical evidence, not a conversion-success predictor.

## Executive summary

**MEASURED:** the scoped C++ runtime is **26 files / 10,859 physical LOC**: 24 public runtime headers / 9,564 LOC, plus reflection and utility implementation files / 1,295 LOC. The C++ tests are **47,592 LOC** and C++ benchmarks are **653 LOC**. The separately measured compiler source directory is **55 files / 43,313 LOC**; it includes the runtime/compiler shared sources.

**ESTIMATED:** FlatBuffers is a credible staged RustyCpp target, but it is less like an ordinary container library than its small size suggests. Its central API interprets arbitrary byte buffers as `Table`, `Vector`, `String`, and generated types through pointer arithmetic and `reinterpret_cast`. The builder has a reverse-growing raw allocation with alignment, relocation, vtable de-duplication, and ownership transfer. These are intentional low-level format operations, not incidental cleanup candidates.

| Estimate | Migration units | Physical runtime LOC |
|---|---:|---:|
| Conservative Rusty-safe ratio; DIRECT_DSL only | 30–45% | 20–35% |
| Practical ratio; refactoring plus narrow unsafe layout core | 55–70% | 40–55% |
| Remain C++ / `@unsafe` / uncertain layout boundary | 30–50% | 45–60% |

The v2 inventory reports 516/556 declarations as `TRIVIAL` (84.7% declaration-span LOC). This is **not** a safe-ratio estimate: many short accessors inherit the serialized-buffer layout and lifetime contracts of their surrounding types. The estimates above discount that scanner bucket accordingly.

Overall doability is **YES as a staged hybrid migration**. A broad all-safe conversion is **UNCERTAIN** until RustyCpp demonstrates compatible expression of layout-sensitive generic APIs, generated C++ interfaces, and cross-translation-unit borrowing over caller-owned buffers.

## Runtime structure

| Subsystem | Files / LOC | Purpose | Difficulty |
|---|---:|---|---|
| Core format views | 8 / ~2,450 | scalar/endian helpers; `Table`, `Vector`, `String`, `Offset`, struct access | High |
| Builder and storage | 6 / ~2,550 | reverse-growing buffer, allocator, detached ownership, vtables | Very High |
| Verification | 1 / 370 | bounds, alignment, nesting and table-count checks | High |
| FlexBuffers | 2 / ~2,150 | dynamic schema-less binary format and builder | High |
| Reflection and mini-reflection | 3 / ~1,520 | schema-driven inspection and mutation | Very High |
| Utility / API integration | 6 / ~1,820 | hashes, STL emulation, registry, gRPC, utilities | Medium–High |

The figures are approximate filename-based allocations and overlap through shared headers. Generated `reflection_generated.h` (1,541 LOC), compiler/parser APIs, and third-party dependencies are excluded from the runtime estimate.

## RustyCpp-relevant feature evidence

**MEASURED:** v2 inventory of the scoped runtime found 556 declarations / 4,058 declaration-span LOC: 516 `TRIVIAL`, 18 `REFACTOR_THEN_DSL`, 21 `NEEDS_TRANSPILER`, one ABI `BOUNDARY`, and no `UNKNOWN`. Lexical signals include 192 raw-pointer parameters, 17 `void *` occurrences, 12 pointer-to-pointer cases, 15 function-pointer cases, 8 bitfields, 5 unions, 6 `memcpy`, 2 `memset`, 2 pointer-arithmetic cases, 60 macro-use signals, and 528 declarations under conditional compilation. Counts are declaration-local signals, not unique bugs or proof of unsafety.

**MANUALLY VERIFIED:**

| Area | Evidence | Classification |
|---|---|---|
| `Table`, `Vector`, `String`, `IndirectHelper` | typed reads are formed from bytes using offsets, pointer arithmetic, and `reinterpret_cast` | SAFE_WITH_SMALL_UNSAFE_CORE / NEEDS_RUSTYCPP_SUPPORT |
| `VerifierTemplate` | checks bounds, alignment, depth, table count and nested offsets before typed access | REFACTOR_THEN_DSL with a small raw-buffer boundary |
| `vector_downward` | owns a reverse-growing allocation with `buf_`, `cur_`, scratch region, relocation, and raw release | REFACTOR_THEN_DSL plus unsafe allocation/layout core |
| `FlatBufferBuilderImpl` | alignment, vtable construction/de-duplication, typed writes to byte storage, generated-code callbacks | SAFE_WITH_SMALL_UNSAFE_CORE |
| `Allocator` / `DetachedBuffer` | virtual allocator interface; explicit `own_allocator_`; raw pointer release and destructor deallocation | LIKELY_UNSAFE_BOUNDARY / REFACTOR_THEN_DSL |
| FlexBuffers and reflection mutation | parsing/mutation over in-place buffers and type-erased data | REFACTOR_THEN_DSL / NEEDS_RUSTYCPP_SUPPORT |
| gRPC and file-system integration | externally owned gRPC slices and OS/file callbacks | LIKELY_UNSAFE_BOUNDARY |

**UNCERTAIN:** current RustyCpp evidence supports `Box`, `Rc`, `Arc`, `Cell`, `RefCell`, `Vec`, `Option`, `Result`, slices, closures, iterators, generic/template forms, RAII, explicit safe/unsafe blocks, and pointer provenance. Exact success remains unproven for FlatBuffers’ template-heavy generated API surface, virtual `Allocator`, layout-punned zero-copy views, byte-buffer type reconstruction, and all public ABI compatibility. These are marked uncertain rather than unsupported.

## Ownership and layout analysis

FlatBuffers has no Arena. Its main lifetime model is:

```text
caller-owned byte buffer ──borrowed by──> Table / Vector / String views
FlatBufferBuilder ──owns──> vector_downward allocation ──released as──> DetachedBuffer
Allocator (optionally owned) ──allocates/deallocates──> builder storage
```

The builder-to-`DetachedBuffer` transfer is a particularly relevant RustyCpp case: `vector_downward::release()` transfers the allocator, ownership flag, allocation base, cursor, and size, and clears the builder's ownership. That policy can plausibly become explicit owned-state logic. The allocation, deallocation, reallocation-downward copy, alignment, and raw-byte cast operations should remain a narrow unsafe core.

Read-side views are different: a `Table` is effectively a typed façade over untyped external bytes. RustyCpp could express the buffer borrow and make validated versus unvalidated views distinct, but the offset calculation and conversion from byte address to a typed view remain format/layout-sensitive. Thus unsafe work is concentrated in several primitives, but their contracts are used throughout generated accessors.

## Representative manual validation sample

Seed `6423` was used for the scanner sample. The following declarations were checked against their source context; the sample deliberately includes easy, refactor, hard, and random/representative central units.

| Group | Declaration | Classification | Reason |
|---|---|---|---|
| Easy | `array.h:117 MutateImpl` | DIRECT_DSL | bounded element mutation wrapper |
| Easy | `base.h:360 VerifyAlignmentRequirements` | DIRECT_DSL | arithmetic validation policy |
| Easy | `flexbuffers.h:1240 StartVector` | REFACTOR_THEN_DSL | builder state but no direct allocation primitive |
| Easy | `flatbuffer_builder.h:300 PushBytes` | SAFE_WITH_SMALL_UNSAFE_CORE | simple forwarding to raw storage |
| Easy | `minireflect.h:60 Double` | DIRECT_DSL | scalar metadata helper |
| Medium | `vector_downward.h:200 push` | REFACTOR_THEN_DSL | buffer growth and byte copy preconditions |
| Medium | `vector_downward.h:229 fill_big` | SAFE_WITH_SMALL_UNSAFE_CORE | memset contained behind storage API |
| Medium | `buffer_ref.h:31 BufferRef` | REFACTOR_THEN_DSL | borrowed/owned buffer state needs explicit lifetime |
| Medium | `reflection.cpp:592 SetString` | REFACTOR_THEN_DSL | in-place resize and mutation over verified buffer |
| Medium | `flexbuffers.h:804 MutateString` | REFACTOR_THEN_DSL | dynamic format mutation |
| Hard | `allocator.h:31 Allocator` | LIKELY_UNSAFE_BOUNDARY | virtual raw allocation/deallocation/reallocation contract |
| Hard | `vector_downward.h:96 release` | REFACTOR_THEN_DSL | ownership transfer of allocator and byte allocation |
| Hard | `vector_downward.h:278 reallocate` | SAFE_WITH_SMALL_UNSAFE_CORE | relocation, alignment and pointer recomputation |
| Hard | `flatbuffer_builder.h:429 EndTable` | SAFE_WITH_SMALL_UNSAFE_CORE | vtable layout, byte writes, pointer reinterprets |
| Hard | `table.h:45 GetPointer` | LIKELY_UNSAFE_BOUNDARY | raw offset dereference forms typed pointer |
| Hard | `verifier.h:119 VerifyTable` | NEEDS_RUSTYCPP_SUPPORT | generic generated `Verify` dispatch over borrowed bytes |
| Hard | `verifier.h:203 VerifyBufferFromStart` | SAFE_WITH_SMALL_UNSAFE_CORE | validates then casts root bytes to generated type |
| Hard | `base.h:398/402` unions | NEEDS_RUSTYCPP_SUPPORT | endian/layout-sensitive scalar implementation |
| Random | `hash.h:56 HashFnv1a` | DIRECT_DSL | pure byte iteration, subject to slice representation |
| Random | `util.h:292 StringToIntegerImpl` | REFACTOR_THEN_DSL | C parsing/locale boundary |

This confirms the scanner's useful finding—many small helpers are simple—but also why its `TRIVIAL` rate overstates whole-subsystem safe conversion.

## Work and migration scopes

**ESTIMATED work by activity:** direct DSL conversion 1–3 person-months; C++ API/lifetime reshaping 2–5; unsafe-boundary isolation 2–4; RustyCpp/transpiler support 2–6; build integration 1–2; correctness validation 2–4; performance validation 1–3. A broad hybrid migration is **10–22 person-months**, with much of the uncertainty due to RustyCpp’s ability to preserve C++ generated-code compatibility rather than total LOC.

| Scope | Recommended content | Size | Expected practical safe ratio | Difficulty |
|---|---|---:|---:|---|
| Proof of concept | hash/scalar utilities, selected verifier policy, `DetachedBuffer` ownership wrapper | 30–60 functions / 800–1,500 LOC | 60–80% | Medium |
| Meaningful evaluation | verifier, builder policy, `vector_downward` ownership transfer, core table/vector access wrappers, focused generated-message tests | 100–180 functions / 4,000–6,000 LOC | 45–65% | High |
| Broad migration | public runtime and selected reflection/FlexBuffers policy while retaining low-level layout core | ~6,000–8,000 LOC plausibly hybrid-migratable | 40–55% LOC | Very High |

The best first subsystem is **validated read-side access plus `DetachedBuffer`/builder ownership policy**, not a wholesale `FlatBufferBuilder` conversion. This tests borrowed-buffer lifetimes, validation boundaries, and transfer of allocation ownership while limiting initial layout-sensitive code.

## Compiler frontend assessment

**MEASURED:** `src/` has 55 C++ files / 43,313 LOC. Its v2 inventory has 528 declarations / 15,888 declaration-span LOC: 460 `TRIVIAL`, nine `REFACTOR_THEN_DSL`, 59 `NEEDS_TRANSPILER`, and no boundary/unknown records. This scope contains all language generators, so it is not comparable to the runtime scanner nor included in runtime ratios.

The common parser/importer path is centered on `idl_parser.cpp` (4,621 LOC), `idl.h`, `flatc.cpp` (1,121), and generator registration/support. It is less raw-memory-intensive than the runtime but uses a large graph of schema definitions, `std::unique_ptr`, callbacks, templates, code-generation strings, and compiler options.

**ESTIMATED:** 45–60% of compiler units / 35–50% of compiler LOC could become Rusty-safe in a staged effort, with **HIGH** work. It is worth evaluating **after** the runtime only if RustyCpp has demonstrated sufficient support for its polymorphic generators and template/callback forms. It is not the better first FlatBuffers target.

## Build, tests, benchmarks, and impact

**MEASURED:** CMake offers `FLATBUFFERS_BUILD_FLATLIB`, `FLATBUFFERS_BUILD_FLATC`, `FLATBUFFERS_BUILD_TESTS`, `FLATBUFFERS_BUILD_BENCHMARKS`, and optional `FLATBUFFERS_BUILD_GRPCTEST`. `flattests` combines the runtime with generated schemas and tests parsing, JSON, fuzzing, FlexBuffers, mutations, vectors, defaults, evolution, and object APIs. `flatbenchmark` is available under `benchmarks/cpp`.

No build was run. A later minimal comparison should build the static library and `flattests`, use at most `-j6` for builds and `-j4` for tests, and compare verifier throughput, buffer construction/finish throughput, parsing/access throughput, allocation/reallocation counts, peak memory, serialized output identity, and latency.

Infrastructure impact is **HIGH**: FlatBuffers' C++ headers are consumed directly by generated C++ code and applications, while builders, format views, verification, and buffer ownership sit on common serialization/deserialization paths. This also raises compatibility risk because these APIs are header-only and template-heavy.

## Evidence and uncertainty

- **MEASURED:** revisions; LOC/file counts; scanner output; lexical feature counts; CMake targets; test and benchmark inventories.
- **MANUALLY VERIFIED:** allocator, `vector_downward`, `DetachedBuffer`, builder table completion, `Table` pointer access, `VerifierTemplate`, and the sampled declarations listed above.
- **ESTIMATED:** migration ratios, work, scopes, subsystem difficulty, and impact.
- **UNCERTAIN:** transpilation of public templates, virtual allocators, generated API calls, layout-sensitive type reconstruction, and cross-TU borrowing contracts.

Raw pointers are evidence for review, not automatic proof that a unit is unsafe or unmigratable.

## Final summary

FlatBuffers C++ runtime:

- Relevant production LOC: **10,859**
- Migration units: **556 scanner units / 4,058 declaration-span LOC**
- Conservative Rusty-safe ratio: **30–45% units / 20–35% LOC**
- Practical Rusty-safe ratio: **55–70% units / 40–55% LOC**
- Expected work: **HIGH; 10–22 person-months for broad hybrid migration**
- Infrastructure impact: **HIGH**
- Main unsafe/boundary area: **serialized byte-layout views, reverse-growing builder storage, allocator transfer, and generated C++ interfaces**
- Best first subsystem: **validated views plus `DetachedBuffer`/builder ownership policy**
- Recommended meaningful migration size: **100–180 functions / 4,000–6,000 LOC**
- Build/test quality: **broad CMake tests and focused C++ benchmarks are available**
- Overall doability: **YES as a staged hybrid; broad all-safe migration remains uncertain**

FlatBuffers compiler frontend:

- Relevant LOC: **43,313 source-directory LOC (shared runtime sources included)**
- Expected Rusty-safe ratio: **45–60% units / 35–50% LOC**
- Expected work: **HIGH**
- Worth evaluating after runtime: **MAYBE**
