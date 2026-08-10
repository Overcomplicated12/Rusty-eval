"""RustyCpp command runner; command shape is supplied entirely by configuration."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from .models import CommandResult


class RustyCppRunner:
    def __init__(self, command: list[str]) -> None:
        if not command:
            raise ValueError("RustyCpp command must be configured")
        self.command = list(command)

    def run(self, workspace: str | Path) -> CommandResult:
        started = time.monotonic()
        completed = subprocess.run(self.command, cwd=workspace, text=True, capture_output=True, check=False)
        return CommandResult(self.command, str(Path(workspace)), completed.stdout, completed.stderr, completed.returncode, time.monotonic() - started)
