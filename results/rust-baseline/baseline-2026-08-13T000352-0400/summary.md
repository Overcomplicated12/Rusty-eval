# Rust Baseline Summary

- Experiment ID: `baseline-2026-08-13T000352-0400`
- Generated at: `2026-08-13T00:03:52-04:00`
- Mode: `default`

| crate | revision | mode | production_files | physical_loc | nonblank_loc | functions_total | functions_safe | functions_unsafe_declared | functions_with_unsafe | functions_unsafe_any | safe_function_pct | functions_without_explicit_unsafe_pct | unsafe_blocks | unsafe_loc_estimate | unsafe_loc_pct_estimate | files_with_unsafe | unsafe_file_pct | top5_unsafe_block_concentration_pct | top5_unsafe_concentration_pct | geiger_status | count_unsafe_status | scan_status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| blake3 | 77b257eee7da5cd608eaf6be8343d3a4c9776af2 | default | 18 | 7196 | 6582 | 260 | 164 | 85 | 96 | 96 | 63.0769 | 63.0769 | 126 | 1745 | 24.2496 | 12 | 66.6667 | 84.127 | 88.3668 | TOOL_UNAVAILABLE | TOOL_UNAVAILABLE | OK |
| bytes | d5c8ad3227afe459c09f1d0d85455abf00f0381a | default | 19 | 9813 | 8896 | 580 | 476 | 58 | 46 | 104 | 82.069 | 82.069 | 62 | 264 | 2.6903 | 8 | 42.1053 | 98.3871 | 99.6212 | TOOL_UNAVAILABLE | TOOL_UNAVAILABLE | OK |
| crossbeam-epoch | 7de845aa13ce5d80084ce0889e014ae0aa0d19ce | default | 12 | 4238 | 3731 | 194 | 105 | 44 | 72 | 89 | 54.1237 | 54.1237 | 102 | 325 | 7.6687 | 8 | 66.6667 | 88.2353 | 82.4615 | TOOL_UNAVAILABLE | TOOL_UNAVAILABLE | OK |
| hashbrown | 8d9d6c51fe1f9a349f4981c8ef2f69359cd2e708 | default | 28 | 20837 | 19091 | 840 | 579 | 103 | 254 | 261 | 68.9286 | 68.9286 | 305 | 1113 | 5.3415 | 17 | 60.7143 | 80.0 | 86.6128 | TOOL_UNAVAILABLE | TOOL_UNAVAILABLE | OK |
| hyper | fca07bd3937d4a3a4822372acdf766d0640796af | default | 64 | 19017 | 16759 | 862 | 829 | 5 | 28 | 33 | 96.1717 | 96.1717 | 37 | 86 | 0.4522 | 15 | 23.4375 | 67.5676 | 58.1395 | TOOL_UNAVAILABLE | TOOL_UNAVAILABLE | OK |
| mio | 52cfaa4168e8545bc197cd333f81f254e25c59b5 | default | 61 | 13371 | 12013 | 716 | 618 | 28 | 70 | 98 | 86.3128 | 86.3128 | 99 | 347 | 2.5952 | 33 | 54.0984 | 45.4545 | 58.7896 | TOOL_UNAVAILABLE | TOOL_UNAVAILABLE | OK |
| parking_lot | d20d71e5a8955ec1d2a53e3659142a505476bb3d | default | 13 | 3432 | 2887 | 120 | 64 | 27 | 29 | 56 | 53.3333 | 53.3333 | 38 | 142 | 4.1375 | 8 | 61.5385 | 94.7368 | 66.1972 | TOOL_UNAVAILABLE | TOOL_UNAVAILABLE | OK |
| prost | aed74ad0e844959ee6948f29c4e9cff0f278e89e | default | 9 | 2393 | 2074 | 158 | 155 | 0 | 3 | 3 | 98.1013 | 98.1013 | 12 | 31 | 1.2954 | 2 | 22.2222 | 100.0 | 100.0 | TOOL_UNAVAILABLE | TOOL_UNAVAILABLE | OK |
| quinn-proto | 148d760d8845dc6315d554a39a1f1f83a4134bfe | default | 50 | 21371 | 18731 | 949 | 945 | 1 | 3 | 4 | 99.5785 | 99.5785 | 4 | 4 | 0.0187 | 4 | 8.0 | 100.0 | 100.0 | TOOL_UNAVAILABLE | TOOL_UNAVAILABLE | OK |
| rayon | 1f9bb2538e50f1e6d1bc2e3d06a361ba2af0b632 | default | 99 | 24152 | 21042 | 1497 | 1462 | 9 | 33 | 35 | 97.662 | 97.662 | 53 | 472 | 1.9543 | 10 | 10.101 | 96.2264 | 98.0932 | TOOL_UNAVAILABLE | TOOL_UNAVAILABLE | OK |
| redb | dea77f0f0653c69aba3487846589ec7e77ceb5a1 | default | 44 | 28410 | 25463 | 1547 | 1522 | 9 | 21 | 25 | 98.384 | 98.384 | 24 | 177 | 0.623 | 5 | 11.3636 | 100.0 | 100.0 | TOOL_UNAVAILABLE | TOOL_UNAVAILABLE | OK |
| rkyv | 3814956a8e11bac7b8587e4b2cb5dde99492deee | default | 129 | 25342 | 22175 | 1395 | 1061 | 119 | 307 | 334 | 76.0573 | 76.0573 | 559 | 1099 | 4.3367 | 74 | 57.3643 | 41.5027 | 37.0337 | TOOL_UNAVAILABLE | TOOL_UNAVAILABLE | OK |
| rustix | 035acdc416d9465abc937bd8cd6a0031afc170aa | default | 315 | 69884 | 63758 | 2916 | 1610 | 498 | 810 | 1306 | 55.2126 | 55.2126 | 1016 | 5362 | 7.6727 | 146 | 46.3492 | 31.3976 | 40.4886 | TOOL_UNAVAILABLE | TOOL_UNAVAILABLE | OK |
| rustls | 3f0d8ea21cc1fdae0c857601bba90af4ec31ad42 | default | 83 | 37898 | 32884 | 1815 | 1815 | 0 | 0 | 0 | 100.0 | 100.0 | 0 | 0 | 0.0 | 0 | 0.0 | None | None | TOOL_UNAVAILABLE | TOOL_UNAVAILABLE | OK |
| serde | 747814f7d5fbab872df3b02f070c165b91bde062 | default | 5 | 5200 | 4620 | 388 | 388 | 0 | 0 | 0 | 100.0 | 100.0 | 0 | 0 | 0.0 | 0 | 0.0 | None | None | TOOL_UNAVAILABLE | TOOL_UNAVAILABLE | OK |
| tokio | 625954f365727668cb02d04172b34f1149637728 | default | 348 | 98038 | 88424 | 3912 | 3338 | 191 | 500 | 574 | 85.3272 | 85.3272 | 667 | 1815 | 1.8513 | 125 | 35.9195 | 13.4933 | 13.0028 | TOOL_UNAVAILABLE | TOOL_UNAVAILABLE | OK |
| tonic | 0a67722863f90392c3b50fddf147c1dc9e33576e | default | 60 | 15645 | 13894 | 750 | 743 | 2 | 7 | 7 | 99.0667 | 99.0667 | 7 | 18 | 0.1151 | 5 | 8.3333 | 100.0 | 100.0 | TOOL_UNAVAILABLE | TOOL_UNAVAILABLE | OK |
| tower | df06d70dbea345facbffb5881fe8647f53bf424d | default | 101 | 11676 | 10497 | 528 | 528 | 0 | 0 | 0 | 100.0 | 100.0 | 0 | 0 | 0.0 | 0 | 0.0 | None | None | TOOL_UNAVAILABLE | TOOL_UNAVAILABLE | OK |
