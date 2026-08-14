# Manual C++ infrastructure feasibility screen

Status: source-audit screening aid for researcher review, not a migration result
or scientific conclusion. Percentages are manual feasibility estimates from
sampled production functions, not measured RustyCpp conversion outcomes.

## Method

Pinned checkouts were read without modification. Tests, examples, benchmarks,
generated source, and vendored dependencies were excluded. Each sample covered
large implementation files, public/internal APIs, ownership, transport I/O,
callbacks, threading, templates/virtual dispatch, and platform boundaries.

A is direct safe migration; B is local refactor; C is retained boundary; D is
hard/currently unsupported. Counts are function-level and not LOC-weighted.

## Results

| Project | Production scope | Functions reviewed | A | A+B | C+D | Difficulty concentration | Relevance | Manageability | Technical screen |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| libzmq | handwritten src runtime | 36 | 27.8% | 55.6% | 44.4% | core paths | Very high | Medium-low | No |
| Apache Thrift C++ | lib/cpp/src/thrift runtime | 36 | 47.2% | 83.3% | 16.7% | transport/server/libevent | High | High | Yes, conditional |
| eCAL | ecal/core/src and core APIs | 36 | 27.8% | 61.1% | 38.9% | transport/SHM plus pubsub | Very high | Medium-low | No |
| Boost.Beast | include/boost/beast headers | 34 | 20.6% | 52.9% | 47.1% | scattered header/template paths | High | Low | No |
| POCO Net | Net/src and public Net API | 36 | 44.4% | 75.0% | 25.0% | socket/reactor/platform files | High | Medium-high | No |
| CAF | libcaf_core and libcaf_net runtime | 36 | 25.0% | 55.6% | 44.4% | scheduler/mailbox/multiplexer core | High | Low | No |

## Source samples and manual classifications

### libzmq at 46493370217ac135246617fa2f6ac819d8b61bfc

Reviewed 36 functions across msg.cpp, pipe.cpp, own.cpp, ctx.cpp,
socket_base.cpp, stream_engine_base.cpp, ypipe.hpp, and generic_mtrie_impl.hpp.

A: message flag/accessor checks, routing-id accessors, HWM calculations,
address/options validation, codec/metadata helpers, and trie traversal
branches.

B: msg_t init_buffer, pipe_t check_read/read/write/rollback, own_t
process_own/process_term_req/process_term, routing-id/hello construction, and
selected socket option policy. These need explicit ownership/lifetime
reshaping.

C: msg_t init/init_size/init_external_storage/init_data/close (malloc,
placement construction, tagged union, atomic refcount, arbitrary free
callback); pipepair; stream-engine socket/credential/timer work; pollers.

D: lock-free ypipe/atomic pointer publication, own_t process_destroy
self-destruction, platform poller variants, and C-ABI deallocator callbacks.

The difficulty is intrinsic: message lifetime, cross-thread pipes, queue
publication, virtual engine interfaces, and OS polling are central. The
existing roughly 70.4% direct / 71.0% refactor inventory signal is more
optimistic than the manual sample because lexical helpers outnumber
semantically central functions. Broad agreement: no.

### Apache Thrift C++ at 9b10484ca7687af6cc67567df9d457d0f031748e

Reviewed 36 functions across protocol/TJSONProtocol.cpp,
protocol/TVirtualProtocol.h, protocol/TProtocolTap.h,
transport/TBufferTransports.h, transport/TSocket.cpp,
transport/TServerSocket.cpp, transport/THeaderTransport.cpp, and
server/TNonblockingServer.cpp.

A: JSON type-name/type-id conversion, hexadecimal/string parsing, protocol
forwarding, field/message bookkeeping, frame/header validation, and simple
configuration methods.

B: buffer read/readAll/write/borrow/consume, memory transport setup, protocol
recursion, server connection lifecycle, thread-pool handoff, and retry/error
policy.

C: TSocket hasPendingDataToRead/peek/options/send/receive, accept/listen,
libevent callback wrappers, and nonblocking event scheduling.

D: raw void-pointer connection context crossing libevent/server callbacks.

Risk is concentrated in socket/transport/server and the libevent bridge; the
protocol and in-memory transports are a broad coherent envelope. Scoped
inventory-v2 reports 97.55% lexical A+B-like evidence; manual 83.33% is lower
because socket, callback, and raw-buffer semantics are absent from lexical
rules. Broad agreement: yes, but inventory is materially optimistic.

### eCAL at 652e92f7cda2ab1f2d0056cb296b66c7a30c8fa8

Reviewed 36 functions across publisher/subscriber implementations, service
client/server implementations, SHM memory-file pool/map, UDP receiver, and
SHM registration broadcast.

A: identifier/configuration construction, layer-state bookkeeping,
registration-record assembly, filter matching, serialization metadata, and
simple getters.

