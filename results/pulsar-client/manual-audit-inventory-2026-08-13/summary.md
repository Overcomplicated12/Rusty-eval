# Inventory summary

## Run metadata

- **inventory_methodology_version**: `2`
- **application**: `pulsar-client`
- **application_commit**: `1d08b2b358db42af2232d17bbe7ccc2937a79bbb`

## Declaration counts

- Declarations: 913
- Total analyzed LOC: 5809

| Bucket | Declarations | Declaration % | LOC | LOC % |
| --- | ---: | ---: | ---: | ---: |
| TRIVIAL | 750 | 82.15 | 3955 | 68.08 |
| REFACTOR_THEN_DSL | 53 | 5.81 | 1018 | 17.52 |
| NEEDS_TRANSPILER | 77 | 8.43 | 803 | 13.82 |
| BOUNDARY | 0 | 0.00 | 0 | 0.00 |
| UNKNOWN | 33 | 3.61 | 33 | 0.57 |

## Blocker/evidence histogram

- `bitfield`: 2
- `c_array`: 11
- `callback`: 48
- `conditional_compilation`: 334
- `function_pointer`: 25
- `goto`: 3
- `lexical_ambiguity`: 33
- `macro_generated_declaration`: 33
- `macro_use`: 64
- `malloc`: 3
- `memcpy`: 13
- `memmove`: 2
- `mutable_global`: 26
- `pointer_arithmetic`: 14
- `pointer_to_pointer`: 18
- `raw_pointer_parameter`: 381
- `raw_pointer_return`: 58
- `static_local`: 1
- `syscall`: 17
- `union`: 2
- `variadic`: 3
- `void_pointer`: 93

## Primary-reason histogram

- `bitfield`: 1
- `callback`: 47
- `function_pointer`: 25
- `macro_generated_declaration`: 33
- `malloc`: 3
- `memcpy`: 7
- `memmove`: 1
- `mutable_global`: 26
- `no_significant_detected_blocker`: 750
- `pointer_arithmetic`: 14
- `static_local`: 1
- `union`: 2
- `variadic`: 3

## Low-confidence declarations

- `lib/Authentication.cc:33` `macro_DECLARE_LOG_OBJECT_33` — macro_generated_declaration
- `lib/AutoClusterFailover.cc:51` `macro_DECLARE_LOG_OBJECT_51` — macro_generated_declaration
- `lib/BatchMessageContainer.cc:25` `macro_DECLARE_LOG_OBJECT_25` — macro_generated_declaration
- `lib/BatchMessageKeyBasedContainer.cc:31` `macro_DECLARE_LOG_OBJECT_31` — macro_generated_declaration
- `lib/BinaryProtoLookupService.cc:26` `macro_DECLARE_LOG_OBJECT_26` — macro_generated_declaration
- `lib/ClientConnection.cc:57` `macro_DECLARE_LOG_OBJECT_57` — macro_generated_declaration
- `lib/ClientImpl.cc:60` `macro_DECLARE_LOG_OBJECT_60` — macro_generated_declaration
- `lib/CompressionCodecZLib.cc:24` `macro_DECLARE_LOG_OBJECT_24` — macro_generated_declaration
- `lib/ConnectionPool.cc:36` `macro_DECLARE_LOG_OBJECT_36` — macro_generated_declaration
- `lib/ConsumerImplBase.cc:24` `macro_DECLARE_LOG_OBJECT_24` — macro_generated_declaration
- `lib/ConsumerInterceptors.cc:25` `macro_DECLARE_LOG_OBJECT_25` — macro_generated_declaration
- `lib/ExecutorService.cc:25` `macro_DECLARE_LOG_OBJECT_25` — macro_generated_declaration
- `lib/HTTPLookupService.cc:38` `macro_DECLARE_LOG_OBJECT_38` — macro_generated_declaration
- `lib/HandlerBase.cc:31` `macro_DECLARE_LOG_OBJECT_31` — macro_generated_declaration
- `lib/MessageBuilder.cc:33` `macro_DECLARE_LOG_OBJECT_33` — macro_generated_declaration
- `lib/MultiTopicsConsumerImpl.cc:36` `macro_DECLARE_LOG_OBJECT_36` — macro_generated_declaration
- `lib/NamespaceName.cc:28` `macro_DECLARE_LOG_OBJECT_28` — macro_generated_declaration
- `lib/NegativeAcksTracker.cc:35` `macro_DECLARE_LOG_OBJECT_35` — macro_generated_declaration
- `lib/PartitionedProducerImpl.cc:31` `macro_DECLARE_LOG_OBJECT_31` — macro_generated_declaration
- `lib/PatternMultiTopicsConsumerImpl.cc:24` `macro_DECLARE_LOG_OBJECT_24` — macro_generated_declaration
- `lib/ProducerInterceptors.cc:25` `macro_DECLARE_LOG_OBJECT_25` — macro_generated_declaration
- `lib/TopicName.cc:32` `macro_DECLARE_LOG_OBJECT_32` — macro_generated_declaration
- `lib/UnAckedMessageTrackerEnabled.cc:30` `macro_DECLARE_LOG_OBJECT_30` — macro_generated_declaration
- `lib/auth/AuthAthenz.cc:30` `macro_DECLARE_LOG_OBJECT_30` — macro_generated_declaration
- `lib/auth/AuthOauth2.cc:31` `macro_DECLARE_LOG_OBJECT_31` — macro_generated_declaration
- `lib/auth/athenz/ZTSClient.cc:62` `macro_DECLARE_LOG_OBJECT_62` — macro_generated_declaration
- `lib/checksum/crc32c_arm.h:47` `macro_PREF4X64L1_47` — macro_generated_declaration
- `lib/checksum/crc32c_arm.h:48` `macro_PREF4X64L1_48` — macro_generated_declaration
- `lib/checksum/crc32c_arm.h:49` `macro_PREF4X64L1_49` — macro_generated_declaration
- `lib/checksum/crc32c_arm.h:50` `macro_PREF4X64L1_50` — macro_generated_declaration
- `lib/st/DagWatchSession.cc:28` `macro_DECLARE_LOG_OBJECT_28` — macro_generated_declaration
- `lib/st/StMessageId.cc:31` `macro_DECLARE_LOG_OBJECT_31` — macro_generated_declaration
- `lib/st/StProducerImpl.cc:35` `macro_DECLARE_LOG_OBJECT_35` — macro_generated_declaration

