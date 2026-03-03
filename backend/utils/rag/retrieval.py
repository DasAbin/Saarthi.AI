"""
Retrieval logic for RAG pipeline.
"""

import logging
from typing import List, Dict, Any, Optional

from utils.aws.bedrock import get_embedding
from utils.rag.vector_store import get_vector_store

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def retrieve_context(
    query: str,
    top_k: int = 5,
    filter_dict: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant context chunks for a query.
    
    Args:
        query: User query
        top_k: Number of chunks to retrieve
        filter_dict: Optional filters (e.g., {"source": "document.pdf"})
        
    Returns:
        List of relevant chunks with scores
    """
    try:
        # Generate query embedding
        logger.info(f"Generating embedding for query: {query[:100]}...")
        query_embedding = get_embedding(query)
        
        # Search vector store
        logger.info(f"Searching vector store for top {top_k} results")
        vector_store = get_vector_store()
        results = vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_dict=filter_dict
        )
        
        logger.info(f"Retrieved {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Error in retrieval: {str(e)}")
        return []


def calculate_confidence(scores: List[float]) -> float:
    """
    Calculate overall confidence score from retrieval scores.
    
    Args:
        scores: List of similarity scores
        
    Returns:
        Confidence score (0-1)
    """
    if not scores:
        return 0.0
    
    # Average score, normalized
    avg_score = sum(scores) / len(scores)
    
    # Boost confidence if multiple high-scoring results
    if len(scores) >= 3:
        avg_score *= 1.1
    
    return min(1.0, avg_score)
