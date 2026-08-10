# Protocol Buffers C++ RustyCpp Feasibility Summary

Read-only research preflight. No Protobuf, RustyCpp, or rusty-eval source files were modified; no conversion, migration patch, build, or benchmark campaign was performed.

## Revisions

- Protobuf: `081ecdd861da4956522661e6a6ed54f8d33eb344`
- RustyCpp: `488e422c293cdce3346f1ae3865ba588a74541e3`
- rusty-eval: `00099c1a13b150fadbe66eb8b400dd94782c4c80`

## Measured scope

Hand-written C++ under `src/google/protobuf/`, excluding compiler code, tests, and generated `.pb.*` files:

- Runtime production: **197 files / 103,813 physical LOC**
- Runtime tests: **83 files / 74,287 LOC**
- Compiler production: **301 files / 89,896 LOC**
- Compiler tests: **39 files / 20,092 LOC**
- Benchmark-related files: **11 files / 3,252 LOC**
- Filtered scanner migration units: **2,223**
- Scanner declaration-span LOC: **20,494**

The scanner is lexical evidence, not a conversion-success predictor.

## Assessment

Protobuf is a credible RustyCpp target as a staged hybrid migration. Broad mechanical conversion is not demonstrated. Low-level unsafe operations are concentrated in Arena/allocation, layout, generated-message interfaces, reflection, extensions, and external IO, but their lifetime contracts propagate through messages, repeated fields, maps, and parsing.

Estimated Rusty-safe ratios:

| Estimate | Units | Physical LOC |
|---|---:|---:|
| Conservative; DIRECT_DSL only | 25–35% | 15–25% |
| Practical; refactoring plus isolated unsafe cores | 50–70% | 35–55% |

The remaining C++/`@unsafe` code is estimated at **25–45% of units / 35–60% of LOC**.

## Strongest targets

1. Repeated-field helpers
2. Parse-context and wire-format helpers
3. MessageLite construction/access helpers
4. Selected Arena lifetime-policy code around an unsafe allocator core
5. Micro-string and string-field helpers
6. JSON lexer/parser helpers

Recommended meaningful evaluation: **150–300 functions / 8,000–15,000 LOC**, covering repeated fields, MessageLite, parsing/wire format, selected Arena policy, strings, focused tests, and parse/serialize benchmarks.

## Arena finding

Arena lifetime relationships are a strong RustyCpp use case: an Arena owns blocks and cleanup records, while arena-allocated messages own or reference submessages, repeated storage, maps, and strings through the Arena lifetime. However, allocation itself uses `void*`, alignment, placement construction, custom allocator/deallocator callbacks, cleanup function pointers, and thread-safe atomic pointer tables. The likely design is safe lifetime/policy logic around a small C++/`@unsafe` allocation and layout boundary.

## Build and validation

CMake supports a minimal runtime build through `protobuf_BUILD_LIBPROTOBUF`, optional `libprotobuf-lite`, optional zlib, and separate test enablement through `protobuf_BUILD_TESTS`. Existing tests cover Arena, lite/full messages, parsing, wire format, reflection, descriptors, repeated fields, extensions, JSON, dynamic messages, and IO. Existing benchmarks cover Arena allocation, parsing, serialization, JSON, descriptor loading, and map probing.

## Compiler frontend

The compiler is separate: **301 production files / 89,896 LOC**. The common parser/importer/descriptor-related subset is approximately **19 files / 10,740 LOC**. Estimated safe ratio is **25–45% of units / 20–40% of LOC**, with HIGH work. It is worthwhile after the runtime, but must not be combined with runtime ratios.

## Provenance limitation

The existing rusty-eval AI-use procedure was inspected. Its required AI log and verbatim prompt record were not created because this evaluation was explicitly read-only and the original checkout was outside the writable workspace. The exact prompt remains in the supplied attachment.

## Project status

This status table surfaces the summary's existing assessment. Impact and
difficulty are qualitative estimates, and the finish level is a migration-scope
assessment rather than a delivery schedule or a measured conversion result.

| Dimension | Status | Evidence and limitation |
|---|---|---|
| Impact | **VERY_HIGH** | The runtime's Arena, messages, repeated fields, maps, parsing, reflection, and generated-runtime interfaces are foundational dependencies. |
| Difficulty | **HIGH** for the runtime; broader work remains unproven | Arena/allocation, layout, generated-message interfaces, reflection, extensions, and external IO have lifetime contracts that propagate across the runtime. |
| Expected finish level | **Staged hybrid runtime migration** | A 150–300-function meaningful evaluation is proposed. Broad mechanical conversion is not demonstrated; the compiler frontend is a separate later target and must not be combined with runtime estimates. |

## Final answer

- Overall doability: **YES**, as a staged hybrid migration
- Infrastructure impact: **VERY_HIGH**
- Main boundary: **Arena allocation/layout and generated-runtime interfaces**
- Best first subsystem: **Repeated fields plus parse-context/wire-format helpers**
- Meaningful evaluation size: **150–300 functions / 8,000–15,000 LOC**
- Compiler frontend after runtime: **YES**
