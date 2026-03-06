"""
Embedding service for the RAG pipeline.

Provides a simple interface for generating embeddings for text chunks using
Amazon Titan Embeddings via Bedrock.
"""

from __future__ import annotations

from typing import List

from utils.aws.bedrock import get_embedding


def generate_embedding(text_chunk: str) -> List[float]:
    """
    Generate an embedding vector for a single text chunk.

    Args:
        text_chunk: Text content to embed.

    Returns:
        Embedding vector as a list of floats.
    """
    return get_embedding(text_chunk)


def generate_embeddings(text_chunks: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple text chunks sequentially.

    Args:
        text_chunks: List of text chunks.

    Returns:
        List of embedding vectors.
    """
    from utils.aws.bedrock import get_embeddings_batch

    return get_embeddings_batch(text_chunks)

