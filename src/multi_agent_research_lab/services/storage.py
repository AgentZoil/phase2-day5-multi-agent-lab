"""Storage skeleton for benchmark artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from multi_agent_research_lab.core.state import ResearchState


class LocalArtifactStore:
    """Small local store for reports and trace exports."""

    def __init__(self, root: Path = Path("reports")) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def write_text(self, relative_path: str, content: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def append_text(self, relative_path: str, content: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        if existing and not existing.endswith("\n"):
            existing += "\n"
        path.write_text(existing + content, encoding="utf-8")
        return path

    def write_trace(self, relative_path: str, state: ResearchState) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "request": state.request.model_dump(),
            "iteration": state.iteration,
            "route_history": state.route_history,
            "sources": [source.model_dump() for source in state.sources],
            "research_notes": state.research_notes,
            "analysis_notes": state.analysis_notes,
            "final_answer": state.final_answer,
            "agent_results": [result.model_dump() for result in state.agent_results],
            "trace": state.trace,
            "errors": state.errors,
        }
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
        return path
