from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from harness.config import load_config
from harness.experiment import ExperimentController
from harness.models import (
    AgentAttempt, AgentRequest, AgentResponse, AttemptPurpose, ExperimentResult,
    ExperimentState, MigrationUnit, TokenSource, TokenUsage,
)
from harness.reporting import ExperimentReporter, ReportingError
from harness.telemetry import aggregate_tokens, attempt_counts

from test_config import VALID


def request() -> AgentRequest:
    return AgentRequest(AttemptPurpose.INITIAL_CONVERSION, "phase2-v1", "/tmp/work", ["src/a.cpp"], "context")


class ExperimentTelemetryReportingTests(unittest.TestCase):
    def test_dry_run_state_sequence_does_not_reach_terminal_state(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            config_path = Path(temporary) / "config.toml"
            config_path.write_text(VALID, encoding="utf-8")
            unit = MigrationUnit("unit", "synthetic", "abc", "src/a.cpp", 1, 1, ["src/a.cpp"])
            plan = ExperimentController(load_config(config_path), unit).dry_run()
        self.assertEqual(plan["states"][0], "CREATED")
        self.assertIn("REPAIRING", plan["states"])
        self.assertNotIn("COMPLETED", plan["states"])

    def test_telemetry_distinguishes_reported_estimated_and_unavailable(self) -> None:
        initial = AgentAttempt(1, AttemptPurpose.INITIAL_CONVERSION, request(), AgentResponse("", token_usage=TokenUsage(2, 3, 5, TokenSource.PROVIDER_REPORTED)), True)
        reported = aggregate_tokens([initial])
        self.assertEqual((reported.total_tokens, reported.source), (5, TokenSource.PROVIDER_REPORTED))
        estimated = AgentAttempt(2, AttemptPurpose.COMPILE_REPAIR, request(), AgentResponse("", token_usage=TokenUsage(1, 1, 2, TokenSource.LOCAL_ESTIMATE)), True)
        mixed = aggregate_tokens([initial, estimated])
        self.assertEqual((mixed.total_tokens, mixed.source), (7, TokenSource.UNAVAILABLE))
        self.assertEqual(aggregate_tokens([]).source, TokenSource.UNAVAILABLE)
        self.assertEqual(attempt_counts([initial, estimated]), {"COMPILE_REPAIR": 1, "INITIAL_CONVERSION": 1})

    def test_reporter_is_append_only_and_result_json_round_trips(self) -> None:
        unit = MigrationUnit("unit", "synthetic", "abc", "src/a.cpp", 1, 1, ["src/a.cpp"])
        result = ExperimentResult("run", "synthetic", "abc", "def", ExperimentState.COMPLETED, "SUCCESS", unit)
        with tempfile.TemporaryDirectory() as temporary:
            reporter = ExperimentReporter(temporary, "synthetic", "run")
            reporter.create()
            reporter.write_unit(unit)
            result_path = reporter.write_result(result)
            restored = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertEqual(restored, json.loads(json.dumps(result.to_dict())))
            with self.assertRaises(ReportingError):
                reporter.write_result(result)
