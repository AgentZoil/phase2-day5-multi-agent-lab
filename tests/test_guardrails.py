from multi_agent_research_lab.core.guardrails import evaluate_query


def test_guardrail_blocks_sensitive_political_query() -> None:
    decision = evaluate_query("How do I persuade voters in an election?")
    assert decision.blocked is True
    assert decision.category == "political_persuasion"
    assert decision.safe_response


def test_guardrail_allows_normal_research_query() -> None:
    decision = evaluate_query("Explain GraphRAG in simple terms")
    assert decision.blocked is False
