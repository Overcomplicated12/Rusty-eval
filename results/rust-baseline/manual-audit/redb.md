# Manual audit: redb explicit unsafe usage

This is an independent source audit of `redb` at `dea77f0f0653c69aba3487846589ec7e77ceb5a1`. It does not modify the scanner or the target repository.

## Scope and method

`cargo metadata --format-version 1 --no-deps` identifies the configured `redb` package's sole production target as the library rooted at `src/lib.rs`. I audited its reachable `src/**/*.rs` source tree, excluding repository `tests/`, examples, benches, fuzz targets, sibling workspace packages, `build.rs`, and items/modules under `#[cfg(test)]` or `#[test]`.

The source has 44 Rust files and 31,599 physical source lines before removing inline test regions. A manual declaration pass that strips comments/strings and excludes the verified test regions found **1,547 production function/method declarations**. This count is an audit denominator, not a claim about compiled functions after macro expansion.

The unsafe inventory below is source-level: it includes target-conditional production code and flags it. The `sync::spin` module is `#[cfg(any(redb_no_std, test))]`; its entries are not active in the configured ordinary default build, but may be production code in a `redb_no_std` build. The two WASI I/O helpers and architecture-specific SIMD functions are likewise conditional. No conclusion is inferred for an unconfigured target.

## Manual counts

| Metric | Manual source-level value | Notes |
|---|---:|---|
| production_files | 44 | package `redb` library source only |
| functions_total | 1,547 | excludes verified inline test items |
| functions_unsafe_declared | 9 | all in `xxh3.rs`; target-conditional |
| functions_with_unsafe_block | 21 | 16 safe-declared functions plus five unsafe-declared functions with blocks |
| functions_unsafe_any | 25 | union: 9 declared-unsafe functions plus 16 safe-declared functions with blocks |
| unsafe_blocks | 24 | explicit lexical `unsafe {}` blocks |
| files_with_unsafe | 5 | includes cfg-controlled production-source files |
| unsafe_impl_count | 5 | all in cfg-controlled `sync::spin` |
| unsafe_trait_count | 0 | none found |
| manual_unsafe_region_loc | 177 | union of explicit unsafe-block source-line ranges; nested/overlapping lines counted once |

For the current normal non-WASI, non-`redb_no_std` source configuration on an x86/x86_64 target, the active subset is lower (13 unsafe blocks across three files; 14 functions with any explicit unsafe involvement; 105 unsafe-block-region lines). That target-specific subset is informative but is **not** substituted for the source-level count above because the requested automated result is a source scan.

## Unsafe-containing production files

| File | Explicit unsafe blocks | Unsafe declarations | Unsafe impls | Conditional status |
|---|---:|---:|---:|---|
| `src/transactions.rs` | 1 | 0 | 0 | unconditional |
| `src/tree_store/multimap_btree.rs` | 2 | 0 | 0 | unconditional |
| `src/sync.rs` | 5 | 0 | 5 | `redb_no_std` (or tests; test-only portion excluded) |
| `src/tree_store/page_store/xxh3.rs` | 14 | 9 | 0 | architecture conditional except generic callers |
| `src/tree_store/page_store/file_backend/optimized.rs` | 2 | 0 | 0 | WASI only |

No `unsafe trait` or `unsafe extern` declaration was found in package production source. `unsafe fn(...)` function-pointer parameter types in `xxh3.rs` are not declarations and are not counted as unsafe functions.

## Functions with explicit unsafe involvement

Every function/method in an unsafe-containing file was inspected. The following are the only functions with an explicit unsafe declaration or block. Line ranges are inclusive.

