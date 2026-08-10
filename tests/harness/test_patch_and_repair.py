from __future__ import annotations

import unittest

from harness.config import AttemptBudgets, EditPolicy
from harness.models import AttemptPurpose
from harness.patch import validate_changed_files
from harness.repair import AUTOMATION_EXHAUSTED, RepairBudget


class PatchAndRepairTests(unittest.TestCase):
    def test_rejects_test_and_unrelated_changes(self) -> None:
        policy = EditPolicy(["src/**"])
        result = validate_changed_files(["src/ok.cpp", "tests/test_ok.cpp", "README.md", "src/../generated/a.cpp"], policy)
        self.assertFalse(result.accepted)
        self.assertEqual(result.rejected_files, ["README.md", "src/../generated/a.cpp", "tests/test_ok.cpp"])

    def test_budget_stops_at_configured_limit(self) -> None:
        budget = RepairBudget(AttemptBudgets(max_total_attempts=2, transpiler_repairs=1, compile_repairs=1, test_repairs=1))
        self.assertIsNone(budget.record(AttemptPurpose.INITIAL_CONVERSION))
        self.assertIsNone(budget.record(AttemptPurpose.COMPILE_REPAIR))
        self.assertEqual(budget.record(AttemptPurpose.TEST_REPAIR), AUTOMATION_EXHAUSTED)
