"""Benchmark skeleton for single-agent vs multi-agent."""

from collections.abc import Callable
from time import perf_counter

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.logging import get_run_id

Runner = Callable[[str], ResearchState]


def run_benchmark(
    run_name: str,
    query: str,
    runner: Runner,
    *,
    case_id: str = "default_case",
) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency and return a placeholder metric object.

    The benchmark now records basic validation signals so reports can distinguish
    between a successful synthesis and a fallback run.
    """

    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started
    validation_passed = bool(state.final_answer) and not state.errors
    source_count = len(state.sources)
    trace_events = len(state.trace)
    error_count = len(state.errors)
    quality_score = _estimate_quality_score(
        validation_passed=validation_passed,
        source_count=source_count,
        error_count=error_count,
        trace_events=trace_events,
    )
    notes = _build_notes(
        state=state,
        validation_passed=validation_passed,
        source_count=source_count,
        error_count=error_count,
        trace_events=trace_events,
    )
    metrics = BenchmarkMetrics(
        case_id=case_id,
        run_id=get_run_id(),
        trace_link="",
        run_name=run_name,
        latency_seconds=latency,
        quality_score=quality_score,
        validation_passed=validation_passed,
        source_count=source_count,
        error_count=error_count,
        trace_events=trace_events,
        estimated_cost_usd=_sum_estimated_cost(state),
        notes=notes,
    )
    return state, metrics


def _sum_estimated_cost(state: ResearchState) -> float | None:
    total = 0.0
    found = False
    for result in state.agent_results:
        cost = result.metadata.get("cost_usd")
        if isinstance(cost, (int, float)):
            total += float(cost)
            found = True
    return total if found else None


def _estimate_quality_score(
    *,
    validation_passed: bool,
    source_count: int,
    error_count: int,
    trace_events: int,
) -> float:
    score = 4.0 if validation_passed else 1.5
    score += min(source_count, 5) * 0.8
    score += min(trace_events, 10) * 0.15
    score -= min(error_count, 5) * 1.5
    return max(0.0, min(10.0, round(score, 1)))


def _build_notes(
    *,
    state: ResearchState,
    validation_passed: bool,
    source_count: int,
    error_count: int,
    trace_events: int,
) -> str:
    status = "pass" if validation_passed else "fallback"
    route_history = " -> ".join(state.route_history) if state.route_history else "none"
    return (
        f"status={status}; "
        f"sources={source_count}; "
        f"errors={error_count}; "
        f"trace_events={trace_events}; "
        f"routes={route_history}"
    )
