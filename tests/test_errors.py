from multi_agent_research_lab.core.errors import AgentExecutionError, LabError, ValidationError


def test_lab_error_preserves_message_and_details() -> None:
    error = LabError("boom", details={"route": "writer"})
    assert str(error) == "boom | details={'route': 'writer'}"
    assert error.code == "lab_error"
    assert error.details == {"route": "writer"}


def test_error_subclasses_expose_codes() -> None:
    assert AgentExecutionError.code == "agent_execution_failed"
    assert ValidationError.code == "validation_failed"