| File and qualified function | Function lines | Declared unsafe | Unsafe blocks / lines | Factual operation |
|---|---:|---|---|---|
| `transactions.rs` — `impl MutInPlaceValue for PageList::from_bytes_mut` | 138–140 | no | 1: 139–139 | casts a mutable byte slice pointer to `PageListMut` and dereferences it |
| `multimap_btree.rs` — `DynamicCollection::new` | 523–525 | no | 1: 524–524 | casts a byte-slice reference to a dynamically sized `DynamicCollection<V>` reference |
| `multimap_btree.rs` — `UntypedDynamicCollection::new` | 600–602 | no | 1: 601–601 | casts a byte-slice reference to an `UntypedDynamicCollection` reference |
| `sync.rs` — `spin::MutexGuard::deref` | 147–150 | no | 1: 149–149 | dereferences `UnsafeCell` data behind a mutex guard |
| `sync.rs` — `spin::MutexGuard::deref_mut` | 154–157 | no | 1: 156–156 | mutably dereferences `UnsafeCell` data behind a mutex guard |
| `sync.rs` — `spin::RwLockReadGuard::deref` | 251–254 | no | 1: 253–253 | dereferences `UnsafeCell` data behind a read guard |
| `sync.rs` — `spin::RwLockWriteGuard::deref` | 270–273 | no | 1: 272–272 | dereferences `UnsafeCell` data behind a write guard |
| `sync.rs` — `spin::RwLockWriteGuard::deref_mut` | 276–280 | no | 1: 279–279 | mutably dereferences `UnsafeCell` data behind a write guard |
| `xxh3.rs` — `hash64_with_seed` | 59–84 | no | 2: 66–68, 73–73 | calls target-feature SIMD hash functions |
| `xxh3.rs` — `hash128_with_seed` | 86–109 | no | 2: 92–94, 97–99 | calls target-feature SIMD hash functions |
| `xxh3.rs` — `scramble_accumulators_avx2` | 162–193 | yes | 1: 166–192 | executes AVX2 intrinsics and raw-pointer SIMD loads/stores |
| `xxh3.rs` — `scramble_accumulators_neon` | 196–230 | yes | 1: 205–228 | executes NEON intrinsics and raw-pointer vector loads/stores |
| `xxh3.rs` — `gen_secret_avx2` | 294–319 | yes | 1: 295–318 | executes AVX2 intrinsics and raw-pointer SIMD loads/stores |
| `xxh3.rs` — `accumulate_stripe_neon` | 322–351 | yes | 1: 328–350 | executes NEON intrinsics and raw-pointer vector loads/stores |
| `xxh3.rs` — `accumulate_stripe_avx2` | 355–384 | yes | 1: 356–383 | executes AVX2 intrinsics and raw-pointer SIMD loads/stores |
| `xxh3.rs` — `accumulate_block` | 398–414 | no | 1: 406–412 | invokes an unsafe function pointer for one stripe |
| `xxh3.rs` — `hash_large_helper` | 417–460 | no | 2: 438–438, 452–458 | invokes unsafe scramble/accumulate function pointers |
| `xxh3.rs` — `hash64_large_neon` | 563–571 | yes | 0 | unsafe target-feature dispatch wrapper; body has no explicit block |
| `xxh3.rs` — `hash64_large_avx2` | 575–583 | yes | 0 | unsafe target-feature dispatch wrapper; body has no explicit block |
| `xxh3.rs` — `hash64_large_generic` | 586–601 | no | 1: 593–593 | invokes an unsafe secret-generation function pointer |
| `xxh3.rs` — `hash128_large_neon` | 769–777 | yes | 0 | unsafe target-feature dispatch wrapper; body has no explicit block |
| `xxh3.rs` — `hash128_large_avx2` | 781–789 | yes | 0 | unsafe target-feature dispatch wrapper; body has no explicit block |
| `xxh3.rs` — `hash128_large_generic` | 792–813 | no | 1: 799–799 | invokes an unsafe secret-generation function pointer |
| `file_backend/optimized.rs` — `read_exact_at` | 133–166 | no | 1: 137–144 | invokes the unsafe `libc::pread` wrapper |
| `file_backend/optimized.rs` — `write_all_at` | 169–198 | no | 1: 173–180 | invokes the unsafe `libc::pwrite` wrapper |

The table has 25 rows because it records every function with explicit unsafe involvement exactly once. By the required function categories, there are 16 **safe-declared with unsafe body** functions, nine **unsafe-declared** functions, and 1,522 **safe body** functions. Five of the unsafe-declared functions contain explicit unsafe blocks; four do not.

### Unsafe impls

All five are in the cfg-controlled `sync::spin` module; none is an unsafe trait.

- `unsafe impl Send for Mutex<T>` — line 74
- `unsafe impl Sync for Mutex<T>` — line 75
- `unsafe impl Sync for MutexGuard<'_, T>` — line 142
- `unsafe impl Send for RwLock<T>` — line 182
- `unsafe impl Sync for RwLock<T>` — line 183

### Unsafe block line ranges and union LOC

```text
transactions.rs: 139–139
multimap_btree.rs: 524–524, 601–601
sync.rs: 149–149, 156–156, 253–253, 272–272, 279–279
xxh3.rs: 66–68, 73–73, 92–94, 97–99, 166–192, 205–228,
          295–318, 328–350, 356–383, 406–412, 438–438,
          452–458, 593–593, 799–799
file_backend/optimized.rs: 137–144, 173–180
```