B: publisher payload preparation/layer selection, subscriber connection-map
changes, buffered reads, service bookkeeping, transport configuration
builders, and monitoring aggregation.

C: subscriber condition-variable reads/callback installation; publisher
dispatch to SHM/TCP/UDP; memory-file observer Start/Stop/Observe; named events,
mapped-file locking, Asio UDP receive, and raw zero-copy payload access.

D: zero-copy callbacks borrowing mapped memory while invoking user code;
cross-process event/liveness protocol; SHM acknowledgement lifetime paths.

Risk is partly concentrated in SHM/TCP/UDP but reached from central pub/sub
functions. Inventory-v2 gives 96.35% lexical A+B-like evidence versus manual
61.11%; it misses threads, callbacks, shared-memory and transport contracts.
Broad agreement: no.

### Boost.Beast at 7c1e061f91e2ef542217b76286c314d006c0c8fc

Reviewed 34 functions across core multi_buffer/basic_stream,
HTTP fields/read/write, and WebSocket read/write/stream implementation.

A: HTTP field iterator operations, start-line writer construction, small
buffer-range predicates, header formatting, and code/verb conversion.

B: basic_multi_buffer subrange traversal, buffer commit/consume, HTTP fields,
frame parsing, masking, and synchronous HTTP read/write orchestration.

C: executor/timer work, socket teardown, external Asio buffer sequence
lifetimes, and user control callbacks.

D: WebSocket async read/write operation state machines: macro-coroutines,
move-only handlers, weak/shared state, cancellation, executor dispatch, lock
arbitration, and template instantiation form one model.

The concern is scattered through the header-only production API. Inventory-v2
reports 88.21% versus manual 52.94%; templates, Asio executors, coroutine
macros, and callback lifetimes are not lexical features. Broad agreement: no.

### POCO Net at a2cf8ccfc48e858d0af493d58e695c5475bc6780

Reviewed 36 functions across SocketImpl, StreamSocketImpl, SocketReactor,
PollSet, HTTP client/server, WebSocket, DNS, and NetworkInterface.

A: address/string/number formatting, HTTP session bookkeeping, request
composition, multipart/mail parsing helpers, interface-property conversion, and
error-class selection.

B: DNS result conversion, HTTP request/response state, WebSocket
frame preparation/parsing, socket option wrappers, poll-set bookkeeping, and
reactor observer dispatch.

C: SocketImpl acceptConnection/connect/connectNB/bind, timeout/poll,
send/receive, epoll/eventfd/sendfile paths, and reactor wakeup integration.

D: cross-platform socket/reactor ownership combining raw descriptors, POSIX or
Windows APIs, and observer callback lifetime.

OS/socket/polling code is relatively concentrated, but HTTP still depends on
it. Inventory-v2 gives 95.81% versus manual 75.00%. Broad agreement: no;
lexical inventory underprices platform and callback semantics.

### CAF at 8379b1b4f5f746043a3c6dfb2e963e4994445845

Reviewed 36 functions across scheduled_actor.cpp, actor_system.cpp,
mailbox/refcount headers, net/multiplexer.cpp, socket_manager.cpp, HTTP
server, and WebSocket framing.

A: default actor error/down/exit handlers, reflection/drop helpers,
configuration lookup, HTTP formatting, and frame predicates.

B: actor initialization, behavior replacement, metrics, serialization,
HTTP route assembly, and selected socket-manager registration.

C: scheduled_actor enqueue, mailbox push/scheduler handoff, private-thread
integration, multiplexer initialization, pipe signaling, poll registration,
and socket-event callbacks.

D: intrusive refcount lifecycle, mailbox/scheduler coordination,
cross-thread action transfer, and type-erased actor behavior/callback
dispatch.

Hard parts are central runtime semantics. No clean inventory comparison was
made: CAF co-locates test cpp files with production module files, so a scanner
scope would violate the stated exclusion rules.

## Provisional technical ordering for researcher review

1. Apache Thrift C++: the only screened scope above 80% A+B; meaningful
   protocol/runtime logic with identifiable boundaries.
2. POCO Net: manageable and recognizable, but did not meet a strict threshold.
3. eCAL: strongest libzmq-domain resemblance, but SHM/callback/lifetime work
   is central.
4. libzmq: ideal stress/comparison case, not a broad safe-migration candidate.
5. Boost.Beast: template/Asio execution model is pervasive.
6. CAF: scheduler, mailbox, intrusive ownership, and networking are
   cross-cutting.

The researcher must independently review these samples, choose any methodology
change, and make any project-selection or scientific conclusion.
+

## Expanded full-library audit (replacement estimates)

This replaces the earlier 34–36-function screening numbers. Each row is a
stratified review of 90 production functions, spread over the stated complete
runtime scope. Function enumeration was used only to distribute samples over
files; A/B/C/D judgments came from reading definitions, surrounding ownership
state, public interfaces, and build/module boundaries.

