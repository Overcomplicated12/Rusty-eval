"""Retry accounting only; repair content remains an agent-backend concern."""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import AttemptBudgets
from .models import AttemptPurpose


AUTOMATION_EXHAUSTED = "AUTOMATION_EXHAUSTED"


@dataclass
class RepairBudget:
    limits: AttemptBudgets
    used: dict[AttemptPurpose, int] = field(default_factory=dict)

    def _limit_for(self, purpose: AttemptPurpose) -> int:
        return {
            AttemptPurpose.INITIAL_CONVERSION: 1,
            AttemptPurpose.TRANSPILER_REPAIR: self.limits.transpiler_repairs,
            AttemptPurpose.COMPILE_REPAIR: self.limits.compile_repairs,
            AttemptPurpose.TEST_REPAIR: self.limits.test_repairs,
        }[purpose]

    @property
    def total_used(self) -> int:
        return sum(self.used.values())

    def can_attempt(self, purpose: AttemptPurpose) -> bool:
        return self.total_used < self.limits.max_total_attempts and self.used.get(purpose, 0) < self._limit_for(purpose)

    def record(self, purpose: AttemptPurpose) -> str | None:
        if not self.can_attempt(purpose):
            return AUTOMATION_EXHAUSTED
        self.used[purpose] = self.used.get(purpose, 0) + 1
        return None
