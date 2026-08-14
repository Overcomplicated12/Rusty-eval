# Manual infrastructure-client feasibility screen

Status: technical source-audit screening artifact for researcher review, not a
migration result or research conclusion. Percentages are manual feasibility
estimates from 90 stratified production functions per project.

## Scope and estimates

| Project | Full production scope | Functions | A | B | C | D | A % | A+B % | Boundary/hard | Technical screen |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Apache Pulsar C++ client | client lib, auth, stats, protocol, producer/consumer, connection, executors; excludes C API, bundled codecs, generated protobuf | 90 | 20 | 27 | 31 | 12 | 22.2% | 52.2% | 47.8% | No |
| redis-plus-plus | complete src/sw/redis++ public/header implementation above hiredis | 90 | 47 | 27 | 13 | 3 | 52.2% | 82.2% | 17.8% | Yes, conditional |
| clickhouse-cpp | complete clickhouse library: base, columns, types, protocol, client; excludes bundled compression/test code | 90 | 43 | 29 | 15 | 3 | 47.8% | 80.0% | 20.0% | Borderline |
| prometheus-cpp | complete core plus pull and push production modules; excludes bundled CivetWeb | 90 | 59 | 23 | 6 | 2 | 65.6% | 91.1% | 8.9% | Yes |
| libpqxx | complete src and public include/pqxx library above libpq | 90 | 49 | 30 | 8 | 3 | 54.4% | 87.8% | 12.2% | Yes |
| OpenTelemetry C++ | API plus SDK core, metrics/traces/logs/resource/common/configuration; exporters excluded as specified | 90 | 44 | 31 | 10 | 5 | 48.9% | 83.3% | 16.7% | Yes, conditional |

A is direct safe migration. B is likely safe after localized ownership,
lifetime, or interface refactoring. C is an external/runtime/OS/concurrency
boundary. D is hard or currently unsupported. The estimates are function
counts, not LOC, and do not imply successful conversion.

## Sample distribution and source observations

### Apache Pulsar C++ client at 1d08b2b358db42af2232d17bbe7ccc2937a79bbb

The sample spans ConsumerImpl, ProducerImpl, ClientImpl, ClientConnection,
MultiTopicsConsumerImpl, connection pools, batching, acknowledgements,
message/ID/protocol utilities, authentication, executors, and stats.

ConsumerImpl alone combines callbacks, listener executors, deadline timers,
ack-grouping, negative acknowledgements, chunked-message policy, weak client
links, and reconnection state. ClientConnection and producer/consumer lifecycle
functions carry Asio-style async callbacks and protocol dispatch across the
normal public path. Protocol/message helpers and configuration validation are
A/B, but queueing, timers, connection state, interception, auth, and network
callbacks are not a thin optional adapter. Difficulty is distributed through
the client runtime.

Secondary inventory: 88.53% lexical A+B-like evidence over lib. The manual
52.2% estimate disagrees: lexical rules do not account for async callback,
executor, timer, reconnection, and cross-object lifetime contracts.

### redis-plus-plus at 397f9c7be0eb82ce92545f259a7f66ab992bd7ee

The sample spans Redis, RedisCluster, AsyncRedis, AsyncRedisCluster,
QueuedRedis, command parsing/formatting, Connection, ConnectionPool,
Sentinel, subscriber, pipeline, transaction, reply conversion, and coroutine
helpers.

Command wrappers, reply conversion, key routing, pipeline/transaction assembly,
cluster redirection policy, and API-level exception/result logic create a broad
ordinary C++ envelope. Connection fetch/release and pool expiration need local
ownership/condition-variable redesign. Hiredis contexts, reply ownership,
subscription callbacks, async event-loop attachment, and coroutine callback
bridges are boundaries; raw hiredis callback ABI is hard.

The low-level Redis protocol/socket implementation is intentionally delegated
to hiredis, so boundary difficulty is concentrated rather than spread over
every command wrapper. Secondary inventory: 89.42%; manual 82.2% broadly
agrees but is less optimistic on pools, asynchronous APIs, and callbacks.

### clickhouse-cpp at eabb71d261d8143d4a7d0313397529ca9cd5f558

