# Apache Thrift C++ manual inventory audit

This audit validates the generic summary runner and its frozen inventory-v2
classification as a lexical inventory, not as a proof of successful migration.

## Evaluated scope

- Repository: `https://github.com/apache/thrift.git`
- Commit: `9b10484ca7687af6cc67567df9d457d0f031748e`
- Intended implementation scope: `lib/cpp/src`
- Scanner methodology: v2
- AI-use record: `AI-2026-019`

The initial automatic-root run was rejected: it scanned unrelated compiler,
test, Lua, C GLib, and contributed code and reported 2,328/2,431 (95.76%)
functions in the migratable envelope. That is not a Thrift C++ core result.
The summary runner now rejects ambiguous source-root discovery and requires an
explicit `--source-dir` in this repository.

The corrected C++ core run reports 438/449 (97.55%) functions in the lexical
migratable envelope (`TRIVIAL` plus `REFACTOR_THEN_DSL`).

## Manual sample

| Scanner bucket | Function | Manual assessment | Result |
| --- | --- | --- | --- |
| TRIVIAL | `protocol/TVirtualProtocol.h:writeFieldEnd` | Throw-only protocol stub; no visible excluded feature. | Agree |
| TRIVIAL | `protocol/TProtocolTap.h:readI32` | Delegating protocol wrapper; no detected lexical blocker. | Agree, lexical only |
| TRIVIAL | `server/TNonblockingServer.h:setTaskExpireTime` | Simple setter. | Agree |
| TRIVIAL | `protocol/TProtocolTap.h:readStructEnd` | Delegating wrapper. | Agree, lexical only |
| TRIVIAL | `transport/TWebSocketServer.h:sendBadRequest` | HTTP/WebSocket response and transport writes put it at a networking boundary. | Disagree: semantic boundary missed |
| REFACTOR_THEN_DSL | `windows/GetTimeOfDay.cpp:thrift_gettimeofday` | Static local state; needs ownership/state reshaping. | Agree |
| REFACTOR_THEN_DSL | `transport/TBufferTransports.h:write` | Buffer pointer arithmetic and `memcpy`. | Agree |
| REFACTOR_THEN_DSL | `transport/TPipe.cpp:pseudo_sync_write` | Buffer clearing plus named-pipe implementation. | Partial: boundary evidence also needed |
| REFACTOR_THEN_DSL | `transport/TBufferTransports.h:initCommon` | Explicit `malloc`; refactor required. | Agree |
| REFACTOR_THEN_DSL | `transport/TWebSocketServer.h:writeFrameHeader` | `alloca`, pointer arithmetic, integer reinterpretation, and network framing. | Partial: boundary evidence also needed |
| NEEDS_TRANSPILER | `transport/TServerSocket.cpp:destroyer_of_fine_sockets` | Closes an OS socket and deletes a raw pointer. | Disagree: boundary is primary; function-pointer reason is not evident |
| NEEDS_TRANSPILER | `transport/TPipe.cpp:pipe_write` | Calls Windows `WriteFile` on a pipe. | Disagree: boundary is primary; callback reason is not evident |
| NEEDS_TRANSPILER | `VirtualProfiling.cpp:makePersistent` | Backtrace/profiling implementation with callback/function-pointer-related support. | Plausible; requires deeper semantic review |
| NEEDS_TRANSPILER | `transport/TPipe.cpp:pipe_read` | Calls Windows `ReadFile` on a pipe. | Disagree: boundary is primary |
| NEEDS_TRANSPILER | `TOutput.h:setOutputFunction` | Stores a function pointer. | Agree |

## Validation outcome

The generic runner correctly pins the commit, records its scope, emits
function-based results, and now prevents an ambiguous repository-wide scan.
The v2 scanner is suitable for a conservative *lexical evidence inventory*,
but this audit does **not** validate its function buckets as a semantic
migratability measure for networking middleware. It misses OS/network boundary
operations and can assign an unsupported primary reason. Therefore the 97.55%
figure must not be used to claim that Apache Thrift C++ meets an 80% migration
quota until a newer, separately versioned methodology adds semantic boundary
handling and is manually validated.
