"""Input guardrails for sensitive or high-risk queries."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import re

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GuardrailDecision:
    """Result of evaluating a user query against the safety policy."""

    blocked: bool
    category: str = ""
    reason: str = ""
    safe_response: str = ""


_RULES: list[tuple[str, tuple[str, ...], str]] = [
    (
        "self_harm",
        (
            r"\bsuicide\b",
            r"\bself[- ]?harm\b",
            r"\bkill myself\b",
            r"\bhurt myself\b",
        ),
        "I can’t help with self-harm instructions.",
    ),
    (
        "violence_or_weapons",
        (
            r"\bmake a bomb\b",
            r"\bexplosive\b",
            r"\bweapon\b",
            r"\bgun\b",
        ),
        "I can’t help with weapons or violent wrongdoing.",
    ),
    (
        "illegal_activity",
        (
            r"\bhack\b",
            r"\bphish\b",
            r"\bmalware\b",
            r"\bstolen\b",
        ),
        "I can’t help with instructions for illegal activity.",
    ),
    (
        "political_persuasion",
        (
            r"\bvote for\b",
            r"\bpersuad\w* voters\b",
            r"\belection manipulation\b",
            r"\bpropaganda\b",
        ),
        "I can’t help with political persuasion or manipulation.",
    ),
    (
        "privacy_or_personal_data",
        (
            r"\bssn\b",
            r"\bcredit card\b",
            r"\bpassword\b",
            r"\bdox\w*\b",
        ),
        "I can’t help with requests involving personal or sensitive data.",
    ),
]


def evaluate_query(query: str) -> GuardrailDecision:
    """Return a safety decision for the given query."""

    normalized = query.strip().lower()
    if not normalized:
        return GuardrailDecision(
            blocked=True,
            category="empty",
            reason="query is empty",
            safe_response="Please provide a specific research question.",
        )

    for category, patterns, response in _RULES:
        for pattern in patterns:
            if re.search(pattern, normalized):
                logger.warning("Guardrail blocked query category=%s pattern=%s", category, pattern)
                return GuardrailDecision(
                    blocked=True,
                    category=category,
                    reason=f"matched pattern: {pattern}",
                    safe_response=(
                        f"{response}\n\n"
                        "I can help with a high-level overview of the topic, "
                        "risk-aware alternatives, or safe background context."
                    ),
                )

    return GuardrailDecision(blocked=False)
