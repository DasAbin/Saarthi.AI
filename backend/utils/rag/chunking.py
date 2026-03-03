"""
Text chunking utilities for RAG pipeline.

Splits documents into chunks with overlap for better context preservation.
"""

import re
from typing import List, Dict, Any, Optional


def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    preserve_sentences: bool = True
) -> List[str]:
    """
    Split text into chunks with optional sentence preservation.
    
    Args:
        text: Input text to chunk
        chunk_size: Target chunk size in tokens (approximate)
        chunk_overlap: Number of tokens to overlap between chunks
        preserve_sentences: If True, try to preserve sentence boundaries
        
    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []
    
    # Simple token approximation (1 token ≈ 4 characters)
    char_size = chunk_size * 4
    char_overlap = chunk_overlap * 4
    
    if preserve_sentences:
        # Split by sentences first
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > char_size and current_chunk:
                # Save current chunk
                chunk_text = " ".join(current_chunk)
                chunks.append(chunk_text)
                
                # Start new chunk with overlap
                if char_overlap > 0:
                    overlap_text = chunk_text[-char_overlap:]
                    current_chunk = [overlap_text, sentence]
                    current_length = len(overlap_text) + sentence_length
                else:
                    current_chunk = [sentence]
                    current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks if chunks else [text]
    
    else:
        # Simple character-based chunking
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + char_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - char_overlap
        
        return chunks if chunks else [text]


def chunk_with_metadata(
    text: str,
    source: str,
    page: Optional[int] = None,
    chunk_size: int = 512,
    chunk_overlap: int = 50
) -> List[Dict[str, Any]]:
    """
    Chunk text and attach metadata to each chunk.
    
    Args:
        text: Input text
        source: Source document identifier
        page: Page number (optional)
        chunk_size: Target chunk size
        chunk_overlap: Overlap size
        
    Returns:
        List of chunks with metadata
    """
    chunks = chunk_text(text, chunk_size, chunk_overlap)
    
    result = []
    for i, chunk_text in enumerate(chunks):
        result.append({
            "text": chunk_text,
            "chunk_index": i,
            "source": source,
            "page": page,
            "total_chunks": len(chunks)
        })
    
    return result
