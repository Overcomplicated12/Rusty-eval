# Inventory summary

## Run metadata

- **inventory_methodology_version**: `2`
- **application**: `boost-beast`
- **application_commit**: `7c1e061f91e2ef542217b76286c314d006c0c8fc`

## Declaration counts

- Declarations: 663
- Total analyzed LOC: 13225

| Bucket | Declarations | Declaration % | LOC | LOC % |
| --- | ---: | ---: | ---: | ---: |
| TRIVIAL | 584 | 88.08 | 9350 | 70.70 |
| REFACTOR_THEN_DSL | 10 | 1.51 | 193 | 1.46 |
| NEEDS_TRANSPILER | 65 | 9.80 | 3678 | 27.81 |
| BOUNDARY | 0 | 0.00 | 0 | 0.00 |
| UNKNOWN | 4 | 0.60 | 4 | 0.03 |

## Blocker/evidence histogram

- `bitfield`: 1
- `c_array`: 15
- `callback`: 10
- `conditional_compilation`: 663
- `function_pointer`: 36
- `goto`: 8
- `lexical_ambiguity`: 4
- `macro_generated_declaration`: 4
- `macro_use`: 84
- `memcpy`: 4
- `memmove`: 3
- `memset`: 1
- `pointer_arithmetic`: 4
- `raw_pointer_parameter`: 35
- `static_local`: 1
- `syscall`: 30
- `union`: 1
- `variadic`: 22
- `void_pointer`: 7

## Primary-reason histogram

- `bitfield`: 1
- `callback`: 9
- `function_pointer`: 36
- `goto`: 2
- `macro_generated_declaration`: 4
- `memcpy`: 3
- `memmove`: 1
- `no_significant_detected_blocker`: 584
- `pointer_arithmetic`: 2
- `static_local`: 1
- `variadic`: 20

## Low-confidence declarations

- `include/boost/beast/_experimental/unit_test/suite.hpp:731` `macro_BEAST_DEFINE_TESTSUITE_INSERT_731` — macro_generated_declaration
- `include/boost/beast/_experimental/unit_test/suite.hpp:733` `macro_BEAST_DEFINE_TESTSUITE_INSERT_733` — macro_generated_declaration
- `include/boost/beast/core/detail/config.hpp:88` `macro_BOOST_ASIO_INITFN_AUTO_RESULT_TYPE_88` — macro_generated_declaration
- `include/boost/beast/core/detail/config.hpp:93` `macro_BOOST_ASIO_INITFN_AUTO_RESULT_TYPE_93` — macro_generated_declaration

## UNKNOWN declarations

- `include/boost/beast/_experimental/unit_test/suite.hpp:731` `macro_BEAST_DEFINE_TESTSUITE_INSERT_731` — macro_generated_declaration
- `include/boost/beast/_experimental/unit_test/suite.hpp:733` `macro_BEAST_DEFINE_TESTSUITE_INSERT_733` — macro_generated_declaration
- `include/boost/beast/core/detail/config.hpp:88` `macro_BOOST_ASIO_INITFN_AUTO_RESULT_TYPE_88` — macro_generated_declaration
- `include/boost/beast/core/detail/config.hpp:93` `macro_BOOST_ASIO_INITFN_AUTO_RESULT_TYPE_93` — macro_generated_declaration
