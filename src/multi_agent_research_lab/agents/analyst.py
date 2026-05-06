"""Analyst agent skeleton."""

from __future__ import annotations

import re

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`.

        Prefer an LLM synthesis of the research notes. If the provider is not
        available, fall back to a deterministic analysis.
        """
        if not state.research_notes:
            state.analysis_notes = "No research notes available for analysis."
            state.errors.append("analyst_missing_research_notes")
            state.add_trace_event(
                "analyst_run",
                {
                    "status": "skipped",
                    "reason": "research_notes missing",
                },
            )
            return state

        source_count = len(state.sources)
        titles = [source.title for source in state.sources[:3]]
        key_points = self._extract_key_points(state.research_notes)
        gaps = self._build_gaps(state.sources, key_points)
        llm_analysis, llm_meta = self._analyze_with_llm(
            query=state.request.query,
            research_notes=state.research_notes,
            sources=state.sources,
        )

        if llm_analysis is not None:
            state.analysis_notes = llm_analysis
            mode = "llm"
            metadata = {
                "source_count": source_count,
                "key_points": key_points,
                "mode": mode,
                "input_tokens": llm_meta.get("input_tokens"),
                "output_tokens": llm_meta.get("output_tokens"),
                "cost_usd": llm_meta.get("cost_usd"),
                "gap_summary": gaps,
            }
        else:
            analysis = [
                "Analysis summary:",
                f"- Source coverage: {source_count} source(s) reviewed.",
                f"- Key themes: {', '.join(key_points) if key_points else 'none detected'}.",
                f"- Strong signals: {', '.join(titles) if titles else 'no named sources'}.",
                f"- Gaps / risks: {gaps}",
                "- Next step: hand off to the writer for a concise final answer.",
            ]
            state.analysis_notes = "\n".join(analysis)
            mode = "fallback"
            metadata = {
                "source_count": source_count,
                "key_points": key_points,
                "mode": mode,
                "gap_summary": gaps,
            }

        state.agent_results.append(
            AgentResult(
                agent=AgentName.ANALYST,
                content=state.analysis_notes,
                metadata=metadata,
            )
        )
        state.add_trace_event(
            "analyst_run",
            {
                "status": "ok",
                "mode": mode,
                "source_count": source_count,
                "key_points": key_points,
            },
        )
        return state

    @staticmethod
    def _extract_key_points(research_notes: str) -> list[str]:
        candidates = re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", research_notes.lower())
        stopwords = {
            "analysis",
            "research",
            "notes",
            "summary",
            "source",
            "sources",
            "topic",
            "focuses",
            "synthetic",
            "reviewed",
            "available",
            "hand",
            "off",
            "writer",
        }
        unique: list[str] = []
        for word in candidates:
            if word in stopwords or word in unique:
                continue
            unique.append(word)
            if len(unique) == 4:
                break
        return unique

    @staticmethod
    def _build_gaps(sources: list, key_points: list[str]) -> str:
        if not sources:
            return "No sources were collected, so confidence is low."
        if not key_points:
            return "The notes are descriptive but not yet distilled into distinct claims."
        if len(sources) < 3:
            return "Coverage is thin; more sources would improve confidence."
        return "No major gap detected from the current synthetic source set."

    @staticmethod
    def _analyze_with_llm(
        query: str,
        research_notes: str,
        sources: list,
    ) -> tuple[str | None, dict[str, int | float | None]]:
        try:
            client = LLMClient()
        except StudentTodoError:
            return None, {}

        source_block = "\n".join(
            f"- {source.title}: {source.snippet}" for source in sources[:5]
        ) or "- No sources collected."
        try:
            response = client.complete(
                system_prompt=(
                    "You are an analyst agent. Convert research notes into structured "
                    "analysis with strengths, gaps, and next-step guidance. Keep it concise."
                ),
                user_prompt=(
                    f"Query: {query}\n\n"
                    f"Research notes:\n{research_notes}\n\n"
                    f"Source snapshot:\n{source_block}\n\n"
                    "Write analysis notes with these sections:\n"
                    "Analysis summary:\n"
                    "- Source coverage: ...\n"
                    "- Key themes: ...\n"
                    "- Strong signals: ...\n"
                    "- Gaps / risks: ...\n"
                    "- Next step: ..."
                ),
            )
            return response.content, {
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd,
            }
        except StudentTodoError:
            return None, {}
