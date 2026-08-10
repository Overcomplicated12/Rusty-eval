# libzmq C++ RustyCpp Feasibility Summary

Read-only research preflight. No libzmq, RustyCpp, or rusty-eval source files were modified; no conversion, migration patch, build, or benchmark campaign was performed.

## Revisions

- libzmq: `46493370217ac135246617fa2f6ac819d8b61bfc`
- RustyCpp: `488e422c293cdce3346f1ae3865ba588a74541e3`
- rusty-eval: `00099c1a13b150fadbe66eb8b400dd94782c4c80`
- AI-use record: `AI-2026-009`

## Measured scope

The primary target is hand-written C++ under `src/`. External/vendor code, tests, and performance tools are reported separately. libzmq has no generated `.pb.*`-style production subsystem and no compiler frontend.

- Runtime production: **278 files / 50,681 physical LOC**
- Tests and test utilities: **150 files / 24,019 LOC**
- Performance tools: **8 files / 1,354 LOC**
- External/vendor C/C++: **7 files / 5,734 LOC**
- Filtered inventory declarations: **613 units**
- Scanner declaration-span LOC: **6,590**

The inventory scanner is lexical evidence, not a conversion-success predictor.

## Executive assessment

libzmq is a good RustyCpp research target, especially for evaluating ownership boundaries, message buffers, callback interfaces, lock-free queues, and C++/C interoperability. It is smaller than Protobuf and has a clear subsystem structure, but its difficult code is concentrated on the main performance and correctness paths rather than in an optional peripheral.

Estimated Rusty-safe ratios:

| Estimate | Units | Physical LOC |
|---|---:|---:|
| Conservative; DIRECT_DSL only | 30–45% | 20–30% |
| Practical; refactoring plus isolated unsafe cores | 55–70% | 40–55% |

The remaining C++/`@unsafe` code is estimated at **30–50% of units / 45–60% of LOC**. The scanner’s `TRIVIAL` bucket is 549/613 declarations, but that reflects many small declarations and does not account for the semantic difficulty of their containing classes, ownership protocols, or platform branches.

Overall doability is **YES as a staged hybrid migration** and **UNCERTAIN for broad safe migration** until RustyCpp support for atomics, callbacks, virtual interfaces, platform APIs, and cross-TU ownership contracts is demonstrated.

## Runtime structure

| Subsystem | Files | LOC | Purpose | Difficulty |
|---|---:|---:|---|---|
| Messaging/state machines | 82 | 18,090 | sockets, pipes, sessions, objects, routing, proxies | Very High |
| Transports | 48 | 8,055 | TCP, IPC, WebSocket, UDP, PGM, VMCI, TIPC, vsock | Very High |
| Codec/utility | 46 | 6,636 | messages, buffers, encoders/decoders, addresses, metadata | High |
| Other/core support | 47 | 9,072 | remaining protocol and library support | High |
| Polling/threading | 31 | 4,909 | pollers, mailboxes, atomics, threads, timers | Very High |
| Security | 24 | 3,919 | CURVE, PLAIN, GSSAPI, mechanisms, ZAP | Very High |

The grouping is filename-based and approximate. Many messaging files depend on transport, polling, and security interfaces.

## RustyCpp-relevant evidence

Measured lexical signals in `src/`:

- Raw-pointer parameters: **171 declarations**
- Raw-pointer returns: **40 declarations**
- `void*`: **105 declarations**
- C arrays: **31 declarations**
- Function pointers: **13 declarations**
- Pointer-to-pointer: **9 declarations**
- Unions: **11 declarations**
- `memcpy`: **20 declarations**
- `malloc`: **12 declarations**
- `free`: **8 declarations**
- Syscall/platform signals: **11 declarations**
- Pointer arithmetic: **4 declarations**

Source-level occurrence signals include 126 `reinterpret_cast` matches, 243 `memcpy` matches, 61 `memset` matches, 241 `new` matches, 44 `delete` matches, 118 `virtual` matches, and 730 thread-related matches. These are lexical counts, not semantic counts.

Important classifications:

| Feature | Classification |
|---|---|
| Pure codec, bounds checks, status/error helpers | DIRECT_DSL |
| `blob_t` ownership policy and message metadata | REFACTOR_THEN_DSL |
| Message copy/move/refcount logic | SAFE_WITH_SMALL_UNSAFE_CORE or REFACTOR_THEN_DSL |
| `void*` public C ABI and user deallocator callbacks | LIKELY_UNSAFE_BOUNDARY |
| `ypipe_t`, `atomic_ptr`, lock-free queue operations | NEEDS_RUSTYCPP_SUPPORT / likely unsafe core |
| `own_t` asynchronous ownership tree | REFACTOR_THEN_DSL, with lifetime redesign |
| Pollers, sockets, eventfds, epoll/kqueue/select | LIKELY_UNSAFE_BOUNDARY |
| Virtual engine/socket/pipe interfaces | NEEDS_RUSTYCPP_SUPPORT |
| CURVE/GSSAPI/libsodium/OpenPGM/NORM | LIKELY_UNSAFE_BOUNDARY or UNCERTAIN |
| Platform conditional compilation | NEEDS_RUSTYCPP_SUPPORT / UNCERTAIN |

