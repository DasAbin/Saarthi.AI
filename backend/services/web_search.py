"""
Web search helper using Tavily.

This is used as a fallback when document retrieval does not provide
sufficiently relevant context for answering a query.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Tuple

try:
    from tavily import TavilyClient  # type: ignore
except ImportError:
    TavilyClient = None  # type: ignore


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


_api_key = os.getenv("TAVILY_API_KEY")
_client: Any | None = None

if TavilyClient is None:
    logger.info(
        "tavily-python package not installed; web search fallback will be disabled."
    )
else:
    if _api_key:
        try:
            _client = TavilyClient(api_key=_api_key)
            logger.info("Tavily client initialized for web search fallback.")
        except Exception as e:
            logger.warning("Failed to initialize Tavily client: %s", str(e))
            _client = None
    else:
        logger.info("TAVILY_API_KEY not set; web search fallback will be disabled.")


def search_web(query: str) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Run a Tavily web search for the given query.

    Returns:
        A tuple of (combined_content, sources), where:
        - combined_content is a newline-joined string of result snippets
        - sources is a list of {title, url} dicts suitable for frontend display
    """
    if not _client:
        logger.warning("Tavily client not available; skipping web search.")
        return "", []

    try:
        result = _client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
        )
    except Exception as e:
        logger.warning("Tavily search failed: %s", str(e))
        return "", []

    raw_results = result.get("results") or []
    if not raw_results:
        return "", []

    contents: List[str] = []
    sources: List[Dict[str, Any]] = []

    for r in raw_results:
        content = r.get("content") or ""
        title = r.get("title") or ""
        url = r.get("url") or ""

        if content:
            contents.append(content)

        if title or url:
            sources.append(
                {
                    "title": title,
                    "url": url,
                }
            )

    combined_content = "\n".join(contents) if contents else ""
    return combined_content, sources

