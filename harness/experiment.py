"""Dry-run/mock-capable state-machine planning; no migration is performed here."""

from __future__ import annotations

from dataclasses import dataclass, field

from .config import HarnessConfig
from .models import ExperimentState, MigrationUnit


DRY_RUN_STATES = [
    ExperimentState.CREATED, ExperimentState.PREPARING, ExperimentState.BASELINING,
    ExperimentState.CONTEXT_BUILDING, ExperimentState.CONVERTING, ExperimentState.TRANSPILING,
    ExperimentState.BUILDING, ExperimentState.TESTING, ExperimentState.REPAIRING,
]


@dataclass
class ExperimentController:
    config: HarnessConfig
    unit: MigrationUnit
    state: ExperimentState = ExperimentState.CREATED
    history: list[ExperimentState] = field(default_factory=lambda: [ExperimentState.CREATED])

    def transition(self, state: ExperimentState) -> None:
        if self.state in (ExperimentState.COMPLETED, ExperimentState.FAILED):
            raise RuntimeError("terminal experiment state cannot transition")
        self.state = state
        self.history.append(state)

    def dry_run(self) -> dict[str, object]:
        """Return the planned flow without creating a worktree or running commands."""
        for state in DRY_RUN_STATES[1:]:
            self.transition(state)
        return {
            "mode": "dry-run",
            "unit": self.unit.to_dict(),
            "states": [state.value for state in self.history],
            "commands": {
                "rustycpp": self.config.rustycpp_command,
                "build": self.config.build_command,
                "targeted_test": self.config.targeted_test_command,
                "full_test": self.config.full_test_command,
                "benchmark": self.config.benchmark_command,
            },
            "notes": [
                "No worktree was created.", "No coding agent was invoked.",
                "No RustyCpp, build, test, or benchmark command was run.",
            ],
        }
