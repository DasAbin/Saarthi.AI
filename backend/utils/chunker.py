"""
Simple character-based text chunking utilities for document ingestion.

This module splits long document text into fixed-size overlapping chunks
so that each chunk is safely within the Bedrock Titan embedding model
limits (<= 50,000 characters).

Defaults:
- chunk_size = 2000 characters
- overlap    = 200 characters
"""

from __future__ import annotations

from typing import List


def split_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping character-based chunks.

    Args:
        text: Full document text.
        chunk_size: Chunk size in characters.
        overlap: Overlap in characters between consecutive chunks.

    Returns:
        List of text chunks.
    """
    if not text or not text.strip():
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be >= 0 and < chunk_size")

    chunks: List[str] = []
    start = 0
    n = len(text)

    while start < n:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
    """
    Backwards-compatible wrapper used by ingestion code.

    Uses simple character-based splitting to ensure:
    - Many chunks are produced for large documents
    - Each chunk length < 50,000 characters (given default 2000)
    """
    return split_text(text, chunk_size=chunk_size, overlap=overlap)

