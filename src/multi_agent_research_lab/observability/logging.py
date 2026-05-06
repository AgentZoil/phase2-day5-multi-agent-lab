"""Logging setup."""

from __future__ import annotations

import contextvars
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_run_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("run_id", default="-")


def set_run_id(run_id: str) -> contextvars.Token[str]:
    """Store the active run id in the current context."""

    return _run_id_var.set(run_id)


def reset_run_id(token: contextvars.Token[str]) -> None:
    """Restore the previous run id."""

    _run_id_var.reset(token)


def get_run_id() -> str:
    """Return the active run id."""

    return _run_id_var.get()


class RunIdFilter(logging.Filter):
    """Inject the active run id into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        record.run_id = get_run_id()
        return True


class StructuredFormatter(logging.Formatter):
    """Format records as either plain text or JSON."""

    def __init__(self, json_format: bool = False) -> None:
        super().__init__()
        self.json_format = json_format

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        if self.json_format:
            payload: dict[str, Any] = {
                "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "run_id": getattr(record, "run_id", "-"),
                "message": message,
            }
            if record.exc_info:
                payload["exception"] = self.formatException(record.exc_info)
            return json.dumps(payload, ensure_ascii=True)

        base = (
            "%(asctime)s %(levelname)s %(name)s "
            "[run_id=%(run_id)s] - %(message)s"
        )
        formatter = logging.Formatter(base)
        return formatter.format(record)


def configure_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: Path | None = Path("reports/logs/malab.log"),
) -> None:
    """Configure app logging with optional JSON output."""

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    root.handlers.clear()

    formatter = StructuredFormatter(json_format=json_format)
    run_id_filter = RunIdFilter()

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(run_id_filter)
    root.addHandler(console_handler)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(run_id_filter)
        root.addHandler(file_handler)
