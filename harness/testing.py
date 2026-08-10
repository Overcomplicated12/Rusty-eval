"""Configured targeted/full test command execution with structured output."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from .models import CommandResult


def run_tests(command: list[str], workspace: str | Path) -> CommandResult:
    started = time.monotonic()
    completed = subprocess.run(command, cwd=workspace, text=True, capture_output=True, check=False)
    return CommandResult(command, str(Path(workspace)), completed.stdout, completed.stderr, completed.returncode, time.monotonic() - started)
