# Inventory summary

## Run metadata

- **inventory_methodology_version**: `1`
- **application**: `sqlite`
- **application_commit**: `ab5206d096d6ecc5f9ea2586889c07e52e852c23`

## Declaration counts

- Declarations: 5615
- Total analyzed LOC: 173002

| Bucket | Declarations | Declaration % | LOC | LOC % |
| --- | ---: | ---: | ---: | ---: |
| TRIVIAL | 1914 | 34.09 | 24328 | 14.06 |
| REFACTOR_THEN_DSL | 3156 | 56.21 | 104786 | 60.57 |
| NEEDS_TRANSPILER | 480 | 8.55 | 36111 | 20.87 |
| BOUNDARY | 65 | 1.16 | 7777 | 4.50 |
| UNKNOWN | 0 | 0.00 | 0 | 0.00 |

## Blocker/evidence histogram

- `bitfield`: 140
- `c_array`: 1242
- `callback`: 61
- `conditional_compilation`: 5563
- `extern_or_abi_boundary`: 65
- `flexible_array`: 632
- `free`: 31
- `function_pointer`: 347
- `global_read`: 192
- `global_write`: 46
- `goto`: 175
- `macro_use`: 5116
- `malloc`: 42
- `memcpy`: 259
- `memmove`: 28
- `memset`: 326
- `mutable_global`: 139
- `pointer_arithmetic`: 196
- `pointer_to_pointer`: 1387
- `raw_pointer_parameter`: 4406
- `raw_pointer_return`: 485
- `realloc`: 13
- `static_local`: 3080
- `syscall`: 23
- `union`: 63
- `va_list`: 45
- `variadic`: 45
- `void_pointer`: 1067

## Primary-reason histogram

- `bitfield`: 68
- `callback`: 36
- `extern_or_abi_boundary`: 65
- `flexible_array`: 430
- `free`: 7
- `function_pointer`: 342
- `goto`: 45
- `malloc`: 25
- `memcpy`: 171
- `memmove`: 8
- `memset`: 184
- `mutable_global`: 42
- `no_significant_detected_blocker`: 1914
- `pointer_arithmetic`: 153
- `realloc`: 6
- `static_local`: 2017
- `union`: 55
- `va_list`: 6
- `variadic`: 41

## Low-confidence declarations


## UNKNOWN declarations
