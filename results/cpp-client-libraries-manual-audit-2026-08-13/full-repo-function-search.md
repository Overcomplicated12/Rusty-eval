# Full-repository production function discovery

This expands the candidate search pool beyond the narrower source roots used for
the initial manual client-library screen. It is a discovery manifest, not a
new migration-feasibility estimate: the 90-function manual classifications
must be resampled before being extrapolated to a wider denominator.

Tracked C/C++ files were enumerated at pinned revisions. Excluded paths were
tests, examples, benchmarks/perf, generated code, vendored/third-party trees,
and build outputs. The function counts are lexical discovery counts used for
sampling, not parser-verified API counts.

| Project | Production C/C++ files | Lexical function candidates | Major production areas now covered |
| --- | ---: | ---: | --- |
| Apache Pulsar C++ client | 365 | 689 | lib, auth, stats, C API, public headers |
| redis-plus-plus | 74 | 671 | complete src/sw/redis++ header and implementation surface |
| clickhouse-cpp | 88 | 149 | complete clickhouse base, columns, types, protocol, client |
| prometheus-cpp | 61 | 31 | core, pull, push, utility C++ source; template-heavy public headers remain separately visible to manual review |
| libpqxx | 107 | 218 | complete public include/pqxx, src, supported tools |
| OpenTelemetry C++ | 940 | 650 | API, SDK, all exporters, extensions, OpenTracing shim, resource detectors |

The largest material scope correction is OpenTelemetry C++: the earlier
SDK/core audit intentionally excluded exporters, while the expanded search
includes the exporter production modules. Any full-repository feasibility
claim must sample gRPC/HTTP/ETW/Zipkin/Prometheus exporter paths and should
not reuse the SDK/core-only 83.3% estimate.

Pulsar and libpqxx also expand materially: Pulsar includes its C API and
authentication/stats components, while libpqxx includes its extensive
inline/template public API. redis-plus-plus and clickhouse-cpp were already
close to their complete production library scopes.

Pinned commits:
- Pulsar: 1d08b2b358db42af2232d17bbe7ccc2937a79bbb
- redis-plus-plus: 397f9c7be0eb82ce92545f259a7f66ab992bd7ee
- clickhouse-cpp: eabb71d261d8143d4a7d0313397529ca9cd5f558
- prometheus-cpp: 458deac15d331ca4ec993d3b88ac8f8f727aae05
- libpqxx: 2d0a8e6a61ca69eff40205337655eb812a0eebb1
- OpenTelemetry C++: 5af96de2a0bf65362ced740d40aab531f5d83126

