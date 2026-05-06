import logging

from multi_agent_research_lab.observability.logging import configure_logging, set_run_id


def test_configure_logging_writes_file(tmp_path) -> None:
    log_file = tmp_path / "malab.log"
    configure_logging(level="INFO", log_file=log_file)
    token = set_run_id("run-123")
    try:
        logging.getLogger("multi_agent_research_lab.test").info("hello log")
    finally:
        from multi_agent_research_lab.observability.logging import reset_run_id

        reset_run_id(token)

    content = log_file.read_text(encoding="utf-8")
    assert "hello log" in content
    assert "run_id=run-123" in content
