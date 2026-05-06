"""Command-line entrypoint for the lab starter."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Annotated
from uuid import uuid4

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.guardrails import evaluate_query
from multi_agent_research_lab.core.schemas import (
    AgentName,
    AgentResult,
    ResearchQuery,
)
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_case_markdown_report
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import (
    configure_logging,
    reset_run_id,
    set_run_id,
)
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.storage import LocalArtifactStore

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a minimal single-agent baseline placeholder."""

    _init()
    run_id = _new_run_id("baseline")
    with _run_context(run_id), trace_span("cli.baseline", {"query": query, "run_id": run_id}):
        state = _run_single_agent_baseline(query=query)
    console.print(
        Panel.fit(
            state.final_answer,
            title="Single-Agent Baseline",
        )
    )


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow skeleton."""

    _init()
    run_id = _new_run_id("multi-agent")
    with _run_context(run_id), trace_span("cli.multi_agent", {"query": query, "run_id": run_id}):
        blocked_state = _guardrail_blocked_state(query=query)
        if blocked_state is not None:
            result = blocked_state
        else:
            state = ResearchState(request=ResearchQuery(query=query))
            workflow = MultiAgentWorkflow()
            try:
                result = workflow.run(state)
            except StudentTodoError as exc:
                console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
                raise typer.Exit(code=2) from exc
    console.print(result.model_dump_json(indent=2))


@app.command()
def benchmark(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
    case_id: Annotated[
        str,
        typer.Option("--case-id", help="Scenario id used to group benchmark runs"),
    ] = "default_case",
    output: Annotated[
        str,
        typer.Option("--output", "-o", help="Relative path for the markdown report"),
    ] = "benchmark_report.md",
) -> None:
    """Run single-agent and multi-agent benchmark, then write a markdown report."""

    _init()
    run_id = _new_run_id("benchmark")
    with _run_context(run_id), trace_span("cli.benchmark", {"query": query, "run_id": run_id}):
        baseline_state, baseline_metrics = run_benchmark(
            run_name="baseline",
            query=query,
            runner=_run_single_agent_baseline,
            case_id=case_id,
        )
        multi_state, multi_metrics = run_benchmark(
            run_name="multi-agent",
            query=query,
            runner=_run_multi_agent,
            case_id=case_id,
        )
        artifact_store = LocalArtifactStore()
        baseline_trace_path = artifact_store.write_trace(
            f"traces/{baseline_metrics.run_id}_baseline.json",
            baseline_state,
        )
        multi_trace_path = artifact_store.write_trace(
            f"traces/{multi_metrics.run_id}_multi-agent.json",
            multi_state,
        )
        baseline_metrics.trace_link = str(baseline_trace_path)
        multi_metrics.trace_link = str(multi_trace_path)
        section = render_case_markdown_report(case_id, [baseline_metrics, multi_metrics])
        report_target = artifact_store.root / output
        prefix = ""
        if report_target.exists() and report_target.stat().st_size > 0:
            prefix = "\n\n"
        else:
            prefix = "# Benchmark Report\n\n"
        report_file = artifact_store.append_text(output, prefix + section)
        report = report_file.read_text(encoding="utf-8")
    console.print(Panel.fit(report, title="Benchmark Report"))
    console.print(
        f"Saved report to {report_file} "
        f"(baseline routes={baseline_state.route_history}, "
        f"multi-agent routes={multi_state.route_history})"
    )


def _run_single_agent_baseline(query: str) -> ResearchState:
    blocked_state = _guardrail_blocked_state(query=query)
    if blocked_state is not None:
        return blocked_state

    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    llm = LLMClient()
    with trace_span("baseline.run", {"query": request.query}):
        try:
            response = llm.complete(
                system_prompt=(
                    "You are a concise research assistant. "
                    "Answer the user's query directly and clearly."
                ),
                user_prompt=(
                    f"Question: {request.query}\n\n"
                    f"Audience: {request.audience}\n"
                    f"Max sources to consider: {request.max_sources}"
                ),
            )
            state.final_answer = response.content
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.SUPERVISOR,
                    content=response.content,
                    metadata={
                        "input_tokens": response.input_tokens,
                        "output_tokens": response.output_tokens,
                        "cost_usd": response.cost_usd,
                    },
                )
            )
        except StudentTodoError as exc:
            state.errors.append(f"baseline_fallback:{type(exc).__name__}")
            state.final_answer = _fallback_baseline_answer(request)
            state.agent_results.append(
                AgentResult(
                    agent=AgentName.SUPERVISOR,
                    content=state.final_answer,
                    metadata={
                        "fallback": True,
                        "error": str(exc),
                    },
                )
            )
            state.add_trace_event(
                "baseline_fallback",
                {
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
    return state


def _run_multi_agent(query: str) -> ResearchState:
    blocked_state = _guardrail_blocked_state(query=query)
    if blocked_state is not None:
        return blocked_state

    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    return workflow.run(state)


@contextmanager
def _run_context(run_id: str) -> None:
    token = set_run_id(run_id)
    try:
        yield
    finally:
        reset_run_id(token)


def _new_run_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


def _fallback_baseline_answer(request: ResearchQuery) -> str:
    return (
        f"Baseline fallback answer for: {request.query}\n\n"
        "The baseline provider was unavailable during the benchmark run, so this "
        "local fallback is used to keep the benchmark artifact complete.\n\n"
        "Takeaway: once the LLM provider is reachable, rerun the benchmark to get "
        "a real single-agent comparison."
    )


def _guardrail_blocked_state(query: str) -> ResearchState | None:
    decision = evaluate_query(query)
    if not decision.blocked:
        return None

    safe_query = query.strip() if len(query.strip()) >= 5 else "guardrail blocked query"
    request = ResearchQuery(query=safe_query)
    state = ResearchState(request=request)
    state.final_answer = decision.safe_response
    state.errors.append(f"guardrail_blocked:{decision.category}")
    state.agent_results.append(
        AgentResult(
            agent=AgentName.SUPERVISOR,
            content=decision.safe_response,
            metadata={
                "guardrail_blocked": True,
                "category": decision.category,
                "reason": decision.reason,
            },
        )
    )
    state.add_trace_event(
        "guardrail_blocked",
        {
            "category": decision.category,
            "reason": decision.reason,
        },
    )
    return state


if __name__ == "__main__":
    app()