RustyCpp documentation and tests provide evidence for `Box`, `Rc`, `Arc`, `Cell`, `RefCell`, `Vec`, `Option`, `Result`, slices, closures, iterators, templates, safe/unsafe blocks, RAII, and pointer provenance. The current model treats unannotated functions as unsafe and generally requires explicit unsafe blocks for external/STL calls. Current support remains uncertain for libzmq’s platform atomics, C function-pointer callbacks, virtual interface graph, inline assembly, and OS socket APIs.

## Ownership and lifetime analysis

libzmq has several ownership models rather than one arena-style model:

1. `msg_t::content_t` owns or shares message storage through a reference count and may invoke a user-supplied `msg_free_fn`.
2. `blob_t` owns malloc’ed bytes or temporarily references external storage through `reference_tag_t`; its comments explicitly require the referenced storage to outlive the blob.
3. `own_t` maintains an asynchronous parent/child ownership hierarchy and termination acknowledgements.
4. `pipe_t` transfers messages between threads through queue and pipe protocols.
5. `ypipe_t` and `atomic_ptr` implement lock-free or atomic pointer transitions with platform-specific implementations.

The strongest RustyCpp opportunity is making these relationships explicit at API boundaries: owned message buffers versus borrowed buffers, ownership transfer on send/move, and parent/child termination lifetimes. The likely unsafe core includes malloc/free, arbitrary user callbacks, raw socket handles, atomic pointer CAS, inline assembly, and platform synchronization.

## Representative deterministic sample

Seed: `6423`. The scanner sample was manually checked against source patterns.

| Group | Representative declarations |
|---|---|
| Easy | `mechanism.cpp:97 value_len_size`; `mutex.hpp:59 try_lock`; `stream_engine_base.cpp:47 if`; `proxy.cpp:77 stats_socket`; `address.cpp:65 if`; `i_engine.hpp:15 i_engine`; `proxy.cpp:85 stats_proxy`; `select.hpp:57 fds_set_t`; `msg.hpp:152 anonymous_enum_152`; `pipe.cpp:23 upipe_conflate_t` |
| Medium | `blob.hpp:46 blob_t`; `zmq.cpp:440 zmq_sendiov`; `zmq_utils.cpp:32 zmq_stopwatch_start`; `zmq.cpp:543 zmq_recviov`; `norm_engine.cpp:814 normWrapperThread`; `blob.hpp:100 set_deep_copy`; `compat.hpp:29 strcpy_s`; `ws_engine.cpp:990 encode_base64`; `pgm_receiver.hpp:75 tsi_comp`; `radix_tree.cpp:162 free_nodes` |
| Hard | `ypipe.hpp:142 probe`; `command.hpp:52 args_t`; `generic_mtrie.hpp:75 _next_t`; `ip_resolver.hpp:16 ip_addr_t`; `address.hpp:70 address_t`; `ip.cpp:177 anonymous_union_177`; `condition_variable.hpp:79 wait`; `msg.hpp:223 anonymous_union_223`; `dbuffer.hpp:89 probe`; `polling_util.hpp:57 resize` |
| Random | `ws_decoder.hpp:26 msg`; `socket_poller.hpp:84 is_socket`; `curve_mechanism_base.cpp:70 nonce_prefix_len`; `v2_decoder.hpp:22 msg`; `proxy.cpp:90 forward`; `condition_variable.hpp:26 broadcast`; `compat.hpp:17 strlcpy`; `command.hpp:172 anonymous_struct_172`; `decoder_allocators.hpp:19 c_single_allocator`; `radix_tree.cpp:162 free_nodes` |

This sample shows that apparently simple helpers are abundant, but the hard units sit on central message, queue, poller, and platform paths.

## Estimated work

Meaningful research evaluation, estimated:

- Direct DSL conversion: **2–5 person-months**
- C++ API/lifetime refactoring: **2–5**
- Unsafe-boundary isolation: **2–5**
- RustyCpp/transpiler changes: **3–8**
- Build integration: **1–2**
- Correctness validation: **2–4**
- Performance validation: **1–3**

Broad migration is likely **HIGH to VERY_HIGH**, approximately **12–30 person-months**, because the central transport and concurrency graph must remain behaviorally compatible.

## Highest-value migration targets

| Rank | Area | Expected practical safe ratio | Work | Impact | Recommended |
|---:|---|---:|---|---|---|
| 1 | `blob_t` and pure message-buffer helpers | 45–65% | Medium–High | High | Yes |
| 2 | Z85/base85 and codec utilities | 65–85% | Low–Medium | Medium | Yes |
| 3 | Message copy/move/refcount policy | 35–55% | High | Very High | Yes, staged |
| 4 | `own_t` ownership/termination policy | 30–50% | High | Very High | Yes, after PoC |
| 5 | `ypipe`/pipe surrounding logic | 20–40% | Very High | Very High | Later |
| 6 | Polling abstraction policy | 25–45% | High | High | Later |
| 7 | Radix tree/trie algorithms | 45–65% | Medium–High | High | Yes |
| 8 | Transport framing/state logic | 25–45% | Very High | Very High | Later |
| 9 | Security mechanism policy | 20–40% | Very High | High | Later |

