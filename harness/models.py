"""JSON-serializable records for Phase 2 harness experiments.

These records describe what happened in a run; they do not infer results or
fill in measurements that an agent/provider did not report.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class ExperimentState(StrEnum):
    CREATED = "CREATED"
    PREPARING = "PREPARING"
    BASELINING = "BASELINING"
    CONTEXT_BUILDING = "CONTEXT_BUILDING"
    CONVERTING = "CONVERTING"
    TRANSPILING = "TRANSPILING"
    BUILDING = "BUILDING"
    TESTING = "TESTING"
    REPAIRING = "REPAIRING"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"
    BENCHMARKING = "BENCHMARKING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AttemptPurpose(StrEnum):
    INITIAL_CONVERSION = "INITIAL_CONVERSION"
    TRANSPILER_REPAIR = "TRANSPILER_REPAIR"
    COMPILE_REPAIR = "COMPILE_REPAIR"
    TEST_REPAIR = "TEST_REPAIR"


class TokenSource(StrEnum):
    PROVIDER_REPORTED = "PROVIDER_REPORTED"
    LOCAL_ESTIMATE = "LOCAL_ESTIMATE"
    UNAVAILABLE = "UNAVAILABLE"


class HumanEffortCategory(StrEnum):
    LOCAL_REFACTOR = "LOCAL_REFACTOR"
    INTERFACE_REFACTOR = "INTERFACE_REFACTOR"
    OWNERSHIP_REFACTOR = "OWNERSHIP_REFACTOR"
    UNSAFE_BOUNDARY = "UNSAFE_BOUNDARY"
    RUSTYCPP_WORKAROUND = "RUSTYCPP_WORKAROUND"
    OTHER = "OTHER"


def _json_value(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    return value


class JsonRecord:
    """Mixin for dataclass records with deterministic JSON-safe dictionaries."""

    def to_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


@dataclass(frozen=True)
class MigrationUnit(JsonRecord):
    id: str
    application: str
    application_commit: str
    file: str
    start_line: int
    end_line: int
    allowed_files: list[str]
    inventory_bucket: str | None = None
    inventory_reason: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TokenUsage(JsonRecord):
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    source: TokenSource = TokenSource.UNAVAILABLE


@dataclass(frozen=True)
class CommandResult(JsonRecord):
    command: list[str]
    cwd: str
    stdout: str
    stderr: str
    exit_code: int
    elapsed_seconds: float


@dataclass(frozen=True)
class AgentRequest(JsonRecord):
    purpose: AttemptPurpose
    prompt_version: str
    workspace: str
    allowed_files: list[str]
    context: str


@dataclass(frozen=True)
class AgentResponse(JsonRecord):
    stdout: str
    stderr: str = ""
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    elapsed_seconds: float | None = None
    proposed_diff: str | None = None


@dataclass(frozen=True)
class AgentAttempt(JsonRecord):
    number: int
    purpose: AttemptPurpose
    request: AgentRequest
    response: AgentResponse | None
    accepted: bool
    rejection_reason: str | None = None


@dataclass(frozen=True)
class RustyCppAttempt(JsonRecord):
    number: int
    result: CommandResult


@dataclass(frozen=True)
class BuildAttempt(JsonRecord):
    number: int
    result: CommandResult
    baseline: bool = False


@dataclass(frozen=True)
class TestAttempt(JsonRecord):
    number: int
    result: CommandResult
    scope: str
    baseline: bool = False


@dataclass(frozen=True)
class BenchmarkResult(JsonRecord):
    command_result: CommandResult
    label: str
    baseline: bool = False


@dataclass(frozen=True)
class HumanIntervention(JsonRecord):
    category: HumanEffortCategory
    minutes: float
    description: str
    unit_id: str
    recorded_by: str | None = None


@dataclass(frozen=True)
class ExperimentResult(JsonRecord):
    experiment_id: str
    application: str
    application_commit: str
    rustycpp_commit: str
    state: ExperimentState
    outcome: str
    unit: MigrationUnit
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    agent_attempts: list[AgentAttempt] = field(default_factory=list)
    rustycpp_attempts: list[RustyCppAttempt] = field(default_factory=list)
    build_attempts: list[BuildAttempt] = field(default_factory=list)
    test_attempts: list[TestAttempt] = field(default_factory=list)
    benchmarks: list[BenchmarkResult] = field(default_factory=list)
    human_interventions: list[HumanIntervention] = field(default_factory=list)
    failure_reason: str | None = None
    ai_use_ids: list[str] = field(default_factory=list)
