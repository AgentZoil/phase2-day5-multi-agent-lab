"""Multi-agent workflow orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langgraph.graph import END, START, StateGraph

from multi_agent_research_lab.agents import (
    AnalystAgent,
    ResearcherAgent,
    SupervisorAgent,
    WriterAgent,
)
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError, ValidationError
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.logging import get_run_id
from multi_agent_research_lab.observability.tracing import trace_span


@dataclass(frozen=True)
class WorkflowBundle:
    """Container for the instantiated agents used by the workflow."""

    supervisor: SupervisorAgent
    researcher: ResearcherAgent
    analyst: AnalystAgent
    writer: WriterAgent


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def build(self):
        """Create the compiled LangGraph workflow."""

        bundle = self._build_bundle()
        graph = StateGraph(ResearchState)

        graph.add_node("supervisor", lambda state: self._run_supervisor(bundle, state))
        graph.add_node(
            "researcher",
            lambda state: self._run_worker(bundle.researcher.run, "researcher", state),
        )
        graph.add_node(
            "analyst",
            lambda state: self._run_worker(bundle.analyst.run, "analyst", state),
        )
        graph.add_node("writer", lambda state: self._run_worker(bundle.writer.run, "writer", state))

        graph.add_edge(START, "supervisor")
        graph.add_conditional_edges(
            "supervisor",
            self._next_route,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "done": END,
            },
        )
        graph.add_edge("researcher", "supervisor")
        graph.add_edge("analyst", "supervisor")
        graph.add_edge("writer", "supervisor")

        return graph.compile(name="multi_agent_workflow")

    def _build_bundle(self) -> WorkflowBundle:
        """Create the workflow bundle used for orchestration."""

        return WorkflowBundle(
            supervisor=SupervisorAgent(),
            researcher=ResearcherAgent(),
            analyst=AnalystAgent(),
            writer=WriterAgent(),
        )

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state.

        LangGraph handles the node transitions while this class keeps the
        recovery and validation policy explicit.
        """
        graph = self.build()
        settings = get_settings()
        with trace_span(
            "workflow.run",
            {
                "query": state.request.query,
                "run_id": get_run_id(),
                "max_iterations": settings.max_iterations,
            },
        ):
            state.add_trace_event(
                "workflow_start",
                {
                    "iteration": state.iteration,
                    "query": state.request.query,
                },
            )
            try:
                result = graph.invoke(state)
            except Exception as exc:
                state.errors.append(f"workflow_failure:{type(exc).__name__}")
                state.add_trace_event(
                    "workflow_error",
                    {
                        "route": "workflow",
                        "status": "graph_failure",
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    },
                )
                state.final_answer = self._fallback_final_answer(state)
                result = state
            final_state = (
                result
                if isinstance(result, ResearchState)
                else ResearchState.model_validate(result)
            )
            final_state.add_trace_event(
                "workflow_end",
                {
                    "iteration": final_state.iteration,
                    "route_history": list(final_state.route_history),
                    "has_final_answer": final_state.final_answer is not None,
                },
            )
        return final_state

    def _run_supervisor(self, bundle: WorkflowBundle, state: ResearchState) -> ResearchState:
        with trace_span(
            "workflow.supervisor",
            {
                "run_id": get_run_id(),
                "iteration": state.iteration,
                "route_history_len": len(state.route_history),
            },
        ):
            return bundle.supervisor.run(state)

    def _run_worker(
        self,
        runner: Any,
        route: str,
        state: ResearchState,
    ) -> ResearchState:
        try:
            with trace_span(
                f"workflow.{route}",
                {
                    "run_id": get_run_id(),
                    "iteration": state.iteration,
                    "route": route,
                },
            ):
                result = runner(state)
        except Exception as exc:
            state.errors.append(f"agent_failure:{route}:{type(exc).__name__}")
            state.add_trace_event(
                "workflow_error",
                {
                    "route": route,
                    "status": "agent_failure",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
            return self._recover_from_failure(state, route, exc)

        return self._validate_and_recover(result, route)

    @staticmethod
    def _next_route(state: ResearchState) -> str:
        if not state.route_history:
            return "done"
        return state.route_history[-1]

    def _validate_and_recover(self, state: ResearchState, route: str) -> ResearchState:
        """Ensure each stage produced the minimum viable output."""

        if route == "researcher" and not state.research_notes:
            return self._recover_from_failure(
                state,
                route,
                ValidationError("researcher did not populate research_notes"),
            )
        if route == "analyst" and not state.analysis_notes:
            return self._recover_from_failure(
                state,
                route,
                ValidationError("analyst did not populate analysis_notes"),
            )
        if route == "writer" and not state.final_answer:
            return self._recover_from_failure(
                state,
                route,
                ValidationError("writer did not populate final_answer"),
            )
        return state

    def _recover_from_failure(
        self,
        state: ResearchState,
        route: str,
        exc: Exception,
    ) -> ResearchState:
        """Create a safe fallback so the workflow can still finish."""

        if route == "researcher":
            if not state.research_notes:
                state.research_notes = self._fallback_research_notes(state)
            state.add_trace_event(
                "workflow_recovery",
                {
                    "route": route,
                    "status": "recovered",
                    "error": str(exc),
                },
            )
            return state

        if route == "analyst":
            if not state.analysis_notes:
                state.analysis_notes = self._fallback_analysis_notes(state)
            state.add_trace_event(
                "workflow_recovery",
                {
                    "route": route,
                    "status": "recovered",
                    "error": str(exc),
                },
            )
            return state

        if route == "writer":
            if not state.final_answer:
                state.final_answer = self._fallback_final_answer(state)
            state.add_trace_event(
                "workflow_recovery",
                {
                    "route": route,
                    "status": "recovered",
                    "error": str(exc),
                },
            )
            return state

        raise AgentExecutionError(f"unsupported route for recovery: {route}")

    @staticmethod
    def _fallback_research_notes(state: ResearchState) -> str:
        return (
            f"Research notes for: {state.request.query}\n"
            "Core topic: unavailable\n"
            "Key takeaways:\n"
            "- Research stage failed to produce notes; continuing with a safe fallback.\n"
            "Recommended next step: route to the analyst with the limited context available."
        )

    @staticmethod
    def _fallback_analysis_notes(state: ResearchState) -> str:
        return (
            "Analysis summary:\n"
            f"- Source coverage: {len(state.sources)} source(s) reviewed.\n"
            "- Key themes: unavailable due to analysis fallback.\n"
            "- Strong signals: none.\n"
            "- Gaps / risks: analysis stage failed; confidence is low.\n"
            "- Next step: hand off to the writer for a safe final answer."
        )

    @staticmethod
    def _fallback_final_answer(state: ResearchState) -> str:
        return (
            f"Final answer for: {state.request.query}\n\n"
            "Summary:\n"
            "The workflow completed with a fallback because one or more stages did not "
            "produce a valid output.\n\n"
            "Evidence snapshot:\n"
            f"{len(state.sources)} source(s) available.\n\n"
            "Takeaway: this answer is a safe fallback, not a fully validated synthesis."
        )
