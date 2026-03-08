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
from decimal import Decimal
from typing import Any, Dict, Optional

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from utils.response import error_response, lambda_response, success_response
from rag.retriever import retrieve_relevant_chunks
from rag.generator import generate_general_answer
from services.query_cache import (
    get_cached_response,
    make_query_hash,
    put_cached_response,
)
from services.conversation_store import append_conversation_event


def convert_decimals(obj: Any) -> Any:
    """
    Recursively convert DynamoDB Decimal objects to float for JSON serialization.
    """
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    if isinstance(obj, Decimal):
        return float(obj)
    return obj


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
        history = body.get("history", []) or []
        user_id: str = body.get("user_id") or event.get("requestContext", {}).get("identity", {}).get("user", "") or "anonymous"
        session_id: str = body.get("session_id") or event.get("headers", {}).get("x-session-id", "") or "default"
        
        if not query:
            logger.warning("Empty query received")
            return lambda_response(
                400,
                error_response("Query is required")
            )

        if len(query) > 2000:
            logger.warning("Query too long: %d characters", len(query))
            return lambda_response(
                400,
                error_response("Query must be under 2000 characters")
            )
        
        if language not in ["en", "hi", "mr"]:
            logger.warning(f"Invalid language: {language}")
            return lambda_response(
                400,
                error_response("Language must be 'en', 'hi', or 'mr'")
            )
        
        logger.info(f"Processing query: {query[:100]}... (language: {language}, document_id={document_id})")

        language_name = {"en": "English", "hi": "Hindi", "mr": "Marathi"}[language]

        # Build LLM query that includes recent conversation history (if any)
        llm_query = query
        if history:
            try:
                history_lines = []
                # Only keep the last few turns to keep prompt size under control
                for m in history[-6:]:
                    role = m.get("role", "user")
                    prefix = "Citizen" if role == "user" else "Assistant"
                    content = m.get("content", "")
                    history_lines.append(f"{prefix}: {content}")
                history_block = "\n".join(history_lines)
                llm_query = (
                    "Conversation so far:\n"
                    f"{history_block}\n\n"
                    f"Latest question from the citizen:\n{query}"
                )
            except Exception as hist_err:
                logger.warning("Failed to process history for LLM query: %s", str(hist_err))
                llm_query = query
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

            return lambda_response(200, success_response(convert_decimals(cached)))

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
        # Limit context size to the top 4 chunks to keep answers focused
        top_chunks = context_chunks[:4] if context_chunks else []

        # Compute max_score for the retrieved chunks (if any)
        max_score = 0.0
        if top_chunks:
            try:
                max_score = max(float(c.get("score", 0.0)) for c in top_chunks)
                logger.info("Max retrieval score for top_chunks: %.4f", max_score)
            except Exception as score_err:
                logger.warning("Failed to compute max score from chunks: %s", str(score_err))
                max_score = 0.0

        # Build a ChatGPT-style prompt, with or without document context depending on retrieval strength.
        question = llm_query

        if not top_chunks or max_score < 0.6:
            # Weak or no document context: answer using model's general knowledge.
            prompt = f"""
You are an expert assistant explaining Indian government schemes clearly.

User Question:
{question}

Provide a detailed answer using your knowledge.

Structure the response with:

Overview
Eligibility
Benefits
Application Process
Important Notes

If the scheme is not widely known, still provide helpful information.
"""

            answer = generate_general_answer(prompt)
            success_payload = {
                "answer": answer.strip(),
                "sources": [],
                "confidence": 65.0,
            }
        else:
            # Strong document context available: behave like ChatGPT with RAG assistance.
            context_text = "\n\n".join([chunk.get("text", "") for chunk in top_chunks])

            prompt = f"""
You are an expert assistant explaining Indian government schemes clearly.

Use the following document context to answer the question. If the context is not sufficient, use your general knowledge as well.

Context:
{context_text}

User Question:
{question}

Provide a detailed answer.

Structure the response with:

Overview
Eligibility
Benefits
Application Process
Important Notes

If the scheme is not widely known, still provide helpful information.
"""

            answer = generate_general_answer(prompt)

            # Build clean, de-duplicated source metadata (no raw text)
            sources = []
            for chunk in top_chunks:
                document_name = (
                    chunk.get("document_name")
                    or chunk.get("source")
                    or chunk.get("metadata", {}).get("document_id")
                    or "Unknown document"
                )
                page = chunk.get("page", "unknown")
                score = round(float(chunk.get("score", 0.0)), 2)
                sources.append(
                    {
                        "document": document_name,
                        "page": page,
                        "score": score,
                    }
                )

            # Remove duplicate (document, page) entries
            dedup_map = {(s["document"], s["page"]): s for s in sources}
            sources = list(dedup_map.values())

            # Confidence based on average retrieval score (0–100)
            if top_chunks:
                raw_scores = [float(c.get("score", 0.0)) for c in top_chunks]
                avg_score = sum(raw_scores) / len(raw_scores)
                confidence = round(avg_score * 100.0, 1)
            else:
                confidence = 0.0

            success_payload = {
                "answer": answer.strip(),
                "sources": sources,
                "confidence": confidence,
            }

        # Normalize any Decimal values before caching / returning
        success_payload = convert_decimals(success_payload)

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