| Project | Full coherent scope used for 90-function audit | A | B | C | D | A % | A+B % | C+D % |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| libzmq | all handwritten src runtime, including API, message, queue/pipe, engines, transports, pollers, security | 22 | 26 | 28 | 14 | 24.4% | 53.3% | 46.7% |
| Apache Thrift C++ | complete lib/cpp/src/thrift runtime: protocol, transport, server, concurrency, SSL, profiling, Windows pipes | 36 | 31 | 18 | 5 | 40.0% | 74.4% | 25.6% |
| eCAL | complete ecal/core/src: public core, pub/sub, services, registration, serialization, SHM/TCP/UDP, process/time/config | 27 | 30 | 26 | 7 | 30.0% | 63.3% | 36.7% |
| Boost.Beast | complete production include/boost/beast implementation, HTTP, WebSocket, core buffers/streams, async operations | 16 | 27 | 28 | 19 | 17.8% | 47.8% | 52.2% |
| POCO Net | complete Net/src implementation and matching public Net interfaces: sockets, reactor, HTTP, WebSocket, DNS, mail, interfaces | 38 | 27 | 21 | 4 | 42.2% | 72.2% | 27.8% |
| CAF | libcaf_core, libcaf_io, and libcaf_net production runtime: actor system, mailbox/scheduler, streams, IO, multiplexer, HTTP/WebSocket | 20 | 29 | 27 | 14 | 22.2% | 54.4% | 45.6% |

### Expanded sample distribution

| Project | Production strata covered (function counts) |
| --- | --- |
| libzmq | C API/context/options 15; message/blob/metadata 14; pipe/ypipe/own 16; socket/session/engine 17; transports/security 14; poller/thread/timer 14 |
| Apache Thrift C++ | protocols and generated-value handling 20; buffers/header/file transport 18; socket/server socket/SSL/pipes 20; nonblocking server/libevent 15; concurrency/threading 8; processor/profiling/misc runtime 9 |
| eCAL | public/init/process/config/time 15; serialization/monitoring 16; pub/sub 18; service/registration 13; SHM/events/mutex 15; UDP/TCP/readwrite 13 |
| Boost.Beast | core buffers/allocators/streams 18; HTTP fields/message/parser/read/write 20; WebSocket framing/read/write/stream 24; async base/teardown/executor integration 16; utility/error/string 12 |
| POCO Net | SocketImpl/StreamSocket/socket address 20; poll/reactor/proactor 14; HTTP client/server/message 18; WebSocket 10; DNS/network interface 12; mail/FTP/multipart/auth 16 |
| CAF | actor system/scheduled actor/mailbox 20; intrusive ownership/type erasure/serialization 15; scheduler/flow/streams 14; IO broker/middleman 13; net multiplexer/socket manager 16; HTTP/WebSocket/octet-stream 12 |

### Expanded audit interpretation

The expanded sample deliberately includes the difficult modules instead of
allowing protocol, serializer, accessor, or formatting helpers to dominate
the denominator.

- libzmq: difficult concerns remain intrinsic and central. The low ratio is
  driven by object lifetime and refcounting, lock-free queues, async
  ownership teardown, virtual engine/socket interfaces, C callbacks, and
  platform polling.
- Thrift: the broad protocol layer still supplies a sizeable A/B envelope,
  but complete transport/server coverage adds raw socket, SSL callback,
  pipe, libevent, thread-pool, and platform branches. The full-scope manual
  estimate falls below 80%.
- eCAL: serializer/configuration functions are often A/B, but the public
  pub/sub path reaches callback, mutex, zero-copy, shared-memory,
  registration, and multi-transport contracts. Risk is not optional.
- Beast: header-only templates, Asio executor/buffer concepts, handler
  propagation, coroutine macros, cancellation, and WebSocket lock state are
  pervasive instead of a narrow socket adapter.
- POCO Net: high-level protocols help, but a full Net scope retains a large
  socket/reactor/platform and callback surface. Boundaries concentrate more
  successfully than in libzmq or CAF, but the manual estimate remains below
  a strict quota.
- CAF: mailbox scheduling, intrusive ownership, type erasure, and
  cross-thread network multiplexing are the framework's primary model.

On this expanded full-library screen, none of the six is supported as a
greater-than-80% safe RustyCpp candidate by the sampled-function estimate.
Apache Thrift C++ remains the nearest candidate for a researcher to examine
further, but it does not pass the stated quota without an independently
justified narrower study scope.

The earlier inventory comparisons remain secondary evidence. Their high
A+B-like percentages are not revised here: the discrepancy grows with the
broader scope because lexical detection does not capture ownership graphs,
callbacks, thread handoff, external runtimes, or OS/platform contracts.

