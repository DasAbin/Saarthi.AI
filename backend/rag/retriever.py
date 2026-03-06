"""
High-level retriever for the RAG pipeline.

Uses DynamoDB-backed vector store to retrieve the most relevant chunks for
an embedded query.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from utils.aws.bedrock import get_embedding
from utils.rag.vector_store import get_vector_store

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def retrieve_relevant_chunks(
    query: str,
    top_k: int = 5,
    filter_dict: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Embed the user query and retrieve the most relevant chunks.

    Args:
        query: User query text.
        top_k: Number of chunks to return.
        filter_dict: Optional metadata filters (e.g. {\"document_id\": \"...\"}).

    Returns:
        List of chunk dicts with at least: text, score, and metadata.
    """
    try:
        logger.info("Generating embedding for query (first 100 chars): %s", query[:100])
        query_embedding = get_embedding(query)

        vector_store = get_vector_store()
        results = vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_dict=filter_dict,
        )

        logger.info("Retriever returned %d chunks", len(results))
        return results

    except Exception as e:
        logger.error("Error during RAG retrieval: %s", str(e))
        return []

