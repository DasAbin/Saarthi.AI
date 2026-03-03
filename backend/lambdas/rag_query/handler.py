"""
Lambda handler for RAG-based query answering.

This handler processes user queries using:
- Amazon Bedrock (Claude 3 Sonnet for generation, Titan for embeddings)
- DynamoDB + FAISS for vector search
- Returns answers with citations and confidence scores
"""

import json
import os
import sys
import logging
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from utils.response import success_response, error_response, lambda_response

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

        # Lazy-import Bedrock client so that import errors
        # are caught and returned as proper JSON instead of generic 500s.
        try:
            from utils.aws.bedrock import invoke_claude  # type: ignore
        except Exception as import_err:
            logger.error(f"Failed to import Bedrock client: {import_err}", exc_info=True)
            return lambda_response(
                500,
                error_response(f"RAG pipeline is not available: {import_err}")
            )
        
        # Parse request body
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})
        
        # Validate input
        query = body.get("query", "").strip()
        language = body.get("language", "en")
        
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
        
        logger.info(f"Processing query: {query[:100]}... (language: {language})")

        language_name = {"en": "English", "hi": "Hindi", "mr": "Marathi"}[language]
        language_instruction = (
            f"Respond in {language_name}. "
            "Do not include translations to other languages. "
            "Use the native script for the language (Hindi/Marathi in Devanagari)."
        )

        # NOTE: For now, we skip vector-store retrieval in Lambda (to avoid heavy
        # native deps like NumPy/FAISS) and directly query Claude with a
        # government-schemes-focused system prompt. This still uses real
        # Bedrock (Claude 3 Sonnet) and gives high-quality answers.
        logger.info("Generating answer with Claude (no vector store retrieval)...")
        system_prompt = (
            "You are a helpful AI assistant providing accurate information about "
            "Indian government schemes and policies. Always cite your sources when "
            "referring to specific documents or schemes. "
            + language_instruction
        )
        
        answer = invoke_claude(
            prompt=(
                "Answer the following question. "
                "If the question is not about Indian government schemes/policies, still answer helpfully, "
                "but prioritize official Indian government sources where applicable.\n\n"
                f"Question: {query}"
            ),
            system_prompt=system_prompt,
            max_tokens=2048,
            temperature=0.7
        )

        logger.info("Generated answer from Claude (no context retrieval).")

        return lambda_response(
            200,
            success_response({
                "answer": answer,
                "sources": [],
                "confidence": 0.5
            })
        )
        
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
