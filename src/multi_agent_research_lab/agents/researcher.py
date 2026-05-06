"""Researcher agent skeleton."""

from __future__ import annotations

import re

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import AgentName, AgentResult, SourceDocument
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`.

        Prefer search results plus an LLM synthesis. If the LLM provider is not
        available, fall back to a compact no-source note instead of fabricating
        citations.
        """
        query = state.request.query.strip()
        max_sources = state.request.max_sources
        keywords = self._extract_keywords(query)
        sources = SearchClient().search(query=query, max_results=max_sources)
        llm_notes, llm_meta = self._synthesize_with_llm(
            query=query,
            keywords=keywords,
            sources=sources,
        )
        if llm_notes is not None:
            state.sources = sources
            state.research_notes = llm_notes
            mode = "llm"
            metadata = {
                "source_count": len(sources),
                "keywords": keywords,
                "mode": mode,
                "input_tokens": llm_meta.get("input_tokens"),
                "output_tokens": llm_meta.get("output_tokens"),
                "cost_usd": llm_meta.get("cost_usd"),
                "fallback": "no_search_results" if not sources else None,
            }
        else:
            state.sources = sources
            state.research_notes = self._build_research_notes(
                query=query,
                keywords=keywords,
                sources=sources,
            )
            mode = "fallback"
            metadata = {
                "source_count": len(sources),
                "keywords": keywords,
                "mode": mode,
                "fallback": "no_search_results" if not sources else "llm_unavailable",
            }

        state.agent_results.append(
            AgentResult(
                agent=AgentName.RESEARCHER,
                content=state.research_notes,
                metadata=metadata,
            )
        )
        state.add_trace_event(
            "researcher_run",
            {
                "query": query,
                "source_count": len(sources),
                "keywords": keywords,
                "mode": mode,
                "fallback": metadata.get("fallback"),
            },
        )
        return state

    @staticmethod
    def _extract_keywords(query: str) -> list[str]:
        words = re.findall(r"[A-Za-z0-9]+", query.lower())
        stopwords = {
            "and",
            "the",
            "for",
            "with",
            "from",
            "into",
            "about",
            "this",
            "that",
            "what",
            "write",
            "summary",
            "research",
            "state",
            "of",
            "art",
        }
        keywords = [word for word in words if len(word) > 2 and word not in stopwords]
        return keywords[:5] or ["multi", "agent", "systems"]

    @staticmethod
    def _build_research_notes(
        query: str,
        keywords: list[str],
        sources: list[SourceDocument],
    ) -> str:
        topic = " ".join(keywords[:3]) if keywords else query
        if sources:
            bullets = "\n".join(f"- {source.title}: {source.snippet}" for source in sources)
        else:
            bullets = "- No external sources were found for this query."
        return (
            f"Research notes for: {query}\n"
            f"Core topic: {topic}\n"
            f"Key takeaways:\n{bullets}\n"
            f"Recommended next step: pass these notes to the analyst for synthesis."
        )

    @staticmethod
    def _synthesize_with_llm(
        query: str,
        keywords: list[str],
        sources: list[SourceDocument],
    ) -> tuple[str | None, dict[str, int | float | None]]:
        try:
            client = LLMClient()
        except StudentTodoError:
            return None, {}

        source_block = "\n".join(
            f"- {source.title}: {source.snippet}" for source in sources
        ) or "- No external sources returned by search."
        try:
            response = client.complete(
                system_prompt=(
                    "You are a research agent. Summarize the query and the retrieved sources "
                    "into concise research notes. Preserve factual tone, mention gaps, and do "
                    "not invent citations."
                ),
                user_prompt=(
                    f"Query: {query}\n"
                    f"Keywords: {', '.join(keywords)}\n\n"
                    f"Retrieved sources:\n{source_block}\n\n"
                    "Write research notes with these sections:\n"
                    "Research notes for: <query>\n"
                    "Core topic: <topic>\n"
                    "Key takeaways:\n"
                    "- ...\n"
                    "Recommended next step: ..."
                ),
            )
            return response.content, {
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "cost_usd": response.cost_usd,
            }
        except StudentTodoError:
            return None, {}
