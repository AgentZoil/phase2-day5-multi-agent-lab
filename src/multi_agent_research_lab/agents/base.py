"""Base agent contract.

Concrete agents implement the workflow-specific logic; this base class keeps the
shared contract small and explicit.
"""

from abc import ABC, abstractmethod
from typing import ClassVar

from multi_agent_research_lab.core.state import ResearchState


class BaseAgent(ABC):
    """Minimal interface every agent must implement."""

    name: ClassVar[str]

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        name = getattr(cls, "name", "")
        if not isinstance(name, str) or not name.strip():
            raise TypeError(f"{cls.__name__} must define a non-empty class attribute `name`")

    @abstractmethod
    def run(self, state: ResearchState) -> ResearchState:
        """Read and update shared state, then return it."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"
