import pytest

from multi_agent_research_lab.agents import SupervisorAgent
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState


def test_supervisor_routes_to_researcher_when_notes_missing() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    result = SupervisorAgent().run(state)
    assert result is state
    assert state.iteration == 1
    assert state.route_history == ["researcher"]
    assert state.trace[0]["name"] == "supervisor_route"
    assert state.trace[0]["payload"]["route"] == "researcher"
