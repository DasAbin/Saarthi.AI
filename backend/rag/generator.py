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


SYSTEM_PROMPT = """
You are an AI assistant helping citizens understand Indian government schemes.

Your job is to explain policies clearly using the provided document context.

Rules:

1. Always answer using ONLY the provided document context.
2. If information is missing, say "The document does not contain this information."
3. Provide concise but structured answers.
4. Use the following format:

Overview
Eligibility
Benefits
How It Works
Important Notes

5. Avoid markdown symbols like ** or ##.
6. Keep explanations simple so a non-technical citizen can understand.

"""


GENERAL_SYSTEM_PROMPT = """
You are an AI assistant helping citizens understand Indian government schemes.

Your job is to explain policies clearly using your general knowledge, even
when no specific document context is available.

Rules:

1. Answer using your general knowledge about Indian government schemes.
2. If you are unsure or information is not commonly known, say
   "I am not sure about this detail based on general knowledge."
3. Provide concise but structured answers.
4. Use the following format:

Overview
Eligibility
Benefits
How It Works
Important Notes

5. Avoid markdown symbols like ** or ##.
6. Keep explanations simple so a non-technical citizen can understand.

"""

def build_civic_prompt(query: str, context_chunks: List[Dict[str, Any]]) -> str:
    """
    Build a prompt with compact document context.
    """
    if context_chunks:
        # Only include brief context headers to keep prompt small.
        context_lines = []
        for idx, chunk in enumerate(context_chunks, start=1):
            doc_name = chunk.get("document_name") or chunk.get("source") or "Unknown document"
            page = chunk.get("page", "unknown")
            context_lines.append(f"[Context {idx}] Document: {doc_name} | Page: {page}")
        context_text = "\n".join(context_lines)
    else:
        context_text = "No specific document context was retrieved."

    prompt = f"""Use the following document context and answer the citizen's question.

Document context:
{context_text}

Citizen question:
{query}
"""

    return prompt


def generate_answer(query: str, context_chunks: List[Dict[str, Any]]) -> str:
    """
    Generate an answer using Bedrock (Nova Micro) with robust fallback.

    On any Bedrock error, the caller should catch and construct a structured
    fallback message for hackathon readiness.
    """
    prompt = build_civic_prompt(query, context_chunks)

    return invoke_claude(
        prompt=prompt,
        system_prompt=SYSTEM_PROMPT,
        max_tokens=1024,
        temperature=0.3,
    )


def generate_general_answer(query: str) -> str:
    """
    Generate an answer using Bedrock (Nova Micro) based on general knowledge,
    without requiring retrieved document context.
    """
    prompt = f"""Answer the citizen's question about Indian government schemes.

Citizen question:
{query}
"""

    return invoke_claude(
        prompt=prompt,
        system_prompt=GENERAL_SYSTEM_PROMPT,
        max_tokens=1024,
        temperature=0.5,
    )

