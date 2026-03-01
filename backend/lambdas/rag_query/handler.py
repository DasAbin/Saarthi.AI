"""
Lambda handler for RAG-based query answering.
"""

import json
import os
import sys
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from utils.bedrock_client import get_embedding, invoke_claude, format_rag_prompt
from utils.opensearch_client import vector_search
from utils.response import success_response, error_response, lambda_response


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for RAG query endpoint.
    
    Expected event body:
    {
        "query": "What are the eligibility criteria for PMAY?",
        "language": "en"
    }
    """
    try:
        # Parse request body
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})
        
        query = body.get("query", "").strip()
        language = body.get("language", "en")
        
        if not query:
            return lambda_response(
                400,
                error_response("Query is required")
            )
        
        # Get query embedding
        query_embedding = get_embedding(query)
        
        # Search OpenSearch for relevant chunks
        search_results = vector_search(query_embedding, top_k=5)
        
        if not search_results:
            # No results found - use LLM without context
            answer = invoke_claude(
                prompt=f"Answer the following question about Indian government schemes: {query}",
                system_prompt="You are a helpful AI assistant providing information about Indian government schemes and policies.",
                temperature=0.7
            )
            
            return lambda_response(
                200,
                success_response({
                    "answer": answer,
                    "sources": [],
                    "confidence": 0.5
                })
            )
        
        # Format context chunks
        context_chunks = [
            {
                "text": result["text"],
                "source": result.get("source", "Unknown"),
                "page": result.get("page"),
                "score": result.get("score", 0.0)
            }
            for result in search_results
        ]
        
        # Generate answer using RAG
        rag_prompt = format_rag_prompt(query, context_chunks)
        answer = invoke_claude(
            prompt=rag_prompt,
            system_prompt="You are a helpful AI assistant providing accurate information about Indian government schemes and policies. Always cite your sources.",
            temperature=0.7
        )
        
        # Calculate confidence based on search scores
        avg_score = sum(r.get("score", 0.0) for r in search_results) / len(search_results) if search_results else 0.0
        confidence = min(avg_score / 10.0, 1.0)  # Normalize to 0-1
        
        # Format sources for response
        sources = [
            {
                "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                "source": chunk["source"],
                "page": chunk.get("page"),
                "score": chunk["score"]
            }
            for chunk in context_chunks
        ]
        
        return lambda_response(
            200,
            success_response({
                "answer": answer,
                "sources": sources,
                "confidence": confidence
            })
        )
        
    except Exception as e:
        print(f"Error in rag_query handler: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return lambda_response(
            500,
            error_response(f"Internal server error: {str(e)}")
        )
