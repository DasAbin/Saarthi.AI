"""
Vector store utilities using DynamoDB + FAISS hybrid approach.

For production:
- FAISS for fast vector search (loaded from S3)
- DynamoDB for metadata storage
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional

# Optional numerical / ANN dependencies
try:
    import numpy as np  # type: ignore
    _NUMPY_AVAILABLE = True
except ImportError:
    _NUMPY_AVAILABLE = False
    logging.warning("NumPy not available. Using DynamoDB-only vector search.")

# Try to import FAISS (optional, requires NumPy)
try:
    import faiss  # type: ignore
    FAISS_AVAILABLE = _NUMPY_AVAILABLE
    if not FAISS_AVAILABLE:
        logging.warning("FAISS installed but NumPy missing. Disabling FAISS; using DynamoDB-only search.")
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS not available. Using DynamoDB-only vector search.")

from utils.aws.dynamodb import vector_search as dynamodb_search, store_chunk, get_chunk
from utils.s3_client import load_faiss_index, save_faiss_index

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class VectorStore:
    """
    Hybrid vector store using FAISS (if available) + DynamoDB.
    Falls back to DynamoDB-only search if FAISS unavailable.
    """
    
    def __init__(self, use_faiss: bool = True):
        self.use_faiss = use_faiss and FAISS_AVAILABLE
        self.faiss_index = None
        self.metadata_map = {}
        
        if self.use_faiss:
            self._load_faiss_index()
    
    def _load_faiss_index(self):
        """Load FAISS index from S3 if available."""
        try:
            index_data = load_faiss_index()
            if index_data:
                self.faiss_index = index_data.get("index")
                self.metadata_map = index_data.get("metadata", {})
                logger.info("Loaded FAISS index from S3")
        except Exception as e:
            logger.warning(f"Could not load FAISS index: {str(e)}. Using DynamoDB-only search.")
            self.use_faiss = False
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results
            filter_dict: Optional filters
            
        Returns:
            List of similar chunks with scores
        """
        if self.use_faiss and self.faiss_index:
            return self._faiss_search(query_embedding, top_k, filter_dict)
        else:
            return dynamodb_search(query_embedding, top_k, filter_dict)
    
    def _faiss_search(
        self,
        query_embedding: List[float],
        top_k: int,
        filter_dict: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Search using FAISS index."""
        try:
            # Convert to numpy array
            query_vector = np.array([query_embedding], dtype=np.float32)
            
            # Normalize for cosine similarity
            faiss.normalize_L2(query_vector)
            
            # Search
            k = min(top_k, self.faiss_index.ntotal)
            distances, indices = self.faiss_index.search(query_vector, k)
            
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx == -1:
                    continue
                
                # Get metadata
                chunk_id = self.metadata_map.get(str(idx), {}).get("chunk_id")
                if not chunk_id:
                    continue
                
                # Get full chunk from DynamoDB
                chunk = get_chunk(chunk_id)
                if not chunk:
                    continue
                
                # Apply filters if provided
                if filter_dict:
                    if not all(chunk.get(k) == v for k, v in filter_dict.items()):
                        continue
                
                # Convert distance to similarity (for cosine similarity)
                similarity = 1.0 - (dist / 2.0)  # L2 distance to cosine similarity
                
                results.append({
                    "chunk_id": chunk_id,
                    "text": chunk.get("text", ""),
                    "source": chunk.get("source", "Unknown"),
                    "page": chunk.get("page"),
                    "score": max(0.0, min(1.0, similarity)),  # Clamp to [0, 1]
                    "metadata": {k: v for k, v in chunk.items() if k not in ["embedding", "embedding_dim"]}
                })
            
            return results
            
        except Exception as e:
            logger.error(f"FAISS search error: {str(e)}")
            # Fallback to DynamoDB
            return dynamodb_search(query_embedding, top_k, filter_dict)
    
    def add_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ):
        """
        Add chunks to vector store.
        
        Args:
            chunks: List of chunk dictionaries with text and metadata
            embeddings: List of embedding vectors
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have same length")
        
        # Store in DynamoDB
        for chunk, embedding in zip(chunks, embeddings):
            chunk_id = chunk.get("chunk_id") or f"{chunk.get('source', 'doc')}_{chunk.get('chunk_index', 0)}"
            store_chunk(
                chunk_id=chunk_id,
                text=chunk["text"],
                embedding=embedding,
                metadata={k: v for k, v in chunk.items() if k != "text"}
            )
        
        # Update FAISS index if available
        if self.use_faiss:
            self._update_faiss_index(chunks, embeddings)
    
    def _update_faiss_index(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ):
        """Update FAISS index with new chunks."""
        try:
            if not FAISS_AVAILABLE:
                return
            
            # Initialize index if needed
            if self.faiss_index is None:
                dimension = len(embeddings[0])
                self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            
            # Convert to numpy and normalize
            embedding_array = np.array(embeddings, dtype=np.float32)
            faiss.normalize_L2(embedding_array)
            
            # Add to index
            start_idx = self.faiss_index.ntotal
            self.faiss_index.add(embedding_array)
            
            # Update metadata map
            for i, chunk in enumerate(chunks):
                idx = start_idx + i
                chunk_id = chunk.get("chunk_id") or f"{chunk.get('source', 'doc')}_{chunk.get('chunk_index', 0)}"
                self.metadata_map[str(idx)] = {
                    "chunk_id": chunk_id,
                    **{k: v for k, v in chunk.items() if k != "text"}
                }
            
            # Save to S3 (async, don't block)
            try:
                save_faiss_index(self.faiss_index, self.metadata_map)
            except Exception as save_error:
                logger.warning(f"Could not save FAISS index: {str(save_error)}")
            
        except Exception as e:
            logger.error(f"Error updating FAISS index: {str(e)}")


# Global vector store instance
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """Get or create global vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