## UNKNOWN declarations

- `lib/Authentication.cc:33` `macro_DECLARE_LOG_OBJECT_33` — macro_generated_declaration
- `lib/AutoClusterFailover.cc:51` `macro_DECLARE_LOG_OBJECT_51` — macro_generated_declaration
- `lib/BatchMessageContainer.cc:25` `macro_DECLARE_LOG_OBJECT_25` — macro_generated_declaration
- `lib/BatchMessageKeyBasedContainer.cc:31` `macro_DECLARE_LOG_OBJECT_31` — macro_generated_declaration
- `lib/BinaryProtoLookupService.cc:26` `macro_DECLARE_LOG_OBJECT_26` — macro_generated_declaration
- `lib/ClientConnection.cc:57` `macro_DECLARE_LOG_OBJECT_57` — macro_generated_declaration
- `lib/ClientImpl.cc:60` `macro_DECLARE_LOG_OBJECT_60` — macro_generated_declaration
- `lib/CompressionCodecZLib.cc:24` `macro_DECLARE_LOG_OBJECT_24` — macro_generated_declaration
- `lib/ConnectionPool.cc:36` `macro_DECLARE_LOG_OBJECT_36` — macro_generated_declaration
- `lib/ConsumerImplBase.cc:24` `macro_DECLARE_LOG_OBJECT_24` — macro_generated_declaration
- `lib/ConsumerInterceptors.cc:25` `macro_DECLARE_LOG_OBJECT_25` — macro_generated_declaration
- `lib/ExecutorService.cc:25` `macro_DECLARE_LOG_OBJECT_25` — macro_generated_declaration
- `lib/HTTPLookupService.cc:38` `macro_DECLARE_LOG_OBJECT_38` — macro_generated_declaration
- `lib/HandlerBase.cc:31` `macro_DECLARE_LOG_OBJECT_31` — macro_generated_declaration
- `lib/MessageBuilder.cc:33` `macro_DECLARE_LOG_OBJECT_33` — macro_generated_declaration
- `lib/MultiTopicsConsumerImpl.cc:36` `macro_DECLARE_LOG_OBJECT_36` — macro_generated_declaration
- `lib/NamespaceName.cc:28` `macro_DECLARE_LOG_OBJECT_28` — macro_generated_declaration
- `lib/NegativeAcksTracker.cc:35` `macro_DECLARE_LOG_OBJECT_35` — macro_generated_declaration
- `lib/PartitionedProducerImpl.cc:31` `macro_DECLARE_LOG_OBJECT_31` — macro_generated_declaration
- `lib/PatternMultiTopicsConsumerImpl.cc:24` `macro_DECLARE_LOG_OBJECT_24` — macro_generated_declaration
- `lib/ProducerInterceptors.cc:25` `macro_DECLARE_LOG_OBJECT_25` — macro_generated_declaration
- `lib/TopicName.cc:32` `macro_DECLARE_LOG_OBJECT_32` — macro_generated_declaration
- `lib/UnAckedMessageTrackerEnabled.cc:30` `macro_DECLARE_LOG_OBJECT_30` — macro_generated_declaration
- `lib/auth/AuthAthenz.cc:30` `macro_DECLARE_LOG_OBJECT_30` — macro_generated_declaration
- `lib/auth/AuthOauth2.cc:31` `macro_DECLARE_LOG_OBJECT_31` — macro_generated_declaration
- `lib/auth/athenz/ZTSClient.cc:62` `macro_DECLARE_LOG_OBJECT_62` — macro_generated_declaration
- `lib/checksum/crc32c_arm.h:47` `macro_PREF4X64L1_47` — macro_generated_declaration
- `lib/checksum/crc32c_arm.h:48` `macro_PREF4X64L1_48` — macro_generated_declaration
- `lib/checksum/crc32c_arm.h:49` `macro_PREF4X64L1_49` — macro_generated_declaration
- `lib/checksum/crc32c_arm.h:50` `macro_PREF4X64L1_50` — macro_generated_declaration
- `lib/st/DagWatchSession.cc:28` `macro_DECLARE_LOG_OBJECT_28` — macro_generated_declaration
- `lib/st/StMessageId.cc:31` `macro_DECLARE_LOG_OBJECT_31` — macro_generated_declaration
- `lib/st/StProducerImpl.cc:35` `macro_DECLARE_LOG_OBJECT_35` — macro_generated_declaration
