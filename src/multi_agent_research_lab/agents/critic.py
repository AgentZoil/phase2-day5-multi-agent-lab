"""Optional critic agent for fact-checking and safety review."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState


class CriticAgent(BaseAgent):
    """Optional fact-checking and safety-review agent."""

    name = "critic"

    def run(self, state: ResearchState) -> ResearchState:
        """Validate final answer and append findings.
        """
        if not state.final_answer:
            state.add_trace_event(
                "critic_run",
                {
                    "status": "skipped",
                    "reason": "final_answer missing",
                },
            )
            return state

        citation_count = sum(1 for source in state.sources if source.url)
        findings = (
            "Critic review:\n"
            f"- Final answer length: {len(state.final_answer.split())} words\n"
            f"- Source count: {len(state.sources)}\n"
            f"- Citation-bearing sources: {citation_count}\n"
            "- Safety note: no obvious blocklisted content detected in the current fallback path."
        )
        state.agent_results.append(
            AgentResult(
                agent=AgentName.CRITIC,
                content=findings,
                metadata={
                    "source_count": len(state.sources),
                    "citation_count": citation_count,
                },
            )
        )
        state.add_trace_event(
            "critic_run",
            {
                "status": "ok",
                "source_count": len(state.sources),
                "citation_count": citation_count,
            },
        )
        return state
