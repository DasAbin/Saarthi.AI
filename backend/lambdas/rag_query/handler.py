"""
Lambda handler for RAG-based query answering.

This handler processes user queries using:
- Amazon Bedrock (Claude 3 Sonnet for generation, Titan for embeddings)
- DynamoDB + FAISS for vector search
- Returns answers with citations and confidence scores
"""

import json
import logging
import os
import sys
from typing import Any, Dict, Optional

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from utils.response import error_response, lambda_response, success_response
from rag.retriever import retrieve_relevant_chunks
from rag.generator import generate_answer
from services.query_cache import (
    get_cached_response,
    make_query_hash,
    put_cached_response,
)
from services.conversation_store import append_conversation_event

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for RAG query endpoint.
    
    Expected event body:
    {
        "query": "What are the eligibility criteria for PMAY?",
        "language": "en" | "hi" | "mr"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "answer": "string",
            "sources": [
                {
                    "text": "string",
                    "source": "string",
                    "page": number,
                    "score": number
                }
            ],
            "confidence": number (0-1)
        }
    }
    """
    try:
        logger.info("RAG query handler invoked")

        # Parse request body
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})
        
        # Validate input
        query = body.get("query", "").strip()
        language = body.get("language", "en")
        document_id: Optional[str] = body.get("document_id")
        user_id: str = body.get("user_id") or event.get("requestContext", {}).get("identity", {}).get("user", "") or "anonymous"
        session_id: str = body.get("session_id") or event.get("headers", {}).get("x-session-id", "") or "default"
        
        if not query:
            logger.warning("Empty query received")
            return lambda_response(
                400,
                error_response("Query is required")
            )
        
        if language not in ["en", "hi", "mr"]:
            logger.warning(f"Invalid language: {language}")
            return lambda_response(
                400,
                error_response("Language must be 'en', 'hi', or 'mr'")
            )
        
        logger.info(f"Processing query: {query[:100]}... (language: {language}, document_id={document_id})")

        language_name = {"en": "English", "hi": "Hindi", "mr": "Marathi"}[language]
        # Cache key includes query, language, and optional document_id
        q_hash = make_query_hash(query, language, document_id)
        cached = get_cached_response(q_hash)
        if cached:
            logger.info("Returning cached response for hash %s", q_hash[:8])
            # Also append to conversation log asynchronously (best effort)
            try:
                append_conversation_event(
                    user_id=user_id,
                    session_id=session_id,
                    query=query,
                    response=cached.get("answer", ""),
                    extra={"cached": True, "document_id": document_id},
                )
            except Exception as e:
                logger.warning("Failed to append cached conversation event: %s", str(e))

            return lambda_response(200, success_response(cached))

        # Retrieve context from vector store (optionally filtered by document_id)
        logger.info("Retrieving context chunks for query...")
        filters: Optional[Dict[str, Any]] = None
        if document_id:
            filters = {"document_id": document_id}

        context_chunks = retrieve_relevant_chunks(
            query=query,
            top_k=5,
            filter_dict=filters,
        )

        # Generate answer with Bedrock, with hackathon-grade fallback
        try:
            logger.info("Generating answer with Bedrock (Nova Micro)...")
            answer = generate_answer(query, context_chunks)
            success_payload = {
                "answer": answer,
                "sources": context_chunks,
                "confidence": 0.9 if context_chunks else 0.6,
            }
        except Exception as gen_err:
            logger.error("Bedrock generation failed: %s", str(gen_err))
            # Fallback response required for hackathon
            preview_sources = [
                {
                    "text": c.get("text", "")[:400],
                    "source": c.get("source", "Unknown"),
                    "score": c.get("score", 0.0),
                }
                for c in (context_chunks or [])[:5]
            ]
            fallback_answer = (
                "We could not generate a detailed response at the moment. "
                "Based on available information, here are the relevant scheme details:\n\n"
            )
            for src in preview_sources:
                fallback_answer += f"- From {src['source']}: {src['text']}\n"

            success_payload = {
                "answer": fallback_answer.strip(),
                "sources": context_chunks,
                "confidence": 0.4,
                "fallback": True,
            }

        # Store in cache (best effort)
        try:
            put_cached_response(q_hash, success_payload)
        except Exception as cache_err:
            logger.warning("Failed to write query cache: %s", str(cache_err))

        # Store conversation in S3 (best effort)
        try:
            append_conversation_event(
                user_id=user_id,
                session_id=session_id,
                query=query,
                response=success_payload.get("answer", ""),
                extra={"document_id": document_id, "from_cache": False},
            )
        except Exception as conv_err:
            logger.warning("Failed to append conversation event: %s", str(conv_err))

        return lambda_response(200, success_response(success_payload))
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return lambda_response(
            400,
            error_response("Invalid JSON in request body")
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return lambda_response(
            500,
            error_response(f"Internal server error: {str(e)}")
        )
