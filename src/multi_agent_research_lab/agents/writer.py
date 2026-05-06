"""Writer agent skeleton."""

from __future__ import annotations

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`.

        Prefer an LLM synthesis of the research and analysis notes. If the
        provider is not available, fall back to the deterministic synthesis.
        """
        if not state.research_notes:
            state.final_answer = "No research notes available, so a final answer cannot be formed."
            state.errors.append("writer_missing_research_notes")
            state.add_trace_event(
                "writer_run",
                {
                    "status": "skipped",
                    "reason": "research_notes missing",
                },
            )
            return state

        analysis_block = state.analysis_notes or "No analysis notes were produced."
        llm_answer, llm_meta = self._write_with_llm(
            query=state.request.query,
            research_notes=state.research_notes,
            analysis_notes=analysis_block,
            sources=state.sources,
        )
        source_lines = []
        for index, source in enumerate(state.sources[:5], start=1):
            if source.url:
                source_lines.append(f"[{index}] {source.title} - {source.url}")
            else:
                source_lines.append(f"[{index}] {source.title}")

        source_summary = "\n".join(source_lines) if source_lines else "No sources collected."
        if llm_answer is not None:
            state.final_answer = llm_answer
            mode = "llm"
            metadata = {
                "source_count": len(state.sources),
                "has_analysis": bool(state.analysis_notes),
                "mode": mode,
                "input_tokens": llm_meta.get("input_tokens"),
                "output_tokens": llm_meta.get("output_tokens"),
                "cost_usd": llm_meta.get("cost_usd"),
            }
        else:
            state.final_answer = (
                f"Final answer for: {state.request.query}\n\n"
                f"Summary:\n{analysis_block}\n\n"
                f"Evidence snapshot:\n{source_summary}\n\n"
                "Takeaway: the current result is a structured synthesis generated from the "
                "research and analysis stages."
            )
            mode = "fallback"
            metadata = {
                "source_count": len(state.sources),
                "has_analysis": bool(state.analysis_notes),
                "mode": mode,
            }

        state.agent_results.append(
            AgentResult(
                agent=AgentName.WRITER,
                content=state.final_answer,
                metadata=metadata,
            )
        )
        state.add_trace_event(
            "writer_run",
            {
                "status": "ok",
                "mode": mode,
                "source_count": len(state.sources),
                "has_analysis": bool(state.analysis_notes),
            },
        )
        return state

    @staticmethod
    def _write_with_llm(
        query: str,
        research_notes: str,
        analysis_notes: str,
        sources: list,
    ) -> tuple[str | None, dict[str, int | float | None]]:
        try:
            client = LLMClient()
        except StudentTodoError:
            return None, {}

        source_block = "\n".join(
            f"- {source.title}: {source.url or source.snippet}" for source in sources[:5]
        ) or "- No sources collected."
        try:
            response = client.complete(
                system_prompt=(
                    "You are a writer agent. Produce a concise final answer from the "
                    "research and analysis notes. Keep the answer grounded and clear."
                ),
                user_prompt=(
                    f"Query: {query}\n\n"
                    f"Research notes:\n{research_notes}\n\n"
                    f"Analysis notes:\n{analysis_notes}\n\n"
                    f"Evidence snapshot:\n{source_block}\n\n"
                    "Write the final answer with these parts:\n"
                    "Final answer for: <query>\n\n"
                    "Summary:\n"
                    "<2-4 bullet or paragraph synthesis>\n\n"
                    "Evidence snapshot:\n"
                    "<top sources or note if none>\n\n"
                    "Takeaway: <one-line conclusion>"
                ),
            )
            return response.content, {
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd,
            }
        except StudentTodoError:
            return None, {}
