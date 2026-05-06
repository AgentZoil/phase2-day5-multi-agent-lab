"""Search client abstraction for ResearcherAgent."""

from __future__ import annotations

import html
import json
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from urllib import parse, request
from urllib.error import HTTPError, URLError

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import SourceDocument

logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"[A-Za-z0-9]+")
_HTML_TAG_RE = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class _ScoredSource:
    source: SourceDocument
    score: float


class SearchClient:
    """Provider-agnostic search client with normalized ranking."""

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query.

        Source priority:
        1. Tavily when configured.
        2. OpenAlex for scholarly works.
        3. arXiv for preprints.
        4. Wikipedia as a general fallback.

        Results from all available providers are merged, deduplicated, and
        re-ranked by query relevance so the final list favors real research
        sources instead of provider order.
        """
        settings = get_settings()
        query = query.strip()
        if not query:
            return []

        candidate_sources: list[SourceDocument] = []

        if settings.tavily_api_key:
            candidate_sources.extend(
                self._search_tavily(
                    query=query,
                    max_results=max_results,
                    api_key=settings.tavily_api_key,
                )
            )

        candidate_sources.extend(self._search_openalex(query=query, max_results=max_results))
        candidate_sources.extend(self._search_arxiv(query=query, max_results=max_results))
        candidate_sources.extend(self._search_wikipedia(query=query, max_results=max_results))

        ranked = self._rank_and_dedupe(query=query, sources=candidate_sources)
        if ranked:
            return [item.source for item in ranked[:max_results]]

        logger.info("Search client returned no results for query=%r", query)
        return []

    @staticmethod
    def _search_tavily(query: str, max_results: int, api_key: str) -> list[SourceDocument]:
        payload = json.dumps(
            {
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "include_answer": False,
                "include_raw_content": False,
            }
        ).encode("utf-8")
        req = request.Request(
            "https://api.tavily.com/search",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            logger.warning("Tavily search failed for query=%r: %s", query, exc)
            return []

        results = data.get("results", [])
        sources: list[SourceDocument] = []
        for item in results[:max_results]:
            title = str(item.get("title") or query)
            url = item.get("url")
            snippet = str(item.get("content") or item.get("snippet") or "")
            if not snippet:
                continue
            sources.append(
                SourceDocument(
                    title=title,
                    url=url,
                    snippet=SearchClient._normalize_text(snippet),
                    metadata={
                        "provider": "tavily",
                        "score": item.get("score"),
                    },
                )
            )
        return sources

    @staticmethod
    def _search_openalex(query: str, max_results: int) -> list[SourceDocument]:
        params = parse.urlencode(
            {
                "search": query,
                "per-page": max_results,
            }
        )
        url = f"https://api.openalex.org/works?{params}"
        req = request.Request(url, headers={"User-Agent": "multi-agent-research-lab/0.1"})
        try:
            with request.urlopen(req, timeout=20) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            logger.warning("OpenAlex search failed for query=%r: %s", query, exc)
            return []

        sources: list[SourceDocument] = []
        for item in data.get("results", [])[:max_results]:
            title = str(item.get("display_name") or query)
            url = (
                item.get("primary_location", {}).get("landing_page_url")
                or item.get("doi")
                or item.get("id")
            )
            abstract = SearchClient._openalex_abstract(item)
            snippet = abstract or title
            sources.append(
                SourceDocument(
                    title=title,
                    url=url,
                    snippet=SearchClient._normalize_text(snippet),
                    metadata={
                        "provider": "openalex",
                        "cited_by_count": item.get("cited_by_count"),
                        "publication_year": item.get("publication_year"),
                    },
                )
            )
        return sources

    @staticmethod
    def _search_arxiv(query: str, max_results: int) -> list[SourceDocument]:
        params = parse.urlencode(
            {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results,
            }
        )
        url = f"https://export.arxiv.org/api/query?{params}"
        req = request.Request(url, headers={"User-Agent": "multi-agent-research-lab/0.1"})
        try:
            with request.urlopen(req, timeout=20) as response:
                xml_text = response.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            logger.warning("arXiv search failed for query=%r: %s", query, exc)
            return []

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            logger.warning("arXiv parse failed for query=%r: %s", query, exc)
            return []

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        sources: list[SourceDocument] = []
        for entry in root.findall("atom:entry", ns)[:max_results]:
            title = SearchClient._normalize_text(
                entry.findtext("atom:title", default="", namespaces=ns)
            )
            url = entry.findtext("atom:id", default="", namespaces=ns) or None
            summary = SearchClient._normalize_text(
                entry.findtext("atom:summary", default="", namespaces=ns)
            )
            if not title and not summary:
                continue
            sources.append(
                SourceDocument(
                    title=title or query,
                    url=url,
                    snippet=summary or title,
                    metadata={
                        "provider": "arxiv",
                    },
                )
            )
        return sources

    @staticmethod
    def _search_wikipedia(query: str, max_results: int) -> list[SourceDocument]:
        params = parse.urlencode(
            {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": max_results,
                "utf8": 1,
            }
        )
        url = f"https://en.wikipedia.org/w/api.php?{params}"
        req = request.Request(url, headers={"User-Agent": "multi-agent-research-lab/0.1"})
        try:
            with request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            logger.warning("Wikipedia search failed for query=%r: %s", query, exc)
            return []

        results = data.get("query", {}).get("search", [])
        sources: list[SourceDocument] = []
        for item in results[:max_results]:
            title = str(item.get("title") or query)
            snippet = str(item.get("snippet") or "")
            snippet = SearchClient._normalize_text(
                snippet.replace("<span class=\"searchmatch\">", "").replace("</span>", "")
            )
            if not snippet:
                continue
            sources.append(
                SourceDocument(
                    title=title,
                    url=f"https://en.wikipedia.org/wiki/{parse.quote(title.replace(' ', '_'))}",
                    snippet=snippet,
                    metadata={
                        "provider": "wikipedia",
                        "pageid": item.get("pageid"),
                    },
                )
            )
        return sources

    @staticmethod
    def _rank_and_dedupe(query: str, sources: list[SourceDocument]) -> list[_ScoredSource]:
        query_terms = SearchClient._extract_terms(query)
        if not sources:
            return []

        best_by_key: dict[str, _ScoredSource] = {}
        for source in sources:
            score = SearchClient._score_source(query_terms=query_terms, source=source)
            normalized_key = SearchClient._dedupe_key(source)
            scored = _ScoredSource(source=SearchClient._annotate_source(source, score), score=score)
            previous = best_by_key.get(normalized_key)
            if previous is None or scored.score > previous.score:
                best_by_key[normalized_key] = scored

        return sorted(best_by_key.values(), key=lambda item: item.score, reverse=True)

    @staticmethod
    def _score_source(query_terms: set[str], source: SourceDocument) -> float:
        provider = str(source.metadata.get("provider", "")).lower()
        provider_weight = {
            "tavily": 4.0,
            "openalex": 3.5,
            "arxiv": 3.2,
            "wikipedia": 1.5,
        }.get(provider, 1.0)

        title_terms = SearchClient._extract_terms(source.title)
        snippet_terms = SearchClient._extract_terms(source.snippet)
        title_overlap = len(query_terms & title_terms)
        snippet_overlap = len(query_terms & snippet_terms)
        exact_phrase_bonus = (
            1.5
            if SearchClient._phrase_present(query_terms, source.title, source.snippet)
            else 0.0
        )
        citation_bonus = 0.0
        if source.metadata.get("cited_by_count"):
            citation_bonus += min(float(source.metadata["cited_by_count"]) / 100.0, 2.0)
        if source.metadata.get("publication_year"):
            citation_bonus += 0.2
        return (
            provider_weight
            + (title_overlap * 2.0)
            + snippet_overlap
            + exact_phrase_bonus
            + citation_bonus
        )

    @staticmethod
    def _annotate_source(source: SourceDocument, score: float) -> SourceDocument:
        metadata = dict(source.metadata)
        metadata["rank_score"] = round(score, 3)
        return SourceDocument(
            title=source.title,
            url=source.url,
            snippet=source.snippet,
            metadata=metadata,
        )

    @staticmethod
    def _dedupe_key(source: SourceDocument) -> str:
        if source.url:
            return source.url.lower().rstrip("/")
        return f"{source.title.lower()}::{source.snippet[:80].lower()}"

    @staticmethod
    def _extract_terms(text: str) -> set[str]:
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
            "multi",
            "agent",
        }
        return {
            word
            for word in _WORD_RE.findall(text.lower())
            if len(word) > 2 and word not in stopwords
        }

    @staticmethod
    def _phrase_present(query_terms: set[str], title: str, snippet: str) -> bool:
        phrase = " ".join(sorted(query_terms))
        haystack = f"{title} {snippet}".lower()
        return bool(phrase and phrase in haystack)

    @staticmethod
    def _normalize_text(text: str) -> str:
        cleaned = html.unescape(text)
        cleaned = _HTML_TAG_RE.sub(" ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    @staticmethod
    def _openalex_abstract(item: dict[str, object]) -> str:
        inverted_index = item.get("abstract_inverted_index")
        if not isinstance(inverted_index, dict) or not inverted_index:
            return ""

        positions: dict[int, str] = {}
        for word, indices in inverted_index.items():
            if not isinstance(word, str) or not isinstance(indices, list):
                continue
            for index in indices:
                if isinstance(index, int):
                    positions[index] = word
        if not positions:
            return ""
        return " ".join(positions[index] for index in sorted(positions))
