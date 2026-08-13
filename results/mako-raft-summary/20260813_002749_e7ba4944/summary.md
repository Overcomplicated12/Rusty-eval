# Mako Raft Summary

Measured metrics; inventory estimates are not safety results.

```json
{
  "authored_nonblank_loc": 12201,
  "boundary_file_pct": 21.21212121212121,
  "boundary_files": 7,
  "boundary_function_pct": 4.956268221574344,
  "boundary_functions": 34,
  "cpp_explicit_unsafe_function_count": 0,
  "cpp_unverified_function_count": 230,
  "cpp_verified_safe_function_count": 0,
  "current_verified_safe_function_pct": 57.72594752186589,
  "direct_safe_envelope_functions": 646,
  "direct_safe_envelope_pct": 94.16909620991254,
  "dsl_authored_loc_pct": 22.440783542332596,
  "dsl_explicit_unsafe_function_count": 60,
  "dsl_function_count": 456,
  "dsl_function_pct": 66.47230320699708,
  "dsl_safe_function_count": 336,
  "excluded_files": [
    {
      "file": "src/deptran/raft/raft_lab_standalone.cc",
      "reason": "test-only or harness"
    },
    {
      "file": "src/deptran/raft/test.cc",
      "reason": "test-only or harness"
    },
    {
      "file": "src/deptran/raft/test.h",
      "reason": "test-only or harness"
    },
    {
      "file": "src/deptran/raft/test_cluster.hpp",
      "reason": "test-only or harness"
    },
    {
      "file": "src/deptran/raft/testconf.cc",
      "reason": "test-only or harness"
    },
    {
      "file": "src/deptran/raft/testconf.h",
      "reason": "test-only or harness"
    }
  ],
  "functions_total_logical": 686,
  "functions_verified_safe": 396,
  "generated_cpp_nonblank_loc": 2664,
  "handwritten_cpp_nonblank_loc": 9463,
  "included_files": [
    "src/deptran/raft/channel_transport.hpp",
    "src/deptran/raft/commo.cc",
    "src/deptran/raft/commo.h",
    "src/deptran/raft/coordinator.cc",
    "src/deptran/raft/coordinator.h",
    "src/deptran/raft/dispatcher.hpp",
    "src/deptran/raft/exec.cc",
    "src/deptran/raft/exec.h",
    "src/deptran/raft/file_snapshot_manager.hpp",
    "src/deptran/raft/frame.cc",
    "src/deptran/raft/frame.h",
    "src/deptran/raft/log_storage.hpp",
    "src/deptran/raft/macros.h",
    "src/deptran/raft/memory_log_storage.hpp",
    "src/deptran/raft/memory_snapshot_manager.hpp",
    "src/deptran/raft/messages.hpp",
    "src/deptran/raft/quorum.hpp",
    "src/deptran/raft/raft_node.hpp",
    "src/deptran/raft/raft_worker.cc",
    "src/deptran/raft/raft_worker.h",
    "src/deptran/raft/read_raft_disk.cc",
    "src/deptran/raft/recovery_manager.hpp",
    "src/deptran/raft/replicated_db.cc",
    "src/deptran/raft/replicated_db.h",
    "src/deptran/raft/rocksdb_log_storage.hpp",
    "src/deptran/raft/rrr_transport.hpp",
    "src/deptran/raft/server.cc",
    "src/deptran/raft/server.h",
    "src/deptran/raft/service.cc",
    "src/deptran/raft/service.h",
    "src/deptran/raft/snapshot_format.hpp",
    "src/deptran/raft/snapshot_manager.hpp",
    "src/deptran/raft/transport.hpp"
  ],
  "migration_counts": {
    "A_ALREADY_SAFE": 456,
    "B_DIRECT_MIGRATION": 190,
    "C_LOCAL_REFACTOR": 6,
    "D_BOUNDARY": 34
  },
  "potential_safe_envelope_functions": 652,
  "potential_safe_envelope_pct": 95.04373177842565,
  "repository": {
    "branch": "frank/raft-rustdsl",
    "dirty": false,
    "head_sha": "00e9c29d184e0d5d6c3c1f2e1bc5e78e0f00c133"
  },
  "rust_dsl_nonblank_loc": 2738,
  "schema_version": 1,
  "unknown_function_count": 0
}
```