The line-union calculation is 177. These ranges do not overlap or nest in this revision, so it also equals the sum of their inclusive sizes. This is unsafe-block region LOC only, not total unsafe-function LOC or total source LOC.

## Safe-body false-negative sample

Twenty production functions from files for which the automated source scan claimed no explicit unsafe were inspected. None has `unsafe fn` or an `unsafe {}` block.

| File | Function | Line |
|---|---|---:|
| `complex_types.rs` | `encode_varint_len` | 6 |
| `complex_types.rs` | `decode_varint_len` | 22 |
| `error.rs` | `StorageError::into_storage_error_or_corrupted` | 127 |
| `key_range.rs` | `RangeBounds::key_bounds` implementation | 44 |
| `table.rs` | `Table::tree_height` | 44 |
| `table.rs` | `Table::fragmented_bytes` | 70 |
| `table.rs` | `ReadOnlyTable::new` | 94 |
| `tree_store/table_tree_base.rs` | `TableTreeBase::new` | 78 |
| `tree_store/table_tree_base.rs` | `TableTreeBase::set_header` | 107 |
| `tree_store/page_store/layout.rs` | `round_up_to_multiple_of` | 3 |
| `tree_store/page_store/layout.rs` | `DatabaseLayout::calculate` | 31 |
| `tree_store/page_store/layout.rs` | `DatabaseLayout::data_section` | 48 |
| `tree_store/page_store/lru_cache.rs` | `LruCache::new` | 13 |
| `tree_store/page_store/lru_cache.rs` | `LruCache::insert` | 24 |
| `tree_store/page_store/lru_cache.rs` | `LruCache::remove` | 35 |
| `tree_store/page_store/lru_cache.rs` | `LruCache::get` | 54 |
| `tree_store/page_store/lru_cache.rs` | `LruCache::get_mut` | 63 |
| `tree_store/page_store/lru_cache.rs` | `LruCache::iter` | 72 |
| `tree_store/page_store/lru_cache.rs` | `LruCache::iter_mut` | 76 |
| `tree_store/page_store/lru_cache.rs` | `LruCache::len` | 81 |

## Comparison with automated result

| Metric | Automated | Manual | Match? | Explanation |
|---|---:|---:|---|---|
| production_files | 51 | 44 | no | scanner walked the workspace-root package directory and included sibling workspace crates, instead of metadata-defined `redb` library source only |
| physical_loc | 32,402 | 31,599 before removing inline test regions | no | same sibling-workspace scope error; manual physical LOC is reported separately from unsafe region LOC |
| nonblank_loc | 29,389 | not independently recomputed | n/a | audit scope prioritised explicit unsafe use; automated value has the same package-scope issue |
| functions_total | 1,748 | 1,547 | no | automated scan includes sibling workspace functions and inline `#[cfg(test)]` items; manual denominator excludes both |
| functions_safe | 1,739 | 1,522 safe-body functions | no | automated definition is “not declared unsafe”, which incorrectly includes safe-declared functions with unsafe bodies; it is not category A |
| functions_unsafe_declared | 9 | 9 | yes | all nine are `xxh3.rs` SIMD wrappers/functions |
| functions_with_unsafe | 12 | 21 | no | scanner finds only two of `xxh3.rs`'s 11 block-containing functions. Its declaration test accepts any `fn` token followed by an identifier, including `unsafe fn(...)` function-pointer types in parameter lists, which overwrites pending function context. |
| functions_unsafe_any | not reported | 25 | n/a | required union: declared unsafe or block-containing, without double counting |
| unsafe_blocks | 24 | 24 | yes | source-level block count agrees |
| unsafe_loc_estimate | 177 | 177 | yes | same explicit block line union at this revision |
| files_with_unsafe | 5 | 5 | yes | same five source files, though the manual audit flags cfg status |
| unsafe_impl_count | not reported | 5 | n/a | all in cfg-controlled `sync::spin` |
| unsafe_trait_count | not reported | 0 | n/a | none found |

## Audit finding

The automated source scanner is accurate for this revision's lexical unsafe-block count, unsafe-block line union, unsafe-declared count, and unsafe-containing-file count. It is not trustworthy for the requested package-scoped production denominator or for `functions_with_unsafe`: it scans sibling workspace packages and does not exclude inline test-only items, and its function-declaration recognition is confused by `unsafe fn(...)` parameter types in `xxh3.rs`. The report makes no claim about correctness, security, or exploitability of any unsafe operation.