## Migration scopes

### Proof of concept

Recommended: Z85/base85 utilities, selected metadata/options helpers, non-owning message inspection, and a small `blob_t` ownership wrapper.

- **25–50 functions / 500–1,500 LOC**
- Expected practical safe ratio: **60–80%**
- Boundary: malloc/free and borrowed external buffers
- Difficulty: **Medium**

### Meaningful research evaluation

Recommended: message buffer lifecycle, `blob_t`, selected `msg_t` copy/move/refcount functions, radix-tree operations, selected `own_t` policy, and focused inproc/pipe tests.

- **100–200 functions / 8,000–12,000 LOC**
- Approximately **16–24% of runtime LOC**
- Expected practical safe ratio: **40–60%**
- Major blockers: user callbacks, atomic queue operations, virtual interfaces, and generated/platform configuration

### Broad migration

A broad hybrid migration might plausibly express **40–55% of runtime LOC** and **55–70% of units** after refactoring. Central atomics, socket/poller calls, platform transports, C ABI functions, external security libraries, and portions of the ownership graph would likely remain C++/`@unsafe`.

## Tests, benchmarks, and build feasibility

CMake builds `libzmq` as shared and/or static libraries. Tests are controlled by `ZMQ_BUILD_TESTS`/`BUILD_TESTS` and cover inproc, TCP, IPC, transports, sockets, messages, routing, security, shutdown, polling, timers, threading, fuzzers, and platform-specific behavior. The test suite is broad and directly useful for later original-versus-RustyCpp correctness comparisons.

Performance tools are enabled through `WITH_PERF_TOOL` and include local/remote throughput and latency, inproc latency/throughput, proxy throughput, and radix-tree benchmarking. Later comparisons should measure:

- Message send/receive throughput
- Inproc and TCP latency
- Allocations and bytes per message
- Message copy/move/refcount cost
- Pipe/queue throughput
- Poller wakeup latency
- Context/socket creation and termination
- CPU time, peak memory, and tail latency

No build was run in this preflight. A minimal later build should disable optional transports/security integrations, build static `libzmq`, enable focused tests, and use at most `-j6`; test execution should use at most `-j4`.

## Infrastructure impact

**HIGH to VERY_HIGH.** libzmq is a foundational messaging library with a public C ABI and many downstream applications. Message ownership, socket state machines, queues, pollers, and transports lie directly beneath common send/receive paths. A partial migration of message and ownership layers would have broad safety value, but mistakes in concurrency or lifetime behavior would affect correctness and liveness system-wide.

## Evidence and uncertainty

- **MEASURED:** revisions, file/LOC counts, scanner declarations, lexical feature signals, test/performance inventories, and CMake options.
- **MANUALLY VERIFIED:** `msg_t`, `blob_t`, `own_t`, `ypipe_t`, `atomic_ptr`, condition variables, C ABI functions, and representative scanner samples.
- **ESTIMATED:** safe ratios, work, migration scopes, and impact ratings.
- **UNCERTAIN:** exact inline-DSL success for virtual interfaces, atomic pointer implementations, platform branches, callbacks, and external security/socket APIs.
- Raw pointers were treated as evidence requiring review, not automatic proof of unsafety.

## Project status

This status table surfaces the summary's existing assessment. Impact and
difficulty are qualitative estimates, and the finish level is a migration-scope
assessment rather than a delivery schedule or a measured conversion result.

| Dimension | Status | Evidence and limitation |
|---|---|---|
| Impact | **HIGH to VERY_HIGH** | The public C ABI, message ownership, socket state machines, queues, pollers, and transports sit on common send/receive paths. |
| Difficulty | **HIGH to VERY_HIGH** | The central correctness and performance paths include message buffers, lock-free queues, pollers, transports, C callbacks, ownership protocols, and platform branches. |
| Expected finish level | **Staged hybrid migration** | The report supports a smaller meaningful evaluation first; broad safe migration remains uncertain until atomics, callbacks, virtual interfaces, platform APIs, and cross-translation-unit ownership contracts are demonstrated. |

## Final summary

- Relevant production LOC: **50,681**
- Migration units: **613 scanner units**
- Conservative Rusty-safe ratio: **30–45% units / 20–30% LOC**
- Practical Rusty-safe ratio: **55–70% units / 40–55% LOC**
- Expected work: **HIGH; 12–30 person-months for broad migration, with a smaller meaningful evaluation first**
- Infrastructure impact: **HIGH to VERY_HIGH**
- Main unsafe/boundary area: **message buffers, lock-free queues, pollers, transports, and C callbacks**
- Best first subsystem: **codec/message-buffer helpers, followed by selected ownership policy**
- Recommended meaningful migration size: **100–200 functions / 8,000–12,000 LOC**
- Build/test quality: **broad and highly useful; performance tools are available**
- Overall doability: **YES as a staged hybrid; broad safe migration remains uncertain**
