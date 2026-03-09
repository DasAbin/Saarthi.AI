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
        
        # Detect voice mode from path or body flag
        voice_mode = body.get("voice_mode", False)
        if event.get("path", "").endswith("/stt") or event.get("path", "").endswith("/voice"):
            voice_mode = True
        
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

        messages = body.get("messages", [])
        if not messages and history:
            messages = history
            
        conversation = ""
        if messages:
            conversation = "\n".join([m.get("content", "") for m in messages[-6:]])
        # Cache key includes query, language, optional document_id, and voice_mode
        q_hash = make_query_hash(query, language, document_id, voice_mode)
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

        # Web Search Fallback
        if not top_chunks or max_score < 0.55:
            try:
                from tavily import TavilyClient
                tavily_api_key = os.environ.get("TAVILY_API_KEY", "")
                if tavily_api_key:
                    client = TavilyClient(api_key=tavily_api_key)
                    search_result = client.search(query=query, search_depth="basic")
                    if search_result and search_result.get("results"):
                        for res in search_result["results"]:
                            top_chunks.append({
                                "text": res.get("content", ""),
                                "source": res.get("title", "Web Search"),
                                "url": res.get("url", ""),
                                "score": 0.8
                            })
                        max_score = max(max_score, 0.8)
            except Exception as e:
                logger.warning(f"Tavily search failed: {e}")

        question = query
        
        confidence = round(min(0.95, max_score + 0.3) * 100, 1) if max_score > 0 else 30.0

        if not top_chunks or max_score < 0.55:
            # Weak or no document context: answer using model's general knowledge.
            prompt = f"""You are Saarthi, an AI assistant designed to help citizens understand Indian government schemes clearly.

Rules:
- Provide factual information only.
- Do not invent scheme details.
- Always respond in structured format.
- Use bullet points when possible.
- Answer using your general knowledge since document context is missing.
- When suggesting resources, strongly prefer: scholarships.gov.in, education.gov.in, AICTE, UGC, or state scholarship portals.
{"- Provide conversational yet detailed explanations." if voice_mode else ""}

Response Format:

## Overview
Explain what the scheme is.

## Eligibility
List eligibility criteria clearly.

## Benefits
Explain financial or social benefits.

## Application Process
Provide step-by-step process.

## Important Notes
Mention deadlines, conditions or special rules.

## Official Website
Provide a government website link if available.

Conversation History:
{conversation if conversation else "None"}

User Question:
{question}

Retrieved Context:
None available.

Generate a clear structured answer.
"""

            answer = generate_general_answer(prompt)
            fallback_text = "\n\n*Note: This information is based on general knowledge and may require verification from official government websites.*"
            if "verification from official government websites" not in answer:
                answer += fallback_text

            success_payload = {
                "answer": answer.strip(),
                "sources": [],
                "confidence": confidence,
            }
        else:
            # Strong document context available
            context_text = "\n\n".join([chunk.get("text", "") for chunk in top_chunks])

            prompt = f"""You are Saarthi, an AI assistant designed to help citizens understand Indian government schemes clearly.

Rules:
- Provide factual information only.
- Do not invent scheme details.
- If the information is not present in the retrieved context, say:
  "Information not found in available policy documents."
- Always respond in structured format.
- Use bullet points when possible.
{"- Provide conversational yet detailed explanations." if voice_mode else ""}

Response Format:

## Overview
Explain what the scheme is.

## Eligibility
List eligibility criteria clearly.

## Benefits
Explain financial or social benefits.

## Application Process
Provide step-by-step process.

## Important Notes
Mention deadlines, conditions or special rules.

## Official Website
Provide a government website link if available.

Conversation History:
{conversation if conversation else "None"}

User Question:
{question}

Retrieved Context:
{context_text}

Generate a clear structured answer.
"""

            answer = generate_general_answer(prompt)

            # Build clean, de-duplicated source metadata
            sources = []
            seen_titles = set()
            for chunk in top_chunks:
                title = chunk.get("source") or chunk.get("document_name") or chunk.get("metadata", {}).get("document_id") or "Policy Document"
                url = chunk.get("url") or "#"
                if title not in seen_titles:
                    seen_titles.add(title)
                    sources.append({
                        "title": title,
                        "url": url
                    })
            sources = sources[:3]

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
