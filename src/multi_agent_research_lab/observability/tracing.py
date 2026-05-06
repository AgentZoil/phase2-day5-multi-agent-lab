"""Tracing hooks.

This file intentionally avoids binding to one provider. Students can plug in LangSmith,
Langfuse, OpenTelemetry, or simple JSON traces.
"""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter
from typing import Any

logger = logging.getLogger(__name__)


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Minimal span context used by the skeleton.

    The helper is provider-agnostic, but it now emits structured start/end logs so
    runs remain debuggable even without an external tracing backend.
    """

    attrs = attributes or {}
    started = perf_counter()
    span: dict[str, Any] = {
        "name": name,
        "attributes": attrs,
        "duration_seconds": None,
        "status": "in_progress",
    }
    logger.info("trace_span_start name=%s attributes=%s", name, attrs)
    try:
        yield span
        span["status"] = "ok"
        logger.info(
            "trace_span_end name=%s status=%s duration_seconds=%.4f attributes=%s",
            name,
            span["status"],
            0.0,
            attrs,
        )
    except Exception as exc:
        span["status"] = "error"
        span["error_type"] = type(exc).__name__
        span["error"] = str(exc)
        logger.exception("trace_span_error name=%s attributes=%s", name, attrs)
        raise
    finally:
        span["duration_seconds"] = perf_counter() - started
        logger.info(
            "trace_span_finish name=%s status=%s duration_seconds=%.4f",
            name,
            span["status"],
            span["duration_seconds"],
        )
