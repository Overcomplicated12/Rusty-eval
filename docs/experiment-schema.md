# Preliminary experiment schema

This initial schema describes fields expected from eventual experiments. It is intentionally not an implementation contract yet.

| Field | Meaning |
| --- | --- |
| `application` | Target application identifier. |
| `application_commit` | Exact target source commit. |
| `rustycpp_commit` | RustyCpp/transpiler commit used. |
| `harness_commit` | `rusty-eval` commit used to run the experiment. |
| `compiler` | Compiler identity and version. |
| `machine_environment` | Relevant machine and environment details. |
| `source_loc` | Source lines considered. |
| `eligible_loc` | Lines eligible for conversion. |
| `converted_loc` | Lines converted. |
| `input_tokens` | Model input tokens measured. |
| `output_tokens` | Model output tokens measured. |
| `total_tokens` | Total measured tokens. |
| `agent_wall_time` | Agent elapsed time. |
| `conversion_attempts` | Conversion attempts performed. |
| `build_attempts` | Build attempts performed. |
| `test_attempts` | Test attempts performed. |
| `human_interventions` | Count of human interventions. |
| `human_minutes` | Human intervention time in minutes. |
| `baseline_tests` | Baseline test outcome. |
| `converted_tests` | Converted test outcome. |
| `baseline_runtime` | Baseline performance measurement. |
| `converted_runtime` | Converted performance measurement. |
| `result` | Overall experiment result. |
| `failure_reason` | Recorded failure reason, when applicable. |
| `ai_use_ids` | Relevant AI-use provenance record IDs; distinct from experimental telemetry. |

For example:

```json
{
  "ai_use_ids": ["AI-2026-014", "AI-2026-015"]
}
```

This links an experiment to relevant human-to-AI interactions without merging
compliance logging with token or performance measurements.