The sample spans Client and Client::Impl, protocol packet parsing, query and
block flow, base wire format/compression/socket abstractions, column classes,
type conversion, date/time, and endpoint selection.

Column/block transformations, query construction, packet variants, row/block
encoding, type conversion, and retry/state policy dominate A/B. Socket factory,
TLS, compression, raw wire reads/writes, block memory views, and user query
callbacks form the concentrated C boundary. The client is intentionally
not internally thread-safe, which avoids a scheduler/pool layer, but protocol
state and raw buffer ownership still require careful local redesign.

Secondary inventory: 93.96%; manual 80.0% is substantially lower because the
scanner does not price socket/TLS/compression, block-view lifetimes, or the
stateful native-protocol client.

### prometheus-cpp at 458deac15d331ca4ec993d3b88ac8f8f727aae05

The sample spans Registry, Family, Counter, Gauge, Histogram, Summary,
collectables, text serialization, labels, gateway push, pull handler, and
utility encoding.

Registry collection/add/remove, family lookup, metric aggregation, label
normalization, histogram/summary calculation, and text serialization are
ordinary A/B logic. The Registry mutex is a local refactor/concurrency edge.
HTTP pull/push transport and the external CivetWeb integration are boundaries;
callback ownership in the pull handler is the small hard group. The difficult
code is concentrated in exposition/push integration, while the dominant core
metrics model is independent.

Secondary inventory only covered core/src (23 lexical functions, 91.30%),
which is too small for a direct whole-library comparison. Its direction agrees
with the manual 91.1% result but is not a sufficient validation.

### libpqxx at 2d0a8e6a61ca69eff40205337655eb812a0eebb1

The sample spans connection, transaction_base, result, row/field conversion,
pipeline, cursor, notification, error handlers, statement/query construction,
and string conversion.

Transactions, result traversal, conversion, query composition, pipeline
bookkeeping, and error/notice policy form the A/B majority. The deliberately
opaque PGconn/PGresult wrappers, libpq calls, polling/wait integration, notice
processor C callback, and raw result-buffer lifetimes are narrow C/D
boundaries. Connection setup shows explicit real_conn casts and libpq wrapper
functions, which makes the boundary visible and auditable rather than
incidental.

Secondary inventory on src alone gives 97.30% over only 37 detected functions;
it omits much inline/template public API and underprices libpq callback and
lifetime semantics. Manual 87.8% is directionally compatible but more useful.

### OpenTelemetry C++ at 5af96de2a0bf65362ced740d40aab531f5d83126

The sample spans API context/provider interfaces and SDK trace, metrics, logs,
resource, instrumentation scope, processors, samplers, aggregation,
configuration, and common runtime utilities. OTLP, Zipkin, Prometheus, ETW,
and other exporters are excluded by scope.

The SDK has substantial A/B data-model, attribute, resource, aggregation,
configuration, and serialization-policy work. TracerProvider demonstrates
unique/shared ownership, mutex-protected tracer cache, virtual processors and
samplers, shutdown/flush lifecycle, and raw instrumentation-scope lifetime
comments. Global provider/context storage, type erasure, asynchronous/batch
processors, and plugin/configuration integration create the C/D portion.
These are cross-cutting, but not as transport-dominant as an exporter.

Secondary inventory on sdk/src gives 93.58%; manual 83.3% agrees only at the
coarse quota level and discounts virtual/type-erased lifecycle and processor
concurrency that lexical rules miss.

## Provisional technical ordering for researcher review

1. redis-plus-plus: best messaging-adjacent candidate; hiredis makes the
   protocol/socket boundary unusually concentrated.
2. libpqxx: clean, explicit libpq boundary and strong C++ transaction/result
   envelope; less messaging-like.
3. prometheus-cpp: strongest safe-envelope estimate and good diversity, but
   observability rather than messaging.
4. OpenTelemetry C++ SDK/core: clears the sample threshold but has more
   cross-cutting virtual/concurrency work than Prometheus.
5. clickhouse-cpp: exactly at the threshold; native protocol and buffers
   warrant a conservative choice.
6. Apache Pulsar C++ client: highly relevant, but its async client runtime
   resembles a smaller messaging runtime rather than a wrapper.

The researcher must independently decide any candidate selection and should
not treat these estimates as measured conversion results.

