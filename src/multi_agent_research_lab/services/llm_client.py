"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from openai import APIError, APITimeoutError, OpenAI, RateLimitError

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client."""

    def __init__(self) -> None:
        """Initialize LLM client with OpenAI."""

        settings = get_settings()
        if not settings.openai_api_key:
            raise StudentTodoError("OPENAI_API_KEY not set in environment variables")

        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.max_retries = 3
        self.timeout_seconds = settings.timeout_seconds

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion.

        Keep retry, timeout, and token logging here rather than inside agents.
        """

        start_time = time.time()
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    timeout=self.timeout_seconds,
                )

                input_tokens = response.usage.prompt_tokens if response.usage else None
                output_tokens = response.usage.completion_tokens if response.usage else None

                cost_usd = None
                if input_tokens and output_tokens:
                    if "gpt-4" in self.model:
                        cost_usd = (input_tokens * 0.00003) + (output_tokens * 0.00006)
                    elif "gpt-3.5" in self.model:
                        cost_usd = (input_tokens * 0.000001) + (output_tokens * 0.000002)
                    elif "gpt-4o" in self.model:
                        cost_usd = (input_tokens * 0.000005) + (output_tokens * 0.000015)

                elapsed_time = time.time() - start_time
                logger.info(
                    "LLM completion successful: model=%s, input_tokens=%s, "
                    "output_tokens=%s, duration=%.2fs, attempt=%s",
                    self.model,
                    input_tokens,
                    output_tokens,
                    elapsed_time,
                    attempt + 1,
                )

                return LLMResponse(
                    content=response.choices[0].message.content,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost_usd,
                )

            except (APIError, APITimeoutError, RateLimitError) as exc:
                last_error = exc
                wait_time = 2**attempt
                logger.warning(
                    "LLM API error (attempt %s/%s): %s: %s, retrying in %ss",
                    attempt + 1,
                    self.max_retries,
                    type(exc).__name__,
                    exc,
                    wait_time,
                )

                if attempt < self.max_retries - 1:
                    time.sleep(wait_time)
                else:
                    logger.error(
                        "LLM API failed after %s attempts: %s",
                        self.max_retries,
                        last_error,
                    )
                    raise StudentTodoError(
                        f"LLM API failed after {self.max_retries} attempts: {last_error}",
                    ) from exc

            except Exception as exc:
                logger.error("Unexpected error in LLM completion: %s: %s", type(exc).__name__, exc)
                raise StudentTodoError(f"Unexpected LLM error: {exc}") from exc

        raise StudentTodoError("LLM completion failed after all retries")
