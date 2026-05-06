"""Domain-specific errors for the lab package."""

from __future__ import annotations

from typing import Any


class LabError(Exception):
    """Base error for the lab package with structured context."""

    code = "lab_error"

    def __init__(self, message: str = "", *, details: dict[str, Any] | None = None) -> None:
        self.message = message or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if not self.details:
            return self.message
        return f"{self.message} | details={self.details}"


class StudentTodoError(LabError):
    """Raised where learners are expected to implement core logic."""

    code = "student_todo"


class AgentExecutionError(LabError):
    """Raised when an agent fails after retries/fallbacks."""

    code = "agent_execution_failed"


class ValidationError(LabError):
    """Raised when state or output validation fails."""

    code = "validation_failed"
