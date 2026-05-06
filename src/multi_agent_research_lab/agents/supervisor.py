"""Supervisor / router skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route.
        """
        settings = get_settings()

        if state.final_answer:
            next_route = "done"
            reason = "final_answer already present"
        elif state.iteration >= settings.max_iterations:
            next_route = "done"
            reason = f"max_iterations reached ({state.iteration}/{settings.max_iterations})"
        elif state.research_notes is None:
            next_route = "researcher"
            reason = "research_notes missing"
        elif state.analysis_notes is None:
            next_route = "analyst"
            reason = "analysis_notes missing"
        else:
            next_route = "writer"
            reason = "research and analysis available"

        state.record_route(next_route)
        state.add_trace_event(
            "supervisor_route",
            {
                "route": next_route,
                "reason": reason,
                "iteration": state.iteration,
                "max_iterations": settings.max_iterations,
            },
        )
        return state
