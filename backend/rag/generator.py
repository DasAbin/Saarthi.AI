"""
Bedrock-based generator for civic RAG responses.

Uses Amazon Nova Micro (via the shared Bedrock client) to generate answers
from retrieved context, with bullet points, simple explanations, and
explicit source citations.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from utils.aws.bedrock import invoke_claude

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def build_civic_prompt(query: str, context_chunks: List[Dict[str, Any]]) -> str:
    """
    Build a civic-assistant prompt with context and explicit source labels.
    """
    if context_chunks:
        context_text = "\n\n".join(
            f"[Source: {chunk.get('source', 'Unknown')} | "
            f"Document ID: {chunk.get('metadata', {}).get('document_id', chunk.get('document_id', 'N/A'))} | "
            f"Score: {chunk.get('score', 0):.2f}]\n"
            f"{chunk.get('text', '')}"
            for chunk in context_chunks
        )
    else:
        context_text = "No specific document context was retrieved. Answer based on your general knowledge of Indian government schemes."

    prompt = f"""You are a civic assistant helping citizens understand Indian government schemes and services.

Use the provided context to answer the question. If the context is insufficient, say so clearly.

Context:
{context_text}

User question:
{query}

Your answer must:
- Start with a very simple explanation in 2–3 sentences.
- Then provide clear bullet points (using "- ") for key details like eligibility, benefits, and how to apply.
- End with a "Source:" section that cites the document name or description and page if available, for example:
  Source: PM-Kisan Guidelines PDF (Page 3)

If you are unsure, say that the answer may not be complete and explain what is missing."""

    return prompt


def generate_answer(query: str, context_chunks: List[Dict[str, Any]]) -> str:
    """
    Generate an answer using Bedrock (Nova Micro) with robust fallback.

    On any Bedrock error, the caller should catch and construct a structured
    fallback message for hackathon readiness.
    """
    prompt = build_civic_prompt(query, context_chunks)

    system_prompt = (
        "You are a helpful civic assistant for Indian citizens. "
        "You always answer clearly, use bullet points, and include source citations."
    )

    return invoke_claude(
        prompt=prompt,
        system_prompt=system_prompt,
        max_tokens=2048,
        temperature=0.5,
    )

