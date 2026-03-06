"""
Simple text chunking utilities for document ingestion.

This module provides a thin wrapper around the existing RAG chunker with
defaults tuned for embedding (chunk_size=800, overlap=100).
"""

from __future__ import annotations

from typing import List

from utils.rag.chunking import chunk_text as _rag_chunk_text


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """
    Split text into overlapping chunks suitable for embedding.

    Args:
        text: Full document text.
        chunk_size: Approximate chunk size in tokens.
        overlap: Approximate overlap size in tokens between chunks.

    Returns:
        List of text chunks.
    """

    # Delegate to the existing RAG chunker to avoid duplication while using
    # ingestion-friendly defaults.
    return _rag_chunk_text(
        text=text,
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        preserve_sentences=True,
    )

