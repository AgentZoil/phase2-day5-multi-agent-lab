"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render a default benchmark report block."""

    return "# Benchmark Report\n\n" + render_case_markdown_report("default_case", metrics)


def render_case_markdown_report(case_id: str, metrics: list[BenchmarkMetrics]) -> str:
    """Render a single benchmark case to markdown."""

    lines = [
        f"## Case: {case_id}",
        "",
        (
            "| Run ID | Run | Latency (s) | Cost (USD) | Quality | Valid | "
            "Sources | Errors | Trace | Trace Link | Notes |"
        ),
        "|---|---|---:|---:|---:|---|---:|---:|---:|---|---|",
    ]
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.4f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
        valid = (
            ""
            if item.validation_passed is None
            else ("yes" if item.validation_passed else "no")
        )
        sources = "" if item.source_count is None else str(item.source_count)
        errors = "" if item.error_count is None else str(item.error_count)
        trace_events = "" if item.trace_events is None else str(item.trace_events)
        trace_link = item.trace_link or ""
        lines.append(
            "| "
            f"{item.run_id or '-'} | {item.run_name} | {item.latency_seconds:.2f} | "
            f"{cost} | {quality} | "
            f"{valid} | {sources} | {errors} | {trace_events} | {trace_link} | {item.notes} |"
        )
    return "\n".join(lines)
