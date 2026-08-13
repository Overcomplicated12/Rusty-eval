from __future__ import annotations

import json
import unittest

from harness.models import (
    AgentAttempt,
    AgentRequest,
    AgentResponse,
    AttemptPurpose,
    ExperimentResult,
    ExperimentState,
    MigrationUnit,
    TokenSource,
    TokenUsage,
)


class ModelSerializationTests(unittest.TestCase):
    def test_nested_records_are_json_serializable(self) -> None:
        unit = MigrationUnit("unit-1", "synthetic", "abc123", "src/a.cpp", 1, 2, ["src/a.cpp"])
        request = AgentRequest(AttemptPurpose.INITIAL_CONVERSION, "phase2-v1", "/tmp/work", ["src/a.cpp"], "context")
        response = AgentResponse("proposal", token_usage=TokenUsage(3, 5, 8, TokenSource.PROVIDER_REPORTED), elapsed_seconds=1.5)
        result = ExperimentResult(
            "experiment-1", "synthetic", "abc123", "rusty123", ExperimentState.COMPLETED, "SUCCESS", unit,
            agent_attempts=[AgentAttempt(1, AttemptPurpose.INITIAL_CONVERSION, request, response, True)],
        )
        payload = result.to_dict()
        self.assertEqual(payload["state"], "COMPLETED")
        self.assertEqual(payload["agent_attempts"][0]["request"]["purpose"], "INITIAL_CONVERSION")
        self.assertEqual(json.loads(json.dumps(payload))["unit"]["id"], "unit-1")
