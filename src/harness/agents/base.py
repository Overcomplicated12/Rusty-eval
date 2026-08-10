"""Abstract contract separating the experiment controller from coding agents."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import AgentRequest, AgentResponse


class AgentBackend(ABC):
    """A coding agent proposes edits; the harness validates all outcomes."""

    @abstractmethod
    def run(self, request: AgentRequest) -> AgentResponse:
        """Submit one request and return only the agent's reported response."""
