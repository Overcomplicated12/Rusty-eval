"""Codex CLI dry-run command construction only; it deliberately does not execute."""

from __future__ import annotations

from dataclasses import dataclass

from ..models import AgentRequest, AgentResponse, TokenUsage
from .base import AgentBackend


@dataclass(frozen=True)
class CodexDryRun:
    command: list[str]
    prompt: str


class CodexCliBackend(AgentBackend):
    def __init__(self, executable: str = "codex") -> None:
        self.executable = executable

    def build_dry_run(self, request: AgentRequest) -> CodexDryRun:
        return CodexDryRun(
            [self.executable, "exec", "--json", "--cd", request.workspace],
            request.context,
        )

    def run(self, request: AgentRequest) -> AgentResponse:
        """Return a dry-run marker instead of invoking an external coding agent."""
        preview = self.build_dry_run(request)
        return AgentResponse(stdout="Dry run only; Codex CLI was not invoked.", token_usage=TokenUsage(), proposed_diff=None)
