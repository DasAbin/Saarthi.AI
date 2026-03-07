"""
Embedding service for the RAG pipeline.

Provides a simple interface for generating embeddings for text chunks using
Amazon Titan Embeddings via Bedrock.
"""

from __future__ import annotations

from typing import List
import logging

from utils.aws.bedrock import get_embedding, get_embeddings_batch

logger = logging.getLogger(__name__)


def generate_embedding(text_chunk: str) -> List[float]:
    """
    Generate an embedding vector for a single text chunk.

    Args:
        text_chunk: Text content to embed.

    Returns:
        Embedding vector as a list of floats. Returns an empty list if
        embedding generation fails so the pipeline can continue.
    """
    try:
        embedding = get_embedding(text_chunk)
        logger.info("Generated embedding for chunk length %d", len(text_chunk or ""))
        return embedding
    except Exception as e:
        logger.error(
            "Embedding generation failed for chunk length %d: %s",
            len(text_chunk or ""),
            str(e),
        )
        # Return empty embedding so caller can decide how to handle it,
        # but do not crash the overall ingestion.
        return []


def generate_embeddings(text_chunks: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple text chunks sequentially.

    Args:
        text_chunks: List of text chunks.

    Returns:
        List of embedding vectors.
    """
    try:
        return get_embeddings_batch(text_chunks)
    except Exception as e:
        logger.error("Batch embedding generation failed: %s", str(e))
        # Fallback: return empty embeddings for each chunk
        return [[] for _ in text_chunks]

